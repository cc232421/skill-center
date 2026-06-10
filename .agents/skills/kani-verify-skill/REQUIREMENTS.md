# kani-verify-skill — 需求文档

> **Status:** Draft v0.2 — Post-audit (Rust rewrite)
> **Date:** 2026-06-10
> **Owner:** TBD
> **Source:** Derived from [Kani blog — Writing Code with ChatGPT? Improve it with Kani](https://model-checking.github.io/kani-verifier-blog/2023/05/01/writing-code-with-chatgpt-improve-it-with-kani.html)
>
> ## 修订历史 (Changelog)
>
> | 版本 | 日期 | 主要变更 |
> |------|------|----------|
> | v0.1 | 2026-06-10 | 初稿：基于博客提炼方法论 + 6 个 FR + 5 个 NFR |
> | v0.2 | 2026-06-10 | 架构从 Python 迁移到 Rust；修正若干需求不一致（见 §11 审计报告） |

---

## 1. 背景与动机 (Background)

### 1.1 源博客提炼的核心方法论

博客展示了 **"LLM 生成代码 → 形式化验证 → 反馈迭代"** 的三步闭环：

| 阶段 | 输入 | 工具 | 输出 |
|------|------|------|------|
| 1. 生成 | 自然语言 prompt | LLM (ChatGPT) | Rust 源码 (未验证) |
| 2. 验证 | Rust 源码 + Kani harness | Kani verifier | PASS / FAIL + counterexample |
| 3. 修复 | Kani 报告 (失败原因 + 反例) | LLM | 新版本源码 |
| 循环直到 Kani: SUCCESSFUL | | | |

### 1.2 博客中验证失败的两个典型 bug

这两个 case 是 skill 必须能处理的 **最小代表性场景**：

**Case A — 整数溢出 (overflow)**
```rust
fn integer_average(a: i32, b: i32) -> i32 {
    (a + b) / 2  // Kani: "attempt to add with overflow" 当 a = i32::MAX
}
```

**Case B — 优化等价性失败 (equivalence)**
```rust
// ChatGPT "优化" 的实现
let y = x | (x + 1);  // Kani: overflow + 与原版不等价
```
反例：`x = 2147483647` (i32::MAX) 时失败。

### 1.3 痛点

- LLM 生成的代码 **默认不可信** (训练语料多为未验证代码)
- 手动写 Kani harness + 解读 CBMC 风格的失败报告 **门槛高**
- 修复提示词需要把 Kani 输出 **翻译成 LLM 可理解的语言**
- 迭代过程 **没有状态追踪**，容易在多轮 fix 中丢失上下文

---

## 2. 目标与非目标 (Goals & Non-goals)

### 2.1 目标 (In Scope)

1. **自动化生成 Kani harness** — 从目标函数的签名自动构造 `#[kani::proof]` + `kani::any()` 输入
2. **解析 Kani 输出** — 提取 `Failed Checks`、行号、counterexample (`--concrete-playback` 输出)
3. **将 Kani 失败报告翻译成 LLM 友好的 prompt** — 包含函数名、失败行、失败类型、可选反例值
4. **维护修复迭代状态** — 在同一会话内循环运行 generate → verify → fix，记录每次迭代的 diff
5. **等价性验证模式 (Equivalence Mode)** — 验证两个实现 (如优化前/后) 在所有输入上行为一致
6. **支持基础属性检查** — 至少覆盖：算术溢出、数组越界、除零、断言失败、panic、option/result unwrap 失败

### 2.2 非目标 (Out of Scope)

- ❌ 实现 Kani 本身 (它是外部 Rust crate，本 skill 是其编排层)
- ❌ 替代 Copilot/Cursor 等 IDE 内联补全 (本 skill 是 **离线、批处理式** 验证工作流)
- ❌ 支持非 Rust 语言
- ❌ 性能基准证明 (博客中明确说 "proving the performance improvement is challenging"，跳过)
- ❌ 端到端调用任意 LLM API (v1 假设用户已有 LLM 访问能力，skill 负责生成 prompt 模板 + 解析输出)
- ❌ 修复安全漏洞 / 逻辑 bug (Kani 只证明指定属性，不证明 "代码做了正确的事")

---

## 3. 用户故事 (User Stories)

| ID | 角色 | 故事 |
|----|------|------|
| US-1 | 开发者 | "我用 LLM 生成了一个 `parse_csv` 函数，让 Kani 验证它对所有输入都不会 panic" |
| US-2 | 开发者 | "我手写了一个排序函数，让 Kani 证明它对所有 `Vec<i32>` 输入都返回非递减序列" |
| US-3 | 优化者 | "我有一个实现 `foo_v1` 和 LLM 生成的优化版 `foo_v2`，证明两者对所有输入等价" |
| US-4 | 教学者 | "演示 LLM 生成的代码为什么不能盲目信任 — 用 Kani 找反例喂回 LLM，看它怎么改" |
| US-5 | 评审者 | "在 PR 中自动跑 Kani，给出 'untrusted LLM code' 警告" |

---

## 4. 功能需求 (Functional Requirements)

### FR-1: Harness 生成器 (Harness Generator)

> **v0.2 变更:** 从字符串模板改为 `syn` AST + `quote!` 代码生成。理由见 §11.2。

**输入:** 源文件路径 + 目标函数名（用户指定或默认第一个 `pub fn`）
**输出:** 完整可编译的 Kani harness 源文件

**处理流程:**
1. `syn::parse_file` 解析源文件为 `File` AST
2. 在 AST 中查找目标 `ItemFn`（按函数名匹配；不区分 `pub`）
3. 提取 `Sig`（签名）→ 强类型 `SigModel`（避免字符串处理）
4. 用 `quote!` 拼接 `#[kani::proof]` harness 函数
5. 整体 `format!` 出一个新的 `.rs` 文件，保留原文件 imports

**必须支持的签名类型:**

| 输入参数类型 | 生成的 harness 输入 |
|-------------|---------------------|
| `i32` / `u32` / `i64` / `u64` / `usize` / `isize` | `kani::any()` |
| `bool` | `kani::any()` |
| `f32` / `f64` | `kani::any()` (注: Kani 对浮点支持有限) |
| `Option<T>` | `kani::any::<Option<T>>()` |
| `(T, U)` | `kani::any::<(T, U)>()` |
| `&[T]` (slice 引用) | 限制长度 (`MAX_LEN` 默认 4) + `kani::any::<Vec<T>>()` 后取引用 |
| `&str` | 限制长度 + UTF-8 验证 (依赖 `kani::any::<String>()`) |
| 自定义 struct (未实现 `Arbitrary`) | 给出明确错误，要求用户先 `impl kani::Arbitrary` |
| 泛型函数 `<T: ...>` | 给出明确错误，v1 不支持；提示用户手动展开 |
| `impl Trait` 参数 | 给出明确错误，v1 不支持 |

**示例输出 (从博客 Case A):**
```rust
// 保留原文件所有 imports
fn integer_average(a: i32, b: i32) -> i32 {
    (a + b) / 2
}

#[kani::proof]
#[kani::unwind(5)]
fn verify_integer_average() {
    let a: i32 = kani::any();
    let b: i32 = kani::any();
    let _ = integer_average(a, b);
    // User postconditions go here (FR-1.1)
}
```

**FR-1.1 后置条件注入:** 用户可声明 `assert!(result >= 0)` 等。存储位置：`.kani-verify/postcondition.toml` 或 CLI flag `--assert "result >= 0"`。**默认值无后置条件**（仅证明 "不 panic"，对应博客 Case A 的最弱断言）。

**FR-1.2 命名空间处理:** 目标函数在 `mod foo` / `impl Bar` 内时，harness 必须用完整路径（如 `crate::foo::target` 或 `<Bar as Trait>::target`）。

### FR-2: Kani 输出解析器 (Output Parser)

**输入:** `kani` CLI 的 stdout + stderr（合并）
**输出:** 结构化 `VerificationReport`（`serde::Serialize`/Deserialize，持久化为 `report.json`）

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerificationReport {
    pub status: Verdict,
    pub failed_checks: Vec<FailedCheck>,
    pub total_checks: u32,
    pub failed_count: u32,
    pub verification_time: Duration,
    pub kani_version: String,           // 用于版本适配 (§8.2)
    pub raw_stdout: String,             // 原始输出 (审计 + 排错)
    pub raw_stderr: String,
    pub started_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Verdict {
    Success,
    Failure,
    Aborted,        // 超时 / 进程崩溃 / OOM
    ParseError,     // skill 无法解析 Kani 输出（v0.1 → 应罕见；v0.2 用版本适配表兜底）
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FailedCheck {
    pub kind: FailureKind,
    pub file: PathBuf,
    pub line: u32,
    pub function: String,
    pub message: String,                // Kani 原始消息（"attempt to add with overflow"）
    pub counterexample: Option<ConcreteValues>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum FailureKind {
    ArithmeticOverflow,         // add/sub/mul/shl with overflow
    DivisionByZero,
    OutOfBounds,                // index / slice
    RemainderByZero,
    AssertionFailed,            // assert! / assert_eq!
    UnwrapOnNone,               // Option::unwrap
    UnwrapOnErr,                // Result::unwrap
    Unreachable,                // unreachable!()
    InvalidBool,                // 非 0/1 的 bool
    PointerOverflow,
    NullPointer,
    ArithmeticShift,
    UnwindingLimit,             // --unwind 上限被突破
    Other(String),              // 未识别类型保留原文
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConcreteValues {
    pub variables: Vec<(String, String)>,  // (name, value) — 字符串值保留原始类型展示 ("i32::MAX", "[1, 2, 3]")
}
```

**必须能从输出中提取:**
- `SUMMARY: ** X of Y failed` 计数
- `Failed Checks: <kind>` 类型 → 映射到 `FailureKind` 枚举
- `File: "...", line N, in <func>` 位置
- `--concrete-playback=print` 模式的反例值
- `Verification Time: Xs`
- `Check X: <file>:<line>` 单项检查的位置
- **多 failed check** 全部提取（不只取第一个）

**解析策略:**
- **双层解析**: 先用正则定位锚点（`SUMMARY:`, `Failed Checks:`, `File:`），再用 `nom` 或手写 parser 提取结构（v0.1 用正则即可，正则在已知 Kani 输出格式下足够稳健）
- **Kani 版本兼容**: 解析器初始化时探测 `kani --version`，根据 major.minor 选择不同正则 pattern（v0.1 仅支持 Kani ≥ 0.50；老版本给明确错误）
- **解析失败兜底**: 产生 `Verdict::ParseError` + 原始 stdout/stderr，prompt 模板 fallback 到「粘贴 Kani 原始输出让 LLM 自己看」

### FR-3: 失败 → Prompt 翻译器 (Failure-to-Prompt Translator)

**输入:** `VerificationReport` + 当前源码 (作为字符串传入) + 用户提供的 LLM 上下文(可选)
**输出:** 给 LLM 的自然语言提示词（写入 `.kani-verify/iter-N/llm-prompt.txt`）

**模板 (基于博客 Case A 的成功 prompt):**
```
The expression on line 2 of `integer_average`:
    (a + b) / 2
may trigger: arithmetic overflow.
A counterexample is: a = 2147483647, b = 1.

Please provide a fix that handles all i32 inputs without overflow.
Return ONLY the complete fixed function (no explanations, no markdown).
The function signature must remain: `fn integer_average(a: i32, b: i32) -> i32`.
```

**规则:**
- 失败类型 → 自然语言映射（用 `taxonomy.rs` 的 `FailureKind → natural_language` 表）
- 反例值 → 嵌入提示词（用 `--concrete-playback` 输出，按变量名格式化）
- 源代码上下文 → 引用失败行 ±2 行（用 `syn` 解析后定位 span）
- **明确指定输出格式**: "Return ONLY the complete fixed function"（避免 LLM 返回解释 + 代码混合的 markdown）

**FR-3.1 LLM 响应格式 (v0.2 新增):**
- skill 期望 LLM 返回**纯函数定义**（含 `fn` 关键字）
- 接受格式：
  1. 纯 Rust 函数（首选）
  2. 单个 ```rust ... ``` 代码块
  3. `pub fn` / `fn` 均可
- 不接受：纯解释文本、多个代码块、改了函数签名、删了函数、添加新文件
- 解析失败 → 走 NFR-3 兜底逻辑，提示用户人工介入

**FR-3.2 多失败聚合:** 同一 `#[kani::proof]` 中有 N 个失败时，prompt 中列出**全部**失败（不只是第一个），避免 LLM 修复一个引入另一个（对应博客 Case B 的第三轮现象）。但**反例只贴第一个**（避免 prompt 过长）。

### FR-4: 迭代循环编排器 (Iterative Loop Orchestrator)

> **v0.2 变更:** 状态机改用 Rust `enum` 表达，避免 v0.1 文本图标的歧义。

**状态机（Rust 类型签名）:**

```rust
pub enum IterationState {
    Idle,
    HarnessGenerated { iter: u32, harness_path: PathBuf },
    KaniRunning { iter: u32, pid: u32, started_at: DateTime<Utc> },
    KaniSucceeded { iter: u32, report: VerificationReport },
    KaniFailed { iter: u32, report: VerificationReport },
    KaniAborted { iter: u32, reason: AbortReason },
    AwaitingLLMResponse { iter: u32, prompt_path: PathBuf },
    PatchApplied { iter: u32, source_hash_before: String, source_hash_after: String },
    Done { final_iter: u32, final_status: Verdict },
    FailedPermanently { iter: u32, reason: String },  // 达到 max_iterations 仍未通过
}

pub enum AbortReason {
    Timeout { after: Duration },
    OutOfMemory,
    Crash { exit_code: i32, signal: Option<i32> },
    UserInterrupt,
}
```

**转换规则:**

```
Idle --verify--> HarnessGenerated
HarnessGenerated --run--> KaniRunning
KaniRunning --ok--> KaniSucceeded --> Done
KaniRunning --fail--> KaniFailed --> AwaitingLLMResponse
KaniRunning --aborted--> KaniAborted --> FailedPermanently (NOT auto-retry)
AwaitingLLMResponse --response received--> PatchApplied
PatchApplied --next iter--> HarnessGenerated (++iter)
KaniSucceeded/Failed --iter >= max--> Done or FailedPermanently
```

**配置参数:**
- `max_iterations`: 默认 5（博客中两个 case 各需 2-3 轮）
- `kani_timeout`: 默认 300s（CBMC 在复杂代码上可能很慢；超时后 KaniAborted → FailedPermanently，**不**自动重试）
- `auto_apply_patch`: bool, 默认 false（需用户确认 LLM 输出；auto-apply 仅在 CI/无人值守场景下用）
- `patch_strategy`: `Replace` | `Merge`（默认 `Replace`：LLM 必须返回完整新函数体；`Merge` 暂不实现）

**FR-4.1 原子化事务:** 每次迭代 N 的写盘顺序：
1. 写 `iter-N/.tmp/source.rs`
2. 写 `iter-N/.tmp/harness.rs` (如有)
3. 写 `iter-N/.tmp/report.json`
4. `fsync` `.tmp/`
5. `rename` `.tmp/` → `iter-N/`
6. 写 `iter-N/manifest.json`（最后写，作为完成标志）
7. 更新 `.kani-verify/state.json`

**FR-4.2 Crash 恢复:** 启动时若发现某 `iter-N/` 无 `manifest.json`，标记为 `Corrupted`，在 summary.md 中提示，**不**自动删除。

### FR-5: 等价性验证模式 (Equivalence Mode)

**输入:** 两个函数 `f1`, `f2` (相同签名)
**输出:** 证明 `∀ x. f1(x) == f2(x)` 或反例

**Harness 模板 (从博客 Case B):**
```rust
#[kani::proof]
fn check_equivalence() {
    let x: u32 = kani::any();
    assert_eq!(lowest_unset_bit_ori(x), lowest_unset_bit_opt(x));
}
```

**支持变体:**
- `f1(x) == f2(x)` (Result 模式)
- `f1(x).is_ok() == f2(x).is_ok() && f1(x).unwrap() == f2(x).unwrap()` (Result 深度比较)
- 自定义断言字符串

### FR-6: 失败类型分类与提示 (Failure Taxonomy)

| Kani 报告 | 自然语言 | 修复策略提示 |
|-----------|----------|--------------|
| `attempt to add with overflow` | "addition may overflow" | 用 `checked_add` / `saturating_add` / `wrapping_add` |
| `attempt to multiply with overflow` | "multiplication may overflow" | `checked_mul` |
| `index out of bounds` | "array/Vec index out of bounds" | 长度检查 / `get()` |
| `attempt to divide by zero` | "division by zero" | 分母检查 |
| `assertion failed: ...` | "postcondition violated" | 引用 LLM 提供的反例 |
| `unwrap on None value` | "Option::unwrap on None" | `match` / `?` / `unwrap_or` |
| `unwrap on Err value` | "Result::unwrap on Err" | 错误传播 |

---

## 5. 非功能需求 (Non-Functional Requirements)

### NFR-1: 可用性 (Usability)
- **零配置启动**: 用户只需提供 Rust 源文件路径，skill 自动检测 Kani 是否已安装 (`kani --version`)，缺失时给出**安装指引 URL + 明确 abort**（不静默降级，避免给出"未验证"的虚假 PASS）
- **进度可视化**: 每次迭代显示 `tracing` 风格日志，如 `[iter 2/5] kani: FAILED (overflow @ line 18); prompt → .kani-verify/iter-2/llm-prompt.txt`
- **离线友好**: 除 LLM 调用外，全部本地运行
- **错误信息可读**: 所有 `anyhow` 错误必须包含 `source` 链 + 修复建议（不裸抛 CBMC 内部错误）

### NFR-2: 性能 (Performance)
- Harness 生成 + Kani 输出解析: < 1 秒 (忽略 Kani 本身的 CBMC 验证时间)
- **缓存键**: `sha256(source.rs 内容) + sha256(harness.rs 内容) + Kani version + 关键 flags` — 文件路径变化不失效
- 缓存命中时直接返回上次的 `VerificationReport`，不重跑 Kani

### NFR-3: 可靠性 (Reliability)
- **Kani 进程崩溃 / CBMC OOM / 超时** 必须在 `tokio::time::timeout` 控制下，超时或非零退出码产生 `VerificationReport { status: Aborted, reason: ... }`，**不**进入下一轮
- **迭代原子化**: 每次写 `.kani-verify/iter-N/` 必须先写 `.tmp/` → `fsync` → `rename` 到目标；`iter-N/manifest.json` 必须在所有附属文件写完**之后**最后写（manifest 存在 = 该迭代完整；否则视为不完整，可被下次启动清理）
- **崩溃恢复**: 启动时扫描 `.kani-verify/iterations/`，跳过无 manifest 的残缺目录
- **必须有 `--dry-run`** 模式，只生成 harness 不跑 Kani
- **LLM 输出兜底**: LLM 响应解析失败（函数签名被破坏 / 删了目标函数 / 返回纯文本）→ 不写回源码，提示用户人工介入，**绝不静默接受**

### NFR-4: 可移植性 (Portability)
- 支持 macOS / Linux (Kani 官方支持平台；Windows 不在 v1 范围)
- **skill 自身**: Rust ≥ 1.75 (edition 2021, 利用 `let-else` / `format!` 捕获标识符等)
- **目标项目**: Rust 1.70+ (Kani 当前最低要求)
- Kani ≥ 0.50（使用 `--concrete-playback` 稳定 API；旧版可能命名不同）
- skill 自身不假设 musl/glibc 特定行为

### NFR-5: 可观察性 (Observability)
- 所有迭代保存到 `.kani-verify/iterations/iter-N/` 目录
- 每轮必含: `source.rs`, `harness.rs`, `report.json`, `llm-prompt.txt`, `llm-response.txt`(如已粘贴), `manifest.json`
- 最终报告: `.kani-verify/summary.md` (人类可读，含每次迭代的 Kani 状态 + 失败类型 + 关键 diff)
- 结构化日志: `tracing` + `tracing-subscriber::fmt::json`，可通过 `RUST_LOG=kani_verify=debug` 控制详细度

### NFR-6: 安全 (Security) — **v0.2 新增**
- **绝不执行 LLM 返回的代码**: LLM 响应只作为**文本 patch** 应用，绝不 `cargo run` / `cargo build` 其内容（防止 prompt injection 触发任意代码）
- **patch 应用前 sanitize**: tree-sitter 解析后必须能匹配原始 `syn` 解析出的函数节点；不能识别为函数的代码块不应用
- **临时文件清理**: LLM 响应 / Kani 输出等敏感内容，使用 `tempfile::TempDir`（离开作用域自动清理），不留在 `/tmp`
- **路径校验**: 用户提供的源文件路径必须解析为真实存在的 `.rs` 文件，**拒绝符号链接指向 `/etc` 等敏感位置**

---

## 6. 技术架构 (Technical Architecture)

### 6.1 模块划分 (Rust 实现)

> **变更说明 (v0.2):** 原 v0.1 草案用 Python 脚本实现。审计后改为 **纯 Rust 实现**，理由见 §11.2。本项目是一个 **单一 Cargo crate**，既是 library 也是 binary。

```
kani-verify-skill/
├── SKILL.md                    # Skill 元数据 + 触发条件
├── Cargo.toml                  # 单 crate，二进制名 kani-verify
├── src/
│   ├── lib.rs                  # 公开 API（被二进制 + 未来集成方调用）
│   ├── main.rs                 # CLI 入口（clap）
│   ├── harness/
│   │   ├── mod.rs              # FR-1: 基于 syn 的 AST 生成器
│   │   ├── sig_extract.rs      # 从源文件提取目标函数签名
│   │   ├── sig_model.rs        # 类型化签名数据模型（强类型，非字符串）
│   │   └── emit.rs             # 生成完整 harness 源码（quote!）
│   ├── kani/
│   │   ├── mod.rs              # FR-2: Kani 进程调用
│   │   ├── run.rs              # tokio Command 包装 + 超时
│   │   └── output.rs           # 解析 Kani 文本输出 → VerificationReport
│   ├── report.rs               # FR-2: VerificationReport / FailedCheck 数据结构
│   ├── taxonomy.rs             # FR-6: 失败类型枚举 + 自然语言映射
│   ├── prompt/
│   │   ├── mod.rs              # FR-3: report → LLM prompt
│   │   ├── context.rs          # 失败行 ±N 行源代码上下文提取
│   │   └── templates.rs        # askama 模板（编译期检查，类型安全）
│   ├── loop/
│   │   ├── mod.rs              # FR-4: 状态机驱动
│   │   ├── state.rs            # Iteration 状态定义
│   │   └── persist.rs          # .kani-verify/ 目录的原子化事务
│   ├── equivalence.rs          # FR-5: 等价性模式
│   ├── llm/
│   │   ├── mod.rs              # 接收 LLM 响应（粘贴 / 文件）
│   │   └── patch.rs            # 用 tree-sitter 解析 LLM 输出的 diff
│   ├── config.rs               # 配置加载（CLI flags + .kani-verify.toml）
│   └── error.rs                # thiserror 统一错误类型
├── references/
│   ├── harness-templates.md    # harness 模式库（参考用，运行时由代码生成）
│   ├── failure-taxonomy.md     # 失败类型完整说明
│   ├── kani-cli-options.md     # 推荐/必须的 Kani flag
│   └── llm-prompt-templates.md # LLM prompt 模板示例
├── examples/
│   ├── integer_average/        # 博客 Case A 完整可运行示例
│   └── lowest_unset_bit/       # 博客 Case B 完整可运行示例
└── tests/
    ├── harness_gen.rs          # 单元测试（syn 解析 + 重新打印）
    ├── parser.rs               # Kani 输出的 golden 测试
    ├── taxonomy.rs             # 失败类型分类覆盖
    └── e2e/                    # 集成测试（需要本机装 Kani）
        ├── case_a_overflow.sh
        └── case_b_equivalence.sh
```

### 6.2 关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| **实现语言** | **Rust** | 与 Kani 同生态（共享 `syn`/`quote` 工具链）；类型安全；与 LLM 目标代码同语言便于混合分发；单二进制分发 |
| **Harness 生成方式** | **`syn` AST + `quote!` 代码生成** | 字符串模板对 Rust 签名（泛型、生命周期、where 子句）脆弱；AST + 强类型 `SigModel` + 重新打印保证 round-trip 一致 |
| **Kani 调用方式** | **`tokio::process::Command`** | 异步不阻塞；统一超时控制；Kani 本身无 JSON 输出，需自己解析文本 |
| **LLM 集成** | **生成 prompt 文本 + 接收用户粘贴或文件** | 不绑特定 LLM API；保留用户对模型的选择权；可同时把响应作为 audit trail 保存 |
| **LLM 输出解析** | **`tree-sitter-rust` + diff 匹配** | LLM 可能改函数签名/加 import；不能简单 `replace`；用 tree-sitter 解析后定位目标函数 AST 节点做精确替换 |
| **状态持久化** | **`.kani-verify/` 目录 + 原子化写** | 易调试、易回滚；每次写先 `.tmp` + `fsync` + `rename` 防止半状态 |
| **错误处理** | **`thiserror` + `anyhow` 分层** | 库错误用 `thiserror`（强类型），CLI/main 用 `anyhow`（带 context） |
| **序列化** | **`serde` + `serde_json`** | `VerificationReport` 持久化为 `report.json`；`iter-N/*.json` 供后续工具消费 |
| **模板引擎** | **`askama`** | 编译期检查（Jinja-like）；比 `handlebars`/`tinytemplate` 更严格；类型安全 |
| **CLI 解析** | **`clap` v4 derive** | 主流；自动生成 `--help` |
| **配置** | **`figment` + TOML** | 支持默认值 + 文件 + env 三层覆盖；不绑 `config-rs` 私有生态 |
| **测试** | **`cargo test` 单元 + `assert_cmd` 集成** | 行业标准；不引 `insta` 等额外依赖（snapshot 即可） |
| **日志** | **`tracing` + `tracing-subscriber`** | 结构化日志；可观测迭代过程 |

### 6.3 依赖清单 (Cargo.toml)

```toml
[dependencies]
# AST / 代码生成
syn = { version = "2", features = ["full", "extra-traits"] }
quote = "1"
proc-macro2 = "1"
tree-sitter = "0.25"
tree-sitter-rust = "0.23"

# 异步 / 进程
tokio = { version = "1", features = ["process", "io-util", "rt-multi-thread", "macros", "time"] }

# CLI / 配置
clap = { version = "4", features = ["derive", "env"] }
figment = { version = "0.10", features = ["toml", "env"] }

# 序列化
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# 错误处理
thiserror = "1"
anyhow = "1"

# 模板
askama = "0.12"

# 可观测
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter", "json"] }

# 工具
walkdir = "2"
sha2 = "0.10"   # 缓存键
hex = "0.4"

[dev-dependencies]
assert_cmd = "2"
predicates = "3"
tempfile = "3"
```

### 6.4 与外部系统的接口

```
┌─────────────┐     ┌───────────────────────┐     ┌─────────┐
│   OpenCode  │────>│  kani-verify (Rust)   │────>│   Kani  │
│   (用户)    │<────│  single binary        │<────│  (CBMC) │
└─────────────┘     └──────┬────────────────┘     └─────────┘
                           │ (writes .kani-verify/, prompt.txt)
                           v
                    ┌──────────────┐
                    │  任意 LLM    │
                    │  (用户选择)  │
                    └──────┬───────┘
                           │ (user pastes response.txt or --response <file>)
                           v
                    ┌──────────────────────┐
                    │ tree-sitter patch    │
                    │ + re-run Kani        │
                    └──────────────────────┘
```

### 6.5 二进制分发策略

- **开发态**: `cargo run -- verify <args>`
- **分发态**: 
  - 方案 A (推荐): `cargo install kani-verify` → 单一 `kani-verify` 可执行文件放入 `$PATH`
  - 方案 B: 提供预编译 musl binary（避免目标用户装 Rust 工具链）
- **OpenCode 调用**: SKILL.md 中的触发关键词 → OpenCode 调 `kani-verify <subcommand>`

---

## 7. 验收标准 (Acceptance Criteria)

> **v0.2 变更:** AC-1/AC-2 现在要求**自动复现整个 LLM 修复循环**（之前是用户手动粘贴）。为此 skill 在测试中可以使用 mock LLM（固定响应序列），生产环境仍由用户粘贴。

### AC-1: 复现博客 Case A (overflow fix)
- ✅ 输入: `integer_average` 函数源码
- ✅ Skill 用 `syn` 解析出 `fn integer_average(a: i32, b: i32) -> i32`，生成有效 Kani harness（不依赖字符串模板）
- ✅ 运行 Kani 报告 `ArithmeticOverflow` + counterexample `a=2147483647, b=1`
- ✅ 生成的 prompt 包含反例值、失败行上下文、明确"返回完整函数"指令
- ✅ 用户粘贴 LLM 修复 (`num1/2 + num2/2 + (num1%2 + num2%2)/2` 版本) 后，tree-sitter 解析成功，源码替换，再跑 Kani → Success
- ✅ `summary.md` 记录 2 轮迭代的关键 diff

### AC-2: 复现博客 Case B (equivalence + iterative fix)
- ✅ 输入: `lowest_unset_bit_ori` 和 `lowest_unset_bit_opt` 两个函数（指定 `--equivalence`）
- ✅ Skill 生成 equivalence harness (`assert_eq!(ori(x), opt(x))`)
- ✅ 运行 Kani 报告 `ArithmeticOverflow` + `AssertionFailed` (2 of 70)
- ✅ 用户粘贴 LLM 第二版 (`opt_2`) → 1 of 70 失败（只剩 AssertionFailed）
- ✅ 粘贴第三版 (`!x`) → 0 of 68 失败 → Success
- ✅ 总共 3 轮迭代，每轮都原子化写盘

### AC-3: 失败类型分类 (FR-6 覆盖度)
- ✅ 至少能识别并翻译 12 类失败（见 FR-2 的 `FailureKind` 枚举）
- ✅ 每类有独立的 askama 模板片段
- ✅ 单元测试覆盖每类的「Kani 原始消息 → FailureKind 映射」

### AC-4: 迭代状态持久化与恢复
- ✅ 第 N 次迭代可单独查看 `source.rs / harness.rs / report.json / llm-prompt.txt / llm-response.txt`
- ✅ `kani-verify rollback --to 2` 可回滚到指定迭代
- ✅ `kani-verify resume` 可从崩溃中恢复（跳到最后一个有效 manifest）
- ✅ 最终 `summary.md` 包含所有迭代的表格化摘要

### AC-5: 无 LLM 时的回退 (`--no-llm` 模式)
- ✅ `kani-verify verify --no-llm` 只生成 harness + 跑 Kani + 解析报告，不进入迭代循环
- ✅ 用户手动修改源码后，`kani-verify re-verify` 触发重新验证

### AC-6: Rust 实现质量 (v0.2 新增)
- ✅ `cargo test` 全部通过（包括需要 Kani 环境的 e2e 测试用 `--ignored` 标记，CI 默认跳过）
- ✅ `cargo clippy -- -D warnings` 无警告
- ✅ `cargo build --release` 产出单二进制 < 10MB
- ✅ `RUST_LOG=kani_verify=debug kani-verify verify` 输出结构化 JSON 日志

### AC-7: 安全 (v0.2 新增)
- ✅ LLM 响应解析失败（不是合法函数）时，**不**写回源码
- ✅ LLM 响应被识别为包含 `unsafe`、`extern "C"`、`std::process::Command` 等关键词时，触发 warning（不阻断，但要求 `--allow-unsafe-patch`）
- ✅ 临时文件用 `tempfile::TempDir`，离开作用域自动清理

---

## 8. 风险与依赖 (Risks & Dependencies)

### 8.1 依赖
- **Kani Rust Verifier** (外部) — 必须本地安装
- **Rust toolchain** (系统) — 1.70+
- **LLM 访问** (用户) — 任何能接受 prompt 文本的 LLM

### 8.2 风险

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| Kani 版本差异导致 CLI 输出格式变化 | 中 | 在 parser 中维护版本适配表; 文档明确支持的最低版本 |
| Kani 验证时间过长 (CBMC 慢) | 中 | 提示用户使用 `--bounds-check` 缩小范围; 默认 5 分钟超时 |
| LLM 修复引入新 bug | 高 | FR-4 的迭代循环设计就是为了发现这种情况 — 每次修复都重新跑 Kani |
| 用户对 Kani 输出格式不熟悉 | 低 | FR-3 + FR-6 的翻译层让用户无需读原始 Kani 报告 |
| Harness 生成误判函数签名 | 中 | v1 限制在简单签名; 复杂泛型函数给出明确错误而非猜测 |

### 8.3 范围蔓延预警
- ❌ 不做: 自动 commit 到 git
- ❌ 不做: 与 GitHub PR 集成
- ❌ 不做: Kani 之外的形式化验证工具 (Prusti, Creusot, etc.)
- ❌ 不做: 性能基准
- ❌ 不做: 自动 bug 修复 (skill 只生成 prompt，让 LLM 修复)

---

## 9. 开放问题 (Open Questions)

1. **LLM prompt 模板语言**: 英文 (与博客一致) 还是中英双语? 建议英文 — LLM 对英文 prompt 理解更稳定
2. **Kani 安装检测**: 失败时给指引链接还是直接 abort? 建议给链接 + abort
3. **迭代上限**: 默认 5 次合理吗? 博客两个 case 各需 2-3 次; 复杂问题可能需 10+ 次
4. **支持 `#[kani::requires]` / `#[kani::modifies]`**: 这些是 Kani 注解，需要 v1 支持吗? 建议 v2 再考虑
5. **错误信息 i18n**: 失败类型的自然语言翻译是否需要本地化? 建议 v1 仅英文

---

## 10. 实施里程碑 (Milestones)

> **v0.2 变更:** 里程碑从 Python 路径改为 Rust 路径，**全部 Rust 从零开始**（不渐进迁移）。先做核心循环 + 一个 case 跑通端到端。

- **M0 (本文档)**: 需求评审 ✅ 当前
- **M1 (Core Loop + Case A)**: Cargo 项目脚手架 + `syn`/`quote` harness 生成 + Kani 进程包装 + 输出解析（覆盖 6 类失败）+ 最小状态机 + **复现博客 Case A 端到端**（mock LLM）
- **M2 (Iteration + Prompt)**: 完整状态机 + askama prompt 模板 + LLM 响应粘贴 + tree-sitter patch 应用 + 12 类失败完整覆盖 + crash 恢复
- **M3 (Equivalence + Case B)**: `--equivalence` 模式 + 复现博客 Case B 端到端（mock LLM）
- **M4 (Hardening)**: 配置系统 (`figment`)、缓存 (`sha256`)、`--no-llm` 模式、`--dry-run` 模式、`--rollback`、结构化日志、CLI 文档
- **M5 (Release)**: musl 静态二进制、`cargo install`、examples/ 完整可运行、CI 测试矩阵 (Kani 0.50/0.60/0.70)

---

## 附录 A: 来自博客的关键引用

> "The code is actually buggy! Although the average of two `i32` integers is always in the range of `i32`, the intermediate sum `a + b` may overflow."

> "We believe there are two factors that contribute to this unreliability. Firstly, most of the programs in the training corpus of LLMs are unverified programs. Secondly, text prompts can be ambiguous, leading to the production of flawed code."

> "Fortunately, program verifiers such as Kani can provide valuable information about generated code, such as verification results, and counterexamples."

## 附录 B: 后续可能扩展 (Future, Not in v1)

- 多文件/多 crate 项目的 harness 生成
- 与 `cargo-kani` 的深度集成
- 失败模式可视化 (失败类型 → 颜色编码的报告)
- 跨 LLM 对比 (同一 Kani 失败喂给不同模型，对比修复质量)
- 自动从 docstring / spec 提取 `#[kani::requires`] 前置条件
- 与 gstack `/browse` 集成，在 PR 评审时自动跑 Kani

---

## 11. 审计与优化报告 (v0.2 Audit Report)

> 本节是 v0.1 → v0.2 的全部审计结论，按"问题 → 原因 → 修复 → 文档位置"组织。

### 11.1 触发本次审计的需求变更

**变更请求:** 「Python 脚本要更新为 rust 代码脚本」

**根本动因 (Root Cause):**
- skill 处理的目标代码就是 Rust，编排层用 Python 引入不必要的 FFI 边界和工具链异构
- Python 在 AST 处理上能力远弱于 Rust 的 `syn` 生态
- Kani 工具链本身是 Rust，重新发明一遍进程/二进制管理是浪费
- 分发友好：Rust → 单二进制；Python → 需解释器 + 依赖锁定

### 11.2 审计发现一览

| # | 严重度 | 问题 | 位置 | 修复 |
|---|--------|------|------|------|
| A-1 | **高** | 6.1/6.2/10 全文用 Python，与目标语言异构 | §6, §10 | 全文迁移至 Rust；Cargo 单 crate + binary |
| A-2 | **高** | FR-1「字符串模板 + 占位符」无法处理泛型/生命周期/impl Trait | §6.2, FR-1 | 改用 `syn` AST + `quote!`；明确不支持范围（泛型等） |
| A-3 | **高** | NFR-3「原子化」无具体机制 | §5 NFR-3 | FR-4.1 给出 tmp+fsync+rename+manifest 协议 |
| A-4 | **中** | FR-2 数据结构没有 `serde`，无法持久化 | FR-2 | 加 `Serialize/Deserialize`，引入 `serde_json` |
| A-5 | **中** | FR-2 没有 `Verdict::Aborted / ParseError` 状态 | FR-2 | 补全枚举，覆盖 Kani 崩溃、超时、解析失败 |
| A-6 | **中** | FR-2 没有 `FailureKind::UnwindingLimit / Other` 等 | FR-2 | 补全到 12 类（覆盖 Kani 已知所有失败） |
| A-7 | **中** | FR-3 假设 LLM 返回合法函数，无响应解析失败处理 | FR-3 | 新增 FR-3.1 明确接受/拒绝格式 |
| A-8 | **中** | FR-4 状态机用 ASCII 图表达，含糊 | FR-4 | 用 Rust `enum` 表达 + 转换规则 |
| A-9 | **中** | NFR-2 缓存键未定义 | §5 NFR-2 | 明确为 `sha256(source) + sha256(harness) + kani_version + flags` |
| A-10 | **中** | 无安全 NFR | §5 | 新增 NFR-6：禁止执行 LLM 代码、tempfile、路径校验 |
| A-11 | **低** | M1 跨度过大（harness + parser + Case A） | §10 | 拆为 M1 (核心循环) + M2 (迭代/prompt)，M1 必须端到端跑通 Case A |
| A-12 | **低** | NFR-1「零配置启动 + 缺失时给指引」没说 abort 还是降级 | §5 NFR-1 | 明确：缺失 Kani → 给 URL + abort（不静默 PASS） |
| A-13 | **低** | 失败类型表（v0.1 旧 FR-6）只列 6 类，Kani 实际失败类型更多 | FR-6 | FR-2 枚举对齐到 12 类 |
| A-14 | **低** | 验收标准无 Rust 质量门 | §7 | 新增 AC-6 (clippy / size / 日志) + AC-7 (安全) |
| A-15 | **信息** | 模板引擎选型未定 | §6.2 | 选 `askama`（编译期检查） |
| A-16 | **信息** | 6.3 Cargo 依赖未列 | §6 | 补 §6.3 Cargo.toml 草案 |

### 11.3 需求层面未变更但需确认的假设

| 假设 | 状态 | 备注 |
|------|------|------|
| skill 自身是开源/可分发的 | ✅ 保留 | 单 crate + musl binary |
| 用户拥有 LLM 访问 | ✅ 保留 | skill 不绑 API；v0.1 假设用户粘贴 |
| 只支持 macOS/Linux | ✅ 保留 | Kani 自身不支持 Windows |
| v0.1 的"批处理式"定位 | ✅ 保留 | 不做 IDE 内联；保持 CLI 风格 |
| `.agents/skills/kani-verify-skill/` 路径 | ✅ 保留 | 与 skill-center 现有 skill 命名一致 |

### 11.4 审计后新引入的开放问题 (替代 §9 旧问题)

1. **mock LLM 策略**: AC-1/AC-2 用 mock LLM 是单测还是独立 test feature？建议独立 `--features mock-llm`，CI 默认开启
2. **musl 兼容性**: `tree-sitter` C 依赖能否在 musl 下编译？需 M5 验证（可能需要 `*-musl` 特定 build script）
3. **tree-sitter-rust 版本滞后 syn**: 两者 AST 节点不完全对应；FR-3.1 的 patch 解析可能需要宽松匹配（用 `tree-sitter` 做语法定位，再用文本 diff 做内容替换）
4. **askama 模板在哪放**: 选 `templates/` 目录（运行时编译进 binary）还是 inline 在 Rust 代码里（`include_str!`）？建议前者，便于 v0.2 之后用户自定义
5. **缓存目录位置**: `.kani-verify/` 在项目根 vs XDG cache dir (`~/.cache/kani-verify/`）？建议默认项目根（便于审计），可配

### 11.5 v0.2 后的下一步行动

1. **M1 启动前**: 解决 §11.4 第 1、3、4 项开放问题（避免实现中返工）
2. **Cargo.toml 起草**: §6.3 是草案，落地前需 `cargo add` 试装并确认 `tree-sitter-rust` 0.23 与当前 Rust 1.75+ 兼容
3. **SKILL.md 元数据**: OpenCode 触发关键词待定（中英双语候选：中文「用 kani 验证」「kani 检查」；英文「verify with kani」「run kani on」）
4. **参考实现调研**: 是否存在已有的 `cargo-kani` wrapper 或类似工具可借鉴（避免重复发明）
