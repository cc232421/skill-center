"""
sandbox_simulation — Historical backtest engine
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from perception_and_regime import fetch_market_data

BACKTEST_DIR = Path(os.path.expanduser("~/.sel_data/backtests"))
BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

GATE_SHARPE = 1.2
GATE_MDD = 12.0
GATE_WINRATE = 0.45
GATE_MIN_TRADES = 10


def apply_rule_to_df(rule: dict, df: pd.DataFrame) -> list[dict]:
    """
    Apply a rule to OHLCV DataFrame to generate trading signals.
    Returns list of trades.
    """
    regime = rule.get("pattern", {}).get("regime")
    action = rule.get("action", "hold")
    n = len(df)
    trades = []

    if regime is None:
        # No regime filter: apply action everywhere
        for i in range(n):
            trades.append({
                "entry_idx": i,
                "entry_date": df["date"].iloc[i],
                "entry_price": df["close"].iloc[i],
                "action": action,
                "rule_id": rule.get("rule_id"),
            })
        return trades

    # Compute regime for each bar (simplified: use SMA slope)
    close = df["close"].values.astype(float)
    sma20 = pd.Series(close).rolling(20).mean().values
    adx_vals = np.zeros(n)
    # Use simple proxy for ADX: rate of change
    roc = np.zeros(n)
    for i in range(20, n):
        roc[i] = (close[i] - close[i - 5]) / close[i - 5] * 100 if close[i - 5] != 0 else 0

    in_position = False
    entry_idx = entry_price = entry_date = None

    for i in range(20, n):
        # Regime classification (simplified)
        if roc[i] > 2.0:
            bar_regime = "trend_up"
        elif roc[i] < -2.0:
            bar_regime = "trend_down"
        else:
            bar_regime = "sideways"

        if bar_regime == regime and not in_position:
            in_position = True
            entry_idx = i
            entry_price = float(df["close"].iloc[i])
            entry_date = df["date"].iloc[i]
        elif in_position and bar_regime != regime:
            # Exit
            exit_price = float(df["close"].iloc[i])
            trades.append({
                "entry_idx": entry_idx,
                "entry_date": entry_date,
                "entry_price": entry_price,
                "exit_idx": i,
                "exit_date": df["date"].iloc[i],
                "exit_price": exit_price,
                "pnl_pct": round((exit_price - entry_price) / entry_price * 100, 3),
                "rule_id": rule.get("rule_id"),
            })
            in_position = False

    return trades


def compute_metrics(trades: list[dict]) -> dict:
    """Compute Sharpe, max drawdown, winrate from trades."""
    if not trades:
        return {"sharpe_ratio": 0.0, "max_drawdown_pct": 100.0, "win_rate": 0.0, "total_trades": 0}

    pnls = [t["pnl_pct"] for t in trades if "pnl_pct" in t]
    if not pnls:
        return {"sharpe_ratio": 0.0, "max_drawdown_pct": 100.0, "win_rate": 0.0, "total_trades": 0}

    # Sharpe ratio (annualized, assuming 252 trading days)
    import math
    mean_pnl = np.mean(pnls)
    std_pnl = np.std(pnls) if len(pnls) > 1 else 1.0
    if std_pnl == 0:
        sharpe = 0.0
    else:
        sharpe = (mean_pnl / std_pnl) * math.sqrt(252)

    # Max drawdown
    cumulative = np.cumsum([p / 100 for p in pnls])
    peak = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - peak) * 100
    max_dd = abs(float(np.min(drawdown))) if len(drawdown) > 0 else 0.0

    win_count = sum(1 for p in pnls if p > 0)
    win_rate = win_count / len(pnls)

    return {
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown_pct": round(max_dd, 2),
        "win_rate": round(win_rate, 3),
        "total_trades": len(pnls),
        "avg_hold_days": 3.5,  # estimated
    }


def _fetch_backtest_data(symbols: list[str], lookback_days: int) -> tuple[dict, str, str]:
    """Fetch market data for backtesting. Returns (data, start_date, end_date)."""
    data = fetch_market_data(symbols, market="A", period="day")
    start_date = end_date = ""
    if data:
        first_sym = list(data.keys())[0]
        dates = data[first_sym]["dates"]
        start_date = dates[0] if dates else ""
        end_date = dates[-1] if dates else ""
    return data, start_date, end_date


def _apply_rule_to_symbols(rule: dict, data: dict, lookback_days: int) -> list[dict]:
    """Apply rule to all symbols, collect all trades."""
    all_trades = []
    for sym, d in data.items():
        df = pd.DataFrame(d)
        if len(df) < 30:
            continue
        df = df.tail(lookback_days)
        all_trades.extend(apply_rule_to_df(rule, df))
    return all_trades


def _gate_check(metrics: dict) -> list[str]:
    """Validate metrics against gates. Returns list of rejection reasons."""
    reasons = []
    if metrics["total_trades"] < GATE_MIN_TRADES:
        reasons.append(f"min_trades:{metrics['total_trades']}<{GATE_MIN_TRADES}")
    elif metrics["win_rate"] < GATE_WINRATE:
        reasons.append(f"winrate:{metrics['win_rate']:.3f}<{GATE_WINRATE}")
    if metrics["max_drawdown_pct"] > GATE_MDD:
        reasons.append(f"mdd:{metrics['max_drawdown_pct']:.2f}%>{GATE_MDD}%")
    if metrics["sharpe_ratio"] < GATE_SHARPE:
        reasons.append(f"sharpe:{metrics['sharpe_ratio']:.3f}<{GATE_SHARPE}")
    return reasons


def run(
    rule: dict,
    symbols: Optional[list[str]] = None,
    lookback_days: int = 60,
) -> dict:
    """
    Run sandbox simulation on a rule.

    Returns:
        {
            "backtest_result": {...},
            "approved": bool,
            "rejection_reason": str | None
        }
    """
    symbols = symbols or ["000001"]
    data, start_date, end_date = _fetch_backtest_data(symbols, lookback_days)
    all_trades = _apply_rule_to_symbols(rule, data, lookback_days)

    metrics = compute_metrics(all_trades)
    backtest_id = str(uuid.uuid4())
    rejection_reasons = _gate_check(metrics)

    result = {
        "backtest_id": backtest_id,
        "rule_id": rule.get("rule_id"),
        "lookback_days": lookback_days,
        "symbols": symbols,
        "start_date": start_date,
        "end_date": end_date,
        **metrics,
        "approved": len(rejection_reasons) == 0,
        "rejection_reasons": rejection_reasons,
    }

    path = BACKTEST_DIR / f"backtest-{backtest_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return {
        "backtest_result": result,
        "approved": result["approved"],
        "rejection_reason": "; ".join(rejection_reasons) if rejection_reasons else None,
    }
