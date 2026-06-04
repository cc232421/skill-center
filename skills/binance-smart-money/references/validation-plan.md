# Validation Plan

## Test Matrix

| Test | Script | Network | Pass Criteria |
|---|---|---:|---|
| Skill structure | `scripts/validate_skill.py` | No | Metadata, required references, fixtures, and scripts exist |
| Fixture interpretation | `scripts/fixture_report.py fixtures/sample_snapshot.json` | No | Markdown report contains required metrics and no direct trade instruction |
| Upstream typecheck | `npm run typecheck` in upstream repo | npm/GitHub only | TypeScript exits 0 |
| Live smart-money smoke | `scripts/smoke_test.sh <repo>` | Binance | One limited smart-money run exits 0 and SQLite has rows |
| Dashboard smoke | `scripts/smoke_test.sh <repo>` | Localhost | `/health` returns JSON and `/api/snapshots` responds |

## Offline Commands

Run from the skill-center repository root:

```bash
python3 skills/binance-smart-money/scripts/validate_skill.py skills/binance-smart-money
python3 skills/binance-smart-money/scripts/fixture_report.py \
  skills/binance-smart-money/fixtures/sample_snapshot.json
```

## Upstream Typecheck

```bash
git clone --depth 1 https://github.com/0xBennie/binance-smart-money-tracker.git /tmp/binance-smart-money-tracker
cd /tmp/binance-smart-money-tracker
npm install
npm run typecheck
```

If a broken local proxy exists:

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u all_proxy \
  git clone --depth 1 https://github.com/0xBennie/binance-smart-money-tracker.git /tmp/binance-smart-money-tracker
```

## Live Smoke Test

Live smoke test calls Binance. Use only after the user accepts that network activity.

```bash
bash skills/binance-smart-money/scripts/smoke_test.sh /tmp/binance-smart-money-tracker
```

The smoke test intentionally uses tiny pool caps:

- `SMART_MONEY_POOL_MAX=1`
- `TOP_TRADER_POOL_MAX=1`
- `OI_POOL_MAX=1`

## Manual Checks

After a live run:

```bash
sqlite3 /tmp/binance-smart-money-tracker/data/snapshots.db \
  "select symbol, datetime(ts/1000,'unixepoch') from ob_smart_money_snapshots order by ts desc limit 5;"
curl -fsS http://127.0.0.1:3001/health
curl -fsS http://127.0.0.1:3001/api/snapshots
```

## Failure Handling

- `403`: stop. Report probable WAF block and wait/change IP.
- `418` or `429`: stop. Honor `Retry-After`.
- Empty SQLite rows: inspect stdout for preflight failure or endpoint schema drift.
- `better-sqlite3` install failure: verify Node >=20 and native build toolchain.
- Dashboard empty: confirm tick scripts ran from same cwd as dashboard.

