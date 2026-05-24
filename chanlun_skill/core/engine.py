from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from core.config import ChanConfig
from core.types import Bi, CombineKLine, Fractal, KLineRaw, Seg, ZS, BSP, BI_UP, BI_DOWN
from kline.raw import df_to_raw
from kline.combine import merge_klines
from chan_io.serializer import serialize_full
from data_api.router import fetch_with_fallback


class ChanEngine:
    def __init__(self, config: ChanConfig, df: Optional[pd.DataFrame] = None):
        self.config = config
        self.df = df
        self.raw_klines: List[KLineRaw] = []
        self.combined_klines: List[CombineKLine] = []
        self.fractals: List[Fractal] = []
        self.bis: List[Bi] = []
        self.segs: List[Seg] = []
        self.zss: List[ZS] = []
        self.bsps: List[BSP] = []
        self.idx: Dict[str, Any] = {}
        if df is not None:
            self._init_klines(df)

    def _init_klines(self, df: pd.DataFrame):
        self.raw_klines = df_to_raw(df)
        self.combined_klines = merge_klines(self.raw_klines)
        self._calculate_idx()

    def _calculate_idx(self):
        prices = np.array([k.c for k in self.raw_klines])
        self.idx = {'prices': prices}

    def analyze(self) -> Dict[str, Any]:
        if not self.combined_klines:
            return {}
        self._find_fractals()
        self._find_bis()
        self._find_segs()
        self._find_zss()
        self._find_bsps()
        return self.serialize()

    def serialize(self) -> Dict[str, Any]:
        trend = _infer_trend(self.bis, self.segs)
        return serialize_full(
            symbol=self.config.symbol,
            market=self.config.market,
            period=self.config.period,
            raw_klines=self.raw_klines,
            cl_klines=self.combined_klines,
            fractals=self.fractals,
            bis=self.bis,
            segs=self.segs,
            zss=self.zss,
            bsps=self.bsps,
            trend=trend,
        )

    def _find_fractals(self):
        from bi.fractal import detect_fractals
        end_k = self.combined_klines[-1] if self.combined_klines else None
        self.fractals = detect_fractals(self.combined_klines, end_k)

    def _find_bis(self):
        from bi.bi_builder import build_bis
        self.bis = build_bis(self.fractals, self.raw_klines, self.idx)

    def _find_segs(self):
        from seg.seg_builder import build_segs
        self.segs = build_segs(self.bis)

    def _find_zss(self):
        from zs.zs_builder import build_zss
        self.zss = build_zss(self.segs)

    def _find_bsps(self):
        from bsp.divergence import detect_divergence
        self.bsps = detect_divergence(self.bis, self.segs)


def _infer_trend(bis: List[Bi], segs: List[Seg]) -> str:
    if not bis:
        return "neutral"
    completed = [b for b in bis if b.done]
    if not completed:
        return "neutral"
    last = completed[-1]
    if last.type == BI_UP and last.high is not None:
        return "up"
    if last.type == BI_DOWN and last.low is not None:
        return "down"
    return "neutral"
