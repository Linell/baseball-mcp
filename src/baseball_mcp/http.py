"""HTTP server implementation for MCP over HTTP."""

import logging
import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import parse_qs

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from baseball_mcp.server import BaseballMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JsonRpcRequest(BaseModel):
    """JSON-RPC request model."""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(description="Method name")
    params: Optional[Dict[str, Any]] = Field(
        default=None, description="Method parameters"
    )
    id: Optional[Union[int, str]] = Field(default=None, description="Request ID")


class JsonRpcResponse(BaseModel):
    """JSON-RPC response model."""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    result: Optional[Any] = Field(default=None, description="Method result")
    error: Optional[Dict[str, Any]] = Field(default=None, description="Error object")
    id: Optional[Union[int, str]] = Field(default=None, description="Request ID")


class HTTPServer:
    """HTTP server for MCP over HTTP."""

    def __init__(self) -> None:
        """Initialize the HTTP server."""
        self.app = FastAPI(
            title="Baseball MCP Server",
            description="A Model Context Protocol server for baseball data",
            version="0.1.0",
        )
        self.mcp_server = BaseballMCPServer()
        self._setup_routes()

    def _parse_config_from_query(self, query_string: str) -> Dict[str, Any]:
        """Parse configuration from query parameters using dot-notation."""
        if not query_string:
            return {}

        config: Dict[str, Any] = {}
        params = parse_qs(query_string)

        for key, values in params.items():
            if not values:
                continue

            raw_value = values[0]  # Take first value

            # Convert boolean strings
            if raw_value.lower() in ('true', 'false'):
                value: Union[str, bool, int, float] = raw_value.lower() == 'true'
            # Convert numeric strings
            elif raw_value.isdigit():
                value = int(raw_value)
            elif raw_value.replace('.', '', 1).isdigit():
                value = float(raw_value)
            else:
                value = raw_value

            # Handle dot notation (e.g., server.host=localhost)
            if "." in key:
                parts = key.split(".")
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                config[key] = value

        # Log configuration for debugging
        if config:
            logger.info(f"Parsed configuration: {config}")

        return config

    def _setup_routes(self) -> None:
        """Set up HTTP routes."""

        @self.app.get("/mcp")
        async def handle_mcp_get(request: Request) -> JSONResponse:
            """Handle GET requests to /mcp endpoint."""
            # GET can be used for health checks or initial handshake
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": True},
                            "resources": {"listChanged": True},
                            "prompts": {"listChanged": True},
                        },
                        "serverInfo": {"name": "baseball-mcp", "version": "0.1.0"},
                    },
                    "id": 1,
                }
            )

        @self.app.post("/mcp")
        async def handle_mcp_post(request: Request) -> JSONResponse:
            """Handle POST requests to /mcp endpoint."""
            try:
                # Parse configuration from query parameters
                config = self._parse_config_from_query(request.url.query)

                # Get JSON-RPC request
                body = await request.json()
                json_request = JsonRpcRequest(**body)

                # Handle the JSON-RPC request
                result = await self._handle_jsonrpc_request(json_request, config)

                return JSONResponse(result.model_dump(exclude_none=True))

            except Exception as e:
                logger.error(f"Error handling MCP POST request: {e}")
                return JSONResponse(
                    JsonRpcResponse(
                        error={
                            "code": -32603,
                            "message": "Internal error",
                            "data": str(e),
                        },
                        id=body.get("id") if "body" in locals() else None,
                    ).model_dump(exclude_none=True),
                    status_code=500,
                )

        @self.app.delete("/mcp")
        async def handle_mcp_delete(request: Request) -> JSONResponse:
            """Handle DELETE requests to /mcp endpoint."""
            # For session cleanup or termination
            return JSONResponse(
                {"jsonrpc": "2.0", "result": {"status": "terminated"}, "id": 1}
            )

        @self.app.get("/health")
        async def health_check() -> Dict[str, str]:
            """Health check endpoint."""
            return {"status": "healthy"}

    async def _handle_jsonrpc_request(
        self, request: JsonRpcRequest, config: Dict[str, Any]
    ) -> JsonRpcResponse:
        """Handle JSON-RPC request."""
        try:
            method = request.method
            params = request.params or {}
            result: Any = None

            # Apply configuration settings
            if config.get("log_level"):
                log_level = getattr(logging, config["log_level"].upper(), logging.INFO)
                logger.setLevel(log_level)

            if method == "initialize":
                # Initialize connection
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"listChanged": True},
                        "prompts": {"listChanged": True},
                    },
                    "serverInfo": {"name": "baseball-mcp", "version": "0.1.0"},
                }

            elif method == "tools/list":
                # List available tools - implement lazy loading
                tools = await self._get_tools_list()
                result = {"tools": tools}

            elif method == "tools/call":
                # Call a tool - this is where we would validate configuration
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if not tool_name:
                    raise ValueError("Tool name is required")

                # Here you could validate API keys from config if needed
                # For now, we'll just call the tool
                result = await self._call_tool(tool_name, arguments)

            elif method == "resources/list":
                # List available resources
                resources = await self._get_resources_list()
                result = {"resources": resources}

            elif method == "resources/read":
                # Read a resource
                uri = params.get("uri")
                if not uri:
                    raise ValueError("Resource URI is required")
                content = await self._read_resource(uri)
                result = {"contents": [content]}

            elif method == "prompts/list":
                # List available prompts
                prompts = await self._get_prompts_list()
                result = {"prompts": prompts}

            elif method == "prompts/get":
                # Get a prompt
                name = params.get("name")
                arguments = params.get("arguments", {})
                if not name:
                    raise ValueError("Prompt name is required")
                prompt_result = await self._get_prompt(name, arguments)
                result = prompt_result

            else:
                raise ValueError(f"Unknown method: {method}")

            return JsonRpcResponse(result=result, id=request.id)

        except Exception as e:
            logger.error(f"Error handling JSON-RPC method {request.method}: {e}")
            return JsonRpcResponse(
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e),
                },
                id=request.id,
            )

    async def _call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool and return the result."""
        try:
            if name == "get_player_stats":
                player_name = arguments.get("player_name")
                if not player_name:
                    raise ValueError("player_name is required")
                year = arguments.get("year")
                result = await self.mcp_server._get_player_stats(player_name, year)
            elif name == "get_team_stats":
                team = arguments.get("team")
                year = arguments.get("year")
                if not team or not year:
                    raise ValueError("team and year are required")
                result = await self.mcp_server._get_team_stats(team, year)
            elif name == "get_schedule":
                team = arguments.get("team")
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                if not team or not start_date or not end_date:
                    raise ValueError("team, start_date, and end_date are required")
                result = await self.mcp_server._get_schedule(team, start_date, end_date)
            elif name == "get_statcast":
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                if not start_date or not end_date:
                    raise ValueError("start_date and end_date are required")
                player_id = arguments.get("player_id")
                statcast_type = arguments.get("statcast_type")
                format_type = arguments.get("format_type")
                result = await self.mcp_server._get_statcast(
                    start_date,
                    end_date,
                    player_id,
                    statcast_type or "all",
                    format_type or "summary"
                )
            elif name == "get_standings":
                year = arguments.get("year")
                if not year:
                    raise ValueError("year is required")
                date = arguments.get("date")
                result = await self.mcp_server._get_standings(year, date)
            elif name == "compare_players":
                players = arguments.get("players")
                if not players:
                    raise ValueError("players list is required")
                year = arguments.get("year")
                metric = arguments.get("metric")
                result = await self.mcp_server._compare_players(players, year, metric)
            elif name == "get_game_log":
                entity = arguments.get("entity")
                if not entity:
                    raise ValueError("entity is required")
                entity_type = arguments.get("entity_type", "player")
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                if not start_date or not end_date:
                    raise ValueError("start_date and end_date are required")
                result = await self.mcp_server._get_game_log(
                    entity, entity_type, start_date, end_date
                )
            elif name == "similarity_score":
                player_a = arguments.get("player_a")
                player_b = arguments.get("player_b")
                if not player_a or not player_b:
                    raise ValueError("player_a and player_b are required")
                year = arguments.get("year")
                metric_set = arguments.get("metric_set")
                result = await self.mcp_server._similarity_score(
                    player_a, player_b, year, metric_set or "batting"
                )
            elif name == "park_factors":
                year = arguments.get("year")
                venue = arguments.get("venue")
                result = await self.mcp_server._park_factors(year, venue)
            elif name == "list_team_abbreviations":
                result = await self.mcp_server._list_team_abbreviations()
            else:
                raise ValueError(f"Unknown tool: {name}")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result),
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}",
                    }
                ],
                "isError": True,
            }

    async def _read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource."""
        try:
            # Use the resource handler from the MCP server
            content = self.mcp_server.resource_handler.get_resource(uri)
            return {"uri": uri, "mimeType": "text/plain", "text": content}
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return {"uri": uri, "mimeType": "text/plain", "text": f"Error: {str(e)}"}

    async def _get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get a prompt."""
        try:
            # Simple prompt implementation
            if name == "analyze_player_performance":
                player_name = arguments.get("player_name", "Player")
                year = arguments.get("year", "2024")
                prompt = f"Analyze the performance of {player_name} in {year}. "
                prompt += (
                    "Include batting average, home runs, RBIs, "
                    "and any notable achievements."
                )
                return {
                    "description": prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": {"type": "text", "text": prompt}
                        }
                    ]
                }
            elif name == "compare_team_seasons":
                team = arguments.get("team", "Team")
                years = arguments.get("years", "2023,2024")
                prompt = (
                    f"Compare the performance of {team} across these seasons: {years}. "
                )
                prompt += "Include wins, losses, key statistics, and notable changes."
                return {
                    "description": prompt,
                    "messages": [
                        {
                            "role": "user",
                            "content": {"type": "text", "text": prompt}
                        }
                    ]
                }
            else:
                raise ValueError(f"Unknown prompt: {name}")
        except Exception as e:
            logger.error(f"Error getting prompt {name}: {e}")
            return {"description": f"Error: {str(e)}", "messages": []}

    async def _get_tools_list(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        # This implements lazy loading - tools are listed without authentication
        return [
            {
                "name": "get_player_stats",
                "description": "Get player statistics for a specific player",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "player_name": {
                            "type": "string",
                            "description": "Name of the player"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year for statistics (optional)",
                            "minimum": 1871
                        }
                    },
                    "required": ["player_name"]
                }
            },
            {
                "name": "get_team_stats",
                "description": "Get team statistics for a specific team and year",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "team": {
                            "type": "string",
                            "description": "Team abbreviation (e.g., 'NYY', 'BOS')"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year for statistics",
                            "minimum": 1871
                        }
                    },
                    "required": ["team", "year"]
                }
            },
            {
                "name": "get_schedule",
                "description": "Get game schedule for a team and date range",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "team": {
                            "type": "string",
                            "description": "Team abbreviation"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)"
                        }
                    },
                    "required": ["team", "start_date", "end_date"]
                }
            },
            {
                "name": "get_statcast",
                "description": "Get Statcast data for a date range",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)"
                        },
                        "player_id": {
                            "type": "integer",
                            "description": "Optional player ID for filtering"
                        },
                        "statcast_type": {
                            "type": "string",
                            "enum": ["all", "batter", "pitcher"],
                            "description": "Type of Statcast data",
                            "default": "all"
                        },
                        "format_type": {
                            "type": "string",
                            "enum": ["summary", "parquet"],
                            "description": "Format of returned data",
                            "default": "summary"
                        }
                    },
                    "required": ["start_date", "end_date"]
                }
            },
            {
                "name": "get_standings",
                "description": "Get division and league standings",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "integer",
                            "description": "Year for standings",
                            "minimum": 1871
                        },
                        "date": {
                            "type": "string",
                            "description": (
                                "Optional date (YYYY-MM-DD) for standings "
                                "on specific date"
                            )
                        }
                    },
                    "required": ["year"]
                }
            },
            {
                "name": "compare_players",
                "description": "Compare statistics between multiple players",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "players": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of player names to compare",
                            "minItems": 2
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year for comparison",
                            "minimum": 1871
                        },
                        "metric": {
                            "type": "string",
                            "description": "Specific metric to focus on (optional)"
                        }
                    },
                    "required": ["players", "year"]
                }
            },
            {
                "name": "get_game_log",
                "description": "Get game-by-game log for a player or team",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "entity": {
                            "type": "string",
                            "description": "Player name or team abbreviation"
                        },
                        "entity_type": {
                            "type": "string",
                            "enum": ["player", "team"],
                            "description": "Type of entity",
                            "default": "player"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)"
                        }
                    },
                    "required": ["entity", "start_date", "end_date"]
                }
            },
            {
                "name": "similarity_score",
                "description": "Calculate sabermetric similarity between two players",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "player_a": {
                            "type": "string",
                            "description": "First player name"
                        },
                        "player_b": {
                            "type": "string",
                            "description": "Second player name"
                        },
                        "year": {
                            "type": "integer",
                            "description": "Year for comparison",
                            "minimum": 1871
                        },
                        "metric_set": {
                            "type": "string",
                            "enum": ["batting", "pitching", "all"],
                            "description": "Set of metrics to use for similarity",
                            "default": "batting"
                        }
                    },
                    "required": ["player_a", "player_b", "year"]
                }
            },
            {
                "name": "park_factors",
                "description": "Get ballpark factors affecting statistics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "integer",
                            "description": "Year for park factors",
                            "minimum": 1871
                        },
                        "venue": {
                            "type": "string",
                            "description": "Specific venue name (optional)"
                        }
                    },
                    "required": ["year"]
                }
            },
            {
                "name": "list_team_abbreviations",
                "description": "List valid team abbreviations",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    async def _get_resources_list(self) -> List[Dict[str, Any]]:
        """Get list of available resources."""
        return [
            {
                "uri": "baseball://leagues",
                "name": "MLB Leagues",
                "description": "Information about MLB leagues and divisions",
                "mimeType": "text/plain"
            },
            {
                "uri": "baseball://teams",
                "name": "MLB Teams",
                "description": "Information about MLB teams and abbreviations",
                "mimeType": "text/plain"
            },
            {
                "uri": "baseball://stats/glossary",
                "name": "Statistics Glossary",
                "description": "Glossary of baseball statistics and their meanings",
                "mimeType": "text/plain"
            }
        ]

    async def _get_prompts_list(self) -> List[Dict[str, Any]]:
        """Get list of available prompts."""
        return [
            {
                "name": "analyze_player_performance",
                "description": "Analyze a player's performance over a season",
                "arguments": [
                    {
                        "name": "player_name",
                        "description": "Name of the player to analyze",
                        "required": True
                    },
                    {
                        "name": "year",
                        "description": "Year to analyze",
                        "required": True
                    }
                ]
            },
            {
                "name": "compare_team_seasons",
                "description": "Compare team performance across multiple seasons",
                "arguments": [
                    {
                        "name": "team",
                        "description": "Team abbreviation",
                        "required": True
                    },
                    {
                        "name": "years",
                        "description": "Years to compare (comma-separated)",
                        "required": True
                    }
                ]
            }
        ]

    def run(self, host: str = "0.0.0.0", port: int = 3000) -> None:
        """Run the HTTP server."""
        # Use PORT environment variable if set
        port = int(os.environ.get("PORT", port))

        logger.info(f"Starting Baseball MCP HTTP server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")


# Create the application instance
server = HTTPServer()
app = server.app


def main() -> None:
    """Main entry point for the HTTP server."""
    try:
        # Use PORT environment variable if set
        port = int(os.environ.get("PORT", 3000))
        host = os.environ.get("HOST", "0.0.0.0")

        logger.info(f"Starting Baseball MCP HTTP server on {host}:{port}")

        # Create server instance
        server = HTTPServer()

        # Run with explicit configuration for better compatibility
        uvicorn.run(
            server.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            timeout_keep_alive=30,
            timeout_graceful_shutdown=30
        )
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        raise


if __name__ == "__main__":
    main()
