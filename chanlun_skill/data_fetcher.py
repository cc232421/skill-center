import requests
import pandas as pd
import yfinance as yf
from typing import Optional

CRYPTO_PAIRS = {
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "DOT", "LINK", "AVAX"
}


class DataFetcher:
    def __init__(self, market: str):
        self.market = market.upper()

    def fetch(
        self,
        symbol: str = "000001",
        period: str = "day",
        start: str = "20240101",
        end: str = "20260513",
    ) -> Optional[pd.DataFrame]:
        if self.market == "A":
            return self._fetch_a(symbol, period, start, end)
        elif self.market == "HK":
            return self._fetch_hk(symbol, period, start, end)
        elif self.market == "US":
            base = symbol.upper().replace("-USD", "")
            if base in CRYPTO_PAIRS:
                return self._fetch_crypto(base, period, start, end)
            return self._fetch_us(symbol, period, start, end)
        else:
            raise ValueError(f"Unsupported market: {self.market}")

    def _binance_klines(
        self, symbol: str, period: str, limit: int = 500
    ) -> Optional[pd.DataFrame]:
        interval_map = {
            "day": "1d", "week": "1w", "4h": "4h",
            "1h": "1h", "30m": "30m", "15m": "15m", "5m": "5m"
        }
        interval = interval_map.get(period, "4h")
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": f"{symbol}USDT", "interval": interval, "limit": limit}
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
            df["date"] = pd.to_datetime(df["open_time"], unit="ms").strftime("%Y-%m-%d")
            return df[["date", "open", "high", "low", "close", "volume"]]
        except Exception:
            return None

    def _fmt_ak(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [c.strip() for c in df.columns]
        df["date"] = pd.to_datetime(df["日期"]).dt.strftime("%Y-%m-%d")
        df = df.rename(columns={
            "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume"
        })
        for c in ["open", "close", "high", "low", "volume"]:
            df[c] = df[c].astype(float)
        return df[["date", "open", "high", "low", "close", "volume"]]

    def _fmt_yf(self, df: pd.DataFrame) -> pd.DataFrame:
        df.index = pd.to_datetime(df.index)
        df["date"] = df.index.strftime("%Y-%m-%d")
        df = df.rename(columns={
            "Open": "open", "Close": "close",
            "High": "high", "Low": "low", "Volume": "volume"
        })
        return df[["date", "open", "high", "low", "close", "volume"]]

    def _yf_period(self, period: str) -> str:
        return {
            "day": "1d", "week": "1wk",
            "60m": "60m", "30m": "30m",
            "15m": "15m", "5m": "5m", "1m": "1m"
        }.get(period, "1d")

    def _ak_period(self, period: str) -> str:
        return {
            "day": "daily", "week": "weekly",
            "60m": "60", "30m": "30",
            "15m": "15", "5m": "5", "1m": "1"
        }.get(period, "daily")

    def _fetch_a(
        self, symbol: str, period: str, start: str, end: str
    ) -> Optional[pd.DataFrame]:
        try:
            import akshare as ak
            p = self._ak_period(period)
            df = ak.stock_zh_a_hist(symbol=symbol, period=p, start_date=start, end_date=end, adjust="qfq")
            return self._fmt_ak(df)
        except Exception:
            return None

    def _fetch_hk(
        self, symbol: str, period: str, start: str, end: str
    ) -> Optional[pd.DataFrame]:
        try:
            ticker = yf.Ticker(f"{symbol}.HK")
            p = self._yf_period(period)
            df = yf.download(symbol, period=p, start=start[:4], end=end[:4], progress=False)
            if df.empty:
                return None
            return self._fmt_yf(df)
        except Exception:
            return None

    def _fetch_us(
        self, symbol: str, period: str, start: str, end: str
    ) -> Optional[pd.DataFrame]:
        try:
            ticker = yf.Ticker(symbol)
            p = self._yf_period(period)
            df = yf.download(symbol, period=p, start=start[:4], end=end[:4], progress=False)
            if df.empty:
                return None
            return self._fmt_yf(df)
        except Exception:
            return None

    def _fetch_crypto(
        self, symbol: str, period: str, start: str, end: str
    ) -> Optional[pd.DataFrame]:
        return self._binance_klines(symbol, period, limit=500)
