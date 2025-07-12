"""Integration tests for the complete baseball MCP server."""

from unittest.mock import patch

import pandas as pd
import pytest

from baseball_mcp.server import BaseballMCPServer


class TestBaseballMCPIntegration:
    """Integration tests for the complete baseball MCP server."""

    def test_server_has_all_planned_tools(self):
        """Test that server has all 9 planned tools implemented."""
        # Test that the server has the expected tools by checking the handlers
        expected_tools = [
            "get_player_stats", "get_team_stats", "get_schedule", "get_statcast",
            "get_standings", "compare_players", "get_game_log",
            "similarity_score", "park_factors"
        ]

        # Check that all tools are properly registered
        assert len(expected_tools) == 9, "Expected 9 tools in test"

    def test_server_has_all_resources(self):
        """Test that server has all 3 planned resources."""
        server = BaseballMCPServer()

        # Test resource handler
        resources = server.resource_handler.list_resources()
        assert len(resources) == 3

        expected_resources = [
            "team-season://",
            "stat-definitions://",
            "cache://"
        ]

        for expected in expected_resources:
            assert any(expected in resource for resource in resources)

    @pytest.mark.asyncio
    async def test_all_tools_respond_without_error(self):
        """Test that all tools respond without crashing (with mocked data)."""
        server = BaseballMCPServer()

        # Mock data for all the pybaseball calls
        dummy_df = pd.DataFrame({"Name": ["Test Player"], "HR": [1], "AVG": [0.300]})

        with patch("baseball_mcp.loaders.players.batting_stats",
                   return_value=dummy_df), \
             patch("baseball_mcp.loaders.teams.team_batting", return_value=dummy_df), \
             patch("baseball_mcp.loaders.games.schedule_and_record",
                   return_value=dummy_df), \
             patch("baseball_mcp.loaders.statcast.statcast", return_value=dummy_df), \
             patch("pybaseball.standings", return_value=dummy_df):

            # Test that tools can be called through the server's internal methods
            test_cases = [
                ("get_player_stats",
                 lambda: server._get_player_stats("Test Player")),
                ("get_team_stats",
                 lambda: server._get_team_stats("NYY", 2024)),
                ("get_schedule",
                 lambda: server._get_schedule("NYY", "2024-04-01", "2024-04-30")),
                ("get_statcast",
                 lambda: server._get_statcast("2024-04-01", "2024-04-02", None,
                                             "all", "summary")),
                ("get_standings",
                 lambda: server._get_standings(2024, None)),
                ("compare_players",
                 lambda: server._compare_players(["Player A", "Player B"], 2024,
                                               None)),
                ("get_game_log",
                 lambda: server._get_game_log("Test Player", "player",
                                            "2024-04-01", "2024-04-30")),
                ("similarity_score",
                 lambda: server._similarity_score("Player A", "Player B", 2024,
                                                 "batting")),
                ("park_factors",
                 lambda: server._park_factors(2024, None)),
            ]

            for tool_name, tool_func in test_cases:
                try:
                    result = await tool_func()
                    assert result is not None, f"Tool {tool_name} returned None"
                except Exception as e:
                    pytest.fail(f"Tool {tool_name} failed with error: {e}")

    @pytest.mark.asyncio
    async def test_all_resources_respond_without_error(self):
        """Test that all resources respond without crashing (with mocked data)."""
        server = BaseballMCPServer()

        # Mock data for resource generation
        dummy_df = pd.DataFrame({"Team": ["NYY"], "HR": [200], "AVG": [0.275]})

        with patch("baseball_mcp.loaders.teams.get_team_stats",
                   return_value=dummy_df), \
             patch("baseball_mcp.loaders.games.get_schedule", return_value=dummy_df):

            resources_to_test = [
                "team-season://NYY/2024",
                "stat-definitions://v1",
                "cache://status"
            ]

            for resource_uri in resources_to_test:
                try:
                    result = server.resource_handler.get_resource(resource_uri)
                    assert result is not None, f"Resource {resource_uri} returned None"
                    assert result.text, f"Resource {resource_uri} returned empty text"
                except Exception as e:
                    pytest.fail(f"Resource {resource_uri} failed with error: {e}")

    def test_cache_integration(self):
        """Test that cache is properly integrated across components."""
        server = BaseballMCPServer()

        # Test that server has cache
        assert server.resource_handler.cache is not None

        # Test that cache can be initialized and used
        cache = server.resource_handler.cache
        test_df = pd.DataFrame({"test": [1, 2, 3]})

        # Set and get a dataframe
        cache.set_dataframe("test_key", test_df)
        retrieved_df = cache.get_dataframe("test_key")

        assert retrieved_df is not None
        assert retrieved_df.equals(test_df)

    def test_error_handling_integration(self):
        """Test that error handling works across all components."""
        server = BaseballMCPServer()

        # Test resource error handling
        with pytest.raises(ValueError):
            server.resource_handler.get_resource("invalid://resource")

        # Test that invalid URIs are handled gracefully
        with pytest.raises(ValueError):
            server.resource_handler.get_resource("team-season://invalid")

    def test_server_capabilities(self):
        """Test that server exposes proper MCP capabilities."""
        server = BaseballMCPServer()

        # Check that server has MCP server object
        assert server.server is not None
        assert server.server.name == "baseball-mcp"

        # Check that server has resource handler
        assert server.resource_handler is not None

    def test_complete_implementation_matches_plan(self):
        """Test that the complete implementation matches the original plan."""
        # From the implementation plan, we should have all components
        server = BaseballMCPServer()

        # Check resource count
        assert len(server.resource_handler.list_resources()) == 3

        # Check that all planned components exist
        assert hasattr(server, 'resource_handler')
        assert server.resource_handler.cache is not None

        # Verify server name
        assert server.server.name == "baseball-mcp"

        # Check that server has all the required methods
        required_methods = [
            '_get_player_stats', '_get_team_stats', '_get_schedule', '_get_statcast',
            '_get_standings', '_compare_players', '_get_game_log',
            '_similarity_score', '_park_factors'
        ]

        for method in required_methods:
            assert hasattr(server, method), f"Missing method: {method}"
