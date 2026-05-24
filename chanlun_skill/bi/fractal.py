"""
Fractal detection from combined klines.
Ported from ChanLunEngine.find_fractals, _filter_fx, _append_unfinished_fx.
"""
from typing import List, Optional
from core.types import CombineKLine, Fractal, FX_DING, FX_DI


def detect_fractals(cl_klines: List[CombineKLine], end_k: CombineKLine) -> List[Fractal]:
    fxs = []
    for i in range(1, len(cl_klines) - 1):
        prev = cl_klines[i - 1]
        curr = cl_klines[i]
        nxt = cl_klines[i + 1]
        fx = _detect_one(prev, curr, nxt)
        if fx is None:
            continue
        if not fxs:
            fxs.append(fx)
            continue
        last_real = _last_real(fxs)
        if last_real is None:
            fxs.append(fx)
            continue
        _filter_fx(fx, last_real)
        fxs.append(fx)
    _append_unfinished(fxs, end_k)
    for idx, f in enumerate(fxs):
        f.index = idx
    return fxs


def _detect_one(prev: CombineKLine, curr: CombineKLine, nxt: CombineKLine) -> Optional[Fractal]:
    if prev.h < curr.h > nxt.h and prev.l < curr.l > nxt.l:
        tk = prev.h < curr.l or curr.l > nxt.h
        return Fractal(type=FX_DING, k=curr, val=curr.h, real=True, done=True, has_gap=tk)
    if prev.h > curr.h < nxt.h and prev.l > curr.l < nxt.l:
        tk = prev.l > curr.h or curr.h < nxt.l
        return Fractal(type=FX_DI, k=curr, val=curr.l, real=True, done=True, has_gap=tk)
    return None


def _last_real(fxs: List[Fractal]) -> Optional[Fractal]:
    for i in range(len(fxs) - 1, -1, -1):
        if fxs[i].real:
            return fxs[i]
    return None


def _filter_fx(fx: Fractal, last_real: Fractal):
    same_type = fx.type == last_real.type
    if same_type and fx.type == FX_DING:
        last_real.real = last_real.val > fx.val
        fx.real = not last_real.real
    elif same_type and fx.type == FX_DI:
        last_real.real = last_real.val < fx.val
        fx.real = not last_real.real
    elif fx.type == FX_DING and last_real.type == FX_DI:
        fx.real = not (fx.val <= last_real.val or fx.k.l <= last_real.k.h)
    elif fx.type == FX_DI and last_real.type == FX_DING:
        fx.real = not (fx.val >= last_real.val or fx.k.h >= last_real.k.l)
    else:
        fx.real = fx.k.index - last_real.k.index >= 4


def _append_unfinished(fxs: List[Fractal], end_k: CombineKLine):
    last_real = _last_real(fxs)
    if last_real is None:
        return
    if last_real.type == FX_DING and end_k.h > last_real.val:
        last_real.real = False
        fxs.append(Fractal(type=FX_DING, k=end_k, val=end_k.h, done=False, real=True))
    elif last_real.type == FX_DI and end_k.l < last_real.val:
        last_real.real = False
        fxs.append(Fractal(type=FX_DI, k=end_k, val=end_k.l, done=False, real=True))
