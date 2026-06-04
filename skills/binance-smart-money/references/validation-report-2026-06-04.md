# Binance Smart Money Skill Validation Report

Date: 2026-06-04

Skill path: `skills/binance-smart-money`

Upstream repository: `https://github.com/0xBennie/binance-smart-money-tracker`

Upstream commit tested: `efcdc3bdfe0aff2283e59df83890a798d46a2f46`

## Summary

Overall status: `DONE`

The OpenClaw skill passes offline validation, metadata checks, fixture report generation, script syntax checks, upstream TypeScript typecheck, upstream build, local dashboard route validation, and controlled live Binance smoke testing.

Direct no-proxy Binance access timed out in this environment. The user-provided VPN proxy `127.0.0.1:7897` restored Binance Futures connectivity, and the live smoke test passed through that proxy.

## Test Results

| Area | Command | Result | Evidence |
|---|---|---|---|
| Skill structure | `python3 skills/binance-smart-money/scripts/validate_skill.py skills/binance-smart-money` | PASS | Printed `PASS: binance-smart-money skill structure and fixture report validated` |
| Fixture report | `python3 skills/binance-smart-money/scripts/fixture_report.py skills/binance-smart-money/fixtures/sample_snapshot.json` | PASS | Generated Markdown report with profit %, whale spread, notional, OI share |
| Forbidden phrase scan | fixture report plus grep for trading instructions | PASS | No `buy now`, `sell now`, `long now`, `short now`, `guaranteed` |
| Script syntax | `bash -n skills/binance-smart-money/scripts/smoke_test.sh` | PASS | Exit 0 |
| Python syntax | `python3 -m py_compile ...` | PASS | Exit 0 during validation run |
| Metadata/readme/permissions | inline Python check | PASS | `skill.json`, frontmatter, README entry, executable scripts verified |
| Upstream typecheck | `npm run typecheck` in `/private/tmp/binance-smart-money-tracker` | PASS | `tsc --noEmit` exit 0 |
| Upstream build | `npm run build` in `/private/tmp/binance-smart-money-tracker` | PASS | `tsc` exit 0 |
| Local dashboard | `PORT=3017 npm run dashboard`, then `/health` and `/api/snapshots` | PASS_WITH_EMPTY_DATA | `/health` returned `{"ok":true,"port":3017}`, `/api/snapshots` returned `[]` |
| Binance connectivity, no proxy | `curl -m 15 https://fapi.binance.com/fapi/v1/ping` | FAIL_ENV | `Connection timed out after 15003 milliseconds` |
| Binance connectivity, proxy | `HTTPS_PROXY=http://127.0.0.1:7897 ... curl -m 20 https://fapi.binance.com/fapi/v1/ping` | PASS | HTTP 200, body length 2, `x-mbx-used-weight-1m: 96` |
| Controlled live smoke, proxy | `HTTPS_PROXY=http://127.0.0.1:7897 ... bash scripts/smoke_test.sh` | PASS | smart-money captured 1/written 1, OI captured 1/written 1, dashboard health/API passed |

## Fixture Output Checks

The fixture report calculated:

- Long profit traders: `46.7%`
- Short profit traders: `74.5%`
- Long whale profit: `46.7%`
- Short whale profit: `80.0%`
- Whale average-entry spread: `6.3%`
- Smart Money notional: `$21.70M`
- Smart Money OI share: `0.1%`
- OI 4h: `-`, preserving `null` as missing data

The generated read used observational language and explicitly said it was not a trade instruction.

## Live Smoke Detail

No-proxy live smoke failed safely:

```text
[preflight] FAILED: timeout of 5000ms exceeded
[smart-money-tick] preflight failed, abort
[Storage] stopped
[preflight] FAILED: timeout of 5000ms exceeded
[oi-tick] preflight failed, abort
[Storage] stopped
FAIL: expected this smoke run to write a new smart-money snapshot row
```

This is the desired failure mode for an unreachable Binance environment:

- It does not continue to hit the undocumented Smart Signal `bapi`.
- It does not retry-loop through a timeout.
- It fails the smoke test because no fresh smart-money data was written.

Proxy live smoke passed with the user-provided VPN proxy:

```bash
HTTPS_PROXY=http://127.0.0.1:7897 \
HTTP_PROXY=http://127.0.0.1:7897 \
ALL_PROXY=http://127.0.0.1:7897 \
bash skills/binance-smart-money/scripts/smoke_test.sh /private/tmp/binance-smart-money-tracker
```

Evidence:

```text
[smart-money-tick] start pool=1 (12s±3s jitter → eta ~12s = 0.2min)
[smart-money-tick] done requested=1 captured=1 written=1 cleaned(sm/tt/oi)=0/0/0 elapsed=13.2s
[oi-tick] start pool=1 (1s±200ms jitter → eta ~1s)
[oi-tick] done requested=1 captured=1 written=1 elapsed=1.6s
{"ok":true,"port":3001}
[{"symbol":"0GUSDT", ...}]
PASS: live smoke test completed
```

SQLite verification after the proxy live smoke:

```text
ob_smart_money_snapshots: count=1, symbol=0GUSDT, max_ts=1780472149707
ob_oi_snapshots: count=1, symbol=0GUSDT, max_ts=1780542600000
```

## Issue Found And Fixed

Finding: `scripts/smoke_test.sh` originally checked only the total row count in `ob_smart_money_snapshots`. If a previous live run had already written rows, a later failed smoke run could pass incorrectly.

Fix applied: the script now records `before_rows` and `before_max_ts`, then requires the current smoke run to increase row count or advance the maximum snapshot timestamp.

Updated pass condition:

```bash
if [ "${after_rows:-0}" -le "${before_rows:-0}" ] && [ "${after_max_ts:-0}" -le "${before_max_ts:-0}" ]; then
  echo "FAIL: expected this smoke run to write a new smart-money snapshot row" >&2
  exit 1
fi
```

## Environment Notes

- Node: `v24.14.0`
- npm: `11.9.0`
- Upstream requires Node `>=20`, so the tested runtime is compatible.
- Direct Binance access timed out, but the local VPN proxy `127.0.0.1:7897` worked for Binance Futures.
- Git/npm required proxy-cleared commands in earlier setup when the proxy was not reachable from the sandbox; live Binance validation used explicit proxy env vars.
- gstack `/browse` was not used for final validation because the local browse server previously failed to allocate a port.
- `tsx` dashboard startup required elevated local execution because sandboxed execution hit `EPERM` on the temporary IPC pipe.

## Acceptance Status

| Requirement | Status |
|---|---|
| OpenClaw metadata exists | PASS |
| Trigger description is specific | PASS |
| Safety boundaries present | PASS |
| Offline validation works | PASS |
| Fixture report works | PASS |
| Upstream compiles | PASS |
| Dashboard routes respond locally | PASS |
| Live Binance smoke passes via VPN proxy | PASS |
| No-proxy live failure is safe | PASS |

## Recommendation

The skill is ready for offline use, project setup guidance, deployment planning, fixture-based report generation, local dashboard validation, and live smoke testing through the local VPN proxy.

Use this command for future local live validation:

```bash
HTTPS_PROXY=http://127.0.0.1:7897 \
HTTP_PROXY=http://127.0.0.1:7897 \
ALL_PROXY=http://127.0.0.1:7897 \
  bash skills/binance-smart-money/scripts/smoke_test.sh /private/tmp/binance-smart-money-tracker
```

Expected live-pass evidence:

- `smart-money:tick` preflight succeeds.
- At least one new row is written to `ob_smart_money_snapshots`.
- `/health` returns JSON OK.
- `/api/snapshots` returns a non-empty JSON array.
