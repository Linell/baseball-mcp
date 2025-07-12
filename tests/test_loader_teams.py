"""Tests for baseball_mcp.loaders.teams."""

from unittest.mock import patch

import pandas as pd

from baseball_mcp.cache import Cache
from baseball_mcp.loaders.teams import get_team_stats


def test_get_team_stats_fetch_and_cache():
    dummy_df = pd.DataFrame({"Team": ["NYY"], "HR": [200]})

    patch_target = "baseball_mcp.loaders.teams.team_batting"
    with patch(patch_target, return_value=dummy_df) as mock_stats:
        cache = Cache(db_path=":memory:")
        df1 = get_team_stats("NYY", year=2024, cache=cache)
        assert not df1.empty
        # Second call should hit cache, not fetch again
        df2 = get_team_stats("NYY", year=2024, cache=cache)
        assert df2.equals(df1)
        assert mock_stats.call_count == 1
