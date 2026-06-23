#!/usr/bin/env python3
"""缠论技能入口: python main.py '{"symbol":"688486","market":"A","period":"day","start_date":"20250401","end_date":"20260527"}'"""

import json
import sys

from chanlun_engine import ChanLunEngine
from data_fetcher import DataFetcher


def main():
    params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    symbol = params.get("symbol", "000001")
    market = params.get("market", "A")
    period = params.get("period", "day")
    start = params.get("start_date", "20240101")
    end = params.get("end_date", None)

    if not symbol:
        print(json.dumps({"error": "symbol required"}, ensure_ascii=False))
        return

    try:
        fetcher = DataFetcher(market)
        df = fetcher.fetch(symbol, period, start, end)
    except Exception as e:
        print(json.dumps({"error": f"fetch failed: {e}", "symbol": symbol}, ensure_ascii=False))
        return

    if df is None or df.empty:
        print(json.dumps({"error": f"no data for {symbol}", "symbol": symbol}, ensure_ascii=False))
        return

    try:
        engine = ChanLunEngine(df)
        result = engine.analyze()
    except Exception as e:
        print(json.dumps({"error": f"analysis failed: {e}"}, ensure_ascii=False))
        return

    result["meta"] = {
        "symbol": symbol,
        "market": market,
        "period": period,
        "klines_raw": len(df),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
