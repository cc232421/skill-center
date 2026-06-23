"""缠论分析引擎 v4.0

升级内容:
- 参数化配置: 从 params.json 加载超参数，支持进化调优
- EVOLVE_ZONE: 代码级进化预留标记区域
- 独立中枢算法: 基于笔序列直接计算中枢
- 趋势背驰: 基于pivot level + MACD divergence
- 盘整背驰: 同向笔MACD力度比较
- 综合评分: 信号数量 + 背驰 + 位置
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


# ──────────────────── 参数配置加载 ────────────────────

DEFAULT_PARAMS = {
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "fractal": {"strictness": 1.0},
    "stroke": {"min_bars": 5, "merge_threshold": 0.0},
    "beichi": {"pz_area_ratio": 0.6, "macd_divergence_threshold": 0.05},
    "mm_score_weights": {
        "1buy": 30, "2buy": 25, "3buy": 20, "l2buy": 15,
        "1sell": 25, "2sell": 20, "3sell": 15,
        "qs_beichi": 20, "pz_beichi": 10,
    },
    "signal_strength": {"strong_threshold": 0.4, "medium_threshold": 0.15},
    "filters": {
        "volume_confirm": False,
        "volume_ratio": 1.2,
        "multi_tf": False,
    },
}


def load_params(params_path: str = None) -> dict:
    """从 params.json 加载参数，不存在则使用默认值"""
    if params_path is None:
        params_path = Path(__file__).parent / "params.json"
    try:
        with open(params_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        loaded = data.get("params", {})
        # 深度合并，确保缺失字段有默认值
        merged = _deep_merge(dict(DEFAULT_PARAMS), loaded)
        return merged
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_PARAMS)


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并两个字典"""
    result = dict(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


# === EVOLVE_ZONE: FILTERS_START ===
# 此区域供 evolve-mutator 修改，修改时只改动本区域内的代码
class FilterStrategy:
    """过滤策略基类"""
    def should_trade(self, signal: dict, context: dict) -> bool:
        return True


class VolumeConfirmFilter(FilterStrategy):
    """成交量确认过滤"""
    def __init__(self, min_ratio: float = 1.2):
        self.min_ratio = min_ratio

    def should_trade(self, signal: dict, context: dict) -> bool:
        if not context.get("volume_confirm", False):
            return True
        vol_ratio = context.get("current_volume", 0) / max(context.get("avg_volume", 1), 1)
        return vol_ratio >= self.min_ratio


class TrendStrengthFilter(FilterStrategy):
    """趋势强度过滤"""
    def __init__(self, min_score: float = 60.0):
        self.min_score = min_score

    def should_trade(self, signal: dict, context: dict) -> bool:
        return signal.get("mm_score", 0) >= self.min_score


DEFAULT_FILTERS = [
    VolumeConfirmFilter(min_ratio=1.2),
    TrendStrengthFilter(min_score=60.0),
]
# === EVOLVE_ZONE: FILTERS_END ===


class ChanLunEngine:
    """Wraps PyChanLun + 自建中枢算法，输出标准化缠论分析结果"""

    def __init__(self, df: pd.DataFrame, params: dict = None):
        required = {"open", "high", "low", "close", "volume"}
        if not required.issubset(df.columns):
            raise ValueError(f"DataFrame must have columns: {required}")
        self.df = df.sort_index().copy()
        self.p = params or load_params()
        fast, slow, signal = self._macd_params()
        self.FAST = fast
        self.SLOW = slow
        self.SIGNAL = signal
        self._add_macd()

    def _macd_params(self) -> tuple:
        m = self.p.get("macd", DEFAULT_PARAMS["macd"])
        return m.get("fast", 12), m.get("slow", 26), m.get("signal", 9)

    def _add_macd(self) -> None:
        fast, slow, signal = self._macd_params()
        close = self.df["close"].values
        ema_fast = self._ema(close, fast)
        ema_slow = self._ema(close, slow)
        dif = ema_fast - ema_slow
        dea = self._ema(dif, signal)
        macd_hist = 2 * (dif - dea)
        self.df["macd_dif"] = dif
        self.df["macd_dea"] = dea
        self.df["macd"] = macd_hist

    @staticmethod
    def _ema(data: np.ndarray, n: int) -> np.ndarray:
        ema = np.empty_like(data, dtype=float)
        ema[0] = data[0]
        k = 2.0 / (n + 1)
        for i in range(1, len(data)):
            ema[i] = data[i] * k + ema[i - 1] * (1 - k)
        return ema

    def analyze(self) -> dict:
        from pychanlun.chan import Chan

        chan = Chan("stock", {"1d": self.df})

        fractals = self._extract_fractals(chan)
        strokes, stroke_macd_map = self._extract_strokes(chan)
        zhongshus = self._extract_zhongshus(strokes)
        signals = self._extract_signals(chan)
        trend = self._determine_trend(strokes)
        summary = self._compute_summary(strokes, zhongshus, signals)

        current_price = self.df["close"].iloc[-1] if len(self.df) > 0 else 0
        last_stroke = strokes[-1] if strokes else None
        last_zs = zhongshus[-1] if zhongshus else None

        position = "中枢震荡"
        if last_zs:
            if current_price > last_zs["zg"]:
                position = "突破中枢"
            elif current_price < last_zs["zd"]:
                position = "跌破中枢"
        elif last_stroke:
            position = f"笔未完成({last_stroke['type']})"

        divergence = None
        if last_stroke and last_stroke["qs_beichi"]:
            divergence = f"趋势背驰({'底' if last_stroke['type'] == 'down' else '顶'})"
        elif last_stroke and last_stroke["pz_beichi"]:
            divergence = f"盘整背驰({'底' if last_stroke['type'] == 'down' else '顶'})"

        # 应用过滤器（EVOLVE_ZONE 策略）
        filtered_signals = self._apply_filters(signals, current_price)

        return {
            "status": "OK",
            "klines_count": len(self.df),
            "cl_klines_count": len(self.df),
            "fractals": fractals,
            "strokes": strokes,
            "zhongshus": zhongshus,
            "signals": filtered_signals,
            "raw_signals": signals,
            "current_trend": trend,
            "position": position,
            "divergence": divergence,
            "last_bi": {
                "type": last_stroke["type"] if last_stroke else None,
                "start_date": last_stroke["start_date"] if last_stroke else None,
                "end_date": last_stroke["end_date"] if last_stroke else None,
                "start_price": last_stroke["low"] if last_stroke and last_stroke["type"] == "up" else last_stroke.get("high") if last_stroke else None,
                "end_price": last_stroke["high"] if last_stroke and last_stroke["type"] == "up" else last_stroke.get("low") if last_stroke else None,
                "td": last_stroke.get("td", False) if last_stroke else False,
                "qs_beichi": last_stroke.get("qs_beichi", False) if last_stroke else False,
                "pz_beichi": last_stroke.get("pz_beichi", False) if last_stroke else False,
                "mmds": last_stroke.get("mmds", []) if last_stroke else [],
                "mm_score": last_stroke.get("mm_score", 0.0) if last_stroke else 0.0,
            } if last_stroke else None,
            "last_zs": {
                "zg": last_zs["zg"] if last_zs else None,
                "zd": last_zs["zd"] if last_zs else None,
                "gg": last_zs.get("gg") if last_zs else None,
                "dd": last_zs.get("dd") if last_zs else None,
            } if last_zs else None,
            "summary": summary,
            "params_version": self.p.get("_version", "default"),
        }

    def _apply_filters(self, signals: list, current_price: float) -> list:
        """应用 EVOLVE_ZONE 过滤器"""
        filters_cfg = self.p.get("filters", DEFAULT_PARAMS["filters"])
        if not filters_cfg.get("volume_confirm", False) and not filters_cfg.get("multi_tf", False):
            return signals

        context = {
            "volume_confirm": filters_cfg.get("volume_confirm", False),
            "multi_tf": filters_cfg.get("multi_tf", False),
            "current_volume": self.df["volume"].iloc[-1] if len(self.df) > 0 else 0,
            "avg_volume": self.df["volume"].mean() if len(self.df) > 0 else 0,
        }

        result = []
        for sig in signals:
            signal_dict = {"mm_score": sig.get("strength", 50), **sig}
            if all(f.should_trade(signal_dict, context) for f in DEFAULT_FILTERS):
                result.append(sig)
        return result

    # ──────────────────── 分型提取 ────────────────────
    def _extract_fractals(self, chan) -> list:
        f_df = chan.get_fractals("1d")
        if f_df is None or f_df.empty:
            return []
        result = []
        for dt, row in f_df.iterrows():
            if pd.notna(row.get("high")):
                result.append({"type": "ding", "date": str(dt.date()),
                               "val": round(float(row["high"]), 4), "real": True})
            if pd.notna(row.get("low")):
                result.append({"type": "di", "date": str(dt.date()),
                               "val": round(float(row["low"]), 4), "real": True})
        return result

    # ──────────────────── 笔提取(含背驰/评分) ────────────────────
    def _extract_strokes(self, chan) -> tuple:
        s_df = chan.get_strokes("1d")
        if s_df is None or s_df.empty:
            return [], {}

        sig_df = chan.get_stroke_pivot_signals("1d")
        pivot_df = chan.get_stroke_pivots("1d")
        sig_map = self._build_signal_map(sig_df)
        pivot_list = list(pivot_df.itertuples()) if pivot_df is not None and not pivot_df.empty else []

        prices = s_df["stroke"].tolist()
        dates = s_df.index.tolist()
        strokes = []
        stroke_macd_map = {}

        for i in range(len(prices) - 1):
            is_up = prices[i] < prices[i + 1]
            start_dt, end_dt = dates[i], dates[i + 1]

            # MACD for this stroke
            macd_sum = self._calc_stroke_macd(start_dt, end_dt)
            stroke_macd_map[i] = macd_sum

            # 信号
            mmds = self._get_mmds_for_stroke(sig_map, start_dt, end_dt)

            # 背驰
            qs_beichi, pz_beichi = self._detect_beichi(pivot_list, is_up, start_dt, end_dt, strokes, macd_sum, stroke_macd_map)

            # 评分
            mm_score = self._calc_mm_score(mmds, qs_beichi, pz_beichi)

            strokes.append({
                "index": i,
                "type": "up" if is_up else "down",
                "start_date": str(start_dt.date()),
                "end_date": str(end_dt.date()),
                "high": round(max(prices[i], prices[i + 1]), 4),
                "low": round(min(prices[i], prices[i + 1]), 4),
                "done": True,
                "td": False,
                "qs_beichi": qs_beichi,
                "pz_beichi": pz_beichi,
                "mmds": mmds,
                "mm_score": mm_score,
            })

        return strokes, stroke_macd_map

    def _calc_stroke_macd(self, start_dt, end_dt) -> float:
        """计算笔区间内MACD柱之和(面积)"""
        mask = (self.df.index >= start_dt) & (self.df.index <= end_dt)
        sub = self.df.loc[mask, "macd"]
        return float(sub.sum()) if len(sub) > 0 else 0.0

    def _build_signal_map(self, sig_df) -> dict:
        if sig_df is None or sig_df.empty:
            return {}
        sig_map = {}
        for dt, row in sig_df.iterrows():
            sig = int(row.get("signal", 0))
            label = {1: "1buy", 2: "2buy", 3: "3buy",
                    -1: "1sell", -2: "2sell", -3: "3sell"}.get(sig)
            if label:
                sig_map[str(dt.date())] = label
        return sig_map

    def _get_mmds_for_stroke(self, sig_map: dict, start_dt, end_dt) -> list:
        mmds = []
        cur = start_dt
        while cur <= end_dt:
            label = sig_map.get(str(cur.date()))
            if label and label not in mmds:
                mmds.append(label)
            cur += pd.Timedelta(days=1)
        return mmds

    def _detect_beichi(self, pivot_list, is_up: bool, start_dt, end_dt,
                       prior_strokes: list, macd_sum: float,
                       stroke_macd_map: dict = None) -> tuple:
        """趋势背驰(qs_beichi) + 盘整背驰(pz_beichi)"""
        qs_beichi, pz_beichi = False, False
        beichi_cfg = self.p.get("beichi", DEFAULT_PARAMS["beichi"])
        pz_ratio = beichi_cfg.get("pz_area_ratio", 0.6)

        if not pivot_list:
            return False, False

        # 找到与当前笔重叠的pivot
        relevant = [p for p in pivot_list if start_dt <= p.Index <= end_dt]
        if len(relevant) < 2:
            relevant = [p for p in pivot_list if p.Index <= end_dt]
        if len(relevant) < 2:
            return False, False

        latest, prev = relevant[-1], relevant[-2]
        if not hasattr(latest, 'level') or not hasattr(prev, 'level'):
            return False, False

        # 趋势背驰: level创新高但macd未跟随 OR level创新低但macd未跟随
        if is_up:
            if (latest.level > prev.level and
                hasattr(latest, 'macd') and hasattr(prev, 'macd') and
                latest.macd is not None and prev.macd is not None and
                latest.macd < prev.macd):
                qs_beichi = True
        else:
            if (latest.level < prev.level and
                hasattr(latest, 'macd') and hasattr(prev, 'macd') and
                latest.macd is not None and prev.macd is not None and
                latest.macd > prev.macd):
                qs_beichi = True

        # 盘整背驰: 同向笔MACD面积萎缩超过阈值
        smap = stroke_macd_map or {}
        if prior_strokes:
            prev_same = [s for s in reversed(prior_strokes) if s["type"] == ("up" if is_up else "down")]
            if prev_same:
                prev_macd = smap.get(prev_same[0]["index"], 0)
                if prev_macd != 0 and abs(macd_sum) < abs(prev_macd) * pz_ratio:
                    pz_beichi = True

        return qs_beichi, pz_beichi

    def _calc_mm_score(self, mmds: list, qs_beichi: bool, pz_beichi: bool) -> float:
        weights = self.p.get("mm_score_weights", DEFAULT_PARAMS["mm_score_weights"])
        score = 0.0
        for m in mmds:
            score += weights.get(m, 0)
        if qs_beichi:
            score += weights.get("qs_beichi", 20)
        if pz_beichi:
            score += weights.get("pz_beichi", 10)
        return max(0.0, min(100.0, score))

    # ──────────────────── 中枢提取(核心算法) ────────────────────
    def _extract_zhongshus(self, strokes: list) -> list:
        if len(strokes) < 5:
            return []

        zhongshus = []
        n = len(strokes)
        used = set()

        for i in range(n - 2):
            s1, s2, s3 = strokes[i], strokes[i + 1], strokes[i + 2]

            if s1["type"] == s2["type"] or s2["type"] == s3["type"]:
                continue

            h1, l1 = s1["high"], s1["low"]
            h2, l2 = s2["high"], s2["low"]
            h3, l3 = s3["high"], s3["low"]

            overlap_12_h = min(h1, h2)
            overlap_12_l = max(l1, l2)
            if overlap_12_h <= overlap_12_l:
                continue

            overlap_23_h = min(h2, h3)
            overlap_23_l = max(l2, l3)
            if overlap_23_h <= overlap_23_l:
                continue

            zg_candidate = min(overlap_12_h, overlap_23_h)
            zd_candidate = max(overlap_12_l, overlap_23_l)
            if zg_candidate <= zd_candidate:
                continue

            gg = max(h1, h2, h3)
            dd = min(l1, l2, l3)

            key = (round(zg_candidate, 2), round(zd_candidate, 2))
            if key in used:
                continue
            used.add(key)

            zhongshus.append({
                "index": len(zhongshus),
                "zg": round(zg_candidate, 4),
                "zd": round(zd_candidate, 4),
                "gg": round(gg, 4),
                "dd": round(dd, 4),
                "stroke_indices": [i, i + 1, i + 2],
            })

        return zhongshus

    # ──────────────────── 信号提取 ────────────────────
    def _extract_signals(self, chan) -> list:
        sig_df = chan.get_stroke_pivot_signals("1d")
        if sig_df is None or sig_df.empty:
            return []
        result = []
        for dt, row in sig_df.iterrows():
            sig = int(row.get("signal", 0))
            if sig == 0:
                continue
            price = row.get("stroke", row.get("high", row.get("low")))
            label = {1: "1buy", 2: "2buy", 3: "3buy",
                    -1: "1sell", -2: "2sell", -3: "3sell"}.get(sig, f"sig{sig}")
            result.append({
                "date": str(dt.date()),
                "type": label,
                "price": round(float(price), 2) if price else None,
            })
        return result

    # ──────────────────── 趋势判断 ────────────────────
    def _determine_trend(self, strokes: list) -> str:
        if len(strokes) < 3:
            return "盘整"
        last = strokes[-1]["type"]
        prev = strokes[-2]["type"]
        if last == "up" and prev == "down":
            return "上涨"
        elif last == "down" and prev == "up":
            return "下跌"
        return "盘整"

    # ──────────────────── 摘要计算 ────────────────────
    def _compute_summary(self, strokes: list, zhongshus: list, signals: list) -> dict:
        buy_count = sum(1 for s in strokes if any(m in s.get("mmds", []) for m in ["1buy", "2buy", "3buy", "l2buy"]))
        sell_count = sum(1 for s in strokes if any(m in s.get("mmds", []) for m in ["1sell", "2sell", "3sell"]))
        div_count = sum(1 for s in strokes if s.get("qs_beichi") or s.get("pz_beichi"))
        active = buy_count + sell_count + div_count
        total = len(strokes)

        strength_cfg = self.p.get("signal_strength", DEFAULT_PARAMS["signal_strength"])
        strong_th = strength_cfg.get("strong_threshold", 0.4)
        medium_th = strength_cfg.get("medium_threshold", 0.15)

        if total == 0:
            strength = "weak"
        elif active / total > strong_th:
            strength = "strong"
        elif active / total > medium_th:
            strength = "medium"
        else:
            strength = "weak"

        return {
            "divergence_count": div_count,
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "signal_strength": strength,
            "signals_list": signals,
        }


# ──────────────────── 批量分析函数 ────────────────────

def build_df_from_lists(dates_str, opens, highs, lows, closes, vols):
    """将列表数据构建为标准DataFrame"""
    dates_rev = list(reversed(dates_str))
    return pd.DataFrame({
        "open":   list(reversed(opens)),
        "high":   list(reversed(highs)),
        "low":    list(reversed(lows)),
        "close":  list(reversed(closes)),
        "volume": list(reversed(vols)),
    }, index=pd.to_datetime(dates_rev))


def analyze_stock(code: str, dates_str, opens, highs, lows, closes, vols, n=360) -> dict:
    """对单只股票进行缠论分析"""
    try:
        df = build_df_from_lists(dates_str[:n], opens[:n], highs[:n], lows[:n], closes[:n], vols[:n])
        df.index.name = "date"
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        engine = ChanLunEngine(df)
        result = engine.analyze()
        result["symbol"] = code
        result["date_range"] = f"{dates_str[-1]}~{dates_str[0]}"
        return result
    except Exception as e:
        return {"symbol": code, "error": str(e)}
