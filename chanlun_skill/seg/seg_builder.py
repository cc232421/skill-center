"""Seg builder from bi sequence."""
from typing import List
from core.types import Bi, Seg, SEG_DOWN, SEG_UP, SEGMENT_VALID, BI_UP, BI_DOWN


def build_segs(bis: List[Bi]) -> List[Seg]:
    if not bis:
        return []
    segs = []
    seg = None
    for bi in bis:
        if seg is None:
            seg = Seg(start=bi, end=bi, type=SEG_DOWN if bi.type == BI_UP else SEG_UP,
                     level=1, status=SEGMENT_VALID)
            continue
        if bi.type != seg.type:
            if _valid_new_seg(seg, bi):
                seg.end = bi
                seg.high = max(seg.high or 0, bi.high or 0)
                seg.low = min(seg.low or float('inf'), bi.low or 0)
            else:
                segs.append(seg)
                seg = Seg(start=bi, end=bi, type=SEG_DOWN if bi.type == BI_UP else SEG_UP,
                         level=1, status=SEGMENT_VALID)
        else:
            seg.end = bi
            if bi.high:
                seg.high = max(seg.high or 0, bi.high or 0)
            if bi.low:
                seg.low = min(seg.low or float('inf'), bi.low or 0)
    if seg:
        segs.append(seg)
    for i, s in enumerate(segs):
        s.index = i
    return segs


def _valid_new_seg(seg: Seg, bi: Bi) -> bool:
    if seg.type == SEG_UP:
        return bi.high is not None and seg.high is not None and bi.high >= seg.high
    else:
        return bi.low is not None and seg.low is not None and bi.low <= seg.low
