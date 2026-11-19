//! Slint front-end for the grammar SRS. All logic lives in `bunpo-core`; this file wires it
//! to the UI. Platform specifics (reminders, keyboard) go through [`Platform`] so the whole
//! UI can be driven headlessly in tests (see `tests/ui.rs`).

use bunpo_core::content::Content;
use bunpo_core::i18n::{tr, Lang};
use bunpo_core::layout::{self, ClozeMode, Metrics};
use bunpo_core::lessons::{lesson_queue, LEVELS as JLPT_LEVELS};
use bunpo_core::clock::date_string;
use bunpo_core::reminder::next_reminder;
use bunpo_core::session::{find_sentence, now_ms, Session, Verdict};
use bunpo_core::store::{Progress, Report, REPORT_REASONS};
use slint::{ComponentHandle, Model, ModelRc, SharedString, VecModel};
use std::cell::RefCell;
use std::path::PathBuf;
use std::rc::Rc;

#[cfg(target_os = "android")]
mod android;
pub mod audit;

slint::include_modules!();

pub const SCREEN_HOME: i32 = 0;
pub const SCREEN_LESSON: i32 = 1;
pub const SCREEN_QUIZ: i32 = 2;
pub const SCREEN_LIST: i32 = 3;
pub const SCREEN_DETAIL: i32 = 4;
pub const SCREEN_SETTINGS: i32 = 5;
pub const SCREEN_STATS: i32 = 6;

/// SRS stage colors: New (neutral grey), then Beginner → Mastered as one blue ramp that gets
/// brighter (= further along) on the dark surface. Validated as an ordinal ramp against the
/// card color (#2b2a33): monotone lightness, visible steps, darkest step ≥ 2:1 contrast.
const STAGE_COLORS: [(u8, u8, u8); 6] =
    [(0x55, 0x53, 0x5e), (0x25, 0x6a, 0xbf), (0x39, 0x87, 0xe5), (0x6d, 0xa7, 0xec), (0x9e, 0xc5, 0xf4), (0xcd, 0xe2, 0xfb)];

fn stage_color(i: usize) -> slint::Color {
    let (r, g, b) = STAGE_COLORS[i];
    slint::Color::from_rgb_u8(r, g, b)
}

/// One pie per JLPT level: points per SRS stage (New, Beginner ... Mastered).
pub fn level_pies(content: &Content, progress: &Progress) -> Vec<LevelPie> {
    let mut out: Vec<(String, [u32; 6])> = vec![];
    for p in &content.points {
        if out.last().is_none_or(|(n, _)| *n != p.level) {
            out.push((p.level.clone(), [0; 6]));
        }
        let card = progress.card(&p.id);
        let stage = if card.is_new() { 0 } else { 1 + LEVELS.iter().position(|l| *l == card.level_name()).unwrap_or(0) };
        out.last_mut().unwrap().1[stage] += 1;
    }
    out.into_iter()
        .map(|(name, counts)| LevelPie {
            name: name.into(),
            learned: (counts.iter().sum::<u32>() - counts[0]) as i32,
            total: counts.iter().sum::<u32>() as i32,
            counts: model(counts.iter().map(|&c| c as i32).collect()),
            slices: model(
                bunpo_core::chart::pie_slices(&counts, 100.0)
                    .into_iter()
                    .map(|s| PieSlice { path: s.path.into(), fill: stage_color(s.category) })
                    .collect(),
            ),
        })
        .collect()
}
const RETENTIONS: [f64; 3] = [0.85, 0.9, 0.95];
const LEVELS: [&str; 5] = ["Beginner", "Adept", "Seasoned", "Expert", "Mastered"];

/// Things only the host OS can do.
pub trait Platform {
    /// Arm (or replace) the review reminder; `text` is the notification text (already translated:
    /// the notification is shown by the OS while the app may not be running).
    fn schedule_reminder(&self, at_ms: i64, count: usize, text: &str, channel: &str);
    fn cancel_reminder(&self);
    /// Remove a reminder notification that is currently shown.
    fn dismiss_reminder(&self) {}
    fn request_notification_permission(&self) {}
    /// Save a copy of the progress file (`path`) where the user picks, suggesting `name`.
    /// The outcome is left in `backup-result.txt` next to it (see [`check_backup_files`]).
    fn export_progress(&self, _path: &str, _name: &str) {}
    /// Let the user pick an exported file; it is copied next to the progress as
    /// `progress.import.json` and imported when the app comes back (see [`check_backup_files`]).
    fn pick_import(&self) {}
    /// Show `word` in the Takoboto dictionary (the app if installed, else its website).
    fn lookup_word(&self, _word: &str) {}
    /// A short vibration for a checked answer (the system's "confirm" or "reject" feedback).
    fn haptic(&self, _correct: bool) {}
    /// Called shortly after start-up.
    fn on_started(&self) {}
}

/// Desktop/test platform: does nothing.
pub struct NoPlatform;
impl Platform for NoPlatform {
    fn schedule_reminder(&self, _: i64, _: usize, _: &str, _: &str) {}
    fn cancel_reminder(&self) {}
}

/// Structured event log (logcat on Android, stderr elsewhere) used by the emulator e2e tests.
pub fn event(msg: &str) {
    #[cfg(target_os = "android")]
    android::log(msg);
    #[cfg(not(target_os = "android"))]
    if std::env::var_os("BUNPO_EVENTS").is_some() {
        eprintln!("bunpo-event {msg}");
    }
}

thread_local! {
    /// Called when the app comes back to the foreground (Android resume).
    static RESUME_HOOK: RefCell<Option<Box<dyn Fn()>>> = const { RefCell::new(None) };
}

/// Refresh time-dependent data (due counts) after the app was in the background.
pub fn on_resume() {
    RESUME_HOOK.with(|h| {
        if let Some(f) = &*h.borrow() {
            f()
        }
    });
}

/// The composition to add to `field`: only while the field is unchanged since the composition was
/// reported (`with`). Once the keyboard commits it (e.g. when Check takes the focus), it is part of
/// the field and must not be added a second time.
fn composition_for(composing: &(String, usize), with: &str, field: &str) -> (String, usize) {
    if field == with { composing.clone() } else { (String::new(), 0) }
}

pub struct State {
    pub progress: Progress,
    stack: Vec<i32>,
    lesson_ids: Vec<String>,
    lesson_idx: usize,
    pub session: Option<Session>,
    detail: Option<String>,
    /// JLPT levels folded in the grammar list (for this run of the app)
    collapsed: std::collections::HashSet<String>,
    /// the sentence the open report dialog is about
    report_target: Option<Report>,
    /// what the last export was ("progress" or "reports"), for its result message
    exporting: &'static str,
    /// the keyboard's composition in the answer field (not confirmed yet), where it goes, and the
    /// field text it was reported with (see [`composition_for`])
    composing: (String, usize),
    composing_with: String,
}

/// The running app: UI + state. Keep it alive while the UI runs.
pub struct App {
    pub ui: AppWindow,
    pub state: Rc<RefCell<State>>,
    pub content: Rc<Content>,
    _timer: slint::Timer,
}

fn model<T: Clone + 'static>(v: Vec<T>) -> ModelRc<T> {
    ModelRc::new(VecModel::from(v))
}

pub fn rel_time(lang: Lang, due: i64, now: i64) -> String {
    let d = due - now;
    let fr = lang == Lang::Fr;
    if d <= 0 {
        return if fr { "maintenant" } else { "now" }.into();
    }
    let m = d / 60_000;
    let days = (m + 60 * 12) / (60 * 24);
    match (m, fr) {
        _ if m < 60 => format!("{} {} min", if fr { "dans" } else { "in" }, m + 1),
        _ if m < 60 * 24 => format!("{} {} h {} min", if fr { "dans" } else { "in" }, m / 60, m % 60),
        (_, false) => format!("in {days} days"),
        (_, true) => format!("dans {days} jours"),
    }
}

/// Text of the review reminder notification.
pub fn reminder_text(lang: Lang, count: usize) -> String {
    match (lang, count) {
        (Lang::En, 1) => "1 grammar review is waiting".into(),
        (Lang::En, n) => format!("{n} grammar reviews are waiting"),
        (Lang::Fr, 1) => "1 révision de grammaire vous attend".into(),
        (Lang::Fr, n) => format!("{n} révisions de grammaire vous attendent"),
    }
}

/// Pick up what the file picker left behind (see [`Platform::export_progress`] / `pick_import`):
/// an imported file to load, or the outcome of an export. Returns a message for the user.
pub fn check_backup_files(st: &mut State) -> Option<String> {
    let dir = st.progress.path()?.parent()?.to_path_buf();
    let fr = st.progress.settings.lang() == Lang::Fr;
    let incoming = dir.join("progress.import.json");
    if let Ok(text) = std::fs::read_to_string(&incoming) {
        let _ = std::fs::remove_file(&incoming);
        let msg = match st.progress.import(&text) {
            Ok(n) => {
                // the imported file may change the language too
                let fr = st.progress.settings.lang() == Lang::Fr;
                if fr { format!("Progression importée : {n} points appris.") } else { format!("Progress imported: {n} learned points.") }
            }
            Err(e) => {
                event(&format!("import failed: {e}"));
                if fr { "Import impossible : ce n'est pas un fichier de progression." } else { "Import failed: this is not a progress file." }
                    .into()
            }
        };
        event(&format!("imported: {msg}"));
        return Some(msg);
    }
    let result = dir.join("backup-result.txt");
    let outcome = std::fs::read_to_string(&result).ok()?;
    let _ = std::fs::remove_file(&result);
    event(&format!("backup {outcome}"));
    Some(
        match (outcome.trim(), fr) {
            ("exported", false) if st.exporting == "reports" => "Reports exported.",
            ("exported", true) if st.exporting == "reports" => "Signalements exportés.",
            ("exported", false) => "Progress exported.",
            ("exported", true) => "Progression exportée.",
            ("cancelled", false) => "Cancelled.",
            ("cancelled", true) => "Annulé.",
            (_, false) => "Something went wrong, nothing was changed.",
            (_, true) => "Une erreur s'est produite, rien n'a été modifié.",
        }
        .into(),
    )
}

/// The reports as a JSON file meant to be read (by a person or Claude): each one with the
/// sentence text, its translations and the grammar point, not only ids.
pub fn reports_json(content: &Content, progress: &Progress) -> String {
    let items: Vec<serde_json::Value> = progress
        .reports
        .iter()
        .map(|r| {
            let p = content.get(&r.point);
            let s = p.and_then(|p| find_sentence(p, r.sentence));
            serde_json::json!({
                "date": date_string(r.ts),
                "point": r.point,
                "point_title": p.map(|p| p.title.as_str()).unwrap_or(""),
                "sentence": r.sentence,
                "japanese": s.map(|s| s.ja.as_str()).unwrap_or(""),
                "english": s.map(|s| s.en.as_str()).unwrap_or(""),
                "french": s.map(|s| s.fr.as_str()).unwrap_or(""),
                "answers": s.map(|s| s.answers.clone()).unwrap_or_default(),
                "reason": r.reason,
                "note": r.note,
                "typed": r.answer,
                "app_language": r.lang,
            })
        })
        .collect();
    serde_json::to_string_pretty(&serde_json::json!({ "reports": items })).unwrap()
}

/// Split chips into rows no wider than `width`: each chip is its text (CJK characters about
/// one font size wide, others about half) plus 24 of padding, with 8 between chips.
pub fn chip_rows(words: &[String], width: f32, font: f32) -> Vec<Vec<String>> {
    let chip = |w: &str| w.chars().map(|c| if (c as u32) < 0x2E80 { font * 0.6 } else { font }).sum::<f32>() + 24.0;
    let mut rows: Vec<Vec<String>> = vec![];
    let mut used = f32::INFINITY;
    for w in words {
        let need = chip(w);
        if used + 8.0 + need > width {
            rows.push(vec![]);
            used = -8.0;
        }
        used += 8.0 + need;
        rows.last_mut().unwrap().push(w.clone());
    }
    rows
}

/// Switch the Slint UI strings (@tr) to `lang`; "" is the untranslated (English) source.
fn apply_language(lang: Lang) {
    let code = if lang == Lang::Fr { "fr" } else { "" };
    if let Err(e) = slint::select_bundled_translation(code) {
        event(&format!("translation {code:?} not available: {e:?}"));
    }
}

fn sentence_key(point: &str, sid: u64) -> SharedString {
    format!("{point}:{sid}").into()
}

fn point_data(content: &Content, st: &State, id: &str) -> PointData {
    let p = content.get(id).expect("known point");
    let card = st.progress.card(id);
    let lang = st.progress.settings.lang();
    let status = match (card.is_new(), lang) {
        (true, Lang::En) => "Status: not learned yet".to_string(),
        (true, Lang::Fr) => "Statut : pas encore appris".to_string(),
        (false, Lang::En) => format!(
            "Status: {} · next review {} · reviews {} · lapses {}",
            card.level_name(),
            rel_time(lang, card.due, now_ms()),
            card.reps,
            card.lapses
        ),
        (false, Lang::Fr) => format!(
            "Statut : {} · prochaine révision {} · révisions {} · oublis {}",
            tr(lang, card.level_name()),
            rel_time(lang, card.due, now_ms()),
            card.reps,
            card.lapses
        ),
    };
    PointData {
        id: p.id.as_str().into(),
        title: p.title_in(lang).into(),
        level: p.level.as_str().into(),
        meaning: p.meaning_in(lang).into(),
        structure: p.structure_in(lang).into(),
        explanation: p.explanation_in(lang).replace('\n', " ").into(),
        status: status.into(),
        can_reset: !card.is_new(),
        examples: model(
            p.sentences
                .iter()
                .map(|s| Example { key: sentence_key(&p.id, s.id), en: s.translation(lang).into() })
                .collect(),
        ),
    }
}

pub fn due_ids(content: &Content, progress: &Progress, now: i64) -> Vec<String> {
    let mut v: Vec<(i64, String)> = content
        .points
        .iter()
        .filter_map(|p| progress.cards.get(&p.id).filter(|c| c.state > 0 && c.due <= now).map(|c| (c.due, p.id.clone())))
        .collect();
    v.sort();
    v.into_iter().map(|(_, id)| id).collect()
}

/// Points first learned today (local time): counted against the daily goal.
pub fn learned_today(progress: &Progress, now: i64) -> usize {
    let today = bunpo_core::clock::local_day(now);
    progress.cards.values().filter(|c| c.learned_at > 0 && bunpo_core::clock::local_day(c.learned_at) == today).count()
}

/// Size of the next lesson: what is left of today's goal, or a whole goal's worth once it is reached
/// (an extra lesson). Returns (size, extra).
fn next_lesson_size(progress: &Progress, now: i64) -> (usize, bool) {
    let goal = progress.settings.batch_size as usize;
    let left = goal.saturating_sub(learned_today(progress, now));
    if left > 0 { (left, false) } else { (goal, true) }
}

fn new_ids(content: &Content, progress: &Progress) -> Vec<String> {
    content.points.iter().filter(|p| progress.card(&p.id).is_new()).map(|p| p.id.clone()).collect()
}

/// The "almost" hint for a nudge, in the UI language. Never says what the answer is.
pub fn nudge_text(lang: Lang, n: &bunpo_core::hints::Nudge, point: &bunpo_core::content::GrammarPoint) -> String {
    use bunpo_core::hints::{Aspect, Nudge};
    let fr = lang == Lang::Fr;
    match n {
        Nudge::Nuance => match (&point.nuance, fr) {
            (Some((_, f)), true) => format!("Ça pourrait aller, mais ici on cherche {f}."),
            (Some((e, _)), false) => format!("That could work, but here we're looking for {e}."),
            (None, true) => "Ça pourrait aller, mais ce n'est pas le point de grammaire travaillé ici.".to_string(),
            (None, false) => "That could work, but it's not the grammar point practised here.".to_string(),
        },
        Nudge::Particle => {
            if fr { "Presque ! Vérifie la particule." } else { "Almost! Check the particle." }.to_string()
        }
        Nudge::Form(aspects) if aspects.is_empty() => {
            if fr { "Presque ! Le bon mot, mais vérifie sa forme." } else { "Almost! Right word, but check its form." }.to_string()
        }
        Nudge::Form(aspects) => {
            let names: Vec<&str> = aspects
                .iter()
                .map(|a| match (a, fr) {
                    (Aspect::Tense, false) => "tense",
                    (Aspect::Tense, true) => "temps",
                    (Aspect::Politeness, false) => "politeness",
                    (Aspect::Politeness, true) => "politesse",
                    (Aspect::TeForm, false) => "て-form",
                    (Aspect::TeForm, true) => "forme en て",
                    (Aspect::Negative, false) => "positive or negative",
                    (Aspect::Negative, true) => "affirmatif ou négatif",
                })
                .collect();
            if fr {
                format!("Presque ! Le bon mot, vérifie la forme : {}.", names.join(", "))
            } else {
                format!("Almost! Right word, check the form: {}.", names.join(", "))
            }
        }
    }
}

/// The answer field's text with the keyboard's composition inserted at `at` (a byte offset).
pub fn with_composition(text: &str, (preedit, at): &(String, usize)) -> String {
    if preedit.is_empty() {
        return text.to_string();
    }
    let mut at = (*at).min(text.len());
    while !text.is_char_boundary(at) {
        at -= 1;
    }
    format!("{}{}{}", &text[..at], preedit, &text[at..])
}

/// Items left in the saved (unfinished) lesson quiz or review session, 0 if there is none.
fn paused_left(content: &Content, st: &State, lesson: bool) -> i32 {
    match &st.progress.paused {
        Some(s) if s.lesson == lesson && s.resumable(content) => s.remaining() as i32,
        _ => 0,
    }
}

/// Keep the running quiz in the progress file, so it can be resumed after leaving it (or after
/// the app was closed); a finished quiz leaves nothing to resume.
fn save_session(st: &mut State) {
    st.progress.paused = st.session.as_ref().filter(|s| !s.finished()).cloned();
    st.progress.save();
}

/// Leaving the quiz screen: an answer already checked counts, the rest can be resumed.
fn leave_session(content: &Content, st: &mut State) {
    let st = &mut *st;
    if let Some(sess) = st.session.as_mut() {
        sess.commit_pending(content, &mut st.progress);
        save_session(st);
    }
    st.session = None;
}

fn refresh_home(ui: &AppWindow, content: &Content, st: &State) {
    let now = now_ms();
    let due = due_ids(content, &st.progress, now).len() as i32;
    let new = new_ids(content, &st.progress);
    let queue = lesson_queue(content, &st.progress);
    let (batch, extra) = next_lesson_size(&st.progress, now);
    let goal = st.progress.settings.batch_size as usize;
    let today = learned_today(&st.progress, now);
    let next_due = st.progress.cards.values().filter(|c| c.state > 0).map(|c| c.due).min();
    let mut levels = [0i32; 5];
    for c in st.progress.cards.values() {
        if let Some(i) = LEVELS.iter().position(|l| *l == c.level_name()) {
            levels[i] += 1;
        }
    }
    let lang = st.progress.settings.lang();
    let next_titles: Vec<&str> =
        queue.iter().take(batch).filter_map(|id| content.get(id)).map(|p| p.title_in(lang)).collect();
    event(&format!("home due={due} learned={}", content.points.len() - new.len()));
    ui.set_home(HomeData {
        due,
        new_count: queue.len() as i32,
        start_level: st.progress.settings.start_level.as_str().into(),
        learned: (content.points.len() - new.len()) as i32,
        total: content.points.len() as i32,
        next_due: next_due.map(|d| rel_time(lang, d, now)).unwrap_or_default().into(),
        next_titles: next_titles.join("  ·  ").into(),
        learn_label: match (lang, extra) {
            (Lang::En, false) => format!("Learn {} new", batch.min(queue.len())),
            (Lang::En, true) => format!("Learn {} extra", batch.min(queue.len())),
            (Lang::Fr, false) => format!("Apprendre {} nouveaux", batch.min(queue.len())),
            (Lang::Fr, true) => format!("Apprendre {} de plus", batch.min(queue.len())),
        }
        .into(),
        goal_line: match (lang, today >= goal) {
            (Lang::En, false) => format!("Today: {today} / {goal} new points"),
            (Lang::En, true) => format!("Daily goal reached ({today} / {goal}). Extra lessons mean more reviews in the next days."),
            (Lang::Fr, false) => format!("Aujourd'hui : {today} / {goal} nouveaux points"),
            (Lang::Fr, true) => format!("Objectif du jour atteint ({today} / {goal}). Des leçons en plus, ce sont plus de révisions les jours suivants."),
        }
        .into(),
        levels: model(levels.to_vec()),
        reviews_24h: st.progress.reviews_since(now - 86_400_000) as i32,
        source: content.source_in(lang).into(),
        level_rows: model(level_rows(content, &st.progress)),
        resume_reviews: paused_left(content, st, false),
        resume_lesson: paused_left(content, st, true),
    });
    ui.set_level_pies(model(level_pies(content, &st.progress)));
    refresh_stats(ui, content, st, now);
}

/// Weeks shown in the activity calendar.
pub const ACTIVITY_WEEKS: usize = 15;

fn day_label(lang: Lang, day: i64) -> String {
    let (_, m, d) = bunpo_core::clock::civil_date(day);
    let wd = (day + 3).rem_euclid(7) as usize; // 1970-01-01 was a Thursday; 0 = Monday
    match lang {
        Lang::En => {
            let w = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][wd];
            let mo = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m as usize - 1];
            format!("{w} {d} {mo}")
        }
        Lang::Fr => {
            let w = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."][wd];
            let mo = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."][m as usize - 1];
            format!("{w} {d} {mo}")
        }
    }
}

/// Activity calendar cells, column by column (one column per week, Monday on top). Days after
/// today have level -1 (not drawn).
pub fn activity_cells(lang: Lang, progress: &Progress, now: i64) -> Vec<DayCell> {
    let today = bunpo_core::clock::local_day(now);
    let weekday = (today + 3).rem_euclid(7);
    let first = today - weekday - 7 * (ACTIVITY_WEEKS as i64 - 1);
    let days = (today - first + 1) as usize;
    let counts = bunpo_core::stats::activity(progress, now, days);
    (0..ACTIVITY_WEEKS * 7)
        .map(|i| {
            let day = first + i as i64;
            if day > today {
                return DayCell { level: -1, label: "".into() };
            }
            let n = counts[i];
            let level = match n {
                0 => 0,
                1..=5 => 1,
                6..=15 => 2,
                16..=30 => 3,
                _ => 4,
            };
            let label = match (lang, n) {
                (Lang::En, 1) => format!("{}: 1 review", day_label(lang, day)),
                (Lang::En, _) => format!("{}: {n} reviews", day_label(lang, day)),
                (Lang::Fr, 0 | 1) => format!("{}\u{a0}: {n} révision", day_label(lang, day)),
                (Lang::Fr, _) => format!("{}\u{a0}: {n} révisions", day_label(lang, day)),
            };
            DayCell { level, label: label.into() }
        })
        .collect()
}

fn refresh_stats(ui: &AppWindow, content: &Content, st: &State, now: i64) {
    use bunpo_core::stats;
    let lang = st.progress.settings.lang();
    let fr = lang == Lang::Fr;
    let (cur, best) = stats::streak(&st.progress, now);
    let days = |n: usize| match (fr, n) {
        (false, 1) => "1 day".to_string(),
        (false, _) => format!("{n} days"),
        (true, 0 | 1) => format!("{n} jour"),
        (true, _) => format!("{n} jours"),
    };
    ui.set_streak_line(
        if fr { format!("Série\u{a0}: {} · record\u{a0}: {}", days(cur), days(best)) } else { format!("Streak: {} · best: {}", days(cur), days(best)) }
            .into(),
    );
    let cells = activity_cells(lang, &st.progress, now);
    ui.set_activity(model(cells));
    let today = bunpo_core::clock::local_day(now);
    let fc = stats::forecast(&st.progress, now, 7);
    ui.set_forecast_max(fc.iter().copied().max().unwrap_or(0).max(1) as i32);
    ui.set_forecast(model(
        fc.iter()
            .enumerate()
            .map(|(i, &n)| ForecastBar {
                label: if i == 0 {
                    (if fr { "Auj." } else { "Today" }).into()
                } else {
                    day_label(lang, today + i as i64).split(' ').next().unwrap_or("").into()
                },
                count: n as i32,
            })
            .collect(),
    ));
    ui.set_leeches(model(
        stats::leeches(&st.progress)
            .into_iter()
            .filter_map(|(id, n)| {
                let p = content.get(&id)?;
                Some(Leech {
                    id: id.as_str().into(),
                    title: p.title_in(lang).into(),
                    meaning: p.meaning_in(lang).into(),
                    mistakes: format!("{n} / {}", stats::LEECH_WINDOW).into(),
                })
            })
            .collect(),
    ));
}

/// Learned / total per JLPT level, in content order (N5 first).
pub fn level_rows(content: &Content, progress: &Progress) -> Vec<LevelRow> {
    let mut rows: Vec<LevelRow> = vec![];
    for p in &content.points {
        if rows.last().is_none_or(|r| r.name != p.level.as_str()) {
            rows.push(LevelRow { name: p.level.as_str().into(), learned: 0, total: 0 });
        }
        let r = rows.last_mut().unwrap();
        r.total += 1;
        if !progress.card(&p.id).is_new() {
            r.learned += 1;
        }
    }
    rows
}

fn refresh_list(ui: &AppWindow, content: &Content, st: &State) {
    let mut items = vec![];
    let lang = st.progress.settings.lang();
    // one header row per JLPT level (tap to fold it), then its points unless folded
    for row in level_rows(content, &st.progress) {
        let level = row.name.to_string();
        let collapsed = st.collapsed.contains(&level);
        items.push(ListItem {
            id: level.as_str().into(),
            header: format!("JLPT {level}").into(),
            num: format!("{} / {}", row.learned, row.total).into(),
            collapsed,
            ..Default::default()
        });
        if collapsed {
            continue;
        }
        for (n, p) in content.points.iter().filter(|p| p.level == level).enumerate() {
            items.push(ListItem {
                id: p.id.as_str().into(),
                num: (n + 1).to_string().into(),
                title: p.title_in(lang).into(),
                meaning: p.meaning_in(lang).into(),
                level: tr(lang, st.progress.card(&p.id).level_name()).into(),
                ..Default::default()
            });
        }
    }
    ui.set_grammar_list(model(items));
}

fn refresh_settings(ui: &AppWindow, st: &State) {
    let s = &st.progress.settings;
    ui.set_furigana(s.furigana);
    ui.set_english(s.english);
    ui.set_romaji(s.romaji);
    ui.set_notifications(s.notifications);
    ui.set_haptics(s.haptics);
    ui.set_batch_size(s.batch_size as i32);
    let li = JLPT_LEVELS.iter().position(|l| *l == s.start_level).unwrap_or(0);
    ui.set_start_level_index(li as i32);
    let ri = RETENTIONS.iter().position(|r| (r - s.retention).abs() < 1e-6).unwrap_or(1);
    ui.set_retention_index(ri as i32);
    ui.set_language_index(if s.lang() == Lang::Fr { 1 } else { 0 });
    ui.set_report_count(st.progress.reports.len() as i32);
}

fn refresh_quiz(ui: &AppWindow, content: &Content, st: &State) {
    let Some(sess) = &st.session else { return };
    let lang = st.progress.settings.lang();
    let fr = lang == Lang::Fr;
    let mut q = QuizData {
        title: match (sess.lesson, fr) {
            (true, false) => "Lesson quiz",
            (false, false) => "Reviews",
            (true, true) => "Quiz de la leçon",
            (false, true) => "Révisions",
        }
        .into(),
        done: sess.done as i32,
        total: sess.total as i32,
        lesson: sess.lesson,
        answered: sess.answered() as i32,
        practising: sess.practising() && sess.verdict.is_none(),
        fixing_typo: sess.fixing_typo && sess.verdict.is_none(),
        nudge: match (&sess.nudge, sess.current(content)) {
            (Some(n), Some((p, _))) => nudge_text(lang, n, p).into(),
            _ => Default::default(),
        },
        finished: sess.finished(),
        summary: if fr {
            format!("{} / {} justes du premier coup.", sess.correct_first_try, sess.total)
        } else {
            format!("{} / {} correct on the first try.", sess.correct_first_try, sess.total)
        }
        .into(),
        ..Default::default()
    };
    if let Some((p, s)) = sess.current(content) {
        if sess.verdict.is_none() && sess.raw.is_empty() {
            event(&format!("item point={} sentence={}", p.id, s.id));
        }
        q.key = sentence_key(&p.id, s.id);
        q.en = s.translation(lang).into();
        q.hint = s.hint(lang).unwrap_or_else(|| p.meaning_in(lang).to_string()).into();
        q.verdict = match sess.verdict {
            None => 0,
            Some(Verdict::Correct) => 1,
            Some(Verdict::Wrong) => 2,
        };
        q.last_answer = sess.last_answer.as_str().into();
        q.answer = s.answers.iter().take(2).cloned().collect::<Vec<_>>().join("  /  ").into();
        q.grammar_line = if fr {
            format!("Grammaire : {} — {}", p.title_in(lang), p.meaning_in(lang))
        } else {
            format!("Grammar: {} — {}", p.title, p.meaning)
        }
        .into();
        q.attribution = s.attribution(lang).into();
        q.words = model(s.words.iter().map(|w| SharedString::from(w.as_str())).collect());
        q.reported = st.progress.reports.iter().any(|r| r.point == p.id && r.sentence == s.id);
        ui.set_notes(point_data(content, st, &p.id));
    }
    ui.set_quiz(q);
    ui.set_quiz_preview(sess.input.as_str().into());
    if ui.get_quiz_input() != sess.raw.as_str() {
        ui.set_quiz_input(sess.raw.as_str().into());
    }
}

fn show(ui: &AppWindow, st: &mut State, screen: i32) {
    let cur = ui.get_screen();
    if screen == SCREEN_HOME {
        st.stack.clear();
    } else if [SCREEN_LIST, SCREEN_STATS, SCREEN_SETTINGS].contains(&screen) {
        // menu-bar tabs: switching tabs doesn't pile up history, Back goes home
        st.stack = vec![SCREEN_HOME];
    } else if cur != screen {
        st.stack.push(cur);
    }
    ui.set_show_notes(false);
    ui.set_screen(screen);
    event(&format!("screen={screen}"));
}

/// Re-arm (or cancel) the review reminder after any change to progress or settings.
fn sync_reminder(platform: &dyn Platform, progress: &Progress) {
    if !progress.settings.notifications {
        platform.cancel_reminder();
        return;
    }
    match next_reminder(progress.cards.values(), now_ms()) {
        Some((at, count)) => {
            event(&format!("reminder at={at} count={count}"));
            let lang = progress.settings.lang();
            let channel = if lang == Lang::Fr { "Rappels de révision" } else { "Review reminders" };
            platform.schedule_reminder(at, count, &reminder_text(lang, count), channel)
        }
        None => platform.cancel_reminder(),
    }
}

fn layout_for(content: &Content, key: &str, mode: i32, typed: &str, furigana: bool, width: f32, font: f32) -> SentenceData {
    let Some((pid, sid)) = key.split_once(':') else { return SentenceData::default() };
    let Some(s) = content.get(pid).and_then(|p| find_sentence(p, sid.parse().unwrap_or(0))) else {
        return SentenceData::default();
    };
    let mode = match mode {
        1 => ClozeMode::Blank,
        2 => ClozeMode::Revealed,
        _ => ClozeMode::Highlight,
    };
    let l = layout::layout(s, width.max(50.0), Metrics::new(font, furigana), mode, typed);
    SentenceData {
        glyphs: model(
            l.glyphs
                .into_iter()
                .map(|g| Glyph {
                    x: g.x,
                    y: g.y,
                    w: g.w,
                    text: g.text.into(),
                    ruby: g.ruby.into(),
                    ruby_x: g.ruby_x,
                    ruby_w: g.ruby_w,
                    cloze: g.in_cloze,
                })
                .collect(),
        ),
        frames: model(l.cloze_rects.iter().map(|r| Frame { x: r.x, y: r.y, w: r.w, h: r.h }).collect()),
        cloze_x: l.cloze.x,
        cloze_y: l.cloze.y,
        cloze_w: l.cloze.w,
        cloze_h: l.cloze.h,
        height: l.height,
        ruby_h: l.ruby_h,
        main_h: l.main_h,
    }
}

/// Create the UI and wire every callback. Does not start the event loop.
pub fn build(progress: Progress, platform: Rc<dyn Platform>) -> Result<App, slint::PlatformError> {
    let content = Rc::new(Content::bundled());
    let st = Rc::new(RefCell::new(State {
        progress,
        stack: vec![],
        lesson_ids: vec![],
        lesson_idx: 0,
        session: None,
        composing: (String::new(), 0),
        composing_with: String::new(),
        detail: None,
        collapsed: Default::default(),
        report_target: None,
        exporting: "progress",
    }));
    let ui = AppWindow::new()?;
    ui.set_stage_colors(model((0..6).map(stage_color).collect()));

    {
        let c = content.clone();
        ui.global::<Logic>().on_layout(move |key, mode, typed, furi, width, font| {
            layout_for(&c, &key, mode, &typed, furi, width, font)
        });
        ui.global::<Logic>().on_chip_rows(|words, width, font| {
            let words: Vec<String> = words.iter().map(|w| w.to_string()).collect();
            model(chip_rows(&words, width, font).into_iter().map(|r| ChipRow { words: model(r.into_iter().map(SharedString::from).collect()) }).collect())
        });
    }

    // clone the handles a callback needs: `cb!(|ui, c, st| body)`; add `p` for the platform
    macro_rules! cb {
        (|$ui:ident, $c:ident, $st:ident $(, $p:ident)?| $body:expr) => {{
            let w = ui.as_weak();
            let $c = content.clone();
            let $st = st.clone();
            $( let $p = platform.clone(); )?
            move || {
                let Some($ui) = w.upgrade() else { return };
                #[allow(unused_mut)]
                let mut $st = $st.borrow_mut();
                let _ = &$c;
                $body
            }
        }};
    }

    ui.on_start_learn(cb!(|ui, c, st| {
        let (size, _) = next_lesson_size(&st.progress, now_ms());
        let ids: Vec<String> = lesson_queue(&c, &st.progress).into_iter().take(size).collect();
        if ids.is_empty() {
            return;
        }
        st.lesson_ids = ids;
        st.lesson_idx = 0;
        ui.set_lesson_count(st.lesson_ids.len() as i32);
        ui.set_lesson_index(0);
        ui.set_lesson_point(point_data(&c, &st, &st.lesson_ids[0].clone()));
        show(&ui, &mut st, SCREEN_LESSON);
    }));

    ui.on_lesson_prev(cb!(|ui, c, st| {
        if st.lesson_idx > 0 {
            st.lesson_idx -= 1;
            ui.set_lesson_index(st.lesson_idx as i32);
            ui.set_lesson_point(point_data(&c, &st, &st.lesson_ids[st.lesson_idx].clone()));
        }
    }));

    ui.on_lesson_next(cb!(|ui, c, st| {
        if st.lesson_idx + 1 < st.lesson_ids.len() {
            st.lesson_idx += 1;
            ui.set_lesson_index(st.lesson_idx as i32);
            ui.set_lesson_point(point_data(&c, &st, &st.lesson_ids[st.lesson_idx].clone()));
        } else {
            let ids = st.lesson_ids.clone();
            st.session = Some(Session::new(&c, &st.progress, ids, true));
            save_session(&mut st);
            st.stack.clear();
            st.stack.push(SCREEN_HOME);
            ui.set_screen(SCREEN_QUIZ);
            event("screen=2 lesson");
            refresh_quiz(&ui, &c, &st);
            ui.set_focus_tick(ui.get_focus_tick() + 1);
        }
    }));

    ui.on_start_reviews(cb!(|ui, c, st| {
        let mut ids = due_ids(&c, &st.progress, now_ms());
        if ids.is_empty() {
            return;
        }
        fastrand::shuffle(&mut ids);
        st.session = Some(Session::new(&c, &st.progress, ids, false));
        save_session(&mut st);
        show(&ui, &mut st, SCREEN_QUIZ);
        refresh_quiz(&ui, &c, &st);
        ui.set_focus_tick(ui.get_focus_tick() + 1);
    }));

    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        ui.on_quiz_edited(move |text| {
            let mut st = st.borrow_mut();
            let st = &mut *st;
            let romaji = st.progress.settings.romaji;
            let Some(sess) = st.session.as_mut() else { return text };
            let mut switched = false;
            if sess.verdict == Some(Verdict::Wrong) && text.as_str() != sess.raw {
                // editing a wrong answer (e.g. deleting a character): fixing a typo
                switched = sess.edit_after_wrong();
            } else if sess.verdict.is_some() {
                // answer already checked: keep showing what was submitted
                return sess.raw.as_str().into();
            }
            let full = with_composition(&text, &composition_for(&st.composing, &st.composing_with, &text));
            sess.on_input_composing(&text, &full, romaji);
            if let Some(ui) = w.upgrade() {
                ui.set_quiz_preview(sess.input.as_str().into());
                if switched {
                    refresh_quiz(&ui, &c, st);
                }
            }
            text
        });
    }

    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        ui.on_quiz_composing(move |text, preedit, cursor| {
            let mut st = st.borrow_mut();
            let st = &mut *st;
            st.composing = (preedit.to_string(), cursor.max(0) as usize);
            st.composing_with = text.to_string();
            let romaji = st.progress.settings.romaji;
            let Some(sess) = st.session.as_mut() else { return };
            let mut switched = false;
            if sess.verdict == Some(Verdict::Wrong) && !preedit.is_empty() {
                switched = sess.edit_after_wrong();
            } else if sess.verdict.is_some() {
                return;
            }
            let full = with_composition(&text, &composition_for(&st.composing, &st.composing_with, &text));
            sess.on_input_composing(&text, &full, romaji);
            if let Some(ui) = w.upgrade() {
                ui.set_quiz_preview(sess.input.as_str().into());
                if switched {
                    refresh_quiz(&ui, &c, st);
                }
            }
        });
    }

    ui.on_quiz_submit(cb!(|ui, c, st, p| {
        let st = &mut *st;
        let Some(sess) = st.session.as_mut() else { return };
        if sess.verdict.is_none() {
            // pick up the final text (e.g. typed with an IME, no `edited` for the last commit),
            // with what the keyboard is still composing
            let raw = ui.get_quiz_input();
            let full = with_composition(&raw, &composition_for(&st.composing, &st.composing_with, &raw));
            sess.on_input_composing(&raw, &full, st.progress.settings.romaji);
            if sess.submit(&c) && sess.verdict.is_none() {
                event(&format!("nudge={:?} point={} kana={:?}", sess.nudge, sess.point.as_deref().unwrap_or(""), sess.input));
            } else if sess.verdict.is_some() {
                if st.progress.settings.haptics {
                    p.haptic(sess.verdict == Some(Verdict::Correct));
                }
                event(&format!(
                    "verdict={:?} point={} raw={:?} kana={:?}",
                    sess.verdict.unwrap(),
                    sess.point.as_deref().unwrap_or(""),
                    sess.raw,
                    sess.input
                ));
            }
        } else {
            sess.next(&c, &mut st.progress);
            if sess.finished() {
                event(&format!("session-finished correct_first_try={} total={}", sess.correct_first_try, sess.total));
            }
            save_session(st);
            sync_reminder(&*p, &st.progress);
            ui.set_focus_tick(ui.get_focus_tick() + 1);
        }
        refresh_quiz(&ui, &c, st);
    }));

    ui.on_quiz_typo(cb!(|ui, c, st| {
        if let Some(s) = st.session.as_mut() {
            s.override_correct();
        }
        refresh_quiz(&ui, &c, &st);
    }));

    ui.on_quiz_retry(cb!(|ui, c, st| {
        if let Some(s) = st.session.as_mut() {
            s.retry();
        }
        refresh_quiz(&ui, &c, &st);
    }));

    ui.on_open_notes(cb!(|ui, c, st| {
        let _ = &st;
        ui.set_show_notes(true);
    }));

    ui.on_resume(cb!(|ui, c, st| {
        match st.progress.paused.clone() {
            Some(s) if s.resumable(&c) => {
                let lesson = s.lesson;
                st.session = Some(s);
                st.stack.clear();
                st.stack.push(SCREEN_HOME);
                ui.set_screen(SCREEN_QUIZ);
                event(if lesson { "screen=2 lesson resumed" } else { "screen=2 resumed" });
                refresh_quiz(&ui, &c, &st);
                ui.set_focus_tick(ui.get_focus_tick() + 1);
            }
            _ => {
                st.progress.paused = None;
                st.progress.save();
                refresh_home(&ui, &c, &st);
            }
        }
    }));

    ui.on_go_home(cb!(|ui, c, st| {
        leave_session(&c, &mut st);
        show(&ui, &mut st, SCREEN_HOME);
        refresh_home(&ui, &c, &st);
        refresh_list(&ui, &c, &st);
    }));

    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        ui.on_go_back(move || {
            let Some(ui) = w.upgrade() else { return false };
            let mut st = st.borrow_mut();
            let cur = ui.get_screen();
            if cur == SCREEN_HOME {
                return false;
            }
            let prev = if cur == SCREEN_QUIZ { SCREEN_HOME } else { st.stack.pop().unwrap_or(SCREEN_HOME) };
            if prev == SCREEN_HOME {
                st.stack.clear();
                leave_session(&c, &mut st);
            }
            ui.set_show_notes(false);
            ui.set_screen(prev);
            event(&format!("screen={prev} back"));
            refresh_home(&ui, &c, &st);
            refresh_list(&ui, &c, &st);
            if prev == SCREEN_DETAIL {
                if let Some(id) = st.detail.clone() {
                    ui.set_notes(point_data(&c, &st, &id));
                }
            }
            true
        });
    }

    ui.on_open_list(cb!(|ui, c, st| {
        refresh_list(&ui, &c, &st);
        show(&ui, &mut st, SCREEN_LIST);
    }));

    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        ui.on_toggle_level(move |level| {
            let Some(ui) = w.upgrade() else { return };
            let mut st = st.borrow_mut();
            let level = level.to_string();
            if !st.collapsed.remove(&level) {
                st.collapsed.insert(level);
            }
            refresh_list(&ui, &c, &st);
        });
    }

    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        ui.on_open_detail(move |id| {
            let Some(ui) = w.upgrade() else { return };
            let mut st = st.borrow_mut();
            st.detail = Some(id.to_string());
            ui.set_notes(point_data(&c, &st, &id));
            show(&ui, &mut st, SCREEN_DETAIL);
        });
    }

    ui.on_open_stats(cb!(|ui, c, st| {
        refresh_home(&ui, &c, &st);
        show(&ui, &mut st, SCREEN_STATS);
    }));

    ui.on_open_settings(cb!(|ui, c, st| {
        refresh_settings(&ui, &st);
        show(&ui, &mut st, SCREEN_SETTINGS);
    }));

    macro_rules! setting {
        ($on:ident, $ty:ty, |$s:ident, $v:ident| $apply:expr) => {{
            let w = ui.as_weak();
            let st = st.clone();
            let c = content.clone();
            let p = platform.clone();
            ui.$on(move |$v: $ty| {
                let Some(ui) = w.upgrade() else { return };
                let mut st = st.borrow_mut();
                {
                    let $s = &mut st.progress.settings;
                    $apply;
                }
                st.progress.save();
                refresh_settings(&ui, &st);
                refresh_home(&ui, &c, &st);
                sync_reminder(&*p, &st.progress);
            });
        }};
    }
    setting!(on_set_furigana, bool, |s, v| s.furigana = v);
    setting!(on_set_english, bool, |s, v| s.english = v);
    setting!(on_set_romaji, bool, |s, v| s.romaji = v);
    setting!(on_set_batch, i32, |s, v| s.batch_size = v.clamp(1, 20) as u32);
    setting!(on_set_retention, i32, |s, v| s.retention = RETENTIONS[(v as usize).min(2)]);
    setting!(on_set_start_level, i32, |s, v| s.start_level = JLPT_LEVELS[(v.max(0) as usize).min(4)].into());
    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        let p = platform.clone();
        ui.on_set_language(move |v| {
            let Some(ui) = w.upgrade() else { return };
            let mut st = st.borrow_mut();
            st.progress.settings.language = if v == 1 { "fr" } else { "en" }.into();
            st.progress.save();
            apply_language(st.progress.settings.lang());
            event(&format!("language={}", st.progress.settings.language));
            refresh_settings(&ui, &st);
            refresh_home(&ui, &c, &st);
            refresh_list(&ui, &c, &st);
            sync_reminder(&*p, &st.progress);
        });
    }
    {
        let p = platform.clone();
        setting!(on_set_notifications, bool, |s, v| {
            s.notifications = v;
            if v {
                p.request_notification_permission();
            }
        });
    }

    setting!(on_set_haptics, bool, |s, v| s.haptics = v);

    ui.on_export_progress(cb!(|ui, c, st, p| {
        st.progress.save();
        let Some(path) = st.progress.path().map(|p| p.to_string_lossy().to_string()) else { return };
        ui.set_backup_status("".into());
        st.exporting = "progress";
        p.export_progress(&path, &format!("bunpo-progress-{}.json", date_string(now_ms())));
    }));

    ui.on_export_reports(cb!(|ui, c, st, p| {
        let Some(dir) = st.progress.path().and_then(|p| p.parent()).map(|d| d.to_path_buf()) else { return };
        let file = dir.join("reports-export.json");
        if std::fs::write(&file, reports_json(&c, &st.progress)).is_err() {
            return;
        }
        ui.set_backup_status("".into());
        st.exporting = "reports";
        p.export_progress(&file.to_string_lossy(), &format!("bunpo-reports-{}.json", date_string(now_ms())));
    }));

    ui.on_lookup({
        let p = platform.clone();
        move |word| {
            event(&format!("lookup {word}"));
            p.lookup_word(&word);
        }
    });

    ui.on_open_report(cb!(|ui, c, st| {
        let Some(sess) = &st.session else { return };
        let Some((point, sentence)) = sess.current(&c) else { return };
        ui.set_report_sentence(sentence.ja.as_str().into());
        ui.set_report_reason(-1);
        ui.set_report_note("".into());
        st.report_target = Some(Report {
            point: point.id.clone(),
            sentence: sentence.id,
            answer: sess.last_answer.clone(),
            lang: st.progress.settings.language.clone(),
            ..Default::default()
        });
        ui.set_show_report(true);
        event(&format!("report-open point={} sentence={}", point.id, sentence.id));
    }));

    ui.on_save_report({
        let (w, c, st) = (ui.as_weak(), content.clone(), st.clone());
        move |reason, note| {
            let Some(ui) = w.upgrade() else { return };
            let mut st = st.borrow_mut();
            let Some(mut r) = st.report_target.take() else { return };
            let Some(reason) = REPORT_REASONS.get(reason as usize) else { return };
            r.reason = reason.to_string();
            r.note = note.trim().to_string();
            r.ts = now_ms();
            event(&format!("report point={} sentence={} reason={}", r.point, r.sentence, r.reason));
            st.progress.add_report(r);
            ui.set_show_report(false);
            refresh_quiz(&ui, &c, &st);
            refresh_settings(&ui, &st);
        }
    });

    ui.on_import_progress(cb!(|ui, c, st, p| {
        let _ = (&ui, &st);
        p.pick_import();
    }));

    ui.on_reset_point(cb!(|ui, c, st, p| {
        if let Some(id) = st.detail.clone() {
            st.progress.reset_point(&id);
            ui.set_notes(point_data(&c, &st, &id));
            refresh_list(&ui, &c, &st);
            sync_reminder(&*p, &st.progress);
        }
    }));

    ui.on_reset_all(cb!(|ui, c, st, p| {
        st.progress.reset_all();
        refresh_home(&ui, &c, &st);
        refresh_list(&ui, &c, &st);
        sync_reminder(&*p, &st.progress);
    }));

    {
        let s = st.borrow();
        apply_language(s.progress.settings.lang());
        refresh_settings(&ui, &s);
        refresh_home(&ui, &content, &s);
        refresh_list(&ui, &content, &s);
        sync_reminder(&*platform, &s.progress);
    }
    platform.dismiss_reminder();
    if st.borrow().progress.settings.notifications {
        platform.request_notification_permission();
    }

    // keep "due" counts fresh
    let timer = slint::Timer::default();
    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        timer.start(slint::TimerMode::Repeated, std::time::Duration::from_secs(60), move || {
            if let (Some(ui), Ok(st)) = (w.upgrade(), st.try_borrow()) {
                refresh_home(&ui, &c, &st);
            }
        });
    }
    {
        let p = platform.clone();
        slint::Timer::single_shot(std::time::Duration::from_millis(300), move || p.on_started());
    }
    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        let p = platform.clone();
        RESUME_HOOK.with(|h| {
            *h.borrow_mut() = Some(Box::new(move || {
                let st_rc = &st;
                let (Some(ui), Ok(st)) = (w.upgrade(), st_rc.try_borrow()) else { return };
                event("resumed");
                p.dismiss_reminder();
                drop(st);
                if let Ok(mut st) = st_rc.try_borrow_mut() {
                    if let Some(msg) = check_backup_files(&mut st) {
                        ui.set_backup_status(msg.into());
                        apply_language(st.progress.settings.lang());
                        refresh_settings(&ui, &st);
                    }
                }
                let Ok(st) = st_rc.try_borrow() else { return };
                refresh_home(&ui, &c, &st);
                refresh_list(&ui, &c, &st);
                sync_reminder(&*p, &st.progress);
            }))
        });
    }
    event("started");
    Ok(App { ui, state: st, content, _timer: timer })
}

pub fn run(progress_path: Option<PathBuf>, platform: Rc<dyn Platform>) -> Result<(), slint::PlatformError> {
    let progress = match &progress_path {
        Some(p) => Progress::load(p),
        None => Progress::in_memory(),
    };
    let app = build(progress, platform)?;
    app.ui.run()
}

#[cfg(target_os = "android")]
#[unsafe(no_mangle)]
fn android_main(app: slint::android::AndroidApp) {
    android::main(app);
}
