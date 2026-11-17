#!/bin/bash
# Run every test suite. Pass --e2e to also run the emulator end-to-end test (needs a running AVD).
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.cargo/bin:$PATH"

echo "### pipeline (pytest)"
pipeline/.venv/bin/python -m pytest -q pipeline/tests

echo "### core + UI (cargo test)"
(cd rust && cargo test -q 2>&1 | grep -E "test result|FAILED|panicked" )
(cd rust && cargo test -q >/dev/null 2>&1) || { echo "cargo tests failed"; exit 1; }

if [[ "${1:-}" == "--e2e" ]]; then
  echo "### android e2e (emulator)"
  (cd rust && ./build-android.sh release x86_64 >/dev/null && cd android && ./gradlew assembleRelease -PskipCargo -q)
  rust/e2e/run.sh
fi
echo "ALL TESTS PASSED"
