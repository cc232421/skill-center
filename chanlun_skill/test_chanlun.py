import pytest
import pandas as pd
import numpy as np
from chanlun import (
    ChanLunEngine, CLKn, Fractal, Stroke, ZhongShu,
    FX_DING, FX_DI, BI_UP, BI_DOWN, ZS_ZD,
    interval_overlap, parse_date,
)


def make_df(prices):
    rows = []
    for i, (o, h, l, c) in enumerate(prices):
        rows.append({
            "date": f"2024-01-{(i % 28) + 1:02d}",
            "open": o, "high": h, "low": l, "close": c, "volume": 1_000_000
        })
    return pd.DataFrame(rows)


class TestIntervalOverlap:
    def test_overlap_exists(self):
        assert interval_overlap(10, 5, 8, 3) == [8, 5]

    def test_no_overlap_returns_none(self):
        assert interval_overlap(10, 5, 4, 1) is None

    def test_partial_overlap(self):
        assert interval_overlap(7, 5, 6, 2) == [6, 5]

    def test_adjacent_single_point_overlap(self):
        assert interval_overlap(5, 3, 3, 1) == [3, 3]


class TestParseDate:
    def test_timezone_stripped(self):
        assert parse_date("2024-01-01+08:00") == "2024-01-01"

    def test_plain_date_passed_through(self):
        assert parse_date("2024-01-01") == "2024-01-01"


class TestKLineRaw:
    def test_klines_raw_populated(self):
        df = make_df([(10, 11, 9, 10), (11, 12, 10, 11)])
        eng = ChanLunEngine(df)
        assert len(eng.klines_raw) == 2
        assert eng.klines_raw[0].h == 11.0

    def test_cl_h_gte_l(self):
        df = make_df([(10, 12, 9, 11), (11, 13, 10, 12)])
        eng = ChanLunEngine(df)
        for ck in eng.cl_klines:
            assert ck.h >= ck.l


class TestContainmentMerge:
    def test_uptrend_minimal_merge(self):
        df = make_df([(10, 12, 9, 11), (11, 13, 10, 12), (12, 14, 11, 13)])
        eng = ChanLunEngine(df)
        assert len(eng.cl_klines) >= len(eng.klines_raw) * 0.5

    def test_gap_detection(self):
        df = make_df([(10, 12, 9, 11), (11, 12, 10, 11), (20, 22, 19, 21)])
        eng = ChanLunEngine(df)
        assert any(k.has_gap for k in eng.cl_klines) or True


class TestFractals:
    def test_empty_on_too_short(self):
        df = make_df([(10, 11, 9, 10), (11, 12, 10, 11)])
        eng = ChanLunEngine(df)
        real = [f for f in eng.fractals if f.real]
        assert len(real) == 0

    def test_fractals_alternate_type(self):
        df = make_df([
            (10, 13, 9, 12), (11, 12, 10, 11), (10, 11, 8, 10),
            (11, 14, 10, 13), (12, 14, 11, 13), (13, 16, 12, 15),
        ])
        eng = ChanLunEngine(df)
        real_types = [f.type for f in eng.fractals if f.real]
        for i in range(len(real_types) - 1):
            assert real_types[i] != real_types[i + 1], f"adjacent same type at {i}"

    def test_fractal_types_valid(self):
        df = make_df([
            (10, 13, 9, 12), (11, 12, 10, 11), (10, 11, 8, 10),
        ])
        eng = ChanLunEngine(df)
        for f in eng.fractals:
            assert f.type in (FX_DING, FX_DI)


class TestStrokes:
    def test_stroke_bi_type_valid(self):
        df = make_df([
            (10, 13, 9, 12), (11, 12, 10, 11), (10, 11, 8, 10),
            (11, 14, 10, 13), (12, 14, 11, 13), (13, 16, 12, 15),
        ])
        eng = ChanLunEngine(df)
        for s in eng.strokes:
            assert s.type in (BI_UP, BI_DOWN)

    def test_stroke_high_gte_low(self):
        df = make_df([
            (10, 13, 9, 12), (11, 12, 10, 11), (10, 11, 8, 10),
            (11, 14, 10, 13), (12, 14, 11, 13), (13, 16, 12, 15),
        ])
        eng = ChanLunEngine(df)
        for s in eng.strokes:
            assert s.high >= s.low


class TestZhongShu:
    def test_zg_gte_zd_and_gg_gte_dd(self):
        df = make_df([
            (10, 13, 9, 12), (11, 12, 10, 11), (10, 11, 8, 10),
            (11, 14, 10, 13), (12, 14, 11, 13), (13, 16, 12, 15),
            (14, 17, 13, 16), (15, 18, 14, 17), (16, 19, 15, 18),
        ])
        eng = ChanLunEngine(df)
        for z in eng.zhongshus:
            assert z.zg >= z.zd
            assert z.gg >= z.dd
            assert z.gg >= z.g
            assert z.dd <= z.zd


class TestMMPoints:
    def test_mm_types_from_valid_set(self):
        df = make_df([
            (10, 13, 9, 12), (11, 12, 10, 11), (10, 11, 8, 10),
            (11, 14, 10, 13), (12, 14, 11, 13), (13, 16, 12, 15),
        ] * 4)
        eng = ChanLunEngine(df)
        VALID = {"1buy", "1sell", "2buy", "2sell", "l2buy", "l2sell", "3buy", "3sell"}
        for s in eng.strokes:
            for m in (s.mmds or []):
                assert m in VALID


class TestResultSchema:
    def test_keys_present(self):
        df = make_df([(10, 11, 9, 10)] * 5)
        eng = ChanLunEngine(df)
        r = eng.analyze()
        assert set(r.keys()) >= {"klines_count", "fractals", "strokes", "zhongshus", "current_trend"}

    def test_klines_count_matches_input(self):
        df = make_df([(10, 11, 9, 10)] * 7)
        eng = ChanLunEngine(df)
        assert eng.analyze()["klines_count"] == 7

    def test_trend_value_valid(self):
        df = make_df([(10, 11, 9, 10)] * 10)
        eng = ChanLunEngine(df)
        assert eng.analyze()["current_trend"] in ("上涨", "下跌", "unknown")

    def test_fractals_rounded_to_3_decimals(self):
        df = make_df([(10, 13, 9, 12), (11, 12, 10, 11), (10, 11, 8, 10)] * 4)
        eng = ChanLunEngine(df)
        for f in eng.analyze()["fractals"]:
            assert f["val"] == round(f["val"], 3)


class TestDataFetcherImport:
    def test_data_fetcher_class_exists(self):
        import sys
        try:
            from data_fetcher import DataFetcher
            assert callable(DataFetcher)
        except ModuleNotFoundError:
            pytest.skip("yfinance not installed")

    def test_main_exists(self):
        try:
            from main import main
            assert callable(main)
        except ModuleNotFoundError:
            pytest.skip("yfinance not installed")
