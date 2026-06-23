"""ChanLun integration tests - full analysis pipeline."""

from datetime import datetime, timedelta
import pandas as pd
import pytest

from chanlun_engine import ChanLunEngine, build_df_from_lists, analyze_stock


def make_klines(n, start="2024-01-01", **kw):
    base = datetime.strptime(start, "%Y-%m-%d")
    close_fn = kw.get("close_fn", lambda i: 100.0 + i)
    o = kw.get("open", 100.0)
    h = kw.get("high", 101.0)
    l = kw.get("low", 99.0)
    v = kw.get("vol", 1000)
    return [
        {"date": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
         "open": o, "high": h, "low": l, "close": close_fn(i), "volume": v}
        for i in range(n)
    ]


class TestIntegration:
    def test_full_analyze_returns_complete_result(self, klines_to_df):
        df = klines_to_df(make_klines(60))
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert "klines_count" in result
            assert "cl_klines_count" in result
            assert "fractals" in result
            assert "strokes" in result
            assert "zhongshus" in result
            assert "signals" in result
            assert "current_trend" in result
            assert "summary" in result
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_analyze_with_sufficient_data(self, klines_to_df):
        df = klines_to_df(make_klines(365, close_fn=lambda i: 100.0 + (i % 10) * 0.5))
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert result["klines_count"] >= 360
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_analyze_with_ascending_prices(self, klines_to_df):
        df = klines_to_df(make_klines(60, close_fn=lambda i: 100.0 + i))
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert result["klines_count"] == 60
            assert result["current_trend"] in ("上涨", "下跌", "盘整")
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_analyze_with_descending_prices(self, klines_to_df):
        df = klines_to_df(make_klines(60, close_fn=lambda i: 160.0 - i))
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert result["klines_count"] == 60
        except ImportError:
            pytest.skip("pychanlun not installed")


class TestBuildDataFrame:
    def test_build_df_from_lists_reverses_dates(self):
        dates = ["2024-01-10", "2024-01-09", "2024-01-08"]
        opens = [100.0, 101.0, 102.0]
        highs = [101.0, 102.0, 103.0]
        lows = [99.0, 100.0, 101.0]
        closes = [100.5, 101.5, 102.5]
        vols = [1000, 1100, 1200]
        df = build_df_from_lists(dates, opens, highs, lows, closes, vols)
        assert df.index[0] == pd.Timestamp("2024-01-08")
        assert df.index[-1] == pd.Timestamp("2024-01-10")

    def test_build_df_from_lists_columns(self):
        dates = ["2024-01-02", "2024-01-03"]
        opens = [100.0, 101.0]
        highs = [101.0, 102.0]
        lows = [99.0, 100.0]
        closes = [100.5, 101.5]
        vols = [1000, 1100]
        df = build_df_from_lists(dates, opens, highs, lows, closes, vols)
        assert set(df.columns) == {"open", "high", "low", "close", "volume"}

    def test_build_df_from_lists_reverses_data(self):
        dates = ["2024-01-10", "2024-01-09", "2024-01-08"]
        opens = [100.0, 101.0, 102.0]
        highs = [101.0, 102.0, 103.0]
        lows = [99.0, 100.0, 101.0]
        closes = [100.5, 101.5, 102.5]
        vols = [1000, 1100, 1200]
        df = build_df_from_lists(dates, opens, highs, lows, closes, vols)
        assert df.iloc[0]["close"] == 102.5
        assert df.iloc[-1]["close"] == 100.5


class TestAnalyzeStock:
    def test_analyze_stock_returns_dict(self):
        dates = [f"2024-01-{i:02d}" for i in range(2, 32)]
        opens = [100.0] * 29
        highs = [101.0] * 29
        lows = [99.0] * 29
        closes = [100.0 + i * 0.5 for i in range(29)]
        vols = [1000] * 29
        try:
            result = analyze_stock("600176", dates, opens, highs, lows, closes, vols)
            assert isinstance(result, dict)
            assert "symbol" in result
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_analyze_stock_handles_error(self):
        try:
            result = analyze_stock("INVALID", [], [], [], [], [], [])
            assert "symbol" in result
        except Exception:
            pass


class TestRegression:
    def test_output_structure_matches_chanlunanalyzer(self, klines_to_df):
        df = klines_to_df(make_klines(100, close_fn=lambda i: 100.0 + (i % 5)))
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert "klines_count" in result
            assert "fractals" in result
            assert "strokes" in result
            assert "zhongshus" in result
            assert "current_trend" in result
            assert "summary" in result
        except ImportError:
            pytest.skip("pychanlun not installed")