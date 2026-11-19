fn main() {
    let config = slint_build::CompilerConfiguration::new()
        .with_style("material-dark".into())
        // French UI strings: lang/fr/LC_MESSAGES/bunpo-app.po, msgids without context
        .with_bundled_translations("lang")
        .with_default_translation_context(slint_build::DefaultTranslationContext::None)
        // element debug info lets the layout audit find elements: in the headless UI tests
        // (tests/ui.rs) and on the device, for the emulator end-to-end tests (src/audit.rs)
        .with_debug_info(true);
    slint_build::compile_with_config("ui/app.slint", config).expect("slint build failed");
}
