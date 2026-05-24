"""
Bi (stroke/笔) builder from fractal sequence.
Ported from ChanLunEngine.draw_strokes, _detect_stroke_td, _query_macd_ld.
"""
from typing import Dict, List, Optional
import numpy as np
from core.types import Bi, Fractal, FX_DING, BI_UP, BI_DOWN


def build_bis(fractals: List[Fractal], raw_klines, idx_metrics: Dict) -> List[Bi]:
    strokes = []
    bi = None
    invalid_count = 0
    for fx in fractals:
        if not fx.real:
            invalid_count += 1
            continue
        if bi is None:
            bi = Bi(start=fx)
            continue
        if bi.start.type == fx.type:
            continue
        bi.end = fx
        bi.type = BI_DOWN if bi.start.type == FX_DING else BI_UP
        bi.high = max(bi.start.val, bi.end.val)
        bi.low = min(bi.start.val, bi.end.val)
        bi.done = fx.done
        bi.fx_invalid_count = invalid_count
        bi.ld = _calc_ld(bi, raw_klines, idx_metrics)
        strokes.append(bi)
        bi = None
        invalid_count = 0
    if strokes:
        _detect_td(strokes[-1], raw_klines)
    _normalize_bi_bounds(strokes, raw_klines)
    for i, s in enumerate(strokes):
        s.index = i
    return strokes


def _calc_ld(bi: Bi, raw_klines, idx_metrics: Dict) -> Dict:
    s = bi.start.k.k_index
    e = bi.end.k.k_index + 1
    hist = idx_metrics.get('hist', [])
    dif = idx_metrics.get('dif', [])
    dea = idx_metrics.get('dea', [])
    if not hist or s >= len(hist) or e > len(hist):
        return {'hist_sum': 0.0, 'dif_end': 0.0, 'dea_end': 0.0}
    h = hist[s:e]
    d = dif[s:e]
    da = dea[s:e]
    return {
        'hist_sum': float(np.abs(h).sum()),
        'dif_end': float(d[-1]) if len(d) else 0.0,
        'dea_end': float(da[-1]) if len(da) else 0.0,
    }


def _detect_td(last_stroke: Bi, raw_klines):
    if not last_stroke or not last_stroke.done:
        return
    if last_stroke.end.k.k_index + 1 >= len(raw_klines):
        return
    next_cl = raw_klines[last_stroke.end.k.k_index + 1]
    search_slice = raw_klines[last_stroke.end.k.k_index + 1:]
    for raw_k in search_slice:
        if last_stroke.type == BI_UP and raw_k.c < next_cl.l:
            last_stroke.td = True
            break
        if last_stroke.type == BI_DOWN and raw_k.c > next_cl.h:
            last_stroke.td = True
            break


def _normalize_bi_bounds(strokes: List[Bi], raw_klines):
    for s in strokes:
        s_idx = s.start.k.k_index
        e_idx = s.end.k.k_index + 1 if s.end else s_idx + 1
        raw_slice = raw_klines[s_idx:e_idx]
        if not raw_slice:
            continue
        if s.high is not None and raw_slice:
            s.high = max(s.high, max(k.h for k in raw_slice))
        if s.low is not None and raw_slice:
            s.low = min(s.low, min(k.l for k in raw_slice))
