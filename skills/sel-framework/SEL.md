# OpenClaw SEL Framework v2.2 — System Overview

**自进化、自学习交易 Skill 完整框架**
版本：2.2 | 2026-05-19 | 纯本地算法，无外部 LLM 依赖

---

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                   7×24 无人值守闭环                       │
│                                                         │
│  感知 ──▶ 体制分类 ──▶ RAG检索 ──▶ 决策+留痕              │
│     │                                              │    │
│     │              ◀── 定时回访 ◀── 自主复盘 ◀──        │    │
│     │                                              │    │
│     └──────▶ Skill/规则进化 ──▶ 沙盒验证 ──▶ 自动注册   │
└─────────────────────────────────────────────────────────┘
```

## Skill 依赖拓扑（数字=执行顺序）

```
[perception_and_regime]          ← 起点：数据+体制
        │
        ▼
[decision_snapshot]              ← 决策时：100%留痕
        │
        ├──► [hierarchical_rag_retriever]  ← 检索历史经验
        │
        ▼
[review_scheduler]               ← 定时触发复盘
        │
        ▼
[self_review_and_extract]        ← 分析P&L，提教训
        │
        ▼
[skill_evolution_meta]           ← 规则驱动进化
        │
        ▼
[sandbox_simulation]             ← 沙盒验证
        │
        ▼
[observability_hub]              ← 统一观测+告警
```

## 核心创新

- **纯本地算法**：无外部 LLM API，全部逻辑基于规则引擎
- **零人工干预**：自进化闭环全自动运行
- **沙盒先行**：任何新规则先过回测验证门
- **可观测闭环**：每步操作写入结构化日志 + 可选告警

## 经验库权重公式

```
score = time_decay(days) × winrate × regime_match
time_decay = 0.5 ^ (days_since / 30)
regime_match = 1.5 if same_regime else 0.8
```

## 进化触发条件

| 条件 | 阈值 | 动作 |
|------|------|------|
| 同 Regime 连续亏损 | ≥3 次 | 生成新规则 |
| 经验命中率 | <80% | 调整检索权重 |
| Sharpe（沙盒）| <1.0 | 丢弃/重生成 |
| 最大回撤 | >15% | 暂停进化48h |

## 文件结构

```
sel_framework/
├── SEL.md                       ← 本文档
├── sel_framework.json           ← 元注册
├── perception_and_regime/        ← Skill 1: 感知+体制
├── decision_snapshot/           ← Skill 2: 决策留痕
├── review_scheduler/            ← Skill 3: 定时复盘
├── self_review_and_extract/      ← Skill 4: 自主复盘
├── hierarchical_rag_retriever/   ← Skill 5: 经验检索
├── skill_evolution_meta/         ← Skill 6: 元进化
├── sandbox_simulation/           ← Skill 7: 沙盒验证
└── observability_hub/            ← Skill 8: 观测告警
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| SEL_DATA_DIR | ~/.sel_data | 经验库/日志存储路径 |
| SEL_EVOLUTION_ENABLED | true | 全局进化开关 |
| SEL_HUMAN_REVIEW_THRESHOLD | 0.0 | 信心低于此值暂停（0=禁用） |
| SEL_ALERT_WEBHOOK_URL | "" | 告警 Webhook URL |
| SEL_LOG_LEVEL | INFO | DEBUG/INFO/WARNING |
