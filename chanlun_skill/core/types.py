"""
Core type definitions for Chanlun analysis.
All entities use consistent field naming across modules.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ============================================================================
# Constants
# ============================================================================

FX_DING = "ding"
FX_DI = "di"
BI_UP = "up"
BI_DOWN = "down"
ZS_ZD = "zd"
ZS_UP = "up"
ZS_BUY = "buy"
ZS_SELL = "sell"
BSP_BUY = "buy"
BSP_SELL = "sell"
BSP_NEUTRAL = "neutral"
SEG_DOWN = "down"
SEG_UP = "up"
SEGMENT_VALID = "valid"

# ============================================================================
# KLine Entities
# ============================================================================


@dataclass(frozen=True)
class KLineRaw:
    """Raw K-line from data source (immutable)."""
    index: int
    date: str
    h: float  # high
    l: float  # low
    o: float  # open
    c: float  # close
    v: float = 0.0  # volume


@dataclass
class CombineKLine:
    """
    Combined/merged K-line after containment logic.
    Contains original klines that were merged into this one.
    """
    index: int
    k_index: int  # last raw kline index
    date: str
    h: float
    l: float
    o: float
    c: float
    v: float = 0.0
    klines: List[KLineRaw] = field(default_factory=list)
    n: int = 1  # count of merged raw klines
    has_gap: bool = False


# Alias for backward compatibility
CLKn = CombineKLine


# ============================================================================
# Structure Entities
# ============================================================================


@dataclass
class Fractal:
    """
    Fractal (分型).
    Top (ding) or bottom (di) pivot point.
    """
    type: str  # FX_DING or FX_DI
    k: CombineKLine
    val: float  # the price value (h for ding, l for di)
    real: bool = True  # is real/invalid
    done: bool = True  # is confirmed
    index: int = 0
    has_gap: bool = False


@dataclass
class Bi:
    """
    Stroke/笔 - from fractal to fractal.
    """
    start: Fractal
    end: Optional[Fractal] = None
    type: Optional[str] = None  # BI_UP or BI_DOWN
    high: Optional[float] = None
    low: Optional[float] = None
    done: bool = True
    td: bool = False  # tao die (逃顶底)
    index: int = 0
    fx_invalid_count: int = 0
    ld: Dict = field(default_factory=dict)  # ling du (力度) - MACD metrics
    qs_beichi: bool = False  # 趋势背驰
    pz_beichi: bool = False  # 盘整背驰
    mmds: List[str] = field(default_factory=list)  # 买卖点 signals


# Alias for backward compatibility
Stroke = Bi


@dataclass
class Seg:
    """
    Segment (线段) - from bi to bi.
    """
    start: 'Bi'
    end: Optional['Bi'] = None
    type: Optional[str] = None
    high: Optional[float] = None
    low: Optional[float] = None
    done: bool = True
    index: int = 0
    bi_count: int = 0
    level: int = 0
    status: str = "pending"


@dataclass
class ZS:
    """
    Zhongshu (中枢) - overlapping seg/zones.
    """
    zg: float  # zhonggao (中枢高)
    zd: float  # zhongdi (中枢低)
    gg: float  # gaoogao (高高)
    dd: float  # didi (低低)
    segs: List[Seg] = field(default_factory=list)
    type: str = ZS_ZD
    index: int = 0
    is_high_level: bool = False
    level: int = 0


# Alias for backward compatibility
ZhongShu = ZS


@dataclass
class BSP:
    """
    Buy/Sell Point (买卖点).
    """
    bi: Bi
    point_type: str
    price: float
    date: str
    seg: Optional[Seg] = None
    confirmed: bool = True


@dataclass
class AnalysisResultV2:
    """
    Full analysis result in schema v2 format.
    """
    schema_version: str = "2.0"
    meta: Dict = field(default_factory=dict)
    stats: Dict = field(default_factory=dict)
    kline: Dict = field(default_factory=dict)
    structures: Dict = field(default_factory=dict)
    signals: List = field(default_factory=list)
    state: Dict = field(default_factory=dict)


# ============================================================================
# Utility Functions
# ============================================================================

def interval_overlap(a_h: float, a_l: float, b_h: float, b_l: float) -> Optional[List[float]]:
    """Check if two price intervals overlap. Returns [hi, lo] or None."""
    lo = max(a_l, b_l)
    hi = min(a_h, b_h)
    return [hi, lo] if lo <= hi else None


def parse_date(d: str) -> str:
    """Strip timezone from date string."""
    return str(d).replace("+08:00", "").strip()
