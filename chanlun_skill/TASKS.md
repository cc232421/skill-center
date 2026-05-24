# TASKS - Chanlun Skill Refactor Plan

## Context

- Project: `/Users/eric/dreame/code/skill-center/chanlun_skill`
- Ref target: align architecture with `Vespa314/chan.py`
- Constraints confirmed:
  - Allow output schema change to standardized v2
  - Implement full Seg in phase 1 scope
  - Multi-timeframe linkage not required in first iteration
  - Data source must be configurable

---

## Phase 1 - Foundation + Standardized Output

### 1. Core types
- [ ] Create `core/types.py`
- [ ] Define entities: `KLineRaw`, `CombineKLine`, `Fractal`, `Bi`, `Seg`, `ZS`, `BSP`, `AnalysisResultV2`
- [ ] Ensure entity field naming is consistent across modules

Tests:
- [ ] Add `tests/unit/test_types.py`
- [ ] Validate defaults, required fields, and serialization compatibility

### 2. Config center
- [ ] Create `core/config.py`
- [ ] Implement `ChanConfig`
- [ ] Add validation for market/period/source_priority/algo params

Tests:
- [ ] Add `tests/unit/test_config.py`
- [ ] Cover valid config, invalid config, default fallback

### 3. Output schema v2
- [ ] Create `io/schema.py`
- [ ] Define `schema_version = "2.0"`
- [ ] Required blocks: `meta`, `stats`, `kline`, `structures`, `signals`, `state`

Tests:
- [ ] Add `tests/contract/test_output_schema_v2.py`
- [ ] Validate required keys and value types

### 4. Serializer
- [ ] Create `io/serializer.py`
- [ ] Implement deterministic conversion from internal entities to output dict
- [ ] Normalize rounding/time formatting/empty values

Tests:
- [ ] Add `tests/unit/test_serializer.py`
- [ ] Verify precision, null handling, and empty list behavior

### 5. Data API split
- [ ] Create `data_api/base.py`
- [ ] Create `data_api/akshare_api.py`
- [ ] Create `data_api/yfinance_api.py`
- [ ] Create `data_api/binance_api.py`
- [ ] Create `data_api/router.py`
- [ ] Migrate logic from `data_fetcher.py`
- [ ] Support source priority fallback by config

Tests:
- [ ] Add `tests/unit/test_data_router.py`
- [ ] Cover routing by market/symbol and fallback on failure
- [ ] Add `tests/integration/test_fetch_schema.py` to verify normalized DataFrame schema

### 6. Kline layer split
- [ ] Create `kline/raw.py`
- [ ] Create `kline/combine.py`
- [ ] Move raw->combined kline logic out of monolith

Tests:
- [ ] Add `tests/unit/test_kline_combine.py`
- [ ] Cover containment merge, gap detection, and edge cases

### 7. Engine skeleton
- [ ] Create `core/engine.py`
- [ ] Build orchestration skeleton: data -> kline -> structure builders -> serializer
- [ ] Return valid schema v2 even with partial builders

Tests:
- [ ] Add `tests/integration/test_engine_smoke.py`
- [ ] Verify successful end-to-end response structure

### 8. CLI migration
- [ ] Create `cli/main.py`
- [ ] Migrate runtime entry from current `main.py`
- [ ] Keep old `main.py` as compatibility wrapper during transition

Tests:
- [ ] Add `tests/integration/test_cli_args.py`
- [ ] Cover missing args, invalid args, normal execution

Gate:
- [ ] Phase 1 complete when schema contract and smoke tests pass

---

## Phase 2 - Algorithm Split (Full Seg Included)

### 9. Fractal builder
- [ ] Create `bi/fractal.py`
- [ ] Move fractal detection + filtering rules

Tests:
- [ ] Add `tests/unit/test_fractal_rules.py`
- [ ] Cover same-type replacement, min-distance, unfinished fractal handling

### 10. Bi builder
- [ ] Create `bi/bi_builder.py`
- [ ] Move stroke generation, ld calculation, td detection

Tests:
- [ ] Add `tests/unit/test_bi_builder.py`
- [ ] Cover direction, high/low normalization, ld metrics

### 11. Seg rules
- [ ] Create `seg/seg_rules.py`
- [ ] Define segment confirmation/extension/reversal rules

Tests:
- [ ] Add `tests/unit/test_seg_rules.py`
- [ ] Cover major decision branches and conflict resolution

### 12. Seg builder (full implementation)
- [ ] Create `seg/seg_builder.py`
- [ ] Build full segment derivation from Bi sequence
- [ ] Support confirmed and unfinished segment states

Tests:
- [ ] Add `tests/unit/test_seg_builder.py`
- [ ] Cover minimum sample, extension, reversal, trailing unfinished segment

### 13. ZS builder
- [ ] Create `zs/zs_builder.py`
- [ ] Build zhongshu from Seg (configurable fallback to Bi)

Tests:
- [ ] Add `tests/unit/test_zs_builder.py`
- [ ] Cover valid/invalid zhongshu and overlap/high-level detection

### 14. Divergence module
- [ ] Create `bsp/divergence.py`
- [ ] Move MACD-based divergence checks into isolated module

Tests:
- [ ] Add `tests/unit/test_divergence.py`
- [ ] Cover trend divergence, consolidation divergence, non-divergence

### 15. BSP detector
- [ ] Create `bsp/bsp_detector.py`
- [ ] Implement 1/2/3 buy-sell point detection and derived signals

Tests:
- [ ] Add `tests/unit/test_bsp_detector.py`
- [ ] Cover trigger conditions and mutual coexistence/exclusion

### 16. Engine full pipeline
- [ ] Update `core/engine.py` to full chain:
  - [ ] KLine -> Fractal -> Bi -> Seg -> ZS -> BSP
- [ ] Ensure outputs are consistently schema v2

Tests:
- [ ] Add `tests/integration/test_engine_pipeline.py`
- [ ] Verify structure counts and key signal consistency

Gate:
- [ ] Phase 2 complete when full chain tests pass

---

## Phase 3 - Regression, Stability, and Docs

### 17. Golden fixtures
- [ ] Add fixed datasets under `tests/fixtures/` (trend, range, gap)
- [ ] Create deterministic expected outputs for key checkpoints

Tests:
- [ ] Add `tests/integration/test_golden_cases.py`
- [ ] Assert stable fractals/bis/segs/zss/bsp outputs

### 18. Data fallback regression
- [ ] Add failure injection for primary source
- [ ] Validate fallback behavior by `source_priority`

Tests:
- [ ] Add `tests/integration/test_data_fallback.py`

### 19. Legacy wrapper compatibility
- [ ] Keep `chanlun.py` as wrapper calling new engine
- [ ] Keep old invocation path valid during migration period

Tests:
- [ ] Add `tests/contract/test_legacy_wrapper.py`

### 20. Documentation
- [ ] Add/update `README.md`
- [ ] Document schema v2, config model, data source strategy, run examples

Checks:
- [ ] Verify all sample commands execute successfully

Gate:
- [ ] Phase 3 complete when regression suite is stable and docs are accurate

---

## Final Acceptance Criteria

- [ ] `pytest` full suite green
- [ ] Output always includes `schema_version = "2.0"`
- [ ] Config-driven data source routing works with fallback
- [ ] Full single-timeframe chain is deterministic on golden fixtures
- [ ] No remaining monolithic dependency on old `chanlun.py` internals

---

## Suggested Execution Order

1. [ ] Phase 1 tasks 1-8
2. [ ] Phase 2 tasks 9-16
3. [ ] Phase 3 tasks 17-20

