# Project Analysis: 0xBennie/binance-smart-money-tracker

Analysis date: 2026-06-04

Inspected commit: `efcdc3bdfe0aff2283e59df83890a798d46a2f46`

## What The Project Does

The project is a production-oriented TypeScript scraper for Binance Futures Smart Signal. It pulls a Binance web `bapi` endpoint:

`https://www.binance.com/bapi/futures/v1/public/future/smart-money/signal/overview?symbol=BTCUSDT`

It captures whale fields not exposed by public `fapi`, including whale average entry prices and in-profit trader/whale counts. It enriches that with public `fapi/futures/data` endpoints for top-trader ratios, taker buy/sell ratio, and open-interest history.

## Architecture

| Area | File | Notes |
|---|---|---|
| Public library | `src/index.ts` | Re-exports client, formatter, rate-limit, storage APIs |
| Smart Signal client | `src/binance-smart-money.ts` | Calls undocumented `bapi`, parses 17 whale fields |
| Top trader client | `src/binance-top-trader.ts` | Calls account/position/taker ratios |
| Open interest client | `src/binance-open-interest.ts` | Calls `openInterestHist`, computes 5m/15m/1h/4h velocity |
| Rate-limit guard | `src/binance-rate-limit.ts` | Retry-After, weight budget, circuit breaker, keep-alive axios |
| Storage | `src/storage.ts` | SQLite WAL, 3 tables, 30-day cleanup |
| Dashboard | `src/scripts/smart-money-dashboard.ts` | Express SSR dashboard and JSON API |
| Cron scripts | `src/scripts/*-tick.ts` | Batch pulls with pool cap and sharding env vars |

## Runtime Requirements

- Node >=20, upstream `.nvmrc` suggests Node 22.
- `npm install` builds native `better-sqlite3`.
- SQLite file defaults to `data/snapshots.db` relative to current working directory.
- Live data requires Binance endpoints reachable from the host IP.

## Data Model

Smart Money table:

- `ob_smart_money_snapshots`
- Primary key: `(symbol, ts)`
- Important fields: long/short trader counts, quantities, average entries, whale counts, whale quantities, whale average entries, in-profit counts.

Top Trader table:

- `ob_top_trader_snapshots`
- Primary key: `(symbol, ts, period)`
- Important fields: top-account ratio, top-position ratio, taker buy/sell ratio.

Open Interest table:

- `ob_oi_snapshots`
- Primary key: `(symbol, ts)`
- Important fields: `oi_now_usd`, `oi_now_coins`, nullable OI change columns.

## Strengths

- Uses serial batch pulls with spacing and jitter instead of burst requests.
- Honors real `Retry-After` values.
- Tracks `X-MBX-USED-WEIGHT-1M` for public fapi calls.
- Preflights `fapi/v1/ping` before cron work.
- Uses a process-wide circuit breaker.
- Uses keep-alive HTTP agents to reduce handshake churn.
- Treats missing OI history as `null`, not false zero.
- Derives Smart Money notional from quantity times average entry instead of Binance's ambiguous `totalPositions`.

## Risks And Constraints

- Smart Signal `bapi` is undocumented and can change without notice.
- Binance WAF behavior depends on IP, region, cadence, and concurrent processes.
- The circuit breaker is process-local; independent cron processes need preflight and staggering.
- No formal test suite exists upstream beyond TypeScript typechecking.
- Dashboard reads SQLite relative to process cwd; wrong cwd means wrong DB path.
- The dashboard HTML includes Chinese labels; report agents should preserve meaning and avoid mistranslation.
- Data is observational and should not be turned into direct trading instructions.

## OpenClaw Skill Adaptation

The best OpenClaw skill shape is a workflow skill with bundled scripts, not a direct code fork:

- Keep upstream as the source of truth and install it on demand.
- Put safety gates in the skill instructions.
- Use offline fixtures to validate interpretation logic.
- Use live smoke tests only with tiny pool caps.
- Generate reports from snapshots and dashboard/API checks.
- Keep deployment guidance focused on `pm2`, shard env vars, and cron staggering.

## Recommended Production Defaults

| Deployment | Smart Money | Top Trader | OI | Notes |
|---|---|---|---|---|
| Light | `SMART_MONEY_POOL_MAX=100`, hourly | 30m | 30m | Safest starter |
| Standard | `SMART_MONEY_POOL_MAX=200`, hourly | 30m | 30m | Reasonable single-host mode |
| Full 2h | all symbols, every 2h | 30m | 30m | Avoids smart-money overlap |
| Full 1h | 2 smart-money shards | 30m | 30m | Requires staggered cron at `:07` and `:37` |

## Agent Reporting Boundaries

Good wording:

- "Short whales are currently more profitable than long whales."
- "Short average entry is above long average entry, which can indicate late shorts and squeeze risk if price rises."
- "OI velocity is missing for 4h, so do not infer 4h participation."

Bad wording:

- "Buy this."
- "Short now."
- "Guaranteed squeeze."
- "Smart money is always right."

