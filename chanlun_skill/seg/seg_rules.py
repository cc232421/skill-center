"""Seg rules for line segment construction."""
from core.types import Bi, SEG_DOWN, SEG_UP


def seg_rules_check(bi: Bi, prev_seg) -> bool:
    if prev_seg is None:
        return True
    if prev_seg.type == SEG_UP and bi.type == BI_DOWN:
        return bi.high > prev_seg.low
    if prev_seg.type == SEG_DOWN and bi.type == BI_UP:
        return bi.low < prev_seg.high
    return False
