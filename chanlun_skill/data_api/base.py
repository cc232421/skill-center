"""
Data source interface and common utilities.
"""
import pandas as pd
from typing import Optional


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    return df


def ensure_float(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(float)
    return df


def parse_date_col(df: pd.DataFrame, date_col: str, fmt: Optional[str] = None) -> pd.DataFrame:
    if date_col in df.columns:
        df["date"] = pd.to_datetime(df[date_col], format=fmt).dt.strftime("%Y-%m-%d")
    return df


def validate_df(df: Optional[pd.DataFrame]) -> bool:
    if df is None or df.empty:
        return False
    required = {"date", "open", "high", "low", "close"}
    return required.issubset(set(df.columns))
