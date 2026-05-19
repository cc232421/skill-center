"""
self_review_and_extract — Rules-based self-review & lesson extraction
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import decision_snapshot

LESSONS_DIR = Path(os.path.expanduser("~/.sel_data/lessons"))
LESSONS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Lesson Type Rules ───────────────────────────────────────────────────────

LESSON_RULES = [
    {
        "name": "black_swan_hit",
        "condition": lambda s: (s.get("pnl") or 999) < -8.0,
        "tags": ["black_swan", "extreme_loss", "stop_loss_missed"],
        "summary_template": "触发黑天鹅事件，单笔亏损 {pnl:.1f}%",
    },
    {
        "name": "trend_riding_success",
        "condition": lambda s: (s.get("pnl") or -999) > 5.0 and s.get("regime") == "trend_up",
        "tags": ["trend_up", "hold", "momentum"],
        "summary_template": "在 {regime} 体制中，持仓盈利 {pnl:.1f}%",
    },
    {
        "name": "trend_riding_loss",
        "condition": lambda s: (s.get("pnl") or 999) < -3.0 and s.get("regime") == "trend_up",
        "tags": ["trend_up", "loss", "overstay"],
        "summary_template": "趋势上涨中持仓亏损 {pnl:.1f}%，可能过度持有",
    },
    {
        "name": "range_trap_loss",
        "condition": lambda s: (s.get("pnl") or 999) < -3.0 and s.get("regime") == "sideways",
        "tags": ["sideways", "loss", "range_trap"],
        "summary_template": "震荡市逆势操作亏损 {pnl:.1f}%",
    },
    {
        "name": "volatile_loss",
        "condition": lambda s: (s.get("pnl") or 999) < -3.0 and s.get("regime") == "volatile",
        "tags": ["volatile", "loss", "high_risk"],
        "summary_template": "高波动体制中亏损 {pnl:.1f}%，建议降仓",
    },
    {
        "name": "stalled_position",
        "condition": lambda s: abs(s.get("pnl") or 0) < 1.0,
        "tags": ["stalled", "no_direction", "wait"],
        "summary_template": "持仓无方向，{pnl:.1f}% 接近零",
    },
    {
        "name": "strategy_rotting",
        "condition": lambda s: False,  # filled in dynamically
        "tags": ["strategy_rotting", "edge_lost"],
        "summary_template": "策略 {strategy} 连续亏损超过阈值",
    },
    {
        "name": "regime_edge",
        "condition": lambda s: (s.get("pnl") or -999) > 2.0 and s.get("regime") in ("trend_up", "trend_down"),
        "tags": ["regime_edge", "directional", "trend"],
        "summary_template": "在 {regime} 体制中顺势盈利 {pnl:.1f}%",
    },
]


def _load_all_snapshots() -> list[dict]:
    """Load all completed snapshots from disk."""
    snapshots = []
    snap_dir = Path(os.path.expanduser("~/.sel_data/snapshots"))
    if not snap_dir.exists():
        return snapshots
    for month in snap_dir.iterdir():
        if not month.is_dir():
            continue
        for path in month.glob("snapshot-*.json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("result") in ("win", "loss") and data.get("pnl") is not None:
                snapshots.append(data)
    return snapshots


def _group_by_strategy(snapshots: list[dict]) -> dict[str, list[dict]]:
    groups: dict = {}
    for s in snapshots:
        key = s.get("strategy", "default")
        groups.setdefault(key, []).append(s)
    return groups


def _detect_rotting(snapshots: list[dict], min_streak: int = 3) -> list[dict]:
    """Detect consecutive losses per strategy."""
    rotting = []
    for strategy, s_list in _group_by_strategy(snapshots).items():
        s_list_sorted = sorted(s_list, key=lambda x: x.get("created_at", ""))
        streak = 0
        for s in reversed(s_list_sorted[-10:]):   # last 10
            if s.get("result") == "loss":
                streak += 1
                if streak >= min_streak:
                    rotting.append({
                        "lesson_type": "strategy_rotting",
                        "strategy": strategy,
                        "summary": f"策略 {strategy} 连续 {streak} 次亏损",
                        "tags": ["strategy_rotting", "edge_lost"],
                        "regime": s.get("regime"),
                        "streak": streak,
                    })
                    break
            else:
                streak = 0
    return rotting


def _safe_lesson_format(template: str, regime: str, pnl: float, strategy: str) -> str:
    """Safe summary formatting — handles NaN/inf gracefully."""
    try:
        return template.format(regime=regime, pnl=pnl, strategy=strategy)
    except (ValueError, TypeError):
        # Fallback for NaN/inf: strip format specs and substitute raw values
        safe_template = template.replace("{pnl:.1f}", str(round(pnl, 1)))
        safe_template = safe_template.replace("{pnl}", str(round(pnl, 1)))
        safe_template = safe_template.replace("{regime}", str(regime))
        safe_template = safe_template.replace("{strategy}", str(strategy))
        return safe_template


def _extract_lesson(snapshot: dict) -> Optional[dict]:
    """Match snapshot against lesson rules."""
    pnl_raw = snapshot.get("pnl", 0.0)
    # Guard against NaN/inf — convert to safe float
    try:
        pnl = float(pnl_raw) if pnl_raw == pnl_raw else 0.0  # NaN check: x != x is True for NaN
    except (TypeError, ValueError):
        pnl = 0.0
    for rule in LESSON_RULES:
        if rule["name"] == "strategy_rotting":
            continue
        if rule["condition"](snapshot):
            template = rule["summary_template"]
            summary = _safe_lesson_format(
                template,
                snapshot.get("regime", ""),
                pnl,
                snapshot.get("strategy", ""),
            )
            return {
                "id": str(uuid.uuid4()),
                "lesson_type": rule["name"],
                "summary": summary,
                "tags": rule["tags"],
                "regime": snapshot.get("regime", "unknown"),
                "strategy": snapshot.get("strategy", "default"),
                "pnl_pct": pnl,
                "winrate_after": 0.5,  # placeholder, updated by sandbox
                "sample_size": 1,
                "confidence": 0.75,
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "source_snapshot_id": snapshot.get("id"),
            }
    return None


def _winrate_by_regime(snapshots: list[dict]) -> dict[str, float]:
    """Calculate winrate per regime."""
    from collections import defaultdict
    regime_stats: dict = defaultdict(lambda: {"wins": 0, "total": 0})
    for s in snapshots:
        r = s.get("regime", "unknown")
        regime_stats[r]["total"] += 1
        if s.get("result") == "win":
            regime_stats[r]["wins"] += 1
    return {
        r: round(stats["wins"] / stats["total"], 3)
        if stats["total"] > 0 else 0.0
        for r, stats in regime_stats.items()
    }


def _count_results(snapshots: list[dict]) -> tuple[int, int, int]:
    """Count wins/losses/holds from snapshot list."""
    wins = losses = holds = 0
    for s in snapshots:
        r = s.get("result")
        if r == "win":
            wins += 1
        elif r == "loss":
            losses += 1
        else:
            holds += 1
    return wins, losses, holds


def _save_lesson(lesson: dict) -> None:
    """Persist a lesson to disk."""
    lesson_path = LESSONS_DIR / f"lesson-{lesson['id']}.json"
    with open(lesson_path, "w", encoding="utf-8") as f:
        json.dump(lesson, f, ensure_ascii=False, indent=2)


def _build_summary(
    snapshots: list[dict],
    lessons: list[dict],
    wins: int,
    losses: int,
    holds: int,
) -> dict:
    """Build the summary dict from stats."""
    total = wins + losses + holds
    winrate = round(wins / (wins + losses), 3) if (wins + losses) > 0 else 0.0
    win_snaps = [s for s in snapshots if s.get("result") == "win"]
    loss_snaps = [s for s in snapshots if s.get("result") == "loss"]
    avg_win = round(sum(s.get("pnl", 0) for s in win_snaps) / max(wins, 1), 2)
    avg_loss = round(sum(s.get("pnl", 0) for s in loss_snaps) / max(losses, 1), 2)
    all_snapshots = _load_all_snapshots()
    regime_wr = _winrate_by_regime(all_snapshots)
    return {
        "snapshots_reviewed": len(snapshots),
        "wins": wins,
        "losses": losses,
        "holds": holds,
        "winrate": winrate,
        "avg_win_pct": avg_win,
        "avg_loss_pct": avg_loss,
        "new_lessons": len(lessons),
        "regime_winrates": regime_wr,
    }


def run(snapshot_ids: Optional[list[str]] = None, force_recalculate: bool = False) -> dict:
    """
    Review snapshots and extract lessons.

    Returns:
        {"lessons": [...], "summary": {...}}
    """
    all_snapshots = _load_all_snapshots()

    # Filter by IDs if given
    if snapshot_ids:
        snapshots = [s for s in all_snapshots if s.get("id") in set(snapshot_ids)]
    else:
        snapshots = [s for s in all_snapshots if s.get("review_status") == "pending"]

    lessons: list[dict] = []

    # Extract lessons from each snapshot
    for s in snapshots:
        lesson = _extract_lesson(s)
        if lesson:
            lessons.append(lesson)
            _save_lesson(lesson)
        _update_snapshot_status(s.get("id"), "reviewed")

    # Add rotting lessons (computed over full history for context)
    rotting_lessons = _detect_rotting(all_snapshots)
    lessons.extend(rotting_lessons)
    for r in rotting_lessons:
        r["id"] = str(uuid.uuid4())
        r["confidence"] = 0.9
        r["sample_size"] = r.get("streak", 1)
        r["extracted_at"] = datetime.now(timezone.utc).isoformat()
        _save_lesson(r)

    wins, losses, holds = _count_results(snapshots)

    return {
        "lessons": lessons,
        "summary": _build_summary(snapshots, lessons, wins, losses, holds),
    }


def _update_snapshot_status(snapshot_id: str, status: str) -> None:
    decision_snapshot.update_snapshot(snapshot_id, {"review_status": status})
