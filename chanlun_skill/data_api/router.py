"""
Data source router with fallback support.
Config-driven source priority selection.
"""
from typing import Optional
import pandas as pd
from core.config import ChanConfig
from data_api.ak_share_api import fetch_a_stock
from data_api.yfinance_api import fetch_yf
from data_api.binance_api import fetch_binance


def fetch_with_fallback(config: ChanConfig) -> Optional[pd.DataFrame]:
    for source in config.source_priority:
        result = _fetch_one(source, config)
        if result is not None and not result.empty:
            return result
    return None


def _fetch_one(source: str, config: ChanConfig) -> Optional[pd.DataFrame]:
    if source == "akshare":
        return _fetch_akshare(config)
    elif source == "yfinance":
        return _fetch_yfinance(config)
    elif source == "binance":
        return _fetch_binance(config)
    return None


def _fetch_akshare(config: ChanConfig) -> Optional[pd.DataFrame]:
    if config.market == "A":
        return fetch_a_stock(
            config.symbol, config.period,
            config.start_date or "20240101", config.end_date or "20250101"
        )
    return None


def _fetch_yfinance(config: ChanConfig) -> Optional[pd.DataFrame]:
    ticker = config.symbol
    if config.market == "HK":
        ticker = f"{config.symbol}.HK"
    return fetch_yf(ticker, config.period, config.start_date or "20240101", config.end_date or "20250101")


def _fetch_binance(config: ChanConfig) -> Optional[pd.DataFrame]:
    return fetch_binance(config.symbol.upper(), config.period)
