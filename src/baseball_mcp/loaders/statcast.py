"""Data loader for Statcast data."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

import pandas as pd
from pybaseball import statcast, statcast_batter, statcast_pitcher

from baseball_mcp.cache import Cache

StatcastType = Literal["all", "batter", "pitcher"]
StatcastFormat = Literal["summary", "parquet"]


def _cache_key(
    start_date: str,
    end_date: str,
    player_id: int | None = None,
    statcast_type: StatcastType = "all",
) -> str:
    """Generate cache key for Statcast data."""
    player_part = f":{player_id}" if player_id else ""
    return f"statcast:{statcast_type}:{start_date}:{end_date}{player_part}"


def _parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    return datetime.strptime(date_str, "%Y-%m-%d")


def _summarize_statcast(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize Statcast data by game date and basic metrics."""
    if df.empty:
        return df

    # Group by game date and calculate summary stats
    summary_cols = [
        "game_date",
        "player_name",
        "batter" if "batter" in df.columns else "pitcher",
    ]

    # Basic aggregation columns that are commonly available
    agg_dict = {}
    if "launch_speed" in df.columns:
        agg_dict["avg_exit_velocity"] = ("launch_speed", "mean")
        agg_dict["max_exit_velocity"] = ("launch_speed", "max")
    if "launch_angle" in df.columns:
        agg_dict["avg_launch_angle"] = ("launch_angle", "mean")
    if "estimated_ba_using_speedangle" in df.columns:
        agg_dict["avg_xba"] = ("estimated_ba_using_speedangle", "mean")
    if "estimated_woba_using_speedangle" in df.columns:
        agg_dict["avg_xwoba"] = ("estimated_woba_using_speedangle", "mean")

    # Count of pitches/batted balls
    agg_dict["pitch_count"] = ("pitch_type", "count")

    # Filter available columns
    available_cols = [col for col in summary_cols if col in df.columns]

    if not available_cols or not agg_dict:
        return df  # Return original if we can't summarize

    try:
        return df.groupby(available_cols).agg(**agg_dict).reset_index()
    except Exception:
        return df  # Return original if grouping fails


def get_statcast(
    start_date: str,
    end_date: str,
    player_id: int | None = None,
    statcast_type: StatcastType = "all",
    format_type: StatcastFormat = "summary",
    *,
    cache: Cache | None = None,
) -> pd.DataFrame:
    """Return Statcast data for a date range.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        player_id: Optional player ID for filtering
        statcast_type: Type of Statcast data to fetch
        format_type: Format of returned data (summary or parquet)
        cache: Cache instance to use

    Returns:
        DataFrame with Statcast data
    """
    if not start_date or not end_date:
        raise ValueError("Both start_date and end_date are required")

    # Validate dates
    start_obj = _parse_date(start_date)
    end_obj = _parse_date(end_date)
    if end_obj < start_obj:
        raise ValueError("end_date must be on or after start_date")

    cache = cache or Cache()
    key = _cache_key(start_date, end_date, player_id, statcast_type)

    if (df := cache.get_dataframe(key)) is not None:
        return _summarize_statcast(df) if format_type == "summary" else df

    # Fetch data based on type
    try:
        if statcast_type == "batter" and player_id:
            df = statcast_batter(start_date, end_date, player_id)
        elif statcast_type == "pitcher" and player_id:
            df = statcast_pitcher(start_date, end_date, player_id)
        else:
            df = statcast(start_date, end_date)
    except Exception:
        # Return empty DataFrame on error to avoid repeated API calls
        df = pd.DataFrame()

    # Cache the full data
    cache.set_dataframe(key, df)

    return _summarize_statcast(df) if format_type == "summary" else df
