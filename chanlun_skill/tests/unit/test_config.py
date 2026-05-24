"""Unit tests for config validation."""
import pytest
from core.config import ChanConfig


class TestChanConfig:
    def test_config_defaults(self):
        cfg = ChanConfig(symbol="000001")
        assert cfg.symbol == "000001"
        assert cfg.market == "A"
        assert cfg.period == "day"
        assert cfg.source_priority == ["akshare", "yfinance", "binance"]

    def test_config_explicit(self):
        cfg = ChanConfig(symbol="AAPL", market="US", period="60m", start_date="20240101")
        assert cfg.symbol == "AAPL"
        assert cfg.market == "US"
        assert cfg.source_priority == ["akshare", "yfinance", "binance"]
