# Baseball MCP Server

A Model Context Protocol (MCP) server for retrieving baseball information using the [pybaseball](https://github.com/jldbc/pybaseball) library.

> Baseball Reference, Baseball Savant, and FanGraphs so you don't have to.

## Overview

This MCP server provides access to comprehensive baseball data through a standardized interface. It leverages the `pybaseball` library to fetch statistics, game information, and player data from various baseball databases.

The primary purpose is to make baseball analysis easy, with a particular focus on fantasy baseball.

## Features

- Player statistics retrieval
- Team performance data  
- Game schedules and results
- Statcast pitch-by-pitch data
- League standings
- Player comparison tools
- Game logs for players and teams
- Sabermetric similarity scoring
- Ballpark factor analysis
- MCP Resources for comprehensive data packages
- SQLite caching for performance
- Both STDIO and HTTP server transports

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Linell/baseball-mcp.git
cd baseball-mcp
```

2. Install the package:
```bash
pip install -e .
```

Or for development:
```bash
pip install -e ".[dev]"
```

## Usage

### Running the Server

Run the STDIO server (default):
```bash
baseball-mcp run
```

Run the HTTP server on port 8000:
```bash
baseball-mcp http --port 8000
```

Reset the on-disk cache:
```bash
baseball-mcp cache-reset --confirm
```

### Available Tools

| Tool | Summary | Parameters |
|------|---------|------------|
| `get_player_stats` | Season or career stats for a single player | `player_name` (required), `year` (optional) |
| `get_team_stats` | Team-level splits by season | `team` (required), `year` (required) |
| `get_schedule` | Games for a team in a date range | `team` (required), `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD) |
| `get_statcast` | Pitch-by-pitch Statcast data | `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD), `player_id` (optional), `statcast_type` (optional), `format_type` (optional) |
| `get_standings` | Division and league standings | `year` (required), `date` (optional) |
| `compare_players` | Side-by-side player comparison | `players` (list), `year` (required), `metric` (optional) |
| `get_game_log` | Game-by-game logs for players/teams | `entity` (required), `entity_type` (optional), `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD) |
| `similarity_score` | Sabermetric similarity between players | `player_a` (required), `player_b` (required), `year` (required), `metric_set` (optional) |
| `park_factors` | Ballpark factors affecting stats | `year` (required), `venue` (optional) |
| `list_team_abbreviations` | List valid team abbreviations | None |

### Example Usage

- "Get Mike Trout's 2023 stats" → uses `get_player_stats`
- "Show me the Yankees' 2024 team statistics" → uses `get_team_stats`  
- "What's the Padres' schedule for March 2025?" → uses `get_schedule`
- "Get Statcast data for Aaron Judge from June 1-7, 2024" → uses `get_statcast`
- "Show me the 2024 AL East standings" → uses `get_standings`
- "Compare Mike Trout and Aaron Judge's 2024 stats" → uses `compare_players`

### Team Abbreviations

The server supports various team abbreviations for convenience:

- **San Diego Padres**: `SD` or `SDP`
- **San Francisco Giants**: `SF` or `SFG`
- **Tampa Bay Rays**: `TB` or `TBR`
- **Kansas City Royals**: `KC` or `KCR`
- **Chicago White Sox**: `CWS` or `CHW`
- **Washington Nationals**: `WSH` or `WSN`

For a complete list, use the `list_team_abbreviations` tool.

## Development

### Setting up Development Environment

1. Clone the repository
2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Quality

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting and code analysis
- **MyPy**: Type checking
- **Pre-commit**: Git hooks for code quality

Run all checks:
```bash
black src tests
ruff check src tests
mypy src
```

## Configuration

### Cache

The server uses SQLite for caching baseball data to improve performance and reduce API calls.

- **Default location**: `~/.config/baseball-mcp/baseball.db`
- **Management**: Data is automatically cached when first requested
- **Reset**: Use `baseball-mcp cache-reset --confirm` to clear all cached data

### Server Modes

- **STDIO Mode** (default): Runs as an MCP server for local AI clients
- **HTTP Mode**: Runs as an HTTP server for remote access (`baseball-mcp http --port 8000`)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [pybaseball](https://github.com/jldbc/pybaseball) for providing the baseball data interface
- [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) for the MCP framework

## Resources

- [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [pybaseball Documentation](https://github.com/jldbc/pybaseball/tree/master/docs)
- [Statcast CSV Documentation](https://baseballsavant.mlb.com/csv-docs)