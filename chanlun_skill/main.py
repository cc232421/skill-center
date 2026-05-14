import json
import sys
from chanlun import ChanLunEngine
from data_fetcher import DataFetcher


def main():
    params = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}

    symbol = params.get('symbol', '000001')
    market = params.get('market', 'A')
    period = params.get('period', 'day')
    start = params.get('start_date', '20240101')
    end = params.get('end_date', '20260513')

    if not symbol:
        print(json.dumps({"error": "symbol required"}, ensure_ascii=False))
        return

    try:
        fetcher = DataFetcher(market)
        df = fetcher.fetch(symbol, period, start, end)
    except Exception as e:
        print(json.dumps({"error": f"fetch failed: {e}"}, ensure_ascii=False))
        return

    if df is None or df.empty:
        print(json.dumps({"error": "no data"}, ensure_ascii=False))
        return

    try:
        engine = ChanLunEngine(df)
        result = engine.analyze()
    except Exception as e:
        print(json.dumps({"error": f"analysis failed: {e}"}, ensure_ascii=False))
        return

    result['meta'] = {
        "symbol": symbol, "market": market,
        "period": period,
        "klines_raw": len(engine.klines_raw),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()