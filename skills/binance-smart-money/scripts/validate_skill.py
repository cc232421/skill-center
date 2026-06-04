#!/usr/bin/env python3
"""Offline structural validation for the binance-smart-money OpenClaw skill."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REQUIRED_FILES = [
    "SKILL.md",
    "skill.json",
    "references/project-analysis.md",
    "references/validation-plan.md",
    "fixtures/sample_snapshot.json",
    "scripts/fixture_report.py",
    "scripts/smoke_test.sh",
]

REQUIRED_SKILL_TEXT = [
    "Safety Rules",
    "offline-fixture",
    "live-smoke",
    "Retry-After",
    "Do not say",
]


def fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_skill.py <skill-dir>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        return fail(f"skill dir does not exist: {root}")

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            return fail(f"missing required file: {rel}")

    skill_md = (root / "SKILL.md").read_text(encoding="utf-8")
    for needle in REQUIRED_SKILL_TEXT:
        if needle not in skill_md:
            return fail(f"SKILL.md missing required text: {needle}")

    meta = json.loads((root / "skill.json").read_text(encoding="utf-8"))
    if meta.get("name") != "binance-smart-money":
        return fail("skill.json name must be binance-smart-money")
    if "OpenClaw" not in meta.get("compatibility", ""):
        return fail("skill.json compatibility must mention OpenClaw")
    if not meta.get("triggers"):
        return fail("skill.json triggers must not be empty")

    fixture = json.loads((root / "fixtures/sample_snapshot.json").read_text(encoding="utf-8"))
    for key in ("symbol", "smart_money", "open_interest"):
        if key not in fixture:
            return fail(f"fixture missing key: {key}")

    cmd = [
        sys.executable,
        str(root / "scripts/fixture_report.py"),
        str(root / "fixtures/sample_snapshot.json"),
    ]
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return fail("fixture_report.py failed")

    output = result.stdout
    for needle in ("Binance Smart Money Report", "Smart Money notional", "not a trade instruction"):
        if needle not in output:
            return fail(f"fixture report missing expected text: {needle}")
    forbidden = ("buy now", "sell now", "long now", "short now", "guaranteed")
    lowered = output.lower()
    for phrase in forbidden:
        if phrase in lowered:
            return fail(f"fixture report contains forbidden phrase: {phrase}")

    print("PASS: binance-smart-money skill structure and fixture report validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

