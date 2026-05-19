---
name: observability_hub
version: 2.2.0
author: OpenClaw SEL Framework v2.2
description: >
  统一观测中心：所有 Skill 的日志汇聚点，同时支持 Webhook 告警。
  当 regime=black_swan、evolution 被拒绝、胜率突变时发送告警。
  Grafana 友好的 JSON 指标导出。
category: monitoring
tags: [observability, logging, alert, metrics, grafana]
inputs:
  - name: event_type
    type: str
    required: true
    description: skill_run|decision|review|evolution|alert
  - name: payload
    type: dict
    required: true
    description: 事件数据
  - name: severity
    type: str
    required: false
    default: "info"
    description: debug|info|warning|error|critical
outputs:
  - name: logged
    type: bool
    description: 是否成功写入
  - name: alerted
    type: bool
    description: 是否发送了告警
triggers:
  - always
self_evolve: true
dependencies: []
llm_router: none
retry_policy:
  max_retries: 2
  backoff_seconds: 2
observability: true
---

# Observability Hub

## 事件类型

| event_type | 触发时机 |
|-----------|---------|
| `skill_run` | 每个 skill 启动/完成 |
| `decision` | decision_snapshot 写入 |
| `review` | self_review_and_extract 完成 |
| `evolution` | skill_evolution_meta 完成 |
| `sandbox` | sandbox_simulation 完成 |
| `alert` | 任意告警事件 |

## 告警规则

| 条件 | severity | 动作 |
|------|---------|------|
| `regime == black_swan` | `critical` | 暂停进化48h |
| `evolution rejected` | `warning` | 通知 + 记录教训 |
| `winrate < 0.4` 连续5天 | `error` | 触发全面复盘 |
| `skill_run failed` | `warning` | 记录 + 重试 |
| `sandbox approved` | `info` | 正常记录 |

## 日志格式（结构化 JSON）

```python
{
    "timestamp": "2026-05-19T10:30:00+08:00",
    "event_type": "evolution",
    "severity": "info",
    "skill": "skill_evolution_meta",
    "message": "Rule approved: sideways_hold_filter",
    "payload": {
        "rule_id": "uuid",
        "sharpe": 1.45,
        "mdd": 8.2,
        "approved": True
    },
    "metrics": {
        "winrate": 0.62,
        "experience_count": 142,
        "rules_active": 8
    }
}
```

## Grafana 导出

GET `/metrics` → 返回 Prometheus-compatible 格式：

```
# HELP sel_framework_winrate Overall win rate
# TYPE sel_framework_winrate gauge
sel_framework_winrate{strategy="chanlun"} 0.62

# HELP sel_framework_experience_count Total experiences in RAG
# TYPE sel_framework_experience_count gauge
sel_framework_experience_count 142

# HELP sel_framework_active_rules Number of active rules
# TYPE sel_framework_active_rules gauge
sel_framework_active_rules 8
```

## Webhook 告警（可选）

设置 `SEL_ALERT_WEBHOOK_URL` 环境变量，告警时 POST JSON 到该 URL。
