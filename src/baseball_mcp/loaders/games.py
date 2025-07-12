"""Data loader for game schedules."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from pybaseball import schedule_and_record

from baseball_mcp.cache import Cache

_DATE_FMT = "%Y-%m-%d"


def _cache_key(team: str, start: str, end: str) -> str:
    return f"schedule:{team.upper()}:{start}:{end}"


def _parse(date_str: str) -> datetime:
    return datetime.strptime(date_str, _DATE_FMT)


def _parse_schedule_dates(date_series: pd.Series, season: int) -> pd.Series:
    """Parse schedule dates that may be incomplete (missing year).

    Args:
        date_series: Series of date strings from pybaseball
        season: The season year to use for dates without year

    Returns:
        Series of datetime objects
    """
    def parse_single_date(date_str: str) -> Any:  # Use Any for pd.NaT compatibility
        if pd.isna(date_str):
            return pd.NaT

        # Handle various date formats from pybaseball
        date_str = str(date_str).strip()

        # Handle empty strings
        if not date_str:
            return pd.NaT

        # If it already has year, try parsing as-is
        date_parts = date_str.split()
        if date_parts and any(char.isdigit() for char in date_parts[-1]):
            try:
                return pd.to_datetime(date_str)
            except Exception:
                pass

        # Handle format like "Thursday, Mar 27"
        if "," in date_str:
            try:
                # Extract day and month, add year
                parts = date_str.split(",")
                if len(parts) >= 2:
                    month_day = parts[1].strip()  # "Mar 27"
                    date_with_year = f"{month_day}, {season}"
                    return pd.to_datetime(date_with_year)
            except Exception:
                pass

        # Try adding year and parsing
        try:
            return pd.to_datetime(f"{date_str}, {season}")
        except Exception:
            pass

        # Last resort - try pandas default parsing
        try:
            return pd.to_datetime(date_str)
        except Exception:
            return pd.NaT

    return date_series.apply(parse_single_date)


def get_schedule(
    team: str,
    start_date: str,
    end_date: str,
    *,
    cache: Cache | None = None,
) -> pd.DataFrame:
    """Return game schedule for a team in a date range.

    The function pulls the full season schedule via
    :pyfunc:`pybaseball.schedule_and_record` (season-level) and then filters by the
    provided start & end dates inclusive. Results are cached for the exact date range
    requested.
    """

    if not team:
        raise ValueError("team abbreviation is required")

    # Validate & normalise dates (YYYY-MM-DD)
    start_obj = _parse(start_date)
    end_obj = _parse(end_date)
    if end_obj < start_obj:
        raise ValueError("end_date must be on or after start_date")

    season = start_obj.year
    if end_obj.year != season:
        raise ValueError(
            "start_date and end_date must be within the same season for now",
        )

    cache = cache or Cache()
    key = _cache_key(team, start_date, end_date)
    if (df := cache.get_dataframe(key)) is not None:
        return df

    df_season: pd.DataFrame = schedule_and_record(season, team.upper())
    # Ensure Date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df_season["Date"]):
        df_season["Date"] = _parse_schedule_dates(df_season["Date"], season)

    mask = (df_season["Date"] >= start_obj) & (df_season["Date"] <= end_obj)
    df_range = df_season.loc[mask]

    cache.set_dataframe(key, df_range)
    return df_range
