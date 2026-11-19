#!/bin/bash
# End-to-end test on the Android emulator (AVD "bunpo", Pixel 7 profile, 1080x2400, gesture nav).
# Drives the real app with taps/typing, checks logcat events ("bunpo" tag), and travels in time by
# setting the emulator clock (needs `adb root`, works on google_apis images).
#   ./e2e/run.sh [apk]      (default: release APK from rust/android)
#   E2E_LANG=fr  run the whole scenario with the app in French
#   SHOTS=dir    save a screenshot of each screen there (for a visual check)
set -euo pipefail
cd "$(dirname "$0")/.."
A="${ADB:-$HOME/Android/Sdk/platform-tools/adb}"
PKG=dev.local.bunpo.rust
APK="${1:-android/app/build/outputs/apk/release/app-release.apk}"
H=3600; D=86400
LANG_UI="${E2E_LANG:-en}"
if [ "$LANG_UI" = fr ]; then NOTE_RE="[0-9]* révisions\? de grammaire vous attend\(ent\)\?"; else NOTE_RE="[0-9]* grammar reviews\? \(is\|are\) waiting"; fi
shot() { [ -n "${SHOTS:-}" ] || return 0; mkdir -p "$SHOTS"; sleep 0.8; $A exec-out screencap -p > "$SHOTS/$LANG_UI-$1.png"; }
fail() { echo "FAIL: $*"; restore_clock; exit 1; }
ok() { echo "  ok: $*"; }
restore_clock() { $A shell date "@$(date +%s)" >/dev/null 2>&1 || true; $A shell settings put global auto_time 1 >/dev/null 2>&1 || true; }
trap restore_clock EXIT

ev() { $A logcat -d -s bunpo:I | sed -n 's/.* bunpo *: //p'; }        # all events so far
last_ev() { ev | grep -E "$1" | tail -1; }
wait_ev() {  # wait_ev <regex> [timeout_s]
  for _ in $(seq 1 $(( ${2:-10} * 4 ))); do last_ev "$1" >/dev/null && [ -n "$(last_ev "$1")" ] && return 0; sleep 0.25; done
  fail "timeout waiting for event /$1/ (last: $(ev | tail -3 | tr '\n' '|'))"
}
tap() { $A shell input tap "$1" "$2"; sleep 0.6; }
# virtual time: the emulator re-syncs its clock with the host now and then, so keep the total
# offset here and re-apply it (host time + OFFSET) whenever it matters.
OFFSET=0
apply_clock() { $A shell date "@$(( $(date +%s) + OFFSET ))" >/dev/null; }
travel() { OFFSET=$(( OFFSET + $1 )); apply_clock; }
# open the app: either a fresh start or a resume of the backgrounded one
launch() { apply_clock; $A logcat -c; $A shell am start -n $PKG/android.app.NativeActivity >/dev/null 2>&1; wait_ev '^(started|resumed)' 15; sleep 1; }
# leave the app like a user would (Home), then let Android kill the background process.
# (Never `am force-stop`: that also cancels the app's alarms, i.e. the reminder.)
close_app() { $A shell input keyevent 3; sleep 0.5; $A shell am kill $PKG; sleep 0.5; }

# answers to try per grammar point (the first lesson is always these five, in this order)
declare -A ANSWERS=(
  [da]="da" [desu]="desu" [deshita]="deshita" [datta]="datta"
  [janai]="janai dehanakatta dehaarimasen jaarimasen janaidesu dehanaidesu"
)
declare -A TRIES=()

answer_session() {  # answer items until the session finishes
  for _ in $(seq 1 40); do
    if last_ev '^session-finished' >/dev/null && [ -n "$(last_ev '^session-finished')" ]; then return 0; fi
    local item p n cands a
    item=$(last_ev '^item '); p=$(sed 's/.*point=\([^ ]*\).*/\1/' <<<"$item")
    sid=$(sed 's/.*sentence=\([0-9]*\).*/\1/' <<<"$item")
    [ -n "$p" ] || fail "no current item"
    # guesses restart for every new sentence (the most likely form first)
    n=${TRIES[$sid]:-0}; cands=(${ANSWERS[$p]}); a=${cands[$(( n % ${#cands[@]} ))]}
    TRIES[$sid]=$(( n + 1 ))
    local before; before=$(ev | grep -c '^verdict' || true)
    for ((k = 0; k < ${#a}; k++)); do $A shell input text "${a:k:1}"; done   # one key at a time, like a person
    $A shell input keyevent 66
    for _ in $(seq 1 20); do [ "$(ev | grep -c '^verdict' || true)" -gt "$before" ] && break; sleep 0.25; done
    v=$(last_ev '^verdict'); echo "    $p <- $a : $v"
    [[ "$v" == *"raw=\"$a\""* ]] || fail "typed '$a' but the app received: $v"
    $A shell input keyevent 66; sleep 0.7
  done
  fail "session did not finish"
}

due_now() { last_ev '^home due=' | sed 's/home due=\([0-9]*\).*/\1/'; }

echo "== install"
$A root >/dev/null 2>&1 || true; $A wait-for-device
$A shell settings put global auto_time 0
$A uninstall $PKG >/dev/null 2>&1 || true
$A install "$APK" >/dev/null
$A shell pm grant $PKG android.permission.POST_NOTIFICATIONS
launch
[ "$(due_now)" = 0 ] || fail "fresh install has due reviews"; ok "fresh start, nothing due"

echo "== settings: 3 points per lesson (だ, です, でした: one possible answer each), language $LANG_UI"
tap 929 2250; wait_ev '^screen=5'              # Settings (menu bar)
tap 207 1343                                   # "3" (points per lesson)
if [ "$LANG_UI" = fr ]; then tap 752 450; wait_ev '^language=fr'; ok "app switched to French"; fi
shot settings
$A shell input keyevent 4; wait_ev '^screen=0 back'
shot home
echo "== lesson"
tap 524 1240                                   # Learn 3 new
wait_ev '^screen=1'
shot lesson
for _ in 1 2 3; do tap 816 2231; done          # Next x2, Start quiz
wait_ev '^screen=2 lesson'
shot quiz
answer_session
ok "$(last_ev '^session-finished')"
shot quiz-finished
tap 540 490; wait_ev '^screen=0'               # Home
tap 669 2250; wait_ev '^screen=6'              # Stats (menu bar)
ok "stats screen opens"
shot stats
tap 409 2250; wait_ev '^screen=3'              # Grammar (menu bar)
shot grammar
$A shell input keyevent 4; wait_ev '^screen=0 back'
rem=$(last_ev '^reminder'); [[ "$rem" == *"count=3"* ]] || fail "reminder not scheduled: $rem"; ok "$rem"
$A shell dumpsys alarm | grep -q "$PKG" || fail "no alarm registered"; ok "alarm registered with AlarmManager"

# Follow the app's own reminders: jump to each reminder time, expect the notification, open the
# app, do the reviews. Gaps between reviews must grow as points move through the SRS levels.
gaps=()
for cycle in 1 2 3 4 5; do
  rem=$(last_ev '^reminder'); at=$(sed 's/.*at=\([0-9]*\).*/\1/' <<<"$rem"); count=$(sed 's/.*count=\([0-9]*\).*/\1/' <<<"$rem")
  dev_ms=$(( ($(date +%s) + OFFSET) * 1000 ))
  gap=$(( (at - dev_ms) / 1000 ))
  gaps+=("$gap")
  printf '== cycle %d: reminder for %d review(s) in %s\n' "$cycle" "$count" "$(awk -v s=$gap 'BEGIN{ if (s<86400) printf "%.1f h", s/3600; else printf "%.1f days", s/86400 }')"
  close_app
  travel $(( gap + 60 ))
  for i in $(seq 1 60); do
    $A shell dumpsys notification --noredact | grep -q "$NOTE_RE" && break
    (( i == 20 )) && travel 660   # past the 10-minute delivery window
    (( i % 10 == 0 )) && apply_clock
    sleep 1
  done
  note=$($A shell dumpsys notification --noredact | grep -o "$NOTE_RE" | head -1)
  [ -n "$note" ] || fail "no reminder notification in cycle $cycle"
  [[ "$note" == "$count "* ]] || fail "notification says '$note', reminder was for $count"
  ok "notification: $note"
  launch
  due=$(due_now)
  [ "$due" = "$count" ] || fail "notification said $count, app shows $due due"; ok "$due due (matches notification)"
  $A shell dumpsys notification --noredact | grep -q "$NOTE_RE" && fail "notification not dismissed on open"
  ok "notification dismissed on open"
  tap 524 695                                  # Start reviews
  wait_ev '^screen=2'
  (( cycle == 1 )) && shot reviews
  answer_session
  tap 540 490; wait_ev '^screen=0'
  [ "$(due_now)" = 0 ] || fail "reviews left after session"
done

echo "== gaps between review sessions (s): ${gaps[*]}"
# learning steps 4h, 8h, 1d, 3d (exact), then the first FSRS interval (> 3 days, at most 3x = 9 days +fuzz)
expect=(14400 28800 86400 259200)
for k in 0 1 2 3; do
  d=$(( gaps[k] - expect[k] )); (( d > -300 && d < 300 )) || fail "step $((k+1)): gap ${gaps[k]}s, expected ${expect[k]}s"
done
ok "learning steps 4h → 8h → 1d → 3d"
(( gaps[4] > 3 * 86400 && gaps[4] < 10 * 86400 )) || fail "first FSRS interval ${gaps[4]}s"
ok "then FSRS: $(awk -v s=${gaps[4]} 'BEGIN{printf "%.1f", s/86400}') days"
echo "PASS"
