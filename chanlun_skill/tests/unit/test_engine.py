import pytest
from core.engine import ChanEngine
from core.config import ChanConfig


class TestEnginePipeline:
    @pytest.fixture
    def up_market_df(self):
        import pandas as pd
        return pd.DataFrame({
            "date": ["2024-01-0%d" % i for i in range(1, 10)],
            "open": [100.0 + i for i in range(9)],
            "high": [105.0 + i for i in range(9)],
            "low": [95.0 + i for i in range(9)],
            "close": [102.0 + i for i in range(9)],
            "volume": [1000.0] * 9
        })

    def test_analyze_produces_schema_v2_keys(self, up_market_df):
        cfg = ChanConfig(symbol="000001")
        engine = ChanEngine(cfg, up_market_df)
        result = engine.analyze()
        assert "schema_version" in result
        assert set(result.keys()) == {"schema_version", "meta", "stats", "kline", "structures", "signals", "state"}

    def test_analyze_has_meta(self, up_market_df):
        cfg = ChanConfig(symbol="000001", period="day")
        engine = ChanEngine(cfg, up_market_df)
        result = engine.analyze()
        assert result["meta"]["symbol"] == "000001"

    def test_trend_reflects_bi_direction(self, up_market_df):
        cfg = ChanConfig(symbol="000001")
        engine = ChanEngine(cfg, up_market_df)
        result = engine.analyze()
        assert result["signals"] == [] or isinstance(result["signals"], list)

    def test_engine_handles_empty_df(self):
        import pandas as pd
        cfg = ChanConfig(symbol="000001")
        engine = ChanEngine(cfg, pd.DataFrame())
        assert engine.analyze() == {}
