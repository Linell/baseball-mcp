"""Tests for baseball_mcp.loaders.statcast."""

from unittest.mock import patch

import pandas as pd
import pytest

from baseball_mcp.cache import Cache
from baseball_mcp.loaders.statcast import get_statcast


def test_get_statcast_fetch_and_cache():
    """Test fetching and caching Statcast data."""
    dummy_df = pd.DataFrame({
        "game_date": ["2024-04-01", "2024-04-01"],
        "player_name": ["Player A", "Player B"],
        "launch_speed": [95.0, 102.5],
        "launch_angle": [25.0, 15.0],
        "pitch_type": ["FF", "CH"]
    })

    patch_target = "baseball_mcp.loaders.statcast.statcast"
    with patch(patch_target, return_value=dummy_df) as mock_statcast:
        cache = Cache(db_path=":memory:")

        # First call should fetch data
        df1 = get_statcast("2024-04-01", "2024-04-02", cache=cache)
        assert not df1.empty

        # Second call should hit cache
        df2 = get_statcast("2024-04-01", "2024-04-02", cache=cache)
        assert df2.equals(df1)
        assert mock_statcast.call_count == 1


def test_get_statcast_player_specific():
    """Test fetching player-specific Statcast data."""
    dummy_df = pd.DataFrame({
        "game_date": ["2024-04-01"],
        "player_name": ["Mike Trout"],
        "launch_speed": [105.0],
        "launch_angle": [20.0],
        "pitch_type": ["FF"]
    })

    patch_target = "baseball_mcp.loaders.statcast.statcast_batter"
    with patch(patch_target, return_value=dummy_df) as mock_statcast:
        cache = Cache(db_path=":memory:")

        df = get_statcast(
            "2024-04-01", "2024-04-02",
            player_id=545361,
            statcast_type="batter",
            cache=cache
        )
        assert not df.empty
        assert mock_statcast.call_count == 1


def test_get_statcast_date_validation():
    """Test date validation in Statcast loader."""
    cache = Cache(db_path=":memory:")

    # Test invalid date order
    with pytest.raises(ValueError, match="end_date must be on or after start_date"):
        get_statcast("2024-04-02", "2024-04-01", cache=cache)

    # Test missing dates
    with pytest.raises(ValueError, match="Both start_date and end_date are required"):
        get_statcast("", "2024-04-01", cache=cache)


def test_get_statcast_summary_format():
    """Test summary format functionality."""
    dummy_df = pd.DataFrame({
        "game_date": ["2024-04-01", "2024-04-01", "2024-04-02"],
        "player_name": ["Player A", "Player A", "Player A"],
        "launch_speed": [95.0, 102.5, 88.0],
        "launch_angle": [25.0, 15.0, 35.0],
        "pitch_type": ["FF", "CH", "CB"]
    })

    patch_target = "baseball_mcp.loaders.statcast.statcast"
    with patch(patch_target, return_value=dummy_df):
        cache = Cache(db_path=":memory:")

        df = get_statcast(
            "2024-04-01", "2024-04-02",
            format_type="summary",
            cache=cache
        )
        # Should have aggregated data
        assert not df.empty


def test_get_statcast_error_handling():
    """Test error handling in Statcast loader."""
    patch_target = "baseball_mcp.loaders.statcast.statcast"
    with patch(patch_target, side_effect=Exception("API Error")):
        cache = Cache(db_path=":memory:")

        # Should return empty DataFrame on error
        df = get_statcast("2024-04-01", "2024-04-02", cache=cache)
        assert df.empty
