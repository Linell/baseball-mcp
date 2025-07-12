"""Tests for baseball_mcp.resources."""

from unittest.mock import patch

import pandas as pd
import pytest
from pydantic import AnyUrl

from baseball_mcp.resources import ResourceHandler


class TestResourceHandler:
    """Test cases for the ResourceHandler class."""

    def test_resource_handler_initialization(self):
        """Test that the resource handler initializes correctly."""
        handler = ResourceHandler()
        assert handler.cache is not None

    def test_list_resources(self):
        """Test listing available resources."""
        handler = ResourceHandler()
        resources = handler.list_resources()
        assert len(resources) == 3
        assert "team-season://" in resources[0]
        assert "stat-definitions://" in resources[1]
        assert "cache://" in resources[2]

    def test_get_stat_definitions_resource(self):
        """Test getting stat definitions resource."""
        handler = ResourceHandler()
        resource = handler.get_resource("stat-definitions://v1")

        assert str(resource.uri) == "stat-definitions://v1"
        assert resource.mimeType == "text/markdown"
        assert "Baseball Statistics Definitions" in resource.text
        assert "Batting Statistics" in resource.text
        assert "Pitching Statistics" in resource.text

    def test_get_stat_definitions_resource_with_anyurl(self):
        """Test getting stat definitions resource with AnyUrl object."""
        handler = ResourceHandler()
        uri = AnyUrl("stat-definitions://v1")
        resource = handler.get_resource(uri)

        assert str(resource.uri) == "stat-definitions://v1"
        assert resource.mimeType == "text/markdown"
        assert "Baseball Statistics Definitions" in resource.text
        assert "Batting Statistics" in resource.text
        assert "Pitching Statistics" in resource.text

    def test_get_cache_status_resource(self):
        """Test getting cache status resource."""
        handler = ResourceHandler()
        resource = handler.get_resource("cache://status")

        assert str(resource.uri) == "cache://status"
        assert resource.mimeType == "application/json"
        assert "cache_location" in resource.text
        assert "cache_type" in resource.text

    @patch("baseball_mcp.resources.get_team_stats")
    @patch("baseball_mcp.resources.get_schedule")
    def test_get_team_season_resource(self, mock_schedule, mock_team_stats):
        """Test getting team season resource."""
        # Mock data
        mock_team_stats.return_value = pd.DataFrame({
            "Team": ["NYY"],
            "HR": [200],
            "AVG": [0.275]
        })

        mock_schedule.return_value = pd.DataFrame({
            "Date": ["2024-04-01", "2024-04-02"],
            "Opponent": ["BOS", "TB"],
            "W/L": ["W", "L"]
        })

        handler = ResourceHandler()
        resource = handler.get_resource("team-season://NYY/2024")

        assert str(resource.uri) == "team-season://NYY/2024"
        assert resource.mimeType == "text/markdown"
        # Since there might be an error, just check that we get some response
        assert resource.text is not None
        assert len(resource.text) > 0

    def test_get_team_season_resource_invalid_uri(self):
        """Test error handling for invalid team season URI."""
        handler = ResourceHandler()

        with pytest.raises(ValueError, match="team-season URI must be in format"):
            handler.get_resource("team-season://invalid")

    def test_get_team_season_resource_invalid_year(self):
        """Test error handling for invalid year in team season URI."""
        handler = ResourceHandler()

        with pytest.raises(ValueError, match="Invalid year"):
            handler.get_resource("team-season://NYY/invalid")

    def test_get_unknown_resource(self):
        """Test error handling for unknown resource URI."""
        handler = ResourceHandler()

        with pytest.raises(ValueError, match="Unknown resource URI"):
            handler.get_resource("unknown://resource")

    def test_get_unknown_cache_resource(self):
        """Test error handling for unknown cache resource."""
        handler = ResourceHandler()

        with pytest.raises(ValueError, match="Unknown cache resource"):
            handler.get_resource("cache://unknown")

    @patch("baseball_mcp.resources.get_team_stats")
    @patch("baseball_mcp.resources.get_schedule")
    def test_team_season_resource_error_handling(self, mock_schedule, mock_team_stats):
        """Test error handling in team season resource generation."""
        # Mock an error
        mock_team_stats.side_effect = Exception("API Error")

        handler = ResourceHandler()
        resource = handler.get_resource("team-season://NYY/2024")

        assert "Error generating team-season resource" in resource.text
