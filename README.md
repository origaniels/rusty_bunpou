# 文法 SRS — offline Japanese grammar SRS for Android

SRS-style grammar drills (cloze sentences, typed answers, spaced repetition), fully offline,
written in Rust (logic + Slint UI). Java only where Android needs an Activity: reminders, file picker,
dictionary lookup, vibration.

How the app works, feature by feature, and how to change it: [APP.md](APP.md). Tests: [TESTING.md](TESTING.md).

The whole app can be used in **English or French** (Settings → Language): interface, grammar explanations
and sentence translations. Lessons can start at any JLPT level (Settings → Start lessons at).

## Layout
- `pipeline/` — Python: picks example sentences from Tatoeba and builds `data/build/content.json`
  - `grammar_n5.py` — grammar points: explanations + token matchers (where the blank goes)
  - `build.py` — filters/scores Tatoeba sentences (preferring ones with a French translation), writes the
    content file (embedded into the app at compile time)
  - `fr/` — French: grammar point texts (`points_n*.py`) and translations of the sentences Tatoeba has no
    French for (`sentences_n*.tsv`, each tied to the Japanese it translates)
  - `tests/` — pytest suite for matchers, readings, furigana, answers
- `rust/core/` — platform-independent logic: content, romaji→kana, FSRS + learning steps, progress (JSON),
  quiz sessions, review reminders, furigana line layout. `tests/` has integration tests incl. SRS simulations.
- `rust/app/` — Slint UI (`ui/app.slint`) + glue (`src/lib.rs`, `src/android.rs`); `tests/ui.rs` drives the
  real UI headlessly through Slint's testing backend. Interface strings are marked `@tr` and translated in
  `lang/fr/LC_MESSAGES/bunpo-app.po`
- `rust/android/` — Gradle project packaging `libbunpo_app.so` + the Java helpers into an APK
- `rust/e2e/` — emulator tests: a two-week scenario with time travel (`run.sh`), a layout tour of every
  screen (`tour.sh`), real-device flows (`flows.sh`) and a crawler that taps every button (`crawl.sh`)
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
    ./test-all.sh --e2e      # + emulator tests (AVD must be running)
    ./test-all.sh --e2e-full # + the button crawler

See [TESTING.md](TESTING.md) for what each suite covers.

## Install on the phone
Copy the APK to the phone and open it, or `adb install -r rust/android/app/build/outputs/apk/release/app-release.apk`.

## Releases
    ./release.sh 0.4.0 "What changed" --dry-run   # tests, build, checks; nothing published
    ./release.sh 0.4.0 "What changed"             # then commit, tag, push, GitHub release + APK

Release builds check GitHub once a day for a newer release (if the user agrees) and offer to
download it. Add `--pre` for a test build that the app doesn't offer.

## Notes
- The answer field keeps exactly what you type; the romaji→kana preview is drawn inside the blank.
  Rewriting the field text would fight the keyboard's composition (Gboard) and garble input.
- `enableOnBackInvokedCallback="false"`: with predictive back (Android 16) a NativeActivity never gets the Back key.
- Reminders use AlarmManager with a 10-minute window (no exact-alarm permission). Force-stopping the app in
  Android settings cancels them until the app is opened again (Android behaviour).

## License
- **Code** (everything in this repository except the content described below): GNU General Public License v3.0
  or later — see [LICENSE](LICENSE).
- **Slint** (UI toolkit) is used under its GPL-3.0 option; `rust/third_party/i-slint-core` is a modified copy of
  Slint's core crate (see `rust/third_party/i-slint-core-cancel.patch`) and keeps its original licensing.
- **Example sentences from Tatoeba** (<https://tatoeba.org>) and their English and French translations are
  licensed CC-BY 2.0 FR by their contributors; the app shows each sentence's Tatoeba number and contributor
  and, in French, the number and contributor of the French translation.
- **Grammar explanations (English and French), the example sentences in `pipeline/extra_examples.py` and the
  French translations in `pipeline/fr/sentences_*.tsv`** were written for this project; all rights reserved
  for now. Translations of Tatoeba sentences are marked as written for this app and still credit the original
  Japanese sentence.
