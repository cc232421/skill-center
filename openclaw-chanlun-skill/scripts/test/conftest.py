"""Pytest configuration and shared fixtures for ChanLun tests."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"
STANDARD_KLINES_FILE = FIXTURES_DIR / "standard_klines.json"


def make_klines(n: int, start_date: str = "2024-01-01", **price_kwargs) -> List[Dict]:
    """Generate n K-lines with sequential dates.

    price_kwargs: can include close_fn(i), open_val, high_val, low_val, volume_val
    """
    base = datetime.strptime(start_date, "%Y-%m-%d")
    close_fn = price_kwargs.get("close_fn", lambda i: 100.0 + i)
    open_val = price_kwargs.get("open_val", 100.0)
    high_val = price_kwargs.get("high_val", 101.0)
    low_val = price_kwargs.get("low_val", 99.0)
    vol_val = price_kwargs.get("volume_val", 1000)
    return [
        {
            "date": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
            "open": open_val if callable(open_val) else open_val,
            "high": high_val if callable(high_val) else high_val,
            "low": low_val if callable(low_val) else low_val,
            "close": close_fn(i),
            "volume": vol_val if callable(vol_val) else vol_val,
        }
        for i in range(n)
    ]


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def standard_klines_data() -> List[Dict]:
    with open(STANDARD_KLINES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def simple_uptrend() -> List[Dict]:
    """Simple uptrend K-line data for testing."""
    return {
        "name": "简单上涨趋势",
        "description": "连续上涨K线，用于测试顶分型识别",
        "data": [
            {"date": "2024-01-02", "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.8, "volume": 1000},
            {"date": "2024-01-03", "open": 100.8, "high": 102.0, "low": 100.5, "close": 101.5, "volume": 1100},
            {"date": "2024-01-04", "open": 101.5, "high": 103.5, "low": 101.0, "close": 103.0, "volume": 1200},
            {"date": "2024-01-05", "open": 103.0, "high": 104.0, "low": 102.5, "close": 103.5, "volume": 1150},
            {"date": "2024-01-08", "open": 103.5, "high": 105.0, "low": 103.0, "close": 104.5, "volume": 1300},
            {"date": "2024-01-09", "open": 104.5, "high": 106.0, "low": 104.0, "close": 105.5, "volume": 1400},
            {"date": "2024-01-10", "open": 105.5, "high": 106.5, "low": 105.0, "close": 106.0, "volume": 1350},
            {"date": "2024-01-11", "open": 106.0, "high": 107.0, "low": 105.5, "close": 106.5, "volume": 1380},
            {"date": "2024-01-12", "open": 106.5, "high": 105.0, "low": 104.0, "close": 104.5, "volume": 1200},
            {"date": "2024-01-15", "open": 104.5, "high": 105.0, "low": 103.0, "close": 103.5, "volume": 1100}
        ]
    }


@pytest.fixture(scope="session")
def simple_downtrend() -> List[Dict]:
    """Simple downtrend K-line data for testing."""
    return {
        "name": "简单下跌趋势",
        "description": "连续下跌K线，用于测试底分型识别",
        "data": [
            {"date": "2024-01-02", "open": 110.0, "high": 110.5, "low": 109.5, "close": 109.8, "volume": 1000},
            {"date": "2024-01-03", "open": 109.8, "high": 109.5, "low": 108.0, "close": 108.5, "volume": 1100},
            {"date": "2024-01-04", "open": 108.5, "high": 108.0, "low": 106.5, "close": 107.0, "volume": 1200},
            {"date": "2024-01-05", "open": 107.0, "high": 107.5, "low": 105.5, "close": 106.0, "volume": 1150},
            {"date": "2024-01-08", "open": 106.0, "high": 106.5, "low": 104.5, "close": 105.0, "volume": 1300},
            {"date": "2024-01-09", "open": 105.0, "high": 105.5, "low": 103.5, "close": 104.0, "volume": 1400},
            {"date": "2024-01-10", "open": 104.0, "high": 104.5, "low": 103.0, "close": 103.5, "volume": 1350},
            {"date": "2024-01-11", "open": 103.5, "high": 104.0, "low": 102.5, "close": 103.0, "volume": 1380},
            {"date": "2024-01-12", "open": 103.0, "high": 104.5, "low": 103.5, "close": 104.0, "volume": 1200},
            {"date": "2024-01-15", "open": 104.0, "high": 105.0, "low": 104.5, "close": 104.8, "volume": 1100}
        ]
    }


@pytest.fixture(scope="session")
def ding_fenxing() -> List[Dict]:
    """Standard top fractal (顶分型) test data."""
    return {
        "name": "标准顶分型",
        "description": "明确的顶分型形态，中间K线高点最高",
        "data": [
            {"date": "2024-01-01", "open": 100.0, "high": 100.5, "low": 99.0, "close": 99.5, "volume": 1000},
            {"date": "2024-01-02", "open": 99.5, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1100},
            {"date": "2024-01-03", "open": 100.5, "high": 103.0, "low": 100.5, "close": 102.5, "volume": 1200},
            {"date": "2024-01-04", "open": 102.5, "high": 104.0, "low": 102.0, "close": 103.0, "volume": 1150},
            {"date": "2024-01-05", "open": 103.0, "high": 103.5, "low": 102.0, "close": 102.5, "volume": 1100},
            {"date": "2024-01-08", "open": 102.5, "high": 102.0, "low": 100.0, "close": 100.5, "volume": 1000},
            {"date": "2024-01-09", "open": 100.5, "high": 101.0, "low": 99.5, "close": 100.0, "volume": 950}
        ]
    }


@pytest.fixture(scope="session")
def di_fenxing() -> List[Dict]:
    """Standard bottom fractal (底分型) test data."""
    return {
        "name": "标准底分型",
        "description": "明确的底分型形态，中间K线低点最低",
        "data": [
            {"date": "2024-01-01", "open": 105.0, "high": 105.5, "low": 104.5, "close": 105.0, "volume": 1000},
            {"date": "2024-01-02", "open": 105.0, "high": 104.5, "low": 103.0, "close": 103.5, "volume": 1100},
            {"date": "2024-01-03", "open": 103.5, "high": 104.0, "low": 101.0, "close": 102.0, "volume": 1200},
            {"date": "2024-01-04", "open": 102.0, "high": 103.0, "low": 101.5, "close": 102.5, "volume": 1150},
            {"date": "2024-01-05", "open": 102.5, "high": 103.5, "low": 102.5, "close": 103.0, "volume": 1100},
            {"date": "2024-01-08", "open": 103.0, "high": 104.5, "low": 103.0, "close": 104.0, "volume": 1000},
            {"date": "2024-01-09", "open": 104.0, "high": 105.0, "low": 104.0, "close": 104.5, "volume": 950}
        ]
    }


@pytest.fixture
def klines_to_df() -> callable:
    """Convert K-line list to DataFrame with date index."""
    def _convert(klines: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(klines)
        df["date"] = pd.to_datetime(df["date"], format="mixed")
        df = df.set_index("date").sort_index()
        return df
    return _convert


@pytest.fixture
def sample_price_series() -> np.ndarray:
    """Sample price series for MACD testing."""
    # Simple ascending prices for predictable MACD output
    return np.array([100.0 + i for i in range(50)])


@pytest.fixture
def sample_macd_params() -> dict:
    """Standard MACD parameters."""
    return {
        "fast": 12,
        "slow": 26,
        "signal": 9
    }