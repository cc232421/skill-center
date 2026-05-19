"""
review_scheduler — Adaptive scheduling skill
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

from decision_snapshot import count_pending

# Strategy frequency → review interval (hours)
FREQUENCY_MAP = {
    "daytrade": 1,
    "intraday": 4,
    "swing": 24,
    "position": 168,    # weekly
    "longterm": 720,    # monthly
}

STATE_FILE = os.path.expanduser("~/.sel_data/review_scheduler_state.json")


def _load_state() -> dict:
    import json
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    import json
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def detect_frequency(strategy_name: str = "default") -> str:
    """Infer review frequency from strategy name heuristics."""
    s = strategy_name.lower()
    if any(k in s for k in ["daytrade", "scalp", "1m", "5m"]):
        return "daytrade"
    elif any(k in s for k in ["intraday", "30m", "60m"]):
        return "intraday"
    elif any(k in s for k in ["swing", "chanlun", "breakout"]):
        return "swing"
    elif any(k in s for k in ["long", "invest", "monthly"]):
        return "longterm"
    return "position"


def should_trigger_review(
    strategy_name: str = "default",
    pending_count: int = 0,
    override: bool = False,
) -> bool:
    """
    Determine if a review should trigger now.
    """
    state = _load_state()
    freq = detect_frequency(strategy_name)
    interval_hours = FREQUENCY_MAP.get(freq, 168)

    last_key = f"last_review_{strategy_name}"
    last_review = state.get(last_key)
    now = datetime.now(timezone.utc)

    if override:
        return True

    if last_review is None:
        return pending_count > 0

    last_dt = datetime.fromisoformat(last_review)
    elapsed = (now - last_dt).total_seconds() / 3600

    # Frequency-based trigger
    if elapsed >= interval_hours and pending_count > 0:
        return True

    # Count-based trigger (regardless of time)
    thresholds = {"daytrade": 5, "intraday": 3, "swing": 1, "position": 1, "longterm": 1}
    if pending_count >= thresholds.get(freq, 1):
        return True

    return False


def trigger_review(strategy_name: str = "default") -> dict:
    """
    Record that a review was triggered and compute next review time.
    """
    state = _load_state()
    freq = detect_frequency(strategy_name)
    interval_hours = FREQUENCY_MAP.get(freq, 168)
    now = datetime.now(timezone.utc)
    next_dt = now + timedelta(hours=interval_hours)

    state[f"last_review_{strategy_name}"] = now.isoformat()
    state[f"frequency_{strategy_name}"] = freq
    _save_state(state)

    pending = count_pending(strategy=strategy_name)

    return {
        "next_review_at": next_dt.isoformat(),
        "pending_reviews": pending,
        "triggered": True,
        "frequency": freq,
        "schedule_id": str(uuid.uuid4()),
    }
