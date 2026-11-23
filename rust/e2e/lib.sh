# Shared helpers for the emulator end-to-end scripts (source it). They drive the real app on the
# emulator with real touches and read its structured log events ("bunpo" tag).
#
# The app answers test commands (src/audit.rs) when its external files folder holds an e2e.on
# marker: where a label is on screen (so taps follow the layout instead of fixed coordinates),
# a layout audit of the screen as drawn on the device, and the buttons on screen.

A="${ADB:-$HOME/Android/Sdk/platform-tools/adb}"
PKG=dev.local.bunpo.rust
EXT=/sdcard/Android/data/$PKG/files
DATA=/data/data/$PKG/files
AUDITS=0

fail() { echo "FAIL: $*"; exit 1; }
ok() { echo "  ok: $*"; }

ev() { $A logcat -d -s bunpo:I | sed -n 's/.* bunpo *: //p'; }        # all events so far
last_ev() { ev | grep -E "$1" | tail -1; }
wait_ev() {  # wait_ev <regex> [timeout_s]
  for _ in $(seq 1 $(( ${2:-10} * 4 ))); do [ -n "$(last_ev "$1")" ] && return 0; sleep 0.25; done
  fail "timeout waiting for event /$1/ (last: $(ev | tail -3 | tr '\n' '|'))"
}
count_ev() { ev | grep -cE "$1" || true; }

# the hook must be on before the app starts
enable_hook() { $A shell mkdir -p $EXT; $A shell touch $EXT/e2e.on; $A logcat -G 16M >/dev/null 2>&1 || true; }

# cmd <command>: run a test command in the app, print its answer (one line)
cmd() {
  # unique even in subshells (where a counter wouldn't advance and $RANDOM repeats)
  local id="$BASHPID-$(date +%s%N)"
  local q=${1//\'/\'\\\'\'}   # quote for the device shell: ' -> '\''
  local r try
  for try in 1 2; do   # once more if the answer got lost (the log daemon may drop lines)
    # owned by the app's user: after a fresh install the app can't read a file root made there
    $A shell "printf '%s\n' '#$id $q' > $EXT/e2e.tmp && chown \$(stat -c %U ${EXT%/files}) $EXT/e2e.tmp && mv $EXT/e2e.tmp $EXT/e2e.cmd"
    for _ in $(seq 1 24); do
      r=$($A logcat -d -s bunpo:I | sed -n "s/.* bunpo *: e2e #$id //p" | tail -1)
      if [ -n "$r" ]; then echo "$r"; return 0; fi
      sleep 0.25
    done
  done
  echo "NO ANSWER to '$1' (is the hook on?)"
}

scroll_down() { $A shell input swipe 540 1500 540 700 300; sleep 0.8; }   # content moves up
scroll_up() { $A shell input swipe 540 700 540 1500 300; sleep 0.8; }
keyboard_shown() { $A shell dumpsys input_method | grep -q 'mInputShown=true'; }
# close the keyboard like a person: Back, only while the keyboard shows (else Back leaves the screen)
hide_keyboard() { if keyboard_shown; then $A shell input keyevent 4; sleep 0.8; fi; }

# where_on <label>: print "x y" of the label on screen, scrolling down to it if needed
# (content scrolled out of view is not reported at all: "none" may mean further down)
# The position must hold still for a moment: while the keyboard opens or closes the layout moves,
# and a tap at the old position would land on the keyboard.
where_on() {
  local r prev="" misses=0
  for _ in $(seq 1 16); do
    r=$(cmd "where $1")
    case "$r" in
      "where on "*)
        if [ "$r" = "$prev" ]; then set -- $r; echo "$3 $4"; return 0; fi
        prev=$r; misses=0; sleep 0.4 ;;
      *)
        # not on screen (or under a bar): maybe the layout is still moving (keyboard); look
        # again before scrolling, up when it is hidden above
        prev=""; misses=$((misses + 1))
        if (( misses < 3 )); then sleep 0.5
        else misses=0; if [[ "$r" == "where above "* ]]; then scroll_up; else scroll_down; fi; fi ;;
    esac
  done
  return 1
}

# tap_label <label>: tap the element with that accessible label, like a finger would
tap_label() {
  local xy; xy=$(where_on "$1") || fail "no '$1' on screen (buttons: $(cmd buttons))"
  $A shell input tap $xy; sleep 0.7
}
has_label() { [[ "$(cmd "where $1")" == "where on "* ]]; }   # on screen now, no scrolling

# audit <name> [strict]: the screen as drawn on the device has no layout problem
# (a list still sliding after a swipe can be caught mid-way: a failure is checked once more, a moment
# later; a real layout problem fails both times)
audit() {
  local r; r=$(cmd "audit $1${2:+ $2}")
  AUDITS=$((AUDITS + 1))
  if [[ "$r" != "audit $1 ok" ]]; then
    sleep 1.5
    r=$(cmd "audit $1${2:+ $2}")
    [[ "$r" == "audit $1 ok" ]] || fail "layout: $r"
  fi
}
# audit_scrolled <name>: audit the whole screen, page by page (up to 6 pages)
audit_scrolled() {
  local prev="" cur
  audit "$1 (top)"
  for i in 1 2 3 4 5 6; do
    cur=$(cmd digest)
    [ "$cur" = "$prev" ] && break
    prev=$cur
    scroll_down
    audit "$1 (page $((i + 1)))"
  done
  for _ in 1 2 3 4 5 6; do scroll_up; done
}

alive() { $A shell pidof $PKG >/dev/null; }
in_front() { $A shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' | grep -q $PKG; }

# install a progress file into the app (as root; owner and SELinux context must match)
push_progress() {
  $A shell am force-stop $PKG
  $A shell mkdir -p $DATA
  $A push "$1" $DATA/progress.json >/dev/null 2>&1
  local owner ctx
  owner=$($A shell stat -c %U:%G /data/data/$PKG)
  ctx=$($A shell ls -dZ /data/data/$PKG | awk '{print $1}')
  $A shell chown -R "$owner" $DATA
  $A shell chcon -R "$ctx" $DATA
}
pull_progress() { $A shell cat $DATA/progress.json > "$1"; }

start_app() { $A logcat -c; $A shell am start -n $PKG/android.app.NativeActivity >/dev/null 2>&1; wait_ev '^(started|resumed)' 15; wait_ev '^e2e hook on' 5; sleep 1; }

# keyboard <en|ja>: pick Gboard's layout (English QWERTY, or Japanese romaji input if installed;
# it is added in the emulator's Gboard settings: Languages > Add keyboard > 日本語 > QWERTY).
# Subtypes are listed in the order they were added: English first.
keyboard() {
  local ids want
  ids=$($A shell settings get secure enabled_input_methods | tr ':' '\n' | grep LatinIME | cut -d';' -f2-)
  if [ "$1" = ja ]; then
    [[ "$ids" == *";"* ]] || return 1   # no Japanese layout installed
    want=$(cut -d';' -f2 <<<"$ids")
  else
    want=$(cut -d';' -f1 <<<"$ids")
  fi
  $A shell settings put secure selected_input_method_subtype "$want"
  $A shell am force-stop com.google.android.inputmethod.latin
  sleep 1
}
