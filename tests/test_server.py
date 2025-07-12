"""Tests for the baseball MCP server."""

import pytest

from baseball_mcp.server import BaseballMCPServer


class TestBaseballMCPServer:
    """Test cases for the BaseballMCPServer class."""

    def test_server_initialization(self):
        """Test that the server initializes correctly."""
        server = BaseballMCPServer()
        assert server.server is not None
        assert server.server.name == "baseball-mcp"

    @pytest.mark.asyncio
    async def test_get_player_stats(self, monkeypatch):
        """Test player stats retrieval via loader with patched pybaseball."""
        import pandas as pd

        dummy_df = pd.DataFrame({"Name": ["Test Player"], "AVG": [0.300]})
        monkeypatch.setattr(
            "baseball_mcp.loaders.players.batting_stats", lambda year: dummy_df
        )

        server = BaseballMCPServer()
        result = await server._get_player_stats("Test Player", 2024)
        assert "Test Player" in result

    @pytest.mark.asyncio
    async def test_get_team_stats(self, monkeypatch):
        """Test team stats retrieval via loader patch."""

        import pandas as pd

        dummy_df = pd.DataFrame({"Team": ["NYY"], "HR": [200]})
        monkeypatch.setattr(
            "baseball_mcp.server._load_team_stats",
            lambda team, year: dummy_df,
        )

        server = BaseballMCPServer()
        result = await server._get_team_stats("NYY", 2024)
        assert "NYY" in result

    @pytest.mark.asyncio
    async def test_get_schedule(self, monkeypatch):
        """Test schedule retrieval via loader patch."""

        import pandas as pd

        dates = pd.date_range("2024-04-01", "2024-04-05", freq="D")
        dummy_df = pd.DataFrame({"Date": dates, "Team": ["ATL"] * len(dates)})
        monkeypatch.setattr(
            "baseball_mcp.server._load_schedule",
            lambda team, start, end: dummy_df,
        )

        server = BaseballMCPServer()
        res = await server._get_schedule("ATL", "2024-04-01", "2024-04-05")
        assert "ATL" in res
        assert "2024-04-01" in res
        assert "2024-04-05" in res

    def test_server_has_required_methods(self):
        """Test that the server has all required methods."""
        server = BaseballMCPServer()
        assert hasattr(server, "_get_player_stats")
        assert hasattr(server, "_get_team_stats")
        assert hasattr(server, "_get_schedule")
        assert hasattr(server, "run")


# TODO: Add integration tests once the actual baseball data functionality is implemented
# TODO: Add tests for MCP protocol compliance
# TODO: Add tests for error handling
# TODO: Add tests for data validation
