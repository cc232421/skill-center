---
name: self_review_and_extract
version: 2.2.0
author: OpenClaw SEL Framework v2.2
description: >
  规则引擎自主复盘：遍历待复盘快照 → 计算P&L → 提取教训 + 标签 + 摘要。
  完全基于规则，无需外部LLM。
  当 review_scheduler 触发、或用户请求复盘时运行。
category: review
tags: [self-review, pnl, lessons, extraction]
inputs:
  - name: snapshot_ids
    type: list[str]
    required: false
    description: 快照ID列表，为空则处理所有pending
  - name: force_recalculate
    type: bool
    required: false
    default: false
    description: 强制重新计算已review过的快照
outputs:
  - name: lessons
    type: list[dict]
    description: 提取的教训列表
  - name: summary
    type: dict
    description: 复盘汇总统计
  - name: lessons_count
    type: int
triggers:
  - after_review_scheduler
  - manual_review
self_evolve: true
dependencies: [decision_snapshot, review_scheduler]
llm_router: none
retry_policy:
  max_retries: 2
  backoff_seconds: 3
observability: true
---

# Self Review & Extract

## 规则引擎逻辑

### Step 1: P&L 计算

```python
if snapshot.result in ("win", "loss"):
    pnl_pct = (exit_price - entry_price) / entry_price * 100
    snapshot.pnl = pnl_pct
    snapshot.review_status = "reviewed"
```

### Step 2: 教训提取规则

| 条件 | 教训标签 | 摘要 |
|------|---------|------|
| `pnl > 5%` AND `regime == "trend_up"` | `trend_riding_success` | 顺势持有盈利 |
| `pnl < -3%` AND `regime == "sideways"` | `range_trap_loss` | 震荡市逆势亏损 |
| `winrate > 60%` for same regime | `regime_edge` | 该体制有效 |
| `max_loss > 8%` | `black_swan_hit` | 触发黑天鹅止损 |
| `hold_days > 10` AND `abs(pnl) < 1%` | `stalled_position` | 持仓无方向 |
| 同策略连续3次亏损 | `strategy_rotting` | 策略失效警告 |

### Step 3: 教训结构

```python
{
    "id": "uuid",
    "lesson_type": "trend_riding_success",
    "summary": "在趋势上涨体制中，顺势持仓平均盈利8.2%",
    "tags": ["trend_up", "hold", "momentum"],
    "regime": "trend_up",
    "winrate_after": 0.62,     # 教训应用后的胜率
    "sample_size": 12,
    "confidence": 0.75,
    "extracted_at": "2026-05-19T10:30:00"
}
```

## 输出汇总

```python
{
    "lessons": [/* list of lesson dicts */],
    "summary": {
        "snapshots_reviewed": 15,
        "wins": 8,
        "losses": 4,
        "holds": 3,
        "winrate": 0.667,
        "avg_win_pct": 5.2,
        "avg_loss_pct": -2.8,
        "new_lessons": 3,
        "lessons_count": 3
    }
}
```

## 进化触发条件

当 `new_lessons >= 2` 时，调用 `skill_evolution_meta`。
当 `strategy_rotting` 出现时，立即调用 `skill_evolution_meta`。
