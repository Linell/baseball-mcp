"""Tests for baseball_mcp.loaders.players."""

from unittest.mock import patch

import pandas as pd

from baseball_mcp.cache import Cache
from baseball_mcp.loaders.players import get_player_stats


def test_get_player_stats_fetch_and_cache():
    dummy_df = pd.DataFrame({"Name": ["Test Player"], "HR": [1]})

    patch_target = "baseball_mcp.loaders.players.batting_stats"
    with patch(patch_target, return_value=dummy_df) as mock_stats:
        cache = Cache(db_path=":memory:")
        df1 = get_player_stats("Test Player", year=2024, cache=cache)
        assert not df1.empty
        # Second call should hit cache – the patched function is not called again
        df2 = get_player_stats("Test Player", year=2024, cache=cache)
        assert df2.equals(df1)
        assert mock_stats.call_count == 1
