# SEL Framework v2.2 — OpenClaw 自进化交易 Skill

**纯本地算法 | 无外部 LLM | 零人工干预 | 沙盒验证**

---

## 快速开始

```python
from sel_framework import SELFramework

sel = SELFramework()
sel.run_cycle(symbols=["000001", "AAPL"])
```

## 8 个核心 Skill

| # | Skill | 职责 | 触发时机 |
|---|-------|------|---------|
| 1 | `perception_and_regime` | 拉取行情 + 体制分类 | 每次决策前 |
| 2 | `decision_snapshot` | 决策结构化留痕 | 每次决策后 |
| 3 | `review_scheduler` | 定时触发复盘 | 每日/每周cron |
| 4 | `self_review_and_extract` | P&L分析 → 提取教训 | 复盘时 |
| 5 | `hierarchical_rag_retriever` | 权重检索历史经验 | 决策时 |
| 6 | `skill_evolution_meta` | 规则驱动自进化 | 连续亏损时 |
| 7 | `sandbox_simulation` | 沙盒回测验证 | 新规则激活前 |
| 8 | `observability_hub` | 统一日志+告警 | 全程 |

详见 [SEL.md](./SEL.md)
