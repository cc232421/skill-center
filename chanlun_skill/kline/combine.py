"""
Combine K-line logic - merge raw klines into combined candles.
Containment rules, gap detection.
"""
from typing import List, Tuple
from core.types import KLineRaw, CombineKLine, BI_UP, BI_DOWN


def merge_klines(raw_klines: List[KLineRaw]) -> List[CombineKLine]:
    if not raw_klines:
        return []
    combined = []
    i = 0
    while i < len(raw_klines):
        k = raw_klines[i]
        new_cl = _make_cl(k, len(combined))
        if len(raw_klines) > 2 and i >= 2:
            prev_raw = raw_klines[i - 2]
            if _has_gap(prev_raw, k):
                gap_cl = _make_gap_cl(prev_raw, k, len(combined))
                combined.append(gap_cl)
        if len(combined) <= 1:
            combined.append(new_cl)
        else:
            _try_merge(combined, new_cl, raw_klines[i].o if i > 0 else None)
        i += 1
    for idx, cl in enumerate(combined):
        cl.index = idx
    return combined


def _has_gap(prev_raw: KLineRaw, k: KLineRaw) -> bool:
    return prev_raw.l > k.h or prev_raw.h < k.l


def _make_cl(k: KLineRaw, idx: int) -> CombineKLine:
    return CombineKLine(
        index=idx, k_index=k.index, date=k.date,
        h=k.h, l=k.l, o=k.o, c=k.c, v=k.v,
        klines=[k], n=1, has_gap=False
    )


def _make_gap_cl(prev_raw: KLineRaw, k: KLineRaw, idx: int) -> CombineKLine:
    return CombineKLine(
        index=idx, k_index=k.index, date=k.date,
        h=min(k.l, prev_raw.l), l=max(k.h, prev_raw.h),
        o=k.o, c=k.c, v=0.0, has_gap=True
    )


def _try_merge(combined: List[CombineKLine], new_cl: CombineKLine, open_price: float):
    if len(combined) <= 1:
        combined.append(new_cl)
        return
    prev = combined[-1]
    prev2 = combined[-2]
    qushi = BI_UP if prev.h > prev2.h else BI_DOWN
    contain = _is_contain(prev, new_cl, qushi)
    if contain:
        _apply_merge(prev, new_cl, qushi)
    else:
        combined.append(new_cl)


def _is_contain(prev: CombineKLine, k: KLineRaw, qushi: str) -> bool:
    if prev.h >= k.h and prev.l <= k.l:
        return True
    if k.h >= prev.h and k.l <= prev.l:
        return prev.h != k.h or prev.l != k.l
    return False


def _apply_merge(prev: CombineKLine, k: KLineRaw, qushi: str):
    if qushi == BI_UP:
        prev.h = max(prev.h, k.h)
        prev.l = max(prev.l, k.l)
    else:
        prev.h = min(prev.h, k.h)
        prev.l = min(prev.l, k.l)
    prev.v += k.v
    prev.n += 1
    prev.klines.append(k)
