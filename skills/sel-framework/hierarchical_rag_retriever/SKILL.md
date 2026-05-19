---
name: hierarchical_rag_retriever
version: 2.2.0
author: OpenClaw SEL Framework v2.2
description: >
  本地分层RAG检索引擎：根据当前体制 + 策略上下文，从经验库中检索最相关的历史决策。
  权重公式 = time_decay × winrate × regime_match。
  当需要做新决策、检索历史经验时触发。
category: decision
tags: [rag, retrieval, experience, memory]
inputs:
  - name: current_regime
    type: str
    required: true
    description: 当前体制 label
  - name: strategy
    type: str
    required: false
    default: "default"
    description: 当前策略名称
  - name: top_k
    type: int
    required: false
    default: 5
    description: 返回topK条经验
  - name: min_score
    type: float
    required: false
    default: 0.1
    description: 最低权重分数门槛
outputs:
  - name: retrieved_experiences
    type: list[dict]
    description: 按权重排序的经验列表
  - name: total_experiences
    type: int
    description: 库中总经验数
  - name: cache_hit
    type: bool
triggers:
  - before_decision
  - experience_query
self_evolve: true
dependencies: [decision_snapshot]
llm_router: none
retry_policy:
  max_retries: 1
  backoff_seconds: 1
observability: true
---

# Hierarchical RAG Retriever

## 权重公式

```
score = time_decay(days_since) × winrate(strategy) × regime_match(regime)

time_decay   = 0.5 ^ (days_since / 30)         # 30天后衰减50%
winrate      = wins / total (for same strategy) # 策略历史胜率
regime_match = 1.5  if same regime
               0.8  if adjacent regime (e.g. trend_up↔volatile)
               0.3  if opposite regime
```

## 检索层次（由粗到精）

1. **L1 粗筛**：按 regime 过滤 → 候选集
2. **L2 打分**：计算加权 score
3. **L3 精排**：按 score 排序，取 top_k
4. **L4 去重**：同策略同体制保留最新一条

## 缓存策略

- regime 未变化 + 1小时内 → 直接返回缓存
- regime 变化 → 重新计算 top_k

## 输出结构

```python
{
    "retrieved_experiences": [
        {
            "snapshot_id": "uuid",
            "score": 0.82,
            "regime_match_boost": 1.5,
            "time_decay_factor": 0.71,
            "winrate": 0.65,
            "strategy": "chanlun_breakout",
            "action": "buy",
            "regime": "trend_up",
            "result": "win",
            "pnl_pct": 6.8,
            "days_ago": 5
        },
        // ... more items
    ],
    "total_experiences": 142,
    "cache_hit": False
}
```

## 命中率统计

每次决策后记录：
- `hit` = 经验被成功参考
- `miss` = 经验库无相关记录
- `wrong` = 参考经验反而导致亏损

命中率 = hit / (hit + miss + wrong)
