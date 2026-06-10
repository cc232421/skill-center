use std::path::PathBuf;
use thiserror::Error;

#[derive(Error, Debug)]
#[allow(dead_code)]
pub enum KaniError {
    #[error("Kani not found. Install: https://model-checking.github.io/kani/install-kani.html")]
    KaniNotFound,

    #[error("Kani version {found} not supported (need >= {min})")]
    KaniVersionUnsupported { found: String, min: String },

    #[error("Source file not found: {0}")]
    SourceNotFound(PathBuf),

    #[error("Function '{0}' not found in {1}")]
    FunctionNotFound(String, PathBuf),

    #[error("Function signature not supported in v1: {0}")]
    UnsupportedSignature(String),

    #[error("Kani timed out after {0:?}")]
    KaniTimeout(std::time::Duration),

    #[error("Kani process exited with code {0}")]
    KaniExit(i32),

    #[error("Kani produced no output")]
    KaniNoOutput,

    #[error("Failed to parse Kani output: {0}")]
    ParseError(String),

    #[error("LLM response does not contain a valid function: {0}")]
    InvalidLLMResponse(String),

    #[error("Iteration limit reached ({0}) without passing verification")]
    IterationLimitReached(u32),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}
