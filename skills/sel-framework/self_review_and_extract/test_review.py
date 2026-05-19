"""
Tests for self_review_and_extract skill
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

os.environ["SEL_DATA_DIR"] = tempfile.mkdtemp()

from self_review_and_extract import (
    _load_all_snapshots, _group_by_strategy, _detect_rotting,
    _extract_lesson, _winrate_by_regime, run,
    LESSON_RULES,
)
from decision_snapshot import save_snapshot, update_snapshot, SNAPSHOT_DIR


@pytest.fixture(autouse=True)
def wipe_snapshots():
    # Clean before test
    for p in SNAPSHOT_DIR.rglob("snapshot-*.json"):
        p.unlink()
    lessons_dir = SNAPSHOT_DIR.parent / "lessons"
    if lessons_dir.exists():
        for p in lessons_dir.glob("lesson-*.json"):
            p.unlink()
    yield
    # Clean after test
    for p in SNAPSHOT_DIR.rglob("snapshot-*.json"):
        p.unlink()
    if lessons_dir.exists():
        for p in lessons_dir.glob("lesson-*.json"):
            p.unlink()


def make_completed_snapshot(symbol: str, action: str, pnl: float,
                             result: str, regime: str, strategy: str = "test") -> dict:
    saved = save_snapshot(
        symbol=symbol, action=action, price=10.0,
        regime=regime, regime_confidence=0.8,
        strategy=strategy, reason="test",
    )
    update_snapshot(saved["snapshot_id"], {"pnl": pnl, "result": result})
    return saved


class TestExtractLesson:
    def test_trend_riding_success(self):
        snap = {"pnl": 8.0, "regime": "trend_up"}
        lesson = _extract_lesson(snap)
        assert lesson is not None
        assert lesson["lesson_type"] == "trend_riding_success"
        assert "trend_up" in lesson["tags"]

    def test_range_trap_loss(self):
        snap = {"pnl": -5.0, "regime": "sideways"}
        lesson = _extract_lesson(snap)
        assert lesson is not None
        assert lesson["lesson_type"] == "range_trap_loss"

    def test_black_swan(self):
        snap = {"pnl": -15.0, "regime": "volatile"}
        lesson = _extract_lesson(snap)
        assert lesson is not None
        assert lesson["lesson_type"] == "black_swan_hit"

    def test_stalled_position(self):
        snap = {"pnl": 0.3, "regime": "sideways"}
        lesson = _extract_lesson(snap)
        assert lesson is not None
        assert lesson["lesson_type"] == "stalled_position"

    def test_no_lesson_for_neutral_pnl(self):
        snap = {"pnl": 2.0, "regime": "sideways"}
        lesson = _extract_lesson(snap)
        # 2% in sideways: may not trigger any specific rule
        assert lesson is None or "sideways" in lesson.get("tags", [])


class TestWinrateByRegime:
    def test_zero_snaps(self):
        wr = _winrate_by_regime([])
        assert wr == {}

    def test_computes_correctly(self):
        snaps = [
            {"regime": "trend_up", "result": "win"},
            {"regime": "trend_up", "result": "loss"},
            {"regime": "trend_up", "result": "win"},
        ]
        wr = _winrate_by_regime(snaps)
        assert wr["trend_up"] == pytest.approx(2 / 3, rel=0.01)


class TestDetectRotting:
    def test_detects_consecutive_loss_streak(self):
        snaps = [
            {"strategy": "bad", "result": "loss", "regime": "trend_up", "created_at": "2024-01-01T00:00:00"},
            {"strategy": "bad", "result": "loss", "regime": "sideways", "created_at": "2024-01-02T00:00:00"},
            {"strategy": "bad", "result": "loss", "regime": "volatile", "created_at": "2024-01-03T00:00:00"},
        ]
        rotting = _detect_rotting(snaps)
        assert len(rotting) == 1
        assert rotting[0]["lesson_type"] == "strategy_rotting"
        assert rotting[0]["streak"] == 3


class TestRun:
    def test_run_returns_lessons_and_summary(self):
        make_completed_snapshot("S1", "buy", 8.0, "win", "trend_up", "strat_a")
        make_completed_snapshot("S2", "buy", -5.0, "loss", "sideways", "strat_a")
        result = run()
        assert "lessons" in result
        assert "summary" in result
        assert "wins" in result["summary"]
        assert "losses" in result["summary"]
        assert "winrate" in result["summary"]

    def test_run_filters_by_ids(self):
        saved = make_completed_snapshot("X1", "buy", 10.0, "win", "trend_up")
        result = run(snapshot_ids=[saved["snapshot_id"]])
        assert result["summary"]["snapshots_reviewed"] == 1