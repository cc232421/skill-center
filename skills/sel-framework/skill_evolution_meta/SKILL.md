---
name: skill_evolution_meta
version: 2.2.0
author: OpenClaw SEL Framework v2.2
description: >
  规则驱动的元进化 Skill：检测教训中的模式 → 生成新策略规则 → 注册到规则库。
  完全本地规则引擎，无需外部LLM。
  当 self_review_and_extract 报告连续亏损教训时触发。
category: evolution
tags: [meta, code-generation, self-evolve, rules-engine]
inputs:
  - name: lessons
    type: list[dict]
    required: true
    description: 来自 self_review_and_extract 的教训列表
outputs:
  - name: new_rules
    type: list[dict]
    description: 生成的新规则
  - name: activated_rules
    type: list[dict]
    description: 已激活的规则（沙盒验证通过）
  - name: rejected_rules
    type: list[dict]
    description: 被沙盒拒绝的规则
  - name: evolution_status
    type: str
    description: evolved | no_signal | paused
triggers:
  - after_self_review
  - strategy_rotting_detected
self_evolve: true
dependencies: [self_review_and_extract]
llm_router: none
retry_policy:
  max_retries: 1
  backoff_seconds: 5
observability: true
evolution_gate:
  min_sharpe: 1.2
  max_drawdown_pct: 12.0
---

# Skill Evolution Meta

## 进化触发条件（任一满足即触发）

| 信号 | 阈值 |
|------|------|
| 同策略连续亏损 | ≥3 次 |
| 策略失效率 | >50% (winrate < 0.5) |
| 教训库新增 `strategy_rotting` | ≥1 次 |
| 经验命中率 | <80% 持续 7 天 |

## 进化模式

### 模式 A：规则补丁（轻量）
检测到特定失误模式 → 在现有策略中追加过滤规则：

```
IF regime == "sideways" AND ATR_pct < 2%
THEN action = "hold"   # 震荡市不追涨杀跌
```

### 模式 B：策略克隆（中等）
检测到某子策略胜率高 → 克隆为独立策略：

```
# 检测到 chanlun_1buy 在 trend_up 胜率 72%
# 克隆为独立规则: chanlun_1buy_trend_up_filter
```

### 模式 C：规则重组（重量）
教训数量 ≥5 且互斥模式 → 完全重组规则优先级：

1. 统计所有 lesson 的 regime + action 分布
2. 构建决策矩阵：regime → action 优先级
3. 替换旧策略的核心规则

## 规则结构

```python
{
    "rule_id": "uuid",
    "name": "sideways_hold_filter",
    "pattern": {"regime": "sideways", "atr_pct": "<", "threshold": 2.0},
    "action": "hold",
    "priority": 1,
    "created_from": "lessons",
    "created_at": "2026-05-19T10:30:00",
    "status": "sandbox_verifying | active | rejected"
}
```

## 流程

```
接收 lessons
    ↓
模式检测（轻/中/重）
    ↓
生成候选规则
    ↓
调用 sandbox_simulation 验证
    ↓
通过 → 注册激活
失败 → 记录 rejected + 通知 observability_hub
```
