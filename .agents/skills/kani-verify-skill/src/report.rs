use serde::{Deserialize, Serialize};
use std::fmt;
use std::path::PathBuf;
use std::time::Duration;

// ── Verdict ──

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Verdict {
    Success,
    Failure,
    Aborted,
    ParseError,
}

impl fmt::Display for Verdict {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Verdict::Success => write!(f, "SUCCESSFUL"),
            Verdict::Failure => write!(f, "FAILED"),
            Verdict::Aborted => write!(f, "ABORTED"),
            Verdict::ParseError => write!(f, "PARSE_ERROR"),
        }
    }
}

// ── FailureKind (FR-6) ──

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum FailureKind {
    ArithmeticOverflow,
    ArithmeticUnderflow,
    DivisionByZero,
    OutOfBounds,
    RemainderByZero,
    AssertionFailed,
    UnwrapOnNone,
    UnwrapOnErr,
    Unreachable,
    InvalidBool,
    PointerOverflow,
    NullPointer,
    ArithmeticShift,
    UnwindingLimit,
    Other(String),
}

impl FailureKind {
    pub fn from_kani_message(msg: &str) -> Self {
        if msg.contains("add with overflow") || msg.contains("sub with overflow") {
            Self::ArithmeticOverflow
        } else if msg.contains("mul with overflow") {
            Self::ArithmeticOverflow
        } else if msg.contains("divide by zero") {
            Self::DivisionByZero
        } else if msg.contains("index out of bounds") {
            Self::OutOfBounds
        } else if msg.contains("remainder by zero") {
            Self::RemainderByZero
        } else if msg.contains("assertion failed") {
            Self::AssertionFailed
        } else if msg.contains("unwrap on None") {
            Self::UnwrapOnNone
        } else if msg.contains("unwrap on Err") {
            Self::UnwrapOnErr
        } else if msg.contains("reached unreachable") {
            Self::Unreachable
        } else if msg.contains("invalid boolean") {
            Self::InvalidBool
        } else if msg.contains("pointer overflow") {
            Self::PointerOverflow
        } else if msg.contains("null pointer") {
            Self::NullPointer
        } else if msg.contains("shift overflow") || msg.contains("arithmetic shift") {
            Self::ArithmeticShift
        } else {
            Self::Other(msg.to_string())
        }
    }

    pub fn natural_language(&self) -> &str {
        match self {
            Self::ArithmeticOverflow => "arithmetic overflow",
            Self::ArithmeticUnderflow => "arithmetic underflow",
            Self::DivisionByZero => "division by zero",
            Self::OutOfBounds => "array/Vec index out of bounds",
            Self::RemainderByZero => "remainder by zero",
            Self::AssertionFailed => "assertion failed",
            Self::UnwrapOnNone => "Option::unwrap on None value",
            Self::UnwrapOnErr => "Result::unwrap on Err value",
            Self::Unreachable => "reached unreachable code",
            Self::InvalidBool => "invalid boolean value",
            Self::PointerOverflow => "pointer overflow",
            Self::NullPointer => "null pointer dereference",
            Self::ArithmeticShift => "arithmetic shift overflow",
            Self::UnwindingLimit => "unwinding limit reached",
            Self::Other(_) => "unknown failure",
        }
    }

    pub fn fix_hint(&self) -> &str {
        match self {
            Self::ArithmeticOverflow | Self::ArithmeticUnderflow => {
                "Use `checked_add`/`checked_sub`/`saturating_add`/`wrapping_add`, or widen the type."
            }
            Self::DivisionByZero => "Add a check for zero before dividing.",
            Self::OutOfBounds => "Use `.get()` instead of `[]`, or add a bounds check.",
            Self::RemainderByZero => "Add a check for zero before the modulo operation.",
            Self::AssertionFailed => "Fix the assertion condition or the code that violates it.",
            Self::UnwrapOnNone => "Use `match`, `if let`, or `unwrap_or` instead of `unwrap()`.",
            Self::UnwrapOnErr => "Use `?` operator or `match` to handle the error.",
            Self::Unreachable => "Remove or fix the unreachable code path.",
            Self::InvalidBool => "Ensure the value is exactly 0 or 1.",
            Self::PointerOverflow => "Check pointer arithmetic bounds.",
            Self::NullPointer => "Add a null check before dereferencing.",
            Self::ArithmeticShift => "Ensure shift amount is within the type's bit width.",
            Self::UnwindingLimit => "Increase the unwind bound with `#[kani::unwind(N)]`.",
            Self::Other(_) => "Review the code at the indicated location.",
        }
    }
}

// ── FailedCheck ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FailedCheck {
    pub kind: FailureKind,
    pub file: PathBuf,
    pub line: u32,
    pub function: String,
    pub message: String,
    pub counterexample: Option<ConcreteValues>,
}

// ── ConcreteValues ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConcreteValues {
    pub variables: Vec<(String, String)>,
}

impl fmt::Display for ConcreteValues {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let parts: Vec<String> = self
            .variables
            .iter()
            .map(|(name, val)| format!("{} = {}", name, val))
            .collect();
        write!(f, "{}", parts.join(", "))
    }
}

// ── VerificationReport (FR-2) ──

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerificationReport {
    pub status: Verdict,
    pub failed_checks: Vec<FailedCheck>,
    pub total_checks: u32,
    pub failed_count: u32,
    pub verification_time: Option<Duration>,
    pub raw_output: String,
}
