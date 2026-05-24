"""
Configuration center for Chanlun analysis.
"""
from dataclasses import dataclass
from typing import List, Optional

MARKETS = {"A", "HK", "US", "CRYPTO"}
PERIODS = {"1m", "5m", "15m", "30m", "60m", "4h", "day", "week"}
SOURCE_PRIORITY_DEFAULT = ["akshare", "yfinance", "binance"]


@dataclass
class ChanConfig:
    symbol: str = "000001"
    market: str = "A"
    period: str = "day"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    source_priority: List[str] = None
    algo_macd_fast: int = 12
    algo_macd_slow: int = 26
    algo_macd_signal: int = 9
    algo_boll_window: int = 20

    def __post_init__(self):
        if self.source_priority is None:
            if self.market == "CRYPTO":
                self.source_priority = ["binance"]
            else:
                self.source_priority = SOURCE_PRIORITY_DEFAULT.copy()
        self._validate()

    def _validate(self) -> None:
        if self.market not in MARKETS:
            raise ValueError(f"Unsupported market: {self.market}. Must be one of {MARKETS}")
        if self.period not in PERIODS:
            raise ValueError(f"Unsupported period: {self.period}. Must be one of {PERIODS}")
        for src in self.source_priority:
            if src not in ["akshare", "yfinance", "binance"]:
                raise ValueError(f"Unsupported source: {src}")
