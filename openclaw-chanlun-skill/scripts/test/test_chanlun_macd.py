"""ChanLun MACD calculation module tests."""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from chanlun_engine import ChanLunEngine


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


class TestMACDCalculation:
    def test_macd_params(self):
        engine = ChanLunEngine(pd.DataFrame({
            "open": [100.0] * 30,
            "high": [101.0] * 30,
            "low": [99.0] * 30,
            "close": [100.0 + i * 0.5 for i in range(30)],
            "volume": [1000] * 30,
        }))
        assert engine.FAST == 12
        assert engine.SLOW == 26
        assert engine.SIGNAL == 9

    def test_macd_columns_added(self, klines_to_df):
        klines = make_klines(30)
        df = klines_to_df(klines)
        engine = ChanLunEngine(df)
        assert "macd_dif" in engine.df.columns
        assert "macd_dea" in engine.df.columns
        assert "macd" in engine.df.columns

    def test_macd_output_shape(self, klines_to_df):
        klines = make_klines(50, close_fn=lambda i: 100.0 + i * 0.5)
        df = klines_to_df(klines)
        engine = ChanLunEngine(df)
        assert len(engine.df) == 50
        assert "macd_dif" in engine.df.columns

    def test_macd_dif_sign(self, klines_to_df):
        df = klines_to_df(make_klines(50, close_fn=lambda i: 90.0 + i))
        engine = ChanLunEngine(df)
        assert engine.df["macd_dif"].iloc[-1] > 0

        df = klines_to_df(make_klines(50, close_fn=lambda i: 140.0 - i))
        engine = ChanLunEngine(df)
        assert engine.df["macd_dif"].iloc[-1] < 0

    def test_macd_histogram_sign(self, klines_to_df):
        df = klines_to_df(make_klines(50, close_fn=lambda i: 100.0 + i))
        engine = ChanLunEngine(df)
        assert engine.df["macd"].iloc[-1] > 0

    def test_ema_calculation(self):
        data = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
        ema = ChanLunEngine._ema(data, 3)
        k = 2.0 / 4
        expected = [
            10.0,
            11.0 * k + 10.0 * (1 - k),
            12.0 * k + (11.0 * k + 10.0 * (1 - k)) * (1 - k),
            13.0 * k + (12.0 * k + (11.0 * k + 10.0 * (1 - k)) * (1 - k)) * (1 - k),
            14.0 * k + (13.0 * k + (12.0 * k + (11.0 * k + 10.0 * (1 - k)) * (1 - k)) * (1 - k)) * (1 - k),
        ]
        assert np.allclose(ema, expected, rtol=1e-5)


class TestMACDEdgeCases:
    def test_short_data(self, klines_to_df):
        df = klines_to_df(make_klines(10, close_fn=lambda i: 100.0 + i * 0.5))
        engine = ChanLunEngine(df)
        assert "macd_dif" in engine.df.columns

    def test_constant_price(self, klines_to_df):
        df = klines_to_df(make_klines(50, close_fn=lambda i: 100.0))
        engine = ChanLunEngine(df)
        assert abs(engine.df["macd_dif"].iloc[-1]) < 0.1

    def test_single_value(self, klines_to_df):
        klines = [{"date": "2024-01-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000}]
        df = klines_to_df(klines)
        engine = ChanLunEngine(df)
        assert "macd" in engine.df.columns

    def test_missing_columns(self):
        df = pd.DataFrame({"open": [100.0], "high": [101.0]})
        with pytest.raises(ValueError, match="DataFrame must have columns"):
            ChanLunEngine(df)