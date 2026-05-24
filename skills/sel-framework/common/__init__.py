"""
Re-export all path getters from paths.py (call-time resolution).
Import from here or from paths directly — both give dynamic resolution.
"""
from common.paths import (
    get_alerts_dir,
    get_backtests_dir,
    get_data_dir,
    get_lessons_dir,
    get_logs_dir,
    get_reviews_dir,
    get_rules_dir,
    get_snapshots_dir,
)

__all__ = [
    "get_data_dir",
    "get_snapshots_dir",
    "get_rules_dir",
    "get_backtests_dir",
    "get_lessons_dir",
    "get_logs_dir",
    "get_reviews_dir",
    "get_alerts_dir",
]
