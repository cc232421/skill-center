# Chanlun Skill 代码审计报告

- 审计目录: `/Users/eric/dreame/code/skill-center/chanlun_skill`
- 审计日期: 2026-05-24
- 审计方式: 静态代码审阅 + 本地测试 + 新引擎最小运行验证

## 一、审计结论

当前重构版本**尚未达到可发布状态**。

尽管 `pytest` 结果为通过（`28 passed, 2 skipped`），但测试覆盖重点偏旧实现，新引擎核心链路存在可复现运行时错误，且模型定义与构造使用存在多处不一致。

---

## 二、关键发现（按严重级别）

## 1) High：新引擎主链路可复现崩溃（NameError）

### 现象
`seg/seg_builder.py` 使用 `BI_UP` 但未导入，分析流程在构建 Seg 时直接失败。

### 证据
- `seg/seg_builder.py:13`

### 影响
- 新架构主路径 `Bi -> Seg` 在真实输入下不稳定，阻断后续 `ZS/BSP`。

---

## 2) High：`Seg/ZS/BSP` 数据模型与实现调用不一致

### 现象
1. `Seg` dataclass 未定义 `level/status`，但构造时传入了这两个参数。  
2. `ZS.zg/zd` 定义为 `float`，实现传入了 `Seg` 对象。  
3. `BSP` dataclass 字段为 `point_type/price/date`，实现传入了 `type/seg`。

### 证据
- `core/types.py:112`
- `seg/seg_builder.py:13`
- `core/types.py:131`
- `zs/zs_builder.py:11`
- `core/types.py:147`
- `bsp/divergence.py:33`

### 影响
- 触达对应分支时可能出现 `TypeError` 或结构语义错误。

---

## 3) High：ZS 校验函数签名与调用方式冲突

### 现象
`_is_valid_zs` 定义为 3 参数，但调用时传入一个 list 切片。

### 证据
- `zs/zs_builder.py:12`
- `zs/zs_builder.py:22`

### 影响
- 一旦执行到该路径，立即抛异常。

---

## 4) High：Skill 入口未切换到新架构

### 现象
`skill.json` 仍指向旧入口 `chanlun.py`。

### 证据
- `skill.json:5`

### 影响
- 外部调用默认不会使用新 `core/engine + cli`，重构成果无法生效。

---

## 5) Medium：新旧双栈并存且缺少明确兼容策略

### 现象
同时存在旧链路：`main.py + data_fetcher.py + chanlun.py`  
和新链路：`cli/main.py + data_api + core/engine.py`。

### 证据
- `main.py:1`
- `cli/main.py:1`

### 影响
- 结果口径分裂，调用路径不确定，维护复杂度高。

---

## 6) Medium：数据层日期参数处理不正确

### 现象
yfinance 接口将 `start_date/end_date` 截断为年份（`[:4]`）。

### 证据
- `data_api/yfinance_api.py:20`

### 影响
- 时间窗口精度丢失，历史分析区间与预期不一致。

---

## 7) Medium：类型定义内部不一致

### 现象
`AnalysisResultV2.signals` 注解为 `Dict`，但默认值工厂是 `list`。

### 证据
- `core/types.py:168`

### 影响
- 类型语义冲突，影响静态检查和后续扩展。

---

## 8) Medium：趋势输出被硬编码

### 现象
序列化时趋势固定写成 `neutral`。

### 证据
- `core/engine.py:58`

### 影响
- 上层若依赖趋势态，会得到无效信号。

---

## 9) Low：测试覆盖重点偏旧实现，未覆盖新核心模块

### 现象
核心测试仍主要围绕 `chanlun.py`（旧单体）展开。

### 证据
- `test_chanlun.py:4`

### 影响
- 产生“测试全绿但新主链路崩溃”的假象。

---

## 三、已执行验证

1. 运行测试：
- 命令：`pytest -q`
- 结果：`28 passed, 2 skipped`

2. 新引擎最小运行验证：
- 直接调用 `ChanEngine(...).analyze()`。
- 在具备一定结构复杂度的数据下触发 `NameError`（`BI_UP` 未定义）。

结论：当前测试未覆盖到新链路关键失败点。

---

## 四、修复建议（按优先级）

## P0（必须先做）
1. 修复 `seg_builder` 常量导入与构造参数错误。  
2. 修复 `zs_builder` 的函数签名/调用不一致。  
3. 修复 `bsp/divergence` 对 `BSP` 的构造字段。  
4. 对齐 `core/types.py` 与各构建器字段定义。  
5. 将 `skill.json` 入口切换到新链路（或加明确 legacy 开关）。

## P1（稳定性）
1. 清理新旧双栈，保留单主链路。  
2. 修复 yfinance 日期窗口（使用完整日期字符串，不截断年份）。  
3. 实现真实趋势判定，移除 `neutral` 硬编码。

## P2（质量保障）
1. 增加新架构集成测试：`engine -> seg -> zs -> bsp`。  
2. 补充 schema contract 测试与黄金样本回归。  
3. 引入类型检查（mypy/pyright）防止 dataclass 参数漂移。

---

## 五、审计总结

这次重构在“目录结构与分层方向”上是正确的，但代码尚处于“骨架搭建后未完全对齐实体契约”的阶段。建议先完成 P0 修复，再进行第二轮审计后再考虑发布。
