"""
skill_evolution_meta — Rules-driven meta evolution
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from decision_snapshot import SNAPSHOT_DIR

RULES_DIR = Path(os.path.expanduser("~/.sel_data/rules"))
RULES_DIR.mkdir(parents=True, exist_ok=True)


# ─── Evolution Triggers ──────────────────────────────────────────────────────

def check_evolution_triggers(lessons: list[dict], snapshots: list[dict]) -> tuple[bool, str]:
    """
    Check if evolution should trigger.
    Returns (should_evolve, reason).
    """
    if not snapshots and not lessons:
        return False, "no_signal"

    # Count consecutive losses per strategy
    from collections import defaultdict
    strategy_results: dict = defaultdict(list)
    for s in sorted(snapshots, key=lambda x: x.get("created_at", "")):
        strategy_results[s.get("strategy", "default")].append(s.get("result"))

    for strategy, results in strategy_results.items():
        recent = results[-10:]
        streak = 0
        for r in reversed(recent):
            if r == "loss":
                streak += 1
            else:
                break
        if streak >= 3:
            return True, f"strategy_rotting:{strategy}"

    # strategy_rotting lessons
    rotting = [l for l in lessons if l.get("lesson_type") == "strategy_rotting"]
    if rotting:
        return True, "strategy_rotting_detected"

    return False, "no_signal"


# ─── Evolution Modes ──────────────────────────────────────────────────────────

def evolve_patch(snapshots: list[dict], strategy: str) -> list[dict]:
    """Mode A: Generate a rule patch for a specific failure pattern."""
    # Detect most common loss regime
    from collections import Counter
    loss_regimes = [s.get("regime") for s in snapshots if s.get("result") == "loss"]
    if not loss_regimes:
        return []
    common_regime, _ = Counter(loss_regimes).most_common(1)[0]

    patch = {
        "rule_id": str(uuid.uuid4()),
        "name": f"{common_regime}_avoid_patch",
        "pattern": {"regime": common_regime},
        "action": "hold",
        "priority": 1,
        "created_from": "lessons",
        "mode": "patch",
        "strategy": strategy,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "sandbox_verifying",
    }
    return [patch]


def evolve_clone(snapshots: list[dict]) -> list[dict]:
    """Mode B: Detect high-winrate sub-strategies and clone them."""
    from collections import defaultdict
    strategy_stats: dict = defaultdict(lambda: {"wins": 0, "losses": 0, "regimes": set()})
    for s in snapshots:
        st = s.get("strategy", "default")
        strategy_stats[st]["regimes"].add(s.get("regime", "unknown"))
        if s.get("result") == "win":
            strategy_stats[st]["wins"] += 1
        elif s.get("result") == "loss":
            strategy_stats[st]["losses"] += 1

    clones = []
    for st, stats in strategy_stats.items():
        total = stats["wins"] + stats["losses"]
        if total < 3:
            continue
        wr = stats["wins"] / total
        if wr >= 0.6:
            for regime in stats["regimes"]:
                clone = {
                    "rule_id": str(uuid.uuid4()),
                    "name": f"{st}_{regime}_clone",
                    "pattern": {"strategy": st, "regime": regime},
                    "action": "increase_exposure",
                    "priority": 2,
                    "created_from": "clone",
                    "mode": "clone",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "sandbox_verifying",
                    "winrate": wr,
                    "sample_size": total,
                }
                clones.append(clone)
    return clones


def evolve_restructure(snapshots: list[dict], lessons: list[dict]) -> list[dict]:
    """Mode C: Full rule restructuring based on regime-action matrix."""
    # Build regime → action priority matrix
    from collections import defaultdict
    regime_action: dict = defaultdict(lambda: {"win": 0, "total": 0})
    for s in snapshots:
        r = s.get("regime", "unknown")
        regime_action[r]["total"] += 1
        if s.get("result") == "win":
            regime_action[r]["win"] += 1

    rules = []
    for regime, stats in regime_action.items():
        if stats["total"] < 3:
            continue
        wr = stats["win"] / stats["total"]
        action = "increase_exposure" if wr > 0.55 else "reduce_exposure" if wr < 0.45 else "maintain"
        rule = {
            "rule_id": str(uuid.uuid4()),
            "name": f"regime_{regime}_restructure",
            "pattern": {"regime": regime},
            "action": action,
            "priority": 3,
            "created_from": "restructure",
            "mode": "restructure",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "sandbox_verifying",
            "winrate": round(wr, 3),
            "sample_size": stats["total"],
        }
        rules.append(rule)
    return rules


# ─── Main ─────────────────────────────────────────────────────────────────────

def _load_snapshots(snap_dir: Optional[Path] = None) -> list[dict]:
    if snap_dir is None:
        snap_dir = SNAPSHOT_DIR
    if not snap_dir.exists():
        return []
    snapshots = []
    for month in snap_dir.iterdir():
        if not month.is_dir():
            continue
        for path in month.glob("snapshot-*.json"):
            with open(path, encoding="utf-8") as f:
                snapshots.append(json.load(f))
    return snapshots


def _save_rule(rule: dict) -> None:
    path = RULES_DIR / f"rule-{rule['rule_id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rule, f, ensure_ascii=False, indent=2)


def run(lessons: list[dict]) -> dict:
    """
    Run evolution meta-skill.
    Returns:
        {
            "new_rules": [...],
            "activated_rules": [...],
            "rejected_rules": [...],
            "evolution_status": "evolved" | "no_signal" | "paused"
        }
    """
    snapshots = _load_snapshots()
    should_ev, reason = check_evolution_triggers(lessons, snapshots)

    if not should_ev:
        return {
            "new_rules": [],
            "activated_rules": [],
            "rejected_rules": [],
            "evolution_status": "no_signal",
            "reason": reason,
        }

    new_rules: list[dict] = []
    activated: list[dict] = []
    rejected: list[dict] = []

    # Determine evolution mode
    rotting_count = sum(1 for l in lessons if l.get("lesson_type") == "strategy_rotting")
    if rotting_count > 0:
        mode = "patch"
        strategy = lessons[0].get("strategy", "default") if lessons else "default"
        new_rules.extend(evolve_patch(snapshots, strategy))
    elif len(lessons) >= 5:
        mode = "restructure"
        new_rules.extend(evolve_clone(snapshots))
        new_rules.extend(evolve_restructure(snapshots, lessons))
    else:
        mode = "clone"
        new_rules.extend(evolve_clone(snapshots))

    # Sandbox validate each rule
    for rule in new_rules:
        _save_rule(rule)
        # Call sandbox (inline to avoid circular import)
        approved = _inline_sandbox_validate(rule)
        if approved:
            rule["status"] = "active"
            activated.append(rule)
        else:
            rule["status"] = "rejected"
            rejected.append(rule)
        _save_rule(rule)

    return {
        "new_rules": new_rules,
        "activated_rules": activated,
        "rejected_rules": rejected,
        "evolution_status": "evolved",
        "evolution_mode": mode,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _inline_sandbox_validate(rule: dict) -> bool:
    """
    Quick inline validation using winrate threshold.
    Full sandbox validation done by sandbox_simulation skill.
    """
    wr = rule.get("winrate", 0.5)
    sample = rule.get("sample_size", 0)
    # Quick gate: reject if winrate < 0.45 and sample >= 5
    if sample >= 5 and wr < 0.45:
        return False
    return True
