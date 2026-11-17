# 文法 SRS — offline Japanese grammar SRS for Android

SRS-style grammar drills (cloze sentences, typed answers, SRS), fully offline.

## Layout
- `pipeline/` — Python: picks example sentences from Tatoeba and builds `content.json`
  - `grammar_n5.py` — grammar points: explanations + token matchers (where the blank goes)
  - `build.py` — filters/scores Tatoeba sentences, writes `data/build/content.json` and copies it into the app assets
- `android/` — Kotlin + Jetpack Compose app (FSRS-5 scheduler, progress in local SQLite)
- `rust/` — native Rust version (Slint UI, no Kotlin)
  - `core/` — platform-independent logic: content, romaji→kana, FSRS, progress (JSON), sessions, furigana layout
  - `app/` — Slint UI (`ui/app.slint`) + glue (`src/lib.rs`), built as `libbunpo_app.so` for a NativeActivity
  - `android/` — minimal Gradle project that packages the library into an APK
- `data/raw/` — Tatoeba exports (CC-BY 2.0 FR), not committed; see `pipeline/fetch_data.sh`

## Rebuild
    cd pipeline && uv venv -p 3.12 .venv && uv pip install -p .venv -r requirements.txt   # once
    ./pipeline/fetch_data.sh                          # once: download Tatoeba exports
    cd pipeline && .venv/bin/python build.py          # regenerate content
    cd android && ./gradlew testDebugUnitTest assembleRelease
    cp android/app/build/outputs/apk/release/app-release.apk bunpo-srs.apk

## Install on the phone
- Copy `bunpo-srs.apk` to the phone and open it (allow "install unknown apps"), or
- USB debugging on: `~/Android/Sdk/platform-tools/adb install -r bunpo-srs.apk`

## Rust version
Needs rustup (`rustup target add aarch64-linux-android x86_64-linux-android`), the Android NDK and `cargo install cargo-ndk`.

    cd rust && cargo test -p bunpo-core                 # core logic tests (host)
    cd rust/android && ./gradlew assembleRelease        # runs ../build-android.sh (cargo ndk) then packages
    # faster iteration for the emulator only:
    cd rust && ./build-android.sh release x86_64 && cd android && ./gradlew assembleRelease -PskipCargo

Notes:
- The answer field keeps exactly what you type; the romaji→kana preview is drawn inside the blank.
  Rewriting the field text would fight the keyboard's composition (Gboard) and garble input.
- `enableOnBackInvokedCallback="false"` in the manifest: with predictive back (Android 16) a NativeActivity
  never receives the Back key.
