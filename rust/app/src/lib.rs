//! Slint front-end for the grammar SRS. All logic lives in `bunpo-core`.

use bunpo_core::content::Content;
use bunpo_core::layout::{self, ClozeMode, Metrics};
use bunpo_core::session::{find_sentence, now_ms, Session, Verdict};
use bunpo_core::store::Progress;
use slint::{ComponentHandle, ModelRc, SharedString, VecModel};
use std::cell::RefCell;
use std::path::PathBuf;
use std::rc::Rc;

slint::include_modules!();

const SCREEN_HOME: i32 = 0;
const SCREEN_LESSON: i32 = 1;
const SCREEN_QUIZ: i32 = 2;
const SCREEN_LIST: i32 = 3;
const SCREEN_DETAIL: i32 = 4;
const SCREEN_SETTINGS: i32 = 5;
const RETENTIONS: [f64; 3] = [0.85, 0.9, 0.95];
const LEVELS: [&str; 5] = ["Beginner", "Adept", "Seasoned", "Expert", "Mastered"];

struct State {
    progress: Progress,
    stack: Vec<i32>,
    lesson_ids: Vec<String>,
    lesson_idx: usize,
    session: Option<Session>,
    detail: Option<String>,
}

fn model<T: Clone + 'static>(v: Vec<T>) -> ModelRc<T> {
    ModelRc::new(VecModel::from(v))
}

fn rel_time(due: i64, now: i64) -> String {
    let d = due - now;
    if d <= 0 {
        return "now".into();
    }
    let m = d / 60_000;
    match m {
        _ if m < 60 => format!("in {} min", m + 1),
        _ if m < 60 * 24 => format!("in {} h {} min", m / 60, m % 60),
        _ => format!("in {} days", (m + 60 * 12) / (60 * 24)),
    }
}

fn sentence_key(point: &str, sid: u64) -> SharedString {
    format!("{point}:{sid}").into()
}

fn point_data(content: &Content, st: &State, id: &str) -> PointData {
    let p = content.get(id).expect("known point");
    let card = st.progress.card(id);
    let status = if card.is_new() {
        "Status: not learned yet".to_string()
    } else {
        format!(
            "Status: {} · next review {} · reviews {} · lapses {}",
            card.level_name(),
            rel_time(card.due, now_ms()),
            card.reps,
            card.lapses
        )
    };
    PointData {
        id: p.id.as_str().into(),
        title: p.title.as_str().into(),
        level: p.level.as_str().into(),
        meaning: p.meaning.as_str().into(),
        structure: p.structure.as_str().into(),
        explanation: p.explanation.replace('\n', " ").into(),
        status: status.into(),
        can_reset: !card.is_new(),
        examples: model(
            p.sentences
                .iter()
                .map(|s| Example { key: sentence_key(&p.id, s.id), en: s.en.as_str().into() })
                .collect(),
        ),
    }
}

fn due_ids(content: &Content, st: &State, now: i64) -> Vec<String> {
    let mut v: Vec<(i64, String)> = content
        .points
        .iter()
        .filter_map(|p| st.progress.cards.get(&p.id).filter(|c| c.state > 0 && c.due <= now).map(|c| (c.due, p.id.clone())))
        .collect();
    v.sort();
    v.into_iter().map(|(_, id)| id).collect()
}

fn new_ids(content: &Content, st: &State) -> Vec<String> {
    content.points.iter().filter(|p| st.progress.card(&p.id).is_new()).map(|p| p.id.clone()).collect()
}

fn refresh_home(ui: &AppWindow, content: &Content, st: &State) {
    let now = now_ms();
    let due = due_ids(content, st, now).len() as i32;
    let new = new_ids(content, st);
    let batch = st.progress.settings.batch_size as usize;
    let next_due = st.progress.cards.values().filter(|c| c.state > 0).map(|c| c.due).min();
    let mut levels = [0i32; 5];
    for c in st.progress.cards.values() {
        if let Some(i) = LEVELS.iter().position(|l| *l == c.level_name()) {
            levels[i] += 1;
        }
    }
    let next_titles: Vec<&str> =
        new.iter().take(batch).filter_map(|id| content.get(id)).map(|p| p.title.as_str()).collect();
    ui.set_home(HomeData {
        due,
        new_count: new.len() as i32,
        learned: (content.points.len() - new.len()) as i32,
        total: content.points.len() as i32,
        next_due: next_due.map(|d| rel_time(d, now)).unwrap_or_default().into(),
        next_titles: next_titles.join("  ·  ").into(),
        learn_label: format!("Learn {} new", batch.min(new.len())).into(),
        levels: model(levels.to_vec()),
        reviews_24h: st.progress.reviews_since(now - 86_400_000) as i32,
        source: content.source.as_str().into(),
    });
}

fn refresh_settings(ui: &AppWindow, st: &State) {
    let s = &st.progress.settings;
    ui.set_furigana(s.furigana);
    ui.set_english(s.english);
    ui.set_romaji(s.romaji);
    ui.set_batch_size(s.batch_size as i32);
    let ri = RETENTIONS.iter().position(|r| (r - s.retention).abs() < 1e-6).unwrap_or(1);
    ui.set_retention_index(ri as i32);
}

fn refresh_quiz(ui: &AppWindow, content: &Content, st: &State) {
    let Some(sess) = &st.session else { return };
    let mut q = QuizData {
        title: if sess.lesson { "Lesson quiz" } else { "Reviews" }.into(),
        done: sess.done as i32,
        total: sess.total as i32,
        lesson: sess.lesson,
        finished: sess.finished(),
        summary: format!("{} / {} correct on the first try.", sess.correct_first_try, sess.total).into(),
        ..Default::default()
    };
    if let Some((p, s)) = sess.current(content) {
        q.key = sentence_key(&p.id, s.id);
        q.en = s.en.as_str().into();
        q.hint = s.hint.clone().unwrap_or_else(|| p.meaning.clone()).into();
        q.verdict = match sess.verdict {
            None => 0,
            Some(Verdict::Correct) => 1,
            Some(Verdict::Wrong) => 2,
        };
        q.last_answer = sess.last_answer.as_str().into();
        q.answer = s.answers.iter().take(2).cloned().collect::<Vec<_>>().join("  /  ").into();
        q.grammar_line = format!("Grammar: {} — {}", p.title, p.meaning).into();
        q.attribution = if s.owner.is_empty() {
            format!("Tatoeba #{}", s.id)
        } else {
            format!("Tatoeba #{} by {}", s.id, s.owner)
        }
        .into();
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
    } else if cur != screen {
        st.stack.push(cur);
    }
    ui.set_show_notes(false);
    ui.set_screen(screen);
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
                .map(|g| Glyph { x: g.x, y: g.y, w: g.w, text: g.text.into(), ruby: g.ruby.into(), cloze: g.in_cloze })
                .collect(),
        ),
        cloze_x: l.cloze.x,
        cloze_y: l.cloze.y,
        cloze_w: l.cloze.w,
        cloze_h: l.cloze.h,
        height: l.height,
        ruby_h: l.ruby_h,
        main_h: l.main_h,
    }
}

/// Called once the window is up; used on Android to hide a keyboard restored from a previous session.
pub type StartupHook = Box<dyn FnOnce()>;

pub fn run(progress_path: Option<PathBuf>, on_started: Option<StartupHook>) -> Result<(), slint::PlatformError> {
    let content = Rc::new(Content::bundled());
    let progress = match &progress_path {
        Some(p) => Progress::load(p),
        None => Progress::in_memory(),
    };
    let st = Rc::new(RefCell::new(State {
        progress,
        stack: vec![],
        lesson_ids: vec![],
        lesson_idx: 0,
        session: None,
        detail: None,
    }));
    let ui = AppWindow::new()?;

    {
        let c = content.clone();
        ui.global::<Logic>().on_layout(move |key, mode, typed, furi, width, font| {
            layout_for(&c, &key, mode, &typed, furi, width, font)
        });
    }

    ui.set_grammar_list(model(
        content
            .points
            .iter()
            .map(|p| ListItem {
                id: p.id.as_str().into(),
                num: (p.order + 1).to_string().into(),
                title: p.title.as_str().into(),
                meaning: p.meaning.as_str().into(),
                level: "New".into(),
            })
            .collect(),
    ));

    // helper macro: clone handles into a callback
    macro_rules! cb {
        ($ui:ident, $c:ident, $st:ident, $body:expr) => {{
            let w = $ui.as_weak();
            let $c = content.clone();
            let $st = st.clone();
            move || {
                let $ui = w.unwrap();
                #[allow(unused_mut)]
                let mut $st = $st.borrow_mut();
                let _ = &$c;
                $body
            }
        }};
    }

    let refresh_list = {
        let content = content.clone();
        move |ui: &AppWindow, st: &State| {
            ui.set_grammar_list(model(
                content
                    .points
                    .iter()
                    .map(|p| ListItem {
                        id: p.id.as_str().into(),
                        num: (p.order + 1).to_string().into(),
                        title: p.title.as_str().into(),
                        meaning: p.meaning.as_str().into(),
                        level: st.progress.card(&p.id).level_name().into(),
                    })
                    .collect(),
            ));
        }
    };

    ui.on_start_learn(cb!(ui, c, st, {
        let ids: Vec<String> = new_ids(&c, &st).into_iter().take(st.progress.settings.batch_size as usize).collect();
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

    ui.on_lesson_prev(cb!(ui, c, st, {
        if st.lesson_idx > 0 {
            st.lesson_idx -= 1;
            ui.set_lesson_index(st.lesson_idx as i32);
            ui.set_lesson_point(point_data(&c, &st, &st.lesson_ids[st.lesson_idx].clone()));
        }
    }));

    ui.on_lesson_next(cb!(ui, c, st, {
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
            refresh_quiz(&ui, &c, &st);
            ui.set_focus_tick(ui.get_focus_tick() + 1);
        }
    }));

    ui.on_start_reviews(cb!(ui, c, st, {
        let mut ids = due_ids(&c, &st, now_ms());
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
        let c = content.clone();
        ui.on_quiz_edited(move |text| {
            let mut st = st.borrow_mut();
            let romaji = st.progress.settings.romaji;
            let Some(sess) = st.session.as_mut() else { return text };
            if sess.verdict.is_some() {
                // answer already checked: keep showing what was submitted
                return sess.raw.as_str().into();
            }
            sess.on_input(&text, romaji);
            let _ = &c;
            if let Some(ui) = w.upgrade() {
                ui.set_quiz_preview(sess.input.as_str().into());
            }
            text
        });
    }

    ui.on_quiz_submit(cb!(ui, c, st, {
        let st = &mut *st;
        let Some(sess) = st.session.as_mut() else { return };
        if sess.verdict.is_none() {
            // pick up the final text (e.g. typed with an IME, no `edited` for the last commit)
            let raw = ui.get_quiz_input();
            sess.on_input(&raw, st.progress.settings.romaji);
            sess.submit(&c);
        } else {
            sess.next(&c, &mut st.progress);
            ui.set_focus_tick(ui.get_focus_tick() + 1);
        }
        refresh_quiz(&ui, &c, st);
    }));

    ui.on_quiz_typo(cb!(ui, c, st, {
        if let Some(s) = st.session.as_mut() {
            s.override_correct();
        }
        refresh_quiz(&ui, &c, &st);
    }));

    ui.on_quiz_retry(cb!(ui, c, st, {
        if let Some(s) = st.session.as_mut() {
            s.retry();
        }
        refresh_quiz(&ui, &c, &st);
    }));

    ui.on_open_notes(cb!(ui, c, st, {
        let _ = &st;
        ui.set_show_notes(true);
    }));

    {
        let rl = refresh_list.clone();
        ui.on_go_home(cb!(ui, c, st, {
            st.session = None;
            show(&ui, &mut st, SCREEN_HOME);
            refresh_home(&ui, &c, &st);
            rl(&ui, &st);
        }));
    }

    {
        let rl = refresh_list.clone();
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        ui.on_go_back(move || {
            let ui = w.unwrap();
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
            refresh_home(&ui, &c, &st);
            rl(&ui, &st);
            if prev == SCREEN_DETAIL {
                if let Some(id) = st.detail.clone() {
                    ui.set_notes(point_data(&c, &st, &id));
                }
            }
            true
        });
    }

    {
        let rl = refresh_list.clone();
        ui.on_open_list(cb!(ui, c, st, {
            rl(&ui, &st);
            show(&ui, &mut st, SCREEN_LIST);
        }));
    }

    {
        let w = ui.as_weak();
        let st = st.clone();
        let c = content.clone();
        ui.on_open_detail(move |id| {
            let ui = w.unwrap();
            let mut st = st.borrow_mut();
            st.detail = Some(id.to_string());
            ui.set_notes(point_data(&c, &st, &id));
            show(&ui, &mut st, SCREEN_DETAIL);
        });
    }

    ui.on_open_settings(cb!(ui, c, st, {
        refresh_settings(&ui, &st);
        show(&ui, &mut st, SCREEN_SETTINGS);
    }));

    macro_rules! setting {
        ($on:ident, $ty:ty, |$s:ident, $v:ident| $apply:expr) => {{
            let w = ui.as_weak();
            let st = st.clone();
            let c = content.clone();
            ui.$on(move |$v: $ty| {
                let ui = w.unwrap();
                let mut st = st.borrow_mut();
                {
                    let $s = &mut st.progress.settings;
                    $apply;
                }
                st.progress.save();
                refresh_settings(&ui, &st);
                refresh_home(&ui, &c, &st);
            });
        }};
    }
    setting!(on_set_furigana, bool, |s, v| s.furigana = v);
    setting!(on_set_english, bool, |s, v| s.english = v);
    setting!(on_set_romaji, bool, |s, v| s.romaji = v);
    setting!(on_set_batch, i32, |s, v| s.batch_size = v.clamp(1, 20) as u32);
    setting!(on_set_retention, i32, |s, v| s.retention = RETENTIONS[(v as usize).min(2)]);

    {
        let rl = refresh_list.clone();
        ui.on_reset_point(cb!(ui, c, st, {
            if let Some(id) = st.detail.clone() {
                st.progress.reset_point(&id);
                ui.set_notes(point_data(&c, &st, &id));
                rl(&ui, &st);
            }
        }));
    }

    {
        let rl = refresh_list.clone();
        ui.on_reset_all(cb!(ui, c, st, {
            st.progress.reset_all();
            refresh_home(&ui, &c, &st);
            rl(&ui, &st);
        }));
    }

    {
        let s = st.borrow();
        refresh_settings(&ui, &s);
        refresh_home(&ui, &content, &s);
        refresh_list(&ui, &s);
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

    if let Some(hook) = on_started {
        slint::Timer::single_shot(std::time::Duration::from_millis(300), hook);
    }

    ui.run()
}

#[cfg(target_os = "android")]
#[unsafe(no_mangle)]
fn android_main(app: slint::android::AndroidApp) {
    let data = app.internal_data_path();
    let app2 = app.clone();
    slint::android::init(app).expect("slint android init");
    let path = data.map(|d| d.join("progress.json"));
    // Android may restore the keyboard if the app was killed while it was open (e.g. mid-quiz)
    let hide: StartupHook = Box::new(move || app2.hide_soft_input(false));
    run(path, Some(hide)).expect("app runs");
}

