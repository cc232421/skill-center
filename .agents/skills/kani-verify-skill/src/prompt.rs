use anyhow::Result;
use std::path::Path;

use crate::report::{FailedCheck, VerificationReport};

/// Build an LLM prompt from a failed verification report.
pub fn build_llm_prompt(
    report: &VerificationReport,
    source: &str,
    source_path: &Path,
    fn_name: &str,
) -> Result<String> {
    if report.status == crate::report::Verdict::Success {
        return Ok("Verification already passing — no LLM prompt needed.".to_string());
    }

    let mut prompt = String::new();

    // Header
    prompt.push_str(&format!(
        "Kani verification failed for `{}` in {}.\n\n",
        fn_name,
        source_path.display()
    ));

    // Summary
    prompt.push_str(&format!(
        "Result: {} ({} of {} checks failed)\n\n",
        report.status, report.failed_count, report.total_checks
    ));

    // List all failures
    prompt.push_str("Failures:\n");
    for (i, check) in report.failed_checks.iter().enumerate() {
        prompt.push_str(&format!(
            "{}. Line {} in `{}`: {} — {}\n",
            i + 1,
            check.line,
            check.function,
            check.kind.natural_language(),
            check.message
        ));

        // Show source context around the failed line
        if let Some(ctx) = source_context(source, check) {
            prompt.push_str(&format!("   {}\n", ctx));
        }

        // Show counterexample if available (only for the first failure)
        if i == 0 {
            if let Some(ce) = &check.counterexample {
                prompt.push_str(&format!("   Counterexample: {}\n", ce));
            }
        }

        // Show fix hint
        prompt.push_str(&format!("   Hint: {}\n", check.kind.fix_hint()));
    }

    // Instruction
    prompt.push_str(
        "\nPlease provide a fix that handles all inputs without any of the above failures.\n",
    );
    prompt.push_str("Return ONLY the complete fixed function (no explanations, no markdown).\n");
    prompt.push_str(&format!(
        "The function signature must remain: `fn {}(...)`.\n",
        fn_name
    ));

    // Postconditions reminder
    prompt.push_str("Do not change the function's behavior — only fix the safety issues.\n");

    Ok(prompt)
}

/// Extract source context around a failed check line.
fn source_context(source: &str, check: &FailedCheck) -> Option<String> {
    let lines: Vec<&str> = source.lines().collect();
    let target = check.line as usize;

    if target == 0 || target > lines.len() {
        return None;
    }

    let start = target.saturating_sub(2);
    let end = std::cmp::min(target + 1, lines.len());

    let mut ctx = String::new();
    for i in start..end {
        let marker = if i + 1 == target { ">>>" } else { "   " };
        ctx.push_str(&format!("{} L{}: {}\n", marker, i + 1, lines[i]));
    }

    Some(ctx.trim_end().to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::report::{FailureKind, Verdict};
    use std::path::PathBuf;

    fn make_report(failed: Vec<FailedCheck>) -> VerificationReport {
        let failed_count = failed.len() as u32;
        VerificationReport {
            status: if failed.is_empty() {
                Verdict::Success
            } else {
                Verdict::Failure
            },
            failed_checks: failed,
            total_checks: 10,
            failed_count,
            verification_time: None,
            raw_output: String::new(),
        }
    }

    #[test]
    fn test_build_prompt_for_success() {
        let report = make_report(vec![]);
        let prompt = build_llm_prompt(&report, "", Path::new("test.rs"), "foo").unwrap();
        assert!(prompt.contains("already passing"));
    }

    #[test]
    fn test_build_prompt_for_failure() {
        let report = make_report(vec![FailedCheck {
            kind: FailureKind::ArithmeticOverflow,
            file: PathBuf::from("test.rs"),
            line: 2,
            function: "add".to_string(),
            message: "attempt to add with overflow".to_string(),
            counterexample: None,
        }]);

        let source = "fn add(a: i32, b: i32) -> i32 {\n    (a + b) / 2\n}\n";
        let prompt = build_llm_prompt(&report, source, Path::new("test.rs"), "add").unwrap();

        assert!(prompt.contains("attempt to add with overflow"));
        assert!(prompt.contains("Return ONLY the complete fixed function"));
        assert!(prompt.contains("arithmetic overflow"));
        assert!(prompt.contains("checked_add"));
    }

    #[test]
    fn test_source_context() {
        let source = "fn foo() {\n    let x = 1;\n    let y = x + 2;\n}\n";
        let check = FailedCheck {
            kind: FailureKind::ArithmeticOverflow,
            file: PathBuf::from("test.rs"),
            line: 3,
            function: "foo".to_string(),
            message: String::new(),
            counterexample: None,
        };

        let ctx = source_context(source, &check).unwrap();
        assert!(ctx.contains(">>> L3:"));
        assert!(ctx.contains("let y = x + 2;"));
    }
}
