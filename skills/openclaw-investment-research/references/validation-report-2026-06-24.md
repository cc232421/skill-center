# OpenClaw Investment Research Test & Validation Report

Generated: 2026-06-24

## Scope

Validated `skills/openclaw-investment-research` as a Chinese investment research production and audit skill. The implementation is instruction-first: it provides workflow, templates, source credibility rules, compliance guardrails, method library, audit rubric, eval prompts, and a structure validator.

## Commands Run

```bash
python3 -m py_compile skills/openclaw-investment-research/scripts/validate_skill.py
python3 skills/openclaw-investment-research/scripts/validate_skill.py
```

## Result

- Python syntax validation exited 0.
- Skill structure validation printed `PASS openclaw-investment-research validation`.

## Test Matrix

| Test | Result | Evidence |
|---|---|
| File structure | PASS | Required files exist: `SKILL.md`, `skill.json`, references, evals, validator |
| Skill manifest | PASS | `skill.json` name is `openclaw-investment-research`, entry is `SKILL.md`, category is finance |
| Trigger metadata | PASS | Description and triggers cover company analysis, research report, SOTP, DCF, memo, report audit |
| Core principles | PASS | `观点先行`, `来源分层`, `估值锚`, `反证优先`, compliance boundary present |
| Default output template | PASS | 10 default modules covered |
| Deep report template | PASS | 16-section deep report structure covered |
| Short note and memo templates | PASS | Short comment and investment memo templates covered |
| Source credibility layering | PASS | A-F source hierarchy covered |
| Compliance | PASS | Default disclaimer and no personalized advice boundary covered |
| Valuation selector | PASS | Company-type valuation selector covered in `SKILL.md` |
| SOTP template | PASS | Segment, assumption, method, multiple/NAV, value contribution, confidence covered |
| DCF template | PASS | Revenue growth, EBIT margin, tax, D&A, CapEx, working capital, FCF, WACC, terminal growth, sensitivity covered |
| Scenario analysis | PASS | Bear/base/bull table covered |
| Catalyst analysis | PASS | Short/mid/long catalyst table covered |
| Risk and falsification | PASS | Risk impact path, monitoring indicator, severity, falsification indicators covered |
| Method library | PASS | Variant Perception, profit migration, bottleneck, ROIC-WACC, cash-flow quality, valuation-anchor migration covered |
| Audit mechanism | PASS | Fact, logic, valuation, risk audit covered |
| Quality scoring | PASS | 100-point scoring rubric covered |
| Eval prompts | PASS | Four eval prompts cover default report, memo rewrite, SOTP, report audit |

## Requirement Coverage

| Requirement Area | Coverage |
|---|---|
| Skill name and positioning | PASS |
| Trigger scenarios | PASS |
| Input types | PASS |
| Data credibility layers | PASS |
| Standard output modules | PASS |
| Deep report / short note / memo formats | PASS |
| Variant Perception framework | PASS |
| Profit structure migration | PASS |
| Industrial bottleneck analysis | PASS |
| ROIC-WACC analysis | PASS |
| Cash-flow quality analysis | PASS |
| Valuation-anchor migration | PASS |
| Output audit mechanism | PASS |
| 100-point quality score | PASS |
| Writing style | PASS |
| Compliance and disclaimer | PASS |

## Known Limitations

- This skill does not fetch real-time market data by itself.
- It does not include a valuation calculator; it guides valuation framing and audit.
- It does not output buy/sell recommendations by design.
- No live LLM eval harness was run in this validation. The included eval prompts are ready for a skill-creator benchmark loop, but this report validates static structure and instruction coverage only.

## Status

PASS with one deliberate scope limit: this is a report-production and audit skill, not a data-fetching or valuation-calculation engine.
