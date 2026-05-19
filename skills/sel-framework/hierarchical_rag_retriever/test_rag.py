"""
Tests for hierarchical_rag_retriever skill
"""
import json
import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

os.environ["SEL_DATA_DIR"] = tempfile.mkdtemp()

from hierarchical_rag_retriever import (
    _time_decay, _regime_match_score, score_experience,
    retrieve, _load_cache, _save_cache,
    _winrate_for_strategy, REGIME_ADJACENCY,
)
from decision_snapshot import save_snapshot, update_snapshot, SNAPSHOT_DIR


def _wipe_dir(d: Path) -> None:
    """Recursively delete all files in a directory."""
    if not d.exists():
        return
    for p in d.rglob("*"):
        if p.is_file():
            p.unlink()


@pytest.fixture(autouse=True)
def wipe_all():
    _wipe_dir(SNAPSHOT_DIR)
    cache = SNAPSHOT_DIR.parent / "rag_cache.json"
    if cache.exists():
        cache.unlink()
    yield


def add_experience(symbol: str, pnl: float, result: str,
                   regime: str, strategy: str, days_ago: int = 5):
    saved = save_snapshot(
        symbol=symbol, action="buy", price=10.0,
        regime=regime, regime_confidence=0.8,
        strategy=strategy, reason="test",
    )
    past = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    update_snapshot(saved["snapshot_id"], {
        "pnl": pnl, "result": result, "created_at": past,
    })
    return saved["snapshot_id"]


class TestTimeDecay:
    def test_decay_half_life(self):
        assert _time_decay(0) == 1.0
        assert _time_decay(30) == pytest.approx(0.5, rel=0.01)
        assert _time_decay(60) == pytest.approx(0.25, rel=0.02)

    def test_decay_zero_days(self):
        assert _time_decay(0) == 1.0

    def test_decay_never_below_zero(self):
        assert _time_decay(1000) > 0.0


class TestRegimeMatch:
    def test_exact_match(self):
        assert _regime_match_score("trend_up", "trend_up") == 1.5

    def test_adjacent_regime(self):
        assert _regime_match_score("trend_up", "volatile") == 0.8

    def test_opposite_regime(self):
        assert _regime_match_score("trend_up", "sideways") == 0.3


class TestScoreExperience:
    def test_score_non_negative(self):
        exp = {
            "strategy": "test",
            "regime": "trend_up",
            "result": "win",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        all_snaps = [exp]
        score = score_experience(exp, "trend_up", "test", all_snaps, datetime.now(timezone.utc))
        assert score >= 0.0

    def test_same_regime_higher_score(self):
        now = datetime.now(timezone.utc)
        exp = {
            "strategy": "test", "regime": "trend_up", "result": "win",
            "created_at": now.isoformat(),
        }
        all_snaps = [exp]
        score_same = score_experience(exp, "trend_up", "test", all_snaps, now)
        score_diff = score_experience(exp, "sideways", "test", all_snaps, now)
        assert score_same > score_diff


class TestRetrieve:
    def test_empty_when_no_experiences(self):
        result = retrieve("trend_up", top_k=5)
        assert result["retrieved_experiences"] == []
        assert result["total_experiences"] == 0

    def test_returns_top_k(self):
        for i in range(10):
            add_experience(f"S{i}", 5.0, "win", "trend_up", "strat_a", days_ago=i)
        result = retrieve("trend_up", top_k=3)
        assert len(result["retrieved_experiences"]) <= 3

    def test_scores_sorted_descending(self):
        add_experience("S1", 5.0, "win", "trend_up", "strat_a", days_ago=1)
        add_experience("S2", 8.0, "win", "trend_up", "strat_a", days_ago=1)
        result = retrieve("trend_up", top_k=5)
        scores = [e["score"] for e in result["retrieved_experiences"]]
        assert scores == sorted(scores, reverse=True)

    def test_deduplicates_by_strategy_regime(self):
        add_experience("S1", 5.0, "win", "trend_up", "strat_a", days_ago=1)
        add_experience("S2", 8.0, "win", "trend_up", "strat_a", days_ago=2)
        result = retrieve("trend_up", top_k=5)
        # Same strategy+regime should be deduped (keep best)
        assert len(result["retrieved_experiences"]) <= 1
