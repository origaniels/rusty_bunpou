# 文法 SRS — offline Japanese grammar SRS for Android

SRS-style grammar drills (cloze sentences, typed answers, spaced repetition), fully offline,
written in Rust (logic + Slint UI). The only Java is a small notification receiver.

## Layout
- `pipeline/` — Python: picks example sentences from Tatoeba and builds `data/build/content.json`
  - `grammar_n5.py` — grammar points: explanations + token matchers (where the blank goes)
  - `build.py` — filters/scores Tatoeba sentences, writes the content file (embedded into the app at compile time)
  - `tests/` — pytest suite for matchers, readings, furigana, answers
- `rust/core/` — platform-independent logic: content, romaji→kana, FSRS + learning steps, progress (JSON),
  quiz sessions, review reminders, furigana line layout. `tests/` has integration tests incl. SRS simulations.
- `rust/app/` — Slint UI (`ui/app.slint`) + glue (`src/lib.rs`, `src/android.rs`); `tests/ui.rs` drives the
  real UI headlessly through Slint's testing backend
- `rust/android/` — Gradle project packaging `libbunpo_app.so` + `ReviewReminder.java` into an APK
- `rust/e2e/run.sh` — end-to-end test on the emulator (time travel via the emulator clock)
- `rust/third_party/i-slint-core/` — Slint core with one fix (`../i-slint-core-cancel.patch`):
  a cancelled touch (Android back gesture) must not count as a tap
- `data/raw/` — Tatoeba exports (CC-BY 2.0 FR), not committed; see `pipeline/fetch_data.sh`

## Scheduling
New points go through fixed learning steps 4h → 8h → 1d → 3d, then FSRS-5 (target retention configurable,
interval growth capped at 3× per review, max 1 year). A mistake on a learned point: retry after 1h, then
1d → 3d → back to FSRS. See it with `cd rust && cargo run -p bunpo-core --example simulate`.

## Build
    # once
    cd pipeline && uv venv -p 3.12 .venv && uv pip install -p .venv -r requirements.txt && ./fetch_data.sh
    rustup target add aarch64-linux-android x86_64-linux-android && cargo install cargo-ndk   # + Android SDK/NDK

    pipeline/.venv/bin/python pipeline/build.py           # regenerate content
    cd rust/android && ./gradlew assembleRelease          # APK (runs cargo ndk for arm64 + x86_64)

## Tests
    ./test-all.sh            # pytest + cargo test (core, SRS simulations, headless UI)
    ./test-all.sh --e2e      # + emulator end-to-end (AVD must be running)

## Install on the phone
Copy the APK to the phone and open it, or `adb install -r rust/android/app/build/outputs/apk/release/app-release.apk`.

## Notes
- The answer field keeps exactly what you type; the romaji→kana preview is drawn inside the blank.
  Rewriting the field text would fight the keyboard's composition (Gboard) and garble input.
- `enableOnBackInvokedCallback="false"`: with predictive back (Android 16) a NativeActivity never gets the Back key.
- Reminders use AlarmManager with a 10-minute window (no exact-alarm permission). Force-stopping the app in
  Android settings cancels them until the app is opened again (Android behaviour).
