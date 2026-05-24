"""
Output schema v2 definition.
Required blocks: meta, stats, kline, structures, signals, state
"""
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "2.0"


def make_schema_v2_meta(symbol: str, market: str, period: str, raw_count: int) -> Dict[str, Any]:
    return {
        "symbol": symbol,
        "market": market,
        "period": period,
        "raw_klines": raw_count,
        "schema_version": SCHEMA_VERSION,
    }


def make_schema_v2_stats(
    cl_count: int,
    fractal_count: int,
    bi_count: int,
    seg_count: int,
    zs_count: int,
    bsp_count: int,
    trend: str,
) -> Dict[str, Any]:
    return {
        "combined_klines": cl_count,
        "fractals": fractal_count,
        "bis": bi_count,
        "segs": seg_count,
        "zhongshus": zs_count,
        "buy_sell_points": bsp_count,
        "current_trend": trend,
    }


def make_schema_v2_kline(cl_klines: List[Dict]) -> Dict[str, Any]:
    return {"items": cl_klines, "count": len(cl_klines)}


def make_schema_v2_structures(
    fractals: List[Dict],
    bis: List[Dict],
    segs: List[Dict],
    zss: List[Dict],
) -> Dict[str, List]:
    return {
        "fractals": fractals,
        "bis": bis,
        "segs": segs,
        "zhongshus": zss,
    }


def make_schema_v2_signals(mmds: List[Dict]) -> List[Dict]:
    return mmds


def make_schema_v2_state(unfinished_bi_index: Optional[int], unfinished_seg_index: Optional[int]) -> Dict[str, Any]:
    return {
        "unfinished_bi": unfinished_bi_index,
        "unfinished_seg": unfinished_seg_index,
    }


def build_schema_v2(
    symbol: str,
    market: str,
    period: str,
    raw_count: int,
    cl_klines: List[Dict],
    fractals: List[Dict],
    bis: List[Dict],
    segs: List[Dict],
    zss: List[Dict],
    mmds: List[Dict],
    trend: str,
    unfinished_bi_index: Optional[int] = None,
    unfinished_seg_index: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "meta": make_schema_v2_meta(symbol, market, period, raw_count),
        "stats": make_schema_v2_stats(
            len(cl_klines),
            len(fractals),
            len(bis),
            len(segs),
            len(zss),
            len(mmds),
            trend,
        ),
        "kline": make_schema_v2_kline(cl_klines),
        "structures": make_schema_v2_structures(fractals, bis, segs, zss),
        "signals": make_schema_v2_signals(mmds),
        "state": make_schema_v2_state(unfinished_bi_index, unfinished_seg_index),
    }
