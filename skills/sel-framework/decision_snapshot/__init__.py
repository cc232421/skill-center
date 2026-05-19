"""
decision_snapshot — Decision logging skill
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DATA_DIR = Path(os.environ.get("SEL_DATA_DIR", os.path.expanduser("~/.sel_data")))
SNAPSHOT_DIR = DATA_DIR / "snapshots"


def _ensure_dirs() -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _persist_snapshot(path: Path, data: dict) -> None:
    """Write snapshot data to disk."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _build_snapshot(
    snapshot_id: str,
    ts: str,
    symbol: str,
    action: str,
    price: float,
    regime: str,
    regime_confidence: float,
    strategy: str,
    reason: str,
    market: str,
    period: str,
    quantity: float,
    risk_ratio: float,
    entry_snapshot: Optional[dict],
    features: Optional[dict],
    pnl: Optional[float],
    result: Optional[str],
) -> dict:
    """Build the snapshot dict."""
    return {
        "id": snapshot_id,
        "symbol": symbol,
        "market": market,
        "period": period,
        "action": action,
        "price": float(price),
        "quantity": float(quantity),
        "regime": regime,
        "regime_confidence": float(regime_confidence),
        "strategy": strategy,
        "reason": reason,
        "features": features or {},
        "entry_snapshot": entry_snapshot or {},
        "risk_ratio": float(risk_ratio),
        "pnl": float(pnl) if pnl is not None else None,
        "result": result,
        "review_status": "pending",
        "created_at": ts,
        "updated_at": ts,
    }


def save_snapshot(
    symbol: str,
    action: str,
    price: float,
    regime: str,
    regime_confidence: float,
    strategy: str,
    reason: str,
    market: str = "A",
    period: str = "day",
    quantity: float = 0.0,
    risk_ratio: float = 0.0,
    entry_snapshot: Optional[dict] = None,
    features: Optional[dict] = None,
    timestamp: Optional[str] = None,
    pnl: Optional[float] = None,
    result: Optional[str] = None,
) -> dict:
    """
    Save a decision snapshot to disk.

    Returns:
        {"snapshot_id": str, "persisted_path": str, "status": "saved"}
    """
    _ensure_dirs()

    ts = timestamp or _now_iso()
    month_dir = SNAPSHOT_DIR / ts[:7]
    month_dir.mkdir(parents=True, exist_ok=True)

    snapshot_id = str(uuid.uuid4())
    path = month_dir / f"snapshot-{snapshot_id}.json"

    data = _build_snapshot(
        snapshot_id, ts, symbol, action, price, regime, regime_confidence,
        strategy, reason, market, period, quantity, risk_ratio,
        entry_snapshot, features, pnl, result,
    )

    _persist_snapshot(path, data)

    return {
        "snapshot_id": snapshot_id,
        "persisted_path": str(path),
        "status": "saved",
    }


def update_snapshot(snapshot_id: str, updates: dict) -> bool:
    """Update fields on an existing snapshot (e.g., fill in pnl after exit)."""
    # Find the snapshot file
    for month_dir in SNAPSHOT_DIR.iterdir():
        if not month_dir.is_dir():
            continue
        path = month_dir / f"snapshot-{snapshot_id}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data.update(updates)
            data["updated_at"] = _now_iso()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
    return False


def load_snapshot(snapshot_id: str) -> Optional[dict]:
    """Load a snapshot by ID."""
    for month_dir in SNAPSHOT_DIR.iterdir():
        if not month_dir.is_dir():
            continue
        path = month_dir / f"snapshot-{snapshot_id}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return None


def list_pending_snapshots(strategy: Optional[str] = None, limit: Optional[int] = 100) -> list[dict]:
    """List snapshots with review_status=pending. Pass limit=None for no cap."""
    results = []
    for month_dir in SNAPSHOT_DIR.iterdir():
        if not month_dir.is_dir():
            continue
        for path in sorted(month_dir.glob("snapshot-*.json"), reverse=True):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("review_status") != "pending":
                continue
            if strategy and data.get("strategy") != strategy:
                continue
            results.append({**data, "_path": str(path)})
            if limit is not None and len(results) >= limit:
                break
        if limit is not None and len(results) >= limit:
            break
    return results


def count_pending(strategy: Optional[str] = None) -> int:
    """Count pending snapshots (uncapped)."""
    return len(list_pending_snapshots(strategy=strategy, limit=None))
