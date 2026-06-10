use anyhow::{Context, Result};
use syn::visit::Visit;
use syn::{File, FnArg, ItemFn, Pat, PatType, Signature, Type};

/// Parsed parameter info for harness generation.
pub struct ParamInfo {
    pub name: String,
    pub ty: String,
}

/// Extract the target function from source by name.
pub fn find_function(source: &str, fn_name: &str) -> Result<ItemFn> {
    let file: File = syn::parse_file(source).context("Failed to parse source as Rust code")?;

    struct FnFinder<'a> {
        name: &'a str,
        found: Option<ItemFn>,
    }

    impl<'a> Visit<'a> for FnFinder<'a> {
        fn visit_item_fn(&mut self, node: &'a ItemFn) {
            if node.sig.ident == self.name {
                self.found = Some(node.clone());
            }
        }
    }

    let mut finder = FnFinder {
        name: fn_name,
        found: None,
    };
    finder.visit_file(&file);

    finder
        .found
        .with_context(|| format!("Function '{}' not found in source", fn_name))
}

/// Extract parameter info from a function signature.
pub fn extract_params(sig: &Signature) -> Result<Vec<ParamInfo>> {
    let mut params = Vec::new();

    for input in &sig.inputs {
        match input {
            FnArg::Typed(PatType { pat, ty, .. }) => {
                let name = match pat.as_ref() {
                    Pat::Ident(pat_ident) => pat_ident.ident.to_string(),
                    _ => "_".to_string(),
                };
                let ty_str = type_to_string(ty);
                params.push(ParamInfo { name, ty: ty_str });
            }
            FnArg::Receiver(_) => {
                anyhow::bail!("Methods with `self` parameter are not supported in v1");
            }
        }
    }

    Ok(params)
}

/// Convert a syn Type to string for mapping.
fn type_to_string(ty: &Type) -> String {
    quote::quote!(#ty).to_string()
}

/// Map a Rust type to the corresponding kani::any() call.
pub fn map_type_to_kani_input(ty_str: &str) -> String {
    match ty_str {
        // Primitive scalars
        "i8" | "i16" | "i32" | "i64" | "i128" | "isize" | "u8" | "u16" | "u32" | "u64" | "u128"
        | "usize" | "bool" | "f32" | "f64" | "char" => {
            format!("kani::any::<{}>()", ty_str)
        }
        // Option<T>
        s if s.starts_with("Option <") || s.starts_with("Option<") => {
            format!("kani::any::<{}>()", s)
        }
        // Result<T, E>
        s if s.starts_with("Result <") || s.starts_with("Result<") => {
            format!("kani::any::<{}>()", s)
        }
        // Tuples
        s if s.starts_with('(') => {
            format!("kani::any::<{}>()", s)
        }
        // Vectors
        s if s.contains("Vec <") || s.contains("Vec<") => {
            format!("kani::any::<{}>()", s)
        }
        // Slices &[T]
        s if s.starts_with("& [") || s.starts_with("&[") => {
            // For slices, we create a Vec and take a reference
            let inner = extract_slice_inner(s);
            format!("kani::any::<Vec<{}>>().as_slice()", inner)
        }
        // &str
        "& str" | "&str" => "kani::any::<String>().as_str()".to_string(),
        // Fallback: assume kani::Arbitrary is implemented
        s => {
            format!("kani::any::<{}>()", s)
        }
    }
}

/// Extract the inner type from a slice type string like "&[T]" or "& [T]".
fn extract_slice_inner(s: &str) -> String {
    let s = s.trim_start_matches('&').trim();
    let s = s.trim_start_matches('[').trim_end_matches(']').trim();
    s.to_string()
}

/// Check if a return type contains Result.
pub fn returns_result(sig: &Signature) -> bool {
    match &sig.output {
        syn::ReturnType::Default => false,
        syn::ReturnType::Type(_, ty) => {
            let ty_str = type_to_string(ty);
            ty_str.contains("Result")
        }
    }
}

/// Generate the complete harness source code.
pub fn generate_harness(source: &str, fn_name: &str, postconditions: &[String]) -> Result<String> {
    let item_fn = find_function(source, fn_name)?;
    let params = extract_params(&item_fn.sig)?;
    let has_result = returns_result(&item_fn.sig);

    // Build parameter declarations for harness
    let param_decls: Vec<String> = params
        .iter()
        .map(|p| {
            let kani_input = map_type_to_kani_input(&p.ty);
            format!("    let {}: {} = {};", p.name, p.ty, kani_input)
        })
        .collect();

    // Build function call arguments
    let call_args: Vec<&str> = params.iter().map(|p| p.name.as_str()).collect();
    let call_args_str = call_args.join(", ");

    // Build the harness body
    let mut body = String::new();
    body.push_str("#[kani::proof]\n");
    body.push_str("#[kani::unwind(5)]\n");
    body.push_str(&format!("fn verify_{}() {{\n", fn_name));

    for decl in &param_decls {
        body.push_str(decl);
        body.push('\n');
    }

    if has_result {
        body.push_str(&format!("    let _ = {}({})?;\n", fn_name, call_args_str));
    } else {
        body.push_str(&format!("    let _ = {}({});\n", fn_name, call_args_str));
    }

    // Add postconditions
    for assertion in postconditions {
        body.push_str(&format!("    {};\n", assertion));
    }

    body.push_str("}\n");

    // Prepend the original function (preserving imports)
    Ok(format!("{}\n{}", source.trim(), body))
}

#[cfg(test)]
mod tests {
    use super::*;

    const SIMPLE_SOURCE: &str = r#"
fn integer_average(a: i32, b: i32) -> i32 {
    (a + b) / 2
}
"#;

    #[test]
    fn test_find_function() {
        let item_fn = find_function(SIMPLE_SOURCE, "integer_average").unwrap();
        assert_eq!(item_fn.sig.ident, "integer_average");
        assert_eq!(item_fn.sig.inputs.len(), 2);
    }

    #[test]
    fn test_find_function_not_found() {
        let result = find_function(SIMPLE_SOURCE, "nonexistent");
        assert!(result.is_err());
    }

    #[test]
    fn test_extract_params() {
        let item_fn = find_function(SIMPLE_SOURCE, "integer_average").unwrap();
        let params = extract_params(&item_fn.sig).unwrap();
        assert_eq!(params.len(), 2);
        assert_eq!(params[0].name, "a");
        assert_eq!(params[0].ty, "i32");
        assert_eq!(params[1].name, "b");
        assert_eq!(params[1].ty, "i32");
    }

    #[test]
    fn test_map_type_to_kani_input() {
        assert_eq!(map_type_to_kani_input("i32"), "kani::any::<i32>()");
        assert_eq!(map_type_to_kani_input("u32"), "kani::any::<u32>()");
        assert_eq!(map_type_to_kani_input("bool"), "kani::any::<bool>()");
        assert_eq!(
            map_type_to_kani_input("Option < i32 >"),
            "kani::any::<Option < i32 >>()"
        );
    }

    #[test]
    fn test_returns_result() {
        let source = "fn foo() -> Result<i32, String> { Ok(0) }";
        let item_fn = find_function(source, "foo").unwrap();
        assert!(returns_result(&item_fn.sig));

        let source2 = "fn bar() -> i32 { 0 }";
        let item_fn2 = find_function(source2, "bar").unwrap();
        assert!(!returns_result(&item_fn2.sig));
    }

    #[test]
    fn test_generate_harness() {
        let harness = generate_harness(SIMPLE_SOURCE, "integer_average", &[]).unwrap();
        assert!(harness.contains("fn integer_average(a: i32, b: i32) -> i32"));
        assert!(harness.contains("#[kani::proof]"));
        assert!(harness.contains("kani::any::<i32>()"));
        assert!(harness.contains("let _ = integer_average(a, b);"));
    }

    #[test]
    fn test_generate_harness_with_postcondition() {
        let harness = generate_harness(
            SIMPLE_SOURCE,
            "integer_average",
            &["assert!(result >= 0)".to_string()],
        )
        .unwrap();
        assert!(harness.contains("assert!(result >= 0)"));
    }
}
