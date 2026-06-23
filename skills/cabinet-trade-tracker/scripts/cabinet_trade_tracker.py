#!/usr/bin/env python3
"""Fetch, normalize, compare, and validate cabinet trade data."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


OPEN_CABINET_JSON_URL = "https://open-cabinet.org/data/full-dataset.json"
OPEN_CABINET_CSV_URL = "https://open-cabinet.org/data/all-transactions.csv"
QUIVER_TRUMP_URL = "https://www.quiverquant.com/Donald-Trump-Stock-Trades/"

CSV_COLUMNS = [
    "source",
    "source_url",
    "source_record_id",
    "official_name",
    "role",
    "agency",
    "level",
    "asset_name",
    "ticker",
    "transaction_type",
    "traded_date",
    "filed_date",
    "amount_range",
    "amount_midpoint",
    "late_filing",
    "excess_return",
    "dedupe_key",
]


@dataclass
class Trade:
    source: str
    source_url: str
    source_record_id: str = ""
    official_name: str = ""
    role: str = ""
    agency: str = ""
    level: str = ""
    asset_name: str = ""
    ticker: str = ""
    transaction_type: str = ""
    traded_date: str = ""
    filed_date: str = ""
    amount_range: str = ""
    amount_midpoint: str = ""
    late_filing: str = ""
    excess_return: str = ""
    dedupe_key: str = ""

    def finalize(self) -> "Trade":
        self.traded_date = iso_date(self.traded_date)
        self.filed_date = iso_date(self.filed_date)
        self.transaction_type = clean(self.transaction_type)
        self.ticker = clean(self.ticker).upper()
        self.asset_name = clean(self.asset_name)
        self.amount_range = normalize_amount_range(self.amount_range)
        self.amount_midpoint = numeric_string(self.amount_midpoint)
        self.excess_return = numeric_string(self.excess_return)
        self.late_filing = bool_string(self.late_filing)
        key_name = self.ticker or normalize_name(self.asset_name)
        self.dedupe_key = "|".join(
            [
                official_key(self.official_name),
                key_name,
                normalize_name(self.transaction_type),
                self.traded_date,
                normalize_amount_range(self.amount_range),
                self.amount_midpoint,
                self.filed_date,
            ]
        )
        return self


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_name(value: str) -> str:
    return re.sub(r"\s+", " ", clean(value).lower())


def official_key(value: str) -> str:
    name = normalize_name(value)
    if "trump" in name and ("donald" in name or "j." in name):
        return "donald trump"
    return name


def iso_date(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    text = text.split(" ")[0]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    return text


def normalize_amount_range(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    text = text.replace("$$", "$")
    text = re.sub(r"\s*-\s*", "-", text)
    return text


def numeric_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value != value:
        return ""
    text = clean(value)
    if not text or text.lower() == "nan":
        return ""
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return text
    if number.is_integer():
        return str(int(number))
    return str(number)


def bool_string(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    text = clean(value).lower()
    if text in {"true", "1", "yes", "y"}:
        return "true"
    if text in {"false", "0", "no", "n"}:
        return "false"
    return text


def read_text(source: str) -> tuple[str, dict[str, Any]]:
    if source.startswith("http://") or source.startswith("https://"):
        request = Request(source, headers={"User-Agent": "cabinet-trade-tracker/1.0"})
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                return raw.decode(charset, errors="replace"), {
                    "source_url": source,
                    "http_status": response.status,
                    "bytes": len(raw),
                }
        except URLError as exc:
            raise SystemExit(f"fetch failed for {source}: {exc}") from exc
    path = Path(source)
    text = path.read_text(encoding="utf-8")
    return text, {"source_url": str(path), "http_status": "", "bytes": len(text.encode())}


def open_cabinet_from_json(text: str, source_url: str) -> list[Trade]:
    payload = json.loads(text)
    officials = payload.get("officials") or payload.get("data") or []
    trades: list[Trade] = []
    for official in officials:
        for index, tx in enumerate(official.get("transactions") or []):
            trade = Trade(
                source="open_cabinet",
                source_url=source_url,
                source_record_id=clean(tx.get("id") or f"{official.get('slug', '')}-{index}"),
                official_name=clean(official.get("name")),
                role=clean(official.get("title")),
                agency=clean(official.get("agency")),
                level=clean(official.get("level")),
                asset_name=clean(tx.get("description") or tx.get("asset_description")),
                ticker=clean(tx.get("ticker")),
                transaction_type=clean(tx.get("type")),
                traded_date=clean(tx.get("date") or tx.get("transaction_date")),
                filed_date=clean(tx.get("filedDate") or tx.get("filed_date")),
                amount_range=clean(tx.get("amount") or tx.get("amount_range")),
                amount_midpoint=clean(tx.get("midpoint") or tx.get("midpoint_estimate")),
                late_filing=tx.get("lateFilingFlag", tx.get("late_filing_flag", "")),
            ).finalize()
            trades.append(trade)
    if not trades:
        raise SystemExit("Open Cabinet JSON parsed but yielded zero trades")
    return trades


def open_cabinet_from_csv(text: str, source_url: str) -> list[Trade]:
    rows = csv.DictReader(text.splitlines())
    trades: list[Trade] = []
    for index, row in enumerate(rows):
        trade = Trade(
            source="open_cabinet",
            source_url=source_url,
            source_record_id=clean(row.get("id") or row.get("source_record_id") or index),
            official_name=clean(row.get("official_name") or row.get("name")),
            role=clean(row.get("title") or row.get("role")),
            agency=clean(row.get("agency")),
            level=clean(row.get("level")),
            asset_name=clean(row.get("asset_description") or row.get("description") or row.get("asset_name")),
            ticker=clean(row.get("ticker")),
            transaction_type=clean(row.get("type") or row.get("transaction_type")),
            traded_date=clean(row.get("date") or row.get("traded_date") or row.get("transaction_date")),
            filed_date=clean(row.get("filed_date") or row.get("filedDate")),
            amount_range=clean(row.get("amount_range") or row.get("amount")),
            amount_midpoint=clean(row.get("midpoint_estimate") or row.get("midpoint") or row.get("amount_midpoint")),
            late_filing=row.get("late_filing_flag", row.get("late_filing", "")),
        ).finalize()
        trades.append(trade)
    if not trades:
        raise SystemExit("Open Cabinet CSV parsed but yielded zero trades")
    return trades


def parse_open_cabinet(source: str) -> tuple[list[Trade], dict[str, Any]]:
    text, manifest = read_text(source)
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        trades = open_cabinet_from_json(text, manifest["source_url"])
        manifest["format"] = "json"
    else:
        trades = open_cabinet_from_csv(text, manifest["source_url"])
        manifest["format"] = "csv"
    manifest["source"] = "open_cabinet"
    manifest["row_count"] = len(trades)
    return trades, manifest


def parse_quiver_html(source: str) -> tuple[list[Trade], dict[str, Any]]:
    text, manifest = read_text(source)
    match = re.search(r"trumpTradesData\s*=\s*(\[.*?\]);", text, re.DOTALL)
    if not match:
        raise SystemExit("Could not find trumpTradesData in Quiver HTML")
    array_text = match.group(1)
    pythonish = re.sub(r"\bNaN\b", "None", array_text)
    pythonish = re.sub(r"\bnull\b", "None", pythonish)
    try:
        rows = ast.literal_eval(pythonish)
    except (SyntaxError, ValueError) as exc:
        raise SystemExit(f"Could not parse trumpTradesData: {exc}") from exc

    trades: list[Trade] = []
    for row in rows:
        if len(row) < 9:
            continue
        trade = Trade(
            source="quiver_trump_page",
            source_url=manifest["source_url"],
            source_record_id=clean(row[7]),
            official_name="Donald Trump",
            role="President of the United States",
            ticker=clean(row[0]),
            transaction_type=clean(row[1]),
            filed_date=clean(row[2]),
            traded_date=clean(row[3]),
            excess_return=clean(row[4]),
            amount_range=clean(row[5]),
            asset_name=clean(row[6]),
            amount_midpoint=clean(row[8]),
        ).finalize()
        trades.append(trade)
    if not trades:
        raise SystemExit("Quiver HTML parsed but yielded zero trades")
    manifest.update({"source": "quiver_trump_page", "format": "html_embedded_js", "row_count": len(trades)})
    return trades, manifest


def write_outputs(
    trades: list[Trade],
    output_dir: Path,
    manifests: list[dict[str, Any]],
    discrepancies: list[dict[str, str]] | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "normalized_trades.csv", trades)
    write_summary(output_dir / "summary.md", trades, discrepancies or [])
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": manifests,
        "row_count": len(trades),
        "limitations": [
            "Amounts are disclosure ranges with midpoint estimates, not exact values.",
            "Quiver excess_return is a performance metric and is not included in amount totals.",
            "For informational and journalism purposes only; not investment advice.",
        ],
    }
    (output_dir / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if discrepancies is not None:
        columns = ["dedupe_key", "issue", "open_cabinet_count", "quiver_count"]
        with (output_dir / "discrepancies.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(discrepancies)


def write_csv(path: Path, trades: list[Trade]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for trade in trades:
            writer.writerow(asdict(trade))


def write_summary(path: Path, trades: list[Trade], discrepancies: list[dict[str, str]]) -> None:
    source_counts = Counter(t.source for t in trades)
    type_counts = Counter(t.transaction_type for t in trades)
    late_count = sum(1 for t in trades if t.late_filing == "true")
    total_midpoint = sum(float(t.amount_midpoint or 0) for t in trades)
    top_officials = Counter(t.official_name for t in trades if t.official_name).most_common(5)
    top_tickers = Counter(t.ticker for t in trades if t.ticker).most_common(5)
    lines = [
        "# Cabinet Trade Tracker Summary",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Counts",
        f"- Rows: {len(trades)}",
        f"- Sources: {dict(source_counts)}",
        f"- Transaction types: {dict(type_counts)}",
        f"- Late filings: {late_count}",
        f"- Midpoint total: ${total_midpoint:,.0f}",
        f"- Discrepancies: {len(discrepancies)}",
        "",
        "## Top Officials",
    ]
    lines.extend(f"- {name}: {count}" for name, count in top_officials)
    lines.append("")
    lines.append("## Top Tickers")
    lines.extend(f"- {ticker}: {count}" for ticker, count in top_tickers)
    lines.extend(
        [
            "",
            "## Limitations",
            "- Amounts are statutory disclosure ranges with midpoint estimates, not exact amounts.",
            "- Quiver excess_return is not included in transaction amount totals.",
            "- This is informational and journalism-oriented output, not investment advice.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compare_trades(open_trades: list[Trade], quiver_trades: list[Trade]) -> list[dict[str, str]]:
    open_counts = Counter(t.dedupe_key for t in open_trades)
    quiver_counts = Counter(t.dedupe_key for t in quiver_trades)
    discrepancies: list[dict[str, str]] = []
    for key in sorted(set(open_counts) | set(quiver_counts)):
        if open_counts[key] != quiver_counts[key]:
            discrepancies.append(
                {
                    "dedupe_key": key,
                    "issue": "count_mismatch",
                    "open_cabinet_count": str(open_counts[key]),
                    "quiver_count": str(quiver_counts[key]),
                }
            )
    return discrepancies


def command_open_cabinet(args: argparse.Namespace) -> None:
    source = args.source or OPEN_CABINET_JSON_URL
    trades, manifest = parse_open_cabinet(source)
    write_outputs(trades, Path(args.output_dir), [manifest])


def command_quiver_trump(args: argparse.Namespace) -> None:
    source = args.source or QUIVER_TRUMP_URL
    trades, manifest = parse_quiver_html(source)
    write_outputs(trades, Path(args.output_dir), [manifest])


def command_compare_trump(args: argparse.Namespace) -> None:
    open_source = args.open_cabinet_source or OPEN_CABINET_JSON_URL
    quiver_source = args.quiver_source or QUIVER_TRUMP_URL
    open_trades, open_manifest = parse_open_cabinet(open_source)
    quiver_trades, quiver_manifest = parse_quiver_html(quiver_source)
    open_trump = [t for t in open_trades if "trump" in normalize_name(t.official_name)]
    discrepancies = compare_trades(open_trump, quiver_trades)
    write_outputs(open_trump + quiver_trades, Path(args.output_dir), [open_manifest, quiver_manifest], discrepancies)


def command_self_check(_: argparse.Namespace) -> None:
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        open_json = root / "fixtures" / "open_cabinet_sample.json"
        open_csv = root / "fixtures" / "open_cabinet_sample.csv"
        quiver_html = root / "fixtures" / "quiver_trump_sample.html"

        json_trades, json_manifest = parse_open_cabinet(str(open_json))
        csv_trades, _ = parse_open_cabinet(str(open_csv))
        quiver_trades, quiver_manifest = parse_quiver_html(str(quiver_html))
        discrepancies = compare_trades([t for t in json_trades if "trump" in normalize_name(t.official_name)], quiver_trades)
        write_outputs(json_trades + quiver_trades, tmp_path, [json_manifest, quiver_manifest], discrepancies)

        assert len(json_trades) == 3, len(json_trades)
        assert len(csv_trades) == 2, len(csv_trades)
        assert len(quiver_trades) == 3, len(quiver_trades)
        assert quiver_trades[0].excess_return == "", quiver_trades[0].excess_return
        assert quiver_trades[1].ticker == "", quiver_trades[1].ticker
        assert quiver_trades[0].amount_midpoint == "3000000"
        assert (tmp_path / "normalized_trades.csv").exists()
        assert (tmp_path / "source_manifest.json").exists()
        assert (tmp_path / "summary.md").read_text(encoding="utf-8").find("not investment advice") != -1

    print("PASS cabinet-trade-tracker self-check")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    open_parser = subparsers.add_parser("open-cabinet", help="Normalize Open Cabinet JSON or CSV")
    open_parser.add_argument("--source", help="URL or local Open Cabinet JSON/CSV")
    open_parser.add_argument("--output-dir", required=True)
    open_parser.set_defaults(func=command_open_cabinet)

    quiver_parser = subparsers.add_parser("quiver-trump", help="Parse Quiver Trump page HTML")
    quiver_parser.add_argument("--source", help="URL or local Quiver Trump HTML")
    quiver_parser.add_argument("--output-dir", required=True)
    quiver_parser.set_defaults(func=command_quiver_trump)

    compare_parser = subparsers.add_parser("compare-trump", help="Compare Open Cabinet Trump rows with Quiver rows")
    compare_parser.add_argument("--open-cabinet-source", help="URL or local Open Cabinet JSON/CSV")
    compare_parser.add_argument("--quiver-source", help="URL or local Quiver Trump HTML")
    compare_parser.add_argument("--output-dir", required=True)
    compare_parser.set_defaults(func=command_compare_trump)

    self_parser = subparsers.add_parser("self-check", help="Run offline fixture validation")
    self_parser.set_defaults(func=command_self_check)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
