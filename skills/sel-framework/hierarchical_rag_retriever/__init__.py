"""
hierarchical_rag_retriever — Local RAG retrieval with weighted scoring
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

SNAPSHOT_DIR = Path(os.path.expanduser("~/.sel_data/snapshots"))
CACHE_FILE = Path(os.path.expanduser("~/.sel_data/rag_cache.json"))

# Regime adjacency map for regime_match scoring
REGIME_ADJACENCY = {
    "trend_up": ["trend_down", "volatile"],    # adjacent regimes
    "trend_down": ["trend_up", "volatile"],
    "sideways": ["volatile"],
    "volatile": ["sideways", "trend_up", "trend_down"],
    "black_swan": [],
    "unknown": [],
}


def _time_decay(days_since: float, half_life: int = 30) -> float:
    """Exponential decay: halves every `half_life` days."""
    return 0.5 ** (days_since / half_life)


def _regime_match_score(regime1: str, regime2: str) -> float:
    """Regime match multiplier."""
    if regime1 == regime2:
        return 1.5
    if regime2 in REGIME_ADJACENCY.get(regime1, []):
        return 0.8
    return 0.3


def _winrate_for_strategy(strategy: str, snapshots: list[dict]) -> float:
    """Historical winrate for a given strategy."""
    strategy_snaps = [s for s in snapshots if s.get("strategy") == strategy]
    if not strategy_snaps:
        return 0.5  # neutral default
    win_count = sum(1 for s in strategy_snaps if s.get("result") == "win")
    return win_count / len(strategy_snaps)


def _load_cache(regime: str) -> Optional[dict]:
    """Load cached retrieval results if regime hasn't changed recently."""
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
        age = time.time() - cache.get("_cache_time", 0)
        if cache.get("_regime") == regime and age < 3600:  # 1 hour
            return cache
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return None


def _save_cache(regime: str, results: list[dict]) -> None:
    """Save retrieval results to cache."""
    cache = {"_regime": regime, "_cache_time": time.time(), "results": results}
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def _load_experiences() -> list[dict]:
    """Load all completed snapshots as experience records."""
    experiences = []
    if not SNAPSHOT_DIR.exists():
        return experiences
    for month in SNAPSHOT_DIR.iterdir():
        if not month.is_dir():
            continue
        for path in month.glob("snapshot-*.json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("result") in ("win", "loss"):
                experiences.append(data)
    return experiences


def score_experience(
    exp: dict,
    current_regime: str,
    current_strategy: str,
    all_snaps: list[dict],
    now: datetime,
) -> float:
    """Compute weighted score for an experience record."""
    # Time decay
    created = exp.get("created_at", "")
    try:
        created_dt = datetime.fromisoformat(created)
        days_since = (now - created_dt).total_seconds() / 86400
    except (ValueError, TypeError):
        days_since = 30
    td = _time_decay(max(days_since, 0))

    # Winrate
    strategy = exp.get("strategy", "default")
    wr = _winrate_for_strategy(strategy, all_snaps)

    # Regime match
    exp_regime = exp.get("regime", "unknown")
    rm = _regime_match_score(current_regime, exp_regime)

    return round(td * wr * rm, 4)


def retrieve(
    current_regime: str,
    strategy: str = "default",
    top_k: int = 5,
    min_score: float = 0.1,
) -> dict:
    """
    Retrieve top-k relevant experiences from the experience store.

    Returns:
        {
            "retrieved_experiences": [...],
            "total_experiences": int,
            "cache_hit": bool,
        }
    """
    # Check cache
    cached = _load_cache(current_regime)
    if cached is not None:
        cached_results = cached.get("results", [])
        return {
            "retrieved_experiences": cached_results[:top_k],
            "total_experiences": len(cached_results),
            "cache_hit": True,
        }

    experiences = _load_experiences()
    now = datetime.now(timezone.utc)

    scored = []
    for exp in experiences:
        score = score_experience(exp, current_regime, strategy, experiences, now)
        if score < min_score:
            continue
        exp_regime = exp.get("regime", "unknown")
        days_ago = 0.0
        try:
            created = datetime.fromisoformat(exp.get("created_at", ""))
            days_ago = (now - created).total_seconds() / 86400
        except (ValueError, TypeError):
            pass

        scored.append({
            "snapshot_id": exp.get("id"),
            "score": score,
            "regime_match_boost": _regime_match_score(current_regime, exp_regime),
            "time_decay_factor": round(_time_decay(max(days_ago, 0)), 4),
            "winrate": round(_winrate_for_strategy(exp.get("strategy", "default"), experiences), 3),
            "strategy": exp.get("strategy", "default"),
            "action": exp.get("action"),
            "regime": exp_regime,
            "result": exp.get("result"),
            "pnl_pct": exp.get("pnl"),
            "days_ago": round(days_ago, 1),
        })

    # Sort by score descending, deduplicate by strategy+regime (keep latest)
    seen: set = set()
    deduped: list[dict] = []
    for item in sorted(scored, key=lambda x: x["score"], reverse=True):
        key = (item["strategy"], item["regime"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    result = deduped[:top_k]
    _save_cache(current_regime, deduped)

    return {
        "retrieved_experiences": result,
        "total_experiences": len(experiences),
        "cache_hit": False,
    }
