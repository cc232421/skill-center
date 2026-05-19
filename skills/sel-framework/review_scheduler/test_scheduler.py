"""
Tests for review_scheduler skill
"""
import json
import os
import tempfile
import pytest
from unittest.mock import patch

os.environ["SEL_DATA_DIR"] = tempfile.mkdtemp()
# Reset state file
_state = tempfile.mkdtemp()
os.environ["SEL_DATA_DIR"] = _state

from review_scheduler import (
    detect_frequency, should_trigger_review, trigger_review,
    FREQUENCY_MAP, _load_state, _save_state, STATE_FILE,
)


class TestDetectFrequency:
    def test_daytrade(self):
        assert detect_frequency("daytrade_strategy") == "daytrade"
        assert detect_frequency("scalp_5m") == "daytrade"

    def test_intraday(self):
        assert detect_frequency("intraday_60m") == "intraday"

    def test_swing(self):
        assert detect_frequency("chanlun_swing") == "swing"

    def test_longterm(self):
        assert detect_frequency("longterm_monthly") == "longterm"

    def test_default(self):
        assert detect_frequency("unknown_strategy_xyz") == "position"


class TestShouldTriggerReview:
    def test_override_true(self):
        assert should_trigger_review(override=True) is True

    def test_no_pending_no_trigger(self):
        assert should_trigger_review(strategy_name="daytrade",
                                     pending_count=0, override=False) is False

    def test_count_threshold_triggers(self):
        # daytrade needs 5+
        assert should_trigger_review(strategy_name="daytrade",
                                     pending_count=5, override=False) is True
        # swing needs 1+
        assert should_trigger_review(strategy_name="swing",
                                     pending_count=1, override=False) is True


class TestTriggerReview:
    def test_returns_correct_fields(self):
        result = trigger_review("test_strategy")
        assert "next_review_at" in result
        assert "pending_reviews" in result
        assert result["triggered"] is True
        assert "schedule_id" in result

    def test_frequency_daily(self):
        result = trigger_review("daytrade")
        assert result["frequency"] == "daytrade"
