"""
Alias entry point — delegates to cli.main:run.
Kept for backward compatibility.
"""
import json
import sys
from cli.main import run


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