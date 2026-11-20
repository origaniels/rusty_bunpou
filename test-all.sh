#!/bin/bash
# Run every test suite. Pass --e2e to also run the emulator tests (needs a running AVD), or
# --e2e-full to add the button crawler (every button on every screen, ~15 more minutes).
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.cargo/bin:$PATH"

echo "### pipeline (pytest)"
pipeline/.venv/bin/python -m pytest -q pipeline/tests

echo "### core + UI (cargo test)"
(cd rust && cargo test -q 2>&1 | grep -E "test result|FAILED|panicked" )
(cd rust && cargo test -q >/dev/null 2>&1) || { echo "cargo tests failed"; exit 1; }

if [[ "${1:-}" == --e2e* ]]; then
  echo "### android (emulator): build"
  (cd rust && ./build-android.sh release x86_64 >/dev/null && cd android && ./gradlew assembleRelease -PskipCargo -q)
  echo "### android e2e: lessons, reviews and reminders over 2 weeks"
  rust/e2e/run.sh
  echo "### android e2e, in French"
  E2E_LANG=fr rust/e2e/run.sh
  echo "### android layout tour (every screen, audited on the device)"
  rust/e2e/tour.sh "" en
  rust/e2e/tour.sh "" fr
  echo "### android layout tour with the phone's largest font size"
  FONT_SCALE=1.3 rust/e2e/tour.sh "" fr
  echo "### android flows (app killed mid-review, Japanese keyboard)"
  rust/e2e/flows.sh
  if [[ "$1" == "--e2e-full" ]]; then
    echo "### android crawl: every button on every screen, tapped for real"
    rust/e2e/crawl.sh "" en
  fi
fi
echo "ALL TESTS PASSED"
