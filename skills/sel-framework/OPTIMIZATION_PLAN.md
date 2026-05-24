# SEL Framework 审计优化建议与落地方案

- 项目路径: `/Users/eric/dreame/code/skill-center/skills/sel-framework`
- 审计日期: 2026-05-23
- 目标: 将“可运行”提升到“可测试、可演化、可审计”的工程状态

## 一、执行摘要

当前实现已经具备模块化结构和基础测试覆盖，但存在几个会直接影响稳定性和可信度的核心问题：

1. 数据目录配置不统一，`SEL_DATA_DIR` 在多个模块失效，导致测试不可隔离。
2. 演化激活未真正经过沙盒回测门控，和文档承诺不一致。
3. 行情拉取使用硬编码结束日期，系统会随时间退化。
4. 调度状态与数据快照路径不一致，跨环境行为可能漂移。
5. 回测实现存在占位/简化逻辑，评估可信度不足。

建议先做 P0 修复（1~3），再做 P1（4~5）和文档对齐。

---

## 二、主要发现（按优先级）

## P0-1: 路径配置与 `SEL_DATA_DIR` 失效（高优先级）

### 问题
多个模块在 import 时把路径固定到 `~/.sel_data`，而不是统一通过环境变量动态解析。

### 影响
- 测试之间互相污染。
- 在受限环境中出现 `PermissionError`。
- 多环境（本地/CI/容器）不可控。

### 证据文件
- `decision_snapshot/__init__.py`
- `review_scheduler/__init__.py`
- `self_review_and_extract/__init__.py`
- `hierarchical_rag_retriever/__init__.py`
- `skill_evolution_meta/__init__.py`
- `sandbox_simulation/__init__.py`
- `observability_hub/__init__.py`
- `conftest.py`

### 优化方案
1. 新增统一路径工具（建议 `sel_framework_paths.py` 或 `common/paths.py`）：
   - `get_data_dir()`
   - `get_snapshots_dir()`
   - `get_rules_dir()`
   - `get_logs_dir()`
   - `get_backtests_dir()`
   - `get_lessons_dir()`
2. 所有模块改为运行时调用 `get_*_dir()`，不要在模块导入时冻结路径。
3. `conftest.py` 用 `tmp_path`/`tmp_path_factory` 注入独立 `SEL_DATA_DIR`。
4. 增加“路径隔离”回归测试：验证不同 `SEL_DATA_DIR` 下数据互不影响。

### 验收标准
- `pytest` 在无宿主目录写权限时仍可通过。
- 测试运行后不会写入 `~/.sel_data`。

---

## P0-2: 演化激活未经过真实沙盒验证门（高优先级）

### 问题
`skill_evolution_meta.run()` 当前只走 `_inline_sandbox_validate()` 的弱校验，并未调用 `sandbox_simulation.run()` 做完整门控。

### 影响
- 可能把未经 Sharpe/MDD/交易数验证的规则激活。
- 与文档承诺不一致，降低系统可审计性。

### 优化方案
1. 在 `skill_evolution_meta.run()` 中对每条候选规则调用 `sandbox_simulation.run(rule, ...)`。
2. 以 `approved` 作为唯一激活条件：
   - `approved=True` -> `status=active`
   - `approved=False` -> `status=rejected` + `rejection_reason`
3. 保留 `_inline_sandbox_validate` 仅作为“预过滤”（可选），但不能替代沙盒门。
4. 将回测结果持久化到规则对象（`backtest_id`、`sharpe_ratio`、`max_drawdown_pct`、`win_rate`、`rejection_reasons`）。
5. 对每次激活/拒绝记录 observability 事件。

### 验收标准
- 无法绕过 `sandbox_simulation` 直接激活规则。
- 测试可验证“同一规则在不同指标下通过/拒绝”。

---

## P0-3: 硬编码行情结束日期（高优先级）

### 问题
A 股抓取函数默认 `end="20260519"`。

### 影响
- 该日期后将持续拉不到新数据或回测窗口过旧。

### 优化方案
1. `end` 默认改为动态当天（UTC 或交易所时区一致化）。
2. 支持外部显式传入 `start/end` 覆盖。
3. 对返回空数据增加结构化错误上下文（symbol、market、period、source）。

### 验收标准
- 不修改代码即可持续拉取最新历史数据。

---

## P1-4: 调度状态与快照路径不一致（中优先级）

### 问题
`review_scheduler` 的状态文件写死在 `~/.sel_data/review_scheduler_state.json`，而待复盘快照计数来自 `decision_snapshot`（可能在 `SEL_DATA_DIR`）。

### 影响
- 同一实例的数据和调度状态可能分离。

### 优化方案
1. 将 `STATE_FILE` 放到统一 `data_dir` 下。
2. 读写状态增加异常保护和文件锁（并发安全）。

### 验收标准
- 切换 `SEL_DATA_DIR` 后，状态文件与快照目录同步迁移。

---

## P1-5: 回测语义偏简化，可信度不足（中优先级）

### 问题
`sandbox_simulation.apply_rule_to_df` 对无 regime 规则会生成无 exit/pnl 的条目；部分变量未使用，体现为占位实现。

### 影响
- 指标统计偏差。
- 难以支撑演化门控可信度。

### 优化方案
1. 统一交易事件结构：每笔交易必须有 entry/exit/pnl 才计入指标。
2. 明确持仓与平仓逻辑（time stop / opposite signal / fixed horizon）。
3. 清理未使用变量，补充注释说明简化假设。
4. 增加固定数据夹具，保证回测测试可重复。

### 验收标准
- `compute_metrics` 输入输出语义稳定。
- 回测测试不依赖网络且结果可复现。

---

## P2-6: 文档与实现口径不一致（低优先级）

### 问题示例
- 文档枚举与实现枚举不一致（如 `trend_down`）。
- 文档写“自动调用下游 skill”，代码仅返回状态，缺少编排器。

### 优化方案
1. 统一术语与枚举来源，建议在单一常量文件定义。
2. 文档明确“skill 本身能力”与“编排层职责”的边界。
3. 为关键契约增加 contract test（输入/输出 schema）。

---

## 三、分阶段实施计划

## Phase 1（P0，建议 1~2 天）
1. 抽取统一路径模块并替换全部硬编码目录。
2. 接入真实沙盒门控到 `skill_evolution_meta` 激活流程。
3. 移除行情结束日期硬编码。
4. 修复测试基座，确保在受限环境可跑。

交付物：
- 代码 patch
- 通过的核心测试
- `CHANGELOG` 或更新记录

## Phase 2（P1，建议 1~2 天）
1. 统一 review_scheduler 状态路径与并发保护。
2. 提升回测交易语义与可重复性测试。

## Phase 3（P2，建议 0.5~1 天）
1. 文档与实现对齐。
2. 增加契约测试和最小示例。

---

## 四、测试与验收建议

1. 单元测试
- 各模块核心函数覆盖边界条件。

2. 集成测试
- 完整链路：`decision_snapshot -> self_review -> evolution -> sandbox -> activation`。

3. 环境隔离测试
- 使用临时 `SEL_DATA_DIR`，验证不会写宿主目录。

4. 回归测试
- 固定数据集 + 固定随机种子，确保回测结果稳定。

---

## 五、建议新增的工程约束

1. 引入静态检查
- `ruff`/`flake8`：未使用变量、复杂度、导入规范。

2. 引入类型检查
- `mypy`（关键模块先行）。

3. 统一配置中心
- 将 gate 阈值、路径策略、数据源优先级集中配置。

4. 明确稳定 API
- 对外暴露函数签名固定，避免测试依赖内部实现细节。

---

## 六、风险与回滚策略

1. 风险
- 路径重构可能影响历史数据读取。
- 演化门控收紧后，短期内激活规则数会下降。

2. 缓解
- 提供一次性迁移脚本（旧目录 -> 新目录）。
- 在规则对象中保留原验证结果，便于对比。

3. 回滚
- 通过 feature flag 控制新门控逻辑：
  - `SEL_STRICT_SANDBOX_GATE=true|false`

---

## 七、结论

该 skill 的结构方向是对的，但当前最大短板是“工程一致性与验证可信度”。
优先修复 P0 后，系统会从“概念可用”进入“可持续演进”的状态；随后通过 P1/P2 可把质量提升到可上线维护级别。
