"""
common/paths.py — Unified path resolution for SEL Framework.
All paths resolve from SEL_DATA_DIR at call time — no cached module-level constants.
"""
from __future__ import annotations

import os
from pathlib import Path


def _sel_data() -> Path:
    return Path(os.environ.get("SEL_DATA_DIR", os.path.expanduser("~/.sel_data")))


def get_data_dir() -> Path:
    return _sel_data()


def get_snapshots_dir() -> Path:
    p = _sel_data() / "snapshots"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_rules_dir() -> Path:
    p = _sel_data() / "rules"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_backtests_dir() -> Path:
    p = _sel_data() / "backtests"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_lessons_dir() -> Path:
    p = _sel_data() / "lessons"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_logs_dir() -> Path:
    p = _sel_data() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_reviews_dir() -> Path:
    p = _sel_data() / "reviews"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_alerts_dir() -> Path:
    p = _sel_data() / "alerts"
    p.mkdir(parents=True, exist_ok=True)
    return p
