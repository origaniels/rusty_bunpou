fn main() {
    let mut config = slint_build::CompilerConfiguration::new()
        .with_style("material-dark".into())
        // French UI strings: lang/fr/LC_MESSAGES/bunpo-app.po, msgids without context
        .with_bundled_translations("lang")
        .with_default_translation_context(slint_build::DefaultTranslationContext::None);
    // element debug info lets the headless UI tests (tests/ui.rs) find elements; not needed on device
    let target = std::env::var("TARGET").unwrap_or_default();
    if !target.contains("android") {
        config = config.with_debug_info(true);
    }
    slint_build::compile_with_config("ui/app.slint", config).expect("slint build failed");
}
