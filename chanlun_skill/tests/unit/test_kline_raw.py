"""Unit tests for KLineRaw construction."""
import pytest
from core.types import KLineRaw, parse_date


class TestKLineRaw:
    def test_parse_date_strips_timezone(self):
        assert parse_date("2024-01-01+08:00") == "2024-01-01"

    def test_kline_raw_index(self):
        k = KLineRaw(index=0, date="2024-01-01", h=100.0, l=90.0, o=95.0, c=98.0)
        assert k.index == 0
        assert k.h == 100.0

    def test_kline_raw_immutable(self):
        k = KLineRaw(index=0, date="2024-01-01", h=100.0, l=90.0, o=95.0, c=98.0, v=1000.0)
        assert k.v == 1000.0
        assert k.c == 98.0
