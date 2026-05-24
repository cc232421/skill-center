"""
Serializer for converting internal entities to schema v2 output.
Deterministic conversion with proper rounding and null handling.
"""
from typing import Any, Dict, List, Optional

from core.types import Bi, CombineKLine, Fractal, Seg, ZS, BSP, KLineRaw
from chan_io.schema import build_schema_v2


def serialize_kline_raw(k: KLineRaw) -> Dict[str, Any]:
    return {
        "index": k.index,
        "date": k.date,
        "h": round(k.h, 3),
        "l": round(k.l, 3),
        "o": round(k.o, 3),
        "c": round(k.c, 3),
        "v": round(k.v, 3),
    }


def serialize_combined_kline(k: CombineKLine) -> Dict[str, Any]:
    return {
        "index": k.index,
        "date": k.date,
        "h": round(k.h, 3),
        "l": round(k.l, 3),
        "o": round(k.o, 3),
        "c": round(k.c, 3),
        "v": round(k.v, 3),
        "n": k.n,
        "has_gap": k.has_gap,
    }


def serialize_fractal(f: Fractal) -> Dict[str, Any]:
    return {
        "index": f.index,
        "type": f.type,
        "date": f.k.date,
        "val": round(f.val, 3),
        "real": f.real,
        "done": f.done,
        "gap": f.has_gap,
    }


def serialize_bi(b: Bi) -> Dict[str, Any]:
    return {
        "index": b.index,
        "type": b.type,
        "start_date": b.start.k.date if b.start else None,
        "end_date": b.end.k.date if b.end else None,
        "high": round(b.high, 3) if b.high else None,
        "low": round(b.low, 3) if b.low else None,
        "done": b.done,
        "td": b.td,
        "qs_beichi": b.qs_beichi,
        "pz_beichi": b.pz_beichi,
        "mmds": b.mmds or [],
        "ld_hist_sum": round(b.ld.get("hist_sum", 0.0), 6) if b.ld else 0.0,
    }


def serialize_seg(s: Seg) -> Dict[str, Any]:
    return {
        "index": s.index,
        "type": s.type,
        "start_date": s.start.start.k.date if s.start and s.start.start else None,
        "end_date": s.end.start.k.date if s.end and s.end.start else None,
        "high": round(s.high, 3) if s.high else None,
        "low": round(s.low, 3) if s.low else None,
        "done": s.done,
        "bi_count": s.bi_count,
    }


def serialize_zs(z: ZS) -> Dict[str, Any]:
    return {
        "index": z.index,
        "type": z.type,
        "zg": round(z.zg, 3),
        "zd": round(z.zd, 3),
        "gg": round(z.gg, 3),
        "dd": round(z.dd, 3),
        "high_level": z.is_high_level,
        "level": z.level,
        "seg_count": len(z.segs),
    }


def serialize_bsp(bsp: BSP) -> Dict[str, Any]:
    return {
        "bi_index": bsp.bi.index,
        "type": bsp.point_type,
        "price": round(bsp.price, 3),
        "date": bsp.date,
        "confirmed": bsp.confirmed,
    }


def serialize_full(
    symbol: str,
    market: str,
    period: str,
    raw_klines: List[KLineRaw],
    cl_klines: List[CombineKLine],
    fractals: List[Fractal],
    bis: List[Bi],
    segs: List[Seg],
    zss: List[ZS],
    bsps: List[BSP],
    trend: str,
    unfinished_bi_index: Optional[int] = None,
    unfinished_seg_index: Optional[int] = None,
) -> Dict[str, Any]:
    return build_schema_v2(
        symbol=symbol,
        market=market,
        period=period,
        raw_count=len(raw_klines),
        cl_klines=[serialize_combined_kline(k) for k in cl_klines],
        fractals=[serialize_fractal(f) for f in fractals],
        bis=[serialize_bi(b) for b in bis],
        segs=[serialize_seg(s) for s in segs],
        zss=[serialize_zs(z) for z in zss],
        mmds=[serialize_bsp(b) for b in bsps],
        trend=trend,
        unfinished_bi_index=unfinished_bi_index,
        unfinished_seg_index=unfinished_seg_index,
    )
