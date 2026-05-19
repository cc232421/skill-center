"""
Tests for perception_and_regime skill
"""
import pytest
import numpy as np
import pandas as pd
from perception_and_regime import (
    compute_features, classify_regime, run,
    _adx, _atr_pct, _macd_hist, _vol_ratio, _sma20_slope,
)


def make_ohlcv(n: int = 50, trend: str = "sideways") -> pd.DataFrame:
    """Generate OHLCV DataFrame with controlled trend."""
    dates = [f"2024-01-{i%28+1:02d}" for i in range(n)]
    close_base = 100.0
    closes = [close_base]
    for i in range(1, n):
        if trend == "up":
            closes.append(closes[-1] * 1.003)
        elif trend == "down":
            closes.append(closes[-1] * 0.997)
        else:
            closes.append(closes[-1] * (1 + np.random.randn() * 0.005))
    closes = np.array(closes)
    highs = closes * 1.02
    lows = closes * 0.98
    opens = closes * (1 + np.random.randn(n) * 0.005)
    volumes = np.random.randint(1_000_000, 5_000_000, n)
    return pd.DataFrame({
        "date": dates, "open": opens, "high": highs,
        "low": lows, "close": closes, "volume": volumes,
    })


class TestRegimeClassifier:
    def test_sideways_classification(self):
        df = make_ohlcv(50, "sideways")
        feat = compute_features(df)
        label, conf = classify_regime(feat, df["close"].tolist())
        assert label in ("sideways", "trend_up", "trend_down", "volatile", "black_swan")
        assert 0.0 <= conf <= 1.0

    def test_features_all_keys(self):
        df = make_ohlcv(50, "sideways")
        feat = compute_features(df)
        assert "adx" in feat
        assert "atr_pct" in feat
        assert "macd_hist" in feat
        assert "vol_ratio" in feat
        assert "sma20_slope" in feat

    def test_features_non_nan(self):
        df = make_ohlcv(50, "sideways")
        feat = compute_features(df)
        for v in feat.values():
            assert not np.isnan(v), f"NaN in feature: {v}"

    def test_black_swan_detection(self):
        feat = {"adx": 50, "atr_pct": 10.0, "macd_hist": -5.0, "price_vs_sma20": 0.85}
        prices = [100.0, 100.0, 100.0, 91.0]  # 9% drop
        label, conf = classify_regime(feat, prices)
        assert label == "black_swan"
        assert conf >= 0.9

    def test_run_returns_dict_structure(self):
        result = run(["FAKE_SYMBOL_THAT_DOES_NOT_EXIST"], market="A", period="day")
        assert "market_snapshot" in result
        assert "regime_label" in result
        assert "regime_confidence" in result
        assert "features" in result
        assert "timestamp" in result

    def test_run_unknown_on_bad_symbols(self):
        result = run(["__DOES_NOT_EXIST__999__"], market="A", period="day")
        assert result["regime_label"] == "unknown"
        assert result["regime_confidence"] == 0.0

    def test_trend_up_features(self):
        df = make_ohlcv(50, "up")
        feat = compute_features(df)
        # In sustained uptrend, price should be above SMA20
        assert feat["price_vs_sma20"] >= 1.0

    def test_confidence_bounded(self):
        df = make_ohlcv(30, "sideways")
        feat = compute_features(df)
        _, conf = classify_regime(feat, df["close"].tolist())
        assert 0.0 <= conf <= 1.0
