"""Baseball MCP Server implementation."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseballMCPServer:
    """Baseball MCP Server for retrieving baseball information."""

    def __init__(self) -> None:
        """Initialize the baseball MCP server."""
        self.server = Server("baseball-mcp")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up the MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
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
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]]
        ) -> List[TextContent]:
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
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=str(result))]

            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_player_stats(
        self, player_name: str, year: Optional[int] = None
    ) -> str:
        """Get player statistics (placeholder implementation)."""
        # TODO: Implement using pybaseball
        return f"Player stats for {player_name}" + (f" in {year}" if year else "")

    async def _get_team_stats(self, team: str, year: int) -> str:
        """Get team statistics (placeholder implementation)."""
        # TODO: Implement using pybaseball
        return f"Team stats for {team} in {year}"

    async def _get_schedule(self, team: str, start_date: str, end_date: str) -> str:
        """Get game schedule (placeholder implementation)."""
        # TODO: Implement using pybaseball
        return f"Schedule for {team} from {start_date} to {end_date}"

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
