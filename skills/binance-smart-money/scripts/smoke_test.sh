#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-/tmp/binance-smart-money-tracker}"
PORT="${PORT:-3001}"

if [ ! -d "$REPO_DIR" ]; then
  echo "FAIL: repo dir not found: $REPO_DIR" >&2
  exit 2
fi

cd "$REPO_DIR"

if [ ! -f package.json ]; then
  echo "FAIL: package.json not found in $REPO_DIR" >&2
  exit 2
fi

if [ ! -d node_modules ]; then
  npm install
fi

npm run typecheck

before_rows=0
before_max_ts=0
if command -v sqlite3 >/dev/null 2>&1 && [ -f data/snapshots.db ]; then
  before_rows="$(sqlite3 data/snapshots.db "select count(*) from ob_smart_money_snapshots;" 2>/dev/null || echo 0)"
  before_max_ts="$(sqlite3 data/snapshots.db "select coalesce(max(ts), 0) from ob_smart_money_snapshots;" 2>/dev/null || echo 0)"
fi

SMART_MONEY_POOL_MAX=1 npm run smart-money:tick
OI_POOL_MAX=1 npm run oi:tick || true

if command -v sqlite3 >/dev/null 2>&1; then
  after_rows="$(sqlite3 data/snapshots.db "select count(*) from ob_smart_money_snapshots;" 2>/dev/null || echo 0)"
  after_max_ts="$(sqlite3 data/snapshots.db "select coalesce(max(ts), 0) from ob_smart_money_snapshots;" 2>/dev/null || echo 0)"
  if [ "${after_rows:-0}" -le "${before_rows:-0}" ] && [ "${after_max_ts:-0}" -le "${before_max_ts:-0}" ]; then
    echo "FAIL: expected this smoke run to write a new smart-money snapshot row" >&2
    exit 1
  fi
else
  echo "WARN: sqlite3 not installed; skipping row-count check"
fi

PORT="$PORT" npm run dashboard >/tmp/binance-smart-money-dashboard.log 2>&1 &
pid=$!
trap 'kill "$pid" >/dev/null 2>&1 || true' EXIT

for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS "http://127.0.0.1:$PORT/health" >/tmp/binance-smart-money-health.json; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:$PORT/health"
echo
curl -fsS "http://127.0.0.1:$PORT/api/snapshots" | head -c 500
echo
echo "PASS: live smoke test completed"
