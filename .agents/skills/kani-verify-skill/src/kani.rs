use anyhow::{Context, Result};
use std::path::Path;
use std::time::Duration;
use tokio::process::Command;

use crate::error::KaniError;
use crate::report::{ConcreteValues, FailedCheck, FailureKind, VerificationReport, Verdict};

/// Run `kani` on the given file and parse the output.
pub async fn run_kani(
    file: &Path,
    _timeout: Duration,
    extra_args: &[&str],
) -> Result<VerificationReport> {
    let mut cmd = Command::new("kani");
    cmd.arg(file);
    // Use concrete playback to get counterexamples
    cmd.args(["-Z", "unstable-options", "-Z", "concrete-playback"]);
    cmd.args(["--concrete-playback=print"]);
    cmd.args(extra_args);

    let output = cmd
        .output()
        .await
        .context("Failed to execute kani. Is it installed?")?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();
    let combined = format!("{}\n{}", stdout, stderr);

    if !output.status.success() && stdout.is_empty() && stderr.is_empty() {
        return Err(KaniError::KaniExit(output.status.code().unwrap_or(-1)).into());
    }

    parse_kani_output(&combined)
}

/// Parse Kani's text output into a structured report.
pub fn parse_kani_output(output: &str) -> Result<VerificationReport> {
    // Extract verdict
    let status = if output.contains("VERIFICATION:- SUCCESSFUL") {
        Verdict::Success
    } else if output.contains("VERIFICATION:- FAILED") {
        Verdict::Failure
    } else if output.contains("VERIFICATION:- FAILED") || output.contains("SUMMARY:") {
        Verdict::Failure
    } else {
        Verdict::ParseError
    };

    // Extract check counts: "SUMMARY: ** X of Y failed"
    let (failed_count, total_checks) = parse_summary(output).unwrap_or((0, 0));

    // Extract verification time
    let verification_time = parse_verification_time(output);

    // Extract failed checks
    let failed_checks = if status == Verdict::Failure {
        parse_failed_checks(output)
    } else {
        vec![]
    };

    Ok(VerificationReport {
        status,
        failed_checks,
        total_checks,
        failed_count,
        verification_time,
        raw_output: output.to_string(),
    })
}

/// Parse "SUMMARY: ** X of Y failed" — may span two lines.
fn parse_summary(output: &str) -> Option<(u32, u32)> {
    let lines: Vec<&str> = output.lines().collect();
    for (i, line) in lines.iter().enumerate() {
        if line.contains("SUMMARY:") {
            // Check current line and next 2 lines for the pattern
            for j in i..std::cmp::min(i + 3, lines.len()) {
                let check_line = lines[j];
                // Try pattern: "** 0 of 6 failed"
                let parts: Vec<&str> = check_line.split_whitespace().collect();
                // Look for "**" followed by number
                if let Some(star_pos) = parts.iter().position(|&p| p == "**") {
                    if let Some(failed_str) = parts.get(star_pos + 1) {
                        if let Ok(failed) = failed_str.parse::<u32>() {
                            // Look for "of" after the number
                            if let Some(of_pos) = parts.iter().position(|&p| p == "of") {
                                if let Some(total_str) = parts.get(of_pos + 1) {
                                    if let Ok(total) = total_str.parse::<u32>() {
                                        return Some((failed, total));
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    None
}

/// Parse "Verification Time: Xs"
fn parse_verification_time(output: &str) -> Option<Duration> {
    for line in output.lines() {
        if line.contains("Verification Time:") {
            let time_str = line
                .split("Verification Time:")
                .nth(1)?
                .trim()
                .trim_end_matches('s')
                .trim();
            if let Ok(secs) = time_str.parse::<f64>() {
                return Some(Duration::from_secs_f64(secs));
            }
        }
    }
    None
}

/// Parse all "Failed Checks:" blocks.
fn parse_failed_checks(output: &str) -> Vec<FailedCheck> {
    let mut checks = Vec::new();
    let lines: Vec<&str> = output.lines().collect();
    let mut i = 0;

    while i < lines.len() {
        let line = lines[i];
        if line.contains("Failed Checks:") {
            let message = line
                .split("Failed Checks:")
                .nth(1)
                .unwrap_or("")
                .trim()
                .to_string();
            let kind = FailureKind::from_kani_message(&message);

            // Next lines should have "File: ..., line N, in func"
            let mut file = std::path::PathBuf::new();
            let mut line_num = 0;
            let mut function = String::new();

            for j in (i + 1)..std::cmp::min(i + 5, lines.len()) {
                if let Some((f, l, fn_name)) = parse_file_line_func(lines[j]) {
                    file = f;
                    line_num = l;
                    function = fn_name;
                    break;
                }
            }

            // Look for concrete playback counterexample
            let counterexample = find_counterexample_after(output, i);

            checks.push(FailedCheck {
                kind,
                file,
                line: line_num,
                function,
                message,
                counterexample,
            });
        }
        i += 1;
    }

    checks
}

/// Parse "File: "...", line N, in func"
fn parse_file_line_func(line: &str) -> Option<(std::path::PathBuf, u32, String)> {
    if !line.contains("File:") {
        return None;
    }

    let after_file = line.split("File:").nth(1)?.trim();
    // Extract quoted path
    let path_str = if after_file.starts_with('"') {
        after_file.split('"').nth(1)?
    } else {
        after_file.split(',').next()?
    };

    // Extract line number
    let line_num = if let Some(idx) = line.find("line ") {
        let after_line = &line[idx + 5..];
        let num_str: String = after_line.chars().take_while(|c| c.is_ascii_digit()).collect();
        num_str.parse().unwrap_or(0)
    } else {
        0
    };

    // Extract function name
    let function = if let Some(idx) = line.find("in ") {
        let after_in = &line[idx + 3..];
        after_in.trim().to_string()
    } else {
        String::new()
    };

    Some((std::path::PathBuf::from(path_str), line_num, function))
}

/// Search for concrete playback counterexample near a failed check.
fn find_counterexample_after(output: &str, after_line: usize) -> Option<ConcreteValues> {
    let lines: Vec<&str> = output.lines().collect();
    let mut variables = Vec::new();

    for i in after_line..std::cmp::min(after_line + 10, lines.len()) {
        let line = lines[i].trim();
        // Concrete playback lines look like: "2147483647" or "a = 2147483647"
        // The --concrete-playback=print output format varies by Kani version
        // Try to detect numeric values that could be counterexamples
        if !line.is_empty() && !line.contains("File:") && !line.contains("Failed Checks") {
            // Check if line is a bare value (common in concrete playback)
            if line.parse::<i64>().is_ok() {
                variables.push(("input".to_string(), line.to_string()));
            } else if let Some((name, val)) = line.split_once('=') {
                let name = name.trim().to_string();
                let val = val.trim().to_string();
                if !name.is_empty() && !val.is_empty() {
                    variables.push((name, val));
                }
            }
        }
    }

    if variables.is_empty() {
        None
    } else {
        Some(ConcreteValues { variables })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SUCCESS_OUTPUT: &str = r#"
SUMMARY:
 ** 0 of 6 failed

VERIFICATION:- SUCCESSFUL
Verification Time: 0.5309424s
"#;

    const FAILURE_OUTPUT: &str = r#"
SUMMARY:
 ** 1 of 4 failed
Failed Checks: attempt to add with overflow
 File: ".../integer_average.rs", line 2, in integer_average

VERIFICATION:- FAILED
Verification Time: 0.6991158s
"#;

    const FAILURE_MULTI: &str = r#"
SUMMARY:
 ** 2 of 70 failed
Failed Checks: attempt to add with overflow
 File: ".../lowest_unset_bit.rs", line 18, in lowest_unset_bit_opt
Failed Checks: assertion failed: lowest_unset_bit_ori(x) == lowest_unset_bit_opt(x)
 File: ".../lowest_unset_bit.rs", line 26, in check

VERIFICATION:- FAILED
Verification Time: 0.84979576s
"#;

    #[test]
    fn test_parse_success() {
        let report = parse_kani_output(SUCCESS_OUTPUT).unwrap();
        assert_eq!(report.status, Verdict::Success);
        assert_eq!(report.total_checks, 6);
        assert_eq!(report.failed_count, 0);
        assert!(report.failed_checks.is_empty());
    }

    #[test]
    fn test_parse_failure_single() {
        let report = parse_kani_output(FAILURE_OUTPUT).unwrap();
        assert_eq!(report.status, Verdict::Failure);
        assert_eq!(report.failed_count, 1);
        assert_eq!(report.total_checks, 4);
        assert_eq!(report.failed_checks.len(), 1);
        assert_eq!(report.failed_checks[0].kind, FailureKind::ArithmeticOverflow);
    }

    #[test]
    fn test_parse_failure_multi() {
        let report = parse_kani_output(FAILURE_MULTI).unwrap();
        assert_eq!(report.status, Verdict::Failure);
        assert_eq!(report.failed_count, 2);
        assert_eq!(report.total_checks, 70);
        assert_eq!(report.failed_checks.len(), 2);
        assert_eq!(report.failed_checks[0].kind, FailureKind::ArithmeticOverflow);
        assert_eq!(report.failed_checks[1].kind, FailureKind::AssertionFailed);
    }

    #[test]
    fn test_failure_kind_from_message() {
        assert_eq!(
            FailureKind::from_kani_message("attempt to add with overflow"),
            FailureKind::ArithmeticOverflow
        );
        assert_eq!(
            FailureKind::from_kani_message("index out of bounds"),
            FailureKind::OutOfBounds
        );
        assert_eq!(
            FailureKind::from_kani_message("divide by zero"),
            FailureKind::DivisionByZero
        );
        assert_eq!(
            FailureKind::from_kani_message("assertion failed"),
            FailureKind::AssertionFailed
        );
        assert_eq!(
            FailureKind::from_kani_message("unwrap on None value"),
            FailureKind::UnwrapOnNone
        );
    }
}
