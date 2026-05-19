# OpenClaw SEL Framework v2.2 完全使用教程

> **自进化、自学习交易框架** — 纯本地算法，无外部 LLM 依赖，8 个核心 Skill 构成 7×24 无人值守闭环
>
> 版本：2.2 | 2026-05-19

---

## 目录

1. [框架概述](#1-框架概述)
2. [安装与快速开始](#2-安装与快速开始)
3. [核心概念速查](#3-核心概念速查)
4. [Skill 1：感知与体制分类](#4-skill-1感知与体制分类)
5. [Skill 2：决策快照](#5-skill-2决策快照)
6. [Skill 3：定时复盘调度器](#6-skill-3定时复盘调度器)
7. [Skill 4：自主复盘与教训提取](#7-skill-4自主复盘与教训提取)
8. [Skill 5：分层 RAG 经验检索](#8-skill-5分层-rag-经验检索)
9. [Skill 6：Skill/规则进化](#9-skill-6skill规则进化)
10. [Skill 7：沙盒回测验证](#10-skill-7沙盒回测验证)
11. [Skill 8：观测与告警中心](#11-skill-8观测与告警中心)
12. [端到端闭环流程](#12-端到端闭环流程)
13. [数据存储结构](#13-数据存储结构)
14. [环境变量配置](#14-环境变量配置)
15. [常见问题](#15-常见问题)

---

## 1. 框架概述

### 1.1 什么是 SEL Framework？

SEL Framework（Self-Evolving Learning Framework）是一个**完全本地运行的交易自进化系统**。它不需要任何外部 LLM API，全部逻辑基于规则引擎，通过"感知→决策→留痕→复盘→进化→验证"的闭环，实现无人值守的自我优化。

### 1.2 8 个核心 Skill

| # | Skill | 作用 | 关键词 |
|---|-------|------|--------|
| 1 | `perception_and_regime` | 拉取实时行情 + 分类市场体制 | 趋势/震荡/波动/黑天鹅 |
| 2 | `decision_snapshot` | 100% 记录每笔交易决策 | 决策留痕、快照 |
| 3 | `review_scheduler` | 按策略频率自动触发复盘 | 日内/日内/波段/持仓 |
| 4 | `self_review_and_extract` | 分析 P&L，提取教训 | 盈亏分析、教训提取 |
| 5 | `hierarchical_rag_retriever` | 从经验库检索最相关历史决策 | RAG、经验检索 |
| 6 | `skill_evolution_meta` | 检测教训模式，生成新规则 | 规则进化、自优化 |
| 7 | `sandbox_simulation` | 沙盒回测验证新规则 | 回测、Sharpe 验证 |
| 8 | `observability_hub` | 统一日志 + 告警 + Grafana 导出 | 监控、告警 |

### 1.3 架构图

```
┌─────────────────────────────────────────────────────────┐
│                   7×24 无人值守闭环                      │
│                                                          │
│  感知 ──▶ 体制分类 ──▶ RAG检索 ──▶ 决策+留痕             │
│     │                                              │     │
│     │              ◀── 定时回访 ◀── 自主复盘 ◀──        │     │
│     │                                              │     │
│     └──────▶ Skill/规则进化 ──▶ 沙盒验证 ──▶ 自动注册   │
└─────────────────────────────────────────────────────────┘
```

### 1.4 依赖执行顺序

```
[perception_and_regime]          ← 起点：行情数据 + 体制分类
        │
        ▼
[decision_snapshot]              ← 决策时：100% 留痕
        │
        ├──► [hierarchical_rag_retriever]  ← 检索历史经验
        │
        ▼
[review_scheduler]               ← 定时触发复盘
        │
        ▼
[self_review_and_extract]        ← 分析 P&L，提炼教训
        │
        ▼
[skill_evolution_meta]           ← 规则驱动进化
        │
        ▼
[sandbox_simulation]             ← 沙盒验证
        │
        ▼
[observability_hub]              ← 统一观测 + 告警
```

---

## 2. 安装与快速开始

### 2.1 前置要求

```bash
# Python ≥ 3.10
python --version  # 要求 3.10+

# 安装依赖
pip install numpy pandas akshare yfinance pytest
```

### 2.2 项目目录结构

```
sel_framework/
├── SEL.md                          ← 框架架构文档
├── sel_framework.json              ← 元注册表
├── SKILL.md                        ← 顶层 Skill 清单
├── conftest.py                     ← pytest 配置
├── perception_and_regime/          ← Skill 1
│   ├── __init__.py
│   ├── SKILL.md
│   └── test_perception.py
├── decision_snapshot/              ← Skill 2
│   ├── __init__.py
│   ├── SKILL.md
│   └── test_snapshot.py
├── review_scheduler/               ← Skill 3
├── self_review_and_extract/        ← Skill 4
├── hierarchical_rag_retriever/     ← Skill 5
├── skill_evolution_meta/           ← Skill 6
├── sandbox_simulation/            ← Skill 7
└── observability_hub/             ← Skill 8
```

### 2.3 快速验证（运行全部测试）

```bash
cd skills/sel-framework
python -m pytest --tb=short -q

# 期望输出：
# 75 passed in 0.19s
```

---

## 3. 核心概念速查

### 3.1 市场体制（Regime）

| Regime | 含义 | 触发条件 |
|--------|------|---------|
| `trend_up` | 趋势上涨 | ADX > 25 且 MACDhist > 0 且价格 > SMA20 |
| `trend_down` | 趋势下跌 | ADX > 25 且 MACDhist < 0 且价格 < SMA20 |
| `sideways` | 区间震荡 | ADX ≤ 25 且 ATR% < 3% |
| `volatile` | 高波动 | ATR% > 5% 或 ADX > 40 |
| `black_swan` | 黑天鹅 | 单日回撤 > 8% 或波动率 > 3σ |

### 3.2 经验权重公式

```
score = time_decay(days) × winrate(strategy) × regime_match(regime)

time_decay   = 0.5 ^ (days_since / 30)       # 30 天后衰减 50%
winrate      = wins / total (同策略)          # 策略历史胜率
regime_match = 1.5  同体制
               0.8  相邻体制（如 trend_up↔volatile）
               0.3  对立体制
```

### 3.3 进化触发条件

| 条件 | 阈值 | 动作 |
|------|------|------|
| 同 Regime 连续亏损 | ≥ 3 次 | 生成新规则 |
| 经验命中率 | < 80% | 调整检索权重 |
| Sharpe（沙盒）| < 1.0 | 丢弃 / 重生成规则 |
| 最大回撤 | > 15% | 暂停进化 48 小时 |

### 3.4 验证门（沙盒）

| 指标 | 门槛 |
|------|------|
| Sharpe 比率 | ≥ 1.2 |
| 最大回撤 | ≤ 12% |
| 胜率 | ≥ 45% |
| 最小交易次数 | ≥ 10 |

---

## 4. Skill 1：感知与体制分类

**模块**：`perception_and_regime`
**作用**：一次性完成行情数据拉取 + 实时市场体制分类

### 4.1 快速开始

```python
from perception_and_regime import run

# 分析 A 股
result = run(symbols=["000001", "000002"], market="A", period="day")
print(result["regime_label"])    # "trend_up"
print(result["regime_confidence"])  # 0.82

# 分析港股
result = run(symbols=["0700"], market="HK", period="day")

# 分析美股
result = run(symbols=["AAPL", "TSLA"], market="US", period="day")

# 分析加密货币
result = run(symbols=["BTCUSDT"], market="crypto", period="1h")
```

### 4.2 返回值详解

```python
result = run(symbols=["000001"], market="A")

# result 包含：
{
    "market_snapshot": {
        "000001": {
            "dates": ["2026-05-15", "2026-05-16", ...],
            "close": [12.50, 12.80, ...],
            "volume": [1234567, ...],
            "high": [...],
            "low": [...]
        }
    },
    "regime_label": "trend_up",           # 当前体制
    "regime_confidence": 0.82,             # 置信度 0~1
    "features": {
        "adx": 32.1,          # 方向性指数
        "atr_pct": 1.8,       # ATR 占价格百分比
        "macd_hist": 0.42,     # MACD 柱状图
        "vol_ratio": 1.1,      # 成交量比
        "sma20_slope": 0.003   # 20 日均线斜率
    },
    "timestamp": "2026-05-19T10:30:00"
}
```

### 4.3 体制分类算法（纯本地）

框架使用 4 个技术指标的特征向量进行阈值规则分类：

```python
# 判断逻辑（来自 __init__.py）
if adx > 40 or atr_pct > 5:
    return "volatile"
elif adx <= 25 and atr_pct < 3:
    return "sideways"
elif adx > 25 and macd_hist > 0 and price > sma20:
    return "trend_up"
elif adx > 25 and macd_hist < 0 and price < sma20:
    return "trend_down"
elif max_drawdown > 8 or volatility > 3 * std:
    return "black_swan"
```

### 4.4 技术指标说明

| 指标 | 计算方式 | 用途 |
|------|---------|------|
| ADX | DMI 方向性指数 | 趋势强度 |
| ATR% | (ATR / close) × 100 | 波动率占价格比例 |
| MACDhist | MACD - Signal | 动量方向 |
| VolRatio | 当前成交量 / 20 日均量 | 成交量异常 |
| SMA20 | 20 日简单均线 | 趋势方向 |

所有指标均使用**纯 NumPy/Pandas** 计算，**无需 TALIB**。

### 4.5 数据源优先级

```
A股（akshare）→ 港股/美股（yfinance）→ 加密（Binance）→ 失败返回 "unknown"
```

---

## 5. Skill 2：决策快照

**模块**：`decision_snapshot`
**作用**：100% 自动记录每笔决策为结构化快照，持久化到经验库

### 5.1 保存决策

```python
from decision_snapshot import save_snapshot, update_snapshot

# Step 1: 做决策时保存快照
snapshot = save_snapshot(
    symbol="000001",
    action="buy",              # buy | sell | hold | stoploss | add | reduce
    price=12.50,
    quantity=1000,
    regime="trend_up",
    regime_confidence=0.82,
    strategy="chanlun_breakout",
    reason="缠论1买+底分型确认",
)
print(snapshot["snapshot_id"])  # "a1b2c3d4-..."

# Step 2: 持仓结束后更新结果
update_snapshot(snapshot["snapshot_id"], {
    "pnl": 8.5,      # 盈利 8.5%
    "result": "win", # win | loss | hold
})
```

### 5.2 快照完整结构

```python
{
    "id": "a1b2c3d4-...",
    "symbol": "000001",
    "market": "A",
    "action": "buy",
    "price": 12.50,
    "quantity": 1000,
    "regime": "trend_up",
    "regime_confidence": 0.82,
    "strategy": "chanlun_breakout",
    "reason": "缠论1买+底分型确认",
    "features": {"adx": 32.1, "atr_pct": 1.8, ...},
    "risk_ratio": 1.5,
    "timestamp": "2026-05-19T10:30:00",
    "pnl": 8.5,           # 持仓结束后填入
    "result": "win",       # win | loss | hold
    "review_status": "pending"  # pending → reviewed → evolved
}
```

### 5.3 查询相关操作

```python
from decision_snapshot import (
    load_snapshot,                    # 加载单条快照
    list_pending_snapshots,           # 列出所有待复盘快照
    count_pending,                   # 统计待复盘数量
)

# 加载单条
snap = load_snapshot("a1b2c3d4-...")

# 列出所有待复盘
pending = list_pending_snapshots()
print(f"待复盘: {len(pending)} 条")

# 统计
n = count_pending()
print(f"待复盘: {n} 条")
```

### 5.4 存储位置

```
~/.sel_data/snapshots/YYYY-MM/snapshot-{uuid}.json
例如：
~/.sel_data/snapshots/2026-05/snapshot-a1b2c3d4.json
```

### 5.5 典型使用流程

```python
# 完整决策 → 快照流程
from perception_and_regime import run as perceive
from decision_snapshot import save_snapshot, update_snapshot

# 1. 感知市场
market = perceive(symbols=["000001"], market="A")

# 2. 做决策
if market["regime_label"] == "trend_up" and market["regime_confidence"] > 0.7:
    snapshot = save_snapshot(
        symbol="000001",
        action="buy",
        price=12.50,
        regime=market["regime_label"],
        regime_confidence=market["regime_confidence"],
        strategy="chanlun_breakout",
        reason=f"体制={market['regime_label']}，信心={market['regime_confidence']}",
    )
    print(f"已记录决策: {snapshot['snapshot_id']}")

# 3. 平仓后更新
update_snapshot(snapshot["snapshot_id"], {
    "pnl": 6.2,
    "result": "win"
})
```

---

## 6. Skill 3：定时复盘调度器

**模块**：`review_scheduler`
**作用**：自适应调度器，按策略风险等级自动安排复盘频率

### 6.1 频率对照表

| 策略频率 | 复盘周期 | 触发条件 |
|---------|---------|---------|
| `daytrade` | 每小时 | 待复盘 ≥ 5 条 |
| `intraday` | 每 4 小时 | 待复盘 ≥ 3 条 |
| `swing` | 每日 | 收盘后 |
| `position` | 每周 | 周末 |
| `longterm` | 每月 | 月末 |

### 6.2 调度器 API

```python
from review_scheduler import run

# 查询调度状态
status = run(strategy_name="chanlun_breakout", frequency="auto")
print(status["next_review_at"])   # "2026-05-19T16:00:00+08:00"
print(status["pending_reviews"])   # 7
print(status["triggered"])        # True（本次已触发）

# 指定频率
status = run(strategy_name="my_strategy", frequency="daily")
```

### 6.3 自适应调整逻辑

```python
# 连续 3 次复盘无新教训 → 频率降一级（减少浪费）
# 连续 3 次复盘有新教训 → 频率升一级（更及时）
# black_swan regime → 立即全量复盘
```

### 6.4 与其他 Skill 的联动

```
review_scheduler.triggered = True
    ↓
self_review_and_extract.run()  ← 处理所有 pending 快照
    ↓
skill_evolution_meta.run()      ← 检测到教训则触发进化
```

---

## 7. Skill 4：自主复盘与教训提取

**模块**：`self_review_and_extract`
**作用**：规则引擎遍历待复盘快照 → 计算 P&L → 提取教训 + 标签 + 摘要

### 7.1 执行复盘

```python
from self_review_and_extract import run

# 复盘所有待处理快照
result = run()

# 只复盘指定快照
result = run(snapshot_ids=["uuid-1", "uuid-2"])

# 强制重新复盘已处理过的
result = run(force_recalculate=True)
```

### 7.2 返回值详解

```python
{
    "lessons": [
        {
            "id": "uuid",
            "lesson_type": "trend_riding_success",
            "summary": "在趋势上涨体制中，顺势持仓平均盈利8.2%",
            "tags": ["trend_up", "hold", "momentum"],
            "regime": "trend_up",
            "winrate_after": 0.62,
            "sample_size": 12,
            "confidence": 0.75,
            "extracted_at": "2026-05-19T10:30:00"
        },
        {
            "id": "uuid",
            "lesson_type": "range_trap_loss",
            "summary": "震荡市逆势亏损，趋势策略不适用于区间市场",
            "tags": ["sideways", "loss", "trap"],
            "regime": "sideways",
            ...
        },
        ...
    ],
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

### 7.3 教训提取规则（按优先级）

| 条件 | 教训标签 | 说明 |
|------|---------|------|
| `pnl > 5%` 且 `regime == trend_up` | `trend_riding_success` | 趋势持有盈利 |
| `pnl < -3%` 且 `regime == sideways` | `range_trap_loss` | 震荡市逆势亏损 |
| `pnl < -8%` | `black_swan_hit` | 触发黑天鹅止损 |
| `pnl < -3%` 且 `regime == volatile` | `volatile_loss` | 高波动亏损 |
| `hold_days > 10` 且 `abs(pnl) < 1%` | `stalled_position` | 持仓无方向 |
| 同策略连续 3 次亏损 | `strategy_rotting` | 策略失效警告 |
| `abs(pnl) > 1%` 且 `abs(pnl) <= 3%` | `mixed_result` | 盈亏各半 |

> **注意**：`black_swan_hit`（pnl < -8%）排在 `volatile_loss`（pnl < -3%）**之前**，避免 -10% 的快照被错误标记为 `volatile_loss`。

### 7.4 与进化模块的联动

```python
# 自动触发进化条件：
# - new_lessons >= 2
# - 出现 strategy_rotting

result = run()
if result["summary"]["new_lessons"] >= 2:
    from skill_evolution_meta import run as evolve
    evolve(result["lessons"])
```

---

## 8. Skill 5：分层 RAG 经验检索

**模块**：`hierarchical_rag_retriever`
**作用**：根据当前体制 + 策略上下文，从经验库中检索最相关的历史决策

### 8.1 检索 API

```python
from hierarchical_rag_retriever import retrieve

# 根据当前体制检索
result = retrieve(
    current_regime="trend_up",
    strategy="chanlun_breakout",
    top_k=5,
    min_score=0.1,
)

print(f"经验库共 {result['total_experiences']} 条")
print(f"本次命中 {len(result['retrieved_experiences'])} 条")
```

### 8.2 返回值详解

```python
{
    "retrieved_experiences": [
        {
            "snapshot_id": "uuid",
            "score": 0.82,           # 综合权重分
            "regime_match_boost": 1.5,  # 体制匹配加成
            "time_decay_factor": 0.71,  # 时间衰减因子
            "winrate": 0.65,        # 策略历史胜率
            "strategy": "chanlun_breakout",
            "action": "buy",
            "regime": "trend_up",
            "result": "win",
            "pnl_pct": 6.8,
            "days_ago": 5
        },
        ...
    ],
    "total_experiences": 142,
    "cache_hit": False
}
```

### 8.3 权重公式详解

```
score = time_decay(days_since) × winrate(strategy) × regime_match(regime)

各因子计算：
time_decay  = 0.5^(days/30)      # 30 天衰减 50%，60 天衰减 75%
winrate     = wins / total       # 同一策略的胜率
regime_match = 1.5（体制相同）
               0.8（相邻体制，如 trend_up ↔ volatile）
               0.3（对立体制，如 trend_up ↔ sideways）
```

### 8.4 分层检索流程

```
L1 粗筛：按当前体制过滤候选集
    ↓
L2 打分：计算 score = time_decay × winrate × regime_match
    ↓
L3 精排：按 score 降序，取 top_k
    ↓
L4 去重：同策略同体制保留最新一条
```

### 8.5 缓存策略

- 当前体制未变 + 1 小时内 → 直接返回缓存（零计算）
- 体制变化 → 重新计算

### 8.6 决策前检索示例

```python
from perception_and_regime import run as perceive
from decision_snapshot import save_snapshot
from hierarchical_rag_retriever import retrieve

# 1. 感知市场体制
market = perceive(symbols=["000001"], market="A")

# 2. 检索相关历史经验
experiences = retrieve(
    current_regime=market["regime_label"],
    strategy="chanlun_breakout",
    top_k=3,
)

# 3. 决策参考
for exp in experiences["retrieved_experiences"]:
    print(f"  {exp['action']} {exp['result']} pnl={exp['pnl_pct']}%")

# 4. 做出决策并记录
if experiences["retrieved_experiences"]:
    top = experiences["retrieved_experiences"][0]
    action = "buy" if top["result"] == "win" else "hold"
else:
    action = "hold"  # 无相关经验，保守操作

save_snapshot(symbol="000001", action=action, ...)
```

---

## 9. Skill 6：Skill/规则进化

**模块**：`skill_evolution_meta`
**作用**：规则驱动进化 — 检测教训模式 → 生成新策略规则 → 注册到规则库

### 9.1 执行进化

```python
from skill_evolution_meta import run

lessons = [
    {"lesson_type": "strategy_rotting", "strategy": "my_strat"},
    {"lesson_type": "range_trap_loss", "regime": "sideways"},
]

result = run(lessons)
print(result["evolution_status"])   # "evolved"
print(f"新规则 {len(result['new_rules'])} 条")
print(f"激活 {len(result['activated_rules'])} 条")
print(f"拒绝 {len(result['rejected_rules'])} 条")
```

### 9.2 返回值详解

```python
{
    "new_rules": [
        {
            "rule_id": "uuid",
            "name": "sideways_hold_filter",
            "pattern": {"regime": "sideways", "atr_pct": "<", "threshold": 2.0},
            "action": "hold",
            "priority": 1,
            "created_from": "lessons",
            "mode": "patch",           # patch | clone | restructure
            "strategy": "my_strat",
            "status": "active",        # sandbox_verifying | active | rejected
            "created_at": "2026-05-19T10:30:00"
        },
        ...
    ],
    "activated_rules": [...],   # 通过沙盒验证的规则
    "rejected_rules": [...],    # 被沙盒拒绝的规则
    "evolution_status": "evolved",
    "evolution_mode": "patch",
    "reason": "strategy_rotting_detected"
}
```

### 9.3 三种进化模式

#### 模式 A：规则补丁（轻量）

检测到特定失误模式，在现有策略中追加过滤规则：

```python
# 输入：多个 sideways + 亏损 的教训
# 输出：生成补丁规则
{
    "name": "sideways_avoid_patch",
    "pattern": {"regime": "sideways"},
    "action": "hold",           # 震荡市不追涨杀跌
    "mode": "patch"
}
```

#### 模式 B：策略克隆（中等）

检测到某子策略胜率 ≥ 60%，克隆为独立策略：

```python
# 输入：chanlun_1buy 在 trend_up 有 5+ 个胜局，胜率 72%
# 输出：生成克隆规则
{
    "name": "chanlun_1buy_trend_up_clone",
    "pattern": {"strategy": "chanlun_1buy", "regime": "trend_up"},
    "action": "increase_exposure",
    "mode": "clone",
    "winrate": 0.72,
    "sample_size": 8
}
```

#### 模式 C：规则重组（重量）

教训数量 ≥ 5 且互斥模式存在时，完全重组规则优先级：

```python
# 统计所有 lesson 的 regime + action 分布
# 构建决策矩阵：regime → action 优先级
# 输出：多 条 restructure 规则
```

### 9.4 进化触发条件

| 触发条件 | 说明 |
|---------|------|
| 同策略连续 3 次亏损 | 策略失效警告 |
| `strategy_rotting` 教训出现 | 立即触发 |
| 教训数量 ≥ 5 | 触发完整重组 |
| 教训数量 2~4 个 | 触发克隆 |
| 教训数量 1 个 | 触发补丁 |

### 9.5 规则存储位置

```
~/.sel_data/rules/rule-{uuid}.json
```

---

## 10. Skill 7：沙盒回测验证

**模块**：`sandbox_simulation`
**作用**：验证新规则在历史数据上的表现，Sharpe ≥ 1.2 且最大回撤 ≤ 12% 才允许激活

### 10.1 沙盒验证 API

```python
from sandbox_simulation import run, apply_rule_to_df, compute_metrics

# 验证单条规则
result = run(
    rule={
        "rule_id": "uuid",
        "name": "sideways_hold_filter",
        "pattern": {"regime": "sideways"},
        "action": "hold",
    },
    symbols=["000001", "000002"],
    lookback_days=60,
)

print(f"Sharpe: {result['sharpe_ratio']}")      # 1.45
print(f"最大回撤: {result['max_drawdown_pct']}%") # 8.2%
print(f"胜率: {result['win_rate']}")             # 0.61
print(f"通过验证: {result['approved']}")        # True
```

### 10.2 验证门详解

```
通过条件（必须同时满足）：
  Sharpe ≥ 1.2  → 风险调整后收益达标
  最大回撤 ≤ 12% → 风险可控
  胜率 ≥ 45%   → 概率正期望
  交易次数 ≥ 10 → 样本足够

全部通过 → approved = True → 注册激活规则
任一失败 → approved = False → 记录 rejected + 触发新教训
```

### 10.3 回测结果详解

```python
{
    "backtest_result": {
        "rule_id": "uuid",
        "lookback_days": 60,
        "symbols": ["000001", "AAPL"],
        "start_date": "2026-03-20",
        "end_date": "2026-05-19",
        "sharpe_ratio": 1.45,
        "max_drawdown_pct": 8.2,
        "win_rate": 0.61,
        "total_trades": 23,
        "avg_hold_days": 4.2,
        "approved": True
    },
    "approved": True,
    "rejection_reason": None
}
```

### 10.4 手动调用回测引擎

```python
from sandbox_simulation import apply_rule_to_df, compute_metrics
import pandas as pd

# 获取历史数据（从 perception_and_regime）
df = pd.DataFrame({
    "date": ["2026-05-01", "2026-05-02", ...],
    "open": [...], "high": [...], "low": [...],
    "close": [...], "volume": [...]
})

rule = {
    "pattern": {"regime": "trend_up"},
    "action": "buy",
}

signals = apply_rule_to_df(rule, df)
metrics = compute_metrics(signals, df)
print(metrics["sharpe_ratio"])
```

---

## 11. Skill 8：观测与告警中心

**模块**：`observability_hub`
**作用**：所有 Skill 的日志汇聚点，同时支持 Webhook 告警和 Grafana 导出

### 11.1 记录日志

```python
from observability_hub import log, metrics, grafana_metrics_text

# 记录技能执行
log(
    event_type="skill_run",
    skill="perception_and_regime",
    payload={"regime": "trend_up", "confidence": 0.82},
    severity="info",
    message="市场体制分析完成",
)

# 记录决策
log(
    event_type="decision",
    skill="decision_snapshot",
    payload={"snapshot_id": "uuid", "action": "buy"},
    severity="info",
)

# 记录进化结果
log(
    event_type="evolution",
    skill="skill_evolution_meta",
    payload={"rule_id": "uuid", "approved": True},
    severity="info" if True else "warning",
)
```

### 11.2 告警规则

| 条件 | 级别 | 说明 |
|------|------|------|
| `regime == black_swan` | `critical` | 暂停进化 48 小时 |
| `evolution rejected` | `warning` | 通知并记录教训 |
| `winrate < 0.4` | `error` | 触发全面复盘 |
| `sandbox approved` | `info` | 正常记录 |

### 11.3 指标查询

```python
from observability_hub import metrics, grafana_metrics_text

# 获取当前指标
m = metrics()
print(m)
# {
#     "winrate": 0.62,
#     "experience_count": 142,
#     "active_rules": 8,
#     "timestamp": "2026-05-19T10:30:00"
# }

# 获取 Prometheus 格式（Grafana 用）
text = grafana_metrics_text()
print(text)
# # HELP sel_framework_winrate Overall win rate
# # TYPE sel_framework_winrate gauge
# sel_framework_winrate 0.62
#
# # HELP sel_framework_experience_count Total experiences in RAG
# # TYPE sel_framework_experience_count gauge
# sel_framework_experience_count 142
#
# # HELP sel_framework_active_rules Number of active rules
# # TYPE sel_framework_active_rules gauge
# sel_framework_active_rules 8
```

### 11.4 最近日志

```python
from observability_hub import get_recent_logs

logs = get_recent_logs(n=50)  # 最近 50 条
for entry in logs:
    print(f"{entry['timestamp']} [{entry['severity']}] {entry['message']}")
```

### 11.5 Webhook 告警配置

```bash
# 设置环境变量（支持任何 POST JSON 的 Webhook）
export SEL_ALERT_WEBHOOK_URL="https://hooks.example.com/alert"

# 支持：
# - Slack Incoming Webhook
# - 企业微信 Webhook
# - 钉钉 Webhook
# - 自建告警服务
```

---

## 12. 端到端闭环流程

### 12.1 每日决策闭环

```python
"""
完整的每日决策 → 复盘 → 进化流程
"""
from perception_and_regime import run as perceive
from hierarchical_rag_retriever import retrieve
from decision_snapshot import save_snapshot, update_snapshot
from self_review_and_extract import run as review
from skill_evolution_meta import run as evolve
from observability_hub import log

# ===== 阶段 1：感知 + 检索 =====
log("skill_run", {"skill": "daily_loop"}, severity="info")

market = perceive(symbols=["000001"], market="A")
log("skill_run", {"skill": "perception", "regime": market["regime_label"]})

experiences = retrieve(
    current_regime=market["regime_label"],
    strategy="chanlun_breakout",
    top_k=3,
)

# ===== 阶段 2：决策 + 留痕 =====
# 根据体制 + 历史经验做出决策
action = "buy"  # 简化示例

snapshot = save_snapshot(
    symbol="000001",
    action=action,
    price=12.50,
    regime=market["regime_label"],
    regime_confidence=market["regime_confidence"],
    strategy="chanlun_breakout",
    reason=f"体制={market['regime_label']}，参考{len(experiences['retrieved_experiences'])}条历史经验",
)
log("decision", {"snapshot_id": snapshot["snapshot_id"], "action": action})

# ===== 阶段 3：持仓结束 → 更新快照 =====
# （实际由定时任务或手动触发）
update_snapshot(snapshot["snapshot_id"], {
    "pnl": 6.5,
    "result": "win"
})

# ===== 阶段 4：定时复盘 =====
from review_scheduler import run as schedule

schedule_status = schedule(strategy_name="chanlun_breakout")
if schedule_status["triggered"]:
    result = review()
    log("review", {
        "lessons_count": result["summary"]["lessons_count"],
        "winrate": result["summary"]["winrate"],
    })

    # ===== 阶段 5：触发进化 =====
    if result["summary"]["new_lessons"] >= 2:
        evo_result = evolve(result["lessons"])
        log("evolution", {
            "status": evo_result["evolution_status"],
            "mode": evo_result.get("evolution_mode"),
            "new_rules": len(evo_result["new_rules"]),
            "activated": len(evo_result["activated_rules"]),
        })

print("每日闭环完成")
```

### 12.2 定时任务配置（Linux cron）

```bash
# 写入 crontab
crontab -e

# 每小时运行一次日内策略复盘
0 * * * * cd /path/to/sel-framework && python -c "
from review_scheduler import run; r=run(frequency='hourly')
if r['triggered']:
    from self_review_and_extract import run as review
    result = review()
    if result['summary']['new_lessons'] >= 2:
        from skill_evolution_meta import run as evolve
        evolve(result['lessons'])
" >> /var/log/sel_daily.log 2>&1

# 每日收盘后运行波段策略复盘
0 16 * * 1-5 cd /path/to/sel-framework && python -c "
from review_scheduler import run; run(strategy_name='swing', frequency='daily')
" >> /var/log/sel_swing.log 2>&1
```

### 12.3 状态流转图

```
pending ──▶ reviewed ──▶ evolved
              ↓
          提取教训
              ↓
         教训库 + 进化触发
              ↓
         新规则生成
              ↓
         沙盒验证
              ↓
      通过 ──▶ 激活
      失败 ──▶ rejected（触发新教训）
```

---

## 13. 数据存储结构

### 13.1 目录结构

```
~/.sel_data/
├── snapshots/              ← 决策快照
│   └── 2026-05/
│       ├── snapshot-a1b2c3d4.json
│       └── snapshot-e5f6g7h8.json
├── rules/                  ← 激活的规则
│   └── rule-12345678.json
├── lessons/               ← 教训历史
│   └── lesson-12345678.json
├── logs/                   ← 结构化日志
│   └── 2026-05.jsonl
├── rag_cache.json          ← RAG 缓存
└── schedules.json          ← 调度状态
```

### 13.2 快照文件示例

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "symbol": "000001",
  "action": "buy",
  "price": 12.50,
  "quantity": 1000,
  "regime": "trend_up",
  "regime_confidence": 0.82,
  "strategy": "chanlun_breakout",
  "reason": "缠论1买+底分型确认，体制trend_up信心0.82",
  "features": {
    "adx": 32.1,
    "atr_pct": 1.8,
    "macd_hist": 0.42,
    "vol_ratio": 1.1
  },
  "risk_ratio": 1.5,
  "timestamp": "2026-05-19T10:30:00+08:00",
  "pnl": 8.5,
  "result": "win",
  "review_status": "evolved"
}
```

### 13.3 日志文件示例

```jsonl
{"timestamp":"2026-05-19T10:30:00+08:00","event_type":"skill_run","severity":"info","skill":"perception_and_regime","message":"市场体制分析完成","payload":{"regime":"trend_up","confidence":0.82},"metrics":{"winrate":0.62,"experience_count":142,"active_rules":8}}
{"timestamp":"2026-05-19T10:30:05+08:00","event_type":"decision","severity":"info","skill":"decision_snapshot","message":"决策已记录","payload":{"snapshot_id":"a1b2c3d4-..."},"metrics":{...}}
```

---

## 14. 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SEL_DATA_DIR` | `~/.sel_data` | 经验库 / 日志存储路径 |
| `SEL_EVOLUTION_ENABLED` | `true` | 全局进化开关 |
| `SEL_HUMAN_REVIEW_THRESHOLD` | `0.0` | 信心低于此值暂停（0=禁用） |
| `SEL_ALERT_WEBHOOK_URL` | `""` | 告警 Webhook URL |
| `SEL_LOG_LEVEL` | `INFO` | DEBUG / INFO / WARNING |

```bash
# 生产环境配置示例
export SEL_DATA_DIR="/data/sel_data"
export SEL_EVOLUTION_ENABLED="true"
export SEL_ALERT_WEBHOOK_URL="https://hooks.slack.com/services/xxx/yyy/zzz"
export SEL_LOG_LEVEL="INFO"
```

---

## 15. 常见问题

### Q1：如何查看当前经验库状态？

```python
from observability_hub import metrics
m = metrics()
print(f"经验数: {m['experience_count']}")
print(f"胜率: {m['winrate']}")
print(f"活跃规则: {m['active_rules']}")
```

### Q2：如何查看规则列表？

```python
import json
from pathlib import Path

rules_dir = Path.home() / ".sel_data" / "rules"
for path in rules_dir.glob("rule-*.json"):
    with open(path) as f:
        rule = json.load(f)
    print(f"{rule['name']} | {rule['status']} | mode={rule['mode']}")
```

### Q3：如何手动触发复盘？

```python
from self_review_and_extract import run
result = run()  # 处理所有 pending
print(f"复盘 {result['summary']['snapshots_reviewed']} 条，产生 {result['summary']['lessons_count']} 条教训")
```

### Q4：进化被暂停了怎么办？

```python
# 检查黑天鹅状态
# black_swan 发生后自动暂停 48 小时
# 检查日志中是否有 black_swan 事件

from observability_hub import get_recent_logs
logs = get_recent_logs(n=100)
for log in logs:
    if log["event_type"] == "regime" and log["payload"].get("regime") == "black_swan":
        print(f"黑天鹅发生于: {log['timestamp']}")
        print("48 小时内不会触发进化")
```

### Q5：如何清空经验库重新开始？

```python
import shutil
from pathlib import Path

sel_data = Path.home() / ".sel_data"
# 警告：此操作不可逆
# shutil.rmtree(sel_data)
# sel_data.mkdir(parents=True)
print("经验库已清空")
```

### Q6：回测失败的原因有哪些？

```python
# 常见原因：
# 1. 样本不足（< 10 笔交易）
# 2. Sharpe < 1.2（策略本身不够好）
# 3. 最大回撤 > 12%（风险超标）
# 4. 胜率 < 45%（概率负期望）

# 排查方法：
result = run(rule={...}, lookback_days=90)  # 增加回看天数
print(result.get("rejection_reason"))
```

### Q7：RAG 检索结果为空怎么办？

```python
# 原因：经验库中没有匹配当前体制的数据
# 解决：先积累更多决策快照

experiences = retrieve(current_regime="volatile", top_k=5)
if not experiences["retrieved_experiences"]:
    print(f"经验库共 {experiences['total_experiences']} 条，但无 volatile 体制记录")
    print("继续交易，系统会自动积累经验")
```

### Q8：如何调试单个 Skill？

```python
# 直接调用 Skill 的 run 函数，查看返回值
from perception_and_regime import run
result = run(symbols=["000001"], market="A")
print(json.dumps(result, indent=2))

from hierarchical_rag_retriever import retrieve
result = retrieve("trend_up", top_k=3)
print(json.dumps(result, indent=2))
```

---

## 附录：测试快速参考

```bash
# 运行全部测试
cd skills/sel-framework
python -m pytest --tb=short -q

# 运行单个 Skill 的测试
python -m pytest perception_and_regime/test_perception.py -v

# 查看覆盖率
python -m pytest --cov=. --cov-report=term

# 期望：75 passed, 0 failures
```

---

*本文档对应 OpenClaw SEL Framework v2.2*
*框架源码：`skill-center/skills/sel-framework/`*
*更新日期：2026-05-19*