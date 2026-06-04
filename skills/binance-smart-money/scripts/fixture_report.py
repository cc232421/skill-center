#!/usr/bin/env python3
"""Generate an offline Binance Smart Money report from a fixture JSON file."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path


FORBIDDEN = ("buy now", "sell now", "long now", "short now", "guaranteed")


def pct(n: float | None, digits: int = 1) -> str:
    if n is None or not math.isfinite(float(n)):
        return "-"
    return f"{float(n) * 100:.{digits}f}%"


def pct_raw(n: float | None, digits: int = 1) -> str:
    if n is None or not math.isfinite(float(n)):
        return "-"
    return f"{float(n):.{digits}f}%"


def usd(n: float | None) -> str:
    if n is None or not math.isfinite(float(n)):
        return "-"
    n = float(n)
    if abs(n) >= 1e9:
        return f"${n / 1e9:.2f}B"
    if abs(n) >= 1e6:
        return f"${n / 1e6:.2f}M"
    if abs(n) >= 1e3:
        return f"${n / 1e3:.2f}K"
    return f"${n:.2f}"


def report(payload: dict) -> str:
    sm = payload["smart_money"]
    oi = payload.get("open_interest") or {}

    long_profit = sm["longProfitTraders"] / sm["longTraders"] if sm["longTraders"] else 0
    short_profit = sm["shortProfitTraders"] / sm["shortTraders"] if sm["shortTraders"] else 0
    long_whale_profit = sm["longProfitWhales"] / sm["longWhales"] if sm["longWhales"] else 0
    short_whale_profit = sm["shortProfitWhales"] / sm["shortWhales"] if sm["shortWhales"] else 0
    spread = (
        (sm["shortWhalesAvgEntryPrice"] - sm["longWhalesAvgEntryPrice"])
        / sm["longWhalesAvgEntryPrice"]
        if sm["longWhalesAvgEntryPrice"]
        else 0
    )
    sm_notional = (
        sm["longTradersQty"] * sm["longTradersAvgEntryPrice"]
        + sm["shortTradersQty"] * sm["shortTradersAvgEntryPrice"]
    )
    oi_now = oi.get("oiNowUsd")
    sm_share = sm_notional / oi_now if oi_now and oi_now > 0 else None

    if short_whale_profit - long_whale_profit > 0.2:
        read = "Short whales are materially more profitable than long whales."
    elif long_whale_profit - short_whale_profit > 0.2:
        read = "Long whales are materially more profitable than short whales."
    else:
        read = "Whale profit distribution is relatively balanced."

    if spread > 0.05:
        spread_read = "Short whale average entry is meaningfully above long whale average entry."
    elif spread < -0.05:
        spread_read = "Long whale average entry is meaningfully above short whale average entry."
    else:
        spread_read = "Whale average-entry spread is small."

    lines = [
        "# Binance Smart Money Report",
        "",
        "## Scope",
        f"- Mode: offline-fixture",
        f"- Source: fixture",
        f"- Snapshot: {payload.get('symbol', sm['symbol'])} @ {payload.get('snapshot_ts', sm['ts'])}",
        "",
        "## Key Metrics",
        "| Metric | Value | Interpretation |",
        "|---|---:|---|",
        f"| Long profit traders | {pct(long_profit)} | all smart-money long traders in profit |",
        f"| Short profit traders | {pct(short_profit)} | all smart-money short traders in profit |",
        f"| Long whale profit | {pct(long_whale_profit)} | whale longs in profit |",
        f"| Short whale profit | {pct(short_whale_profit)} | whale shorts in profit |",
        f"| Whale average-entry spread | {pct(spread)} | short avg minus long avg, divided by long avg |",
        f"| Smart Money notional | {usd(sm_notional)} | derived from quantity times average entry |",
        f"| Smart Money OI share | {pct(sm_share)} | share of total OI when OI is available |",
        f"| OI change 1h | {pct_raw(oi.get('oiChg1h'))} | open-interest velocity |",
        f"| OI change 4h | {pct_raw(oi.get('oiChg4h'))} | null means missing data, not zero |",
        "",
        "## Read",
        f"{read} {spread_read} This is a positioning read, not a trade instruction.",
        "",
        "## Risks And Data Gaps",
        "- Fixture data is static and only validates calculations.",
        "- Binance Smart Signal is undocumented and can change schema.",
        "- Missing OI velocity must stay missing rather than being treated as zero.",
        "",
        "## Verification",
        "- Calculated from fixture without network access.",
    ]
    output = "\n".join(lines)
    lowered = output.lower()
    for phrase in FORBIDDEN:
        if phrase in lowered:
            raise RuntimeError(f"forbidden trading instruction found: {phrase}")
    return output


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: fixture_report.py <fixture.json>", file=sys.stderr)
        return 2
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(report(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

