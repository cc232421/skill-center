mod error;
mod harness;
mod kani;
mod prompt;
mod report;

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::io::BufRead;
use std::path::{Path, PathBuf};
use std::time::Duration;
use tracing::{info, warn};

#[derive(Parser)]
#[command(name = "kani-verify")]
#[command(about = "Orchestrate Kani verification for Rust code")]
#[command(version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Generate a Kani harness and run verification
    Verify {
        /// Rust source file
        file: PathBuf,

        /// Function name to verify (default: first pub fn)
        #[arg(short, long)]
        function: Option<String>,

        /// Maximum iteration fixes
        #[arg(short, long, default_value_t = 5)]
        max_iterations: u32,

        /// Only generate harness, don't run Kani
        #[arg(long)]
        dry_run: bool,

        /// Just generate the LLM prompt from last failure
        #[arg(long)]
        prompt_only: bool,

        /// Postcondition assertions (repeatable)
        #[arg(short = 'a', long = "assert")]
        postconditions: Vec<String>,
    },

    /// Verify equivalence of two implementations
    Equivalence {
        /// Rust source file
        file: PathBuf,

        /// First function name
        #[arg(long)]
        fn1: String,

        /// Second function name
        #[arg(long)]
        fn2: String,

        /// Maximum iteration fixes
        #[arg(short, long, default_value_t = 5)]
        max_iterations: u32,
    },

    /// Check if Kani is installed and get version
    Check,

    /// Show help for generating LLM prompts
    PromptHelp,
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    let cli = Cli::parse();

    match cli.command {
        Commands::Verify {
            file,
            function,
            max_iterations,
            dry_run,
            prompt_only,
            postconditions,
        } => {
            cmd_verify(
                &file,
                function.as_deref(),
                max_iterations,
                dry_run,
                prompt_only,
                &postconditions,
            )
            .await
        }
        Commands::Equivalence {
            file,
            fn1,
            fn2,
            max_iterations,
        } => cmd_equivalence(&file, &fn1, &fn2, max_iterations).await,
        Commands::Check => cmd_check().await,
        Commands::PromptHelp => cmd_prompt_help(),
    }
}

/// Main verification command.
async fn cmd_verify(
    file: &Path,
    fn_name: Option<&str>,
    max_iterations: u32,
    dry_run: bool,
    prompt_only: bool,
    postconditions: &[String],
) -> Result<()> {
    // Read source
    let source = std::fs::read_to_string(file)
        .with_context(|| format!("Failed to read {}", file.display()))?;

    // Find function name
    let fn_name = match fn_name {
        Some(name) => name.to_string(),
        None => find_first_fn(&source)?,
    };

    info!("Target function: {}", fn_name);

    // Generate harness
    let harness = harness::generate_harness(&source, &fn_name, postconditions)?;

    if dry_run {
        println!("=== Generated Harness ===");
        println!("{}", harness);
        return Ok(());
    }

    // Write harness to temp file
    let tmp_dir = tempfile::tempdir()?;
    let harness_path = tmp_dir.path().join("harness.rs");
    std::fs::write(&harness_path, &harness)?;

    info!("Wrote harness to {}", harness_path.display());

    // Run Kani
    let timeout = Duration::from_secs(300);
    let report = kani::run_kani(&harness_path, timeout, &[]).await?;

    // If prompt_only, just generate the prompt and exit
    if prompt_only {
        if report.status == report::Verdict::Success {
            println!("Verification passing — no prompt needed.");
            return Ok(());
        }
        let prompt = prompt::build_llm_prompt(&report, &source, file, &fn_name)?;
        println!("{}", prompt);
        return Ok(());
    }

    // Print initial result
    print_report(&report, 0);

    if report.status == report::Verdict::Success {
        return Ok(());
    }

    // Iteration loop: generate prompt, wait for user to provide LLM response
    if max_iterations == 0 {
        return Err(error::KaniError::IterationLimitReached(0).into());
    }

    let mut current_source = source.clone();
    let mut iter = 1;

    loop {
        if iter > max_iterations {
            warn!("Reached iteration limit ({})", max_iterations);
            break;
        }

        // Generate LLM prompt
        let llm_prompt = prompt::build_llm_prompt(&report, &current_source, file, &fn_name)?;

        // Write prompt to file for user
        let prompt_path = tmp_dir.path().join(format!("iter-{}-prompt.txt", iter));
        std::fs::write(&prompt_path, &llm_prompt)?;
        info!(
            "LLM prompt written to {} (iteration {}/{})",
            prompt_path.display(),
            iter,
            max_iterations
        );

        // Print prompt to stdout
        println!("\n=== Iteration {} LLM Prompt ===", iter);
        println!("Prompt saved to: {}", prompt_path.display());
        println!("---");
        println!("{}", llm_prompt);
        println!("---");

        // Read LLM response from stdin
        println!("\nPaste the LLM response (complete fixed function) and press Enter:");
        let mut response = String::new();
        let stdin = std::io::stdin();
        stdin.lock().read_line(&mut response)?;
        let response = response.trim();

        if response.is_empty() {
            info!("Empty response, skipping iteration");
            iter += 1;
            continue;
        }

        // Validate response contains a function
        if !response.contains("fn ") {
            warn!("LLM response does not contain a function definition. Skipping.");
            println!("Warning: Response does not contain 'fn '. Skipping this iteration.");
            iter += 1;
            continue;
        }

        // Apply patch: replace the target function in source
        match apply_function_patch(&current_source, &fn_name, response) {
            Ok(new_source) => {
                current_source = new_source;

                // Write updated source
                let updated_path = tmp_dir.path().join(format!("iter-{}-source.rs", iter));
                std::fs::write(&updated_path, &current_source)?;
                info!("Updated source written to {}", updated_path.display());

                // Re-generate harness from updated source
                let new_harness =
                    harness::generate_harness(&current_source, &fn_name, postconditions)?;
                let new_harness_path = tmp_dir.path().join(format!("iter-{}-harness.rs", iter));
                std::fs::write(&new_harness_path, &new_harness)?;

                // Re-run Kani
                let new_report = kani::run_kani(&new_harness_path, timeout, &[]).await?;
                print_report(&new_report, iter);

                if new_report.status == report::Verdict::Success {
                    println!("\nVerification PASSED after {} iterations!", iter);
                    return Ok(());
                }

                // Save LLM response
                let response_path = tmp_dir.path().join(format!("iter-{}-response.txt", iter));
                std::fs::write(&response_path, response)?;

                iter += 1;
            }
            Err(e) => {
                warn!("Failed to apply patch: {}", e);
                println!("Error applying patch: {}. Skipping iteration.", e);
                iter += 1;
            }
        }
    }

    Err(error::KaniError::IterationLimitReached(max_iterations).into())
}

/// Equivalence verification command.
async fn cmd_equivalence(
    file: &Path,
    fn1: &str,
    fn2: &str,
    _max_iterations: u32,
) -> Result<()> {
    let source = std::fs::read_to_string(file)
        .with_context(|| format!("Failed to read {}", file.display()))?;

    // Generate equivalence harness
    let harness = generate_equivalence_harness(&source, fn1, fn2)?;

    let tmp_dir = tempfile::tempdir()?;
    let harness_path = tmp_dir.path().join("equiv_harness.rs");
    std::fs::write(&harness_path, &harness)?;

    info!("Generated equivalence harness for {} vs {}", fn1, fn2);

    let timeout = Duration::from_secs(300);
    let report = kani::run_kani(&harness_path, timeout, &[]).await?;

    println!("=== Equivalence Check: {} vs {} ===", fn1, fn2);
    print_report(&report, 0);

    if report.status == report::Verdict::Success {
        println!("\nEquivalence VERIFIED: {} == {} for all inputs", fn1, fn2);
        return Ok(());
    }

    // For equivalence failures, generate prompt
    let prompt = prompt::build_llm_prompt(&report, &source, file, fn1)?;
    println!("\n=== LLM Prompt for Fix ===");
    println!("{}", prompt);

    Ok(())
}

/// Generate an equivalence harness for two functions.
fn generate_equivalence_harness(source: &str, fn1: &str, fn2: &str) -> Result<String> {
    // Find both functions to get their signatures
    let item1 = harness::find_function(source, fn1)?;
    let item2 = harness::find_function(source, fn2)?;

    let params1 = harness::extract_params(&item1.sig)?;
    let params2 = harness::extract_params(&item2.sig)?;

    // Verify signatures match
    if params1.len() != params2.len() {
        anyhow::bail!(
            "Functions have different parameter counts: {} has {}, {} has {}",
            fn1,
            params1.len(),
            fn2,
            params2.len()
        );
    }

    // Build parameter types for harness
    let param_decls: Vec<String> = params1
        .iter()
        .map(|p| {
            let kani_input = harness::map_type_to_kani_input(&p.ty);
            format!("    let {}: {} = {};", p.name, p.ty, kani_input)
        })
        .collect();

    let call_args: Vec<&str> = params1.iter().map(|p| p.name.as_str()).collect();
    let call_args_str = call_args.join(", ");

    let harness = format!(
        r#"{}

#[kani::proof]
#[kani::unwind(5)]
fn check_equivalence() {{
{}
    assert_eq!({fn1}({call_args}), {fn2}({call_args}));
}}
"#,
        source.trim(),
        param_decls.join("\n"),
        fn1 = fn1,
        fn2 = fn2,
        call_args = call_args_str,
    );

    Ok(harness)
}

/// Check if Kani is installed.
async fn cmd_check() -> Result<()> {
    let output = tokio::process::Command::new("kani")
        .arg("--version")
        .output()
        .await;

    match output {
        Ok(out) if out.status.success() => {
            let version = String::from_utf8_lossy(&out.stdout);
            println!("Kani found: {}", version.trim());
            Ok(())
        }
        Ok(out) => {
            let stderr = String::from_utf8_lossy(&out.stderr);
            anyhow::bail!("Kani check failed: {}", stderr);
        }
        Err(e) => {
            anyhow::bail!(
                "Kani not found. Install: https://model-checking.github.io/kani/install-kani.html\nError: {}",
                e
            );
        }
    }
}

/// Print prompt help.
fn cmd_prompt_help() -> Result<()> {
    println!(
        r#"kani-verify: LLM Prompt Workflow

When verification fails, the tool generates an LLM prompt with:
1. The failing function's source code and line numbers
2. The exact failure type and counterexample
3. A fix hint specific to the failure kind

Workflow:
1. kani-verify verify src.rs --function foo
2. Read the generated prompt
3. Paste the prompt into your LLM (ChatGPT, Claude, etc.)
4. Copy the LLM's response (complete fixed function)
5. Paste it back when prompted
6. Repeat until verification passes

The tool handles the iteration loop automatically."#
    );
    Ok(())
}

/// Find the first function in source.
fn find_first_fn(source: &str) -> Result<String> {
    let file: syn::File = syn::parse_file(source).context("Failed to parse source")?;

    for item in &file.items {
        if let syn::Item::Fn(func) = item {
            return Ok(func.sig.ident.to_string());
        }
    }

    anyhow::bail!("No functions found in source file")
}

/// Apply a function patch by replacing the target function.
fn apply_function_patch(source: &str, fn_name: &str, new_fn: &str) -> Result<String> {
    // Parse to validate the new function is valid
    let _new_item: syn::ItemFn =
        syn::parse_str(new_fn).context("Failed to parse new function")?;

    // Find the function by searching for its signature line
    let lines: Vec<&str> = source.lines().collect();
    let mut fn_start: Option<usize> = None;
    let mut fn_end: Option<usize> = None;
    let mut brace_count = 0;
    let mut in_function = false;

    for (i, line) in lines.iter().enumerate() {
        if !in_function {
            // Look for "fn <fn_name>(" or "fn <fn_name> ("
            let trimmed = line.trim_start();
            if trimmed.starts_with("fn ") || trimmed.starts_with("pub fn ") || trimmed.starts_with("pub(crate) fn ") {
                let _after_fn = trimmed.trim_start_matches(|c: char| c.is_alphabetic() || c == '_' || c == '(' || c == ')');
                if trimmed.contains(&format!("{}(", fn_name)) || trimmed.contains(&format!("{} (", fn_name)) {
                    // Check this isn't just a substring match
                    let fn_call = format!("fn {}(", fn_name);
                    let fn_call_space = format!("fn {} (", fn_name);
                    if trimmed.contains(&fn_call) || trimmed.contains(&fn_call_space) || trimmed.contains(&format!("pub fn {}(", fn_name)) || trimmed.contains(&format!("pub fn {} (", fn_name)) {
                        fn_start = Some(i);
                        in_function = true;
                        // Count braces on this line
                        for c in line.chars() {
                            match c {
                                '{' => brace_count += 1,
                                '}' => brace_count -= 1,
                                _ => {}
                            }
                        }
                        if brace_count == 0 {
                            fn_end = Some(i);
                            in_function = false;
                        }
                    }
                }
            }
        } else {
            // Count braces to find the end of the function
            for c in line.chars() {
                match c {
                    '{' => brace_count += 1,
                    '}' => brace_count -= 1,
                    _ => {}
                }
            }
            if brace_count == 0 {
                fn_end = Some(i);
                break;
            }
        }
    }

    let start = fn_start.context("Function start not found")?;
    let end = fn_end.context("Function end not found (unbalanced braces)")?;

    // Replace the function (including any doc comments/attributes before it)
    let before: String = lines[..start].join("\n");
    let after: String = if end + 1 < lines.len() {
        format!("\n{}", lines[end + 1..].join("\n"))
    } else {
        String::new()
    };

    let new_code = new_fn.trim();

    let mut result = String::new();
    if !before.is_empty() {
        result.push_str(&before);
        result.push('\n');
    }
    result.push_str(new_code);
    result.push_str(&after);

    Ok(result)
}

/// Print verification report in human-readable format.
fn print_report(report: &report::VerificationReport, iteration: u32) {
    println!("\n=== Kani Verification Report (iteration {}) ===", iteration);
    println!("Status: {}", report.status);
    println!("Checks: {} total, {} failed", report.total_checks, report.failed_count);

    if let Some(time) = report.verification_time {
        println!("Time: {:.2}s", time.as_secs_f64());
    }

    for (i, check) in report.failed_checks.iter().enumerate() {
        println!(
            "\n  Failed #{}: {} at {}:{} ({})",
            i + 1,
            check.kind.natural_language(),
            check.file.display(),
            check.line,
            check.function
        );
        if let Some(ce) = &check.counterexample {
            println!("    Counterexample: {}", ce);
        }
        println!("    Fix hint: {}", check.kind.fix_hint());
    }
}
