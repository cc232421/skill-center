"""多源 OHLCV 数据获取 — A 股(akshare)、港股/美股(yfinance)、加密货币(Binance)."""

import time
from datetime import datetime
from typing import Optional

import pandas as pd


class DataFetcher:
    """Multi-source OHLCV data fetcher."""

    CRYPTO_SYMBOLS = {
        "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "DOT",
        "AVAX", "LINK", "MATIC", "UNI", "ATOM", "LTC", "BCH", "NEAR",
    }

    def __init__(self, market: str = "A"):
        valid = {"A", "HK", "US", "CRYPTO"}
        if market not in valid:
            raise ValueError(f"Unsupported market: {market}")
        self.market = market

    def fetch(
        self,
        symbol: str,
        period: str = "day",
        start_date: str = "20240101",
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        source = self._resolve_source(symbol)
        if self.market == "A":
            try:
                return getattr(self, f"_fetch_{source}")(symbol, period, start_date, end_date)
            except Exception:
                return self._fetch_akshare(symbol, period, start_date, end_date)
        fn = getattr(self, f"_fetch_{source}")
        return fn(symbol, period, start_date, end_date)

    def _resolve_source(self, symbol: str) -> str:
        if self.market == "A":
            return "tencent"
        if self.market == "HK":
            return "yfinance"
        if self.market == "US" and symbol.upper() in self.CRYPTO_SYMBOLS:
            return "binance"
        if self.market == "CRYPTO":
            return "binance"
        return "yfinance"

    def _tencent_prefix(self, symbol: str) -> str:
        return "sh" if symbol.startswith(("6", "9")) else "sz"

    def _fetch_tencent(self, symbol: str, period: str, start: str, end: str) -> pd.DataFrame:
        import requests

        period_map = {
            "1m": "m1", "5m": "m5", "15m": "m15",
            "30m": "m30", "60m": "m60",
            "day": "day", "week": "week",
        }
        tperiod = period_map.get(period, "day")
        start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:8]}" if "-" not in start else start[:10]
        end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:8]}" if "-" not in end else end[:10]
        prefix = self._tencent_prefix(symbol)
        param = f"{prefix}{symbol},{tperiod},{start_fmt},{end_fmt},640,qfq"

        resp = requests.get(
            "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
            params={"param": param},
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("code") != 0:
            raise RuntimeError(f"tencent error: {payload.get('msg')}")

        series = payload.get("data", {}).get(f"{prefix}{symbol}", {}).get("qfqday") or []
        if not series:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        rows = [{
            "date": pd.to_datetime(r[0]),
            "open": float(r[1]),
            "close": float(r[2]),
            "high": float(r[3]),
            "low": float(r[4]),
            "volume": float(r[5]),
        } for r in series]

        df = pd.DataFrame(rows).set_index("date").sort_index()
        return df[["open", "high", "low", "close", "volume"]]

    def _fetch_akshare(self, symbol: str, period: str, start: str, end: str) -> pd.DataFrame:
        import akshare as ak
        import os
        # disable proxy for eastmoney
        for k in list(os.environ.keys()):
            if 'proxy' in k.lower():
                del os.environ[k]
        os.environ['NO_PROXY'] = '*'
        os.environ['no_proxy'] = '*'

        freq_map = {
            "1m": "1", "5m": "5", "15m": "15", "30m": "30",
            "60m": "60", "day": "daily", "week": "weekly",
        }
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=freq_map.get(period, "daily"),
            start_date=start, end_date=end, adjust="qfq",
        )
        if df.empty:
            return df

        df = df.rename(columns={
            "日期": "date", "开盘": "open", "最高": "high",
            "最低": "low", "收盘": "close", "成交量": "volume",
        })
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date")[["open", "high", "low", "close", "volume"]].sort_index()

    def _fetch_yfinance(self, symbol: str, period: str, start: str, end: str) -> pd.DataFrame:
        import yfinance as yf

        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "60m": "60m", "day": "1d", "week": "1wk",
        }
        if self.market == "HK" and not symbol.endswith(".HK"):
            symbol = f"{symbol}.HK"

        ticker = yf.Ticker(symbol)
        start_fmt = start[:10] if "-" in start else f"{start[:4]}-{start[4:6]}-{start[6:]}"
        end_fmt = end[:10] if "-" in end else f"{end[:4]}-{end[4:6]}-{end[6:]}"
        df = ticker.history(interval=interval_map.get(period, "1d"), start=start_fmt, end=end_fmt)
        if df.empty:
            return df

        df = df.rename(columns={
            "Open": "open", "High": "high", "Low": "low",
            "Close": "close", "Volume": "volume",
        })
        df.index.name = "date"
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df[["open", "high", "low", "close", "volume"]]

    def _fetch_binance(self, symbol: str, period: str, start: str, end: str) -> pd.DataFrame:
        import requests

        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "60m": "1h", "4h": "4h", "day": "1d", "week": "1w",
        }

        def _to_ts(date_str: str) -> int:
            if "-" in date_str:
                dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            else:
                dt = datetime.strptime(date_str, "%Y%m%d")
            return int(dt.timestamp() * 1000)

        start_ts, end_ts = _to_ts(start), _to_ts(end)
        pair = f"{symbol.upper()}USDT"
        all_klines = []
        cursor = start_ts

        while cursor < end_ts:
            resp = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={
                    "symbol": pair,
                    "interval": interval_map.get(period, "1d"),
                    "startTime": cursor,
                    "limit": 1000,
                },
                timeout=15,
            )
            data = resp.json()
            if not data or "code" in data:
                break
            all_klines.extend(data)
            cursor = data[-1][0] + 1
            if len(data) < 1000:
                break
            time.sleep(0.1)

        if not all_klines:
            return pd.DataFrame()

        rows = [{
            "date": pd.to_datetime(k[0], unit="ms"),
            "open": float(k[1]), "high": float(k[2]), "low": float(k[3]),
            "close": float(k[4]), "volume": float(k[5]),
        } for k in all_klines]

        return pd.DataFrame(rows).set_index("date").sort_index()


if __name__ == "__main__":
    for market, symbol in [("A", "000001"), ("US", "BTC"), ("US", "AAPL")]:
        try:
            fetcher = DataFetcher(market)
            df = fetcher.fetch(symbol, period="day", start_date="20250101")
            print(f"[{market}] {symbol}: {len(df)} rows")
        except Exception as e:
            print(f"[{market}] {symbol}: ERROR {e}")
