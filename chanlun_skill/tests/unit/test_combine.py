"""Unit tests for combine logic."""
import pytest
import pandas as pd
from kline.raw import df_to_raw
from kline.combine import merge_klines


class TestCombine:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "date": ["2024-01-02", "2024-01-03", "2024-01-04"],
            "open": [100.0, 101.0, 99.0],
            "high": [105.0, 103.0, 102.0],
            "low": [98.0, 97.0, 96.0],
            "close": [102.0, 98.5, 101.0],
            "volume": [1000.0] * 3,
        })

    def test_df_to_raw(self, sample_df):
        raw = df_to_raw(sample_df)
        assert len(raw) == 3
        assert raw[0].h == 105.0

    def test_merge_klines_produces_combined(self, sample_df):
        raw = df_to_raw(sample_df)
        merged = merge_klines(raw)
        assert len(merged) >= len(raw)
