---
name: binance-smart-money
description: |
  Binance Smart Money tracker workflow for OpenClaw agents. Use this when the user asks to analyze Binance Smart Signal, whale positioning, long/short profit ratios, futures open interest, Binance smart money dashboards, or wants to deploy/test the 0xBennie/binance-smart-money-tracker project. This skill turns the tracker into a safe agent workflow: install the Node/SQLite tool, run low-rate data pulls, inspect dashboard/API output, interpret whale signals, and validate with offline fixtures before any live Binance calls. Do not use for placing trades.
allowed-tools: Bash, Read, Write, Edit
compatibility: "Claude Code >=1.0, OpenClaw, OpenCode"
metadata:
  openclaw:
    emoji: "🐋"
    trigger-phrases:
      - "分析 Binance smart money"
      - "巨鲸持仓"
      - "Binance Smart Signal"
      - "smart money tracker"
      - "部署 Binance 巨鲸监控"
      - "验证 binance-smart-money-tracker"
---

# Binance Smart Money

## Purpose

Use this skill to operate and explain the Binance Smart Money tracker from:

`https://github.com/0xBennie/binance-smart-money-tracker`

The upstream project is a TypeScript/Node tool that pulls Binance Smart Signal whale overview data from Binance web `bapi`, supplements it with public `fapi` top-trader and open-interest data, stores snapshots in SQLite, and serves an Express dashboard.

The skill's job is to help an agent run the workflow safely, produce useful market-structure reports, and verify behavior before live calls. It is not a trading bot.

## Safety Rules

1. Never place trades, submit orders, or present output as financial advice.
2. Default to offline fixture validation first.
3. Before live Binance calls, state expected call volume and cadence.
4. For live smoke tests, use `SMART_MONEY_POOL_MAX=1` unless the user asks for broader coverage.
5. If Binance returns `403`, `418`, or `429`, stop live requests and report the block state.
6. Do not bypass `Retry-After`, circuit breakers, shard spacing, or cache behavior.
7. Treat the Smart Signal endpoint as undocumented and unstable; verify current behavior when accuracy matters.

## Upstream Facts

Read `references/project-analysis.md` when you need the project map, risks, and adaptation rationale.

Key facts:

- Runtime: Node >=20, TypeScript ESM, `tsx`, SQLite via `better-sqlite3`, Express dashboard.
- Library entry: `src/index.ts`.
- Cron entries: `smart-money-tick.ts`, `top-trader-tick.ts`, `oi-tick.ts`.
- Dashboard: `src/scripts/smart-money-dashboard.ts`, default port `3001`.
- Storage: `data/snapshots.db`, 30-day retention, WAL mode.
- Protection: preflight ping, weight budget, `Retry-After`, jittered spacing, exponential backoff, process circuit breaker, memory cache.

## Workflow

### 1. Clarify Mode

Choose one mode from the user's request:

| Mode | Use when | Network |
|---|---|---|
| `offline-fixture` | Validate the skill, generate sample report, test formatting | No |
| `repo-typecheck` | Verify upstream project installs and compiles | GitHub/npm only |
| `live-smoke` | Pull 1-3 symbols and inspect SQLite/dashboard | Binance |
| `deploy-plan` | User wants pm2/cron/sharding production setup | Optional |
| `market-report` | User asks for current whale/OI interpretation | Binance unless they provide data |

If the user did not specify, start with `offline-fixture`, then offer the next mode.

### 2. Install Or Locate Upstream

If the repository is already present, use it. Otherwise clone it into a work directory:

```bash
git clone --depth 1 https://github.com/0xBennie/binance-smart-money-tracker.git /tmp/binance-smart-money-tracker
cd /tmp/binance-smart-money-tracker
npm install
npm run typecheck
```

Use `env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u all_proxy` if a broken local proxy blocks GitHub.

### 3. Offline Validation

Run the bundled validation first:

```bash
python3 skills/binance-smart-money/scripts/validate_skill.py skills/binance-smart-money
python3 skills/binance-smart-money/scripts/fixture_report.py \
  skills/binance-smart-money/fixtures/sample_snapshot.json
```

Expected result:

- `validate_skill.py` prints `PASS`.
- `fixture_report.py` prints a Markdown report with long/short profit percentages, whale average-entry spread, Smart Money notional, and OI share.

### 4. Live Smoke Test

Only run after the user accepts live Binance calls:

```bash
cd /tmp/binance-smart-money-tracker
SMART_MONEY_POOL_MAX=1 npm run smart-money:tick
OI_POOL_MAX=1 npm run oi:tick
PORT=3001 npm run dashboard
```

Then verify:

```bash
sqlite3 data/snapshots.db "select count(*) from ob_smart_money_snapshots;"
curl -fsS http://127.0.0.1:3001/health
curl -fsS http://127.0.0.1:3001/api/snapshots | head -c 500
```

Bundled helper:

```bash
bash skills/binance-smart-money/scripts/smoke_test.sh /tmp/binance-smart-money-tracker
```

### 5. Interpret Data

When producing a report, include:

- `symbol`, snapshot time, data freshness.
- Long vs short trader count and long/short ratio.
- Long/short in-profit percentages for all traders and whales.
- Whale average-entry spread: `(shortWhalesAvgEntryPrice - longWhalesAvgEntryPrice) / longWhalesAvgEntryPrice`.
- Smart Money notional: `longTradersQty * longTradersAvgEntryPrice + shortTradersQty * shortTradersAvgEntryPrice`.
- Smart Money OI share when OI exists.
- OI 5m/15m/1h/4h velocity, preserving `null` as missing data.
- A bounded interpretation: positioning pressure, squeeze risk, data gaps, and what would invalidate the read.

Do not say "buy", "sell", "long now", or "short now". Use observational language like "longs are currently more profitable" or "shorts entered higher on average".

## Output Template

```markdown
# Binance Smart Money Report

## Scope
- Mode:
- Source:
- Snapshot:

## Key Metrics
| Metric | Value | Interpretation |
|---|---:|---|

## Read

## Risks And Data Gaps

## Verification
```

## Validation

Read `references/validation-plan.md` for the complete test plan.

Minimum acceptance:

1. Skill metadata validates.
2. Fixture report runs without network.
3. Upstream `npm run typecheck` passes.
4. Optional live smoke writes at least one smart-money row and dashboard `/health` returns OK.

