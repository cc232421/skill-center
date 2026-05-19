---
name: review_scheduler
version: 2.2.0
author: OpenClaw SEL Framework v2.2
description: >
  自适应调度器，按策略风险等级自动安排复盘频率。
  高频策略（daytrade）每小时复盘，趋势策略每日复盘，长线策略每周复盘。
  当用户问及复盘、绩效回顾、持仓总结时触发。
category: review
tags: [scheduler, cron, review, adaptive]
inputs:
  - name: strategy_name
    type: str
    required: false
    default: "default"
    description: 策略名称
  - name: frequency
    type: str
    required: false
    default: "auto"
    description: auto|hourly|daily|weekly
outputs:
  - name: next_review_at
    type: str
    description: ISO8601 时间
  - name: pending_reviews
    type: int
    description: 待复盘快照数
  - name: triggered
    type: bool
    description: 本次是否触发复盘
triggers:
  - scheduled_review
  - manual_review
self_evolve: true
dependencies: [decision_snapshot]
llm_router: none
retry_policy:
  max_retries: 1
  backoff_seconds: 5
observability: true
---

# Review Scheduler

## 频率规则

| 策略频率 | 复盘周期 | 触发条件 |
|---------|---------|---------|
| `daytrade` | 每小时 | `pending_reviews >= 5` |
| `intraday` | 每4小时 | `pending_reviews >= 3` |
| `swing` | 每日 | 收盘后 |
| `position` | 每周 | 周末 |
| `longterm` | 每月 | 月末 |

## 自适应调整

- 连续 3 次复盘无新教训 → 频率降一级
- 连续 3 次复盘有新教训 → 频率升一级
- `black_swan` regime → 立即全量复盘

## 输出结构

```python
{
    "next_review_at": "2026-05-19T16:00:00+08:00",
    "pending_reviews": 7,
    "triggered": True,          # 本次是否已触发
    "frequency": "hourly",
    "schedule_id": "uuid"
}
```

## 触发后的动作

调用 `self_review_and_extract` skill 处理所有 `review_status=pending` 的快照。
