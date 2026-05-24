# SEL Framework 严格审计意见（更新后代码）

- 代码路径: `/Users/eric/dreame/code/skill-center/skills/sel-framework`
- 审计日期: 2026-05-24
- 审计范围: 本次变更涉及的 11 个文件 + `common/`

## 一、审计结论概览

本次更新方向正确（开始引入统一路径与沙盒门控），但当前仍存在**高优先级回归问题**，尚未达到“可上线、可稳定演化”的质量门槛。

- 测试结果: `73 passed, 2 failed`
- 关键失败点: `skill_evolution_meta` 中未定义变量 `SNAPSHOT_DIR` 被引用，导致演化主链路在运行时失败。

---

## 二、按严重级别排序的审计发现

## 1) High: `skill_evolution_meta` 演化主链路存在确定性运行错误

### 现象
`_load_snapshots()` 在默认路径分支引用 `SNAPSHOT_DIR`，但当前模块中并未定义该符号。

### 证据
- `skill_evolution_meta/__init__.py:156`

### 影响
- `run()` 直接触发 `NameError`。
- 演化流程无法执行，核心能力不可用。

### 建议修复
1. 用 `decision_snapshot.SNAPSHOT_DIR`（动态属性）或 `get_snapshots_dir()` 替代。
2. 增加针对“空 lessons + 无 snapshots”的回归测试，确保不抛异常。

---

## 2) High: 生产代码残留 DEBUG 输出与不可达死代码

### 现象
- `run()` 中保留 `print()` 调试输出。
- `_run_sandbox_validate()` 后面有不可达 `return` 代码块。

### 证据
- `skill_evolution_meta/__init__.py:188`
- `skill_evolution_meta/__init__.py:250`

### 影响
- 污染日志，影响可观测性信噪比。
- 反映代码清理不完整，增加维护与误判风险。

### 建议修复
1. 删除所有 DEBUG `print`。
2. 删除不可达代码块，保留单一路径返回。
3. 如需调试，改为可控 logger（按环境变量开关）。

---

## 3) High: `observability_hub` 路径修复不彻底，仍存在硬编码回退

### 现象
`_current_metrics()` 前半段已采用 `get_rules_dir()`，后半段又覆盖为 `Path("~/.sel_data/rules")`。

### 证据
- `observability_hub/__init__.py:112`

### 影响
- 破坏 `SEL_DATA_DIR` 隔离。
- 受限环境可能再次触发权限问题。
- 指标可能从错误目录读取，导致监控失真。

### 建议修复
1. 删除该硬编码路径分支。
2. 统一只通过 `common.paths` 获取目录。
3. 增加测试：设置临时 `SEL_DATA_DIR` 后，指标统计仅来自该目录。

---

## 4) Medium: “调用时动态解析路径”目标尚未完全落地

### 现象
多个模块仍在 import 时计算目录常量。

### 证据
- `hierarchical_rag_retriever/__init__.py:17`
- `review_scheduler/__init__.py:24`
- `sandbox_simulation/__init__.py:18`
- `skill_evolution_meta/__init__.py:17`
- `observability_hub/__init__.py:16`

### 影响
- 导入后再切换 `SEL_DATA_DIR` 时行为不一致。
- 测试/子进程场景下仍可能出现路径漂移。

### 建议修复
1. 目录路径改为函数内实时取值，不在模块顶层缓存。
2. 若保留缓存，需显式说明“初始化后不可变”并避免测试中动态切换。

---

## 5) Medium: `decision_snapshot` 读路径存在目录不存在异常风险

### 现象
`update/load/list_pending` 直接对 `_snapshot_dir().iterdir()` 遍历，缺少存在性判断。

### 证据
- `decision_snapshot/__init__.py:131`
- `decision_snapshot/__init__.py:148`
- `decision_snapshot/__init__.py:161`

### 影响
- 首次运行、空目录或清理后调用时可能抛 `FileNotFoundError`。

### 建议修复
1. 遍历前加 `if not dir.exists(): return ...`。
2. 补充单元测试覆盖“目录不存在”场景。

---

## 6) Low: `common` 包存在双路径实现，语义冲突

### 现象
- `common/paths.py` 是调用时动态解析。
- `common/__init__.py` 仍是导入时缓存 `_SEL_DATA`。

### 证据
- `common/paths.py`
- `common/__init__.py:10`

### 影响
- 后续开发若误用 `common.__init__` 导出逻辑，会引入隐蔽不一致。

### 建议修复
1. 删除或重写 `common/__init__.py`，避免缓存式路径。
2. 将 `common.__init__` 明确为仅导出 `paths` 中函数（不定义路径状态）。

---

## 7) Low: 测试代码残留调试打印

### 现象
`skill_evolution_meta/test_evolution.py` 留有 DEBUG `print`。

### 证据
- `skill_evolution_meta/test_evolution.py:129`
- `skill_evolution_meta/test_evolution.py:131`

### 影响
- CI 输出噪音增加，降低失败排查效率。

### 建议修复
1. 删除打印。
2. 若必要，改为断言上下文信息。

---

## 三、建议修复优先级（执行顺序）

1. 修复 `skill_evolution_meta` 的 `SNAPSHOT_DIR` 引用错误 + 清理 DEBUG/死代码。
2. 清理 `observability_hub` 中残留 `~/.sel_data` 硬编码。
3. 统一目录解析策略（避免 import 时冻结路径）。
4. 给 `decision_snapshot` 读操作补目录存在性保护。
5. 清理 `common/__init__.py` 冲突实现与测试打印噪音。

---

## 四、验收标准

1. `pytest -q` 全绿（无 failed）。
2. 任意模块不再出现 `~/.sel_data` 直接硬编码（除 `common/paths.py` 默认回退逻辑）。
3. 在临时 `SEL_DATA_DIR` 下运行，不写入宿主目录。
4. `skill_evolution_meta.run()` 在空输入和正常输入场景均可稳定返回。

---

## 五、总体评价

本次更新在架构方向上明显进步，但仍有少量高风险回归阻塞上线。建议先完成上述高优先级修复，再进行下一轮审计确认。
