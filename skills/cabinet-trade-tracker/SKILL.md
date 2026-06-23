---
name: cabinet-trade-tracker
description: |
  Track and analyze U.S. executive branch and cabinet financial disclosure trades from Open Cabinet, OGE-derived 278-T data, and QuiverQuant Trump trades. Use this whenever the user asks about cabinet trades, executive branch stock trades, Open Cabinet, Quiver Trump trades, OGE 278-T filings, late filings, political stock trade datasets, or wants CSV/JSON/report output comparing those sources. Produces normalized trade data, source manifests, summaries, and discrepancy reports. Not for investment advice.
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
compatibility: "Python 3.10+, no third-party Python packages required"
---

# Cabinet Trade Tracker

## Purpose

Use this skill to fetch, normalize, compare, and summarize cabinet and executive branch financial transaction data.

Primary source:

- Open Cabinet downloadable data:
  - `https://open-cabinet.org/data/full-dataset.json`
  - `https://open-cabinet.org/data/all-transactions.csv`

Optional comparison source:

- QuiverQuant Donald Trump Stock Trades:
  - `https://www.quiverquant.com/Donald-Trump-Stock-Trades/`
  - Prefer a user-provided Quiver API export/key when available. Without an API key, only parse publicly visible page data and label it as page-extracted.

## Safety and Attribution

1. State that this is informational and not investment advice.
2. Preserve source names and URLs in every output.
3. Treat Open Cabinet amounts as statutory ranges with midpoint estimates, not exact values.
4. Keep Quiver `excess_return` separate from transaction amount. Never include it in amount totals.
5. If Quiver page extraction fails, report the failure clearly instead of guessing.
6. Do not imply ethics/legal conclusions from the dataset alone.

## Workflow

### 1. Choose source mode

Use Open Cabinet by default.

Use Quiver only when the user asks about Trump trades, asks for source comparison, or provides Quiver data/API access.

### 2. Normalize data

Run:

```bash
python3 skills/cabinet-trade-tracker/scripts/cabinet_trade_tracker.py \
  open-cabinet --output-dir /tmp/cabinet-trades
```

For Quiver Trump page extraction:

```bash
python3 skills/cabinet-trade-tracker/scripts/cabinet_trade_tracker.py \
  quiver-trump --output-dir /tmp/cabinet-trades
```

For both sources and discrepancy output:

```bash
python3 skills/cabinet-trade-tracker/scripts/cabinet_trade_tracker.py \
  compare-trump --output-dir /tmp/cabinet-trades
```

### 3. Validate before using live data

Always run offline validation first:

```bash
python3 skills/cabinet-trade-tracker/scripts/cabinet_trade_tracker.py self-check
```

Expected result: `PASS`.

### 4. Output files

The script writes:

- `normalized_trades.csv`
- `summary.md`
- `source_manifest.json`
- `discrepancies.csv` for comparison mode

## Reporting Format

When reporting results, include:

- Source URLs and fetch time.
- Row counts per source.
- Buy/sell counts and midpoint totals.
- Late filing counts when available.
- Top officials and top tickers when available.
- Any discrepancy count.
- A limitation note: amounts are ranges, coverage may be incomplete, and output is not investment advice.

## Troubleshooting

- If Open Cabinet JSON shape changes, try `all-transactions.csv` as fallback.
- If Quiver parsing fails, inspect whether `trumpTradesData` still exists in the HTML.
- If live network is blocked, run `self-check` and ask the user for downloaded source files.

