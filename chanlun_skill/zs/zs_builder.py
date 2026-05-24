"""Zhongshu (ZS) builder from seg sequence."""
from typing import List
from core.types import Seg, ZS, ZS_BUY, ZS_SELL, SEG_UP, SEG_DOWN


def build_zss(segs: List[Seg]) -> List[ZS]:
    if len(segs) < 3:
        return []
    zss = []
    for i in range(len(segs) - 2):
        zg_seg = segs[i]
        zd_seg = segs[i + 1]
        gg_seg = segs[i + 2]
        zg_price = zg_seg.high
        zd_price = zd_seg.high if zg_seg.type == SEG_UP else zd_seg.low
        gg_price = max(zg_seg.high, zd_seg.high) if zg_seg.high is not None and zd_seg.high is not None else None
        dd_price = min(zg_seg.low, zd_seg.low) if zg_seg.low is not None and zd_seg.low is not None else None
        if _is_valid_zs(segs[i], segs[i + 1], segs[i + 2]):
            zss.append(ZS(zg=zg_price, zd=zd_price, gg=gg_price, dd=dd_price,
                         segs=[zg_seg, zd_seg, gg_seg],
                         type=ZS_SELL if zg_seg.type == SEG_UP else ZS_BUY))
    for i, z in enumerate(zss):
        z.index = i
    return zss


def _is_valid_zs(s0: Seg, s1: Seg, s2: Seg) -> bool:
    if not all([s0.high, s0.low, s1.high, s1.low, s2.high, s2.low]):
        return False
    if s0.type == SEG_UP:
        return s1.high < s0.high and s2.high < s1.high and s1.low > s0.low and s2.low > s1.low
    else:
        return s1.low > s0.low and s2.low > s1.low and s1.high < s0.high and s2.high < s1.high
