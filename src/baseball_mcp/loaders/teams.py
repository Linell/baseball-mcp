"""Data loader for team statistics (batting + pitching)."""

from __future__ import annotations

import pandas as pd
from pybaseball import team_batting

from baseball_mcp.cache import Cache


def _cache_key(team: str, year: int, split: str | None = None) -> str:
    return f"team_stats:{team.upper()}:{year}:{split or 'default'}"


def _normalize_team_abbreviation(team: str) -> str:
    """Normalize team abbreviation to pybaseball format."""
    team = team.upper()

    # Map common abbreviations to pybaseball team codes
    team_mapping = {
        'SD': 'SDP',     # San Diego Padres
        'LAD': 'LAD',    # Los Angeles Dodgers
        'LAA': 'LAA',    # Los Angeles Angels
        'SF': 'SFG',     # San Francisco Giants
        'TB': 'TBR',     # Tampa Bay Rays
        'KC': 'KCR',     # Kansas City Royals
        'CWS': 'CHW',    # Chicago White Sox
        'WSH': 'WSN',    # Washington Nationals
        'ARI': 'ARI',    # Arizona Diamondbacks
        'NYM': 'NYM',    # New York Mets
        'NYY': 'NYY',    # New York Yankees
        'BOS': 'BOS',    # Boston Red Sox
        'BAL': 'BAL',    # Baltimore Orioles
        'TOR': 'TOR',    # Toronto Blue Jays
        'PHI': 'PHI',    # Philadelphia Phillies
        'ATL': 'ATL',    # Atlanta Braves
        'MIA': 'MIA',    # Miami Marlins
        'CHC': 'CHC',    # Chicago Cubs
        'MIL': 'MIL',    # Milwaukee Brewers
        'CIN': 'CIN',    # Cincinnati Reds
        'PIT': 'PIT',    # Pittsburgh Pirates
        'STL': 'STL',    # St. Louis Cardinals
        'HOU': 'HOU',    # Houston Astros
        'TEX': 'TEX',    # Texas Rangers
        'SEA': 'SEA',    # Seattle Mariners
        'OAK': 'OAK',    # Oakland Athletics
        'COL': 'COL',    # Colorado Rockies
        'DET': 'DET',    # Detroit Tigers
        'CLE': 'CLE',    # Cleveland Guardians
        'MIN': 'MIN',    # Minnesota Twins
        'SDP': 'SDP',    # San Diego Padres (already correct)
        'SFG': 'SFG',    # San Francisco Giants (already correct)
        'TBR': 'TBR',    # Tampa Bay Rays (already correct)
        'KCR': 'KCR',    # Kansas City Royals (already correct)
        'CHW': 'CHW',    # Chicago White Sox (already correct)
        'WSN': 'WSN',    # Washington Nationals (already correct)
    }

    return team_mapping.get(team, team)


def get_team_stats(
    team: str,
    year: int,
    split: str | None = None,
    *,
    cache: Cache | None = None,
) -> pd.DataFrame:
    """Return season-level team stats, using cache when available.

    Currently fetches Fangraphs season data via :pyfunc:`pybaseball.team_batting`. In a
    future iteration we'll join pitching/fielding splits and allow granular `split`
    options. For now, `split` is unused beyond cache-key namespacing.
    """

    if not team:
        raise ValueError("team must be provided (e.g. 'ATL', 'NYY')")
    if year < 1871:
        raise ValueError("year must be 1871 or later")

    # Normalize team abbreviation
    normalized_team = _normalize_team_abbreviation(team)

    cache = cache or Cache()
    key = _cache_key(normalized_team, year, split)

    if (df := cache.get_dataframe(key)) is not None:
        return df

    # Fetch season-level statistics. `team_batting` accepts a start & end season
    # (inclusive). We fetch a single season and then filter the requested team.
    try:
        df_all: pd.DataFrame = team_batting(year, year, normalized_team.upper())
        # `team_batting` returns *all* teams by default; filter defensively.
        if "Team" in df_all.columns:
            df_team = df_all[df_all["Team"].str.upper() == normalized_team.upper()]
        else:
            df_team = df_all
    except Exception:
        # If the team abbreviation still doesn't work, try without the team parameter
        # to get all teams and then filter
        try:
            df_fallback: pd.DataFrame = team_batting(year, year)
            if "Team" in df_fallback.columns:
                # Try both the original and normalized team names
                df_team = df_fallback[
                    (df_fallback["Team"].str.upper() == team.upper()) |
                    (df_fallback["Team"].str.upper() == normalized_team.upper())
                ]
            else:
                df_team = pd.DataFrame()  # Return empty if no Team column
        except Exception:
            # If all else fails, return empty DataFrame
            df_team = pd.DataFrame()

    cache.set_dataframe(key, df_team)
    return df_team
