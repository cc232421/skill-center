"""
observability_hub — Unified logging + alert hub
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

LOG_DIR = Path(os.path.expanduser("~/.sel_data/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

WEBHOOK_URL = os.environ.get("SEL_ALERT_WEBHOOK_URL", "")

# ─── Alert Rules ─────────────────────────────────────────────────────────────

ALERT_RULES = [
    {
        "event_type": "regime",
        "condition": lambda p: p.get("regime_label") == "black_swan" or p.get("regime") == "black_swan",
        "severity": "critical",
        "message_template": "Black swan regime detected: {regime_label}",
    },
    {
        "event_type": "evolution",
        "condition": lambda p: p.get("approved") is False,
        "severity": "warning",
        "message_template": "Evolution rule rejected: {rule_id}",
    },
    {
        "event_type": "winrate",
        "condition": lambda p: p.get("win_rate", 1.0) < 0.4,
        "severity": "error",
        "message_template": "Winrate below 40%: {win_rate}",
    },
    {
        "event_type": "sandbox",
        "condition": lambda p: p.get("approved") is True,
        "severity": "info",
        "message_template": "Sandbox approved: {rule_id} sharpe={sharpe_ratio}",
    },
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _persist_log(event_type: str, severity: str, skill: str, message: str, payload: dict) -> None:
    """Write structured log entry to disk."""
    log_file = LOG_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m')}.jsonl"
    entry = {
        "timestamp": _now_iso(),
        "event_type": event_type,
        "severity": severity,
        "skill": skill,
        "message": message,
        "payload": payload,
        "metrics": _current_metrics(),
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _current_metrics() -> dict:
    """Compute current framework metrics."""
    # Load snapshots
    snap_dir = Path(os.path.expanduser("~/.sel_data/snapshots"))
    snapshots = []
    if snap_dir.exists():
        for month in snap_dir.iterdir():
            if not month.is_dir():
                continue
            for path in month.glob("snapshot-*.json"):
                try:
                    with open(path, encoding="utf-8") as f:
                        snapshots.append(json.load(f))
                except (json.JSONDecodeError, FileNotFoundError):
                    pass

    win_count = sum(1 for s in snapshots if s.get("result") == "win")
    loss_count = sum(1 for s in snapshots if s.get("result") == "loss")
    total = win_count + loss_count
    winrate = round(win_count / total, 3) if total > 0 else 0.0

    rules_dir = Path(os.path.expanduser("~/.sel_data/rules"))
    active_rules = 0
    if rules_dir.exists():
        for p in rules_dir.glob("rule-*.json"):
            try:
                with open(p) as f:
                    r = json.load(f)
                if r.get("status") == "active":
                    active_rules += 1
            except (json.JSONDecodeError, FileNotFoundError):
                pass

    return {
        "winrate": winrate,
        "experience_count": len(snapshots),
        "active_rules": active_rules,
    }


def _safe_format(template: str, payload: dict) -> str:
    """Safe message formatting — substitutes {key} with truncated string values only."""
    result = template
    for key, value in payload.items():
        placeholder = f"{{{key}}}"
        if placeholder in result:
            # Truncate to 200 chars to prevent memory exhaustion, convert to str
            result = result.replace(placeholder, str(value)[:200])
    return result


def _send_webhook(event: dict) -> bool:
    """Send alert via webhook if configured."""
    if not WEBHOOK_URL:
        return False
    try:
        import requests
        response = requests.post(WEBHOOK_URL, json=event, timeout=5)
        response.raise_for_status()
        return True
    except Exception:
        return False


def log(
    event_type: str,
    payload: dict,
    severity: str = "info",
    skill: str = "",
    message: str = "",
) -> dict:
    """
    Main entry point: log an event and optionally alert.

    Returns:
        {"logged": bool, "alerted": bool}
    """
    # Auto-generate message from template if empty
    if not message:
        for rule in ALERT_RULES:
            if rule["event_type"] == event_type and rule["condition"](payload):
                message = _safe_format(rule["message_template"], payload)
                severity = rule["severity"]
                break

    _persist_log(event_type, severity, skill, message, payload)

    # Check if this should alert
    alerted = False
    alerted_condition_met = False
    for rule in ALERT_RULES:
        if rule["event_type"] == event_type and rule["condition"](payload):
            alerted_condition_met = True
            alert_payload = {
                "timestamp": _now_iso(),
                "event_type": event_type,
                "severity": rule["severity"],
                "skill": skill,
                "message": message,
                "payload": payload,
            }
            alerted = _send_webhook(alert_payload)
            break

    return {"logged": True, "alerted": alerted_condition_met}


def get_recent_logs(n: int = 50) -> list[dict]:
    """Get the most recent n log entries."""
    log_file = LOG_DIR / f"{datetime.now(timezone.utc).strftime('%Y-%m')}.jsonl"
    if not log_file.exists():
        return []
    with open(log_file, encoding="utf-8") as f:
        lines = f.readlines()
    entries = [json.loads(l) for l in lines[-n:]]
    return list(reversed(entries))


def metrics() -> dict:
    """Return current framework metrics for Grafana export."""
    m = _current_metrics()
    return {
        "winrate": m["winrate"],
        "experience_count": m["experience_count"],
        "active_rules": m["active_rules"],
        "timestamp": _now_iso(),
    }


def grafana_metrics_text() -> str:
    """Return Prometheus-compatible /metrics text."""
    m = _current_metrics()
    lines = [
        "# HELP sel_framework_winrate Overall win rate",
        "# TYPE sel_framework_winrate gauge",
        f"sel_framework_winrate {m['winrate']}",
        "",
        "# HELP sel_framework_experience_count Total experiences in RAG",
        "# TYPE sel_framework_experience_count gauge",
        f"sel_framework_experience_count {m['experience_count']}",
        "",
        "# HELP sel_framework_active_rules Number of active rules",
        "# TYPE sel_framework_active_rules gauge",
        f"sel_framework_active_rules {m['active_rules']}",
    ]
    return "\n".join(lines)
