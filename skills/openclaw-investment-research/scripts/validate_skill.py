#!/usr/bin/env python3
"""Validate the openclaw-investment-research skill structure."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FILES = [
    "SKILL.md",
    "skill.json",
    "references/templates.md",
    "references/source-and-compliance.md",
    "references/method-library.md",
    "references/audit-and-scoring.md",
    "evals/evals.json",
]

REQUIRED_SKILL_PHRASES = [
    "观点先行",
    "来源分层",
    "估值锚",
    "反证优先",
    "不提供个性化投资建议",
    "一句话投资判断",
    "认知差",
    "盈利模型",
    "估值方法",
    "质量自检",
]

REQUIRED_TEMPLATE_PHRASES = [
    "深度报告",
    "短评",
    "投资备忘录",
    "SOTP",
    "DCF",
    "情景分析",
    "风险与反证",
]

REQUIRED_AUDIT_PHRASES = [
    "事实审计",
    "逻辑审计",
    "估值审计",
    "风险审计",
    "100 分评分表",
]

REQUIRED_METHOD_PHRASES = [
    "Variant Perception",
    "利润结构迁移",
    "产业瓶颈",
    "ROIC-WACC",
    "现金流质量",
    "估值锚迁移",
]

REQUIRED_OUTPUT_MODULES = [
    "一句话投资判断",
    "核心逻辑三点",
    "市场认知差",
    "业务与产业链拆解",
    "盈利模型关键变量",
    "估值框架",
    "催化剂",
    "风险与反证",
    "后续跟踪指标",
    "质量自检与免责声明",
]

REQUIRED_DEEP_REPORT_SECTIONS = [
    "标题",
    "核心摘要",
    "公司到底卖什么",
    "产业链位置",
    "业务分部拆解",
    "盈利模型变化",
    "行业供需与竞争格局",
    "同业比较",
    "结论与免责声明",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    root = Path(__file__).resolve().parents[1]

    for rel in REQUIRED_FILES:
        require((root / rel).is_file(), f"missing {rel}")

    skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
    template_text = (root / "references/templates.md").read_text(encoding="utf-8")
    audit_text = (root / "references/audit-and-scoring.md").read_text(encoding="utf-8")
    compliance_text = (root / "references/source-and-compliance.md").read_text(encoding="utf-8")
    method_text = (root / "references/method-library.md").read_text(encoding="utf-8")

    for phrase in REQUIRED_SKILL_PHRASES:
        require(phrase in skill_text, f"SKILL.md missing phrase: {phrase}")
    for phrase in REQUIRED_TEMPLATE_PHRASES:
        require(phrase in template_text, f"templates.md missing phrase: {phrase}")
    for phrase in REQUIRED_AUDIT_PHRASES:
        require(phrase in audit_text, f"audit-and-scoring.md missing phrase: {phrase}")
    for phrase in REQUIRED_METHOD_PHRASES:
        require(phrase in method_text, f"method-library.md missing phrase: {phrase}")
    for phrase in REQUIRED_OUTPUT_MODULES:
        require(phrase in skill_text, f"default output missing module: {phrase}")
    for phrase in REQUIRED_DEEP_REPORT_SECTIONS:
        require(phrase in template_text, f"deep report missing section: {phrase}")

    require("A | 公司公告" in compliance_text, "source trust layer A missing")
    require("F | 用户推测" in compliance_text, "source trust layer F missing")
    require("免责声明" in compliance_text, "disclaimer missing")
    require("不构成任何投资建议" in compliance_text, "investment advice disclaimer missing")

    manifest = json.loads((root / "skill.json").read_text(encoding="utf-8"))
    require(manifest["name"] == "openclaw-investment-research", "manifest name mismatch")
    require(manifest["entry"] == "SKILL.md", "manifest entry mismatch")
    require("finance" in manifest["category"], "manifest category mismatch")

    evals = json.loads((root / "evals/evals.json").read_text(encoding="utf-8"))
    require(evals["skill_name"] == "openclaw-investment-research", "eval skill_name mismatch")
    require(len(evals["evals"]) >= 4, "need at least four evals")

    print("PASS openclaw-investment-research validation")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
