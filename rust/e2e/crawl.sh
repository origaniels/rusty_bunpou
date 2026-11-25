#!/bin/bash
# Button crawler on the emulator: on every screen and state of the app, tap every button and
# switch for real (each time from the same saved progress, the app freshly opened), then check:
# the app is still running and in front (unless the button opens another app on purpose),
# something changed on screen, and the layout audit passes on what it led to.
#   ./e2e/crawl.sh [apk] [en|fr] [state ...]   (default: every state; ~10-15 minutes)
set -euo pipefail
cd "$(dirname "$0")/.."
source e2e/lib.sh
APK="${1:-android/app/build/outputs/apk/release/app-release.apk}"
LANG_UI="${2:-en}"
shift $(( $# < 2 ? $# : 2 ))
WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
PO=app/lang/fr/LC_MESSAGES/bunpo-app.po
JA='[\p{Hiragana}\p{Katakana}\p{Han}]'   # a Japanese label: a dictionary chip

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
labels() { sed 's/^buttons //' | tr '|' '\n' | sed 's/^ *//; s/ *$//' | grep -v '^$' || true; }
button_starting() { cmd buttons | labels | sed 's/ \[on\]$//' | grep -E "^($1)" | sed -n 1p; }

# buttons that open another app on purpose: file pickers, the dictionary (any Japanese label)
external() { [[ "$1" =~ ^($(L 'Export progress')|$(L 'Import progress')|Export|Exporter|Share|Partager) ]] || grep -qP "$JA" <<<"$1"; }

# ------------------------------------------------------------------ states (from a fresh start)
goto_home() { :; }
goto_settings() { tap_label "$(L Settings)"; wait_ev '^screen=5'; }
goto_grammar_list() { tap_label "$(L 'Grammar list')"; wait_ev '^screen=3'; }
goto_grammar_point() { goto_grammar_list; has_label "$FIRST" || tap_label "JLPT N5"; tap_label "$FIRST"; wait_ev '^screen=4'; }
goto_stats() { tap_label "$(L Stats)"; wait_ev '^screen=6'; }
goto_lesson() { tap_label "$(button_starting 'Learn|Apprendre')"; wait_ev '^screen=1'; }
goto_lesson_last() {
  goto_lesson
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    cmd buttons | grep -qF "$(L 'Start quiz')" && return 0
    tap_label "$(L Next)"
  done
}
goto_quiz() { goto_lesson_last; tap_label "$(L 'Start quiz')"; wait_ev '^screen=2 lesson'; sleep 1; hide_keyboard; }
goto_quiz_wrong() {
  goto_lesson_last; tap_label "$(L 'Start quiz')"; wait_ev '^screen=2 lesson'; sleep 1
  $A shell input text xx; tap_label "$(L Check)"; wait_ev '^verdict=Wrong'; hide_keyboard
}
goto_quiz_right() { goto_quiz_wrong; tap_label "$(L Typo)"; }
goto_notes() { goto_quiz_wrong; tap_label "$(L 'Grammar note')"; }
goto_report() { goto_quiz_wrong; tap_label "$(L Report)"; }
goto_reviews() { tap_label "$(L 'Start reviews')"; wait_ev '^screen=2'; sleep 1; hide_keyboard; }
goto_word_lesson() { tap_label "$(button_starting "$(L 'Learn') [0-9]+ new words|$(L 'Learn') [0-9]+ extra words|Apprendre [0-9]+ (nouveaux mots|mots de plus)")"; wait_ev '^screen=7'; }
goto_word_quiz() {
  goto_word_lesson
  for _ in $(seq 1 25); do
    cmd buttons | grep -qF "$(L 'Start quiz')" && break
    tap_label "$(L Next)"
  done
  tap_label "$(L 'Start quiz')"; wait_ev '^screen=8 lesson'
}
goto_word_answer() { goto_word_quiz; tap_label "$(L 'Show answer')"; }
goto_reset_point() { goto_grammar_point; tap_label "$(L Reset)"; }
goto_reset_all() { goto_settings; tap_label "$(L 'Reset all progress')"; }

ALL_STATES=(home settings grammar_list grammar_point stats lesson lesson_last quiz quiz_wrong quiz_right
            notes report reviews reset_point reset_all word_lesson word_quiz word_answer)
if [ $# -gt 0 ]; then STATES=("$@"); else STATES=("${ALL_STATES[@]}"); fi

fresh() { push_progress "$WORK/p.json"; start_app; }

# every control in a state: the buttons of each page, scrolling down until nothing new appears
DIALOGS=" notes report reset_point reset_all "
controls_of() {
  local st=$1 prev="" cur all="" pages=6
  # a dialog doesn't scroll (and a swipe on its backdrop would close it)
  [[ "$DIALOGS" == *" $st "* ]] && pages=1
  fresh; "goto_$st"
  for _ in $(seq 1 $pages); do
    all+=$(cmd buttons | labels)$'\n'
    cur=$(cmd digest); [ "$cur" = "$prev" ] && break; prev=$cur
    (( pages > 1 )) && scroll_down
  done
  # dictionary chips (Japanese labels) vary with the sentence: keep one of them
  { grep -vP "$JA" <<<"$all" | sort -u; grep -P "$JA" <<<"$all" | sed -n 1p; } | grep -v '^$' || true
}

echo "== crawl ($LANG_UI): ${STATES[*]}"
$A root >/dev/null 2>&1 || true; $A wait-for-device
$A install -r "$APK" >/dev/null
$A shell pm grant $PKG android.permission.POST_NOTIFICATIONS
enable_hook
keyboard en
python3 e2e/make_progress.py "$WORK/p.json" "$LANG_UI" --due 6 --learned 8
FIRST=$(python3 -c "import json; print(json.load(open('../data/build/content.json'))['points'][0]['title'])")
PRESSED=0; EXTERNAL=0
for st in "${STATES[@]}"; do
  controls_of "$st" > "$WORK/controls"   # not in a subshell: a failure must stop the crawl
  mapfile -t ctl < "$WORK/controls"
  echo "== $st: ${#ctl[@]} controls"
  (( ${#ctl[@]} > 0 )) || fail "$st: no controls found"
  for c in "${ctl[@]}"; do
    label=${c% \[on\]}
    fresh; "goto_$st"
    # dictionary chips depend on the sentence, which is picked at random: tap whichever is there
    if grep -qP "$JA" <<<"$label"; then
      label=""
      for _ in 1 2 3; do
        label=$(cmd buttons | labels | { grep -P "$JA" || true; } | sed -n 1p)
        [ -n "$label" ] && break
        scroll_down
      done
      if [ -z "$label" ]; then echo "    (this sentence has no dictionary chip)"; continue; fi
    fi
    before=$(cmd digest); nev=$(count_ev '^(screen|verdict|nudge|item|language|lookup|session|e2e hook)')
    tap_label "$label"; sleep 1
    alive || fail "$st: the app died after '$label'"
    if ! in_front; then
      external "$label" || fail "$st: '$label' left the app"
      EXTERNAL=$((EXTERNAL + 1)); echo "    $label -> another app (expected)"
      $A shell input keyevent 4; sleep 1.5
      in_front || { $A shell am start -n $PKG/android.app.NativeActivity >/dev/null; sleep 1.5; }
      in_front || fail "$st: could not come back after '$label'"
      PRESSED=$((PRESSED + 1)); continue
    fi
    after=$(cmd digest); nev2=$(count_ev '^(screen|verdict|nudge|item|language|lookup|session|e2e hook)')
    if [ "$after" = "$before" ] && [ "$nev2" = "$nev" ] && [ "$c" = "$label" ]; then
      fail "$st: '$label' did nothing (screen unchanged)"
    fi
    audit "$st, after '$label'"
    PRESSED=$((PRESSED + 1)); echo "    $label ok"
  done
done
echo "PASS: crawl ($LANG_UI): $PRESSED controls pressed ($EXTERNAL open another app), $AUDITS layout audits"
