//! Slint front-end for the grammar SRS. All logic lives in `bunpo-core`; this file wires it
//! to the UI. Platform specifics (reminders, keyboard) go through [`Platform`] so the whole
//! UI can be driven headlessly in tests (see `tests/ui.rs`).

use bunpo_core::content::Content;
use bunpo_core::i18n::{tr, Lang};
use bunpo_core::layout::{self, ClozeMode, Metrics};
use bunpo_core::lessons::{lesson_queue, LEVELS as JLPT_LEVELS};
use bunpo_core::reminder::next_reminder;
use bunpo_core::session::{find_sentence, now_ms, Session, Verdict};
use bunpo_core::store::Progress;
use slint::{ComponentHandle, ModelRc, SharedString, VecModel};
use std::cell::RefCell;
use std::path::PathBuf;
use std::rc::Rc;

#[cfg(target_os = "android")]
mod android;

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

pub struct State {
    pub progress: Progress,
    stack: Vec<i32>,
    lesson_ids: Vec<String>,
    lesson_idx: usize,
    pub session: Option<Session>,
    detail: Option<String>,
    /// JLPT levels folded in the grammar list (for this run of the app)
    collapsed: std::collections::HashSet<String>,
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

fn new_ids(content: &Content, progress: &Progress) -> Vec<String> {
    content.points.iter().filter(|p| progress.card(&p.id).is_new()).map(|p| p.id.clone()).collect()
}

fn refresh_home(ui: &AppWindow, content: &Content, st: &State) {
    let now = now_ms();
    let due = due_ids(content, &st.progress, now).len() as i32;
    let new = new_ids(content, &st.progress);
    let queue = lesson_queue(content, &st.progress);
    let batch = st.progress.settings.batch_size as usize;
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
        learn_label: match lang {
            Lang::En => format!("Learn {} new", batch.min(queue.len())),
            Lang::Fr => format!("Apprendre {} nouveaux", batch.min(queue.len())),
        }
        .into(),
        levels: model(levels.to_vec()),
        reviews_24h: st.progress.reviews_since(now - 86_400_000) as i32,
        source: content.source_in(lang).into(),
        level_rows: model(level_rows(content, &st.progress)),
    });
    ui.set_level_pies(model(level_pies(content, &st.progress)));
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
    ui.set_batch_size(s.batch_size as i32);
    let li = JLPT_LEVELS.iter().position(|l| *l == s.start_level).unwrap_or(0);
    ui.set_start_level_index(li as i32);
    let ri = RETENTIONS.iter().position(|r| (r - s.retention).abs() < 1e-6).unwrap_or(1);
    ui.set_retention_index(ri as i32);
    ui.set_language_index(if s.lang() == Lang::Fr { 1 } else { 0 });
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
        detail: None,
        collapsed: Default::default(),
    }));
    let ui = AppWindow::new()?;
    ui.set_stage_colors(model((0..6).map(stage_color).collect()));

    {
        let c = content.clone();
        ui.global::<Logic>().on_layout(move |key, mode, typed, furi, width, font| {
            layout_for(&c, &key, mode, &typed, furi, width, font)
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
        let ids: Vec<String> =
            lesson_queue(&c, &st.progress).into_iter().take(st.progress.settings.batch_size as usize).collect();
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
        show(&ui, &mut st, SCREEN_QUIZ);
        refresh_quiz(&ui, &c, &st);
        ui.set_focus_tick(ui.get_focus_tick() + 1);
    }));

    {
        let w = ui.as_weak();
        let st = st.clone();
        ui.on_quiz_edited(move |text| {
            let mut st = st.borrow_mut();
            let romaji = st.progress.settings.romaji;
            let Some(sess) = st.session.as_mut() else { return text };
            if sess.verdict.is_some() {
                // answer already checked: keep showing what was submitted
                return sess.raw.as_str().into();
            }
            sess.on_input(&text, romaji);
            if let Some(ui) = w.upgrade() {
                ui.set_quiz_preview(sess.input.as_str().into());
            }
            text
        });
    }

    ui.on_quiz_submit(cb!(|ui, c, st, p| {
        let st = &mut *st;
        let Some(sess) = st.session.as_mut() else { return };
        if sess.verdict.is_none() {
            // pick up the final text (e.g. typed with an IME, no `edited` for the last commit)
            let raw = ui.get_quiz_input();
            sess.on_input(&raw, st.progress.settings.romaji);
            if sess.submit(&c) {
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
            sync_reminder(&*p, &st.progress);
            if sess.finished() {
                event(&format!("session-finished correct_first_try={} total={}", sess.correct_first_try, sess.total));
            }
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

    ui.on_go_home(cb!(|ui, c, st| {
        st.session = None;
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
                st.session = None;
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
                let (Some(ui), Ok(st)) = (w.upgrade(), st.try_borrow()) else { return };
                event("resumed");
                p.dismiss_reminder();
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
