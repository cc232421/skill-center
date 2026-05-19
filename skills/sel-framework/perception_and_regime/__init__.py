"""
perception_and_regime — Market data fetch + Regime classification
纯本地算法，无需外部 LLM API
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd

# ─── Data Sources ────────────────────────────────────────────────────────────

CRYPTO_PAIRS = {"BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "DOT", "LINK", "AVAX"}


def _binance_klines(symbol: str, period: str, limit: int = 500) -> Optional[pd.DataFrame]:
    import requests

    interval_map = {
        "day": "1d", "week": "1w", "4h": "4h",
        "60m": "1h", "30m": "30m", "15m": "15m", "5m": "5m", "1m": "1m",
    }
    interval = interval_map.get(period, "1d")
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": f"{symbol.upper()}USDT", "interval": interval, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        raw = r.json()
        cols = [
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "ignore", "ignore2", "ignore3", "ignore4", "ignore5",
        ]
        df = pd.DataFrame(raw, columns=cols)
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = df[c].astype(float)
        df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.strftime("%Y-%m-%d")
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return None


def _fetch_a_stock(symbol: str, period: str = "day", start: str = "20240101", end: str = "20260519") -> Optional[pd.DataFrame]:
    try:
        import akshare as ak  # type: ignore
        period_map = {
            "day": "daily", "week": "weekly",
            "60m": "60", "30m": "30", "15m": "15", "5m": "5", "1m": "1",
        }
        p = period_map.get(period, "daily")
        df = ak.stock_zh_a_hist(symbol=symbol, period=p, start_date=start, end_date=end, adjust="qfq")
        df.columns = [c.strip() for c in df.columns]
        df["date"] = pd.to_datetime(df["日期"]).dt.strftime("%Y-%m-%d")
        df = df.rename(columns={
            "开盘": "open", "收盘": "close", "最高": "high", "最低": "low", "成交量": "volume",
        })
        for c in ["open", "close", "high", "low", "volume"]:
            df[c] = df[c].astype(float)
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return None


def _fetch_yf(symbol: str, period: str = "day") -> Optional[pd.DataFrame]:
    try:
        import yfinance as yf  # type: ignore
        period_map = {
            "day": "1d", "week": "1wk",
            "60m": "60m", "30m": "30m", "15m": "15m", "5m": "5m", "1m": "1m",
        }
        p = period_map.get(period, "1d")
        ticker = yf.Ticker(symbol)
        df = ticker.download(period=p, progress=False)
        if df.empty:
            return None
        df.index = pd.to_datetime(df.index)
        df["date"] = df.index.strftime("%Y-%m-%d")
        df = df.rename(columns={
            "Open": "open", "Close": "close", "High": "high", "Low": "low", "Volume": "volume",
        })
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return None


def fetch_market_data(symbols: list[str], market: str = "A", period: str = "day") -> dict:
    """Fetch OHLCV data for all symbols."""
    result: dict = {}
    for sym in symbols:
        sym = sym.strip()
        if not sym:
            continue
        if market == "A":
            df = _fetch_a_stock(sym, period)
        elif market == "HK":
            df = _fetch_yf(f"{sym}.HK", period)
        elif market == "US":
            base = sym.upper().replace("-USD", "")
            if base in CRYPTO_PAIRS:
                df = _binance_klines(base, period)
            else:
                df = _fetch_yf(sym, period)
        else:
            df = None

        if df is not None and not df.empty:
            result[sym] = {
                "dates": df["date"].tolist(),
                "open": df["open"].tolist(),
                "high": df["high"].tolist(),
                "low": df["low"].tolist(),
                "close": df["close"].tolist(),
                "volume": df["volume"].tolist(),
            }
    return result


# ─── Indicators ──────────────────────────────────────────────────────────────

def _adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14) -> float:
    """Average Directional Index (simplified)."""
    plus_dm = np.zeros_like(close)
    minus_dm = np.zeros_like(close)
    tr = np.zeros_like(close)

    for i in range(1, len(close)):
        tr[i] = high[i] - low[i]
        up = high[i] - high[i - 1]
        dn = low[i - 1] - low[i]
        plus_dm[i] = up if up > dn and up > 0 else 0.0
        minus_dm[i] = dn if dn > up and dn > 0 else 0.0

    tr_smooth = pd.Series(tr).rolling(n).sum().values
    plus_dm_smooth = pd.Series(plus_dm).rolling(n).sum().values
    minus_dm_smooth = pd.Series(minus_dm).rolling(n).sum().values

    with np.errstate(divide="ignore", invalid="ignore"):
        plus_di = np.where(tr_smooth != 0, plus_dm_smooth / tr_smooth * 100, 0)
        minus_di = np.where(tr_smooth != 0, minus_dm_smooth / tr_smooth * 100, 0)
        dx = np.where(plus_di + minus_di != 0,
                      np.abs(plus_di - minus_di) / (plus_di + minus_di) * 100, 0)

    adx_vals = pd.Series(dx).rolling(n).mean().values
    return float(adx_vals[-1]) if len(adx_vals) > 0 and not np.isnan(adx_vals[-1]) else 0.0


def _atr_pct(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int = 14) -> float:
    """ATR as percentage of close price."""
    tr = np.maximum.reduce([
        high - low,
        np.abs(high - np.roll(close, 1)),
        np.abs(np.roll(low, 1) - close),
    ])
    tr[0] = high[0] - low[0]
    atr = pd.Series(tr).rolling(n).mean().values
    atr_val = float(atr[-1]) if len(atr) > 0 and not np.isnan(atr[-1]) else 0.0
    return (atr_val / float(close[-1]) * 100) if close[-1] != 0 else 0.0


def _macd_hist(close: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> float:
    """MACD histogram (no TALIB needed)."""
    ema_fast = pd.Series(close).ewm(span=fast, adjust=False).mean().values
    ema_slow = pd.Series(close).ewm(span=slow, adjust=False).mean().values
    macd_line = ema_fast - ema_slow
    signal_line = pd.Series(macd_line).ewm(span=signal, adjust=False).mean().values
    hist = macd_line - signal_line
    return float(hist[-1]) if len(hist) > 0 else 0.0


def _vol_ratio(volume: np.ndarray, n: int = 20) -> float:
    """Recent volume / average volume ratio."""
    avg = pd.Series(volume).rolling(n).mean().values
    avg_val = float(avg[-1]) if len(avg) > 0 and not np.isnan(avg[-1]) else 1.0
    return float(volume[-1]) / avg_val if avg_val != 0 else 1.0


def _sma20_slope(close: np.ndarray, n: int = 20) -> float:
    """SMA20 slope (rate of change per bar)."""
    if len(close) < n + 2:
        return 0.0
    sma_vals = pd.Series(close).rolling(n).mean().values
    recent = float(sma_vals[-1]) if not np.isnan(sma_vals[-1]) else 0.0
    prev = float(sma_vals[-2]) if not np.isnan(sma_vals[-2]) else 0.0
    return (recent - prev) / prev if prev != 0 else 0.0


def compute_features(df: pd.DataFrame) -> dict:
    """Compute regime classification features from OHLCV DataFrame."""
    close = df["close"].values.astype(float)
    high = df["high"].values.astype(float)
    low = df["low"].values.astype(float)
    volume = df["volume"].values.astype(float)

    if len(close) < 30:
        return {
            "adx": 0.0, "atr_pct": 0.0, "macd_hist": 0.0,
            "vol_ratio": 1.0, "sma20_slope": 0.0, "price_vs_sma20": 1.0,
        }

    adx_val = _adx(high, low, close)
    atr_val = _atr_pct(high, low, close)
    macd_val = _macd_hist(close)
    vol_val = _vol_ratio(volume)
    slope_val = _sma20_slope(close)
    sma20 = float(pd.Series(close).rolling(20).mean().values[-1])
    price_vs_sma = float(close[-1]) / sma20 if sma20 != 0 else 1.0

    return {
        "adx": round(adx_val, 2),
        "atr_pct": round(atr_val, 3),
        "macd_hist": round(macd_val, 4),
        "vol_ratio": round(vol_val, 2),
        "sma20_slope": round(slope_val, 5),
        "price_vs_sma20": round(price_vs_sma, 4),
    }


def classify_regime(features: dict, prices: list[float]) -> tuple[str, float]:
    """
    Classify market regime from features.
    Returns (regime_label, confidence).
    """
    adx = features["adx"]
    atr_pct = features["atr_pct"]
    macd_hist = features["macd_hist"]
    price_vs_sma = features["price_vs_sma20"]

    hits: list[float] = []
    label = "sideways"

    # Black swan: extreme single-day drop
    if len(prices) >= 2:
        day_returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        max_loss = min(day_returns) if day_returns else 0.0
        if max_loss < -0.08 or atr_pct > 8.0:
            return ("black_swan", 0.95)

    # Volatile
    if atr_pct > 5.0 or adx > 40:
        label = "volatile"
        hits.append(0.9 if atr_pct > 5.0 else 0.7)
    # Trend up
    elif adx > 25 and macd_hist > 0 and price_vs_sma > 1.0:
        label = "trend_up"
        hits.extend([adx / 50, 0.9, 0.85])
    # Trend down
    elif adx > 25 and macd_hist < 0 and price_vs_sma < 1.0:
        label = "trend_down"
        hits.extend([adx / 50, 0.9, 0.85])
    # Sideways
    else:
        label = "sideways"
        hits.extend([max(0, 1 - adx / 25), max(0, 1 - atr_pct / 5)])

    confidence = float(np.mean(hits)) if hits else 0.3
    return label, round(min(confidence, 0.99), 3)


# ─── Main Skill ───────────────────────────────────────────────────────────────

@dataclass
class PerceptionResult:
    market_snapshot: dict
    regime_label: str
    regime_confidence: float
    features: dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "market_snapshot": self.market_snapshot,
            "regime_label": self.regime_label,
            "regime_confidence": self.regime_confidence,
            "features": self.features,
            "timestamp": self.timestamp,
        }


def _aggregate_features(snapshot: dict) -> tuple[list[float], dict]:
    """Aggregate features across all symbols, return (prices, avg_features)."""
    all_close: list[float] = []
    combined: dict = {}
    for sym, data in snapshot.items():
        if not data["close"]:
            continue
        all_close.extend(data["close"][-30:])
        feat = compute_features(pd.DataFrame(data))
        for k, v in feat.items():
            combined.setdefault(k, []).append(v)
    prices = all_close[-60:] if all_close else [0.0]
    avg = {k: round(float(np.mean(v)), 4) for k, v in combined.items()}
    return prices, avg


def run(symbols: list[str], market: str = "A", period: str = "day") -> dict:
    """
    Main entry point for perception_and_regime skill.

    Args:
        symbols: list of stock/crypto symbols
        market: A|HK|US (default: A)
        period: K-line period (default: day)

    Returns:
        PerceptionResult as dict
    """
    snapshot = fetch_market_data(symbols, market, period)

    if not snapshot:
        return {
            "market_snapshot": {},
            "regime_label": "unknown",
            "regime_confidence": 0.0,
            "features": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "No market data fetched",
        }

    prices, avg_features = _aggregate_features(snapshot)
    regime_label, confidence = classify_regime(avg_features, prices)

    result = PerceptionResult(
        market_snapshot=snapshot,
        regime_label=regime_label,
        regime_confidence=confidence,
        features=avg_features,
    )
    return result.to_dict()
