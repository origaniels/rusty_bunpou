#!/bin/bash
# Device behaviour that only shows on a real phone:
#  1. leaving reviews halfway while Android kills the app in the background, then resuming;
#  2. the Japanese keyboard: kana being composed show in the blank and are checked once, whether
#     Check is tapped right away or after confirming with the keyboard's Enter (needs the
#     Japanese QWERTY layout in the emulator's Gboard; skipped otherwise);
#   ./e2e/flows.sh [apk]
set -euo pipefail
cd "$(dirname "$0")/.."
source e2e/lib.sh
APK="${1:-android/app/build/outputs/apk/release/app-release.apk}"
WORK=$(mktemp -d)
cleanup() { keyboard en || true; rm -rf "$WORK"; }
trap cleanup EXIT

$A root >/dev/null 2>&1 || true; $A wait-for-device
$A install -r "$APK" >/dev/null
$A shell pm grant $PKG android.permission.POST_NOTIFICATIONS
enable_hook
keyboard en
python3 e2e/make_progress.py "$WORK/p.json" en --due 6 --learned 8

home_due() { last_ev '^home due=' | sed 's/home due=\([0-9]*\).*/\1/'; }
# leave like a person (Home), then Android reclaims the process
close_app() {
  $A shell input keyevent 3; sleep 1
  $A shell am kill $PKG; sleep 1
  # like the low-memory killer would, if Android didn't reclaim it yet
  if alive; then $A shell kill -9 "$($A shell pidof $PKG)"; sleep 1; fi
  alive && fail "the app is still running"
  return 0
}

echo "== 1. reviews left halfway, the app killed in the background"
push_progress "$WORK/p.json"; start_app
[ "$(home_due)" = 6 ] || fail "expected 6 due, got $(home_due)"
tap_label "Start reviews"; wait_ev '^screen=2'
for i in 1 2; do
  $A shell input text xx; tap_label Check; wait_ev "^verdict=Wrong"
  tap_label Next; sleep 0.5
done
ok "2 reviews answered (wrong)"
$A shell input text xx; tap_label Check; sleep 0.5   # a third one checked, then the app is closed
close_app
start_app
[ "$(home_due)" = 4 ] || fail "after 2 graded answers 4 should be due, got $(home_due)"
ok "4 due: the 2 answers before the app was killed were kept"
has_label "Resume reviews (6 left)" || fail "no resume button: $(cmd buttons)"
ok "home offers: Resume reviews (6 left)"
audit "home, reviews to resume"
tap_label "Resume reviews (6 left)"; wait_ev '^screen=2 resumed'
has_label "Reviews  2 / 6" || fail "header should count 2 answered of 6: $(cmd texts | cut -c1-300)"
ok "resumed where it stopped: 2 / 6 answered"
audit "resumed reviews"

echo "== 2. Japanese keyboard"
# key centres of Gboard's Japanese QWERTY layout on this AVD (1080x2400, keyboard at the bottom)
declare -A KEY
i=0; for k in q w e r t y u i o p; do KEY[$k]="$((58 + 107 * i)) 1715"; i=$((i + 1)); done
i=0; for k in a s d f g h j k l; do KEY[$k]="$((58 + 107 * i)) 1868"; i=$((i + 1)); done
i=0; for k in z x c v b n m; do KEY[$k]="$((218 + 107 * i)) 2023"; i=$((i + 1)); done
IME_ENTER="993 2180"
type_keys() { local w=$1; for ((k = 0; k < ${#w}; k++)); do $A shell input tap ${KEY[${w:k:1}]}; sleep 0.25; done; }
kana_answer() {  # the current item's answer in kana
  local item p s
  item=$(last_ev '^item '); p=$(sed 's/.*point=\([^ ]*\).*/\1/' <<<"$item"); s=$(sed 's/.*sentence=\([0-9]*\).*/\1/' <<<"$item")
  python3 - "$p" "$s" <<'PY'
import json, sys
c = json.load(open("../data/build/content.json"))
p = next(p for p in c["points"] if p["id"] == sys.argv[1])
s = next(s for s in p["sentences"] if s["id"] == int(sys.argv[2]))
print(next((a for a in s["answers"] if all("ぁ" <= ch <= "ゟ" for ch in a)), ""))
PY
}
if keyboard ja; then
  push_progress "$WORK/p.json"; start_app
  tap_label "Start reviews"; wait_ev '^screen=2'; sleep 1
  done_items=0
  for attempt in 1 2 3 4 5 6; do
    ans=$(kana_answer); keys=$(python3 e2e/romaji.py "$ans")
    if [ -z "$keys" ]; then   # can't type this one: skip it
      $A shell input tap ${KEY[x]}; tap_label Check; tap_label Typo; tap_label Next; sleep 0.5; continue
    fi
    nv=$(count_ev '^verdict=')
    type_keys "$keys"; sleep 0.5
    has_label "$ans" || fail "the blank doesn't show '$ans' while it is composed"
    if (( done_items == 1 )); then $A shell input tap $IME_ENTER; sleep 0.5; how="Enter on the keyboard, then Check"; else how="Check right away"; fi
    tap_label Check
    for _ in $(seq 1 20); do [ "$(count_ev '^verdict=')" -gt "$nv" ] && break; sleep 0.25; done
    v=$(last_ev '^verdict=')
    [[ "$v" == "verdict=Correct"*"kana=\"$ans\""* ]] || fail "typed $ans ($keys): $v"
    ok "$ans typed as $keys, shown in the blank, checked once ($how)"
    done_items=$((done_items + 1))
    tap_label Next; sleep 0.5
    (( done_items == 2 )) && break
  done
  (( done_items == 2 )) || fail "could not type two answers"
  keyboard en
else
  echo "  skipped: no Japanese layout in the emulator's Gboard"
fi

echo "PASS: flows ($AUDITS layout audits)"
