---
name: sandbox_simulation
version: 2.2.0
author: OpenClaw SEL Framework v2.2
description: >
  沙盒回测引擎：验证新规则在历史数据上的表现。
  Sharpe ≥ 1.2 且 最大回撤 ≤ 12% 才允许激活。
  当 skill_evolution_meta 生成新规则时触发。
category: sandbox
tags: [backtest, sandbox, simulation, sharpe]
inputs:
  - name: rule
    type: dict
    required: true
    description: 待验证的规则
  - name: symbols
    type: list[str]
    required: false
    default: ["000001"]
    description: 回测标的
  - name: lookback_days
    type: int
    required: false
    default: 60
    description: 回看天数（30/60/90）
outputs:
  - name: backtest_result
    type: dict
    description: 回测结果
  - name: approved
    type: bool
    description: 是否通过验证门
  - name: sharpe_ratio
    type: float
  - name: max_drawdown_pct
    type: float
triggers:
  - rule_validation
  - sandbox_check
self_evolve: true
dependencies: [skill_evolution_meta]
llm_router: none
retry_policy:
  max_retries: 1
  backoff_seconds: 10
observability: true
validation_gate:
  min_sharpe: 1.2
  max_drawdown_pct: 12.0
---

# Sandbox Simulation

## 验证门

| 指标 | 门槛 | 说明 |
|------|------|------|
| `sharpe_ratio` | ≥ 1.2 | 夏普比率 |
| `max_drawdown_pct` | ≤ 12% | 最大回撤 |
| `win_rate` | ≥ 45% | 胜率 |
| `min_trades` | ≥ 10 | 最小交易次数 |

**全部满足** → `approved = True` → 注册激活规则
**任一不满足** → `approved = False` → 记录 rejected + 触发新教训

## 回测引擎

```python
class SandboxEngine:
    def run(self, rule: dict, df: pd.DataFrame) -> BacktestResult:
        # 1. 生成信号序列
        signals = rule.apply(df)
        # 2. 计算PnL
        trades = self._execute_trades(signals, df)
        # 3. 计算指标
        sharpe = self._sharpe(trades)
        mdd = self._max_drawdown(trades)
        wr = self._winrate(trades)
        return BacktestResult(sharpe, mdd, wr, trades)
```

## 输出结构

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

## 安全机制

- **模拟账户**：不涉及真实资金
- **历史数据**：只用已结束的K线（无前瞻偏差）
- **规则隔离**：每个规则独立回测，互不干扰
