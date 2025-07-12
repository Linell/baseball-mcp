"""Tests for baseball_mcp.cache."""

import pandas as pd

from baseball_mcp.cache import Cache


def test_set_get_dataframe():
    cache = Cache(db_path=":memory:")
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    cache.set_dataframe("test-key", df)
    retrieved = cache.get_dataframe("test-key")
    assert retrieved is not None
    assert df.equals(retrieved)


def test_reset():
    cache = Cache(db_path=":memory:")
    cache.set_dataframe("x", pd.DataFrame({"col": [1]}))
    cache.reset()
    assert cache.get_dataframe("x") is None
