# Chanlun Skill 代码审计修复方案

- 项目路径: `/Users/eric/dreame/code/skill-center/chanlun_skill`
- 生成日期: 2026-05-24
- 文档目标: 将当前严格审计发现转化为可执行修复方案

---

## 一、执行摘要

当前代码在结构上已完成重构雏形，但仍存在影响交易语义正确性的高风险缺陷（尤其是 BSP 信号方向与实体契约漂移）。

建议先完成 P0 修复，再进入回归验证与发布评审。

---

## 二、问题清单（按严重级别）

## P0-1（High）BSP 买卖信号方向反转

### 问题描述
在背驰检测中，分支逻辑将 `sell` 条件返回为 `buy`，`buy` 条件返回为 `sell`。

### 影响
- 交易信号方向错误，属于策略级致命问题。
- 可直接导致反向操作。

### 证据
- `bsp/divergence.py:33`
- `bsp/divergence.py:38`

### 修复方案
1. 统一方向判定逻辑：
   - `direction == BSP_SELL` 时只能返回 `BSP_SELL`
   - `direction == BSP_BUY` 时只能返回 `BSP_BUY`
2. 增加方向一致性断言（开发态可选）。

### 验收标准
- 针对同一输入样本，方向断言测试稳定通过。

---

## P0-2（High）BSP 日期字段取值路径错误

### 问题描述
`Bi.start` 是 `Fractal`，日期应从 `bi.start.k.date` 获取，当前代码使用 `bi.start.date`。

### 影响
- 命中分支时可能触发 `AttributeError`。
- 即使不崩溃也会输出空/错日期。

### 证据
- `bsp/divergence.py:32`

### 修复方案
1. 改为 `date = cb.start.k.date if cb.start and cb.start.k else ""`。
2. 对空日期增加显式保护和测试。

### 验收标准
- BSP 输出 `date` 在有效样本中始终是 ISO 日期字符串。

---

## P0-3（High）Seg 类型契约与实现不一致

### 问题描述
`Seg.start/end` 类型定义为 `Bi`，实现中传入 `Fractal`。

### 影响
- 下游模块基于类型推导会出现错配。
- 长期会导致序列化、规则计算和扩展接口不稳定。

### 证据
- `core/types.py:116`
- `seg/seg_builder.py:13`

### 修复方案（两选一，必须统一）
1. 方案 A（推荐）
   - 保持 `Seg.start/end` 为 `Bi`
   - `seg_builder` 中传入 `bi` 对象而非 `bi.start/bi.end`
2. 方案 B
   - 修改类型定义为 `Fractal`
   - 全链路按 Fractal 重构（改动更大，不推荐）

### 验收标准
- `mypy/pyright` 不再报 `Seg` 相关类型错配。
- `serialize_seg` 与构建数据一致。

---

## P1-4（Medium）ZS 实体字段契约漂移

### 问题描述
`ZS.bis` 声明为 `List[Bi]`，当前构建传入 `List[Seg]`。

### 影响
- 语义错位，后续统计与规则复用风险高。

### 证据
- `core/types.py:137`
- `zs/zs_builder.py:20`

### 修复方案
1. 若中枢由 Seg 构建：字段更名为 `segs: List[Seg]`。
2. 若沿用 `bis` 命名：保持 `List[Bi]` 并在构建阶段传 Bi。
3. 同步 serializer 字段说明与 schema 文档。

### 验收标准
- 类型定义、构造实现、序列化三者一致。

---

## P1-5（Medium）ZS 数值判定对 0 值不安全

### 问题描述
`if x and y` 判断会把 `0.0` 误判为缺失。

### 影响
- `gg/dd` 计算在边界行情下错误。

### 证据
- `zs/zs_builder.py:16`
- `zs/zs_builder.py:17`

### 修复方案
1. 全部替换为 `is not None` 判断。
2. 增加 0 值边界样本测试。

### 验收标准
- 含 0 值样本时 `gg/dd` 计算正确。

---

## P1-6（Medium）对外参数契约与实现能力不一致

### 问题描述
配置支持 `CRYPTO`，`skill.json` market enum 未包含 `CRYPTO`。

### 影响
- 对外调用方无法正确发现能力。

### 证据
- `core/config.py:7`
- `skill.json:16`

### 修复方案
1. `skill.json` market enum 加入 `CRYPTO`。
2. 文档补充 symbol 约定（如 `BTC` -> `BTCUSDT`）。

### 验收标准
- 配置层能力与 `skill.json` 完全一致。

---

## P2-7（Low）测试覆盖不足导致“假绿”

### 问题描述
现有测试主要校验 schema 形状，未验证核心业务正确性（方向、结构语义、关键字段）。

### 影响
- 高风险缺陷无法被 CI 捕捉。

### 证据
- `tests/unit/test_engine.py`

### 修复方案
新增以下测试集：
1. `tests/unit/test_bsp_direction.py`
   - 覆盖 buy/sell 方向映射。
2. `tests/unit/test_bsp_date_field.py`
   - 覆盖 `date` 字段来源与非空性。
3. `tests/unit/test_seg_type_contract.py`
   - 校验 Seg start/end 类型一致性。
4. `tests/unit/test_zs_contract.py`
   - 校验 ZS `bis/segs` 契约一致。
5. `tests/integration/test_pipeline_golden.py`
   - 固定样本断言 `Bi/Seg/ZS/BSP` 关键输出。

### 验收标准
- 能稳定复现并防回归 P0/P1 问题。

---

## 三、修复实施顺序（建议）

## Step 1（P0，必须先做）
1. 修复 BSP 方向反转。
2. 修复 BSP 日期字段路径。
3. 统一 Seg 类型契约并改造构建器。

## Step 2（P1）
1. 统一 ZS 契约（字段命名 + 类型）。
2. 修复 ZS `None` 判定逻辑。
3. 对齐 `skill.json` 与配置能力。

## Step 3（P2）
1. 补齐单元 + 集成黄金样本测试。
2. 建立发布前检查清单。

---

## 四、发布前验收清单

1. 功能正确性
- [ ] BSP 方向测试通过
- [ ] BSP 日期字段测试通过
- [ ] Seg/ZS 契约一致性测试通过

2. 回归质量
- [ ] `pytest -q` 全绿
- [ ] 新增黄金样本测试通过

3. 契约一致性
- [ ] `skill.json` 与 `ChanConfig` 能力一致
- [ ] schema 文档与序列化输出一致

4. 工程健康
- [ ] 无明显死代码/未使用导入
- [ ] 类型检查（可选但推荐）无关键告警

---

## 五、建议的最小提交拆分（便于审阅）

1. `fix(bsp): correct signal direction and date source`
2. `refactor(seg): align Seg type contract with builder`
3. `refactor(zs): unify ZS entity contract and None-safe numeric checks`
4. `chore(skill): align market enum with runtime config`
5. `test(core): add bsp/seg/zs contract and golden pipeline tests`

---

## 六、结论

当前版本可作为重构中间态，但不建议直接发布。完成本报告中的 P0/P1 修复并补齐关键测试后，才具备进入下一轮发布评审的条件。
