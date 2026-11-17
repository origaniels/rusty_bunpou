# 文法 SRS — offline Japanese grammar SRS for Android

SRS-style grammar drills (cloze sentences, typed answers, SRS), fully offline.

## Layout
- `pipeline/` — Python: picks example sentences from Tatoeba and builds `content.json`
  - `grammar_n5.py` — grammar points: explanations + token matchers (where the blank goes)
  - `build.py` — filters/scores Tatoeba sentences, writes `data/build/content.json` and copies it into the app assets
- `android/` — Kotlin + Jetpack Compose app (FSRS-5 scheduler, progress in local SQLite)
- `data/raw/` — Tatoeba exports (CC-BY 2.0 FR)

## Rebuild
    cd pipeline && uv venv -p 3.12 .venv && uv pip install -p .venv -r requirements.txt   # once
    ./pipeline/fetch_data.sh                          # once: download Tatoeba exports
    cd pipeline && .venv/bin/python build.py          # regenerate content
    cd android && ./gradlew testDebugUnitTest assembleRelease
    cp android/app/build/outputs/apk/release/app-release.apk bunpo-srs.apk

## Install on the phone
- Copy `bunpo-srs.apk` to the phone and open it (allow "install unknown apps"), or
- USB debugging on: `~/Android/Sdk/platform-tools/adb install -r bunpo-srs.apk`
