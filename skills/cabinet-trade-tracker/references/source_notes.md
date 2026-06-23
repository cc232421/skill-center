# Source Notes

Open Cabinet:

- Main source for executive branch trades.
- Download page exposes CSV and JSON files.
- Data is sourced from public OGE financial disclosures.
- Amounts are statutory ranges; midpoint values are estimates.
- Late filing flags come from Open Cabinet's parsing and methodology.

QuiverQuant:

- Use only as optional Trump trade comparison data unless the user provides API access or an exported file.
- Public page embeds `trumpTradesData` used to render the table.
- Field order observed on 2026-06-23:
  `ticker, transaction_type, filed_at, traded_at, excess_return, amount_range, asset_name, quiver_id, midpoint_value`.
- `excess_return` is a market-performance metric and must not be summed as transaction value.

