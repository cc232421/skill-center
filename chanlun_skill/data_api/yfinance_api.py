"""
yfinance data source for HK/US markets.
"""
import pandas as pd
from typing import Optional
from data_api.base import normalize_columns, ensure_float, parse_date_col, validate_df


def fetch_yf(
    ticker: str, period: str, start_date: str, end_date: str
) -> Optional[pd.DataFrame]:
    try:
        import yfinance as yf
        period_map = {
            "day": "1d", "week": "1wk",
            "60m": "60m", "30m": "30m", "15m": "15m", "5m": "5m", "1m": "1m",
        }
        p = period_map.get(period, "1d")
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.download(start=start_date, end=end_date, period=p, progress=False)
        if df.empty:
            return None
        df = df.reset_index()
        if "Price" in df.columns:
            df = df["Price"]
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = normalize_columns(df)
        df = parse_date_col(df, df.columns[0])
        df = df.rename(columns={
            "Open": "open", "Close": "close",
            "High": "high", "Low": "low", "Volume": "volume"
        })
        cols = ["open", "close", "high", "low", "volume"]
        df = ensure_float(df, cols)
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return None
