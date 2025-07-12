"""Data loader for player statistics."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from pybaseball import batting_stats

from baseball_mcp.cache import Cache


def _cache_key(player_name: str, year: int, split: str | None = None) -> str:
    return f"player_stats:{player_name.lower()}:{year}:{split or 'default'}"


def get_player_stats(
    player_name: str,
    year: int | None = None,
    split: str | None = None,
    *,
    cache: Cache | None = None,
) -> pd.DataFrame:
    """Return season stats for a player, using cache when available."""

    if not player_name:
        raise ValueError("player_name must be provided")

    if year is None:
        year = datetime.now().year

    cache = cache or Cache()
    key = _cache_key(player_name, year, split)

    if (df := cache.get_dataframe(key)) is not None:
        return df

    # Fetch fresh stats via pybaseball
    df_all: pd.DataFrame = batting_stats(year)
    df_player = df_all[df_all["Name"].str.contains(player_name, case=False, na=False)]

    # Persist result (including empty frames to avoid repeated hits)
    cache.set_dataframe(key, df_player)
    return df_player
