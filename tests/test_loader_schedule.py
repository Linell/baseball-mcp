"""Tests for baseball_mcp.loaders.games schedule loader."""

from unittest.mock import patch

import pandas as pd

from baseball_mcp.cache import Cache
from baseball_mcp.loaders.games import _parse_schedule_dates, get_schedule


def test_get_schedule_fetch_and_cache():
    # Create dummy schedule DataFrame covering April 2024
    dates = pd.date_range("2024-04-01", "2024-04-05", freq="D")
    dummy_df = pd.DataFrame({
        "Date": dates,
        "Team": ["ATL"] * len(dates),
        "Opp": ["NYM", "MIA", "PHI", "PHI", "NYM"],
    })

    patch_target = "baseball_mcp.loaders.games.schedule_and_record"
    with patch(patch_target, return_value=dummy_df) as mock_sched:
        cache = Cache(db_path=":memory:")
        df1 = get_schedule("ATL", "2024-04-01", "2024-04-05", cache=cache)
        assert len(df1) == 5
        df2 = get_schedule("ATL", "2024-04-01", "2024-04-05", cache=cache)
        assert df2.equals(df1)
        assert mock_sched.call_count == 1


def test_parse_schedule_dates_with_incomplete_formats():
    """Test _parse_schedule_dates handles incomplete date formats from pybaseball."""

    # Test data with incomplete date formats (like from pybaseball)
    test_dates = pd.Series([
        "Thursday, Mar 27",
        "Friday, Mar 28",
        "Saturday, Apr 5",
        "Sunday, Oct 6",
        "2024-03-27",  # Complete date
        "",  # Empty string
        pd.NaT,  # NaT value
    ])

    # Parse with season 2025
    result = _parse_schedule_dates(test_dates, 2025)

    # Check that all valid dates were parsed
    assert not pd.isna(result[0])  # "Thursday, Mar 27" -> parsed
    assert not pd.isna(result[1])  # "Friday, Mar 28" -> parsed
    assert not pd.isna(result[2])  # "Saturday, Apr 5" -> parsed
    assert not pd.isna(result[3])  # "Sunday, Oct 6" -> parsed
    assert not pd.isna(result[4])  # "2024-03-27" -> parsed
    assert pd.isna(result[5])      # "" -> NaT
    assert pd.isna(result[6])      # NaT -> NaT

    # Check that the year was correctly inferred for incomplete dates
    assert result[0].year == 2025
    assert result[1].year == 2025
    assert result[2].year == 2025
    assert result[3].year == 2025

    # Check that complete dates preserve their year
    assert result[4].year == 2024


def test_get_schedule_with_incomplete_date_formats():
    """Test get_schedule handles incomplete date formats from pybaseball."""

    # Create dummy schedule DataFrame with incomplete date formats
    dummy_df = pd.DataFrame({
        "Date": ["Thursday, Mar 27", "Friday, Mar 28", "Saturday, Mar 29"],
        "Team": ["SD"] * 3,
        "Opp": ["LAD", "SF", "COL"],
    })

    patch_target = "baseball_mcp.loaders.games.schedule_and_record"
    with patch(patch_target, return_value=dummy_df) as mock_sched:
        cache = Cache(db_path=":memory:")
        df = get_schedule("SD", "2025-03-01", "2025-03-31", cache=cache)

        # Should successfully parse and return games
        assert len(df) == 3
        assert pd.api.types.is_datetime64_any_dtype(df["Date"])
        assert all(df["Date"].dt.year == 2025)
        assert mock_sched.call_count == 1
