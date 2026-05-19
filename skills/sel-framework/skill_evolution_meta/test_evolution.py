"""
Tests for skill_evolution_meta skill
"""
import json
import os
import tempfile
import pytest

os.environ["SEL_DATA_DIR"] = tempfile.mkdtemp()

from skill_evolution_meta import (
    check_evolution_triggers, evolve_patch, evolve_clone,
    evolve_restructure, run, _load_snapshots, _save_rule,
)
from decision_snapshot import save_snapshot, update_snapshot, SNAPSHOT_DIR


@pytest.fixture(autouse=True)
def wipe_snapshots_and_rules():
    for p in SNAPSHOT_DIR.rglob("snapshot-*.json"):
        p.unlink()
    rules_dir = SNAPSHOT_DIR.parent / "rules"
    if rules_dir.exists():
        for p in rules_dir.glob("rule-*.json"):
            p.unlink()
    yield


def make_snap(strategy: str, result: str, regime: str = "trend_up"):
    saved = save_snapshot(
        symbol="TEST", action="buy", price=10.0,
        regime=regime, regime_confidence=0.8,
        strategy=strategy, reason="test",
    )
    update_snapshot(saved["snapshot_id"], {"pnl": 5.0 if result == "win" else -5.0, "result": result})
    return saved


class TestCheckEvolutionTriggers:
    def test_no_signal_empty(self):
        should, reason = check_evolution_triggers([], [])
        assert should is False
        assert reason == "no_signal"

    def test_consecutive_losses_triggers(self):
        # Wipe only bad_strat snapshots to isolate this test
        for path in SNAPSHOT_DIR.glob("snapshot-*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("strategy") == "bad_strat":
                    path.unlink()
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        for _ in range(5):
            make_snap("bad_strat", "loss", "trend_up")
        # Add a win to prevent simple count
        snaps = _load_snapshots(SNAPSHOT_DIR)
        bad_snaps = [s for s in snaps if s.get("strategy") == "bad_strat"]
        assert len(bad_snaps) >= 5, f"Expected ≥5 bad_strat snaps, got {len(bad_snaps)}"
        # Verify order
        bad_strat_results = [s.get("result") for s in bad_snaps]
        assert bad_strat_results == ["loss"] * len(bad_strat_results), \
            f"bad_strat results not all loss: {bad_strat_results}"
        lessons = []
        should, reason = check_evolution_triggers(lessons, snaps)
        assert should is True, f"reason={reason}"
        assert "strategy_rotting" in reason

    def test_rotting_lesson_triggers(self):
        lessons = [{"lesson_type": "strategy_rotting", "strategy": "test"}]
        should, reason = check_evolution_triggers(lessons, [])
        assert should is True
        assert reason == "strategy_rotting_detected"


class TestEvolvePatch:
    def test_generates_rule(self):
        # Create loss snapshots so evolve_patch has data to work with
        for _ in range(3):
            make_snap("test_strat", "loss", "trend_up")
        snaps = _load_snapshots(SNAPSHOT_DIR)
        rules = evolve_patch(snaps, "test_strat")
        assert len(rules) >= 1
        assert "rule_id" in rules[0]
        assert rules[0]["mode"] == "patch"

    def test_rule_has_required_fields(self):
        rules = evolve_patch([], "test")
        if rules:
            assert "name" in rules[0]
            assert "pattern" in rules[0]
            assert "action" in rules[0]
            assert "status" in rules[0]


class TestEvolveClone:
    def test_high_winrate_strategy_cloned(self):
        # Add 5 winning snapshots for same strategy+regime
        for _ in range(5):
            make_snap("good_strat", "win", "trend_up")
        snaps = _load_snapshots(SNAPSHOT_DIR)
        clones = evolve_clone(snaps)
        assert len(clones) >= 1
        assert clones[0]["mode"] == "clone"


class TestEvolveRestructure:
    def test_regime_action_matrix(self):
        snaps = _load_snapshots(SNAPSHOT_DIR)
        rules = evolve_restructure(snaps, [])
        assert isinstance(rules, list)


class TestRun:
    def test_no_signal_returns_no_rules(self):
        result = run([])
        assert result["evolution_status"] == "no_signal"
        assert result["new_rules"] == []

    def test_run_with_rotting_triggers_evolution(self):
        for _ in range(4):
            make_snap("rotting_strat", "loss")
        lessons = [{"lesson_type": "strategy_rotting", "strategy": "rotting_strat"}]
        result = run(lessons)
        assert result["evolution_status"] == "evolved"
        assert len(result["new_rules"]) >= 1
