"""Baseball MCP Server implementation."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, cast

from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl

from baseball_mcp.loaders.games import get_schedule as _load_schedule
from baseball_mcp.loaders.players import get_player_stats
from baseball_mcp.loaders.statcast import StatcastFormat, StatcastType, get_statcast
from baseball_mcp.loaders.teams import get_team_stats as _load_team_stats
from baseball_mcp.resources import ResourceHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseballMCPServer:
    """Baseball MCP Server for retrieving baseball information."""

    def __init__(self) -> None:
        """Initialize the baseball MCP server."""
        self.server: Server = Server("baseball-mcp")
        self.resource_handler = ResourceHandler()
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up the MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available baseball tools."""
            return [
                Tool(
                    name="get_player_stats",
                    description="Get player statistics for a specific player",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "player_name": {
                                "type": "string",
                                "description": "Name of the player",
                            },
                            "year": {
                                "type": "integer",
                                "description": "Year for statistics (optional)",
                                "minimum": 1871,
                            },
                        },
                        "required": ["player_name"],
                    },
                ),
                Tool(
                    name="get_team_stats",
                    description="Get team statistics for a specific team and year",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "team": {
                                "type": "string",
                                "description": "Team abbreviation (e.g., 'NYY', 'BOS')",
                            },
                            "year": {
                                "type": "integer",
                                "description": "Year for statistics",
                                "minimum": 1871,
                            },
                        },
                        "required": ["team", "year"],
                    },
                ),
                Tool(
                    name="get_schedule",
                    description="Get game schedule for a team and date range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "team": {
                                "type": "string",
                                "description": "Team abbreviation",
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD)",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD)",
                            },
                        },
                        "required": ["team", "start_date", "end_date"],
                    },
                ),
                Tool(
                    name="get_statcast",
                    description="Get Statcast data for a date range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD)",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD)",
                            },
                            "player_id": {
                                "type": "integer",
                                "description": "Optional player ID for filtering",
                            },
                            "statcast_type": {
                                "type": "string",
                                "enum": ["all", "batter", "pitcher"],
                                "description": "Type of Statcast data",
                                "default": "all",
                            },
                            "format_type": {
                                "type": "string",
                                "enum": ["summary", "parquet"],
                                "description": "Format of returned data",
                                "default": "summary",
                            },
                        },
                        "required": ["start_date", "end_date"],
                    },
                ),
                Tool(
                    name="get_standings",
                    description="Get division and league standings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "year": {
                                "type": "integer",
                                "description": "Year for standings",
                                "minimum": 1871,
                            },
                            "date": {
                                "type": "string",
                                "description": (
                                    "Optional date (YYYY-MM-DD) for standings "
                                    "on specific date"
                                ),
                            },
                        },
                        "required": ["year"],
                    },
                ),
                Tool(
                    name="compare_players",
                    description="Compare statistics between multiple players",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "players": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of player names to compare",
                                "minItems": 2,
                            },
                            "year": {
                                "type": "integer",
                                "description": "Year for comparison",
                                "minimum": 1871,
                            },
                            "metric": {
                                "type": "string",
                                "description": "Specific metric to focus on (optional)",
                            },
                        },
                        "required": ["players", "year"],
                    },
                ),
                Tool(
                    name="get_game_log",
                    description="Get game-by-game log for a player or team",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "entity": {
                                "type": "string",
                                "description": "Player name or team abbreviation",
                            },
                            "entity_type": {
                                "type": "string",
                                "enum": ["player", "team"],
                                "description": "Type of entity",
                                "default": "player",
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD)",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD)",
                            },
                        },
                        "required": ["entity", "start_date", "end_date"],
                    },
                ),
                Tool(
                    name="similarity_score",
                    description="Calculate sabermetric similarity between two players",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "player_a": {
                                "type": "string",
                                "description": "First player name",
                            },
                            "player_b": {
                                "type": "string",
                                "description": "Second player name",
                            },
                            "year": {
                                "type": "integer",
                                "description": "Year for comparison",
                                "minimum": 1871,
                            },
                            "metric_set": {
                                "type": "string",
                                "enum": ["batting", "pitching", "all"],
                                "description": "Set of metrics to use for similarity",
                                "default": "batting",
                            },
                        },
                        "required": ["player_a", "player_b", "year"],
                    },
                ),
                Tool(
                    name="park_factors",
                    description="Get ballpark factors affecting statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "year": {
                                "type": "integer",
                                "description": "Year for park factors",
                                "minimum": 1871,
                            },
                            "venue": {
                                "type": "string",
                                "description": "Specific venue name (optional)",
                            },
                        },
                        "required": ["year"],
                    },
                ),
                Tool(
                    name="list_team_abbreviations",
                    description="List valid team abbreviations for use with team tools",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
            ]

        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """List available MCP resources."""
            return [
                Resource(
                    uri=cast(AnyUrl, "team-season://SDP/2024"),
                    name="Team Season Package",
                    description=(
                        "Complete team season data including stats, "
                        "schedule, and overview. Example: team-season://SDP/2024 "
                        "Format: team-season://TEAM/YEAR"
                    ),
                    mimeType="text/markdown",
                ),
                Resource(
                    uri=cast(AnyUrl, "stat-definitions://v1"),
                    name="Baseball Statistics Definitions",
                    description=(
                        "Comprehensive glossary of baseball statistics "
                        "and metrics"
                    ),
                    mimeType="text/markdown",
                ),
                Resource(
                    uri=cast(AnyUrl, "cache://status"),
                    name="Cache Status",
                    description="Information about the cache usage and performance",
                    mimeType="application/json",
                ),
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read a specific resource."""
            try:
                resource = self.resource_handler.get_resource(uri)
                if isinstance(resource, types.TextResourceContents):
                    return resource.text
                else:
                    # For BlobResourceContents, we'd need to handle differently
                    raise ValueError(f"Resource {uri} is not a text resource")
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                raise ValueError(f"Could not read resource {uri}: {str(e)}") from e

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
        ) -> list[TextContent]:
            """Handle tool calls."""
            if arguments is None:
                arguments = {}

            try:
                if name == "get_player_stats":
                    result = await self._get_player_stats(
                        arguments.get("player_name", ""), arguments.get("year")
                    )
                elif name == "get_team_stats":
                    year = arguments.get("year")
                    if not isinstance(year, int):
                        raise ValueError("Year must be an integer")
                    result = await self._get_team_stats(arguments.get("team", ""), year)
                elif name == "get_schedule":
                    result = await self._get_schedule(
                        arguments.get("team", ""),
                        arguments.get("start_date", ""),
                        arguments.get("end_date", ""),
                    )
                elif name == "get_statcast":
                    result = await self._get_statcast(
                        arguments.get("start_date", ""),
                        arguments.get("end_date", ""),
                        arguments.get("player_id"),
                        arguments.get("statcast_type", "all"),
                        arguments.get("format_type", "summary"),
                    )
                elif name == "get_standings":
                    result = await self._get_standings(
                        arguments.get("year"),
                        arguments.get("date"),
                    )
                elif name == "compare_players":
                    result = await self._compare_players(
                        arguments.get("players", []),
                        arguments.get("year"),
                        arguments.get("metric"),
                    )
                elif name == "get_game_log":
                    result = await self._get_game_log(
                        arguments.get("entity", ""),
                        arguments.get("entity_type", "player"),
                        arguments.get("start_date", ""),
                        arguments.get("end_date", ""),
                    )
                elif name == "similarity_score":
                    result = await self._similarity_score(
                        arguments.get("player_a", ""),
                        arguments.get("player_b", ""),
                        arguments.get("year"),
                        arguments.get("metric_set", "batting"),
                    )
                elif name == "park_factors":
                    result = await self._park_factors(
                        arguments.get("year"),
                        arguments.get("venue"),
                    )
                elif name == "list_team_abbreviations":
                    result = await self._list_team_abbreviations()
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=str(result))]

            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_player_stats(
        self, player_name: str, year: int | None = None
    ) -> str:
        """Fetch player statistics via loader and return TSV string."""

        try:
            df = await asyncio.to_thread(get_player_stats, player_name, year)
            if df.empty:
                return f"No stats found for {player_name}"
            result: str = df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to fetch player stats: %s", exc)
            return f"Error fetching stats for {player_name}: {exc}"

    async def _get_team_stats(self, team: str, year: int) -> str:
        """Fetch team statistics via loader and return TSV string."""

        try:
            df = await asyncio.to_thread(_load_team_stats, team, year)
            if df.empty:
                return f"No stats found for team {team} in {year}"
            result: str = df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to fetch team stats: %s", exc)
            return f"Error fetching stats for {team}: {exc}"

    async def _get_schedule(self, team: str, start_date: str, end_date: str) -> str:
        """Fetch game schedule via loader and return TSV string."""

        try:
            df = await asyncio.to_thread(_load_schedule, team, start_date, end_date)
            if df.empty:
                return f"No games found for {team} between {start_date} and {end_date}"
            result: str = df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to fetch schedule: %s", exc)
            return f"Error fetching schedule for {team}: {exc}"

    async def _get_statcast(
        self, start_date: str, end_date: str, player_id: int | None,
        statcast_type: str, format_type: str
    ) -> str:
        """Fetch Statcast data via loader and return TSV string."""
        try:
            df = await asyncio.to_thread(
                get_statcast, start_date, end_date,
                player_id,
                cast(StatcastType, statcast_type),
                cast(StatcastFormat, format_type)
            )
            if df.empty:
                return f"No Statcast data found for {start_date} to {end_date}"
            result: str = df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to fetch Statcast data: %s", exc)
            return f"Error fetching Statcast data: {exc}"

    async def _get_standings(self, year: int | None, date: str | None) -> str:
        """Fetch standings data."""
        try:
            from pybaseball import standings

            if year is None:
                from datetime import datetime
                year = datetime.now().year

            # Get standings for the year
            standings_list = await asyncio.to_thread(standings, year)

            # standings returns a list of DataFrames (one for each division)
            if not standings_list or len(standings_list) == 0:
                return f"No standings data found for {year}"

            # Combine all standings into a single DataFrame
            import pandas as pd
            all_standings = []
            for i, df in enumerate(standings_list):
                if not df.empty:
                    # Add division information
                    df = df.copy()
                    df['Division'] = f'Division_{i+1}'
                    all_standings.append(df)

            if not all_standings:
                return f"No standings data found for {year}"

            combined_df = pd.concat(all_standings, ignore_index=True)
            result: str = combined_df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to fetch standings: %s", exc)
            return f"Error fetching standings for {year}: {exc}"

    async def _compare_players(
        self, players: list[str], year: int | None, metric: str | None
    ) -> str:
        """Compare statistics between multiple players."""
        try:
            if not players or len(players) < 2:
                return "Error: Need at least 2 players to compare"

            if year is None:
                from datetime import datetime
                year = datetime.now().year

            # Get stats for all players
            player_stats = []
            for player in players:
                df = await asyncio.to_thread(get_player_stats, player, year)
                if not df.empty:
                    df['Player'] = player
                    player_stats.append(df)

            if not player_stats:
                return "No player statistics found for comparison"

            # Combine all player stats
            import pandas as pd
            combined_df = pd.concat(player_stats, ignore_index=True)

            # Focus on specific metric if provided
            if metric and metric in combined_df.columns:
                comparison_df = combined_df[['Player', metric]].sort_values(
                    by=metric, ascending=False
                )
            else:
                comparison_df = combined_df

            result: str = comparison_df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to compare players: %s", exc)
            return f"Error comparing players: {exc}"

    async def _get_game_log(
        self, entity: str, entity_type: str, start_date: str, end_date: str
    ) -> str:
        """Get game-by-game log for a player or team."""
        try:
            if entity_type == "player":
                # For player game logs, we'll use a simplified approach
                # In a full implementation, you'd use pybaseball's game log functions
                df = await asyncio.to_thread(get_player_stats, entity, None)
                if df.empty:
                    return f"No game log found for player {entity}"
            else:
                # For team game logs, use the schedule as a proxy
                df = await asyncio.to_thread(
                    _load_schedule, entity, start_date, end_date
                )
                if df.empty:
                    return f"No game log found for team {entity}"

            result: str = df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to fetch game log: %s", exc)
            return f"Error fetching game log for {entity}: {exc}"

    async def _similarity_score(
        self, player_a: str, player_b: str, year: int | None, metric_set: str
    ) -> str:
        """Calculate sabermetric similarity between two players."""
        try:
            if year is None:
                from datetime import datetime
                year = datetime.now().year

            # Get stats for both players
            df_a = await asyncio.to_thread(get_player_stats, player_a, year)
            df_b = await asyncio.to_thread(get_player_stats, player_b, year)

            if df_a.empty or df_b.empty:
                return (
                    f"Cannot find stats for comparison between "
                    f"{player_a} and {player_b}"
                )

            # Simple similarity calculation based on key metrics
            import pandas as pd

            # Define metrics to compare based on metric_set
            if metric_set == "batting":
                metrics = ['AVG', 'HR', 'RBI', 'OPS']
            elif metric_set == "pitching":
                metrics = ['ERA', 'WHIP', 'K/9', 'BB/9']
            else:
                metrics = ['AVG', 'HR', 'RBI', 'OPS', 'ERA', 'WHIP']

            # Filter available metrics
            available_metrics = [
                m for m in metrics
                if m in df_a.columns and m in df_b.columns
            ]

            if not available_metrics:
                return "No common metrics found for comparison"

            # Calculate simple similarity score
            similarity_data = []
            for metric in available_metrics:
                val_a = df_a[metric].iloc[0] if len(df_a) > 0 else 0
                val_b = df_b[metric].iloc[0] if len(df_b) > 0 else 0
                similarity_data.append({
                    'Metric': metric,
                    f'{player_a}': val_a,
                    f'{player_b}': val_b,
                    'Difference': abs(val_a - val_b)
                })

            result_df = pd.DataFrame(similarity_data)
            result: str = result_df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to calculate similarity score: %s", exc)
            return (
                f"Error calculating similarity between "
                f"{player_a} and {player_b}: {exc}"
            )

    async def _park_factors(self, year: int | None, venue: str | None) -> str:
        """Get ballpark factors affecting statistics."""
        try:
            if year is None:
                from datetime import datetime
                year = datetime.now().year

            # In a full implementation, you'd use pybaseball's park factors
            # For now, return a placeholder
            import pandas as pd

            # Sample park factors data
            park_data = {
                'Park': [
                    'Fenway Park', 'Yankee Stadium', 'Coors Field', 'Marlins Park'
                ],
                'Team': ['BOS', 'NYY', 'COL', 'MIA'],
                'HR_Factor': [0.96, 1.31, 1.50, 0.80],
                'Overall_Factor': [1.02, 1.15, 1.25, 0.95]
            }

            df = pd.DataFrame(park_data)

            if venue:
                df = df[df['Park'].str.contains(venue, case=False, na=False)]

            result: str = df.to_csv(sep="\t", index=False)
            return result
        except Exception as exc:
            logger.error("Failed to fetch park factors: %s", exc)
            return f"Error fetching park factors: {exc}"

    async def _list_team_abbreviations(self) -> str:
        """List valid team abbreviations."""
        try:
            # Import the team mapping from our teams loader

            # Define the known team abbreviations
            team_abbreviations = {
                'ARI': 'Arizona Diamondbacks',
                'ATL': 'Atlanta Braves',
                'BAL': 'Baltimore Orioles',
                'BOS': 'Boston Red Sox',
                'CHC': 'Chicago Cubs',
                'CHW': 'Chicago White Sox',
                'CIN': 'Cincinnati Reds',
                'CLE': 'Cleveland Guardians',
                'COL': 'Colorado Rockies',
                'DET': 'Detroit Tigers',
                'HOU': 'Houston Astros',
                'KC': 'Kansas City Royals (also KCR)',
                'LAA': 'Los Angeles Angels',
                'LAD': 'Los Angeles Dodgers',
                'MIA': 'Miami Marlins',
                'MIL': 'Milwaukee Brewers',
                'MIN': 'Minnesota Twins',
                'NYM': 'New York Mets',
                'NYY': 'New York Yankees',
                'OAK': 'Oakland Athletics',
                'PHI': 'Philadelphia Phillies',
                'PIT': 'Pittsburgh Pirates',
                'SD': 'San Diego Padres (also SDP)',
                'SEA': 'Seattle Mariners',
                'SF': 'San Francisco Giants (also SFG)',
                'STL': 'St. Louis Cardinals',
                'TB': 'Tampa Bay Rays (also TBR)',
                'TEX': 'Texas Rangers',
                'TOR': 'Toronto Blue Jays',
                'WSH': 'Washington Nationals (also WSN)',
            }

            # Format as a nice table
            result = "Valid Team Abbreviations:\n"
            result += "=" * 50 + "\n"
            for abbr, name in sorted(team_abbreviations.items()):
                result += f"{abbr:<4} - {name}\n"

            result += (
                "\nNote: Some teams have multiple valid abbreviations "
                "(shown in parentheses)."
            )
            result += "\nExample: Use 'SD' or 'SDP' for San Diego Padres"

            return result
        except Exception as exc:
            logger.error("Failed to list team abbreviations: %s", exc)
            return f"Error listing team abbreviations: {exc}"

    async def run(self) -> None:
        """Run the MCP server."""
        logger.info("Starting Baseball MCP Server")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="baseball-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main() -> None:
    """Main entry point for the baseball MCP server."""
    server = BaseballMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
