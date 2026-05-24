"""
Binance data source for crypto.
"""
import requests
import pandas as pd
from typing import Optional


CRYPTO_PAIRS = {
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "DOT", "LINK", "AVAX"
}


def fetch_binance(symbol: str, period: str, limit: int = 500) -> Optional[pd.DataFrame]:
    interval_map = {
        "day": "1d", "week": "1w",
        "4h": "4h", "1h": "1h", "30m": "30m", "15m": "15m", "5m": "5m", "1m": "1m",
    }
    interval = interval_map.get(period, "1d")
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        raw = r.json()
        cols = [
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "ignore", "ignore2", "ignore3", "ignore4", "ignore5"
        ]
        df = pd.DataFrame(raw, columns=cols)
        for c in ["open", "high", "low", "close", "volume"]:
            df[c] = df[c].astype(float)
        df["date"] = pd.to_datetime(df["open_time"], unit="ms").dt.strftime("%Y-%m-%d")
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return None
