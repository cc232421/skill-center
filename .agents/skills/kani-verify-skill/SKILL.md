---
name: kani-verify
description: >-
  Verify Rust code properties using Kani — formal verification for panic-freedom,
  overflow safety, and functional equivalence. Use this skill when: the user asks
  to "verify", "check", or "prove" properties of Rust code; wants to find bugs in
  LLM-generated Rust code; asks to prove two implementations are equivalent; asks
  "will this panic?", "is this safe?", "does this overflow?"; or wants to use
  Kani on any Rust function. Also use when user pastes Rust code and asks for
  safety analysis. Do NOT use for general Rust review (use code-review skills instead).
---

# Kani Verify Skill

Orchestrate Kani formal verification for Rust code through a guided workflow.

## When to Use

- User asks to verify, check, or prove properties of Rust code
- User has LLM-generated Rust code they don't trust
- User asks to prove two implementations are equivalent
- User asks "will this panic?" or "is this safe?"
- User mentions "kani", "formal verification", "model checking"

## Prerequisites

Before running verification, confirm Kani is installed:

```bash
kani-verify check
```

If not installed, direct user to: https://model-checking.github.io/kani/install-kani.html

## Workflow

### Step 1: Verify a Function (Single Implementation)

```bash
kani-verify verify <file.rs> --function <fn_name>
```

- If `--function` is omitted, the first `fn` in the file is used
- Add `--assert "condition"` for postconditions (repeatable)
- Add `--max-iterations N` to control fix attempts (default: 5)

**What happens:**
1. Generates a Kani proof harness from the function signature
2. Runs `kani` on the harness
3. Reports pass/fail with failure details

### Step 2: If Verification Fails

When verification fails, the tool generates an LLM prompt containing:
- The exact failure type and location
- Counterexample input values (when available)
- Fix hints specific to the failure kind

**Manual workflow:**
1. Read the prompt from stdout (or the saved file)
2. Paste it into your LLM (Claude, ChatGPT, etc.)
3. Copy the LLM's response (complete fixed function)
4. Paste it back when prompted

### Step 3: Verify Equivalence

To prove two implementations produce the same output for all inputs:

```bash
kani-verify equivalence <file.rs> --fn1 <name1> --fn2 <name2>
```

This generates a harness that asserts `fn1(args) == fn2(args)` for all valid inputs.

## Failure Types and Fix Hints

| Failure | What It Means | How to Fix |
|---------|---------------|------------|
| Arithmetic overflow | `+`, `-`, `*`, or `<<` overflowed | Use `checked_add`, `saturating_add`, `wrapping_add` |
| Division by zero | Divide or modulo by zero | Add zero-check before the operation |
| Index out of bounds | Array/Vec index exceeded length | Use `.get()` instead of `[]` |
| Assertion failed | A postcondition or `assert!` was violated | Fix the assertion or the code |
| Option::unwrap on None | Called `.unwrap()` on a `None` | Use `match`, `if let`, or `unwrap_or` |
| Result::unwrap on Err | Called `.unwrap()` on an `Err` | Use `?` or `match` to handle errors |

## Tool Interface

The `kani-verify` binary provides these commands:

```
kani-verify check                          # Verify Kani is installed
kani-verify verify <file> [options]        # Run verification
kani-verify equiv <file> --fn1 a --fn2 b   # Equivalence check
kani-verify prompt-help                    # Show LLM prompt workflow
```

### Verify Options

| Flag | Description |
|------|-------------|
| `-f, --function <name>` | Target function (default: first fn) |
| `-a, --assert <expr>` | Postcondition assertion (repeatable) |
| `-m, --max-iterations <N>` | Max fix iterations (default: 5) |
| `--dry-run` | Generate harness only, don't run Kani |
| `--prompt-only` | Generate LLM prompt from last failure |

## Examples

### Example 1: Basic overflow detection

```rust
fn integer_average(a: i32, b: i32) -> i32 {
    (a + b) / 2
}
```

Run: `kani-verify verify source.rs --function integer_average`

Result: FAIL — "attempt to add with overflow" when `a = i32::MAX`

### Example 2: Prove equivalence

Given `fn1` (loop-based) and `fn2` (bit-twiddling), prove they return the same result:

```bash
kani-verify equivalence source.rs --fn1 lowest_unset_bit_ori --fn2 lowest_unset_bit_opt
```

## Output Directory

All iteration artifacts are saved to `.kani-verify/` in the current directory:
- `iter-N/source.rs` — source after Nth fix
- `iter-N/harness.rs` — generated harness
- `iter-N/report.json` — structured verification report
- `iter-N/llm-prompt.txt` — prompt for the LLM
- `iter-N/llm-response.txt` — LLM's response
- `summary.md` — final human-readable summary

## Limitations (v0.1)

- No support for generic functions (`<T>`)
- No support for methods with `self` parameter
- Complex type signatures may need manual harness adjustment
- Kani verification time scales with code complexity (may timeout on large functions)
