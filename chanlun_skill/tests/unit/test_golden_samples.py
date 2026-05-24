"""Golden-sample end-to-end tests via ChanEngine with synthetic market data."""
import pandas as pd
import pytest
from core.engine import ChanEngine
from core.config import ChanConfig


def _ckl(date, o, h, l, c, v=1000.0):
    return pd.DataFrame({
        "date": [date], "open": [o], "high": [h],
        "low": [l], "close": [c], "volume": [v],
    })


class TestSegGoldenSamples:
    def test_schema_keys_present(self):
        df = pd.DataFrame({
            "date": ["2024-01-0%d" % i for i in range(1, 10)],
            "open": [100.0 + i for i in range(9)],
            "high": [105.0 + i for i in range(9)],
            "low": [95.0 + i for i in range(9)],
            "close": [102.0 + i for i in range(9)],
            "volume": [1000.0] * 9,
        })
        cfg = ChanConfig(symbol="TEST")
        result = ChanEngine(cfg, df).analyze()
        assert "structures" in result
        assert "schema_version" in result

    def test_empty_df_engine_analyze_returns_empty(self):
        engine = ChanEngine(ChanConfig(symbol="TEST"), pd.DataFrame())
        assert engine.analyze() == {}


class TestZSGoldenSamples:
    def test_schema_v2_zs_key_present(self):
        df = pd.DataFrame({
            "date": ["2024-01-0%d" % i for i in range(1, 10)],
            "open": [100.0 + i for i in range(9)],
            "high": [105.0 + i for i in range(9)],
            "low": [95.0 + i for i in range(9)],
            "close": [102.0 + i for i in range(9)],
            "volume": [1000.0] * 9,
        })
        cfg = ChanConfig(symbol="TEST")
        result = ChanEngine(cfg, df).analyze()
        assert "structures" in result
        assert "zss" in result["structures"] or "zhongshus" in result["structures"]

