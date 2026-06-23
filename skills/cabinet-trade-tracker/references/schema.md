# Cabinet Trade Tracker Schema

Normalized CSV columns:

| Column | Meaning |
|---|---|
| `source` | `open_cabinet` or `quiver_trump_page` |
| `source_url` | URL or local file path used |
| `source_record_id` | Source-specific ID when present |
| `official_name` | Official or politician name |
| `role` | Title/role when available |
| `agency` | Agency when available |
| `level` | Cabinet/Sub-Cabinet/etc. when available |
| `asset_name` | Security or asset description |
| `ticker` | Ticker if supplied |
| `transaction_type` | Purchase/Sale/etc. |
| `traded_date` | Transaction date, ISO date when possible |
| `filed_date` | Filing date, ISO date when available |
| `amount_range` | Disclosure range string |
| `amount_midpoint` | Numeric midpoint estimate when available |
| `late_filing` | `true`, `false`, or empty |
| `excess_return` | Quiver excess return only, never amount |
| `dedupe_key` | Best-effort comparison key |

Comparison rules:

- Exact key match means same `official_name`, normalized ticker or asset name, transaction type, traded date, amount range, midpoint, and filed date where available.
- If no source ID exists and multiple rows share a key, preserve all rows and treat dedupe confidence as low.
- Write disagreements to `discrepancies.csv`; do not silently collapse rows.

