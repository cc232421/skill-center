"""ChanLun core algorithm tests (fractals, strokes, zhongshus)."""

from datetime import datetime, timedelta
import pandas as pd
import pytest

from chanlun_engine import ChanLunEngine


def make_klines(n, start="2024-01-01", **kw):
    base = datetime.strptime(start, "%Y-%m-%d")
    close_fn = kw.get("close_fn", lambda i: 100.0 + i)
    o = kw.get("open", 100.0)
    h = kw.get("high", 101.0)
    l = kw.get("low", 99.0)
    v = kw.get("vol", 1000)
    return [
        {"date": (base + timedelta(days=i)).strftime("%Y-%m-%d"),
         "open": o, "high": h, "low": l, "close": close_fn(i), "volume": v}
        for i in range(n)
    ]


class TestFractalExtraction:
    def test_fractal_output_structure(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert "fractals" in result
            if result["fractals"]:
                fx = result["fractals"][0]
                assert "type" in fx
                assert "date" in fx
                assert "val" in fx
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_fractal_types(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            for fx in result["fractals"]:
                assert fx["type"] in ("ding", "di")
        except ImportError:
            pytest.skip("pychanlun not installed")


class TestStrokeExtraction:
    def test_stroke_output_structure(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert "strokes" in result
            if result["strokes"]:
                stroke = result["strokes"][0]
                assert "index" in stroke
                assert "type" in stroke
                assert "start_date" in stroke
                assert "end_date" in stroke
                assert stroke["type"] in ("up", "down")
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_stroke_alternation(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            strokes = result["strokes"]
            for i in range(len(strokes) - 1):
                assert strokes[i]["type"] != strokes[i + 1]["type"]
        except ImportError:
            pytest.skip("pychanlun not installed")


class TestZhongshuExtraction:
    def test_zhongshu_output_structure(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert "zhongshus" in result
            for zs in result["zhongshus"]:
                assert "index" in zs
                assert "zg" in zs
                assert "zd" in zs
                assert zs["zg"] > zs["zd"]
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_zhongshu_stroke_count(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            for zs in result["zhongshus"]:
                assert len(zs["stroke_indices"]) == 3
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_zhongshu_zg_zd_relationship(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            for zs in result["zhongshus"]:
                assert zs["zg"] > zs["zd"]
                assert zs["gg"] >= zs["zg"]
                assert zs["dd"] <= zs["zd"]
        except ImportError:
            pytest.skip("pychanlun not installed")


class TestTrendDetermination:
    def test_trend_values(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            assert result["current_trend"] in ("上涨", "下跌", "盘整")
        except ImportError:
            pytest.skip("pychanlun not installed")


class TestSummary:
    def test_summary_structure(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            summary = result["summary"]
            assert "divergence_count" in summary
            assert "buy_signals" in summary
            assert "sell_signals" in summary
            assert "signal_strength" in summary
            assert summary["signal_strength"] in ("weak", "medium", "strong")
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_summary_counts(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            summary = result["summary"]
            assert summary["divergence_count"] >= 0
            assert summary["buy_signals"] >= 0
            assert summary["sell_signals"] >= 0
        except ImportError:
            pytest.skip("pychanlun not installed")


class TestBeichiDetection:
    def test_beichi_flags_in_strokes(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            for stroke in result["strokes"]:
                assert "qs_beichi" in stroke
                assert "pz_beichi" in stroke
                assert isinstance(stroke["qs_beichi"], bool)
                assert isinstance(stroke["pz_beichi"], bool)
        except ImportError:
            pytest.skip("pychanlun not installed")


class TestSignals:
    def test_signal_types(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            for sig in result["signals"]:
                assert "date" in sig
                assert "type" in sig
        except ImportError:
            pytest.skip("pychanlun not installed")

    def test_mmds_in_strokes(self, klines_to_df):
        klines = make_klines(60)
        df = klines_to_df(klines)
        try:
            engine = ChanLunEngine(df)
            result = engine.analyze()
            for stroke in result["strokes"]:
                assert "mmds" in stroke
                assert isinstance(stroke["mmds"], list)
        except ImportError:
            pytest.skip("pychanlun not installed")