#!/bin/bash
# Layout tour on the emulator: visit every screen and state of the app (dialogs, keyboard open,
# answered or not, long pages scrolled through) and run the layout audit on each, as drawn on the
# device with its real fonts. Taps go through the labels the app reports, like a finger would.
#   ./e2e/tour.sh [apk] [en|fr]    (needs the AVD "bunpo" running; the APK is installed first)
set -euo pipefail
cd "$(dirname "$0")/.."
source e2e/lib.sh
APK="${1:-android/app/build/outputs/apk/release/app-release.apk}"
LANG_UI="${2:-en}"
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
PO=app/lang/fr/LC_MESSAGES/bunpo-app.po

# L <English>: the label in the tour's language (from the French translations)
L() {
  if [ "$LANG_UI" = fr ]; then
    python3 - "$PO" "$1" <<'PY'
import sys
po, want = open(sys.argv[1], encoding="utf8").read().split("\n"), sys.argv[2]
for i, l in enumerate(po):
    if l == 'msgid "%s"' % want:
        print(po[i + 1][len('msgstr "'):-1]); break
else:
    print(want)
PY
  else
    echo "$1"
  fi
}
# first button whose label starts with one of the given prefixes
button_starting() {
  cmd buttons | sed 's/^buttons //' | tr '|' '\n' | sed 's/^ *//; s/ *$//; s/ \[on\]$//' | grep -E "^($1)" | head -1
}

echo "== tour ($LANG_UI)"
$A root >/dev/null 2>&1 || true; $A wait-for-device
$A install -r "$APK" >/dev/null
$A shell pm grant $PKG android.permission.POST_NOTIFICATIONS
enable_hook
keyboard en
python3 e2e/make_progress.py "$WORK/p.json" "$LANG_UI" --due 6 --learned 8
push_progress "$WORK/p.json"
start_app

audit_scrolled home; ok "home"

tap_label "$(L Settings)"; wait_ev '^screen=5'
audit_scrolled settings; ok "settings"
tap_label "$(L 'Reset all progress')"
audit "reset-all dialog"; ok "reset-all dialog"
tap_label "$(L Cancel)"

tap_label "$(L "Grammar list")"; wait_ev '^screen=3'
audit_scrolled "grammar list"; ok "grammar list"
first=$(python3 -c "import json; print(json.load(open('../data/build/content.json'))['points'][0]['title'])")
tap_label "$first"; wait_ev '^screen=4'
audit_scrolled "grammar point"; ok "grammar point"
tap_label "$(L Reset)"
audit "reset-point dialog"; ok "reset-point dialog"
tap_label "$(L Cancel)"
$A shell input keyevent 4; sleep 0.8

tap_label "$(L Stats)"; wait_ev '^screen=6'
audit_scrolled stats; ok "stats (streak, calendar, forecast, leech, levels)"

tap_label "$(L Home)"; wait_ev '^screen=0'
learn=$(button_starting 'Learn|Apprendre')
[ -n "$learn" ] || fail "no Learn button: $(cmd buttons)"
tap_label "$learn"; wait_ev '^screen=1'
next=$(L Next)
for page in 1 2 3 4 5 6 7 8 9 10; do
  audit_scrolled "lesson page $page"
  if cmd buttons | grep -qF "$(L 'Start quiz')"; then break; fi
  tap_label "$next"
done
ok "lesson pages"
tap_label "$(L 'Start quiz')"; wait_ev '^screen=2 lesson'
sleep 1
audit "quiz, keyboard open"; ok "quiz with the keyboard open"
$A shell input text xx; tap_label "$(L Check)"; wait_ev '^verdict=Wrong'
audit "quiz, wrong answer, keyboard open"
hide_keyboard
audit_scrolled "quiz, wrong answer"; ok "quiz, wrong answer"
tap_label "$(L 'Grammar notes')"
audit "grammar notes dialog"; ok "grammar notes dialog"
tap_label "$(L Close)"
tap_label "$(L Report)"
audit "report dialog"
reason=$(L "The translation is wrong")
has_label "$reason" && tap_label "$reason"
audit "report dialog, reason picked"; ok "report dialog"
tap_label "$(L Cancel)"
tap_label "$(L Typo)"
audit_scrolled "quiz, right answer"; ok "quiz, right answer (typo)"
$A shell input keyevent 4; wait_ev '^screen=0 back'
audit_scrolled "home, lesson quiz to resume"; ok "home with a lesson quiz to resume"

resume=$(button_starting 'Resume|Reprendre')
[ -n "$resume" ] || fail "no resume button: $(cmd buttons)"
tap_label "$resume"; sleep 1
audit "resumed quiz"; ok "resumed quiz"
echo "PASS: tour ($LANG_UI), $AUDITS layout audits on the device"
