# Kani CLI Reference

## Installation

```bash
# Via cargo
cargo install kani-verifier
cargo kani setup

# Via kani-installer (recommended)
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/model-checking/kani/main/scripts/kani-install.sh | sh
```

## Core Commands

### `kani <file.rs>`

Run verification on a Rust file containing `#[kani::proof]` harnesses.

### Key Flags

| Flag | Description |
|------|-------------|
| `--harness <name>` | Verify only a specific harness |
| `-Z unstable-options` | Enable unstable options (required for `--concrete-playback`) |
| `-Z concrete-playback` | Enable concrete playback feature |
| `--concrete-playback=print` | Print concrete counterexamples |
| `--unwind <N>` | Set loop unwinding bound |
| `--unwind <N> --unwind-for-harness <name> <M>` | Per-harness unwind |
| `--cbmc-args <args>` | Pass arguments to CBMC backend |
| `--output-format <pretty\|terse\|json>` | Control output format |
| `--quiet` | Suppress non-error output |

### `kani --version`

Print Kani version.

## Harness Attributes

### `#[kani::proof]`

Marks a function as a verification entry point.

### `#[kani::unwind(N)]`

Sets the loop unwinding bound for this harness. Use when Kani reports "unwinding limit reached".

### `#[kani::requires(expr)]`

Precondition for the harness.

### `#[kani::ensures(expr)]`

Postcondition for the harness.

## Concrete Playback

To get counterexample values:

```bash
kani file.rs --enable-unstable --concrete-playback=print
```

Output format (varies by version):
```
Counterexample: a = 2147483647, b = 1
```

Or in newer versions:
```
Concrete playback: vec!["a = 2147483647", "b = 1"]
```

## Common Failure Messages

| Message | FailureKind | Root Cause |
|---------|-------------|------------|
| `attempt to add with overflow` | ArithmeticOverflow | `+` overflowed |
| `attempt to sub with overflow` | ArithmeticOverflow | `-` overflowed |
| `attempt to mul with overflow` | ArithmeticOverflow | `*` overflowed |
| `attempt to divide by zero` | DivisionByZero | `/` by zero |
| `attempt to remainder by zero` | RemainderByZero | `%` by zero |
| `index out of bounds` | OutOfBounds | Array/Vec index too large |
| `assertion failed` | AssertionFailed | `assert!` or `assert_eq!` |
| `unwrap on None value` | UnwrapOnNone | `.unwrap()` on `None` |
| `unwrap on Err value` | UnwrapOnErr | `.unwrap()` on `Err` |
| `reached unreachable` | Unreachable | `unreachable!()` hit |
| `invalid boolean` | InvalidBool | Bool with non-0/1 value |

## Output Format

Standard output structure:
```
Checking <function_name> in <file>
...

SUMMARY:
 ** X of Y failed
Failed Checks: <message>
 File: "<file>", line <N>, in <function_name>

VERIFICATION:- SUCCESSFUL (or FAILED)
Verification Time: <X>s
```
