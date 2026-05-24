"""Divergence detection for BSP."""
from typing import List, Optional
from core.types import Bi, BSP, BSP_BUY, BSP_SELL, SEG_UP, SEG_DOWN, Seg


def detect_divergence(bis: List[Bi], segs: List[Seg]) -> List[BSP]:
    bsps = []
    if len(bis) < 5 or len(segs) < 2:
        return bsps
    for i in range(2, len(bis) - 2):
        b = bis[i]
        if not b.done:
            continue
        bsp = _check_bsp(b, bis, segs)
        if bsp:
            bsps.append(bsp)
    for i, b in enumerate(bsps):
        b.index = i
    return bsps


def _check_bsp(bi: Bi, bis: List[Bi], segs: List[Seg]) -> Optional[BSP]:
    direction = BSP_SELL if bi.type == SEG_UP else BSP_BUY
    pool = [b for b in bis if b.done and b.type != bi.type]
    if not pool:
        return None
    candidates = [b for b in pool if abs(b.high - bi.high) < 0.001 or abs(b.low - bi.low) < 0.001]
    if not candidates:
        return None
    cb = min(candidates, key=lambda x: abs(x.high - bi.high) + abs(x.low - bi.low))
    price = cb.high if direction == BSP_SELL else cb.low
    date = cb.start.k.date if cb.start and cb.start.k else ""
    if direction == BSP_SELL:
        if cb.high >= bi.high:
            return BSP(bi=bi, point_type=BSP_SELL, price=price, date=date)
    else:
        if cb.low <= bi.low:
            return BSP(bi=bi, point_type=BSP_BUY, price=price, date=date)
    return None
