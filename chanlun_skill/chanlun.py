import numpy as np
import pandas as pd

try:
    import talib
    TALIB = True
except ImportError:
    import ta.trend as _ta_trend
    import ta.volatility as _ta_vol
    TALIB = False

from dataclasses import dataclass, field
from typing import List, Optional, Dict


FX_DING = "ding"
FX_DI = "di"
BI_UP = "up"
BI_DOWN = "down"
ZS_ZD = "zd"


@dataclass
class KLineRaw:
    index: int
    date: str
    h: float
    l: float
    o: float
    c: float
    v: float


@dataclass
class CLKn:
    index: int
    k_index: int
    date: str
    h: float
    l: float
    o: float
    c: float
    v: float
    klines: List[KLineRaw] = field(default_factory=list)
    n: int = 0
    has_gap: bool = False


@dataclass
class Fractal:
    type: str
    k: CLKn
    val: float
    real: bool = True
    done: bool = True
    index: int = 0
    has_gap: bool = False


@dataclass
class Stroke:
    start: Fractal
    end: Fractal = None
    type: str = None
    high: float = None
    low: float = None
    done: bool = True
    td: bool = False
    index: int = 0
    fx_invalid_count: int = 0
    ld: Dict = field(default_factory=dict)
    qs_beichi: bool = False
    pz_beichi: bool = False
    mmds: List[str] = field(default_factory=list)


@dataclass
class ZhongShu:
    zg: float
    zd: float
    gg: float
    dd: float
    bis: List[Stroke]
    type: str = ZS_ZD
    index: int = 0
    is_high_level: bool = False
    level: int = 0


def interval_overlap(a_h, a_l, b_h, b_l):
    lo = max(a_l, b_l)
    hi = min(a_h, b_h)
    return [hi, lo] if lo <= hi else None


def parse_date(d: str) -> str:
    return str(d).replace("+08:00", "").strip()


class ChanLunEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.klines_raw: List[KLineRaw] = []
        self.cl_klines: List[CLKn] = []
        self.fractals: List[Fractal] = []
        self.strokes: List[Stroke] = []
        self.zhongshus: List[ZhongShu] = []
        self.idx: Dict = {}

        self._init_klines(df)
        self._calculate_idx()

    def _init_klines(self, df: pd.DataFrame):
        for i in range(len(df)):
            row = df.iloc[i]
            k = KLineRaw(
                index=i,
                date=parse_date(str(row['date'])),
                h=float(row['high']),
                l=float(row['low']),
                o=float(row['open']),
                c=float(row['close']),
                v=float(row.get('volume', 0.0)),
            )
            self.klines_raw.append(k)
            self._merge_one_kline(k)

        for i, ck in enumerate(self.cl_klines):
            ck.index = i

    def _merge_one_kline(self, k: KLineRaw):
        new_cl = CLKn(
            index=len(self.cl_klines),
            k_index=k.index,
            date=k.date,
            h=k.h, l=k.l, o=k.o, c=k.c, v=k.v,
            klines=[k], n=1, has_gap=False
        )

        if len(self.klines_raw) > 2:
            prev_raw = self.klines_raw[-2]
            if prev_raw.l > k.h or prev_raw.h < k.l:
                self.cl_klines.append(CLKn(
                    index=len(self.cl_klines),
                    k_index=k.index,
                    date=k.date,
                    h=min(k.l, prev_raw.l),
                    l=max(k.h, prev_raw.h),
                    o=k.o, c=k.c, v=0.0,
                    has_gap=True
                ))

        if len(self.cl_klines) <= 1:
            self.cl_klines.append(new_cl)
            return

        prev = self.cl_klines[-1]
        prev2 = self.cl_klines[-2]

        qushi = "up" if prev.h > prev2.h else "down"

        contain = (
            (prev.h >= k.h and prev.l <= k.l) or
            (k.h >= prev.h and k.l <= prev.l)
        ) and not (prev.h == k.h and prev.l == k.l)

        if contain:
            if qushi == "up":
                prev.h = max(prev.h, k.h)
                prev.l = max(prev.l, k.l)
            else:
                prev.h = min(prev.h, k.h)
                prev.l = min(prev.l, k.l)
            prev.v += k.v
            prev.n += 1
            prev.klines.append(k)
        else:
            self.cl_klines.append(new_cl)

    def _calculate_idx(self):
        prices = np.array([k.c for k in self.klines_raw])
        if TALIB:
            dif, dea, hist = talib.MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9)
            boll_u, boll_m, boll_l = talib.BBANDS(prices, timeperiod=20)
        else:
            s = pd.Series(prices)
            m = _ta_trend.MACD(s, window_fast=12, window_slow=26, window_sign=9)
            dif = m.macd().values
            dea = m.macd_signal().values
            hist = m.macd_diff().values
            bb = _ta_vol.BollingerBands(s, window=20)
            boll_u = bb.bollinger_hband().values
            boll_m = bb.bollinger_mavg().values
            boll_l = bb.bollinger_lband().values
        self.idx = {
            'dif': dif, 'dea': dea, 'hist': hist,
            'boll_u': boll_u, 'boll_m': boll_m, 'boll_l': boll_l,
        }

    def find_fractals(self) -> List[Fractal]:
        fxs = []
        for i in range(1, len(self.cl_klines) - 1):
            prev = self.cl_klines[i - 1]
            curr = self.cl_klines[i]
            nxt = self.cl_klines[i + 1]

            fx = None
            if prev.h < curr.h > nxt.h and prev.l < curr.l > nxt.l:
                tk = prev.h < curr.l or curr.l > nxt.h
                fx = Fractal(type=FX_DING, k=curr, val=curr.h, has_gap=tk)
            elif prev.h > curr.h < nxt.h and prev.l > curr.l < nxt.l:
                tk = prev.l > curr.h or curr.h < nxt.l
                fx = Fractal(type=FX_DI, k=curr, val=curr.l, has_gap=tk)

            if fx is None:
                continue

            if not fxs:
                fxs.append(fx)
                continue

            last_real = self._last_real_fx(fxs)
            if last_real is None:
                fxs.append(fx)
                continue

            self._filter_fx(fx, last_real)
            fxs.append(fx)

        self._append_unfinished_fx(fxs)

        for i, f in enumerate(fxs):
            f.index = i
        self.fractals = fxs
        return fxs

    def _last_real_fx(self, fxs: List[Fractal]) -> Optional[Fractal]:
        for i in range(len(fxs) - 1, -1, -1):
            if fxs[i].real:
                return fxs[i]
        return None

    def _filter_fx(self, fx: Fractal, last_real: Fractal):
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

    def _append_unfinished_fx(self, fxs: List[Fractal]):
        last_real = self._last_real_fx(fxs)
        if last_real is None:
            return
        end_k = self.cl_klines[-1]

        if last_real.type == FX_DING and end_k.h > last_real.val:
            last_real.real = False
            fxs.append(Fractal(type=FX_DING, k=end_k, val=end_k.h, done=False, real=True))
        elif last_real.type == FX_DI and end_k.l < last_real.val:
            last_real.real = False
            fxs.append(Fractal(type=FX_DI, k=end_k, val=end_k.l, done=False, real=True))

    def draw_strokes(self) -> List[Stroke]:
        strokes = []
        bi = None
        invalid_count = 0

        for fx in self.fractals:
            if not fx.real:
                invalid_count += 1
                continue

            if bi is None:
                bi = Stroke(start=fx)
                continue

            if bi.start.type == fx.type:
                continue

            bi.end = fx
            bi.type = BI_UP if bi.start.type == FX_DI else BI_DOWN
            bi.high = max(bi.start.val, bi.end.val)
            bi.low = min(bi.start.val, bi.end.val)
            bi.done = fx.done
            bi.fx_invalid_count = invalid_count
            bi.ld = self._query_macd_ld(bi.start, bi.end)
            strokes.append(bi)
            bi = None
            invalid_count = 0

        if strokes:
            self._detect_stroke_td(strokes[-1])

        for i, s in enumerate(strokes):
            s.index = i
            raw_high = max(s.high, *[k.h for k in self.klines_raw[s.start.k.k_index:s.end.k.k_index + 1]])
            raw_low = min(s.low, *[k.l for k in self.klines_raw[s.start.k.k_index:s.end.k.k_index + 1]])
            s.high = raw_high
            s.low = raw_low

        self.strokes = strokes
        return strokes

    def _detect_stroke_td(self, last_stroke: Optional[Stroke]):
        if last_stroke is None or not last_stroke.done:
            return
        if len(self.cl_klines) <= last_stroke.end.k.index + 1:
            return

        next_cl = self.cl_klines[last_stroke.end.k.index + 1]
        for raw_k in self.klines_raw[last_stroke.end.k.k_index + 1:]:
            if last_stroke.type == BI_UP and raw_k.c < next_cl.l:
                last_stroke.td = True
                break
            if last_stroke.type == BI_DOWN and raw_k.c > next_cl.h:
                last_stroke.td = True
                break

    def _query_macd_ld(self, start_fx: Fractal, end_fx: Fractal) -> Dict:
        s = start_fx.k.k_index
        e = end_fx.k.k_index + 1
        hist = self.idx['hist'][s:e]
        dif = self.idx['dif'][s:e]
        dea = self.idx['dea'][s:e]
        return {
            'hist_sum': float(np.abs(hist).sum()),
            'dif_end': float(dif[-1]) if len(dif) else 0.0,
            'dea_end': float(dea[-1]) if len(dea) else 0.0,
        }

    def find_zhongshus(self) -> List[ZhongShu]:
        if len(self.strokes) < 3:
            self.zhongshus = []
            return []

        zss = []
        i = 0
        while i <= len(self.strokes) - 3:
            window = self.strokes[i:i + 3]
            zs = self._build_zs_one(window)
            if zs is not None:
                if zss:
                    prev_bi_idx = zs.bis[0].index - 1
                    end_bi = self.strokes[i + 2]
                    prev_bi = self.strokes[prev_bi_idx] if prev_bi_idx >= 0 else None
                    if prev_bi and self._compare_beichi(prev_bi, end_bi, zss[-1], zs):
                        end_bi.pz_beichi = True
                zss.append(zs)
                i += 3
            else:
                i += 1

        for idx, zs in enumerate(zss):
            zs.index = idx
            if idx > 0 and self._zs_overlap(zss[idx - 1], zs):
                zs.is_high_level = True
                zs.level = len(zs.bis) // 3

        self.zhongshus = zss
        return zss

    def _build_zs_one(self, strokes: List[Stroke]) -> Optional[ZhongShu]:
        if len(strokes) < 3:
            return None

        gg = max(s.high for s in strokes)
        dd = min(s.low for s in strokes)

        fanwei = [strokes[0].high, strokes[0].low]
        for bi in strokes[1:]:
            cross = interval_overlap(fanwei[0], fanwei[1], bi.high, bi.low)
            if cross is None:
                return None
            fanwei = cross

        return ZhongShu(
            zg=fanwei[0], zd=fanwei[1],
            gg=gg, dd=dd, bis=strokes, type=ZS_ZD
        )

    def _compare_beichi(self, bi1: Stroke, bi2: Stroke,
                          zs1: ZhongShu, zs2: ZhongShu) -> bool:
        return bi2.ld['hist_sum'] < bi1.ld['hist_sum']

    def _zs_overlap(self, zs1: ZhongShu, zs2: ZhongShu) -> bool:
        return interval_overlap(zs1.zg, zs1.zd, zs2.zg, zs2.zd) is not None

    def find_mm_points(self):
        for bi in self.strokes:
            bi.mmds = []

            if bi.pz_beichi or bi.qs_beichi:
                bi.mmds.append("1sell" if bi.type == BI_UP else "1buy")

            zs = self._find_bi_zs(bi)
            prev2_bi = self.strokes[bi.index - 2] if bi.index >= 2 else None

            if prev2_bi and (prev2_bi.mmds or bi.index > 0):
                if bi.type == BI_DOWN and bi.low > prev2_bi.low:
                    bi.mmds.append("2buy")
                elif bi.type == BI_UP and bi.high < prev2_bi.high:
                    bi.mmds.append("2sell")

            if prev2_bi and "2buy" in prev2_bi.mmds:
                if bi.type == BI_DOWN and bi.ld['hist_sum'] < prev2_bi.ld['hist_sum']:
                    bi.mmds.append("l2buy")
            if prev2_bi and "2sell" in prev2_bi.mmds:
                if bi.type == BI_UP and bi.ld['hist_sum'] < prev2_bi.ld['hist_sum']:
                    bi.mmds.append("l2sell")

            if zs and len(zs.bis) >= 1:
                last_in_zs = zs.bis[-1]
                if bi.type == BI_DOWN and bi.low > zs.zg and bi.index - last_in_zs.index == 2:
                    bi.mmds.append("3buy")
                if bi.type == BI_UP and bi.high < zs.zd and bi.index - last_in_zs.index == 2:
                    bi.mmds.append("3sell")

    def _find_bi_zs(self, bi: Stroke) -> Optional[ZhongShu]:
        candidate = None
        for zs in self.zhongshus:
            if zs.bis[0].start.index < bi.start.index:
                candidate = zs
        return candidate

    def analyze(self) -> Dict:
        self.find_fractals()
        self.draw_strokes()
        self.find_zhongshus()
        self.find_mm_points()
        return self.build_result()

    def build_result(self) -> Dict:
        return {
            "klines_count": len(self.klines_raw),
            "cl_klines_count": len(self.cl_klines),
            "fractals": [
                {
                    "index": f.index,
                    "type": f.type,
                    "date": f.k.date,
                    "val": round(f.val, 3),
                    "real": f.real,
                    "done": f.done,
                    "gap": f.has_gap,
                }
                for f in self.fractals
            ],
            "strokes": [
                {
                    "index": s.index,
                    "type": s.type,
                    "start_date": s.start.k.date,
                    "end_date": s.end.k.date,
                    "high": round(s.high, 3),
                    "low": round(s.low, 3),
                    "done": s.done,
                    "td": s.td,
                    "qs_beichi": s.qs_beichi,
                    "pz_beichi": s.pz_beichi,
                    "mmds": s.mmds,
                    "ld_hist_sum": round(s.ld.get('hist_sum', 0.0), 6),
                }
                for s in self.strokes
            ],
            "zhongshus": [
                {
                    "index": z.index,
                    "type": z.type,
                    "zg": round(z.zg, 3),
                    "zd": round(z.zd, 3),
                    "gg": round(z.gg, 3),
                    "dd": round(z.dd, 3),
                    "high_level": z.is_high_level,
                    "stroke_count": len(z.bis),
                }
                for z in self.zhongshus
            ],
            "current_trend": "上涨" if (self.strokes and self.strokes[-1].type == BI_UP) else "下跌",
        }
