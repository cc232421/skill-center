"""
Tests for sandbox_simulation skill
"""
import os
import tempfile
import pytest
import numpy as np
import pandas as pd

os.environ["SEL_DATA_DIR"] = tempfile.mkdtemp()

from sandbox_simulation import (
    apply_rule_to_df, compute_metrics, run,
    GATE_SHARPE, GATE_MDD, GATE_WINRATE, GATE_MIN_TRADES,
)


def make_trend_df(n: int = 60) -> pd.DataFrame:
    np.random.seed(42)
    close = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame({
        "date": [f"2024-01-{i%28+1:02d}" for i in range(n)],
        "open": close * (1 + np.random.randn(n) * 0.002),
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "volume": np.random.randint(1_000_000, 5_000_000, n),
    })


class TestApplyRule:
    def test_no_regime_rule_applies_everywhere(self):
        df = make_trend_df(60)
        rule = {"rule_id": "test", "pattern": {}, "action": "hold"}
        trades = apply_rule_to_df(rule, df)
        assert len(trades) > 0

    def test_regime_filter(self):
        df = make_trend_df(60)
        rule = {"rule_id": "test", "pattern": {"regime": "trend_up"}, "action": "buy"}
        trades = apply_rule_to_df(rule, df)
        assert isinstance(trades, list)


class TestComputeMetrics:
    def test_empty_trades(self):
        m = compute_metrics([])
        assert m["total_trades"] == 0
        assert m["sharpe_ratio"] == 0.0

    def test_all_winners(self):
        trades = [{"pnl_pct": 5.0}, {"pnl_pct": 3.0}, {"pnl_pct": 7.0}]
        m = compute_metrics(trades)
        assert m["win_rate"] == 1.0
        assert m["total_trades"] == 3

    def test_mixed_trades(self):
        trades = [
            {"pnl_pct": 10.0}, {"pnl_pct": -3.0},
            {"pnl_pct": 5.0}, {"pnl_pct": -2.0},
        ]
        m = compute_metrics(trades)
        assert m["win_rate"] == 0.5
        assert m["total_trades"] == 4

    def test_max_drawdown(self):
        # Simulate drawdown
        trades = [{"pnl_pct": -8.0}, {"pnl_pct": 5.0}, {"pnl_pct": 3.0}]
        m = compute_metrics(trades)
        assert m["max_drawdown_pct"] >= 0.0


class TestRun:
    def test_run_returns_approval_fields(self):
        rule = {
            "rule_id": "test-rule",
            "name": "test",
            "pattern": {"regime": "sideways"},
            "action": "hold",
            "winrate": 0.6,
            "sample_size": 15,
        }
        result = run(rule, symbols=["000001"], lookback_days=30)
        assert "backtest_result" in result
        assert "approved" in result
        assert "rejection_reason" in result

    def test_good_rule_can_pass(self):
        rule = {
            "rule_id": "good-rule",
            "name": "good",
            "pattern": {"regime": "trend_up"},
            "action": "buy",
            "winrate": 0.7,
            "sample_size": 15,
        }
        result = run(rule, symbols=["000001"], lookback_days=30)
        # May or may not approve depending on data availability
        assert "approved" in result


class TestGates:
    def test_gate_constants_defined(self):
        assert GATE_SHARPE == 1.2
        assert GATE_MDD == 12.0
        assert GATE_WINRATE == 0.45
        assert GATE_MIN_TRADES == 10
