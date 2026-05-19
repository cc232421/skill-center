"""
Tests for observability_hub skill
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

os.environ["SEL_DATA_DIR"] = tempfile.mkdtemp()
os.environ.pop("SEL_ALERT_WEBHOOK_URL", None)  # Disable webhook

from observability_hub import (
    log, get_recent_logs, metrics, grafana_metrics_text,
    _persist_log, _current_metrics, ALERT_RULES,
)


class TestLog:
    def test_log_returns_fields(self):
        result = log(
            event_type="skill_run",
            payload={"skill": "test", "status": "ok"},
            severity="info",
            skill="test_skill",
            message="Test event",
        )
        assert "logged" in result
        assert "alerted" in result
        assert result["logged"] is True

    def test_log_persists_to_disk(self):
        log(event_type="test_persist", payload={"key": "value"},
            severity="info", skill="test", message="persist test")
        recent = get_recent_logs(n=10)
        assert any(e["event_type"] == "test_persist" for e in recent)

    def test_black_swan_triggers_alert(self):
        result = log(
            event_type="regime",
            payload={"regime_label": "black_swan"},
            severity="critical",
            skill="perception",
        )
        assert result["alerted"] is True

    def test_approved_sandbox_logs_info(self):
        result = log(
            event_type="sandbox",
            payload={"approved": True, "rule_id": "r1", "sharpe_ratio": 1.5},
            severity="info",
            skill="sandbox",
        )
        assert result["logged"] is True

    def test_rejected_evolution_warns(self):
        result = log(
            event_type="evolution",
            payload={"approved": False, "rule_id": "bad-rule"},
            severity="warning",
            skill="evolution",
        )
        assert result["logged"] is True


class TestGetRecentLogs:
    def test_returns_list(self):
        result = get_recent_logs(n=5)
        assert isinstance(result, list)


class TestMetrics:
    def test_metrics_has_required_keys(self):
        m = metrics()
        assert "winrate" in m
        assert "experience_count" in m
        assert "active_rules" in m
        assert "timestamp" in m

    def test_grafana_text_format(self):
        text = grafana_metrics_text()
        assert "sel_framework_winrate" in text
        assert "sel_framework_experience_count" in text
        assert "sel_framework_active_rules" in text
        assert "# HELP" in text
        assert "# TYPE" in text


class TestAlertRules:
    def test_alert_rules_defined(self):
        assert len(ALERT_RULES) >= 4
        event_types = [r["event_type"] for r in ALERT_RULES]
        assert "regime" in event_types
        assert "evolution" in event_types
        assert "sandbox" in event_types
