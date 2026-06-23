"""Tests for DataFetcher — focuses on Tencent K-line fetcher."""

from datetime import datetime
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from data_fetcher import DataFetcher


def _tencent_response(market: str, code: str, rows: list) -> dict:
    return {
        "code": 0,
        "msg": "",
        "data": {f"{market}{code}": {"qfqday": rows}},
    }


def _row(date: str, o: float, c: float, h: float, lo: float, v: float) -> list:
    return [date, f"{o:.3f}", f"{c:.3f}", f"{h:.3f}", f"{lo:.3f}", f"{v:.3f}"]


SAMPLE_ROWS = [
    _row("2025-01-02", 10.00, 10.50, 10.80, 9.90, 1_000_000),
    _row("2025-01-03", 10.50, 10.20, 10.70, 10.10, 800_000),
    _row("2025-01-06", 10.20, 10.80, 10.90, 10.15, 1_200_000),
]


class TestTencentSymbolPrefix:
    def test_shanghai_main_board(self):
        assert DataFetcher("A")._tencent_prefix("600176") == "sh"

    def test_shanghai_star_market(self):
        fetcher = DataFetcher("A")
        assert fetcher._tencent_prefix("688486") == "sh"
        assert fetcher._tencent_prefix("688002") == "sh"

    def test_shanghai_b_share(self):
        assert DataFetcher("A")._tencent_prefix("900901") == "sh"

    def test_shenzhen_main_board(self):
        fetcher = DataFetcher("A")
        assert fetcher._tencent_prefix("002957") == "sz"
        assert fetcher._tencent_prefix("000001") == "sz"

    def test_shenzhen_chinext(self):
        fetcher = DataFetcher("A")
        assert fetcher._tencent_prefix("300750") == "sz"
        assert fetcher._tencent_prefix("300003") == "sz"


class TestTencentFetch:
    @patch("requests.get")
    def test_returns_ohlcv_dataframe_with_correct_schema(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: _tencent_response("sh", "600176", SAMPLE_ROWS),
        )
        df = DataFetcher("A")._fetch_tencent("600176", "day", "20250101", "20251231")

        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert len(df) == 3
        assert df.index.name == "date"
        assert isinstance(df.index, pd.DatetimeIndex)

    @patch("requests.get")
    def test_field_mapping_corrects_tencent_row_order(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: _tencent_response(
                "sh", "600176",
                [_row("2025-01-02", 10.0, 11.0, 12.0, 9.0, 100.0)]
            ),
        )
        df = DataFetcher("A")._fetch_tencent("600176", "day", "20250101", "20250110")

        assert df.iloc[0]["open"] == 10.0
        assert df.iloc[0]["close"] == 11.0
        assert df.iloc[0]["high"] == 12.0
        assert df.iloc[0]["low"] == 9.0
        assert df.iloc[0]["volume"] == 100.0

    @patch("requests.get")
    def test_period_mapping(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: _tencent_response("sh", "600176", SAMPLE_ROWS),
        )
        fetcher = DataFetcher("A")

        fetcher._fetch_tencent("600176", "1m", "20250101", "20250110")
        assert "m1" in mock_get.call_args.kwargs["params"]["param"]

        fetcher._fetch_tencent("600176", "60m", "20250101", "20250110")
        assert "m60" in mock_get.call_args.kwargs["params"]["param"]

        fetcher._fetch_tencent("600176", "week", "20250101", "20251231")
        assert "week" in mock_get.call_args.kwargs["params"]["param"]

    @patch("requests.get")
    def test_requests_qfq_adjustment(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: _tencent_response("sh", "600176", SAMPLE_ROWS),
        )
        DataFetcher("A")._fetch_tencent("600176", "day", "20250101", "20250110")
        assert mock_get.call_args.kwargs["params"]["param"].endswith(",qfq")

    @patch("requests.get")
    def test_url_uses_correct_endpoint(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: _tencent_response("sz", "002957", SAMPLE_ROWS),
        )
        DataFetcher("A")._fetch_tencent("002957", "day", "20250101", "20250110")
        assert mock_get.call_args.args[0] == "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

    @patch("requests.get")
    def test_empty_response_returns_empty_dataframe(self, mock_get):
        mock_get.return_value = MagicMock(
            json=lambda: {"code": 0, "msg": "", "data": {}},
        )
        df = DataFetcher("A")._fetch_tencent("600176", "day", "20250101", "20250110")
        assert df.empty


class TestSourceRouting:
    def test_a_stock_prefers_tencent(self):
        fetcher = DataFetcher("A")
        assert fetcher._resolve_source("600176") == "tencent"
        assert fetcher._resolve_source("688486") == "tencent"
        assert fetcher._resolve_source("002957") == "tencent"

    def test_falls_back_to_akshare_when_tencent_fails(self, monkeypatch):
        fetcher = DataFetcher("A")
        sentinel_df = pd.DataFrame(
            {"open": [1.0], "high": [2.0], "low": [0.5], "close": [1.5], "volume": [100]},
            index=pd.DatetimeIndex([pd.Timestamp("2025-01-02")]),
        )

        def _boom(*a, **kw):
            raise RuntimeError("tencent down")

        monkeypatch.setattr(fetcher, "_fetch_tencent", _boom)
        monkeypatch.setattr(fetcher, "_fetch_akshare", lambda *a, **kw: sentinel_df)
        df = fetcher.fetch("600176", "day", "20250101", "20250110")
        assert df is sentinel_df
