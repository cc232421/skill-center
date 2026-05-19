---
name: decision_snapshot
version: 2.2.0
author: OpenClaw SEL Framework v2.2
description: >
  100% 自动记录每笔决策为结构化快照，持久化到经验库。
  当用户做出交易决策、持仓调整、风控操作时触发。
  支持买入/卖出/持有/止损/追涨/杀跌等所有决策类型。
category: decision
tags: [snapshot, logging, experience, decision-log]
inputs:
  - name: decision_data
    type: dict
    required: true
    description: 决策数据（见下方字段定义）
outputs:
  - name: snapshot_id
    type: str
    description: UUID快照ID
  - name: persisted_path
    type: str
    description: 存储路径
triggers:
  - after_decision
  - trade_execution
self_evolve: true
dependencies: [perception_and_regime]
llm_router: none
retry_policy:
  max_retries: 3
  backoff_seconds: 1
observability: true
---

# Decision Snapshot

## 输入字段（decision_data）

```python
{
    "symbol": "000001",
    "market": "A",
    "action": "buy",        # buy|sell|hold|stoploss|add|reduce
    "price": 12.50,
    "quantity": 1000,
    "regime": "trend_up",   # from perception_and_regime
    "regime_confidence": 0.82,
    "strategy": "chanlun_breakout",  # 策略来源
    "reason": "缠论1买+底分型确认",
    "entry_snapshot": {...},  # 当时的行情快照
    "risk_ratio": 1.5,      # 风险收益比
    "timestamp": "2026-05-19T10:30:00"
}
```

## 输出

```python
{
    "snapshot_id": "uuid-v4",
    "persisted_path": "~/.sel_data/snapshots/2026-05/uuid.json",
    "status": "saved"
}
```

## 存储格式

每个快照存为 JSON 文件：
`$SEL_DATA_DIR/snapshots/YYYY-MM/snapshot-{uuid}.json`

## 快照内容（完整）

```python
{
    "id": "uuid-v4",
    "symbol": "000001",
    "market": "A",
    "action": "buy",
    "price": 12.50,
    "quantity": 1000,
    "regime": "trend_up",
    "regime_confidence": 0.82,
    "strategy": "chanlun_breakout",
    "reason": "缠论1买+底分型确认",
    "features": {...},       # perception features
    "risk_ratio": 1.5,
    "timestamp": "...",
    "pnl": None,             # 持仓结束后填入
    "result": None,          # win/loss/hold
    "review_status": "pending"  # pending/reviewed/evolved
}
```

## 规则

- **必须 100% 留痕**：任何决策类型都必须记录
- **不允许覆盖**：snapshot_id 全局唯一，失败则重试
- **异步写入**：不影响决策延迟
