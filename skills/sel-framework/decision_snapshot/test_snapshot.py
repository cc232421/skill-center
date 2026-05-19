"""
Tests for decision_snapshot skill
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

# Patch SEL_DATA_DIR to temp dir
os.environ["SEL_DATA_DIR"] = tempfile.mkdtemp()

from decision_snapshot import (
    save_snapshot, update_snapshot, load_snapshot,
    list_pending_snapshots, count_pending, SNAPSHOT_DIR,
)


class TestSaveSnapshot:
    def test_save_returns_id_and_path(self):
        result = save_snapshot(
            symbol="000001",
            action="buy",
            price=12.50,
            regime="trend_up",
            regime_confidence=0.82,
            strategy="chanlun_breakout",
            reason="缠论1买",
        )
        assert "snapshot_id" in result
        assert "persisted_path" in result
        assert result["status"] == "saved"
        assert len(result["snapshot_id"]) == 36  # UUID length

    def test_saved_file_is_valid_json(self):
        result = save_snapshot(
            symbol="AAPL", action="sell", price=180.0,
            regime="sideways", regime_confidence=0.6,
            strategy="default", reason="test",
        )
        with open(result["persisted_path"]) as f:
            data = json.load(f)
        assert data["symbol"] == "AAPL"
        assert data["action"] == "sell"
        assert data["review_status"] == "pending"

    def test_pnl_not_set_initially(self):
        result = save_snapshot(
            symbol="000001", action="buy", price=10.0,
            regime="trend_up", regime_confidence=0.8,
            strategy="test", reason="test",
        )
        snap = load_snapshot(result["snapshot_id"])
        assert snap["pnl"] is None
        assert snap["result"] is None


class TestUpdateSnapshot:
    def test_update_fills_pnl(self):
        saved = save_snapshot(
            symbol="000001", action="buy", price=10.0,
            regime="trend_up", regime_confidence=0.8,
            strategy="test", reason="test",
        )
        updated = update_snapshot(saved["snapshot_id"], {
            "pnl": 5.5,
            "result": "win",
        })
        assert updated is True
        snap = load_snapshot(saved["snapshot_id"])
        assert snap["pnl"] == 5.5
        assert snap["result"] == "win"
        assert snap["review_status"] == "pending"  # unchanged unless specified

    def test_update_nonexistent_returns_false(self):
        assert update_snapshot("fake-id-123", {"pnl": 1.0}) is False


class TestLoadSnapshot:
    def test_load_existing(self):
        saved = save_snapshot(
            symbol="TEST", action="hold", price=5.0,
            regime="sideways", regime_confidence=0.5,
            strategy="test", reason="test",
        )
        snap = load_snapshot(saved["snapshot_id"])
        assert snap is not None
        assert snap["symbol"] == "TEST"


class TestListPending:
    def test_pending_count(self):
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        save_snapshot(symbol="P1", action="buy", price=1.0,
                      regime="trend_up", regime_confidence=0.8,
                      strategy="test", reason="t")
        save_snapshot(symbol="P2", action="sell", price=2.0,
                      regime="sideways", regime_confidence=0.6,
                      strategy="test", reason="t")
        assert count_pending() >= 2

    def test_strategy_filter(self):
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        save_snapshot(symbol="S1", action="buy", price=1.0,
                      regime="trend_up", regime_confidence=0.8,
                      strategy="strat_a", reason="t")
        pending = list_pending_snapshots(strategy="strat_a")
        assert all(p.get("strategy") == "strat_a" for p in pending)
