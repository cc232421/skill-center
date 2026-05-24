"""
AkShare data source for A-share market.
"""
import pandas as pd
from typing import Optional
from data_api.base import normalize_columns, ensure_float, parse_date_col, validate_df


def fetch_a_stock(
    symbol: str, period: str, start_date: str, end_date: str
) -> Optional[pd.DataFrame]:
    try:
        import akshare as ak
        period_map = {
            "day": "daily", "week": "weekly",
            "60m": "60", "30m": "30", "15m": "15", "5m": "5", "1m": "1"
        }
        p = period_map.get(period, "daily")
        df = ak.stock_zh_a_hist(
            symbol=symbol, period=p, start_date=start_date, end_date=end_date, adjust="qfq"
        )
        df = normalize_columns(df)
        df = df.rename(columns={
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume"
        })
        df = parse_date_col(df, "date")
        cols = ["open", "close", "high", "low", "volume"]
        df = ensure_float(df, cols)
        return df[["date", "open", "high", "low", "close", "volume"]] if validate_df(df) else None
    except Exception:
        return None
