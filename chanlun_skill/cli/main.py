"""
CLI entry point for Chanlun analysis.
Replaces monolithic main.py with modular structure.
"""
import json
import sys
from typing import Any, Dict
from core.config import ChanConfig
from data_api.router import fetch_with_fallback
from core.engine import ChanEngine


def run(symbol: str, market: str = "A", period: str = "day",
        start_date: str = None, end_date: str = None,
        source_priority: list = None) -> Dict[str, Any]:
    config = ChanConfig(
        symbol=symbol, market=market, period=period,
        start_date=start_date, end_date=end_date,
        source_priority=source_priority
    )
    df = fetch_with_fallback(config)
    if df is None or df.empty:
        return {"error": "fetch failed", "symbol": symbol, "market": market}
    engine = ChanEngine(config, df)
    return engine.analyze()


def main():
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    symbol = args.get("symbol", "000001")
    market = args.get("market", "A")
    period = args.get("period", "day")
    start = args.get("start_date", "20240101")
    end = args.get("end_date", "20260513")
    if not symbol:
        print(json.dumps({"error": "symbol required"}, ensure_ascii=False))
        return
    result = run(symbol, market, period, start, end)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
