---
name: perception_and_regime
version: 2.2.0
author: OpenClaw SEL Framework v2.2
description: >
  一次性完成所有市场数据拉取 + 实时市场体制分类（trend_up / sideways / volatile / black_swan）。
  当用户提到行情分析、市场状态、趋势判断、体制分类时触发。
  支持 A股（akshare）、港股/美股（yfinance）、加密货币（Binance）。
category: perception
tags: [regime, data-fetch, classifier, market-regime]
inputs:
  - name: symbols
    type: list[str]
    required: true
    description: 股票代码列表，如 ["000001", "AAPL"]
  - name: market
    type: str
    required: false
    default: "A"
    description: 市场类型 A/HK/US
  - name: period
    type: str
    required: false
    default: "day"
    description: K线周期 day/week/60m/30m/...
outputs:
  - name: market_snapshot
    type: dict
    description: 所有symbol的原始行情数据
  - name: regime_label
    type: str
    description: trend_up | sideways | volatile | black_swan
  - name: regime_confidence
    type: float
    description: 0.0~1.0，分类置信度
  - name: features
    type: dict
    description: 技术指标特征（ADX/ATR/MACDhist/VolRatio）
triggers:
  - before_decision
  - market_analysis
self_evolve: true
dependencies: []
llm_router: none
retry_policy:
  max_retries: 3
  backoff_seconds: 2
observability: true
---

# Perception & Regime Classification

## 输入

- `symbols: list[str]` — 股票代码列表
- `market: str` — A/HK/US（默认 A）
- `period: str` — K线周期（默认 day）

## Regime 分类算法（纯本地）

基于 4 个技术指标的特征向量，用阈值规则分类：

| Regime | 条件 |
|--------|------|
| `trend_up` | ADX > 25 AND MACDhist > 0 AND price > SMA20 |
| `trend_down` | ADX > 25 AND MACDhist < 0 AND price < SMA20 |
| `sideways` | ADX ≤ 25 AND ATR_pct < 3% |
| `volatile` | ATR_pct > 5% OR ADX > 40 |
| `black_swan` | 单日最大回撤 > 8% OR volatility > 3σ |

置信度 = 各指标命中的加权平均 / 4

## 输出结构

```python
{
    "market_snapshot": {symbol: {"dates": [...], "close": [...], "volume": [...]}},
    "regime_label": "trend_up",
    "regime_confidence": 0.82,
    "features": {
        "adx": 32.1,
        "atr_pct": 1.8,
        "macd_hist": 0.42,
        "vol_ratio": 1.1,
        "sma20_slope": 0.003
    },
    "timestamp": "2026-05-19T10:30:00"
}
```

## 数据源优先级

1. **A股**: akshare `stock_zh_a_hist`
2. **港股/美股**: yfinance
3. **加密**: Binance `/api/v3/klines`
4. **全部失败**: 返回 `regime_label = "unknown"`, confidence = 0.0

## 告警条件

- `black_swan` → 通知 observability_hub 暂停进化 48h
- `volatile` AND `confidence > 0.8` → 通知降仓
