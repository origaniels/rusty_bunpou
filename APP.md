# 文法 SRS: how the app works

A guide for anyone (person or coding agent) picking up this codebase: what the app does, where each
feature lives, the data formats, and how to change things without breaking them. Build commands are
in [README.md](README.md), the test suites in [TESTING.md](TESTING.md).

## What it is

An offline Android app for learning Japanese grammar with spaced repetition. Each grammar point
(456 of them, JLPT N5 to N1) has an explanation and example sentences with a blank; you learn points
in lessons, then review them by typing the missing part. Everything is in English or French
(interface, explanations, translations). No account, no network: content is embedded in the binary,
progress is one JSON file on the phone.

Content sources: example sentences from Tatoeba (CC-BY 2.0 FR, credited per sentence), and texts
written for this app (explanations, extra example sentences, French translations), marked as such.

## Architecture

```
pipeline/ (Python)  ──build.py──▶  data/build/content.json  ──include_str!──▶  rust/core (logic)
                                                                                    │
                                                         rust/app (Slint UI + glue) ┘
                                                              │ Platform trait
                                              android.rs ─JNI─▶ Java helpers (rust/android)
```

- **pipeline/**: picks and annotates sentences, writes `content.json`. Only run when content changes.
- **rust/core**: everything that can be tested without a UI: content model, kana input, scheduling,
  sessions, hints, stats, storage, sentence layout.
- **rust/app**: `ui/app.slint` (all screens), `src/lib.rs` (callbacks, refreshes, state),
  `src/android.rs` (Platform implementation over JNI), `src/audit.rs` (layout audit for tests).
- **rust/android**: Gradle project; Java only where Android APIs need an Activity: reminders
  (`ReviewReminder`), file picker (`Backup`), dictionary lookup (`Lookup`), vibration (`Haptics`).

The UI never holds logic: Slint callbacks call into `lib.rs`, which updates `State` (progress,
session, navigation) and pushes plain data structs (`HomeData`, `QuizData`, …) back to the UI with
`refresh_*` functions.

## Content (`data/build/content.json`)

Built by `pipeline/build.py` from the grammar definitions (`grammar_n5.py`: token matchers;
`grammar_n4..n1.py` via `patterns.py`: regexes aligned to token boundaries), Tatoeba, the extra
examples (`extra_examples.py`) and the French texts (`fr/`).

A **point**: `id` (never rename: progress is keyed by it), `level`, `title`, `meaning`, `structure`,
`explanation`, `fr` (French texts), `nuance` (EN/FR, for points that have look-alikes, see Hints),
`sentences`.

A **sentence**: `ja`, `en`, `fr`, `furi` (furigana segments), `cloze` (character offsets of the
blank), `answers` (accepted answers: surface, reading, variants), `hint` (dictionary form + form tags
for verb points, e.g. `話す（はなす） · polite, past`), `words` (dictionary forms for the lookup
chips), `parts` (the answer's tokens: particle / conjugating / other), `alts` (answers using a point
with the same meaning but another nuance), attribution fields (Tatoeba id and owner, or
`src="app"`).

The content is embedded with `include_str!`: rebuild the APK after regenerating it. A content build
takes about 6 minutes (tokenization is cached in `data/build/tokens.pkl`).

## Features and where they live

### Lessons and the daily goal
- Home: "Learn N new" until today's goal (Settings, "Daily goal": 3/5/10) is reached, then
  "Learn N extra". `next_lesson_size`, `learned_today` in `lib.rs` (uses `Card.learned_at`).
- Lesson order: `core/src/lessons.rs` (by level from "Start lessons at", then a fixed order).
- A lesson shows each point's explanation and 4 examples, then a quiz on other sentences
  (`LESSON_EXAMPLES` in `session.rs`).

### Quiz and reviews (`core/src/session.rs`)
- Each point is graded on its first answer of the session; a missed point comes back at the end
  (practice, not graded again) **with the same sentence**; the next session uses another sentence
  (`chosen` map; `Card.last_sentence` is avoided).
- Answer field: romaji is converted to kana (`core/src/kana.rs`); the field keeps what was typed and
  the kana preview is drawn in the blank. The keyboard's composition (Japanese IME, before Enter) is
  shown in the blank too and checked on Check (`AnswerField` in `app.slint`, `with_composition`,
  `composition_for` in `lib.rs`).
- After a wrong answer: **Typo** (counts as right), **Retry** (try again, still counted as missed),
  or editing the field = typo fix (a right answer then counts as right).
- Check is disabled while the field is empty; the clear button is hidden once the answer is right.
- Leaving a quiz keeps it (`Progress.paused`, saved after every answer): Home offers "Resume reviews
  (N left)" / "Resume the lesson quiz". An answer checked but not moved past counts when leaving.
- After answering: grammar notes, Report, dictionary chips, haptics (see below).

### "Almost" hints (`core/src/hints.rs`)
A wrong answer that is nearly right gets a hint and a free retry (once per item) instead of a verdict:
- **Particle**: the expected answer with one particle dropped, added or swapped (uses `parts`; never
  for an answer that is only particles).
- **Form**: the right word (same stem as the hint's dictionary form) in another form; the hint names
  what differs (tense, politeness, て-form, positive/negative), never which way.
- **Nuance**: another grammar point that fits the sentence (`alts`): the hint describes what the
  expected point adds (`nuance`), without the answer. Groups and their context rules are in
  `pipeline/alternatives.py` (から/ので, けど/が/のに, the "must" forms, かもしれない/でしょう/だろう,
  ようだ/みたい/らしい, おかげで/せいで, ないで/ずに, …). A swap is only listed where it is grammatical;
  add a rule and a test when a group gets a new exception.

### Scheduling (`core/src/fsrs.rs`, `store.rs`)
Learning steps 4h → 8h → 1d → 3d, then FSRS-5 (retention 85/90/95 %, growth ≤ 3× per review, ≤ 1
year). A mistake on a learned point: retry after 1h, then 1d → 3d → back to FSRS. Simulation: `cargo run -p bunpo-core --example simulate`.

### Progress file (`core/src/store.rs`)
`progress.json` in the app's internal files: `cards` (per point id: state, stability, difficulty,
due, last review, reps, lapses, step, last sentence, learned_at), `settings`, `log` (every graded
answer), `reports`, `paused` (the unfinished quiz). Atomic writes; an unreadable file is moved to
`progress.json.bad`, never overwritten. All fields use `serde(default)`: add fields that way so old
files still load.

### Grammar list and points
Grammar tab: levels fold/unfold, each point shows its SRS stage. A point page shows the explanation,
examples (with furigana), and "Reset" (back to new). `refresh_list`, `point_data` in `lib.rs`.

### Stats (`core/src/stats.rs`, `chart.rs`)
Streak and a 15-week activity calendar, 7-day review forecast, leeches (3 wrong among the last 5
reviews, lesson quiz and pre-reset reviews excluded), progress pies per level, counts per SRS stage.

### Settings
Language (en/fr, everything follows), furigana, translation before answering, romaji conversion,
reminders, vibration, daily goal, start level, target retention, backup (export/import progress,
export reports), reset all.

### Reports
"Report" in the quiz: a reason and a note, stored in `Progress.reports` (kept across resets, merged
on import). Settings → "Export reports" writes a readable JSON with the sentence, translations,
answers and what was typed, to fix the content later.

### Backup
Export/import through Android's file picker (`Backup.java`). The picker leaves
`files/progress.import.json` or `files/backup-result.txt`; `check_backup_files` handles them when the
app resumes. Import keeps the previous file as `progress.json.before-import`.

### Reminders (`core/src/reminder.rs`, `ReviewReminder.java`)
One alarm at the next due time, a notification with the count; dismissed when the app opens.

### Dictionary chips
After answering, the sentence's words (dictionary forms) as chips; a tap opens Takoboto (app via the
"process text" / "share" intents, else its website). `Lookup.java`; `chip_rows` in `lib.rs` wraps them.

### Haptics
A short confirm/reject vibration on a verdict (system haptic feedback, no permission), Settings toggle.

### Text size
The app follows Android's font size setting: every font size is `Npx * Theme.text-scale`, set from
`Configuration.fontScale` at start and on resume, clamped to 1.0–1.3 (`set_text_scale`,
`MAX_TEXT_SCALE`). Button labels and titles wrap instead of being cut.

### Furigana layout (`core/src/layout.rs`)
Sentences are laid out in Rust (each character placed, readings above kanji, readings may overhang
kana, no line starts with closing punctuation, lines without readings get no reading band); Slint
only draws the glyphs. Character widths are estimates (`char_em`): each character gets its own box.

### Localisation
UI strings: `@tr("...")` in `app.slint`, French in `rust/app/lang/fr/LC_MESSAGES/bunpo-app.po`
(a test fails if a string has no French). Strings built in Rust (labels with numbers, hints) use
`Lang` (`core/src/i18n.rs`). Point texts in French: `pipeline/fr/points_n*.py`; sentence
translations: `pipeline/fr/sentences_n*.tsv` (`id<TAB>Japanese<TAB>French`, the Japanese must match).

## Common changes

- **A UI string**: add it with `@tr` and its msgid/msgstr in the `.po`; run the UI tests (they check
  French exists and every screen still fits at 360 px, in both languages, at the largest text size).
- **A new screen element**: one-line texts that could be squeezed use `FitText` (it reports itself
  when cut); fixed bars and dialogs carry `accessible-role: groupbox` with label `bar` / `dialog` so
  the layout audit treats them right; give buttons an accessible label (tests press them by label).
- **A grammar point**: add it to `grammar_n*.py` (example sentence must match exactly once), its
  French text in `fr/points_n*.py`, rebuild content; if Tatoeba has fewer than 8 sentences, add
  original examples to `extra_examples.py` (+ French in the tsv). Check matches for look-alikes and
  add false positives to `NEGATIVE` in `pipeline/tests/test_levels.py`.
- **Points that are near-synonyms**: add a group in `pipeline/alternatives.py` with each member's
  endings, a `NUANCE` text (EN/FR, without the answer) and context rules; read a sample of the
  generated swaps before trusting them.
- **A progress field**: `serde(default)`, and think about import (`Progress::import`) and reset.
- **Anything platform-specific**: add a method to the `Platform` trait (default no-op) so the
  headless tests and desktop keep working, implement it in `android.rs`.

## Things that bite

- Never rename a point id (it would orphan everyone's progress for that point).
- The content is compiled in: after `build.py`, rebuild the app/APK.
- Matchers produce false positives (literal verbs, set phrases, kana homographs): read the sentences
  a matcher selects before trusting it.
- Slint only reports elements inside the window to its search API: headless tests use tall windows;
  on the device, scroll to things first.
- On the emulator, the app answers test commands only when its external files folder holds
  `e2e.on`; command files must belong to the app's user (see `rust/e2e/lib.sh`).
- The release build keeps Slint's element debug info on purpose (the layout audit needs it).
- `rust/third_party/i-slint-core` is a patched Slint core: keep the patch when upgrading Slint.
