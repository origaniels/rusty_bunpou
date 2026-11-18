//! Headless UI tests: the real Slint UI and app wiring, driven through Slint's testing backend.
//! Run with `cargo test -p bunpo-app`.

use bunpo_app::*;
use bunpo_core::clock;
use bunpo_core::store::Progress;
use i_slint_backend_testing::ElementHandle;
use i_slint_core::input::TouchPhase;
use i_slint_core::lengths::LogicalPoint;
use i_slint_core::platform::{InternalEvent, WindowEvent};
use slint::ComponentHandle;
use std::cell::RefCell;
use std::rc::Rc;

const HOUR: i64 = 3_600_000;
const DAY: i64 = 24 * HOUR;

/// Records platform calls instead of talking to Android.
#[derive(Default)]
struct Recorder(RefCell<Vec<String>>);
impl Platform for Recorder {
    fn schedule_reminder(&self, at_ms: i64, count: usize) {
        self.0.borrow_mut().push(format!("schedule {at_ms} {count}"));
    }
    fn cancel_reminder(&self) {
        self.0.borrow_mut().push("cancel".into());
    }
    fn request_notification_permission(&self) {
        self.0.borrow_mut().push("permission".into());
    }
}
impl Recorder {
    fn last(&self) -> String {
        self.0.borrow().last().cloned().unwrap_or_default()
    }
    fn clear(&self) {
        self.0.borrow_mut().clear();
    }
}

struct T {
    app: App,
    rec: Rc<Recorder>,
}

fn setup() -> T {
    setup_with(Progress::in_memory())
}

fn setup_with(progress: Progress) -> T {
    i_slint_backend_testing::init_no_event_loop();
    clock::reset();
    let rec = Rc::new(Recorder::default());
    let app = build(progress, rec.clone()).expect("build ui");
    app.ui.window().set_size(slint::LogicalSize::new(400.0, 860.0));
    app.ui.show().unwrap();
    T { app, rec }
}

impl T {
    fn screen(&self) -> i32 {
        self.app.ui.get_screen()
    }

    fn find(&self, label: &str) -> ElementHandle {
        ElementHandle::find_by_accessible_label(&self.app.ui, label)
            .next()
            .unwrap_or_else(|| panic!("no element labelled {label:?} on screen {}", self.screen()))
    }

    fn exists(&self, label: &str) -> bool {
        ElementHandle::find_by_accessible_label(&self.app.ui, label).next().is_some()
    }

    fn press(&self, label: &str) {
        self.find(label).invoke_accessible_default_action();
    }

    /// Type like the keyboard would (field edit + `edited` callback), then press Enter.
    fn type_and_enter(&self, text: &str) {
        self.app.ui.set_quiz_input(text.into());
        let shown = self.app.ui.invoke_quiz_edited(text.into());
        self.app.ui.set_quiz_input(shown);
        self.app.ui.invoke_quiz_submit();
    }

    fn correct_answer(&self) -> String {
        let st = self.app.state.borrow();
        st.session.as_ref().unwrap().current(&self.app.content).unwrap().1.answer()
    }

    /// Answer every remaining quiz item (correctly, or wrong-then-typo for `wrong_ids`).
    fn finish_quiz(&self, wrong_ids: &[&str]) {
        let mut failed: Vec<String> = vec![];
        for _ in 0..50 {
            if self.app.ui.get_quiz().finished {
                return;
            }
            let pid = self.app.state.borrow().session.as_ref().unwrap().point.clone().unwrap();
            if wrong_ids.contains(&pid.as_str()) && !failed.contains(&pid) {
                failed.push(pid);
                self.type_and_enter("ぜんぜんちがう");
                assert_eq!(self.app.ui.get_quiz().verdict, 2);
            } else {
                let a = self.correct_answer();
                self.type_and_enter(&a);
                assert_eq!(self.app.ui.get_quiz().verdict, 1, "answer {a} rejected");
            }
            self.app.ui.invoke_quiz_submit(); // Enter again = next
        }
        panic!("quiz did not finish");
    }

    fn learn_lesson(&self) {
        self.press(&format!("Learn {} new", self.app.state.borrow().progress.settings.batch_size));
        assert_eq!(self.screen(), SCREEN_LESSON);
        for _ in 0..10 {
            if self.exists("Start quiz") {
                break;
            }
            self.press("Next");
        }
        self.press("Start quiz");
        assert_eq!(self.screen(), SCREEN_QUIZ);
        self.finish_quiz(&[]);
        self.press("Home");
        assert_eq!(self.screen(), SCREEN_HOME);
    }

    /// Move time forward and come back to the home screen (refreshes counts).
    fn wait(&self, ms: i64) {
        clock::advance(ms);
        self.app.ui.invoke_go_home();
    }

    fn levels(&self) -> Vec<String> {
        use slint::Model;
        let l = self.app.ui.get_grammar_list();
        (0..l.row_count()).map(|i| l.row_data(i).unwrap().level.to_string()).collect()
    }

    fn touch(&self, pos: LogicalPoint, phase: TouchPhase) {
        self.app.ui.window().dispatch_event(WindowEvent::internal(InternalEvent::Touch {
            id: 0,
            position: pos,
            phase,
            event_time: None,
            history: Default::default(),
        }));
    }
}

#[test]
fn home_screen_initial_state() {
    let t = setup();
    let h = t.app.ui.get_home();
    assert_eq!((h.due, h.learned), (0, 0));
    assert_eq!(h.new_count, h.total);
    assert!(h.total >= 70);
    assert!(!t.find("Start reviews").accessible_enabled().unwrap());
    assert!(t.find("Learn 5 new").accessible_enabled().unwrap());
}

#[test]
fn full_lesson_then_home_counts() {
    let t = setup();
    t.learn_lesson();
    let h = t.app.ui.get_home();
    assert_eq!(h.learned, 5);
    assert_eq!(h.due, 0);
    assert_eq!(h.reviews_24h, 5);
    assert!(h.next_due.contains("h"), "next review in hours: {}", h.next_due);
    assert_eq!(t.app.state.borrow().progress.cards.len(), 5);
    assert!(t.rec.last().starts_with("schedule"), "reminder armed: {:?}", t.rec.0.borrow());
}

#[test]
fn lesson_navigation_previous_next() {
    let t = setup();
    t.press("Learn 5 new");
    assert!(!t.find("Previous").accessible_enabled().unwrap());
    let first = t.app.ui.get_lesson_point().id;
    t.press("Next");
    assert_ne!(t.app.ui.get_lesson_point().id, first);
    t.press("Previous");
    assert_eq!(t.app.ui.get_lesson_point().id, first);
}

#[test]
fn wrong_answer_typo_and_retry() {
    let t = setup();
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    t.type_and_enter("ぜんぜんちがう");
    assert_eq!(t.app.ui.get_quiz().verdict, 2);
    assert!(t.exists("Typo") && t.exists("Retry"));
    t.press("Retry");
    assert_eq!(t.app.ui.get_quiz().verdict, 0);
    assert_eq!(t.app.ui.get_quiz_input(), "");
    t.type_and_enter("ぜんぜんちがう");
    t.press("Typo");
    assert_eq!(t.app.ui.get_quiz().verdict, 1);
}

#[test]
fn romaji_preview_and_field_is_locked_after_checking() {
    let t = setup();
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    let shown = t.app.ui.invoke_quiz_edited("deshi".into());
    assert_eq!(shown, "deshi", "the field keeps the raw romaji");
    assert_eq!(t.app.ui.get_quiz_preview(), "でし", "the blank shows kana");
    t.type_and_enter("zz");
    // typing after the verdict is undone
    assert_eq!(t.app.ui.invoke_quiz_edited("zzx".into()), "zz");
}

#[test]
fn back_navigation_stack() {
    let t = setup();
    t.press("Grammar list");
    assert_eq!(t.screen(), SCREEN_LIST);
    t.press("だ");
    assert_eq!(t.screen(), SCREEN_DETAIL);
    assert_eq!(t.app.ui.get_notes().id, "da");
    assert!(t.app.ui.invoke_go_back());
    assert_eq!(t.screen(), SCREEN_LIST);
    assert!(t.app.ui.invoke_go_back());
    assert_eq!(t.screen(), SCREEN_HOME);
    assert!(!t.app.ui.invoke_go_back(), "back on home leaves the app");
}

#[test]
fn back_from_quiz_goes_home_and_keeps_graded_items() {
    let t = setup();
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    let a = t.correct_answer();
    t.type_and_enter(&a);
    t.app.ui.invoke_quiz_submit();
    assert!(t.app.ui.invoke_go_back());
    assert_eq!(t.screen(), SCREEN_HOME);
    assert_eq!(t.app.ui.get_home().learned, 1, "the answered point is learned, the rest stay new");
}

/// Regression test for the Android back gesture: the system cancels the touch it steals,
/// and that must not count as a tap on the list item underneath.
#[test]
fn cancelled_touch_does_not_open_grammar_point() {
    let t = setup();
    t.press("Grammar list");
    let row = t.find("だ");
    let p = row.absolute_position();
    let s = row.size();
    let center = LogicalPoint::new(p.x + s.width / 2.0, p.y + s.height / 2.0);

    t.touch(center, TouchPhase::Started);
    t.touch(center, TouchPhase::Cancelled);
    assert_eq!(t.screen(), SCREEN_LIST, "a cancelled touch must not open the item");

    // control: a real tap still works
    t.touch(center, TouchPhase::Started);
    t.touch(center, TouchPhase::Ended);
    assert_eq!(t.screen(), SCREEN_DETAIL);
}

#[test]
fn settings_toggles_persist_and_control_reminders() {
    let dir = std::env::temp_dir().join(format!("bunpo-ui-{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    let path = dir.join("progress.json");
    let _ = std::fs::remove_file(&path);
    let t = setup_with(Progress::load(&path));
    t.learn_lesson();
    t.press("Settings");
    assert_eq!(t.screen(), SCREEN_SETTINGS);
    t.rec.clear();
    t.app.ui.invoke_set_notifications(false);
    assert_eq!(t.rec.last(), "cancel");
    t.app.ui.invoke_set_notifications(true);
    let calls = t.rec.0.borrow().clone();
    assert!(calls.contains(&"permission".to_string()) && calls.last().unwrap().starts_with("schedule"), "{calls:?}");
    t.app.ui.invoke_set_furigana(false);
    t.app.ui.invoke_set_batch(3);
    t.app.ui.invoke_set_retention(2);
    assert!(!t.app.ui.get_furigana());
    assert_eq!(t.app.ui.get_retention_index(), 2);
    let saved = Progress::load(&path);
    assert!(!saved.settings.furigana);
    assert_eq!(saved.settings.batch_size, 3);
    assert_eq!(saved.settings.retention, 0.95);
    assert_eq!(saved.cards.len(), 5);
    t.app.ui.invoke_go_home();
    assert!(t.exists("Learn 3 new"));
}

#[test]
fn reset_point_and_reset_all() {
    let t = setup();
    t.learn_lesson();
    t.press("Grammar list");
    t.press("だ");
    assert!(t.app.ui.get_notes().can_reset);
    t.app.ui.invoke_reset_point();
    assert!(!t.app.ui.get_notes().can_reset);
    t.app.ui.invoke_go_home();
    assert_eq!(t.app.ui.get_home().learned, 4);
    t.rec.clear();
    t.app.ui.invoke_reset_all();
    assert_eq!(t.app.ui.get_home().learned, 0);
    assert_eq!(t.rec.last(), "cancel", "nothing left to remind about");
}

/// The whole SRS cycle through the UI, travelling in time between sessions:
/// learning steps 4h → 8h → 1d → 3d, then FSRS intervals; a mistake drops the point back.
#[test]
fn srs_over_weeks_through_the_ui() {
    let t = setup();
    t.learn_lesson();
    for (step, wait) in [4 * HOUR, 8 * HOUR, DAY, 3 * DAY].into_iter().enumerate() {
        t.wait(wait - 60_000);
        assert_eq!(t.app.ui.get_home().due, 0, "step {step}: not due a minute early");
        t.wait(120_000);
        assert_eq!(t.app.ui.get_home().due, 5, "step {step}: all due");
        t.press("Start reviews");
        t.finish_quiz(&[]);
        t.press("Home");
    }
    // graduated: next interval is FSRS-based, more than 3 days but capped at 3x
    let card = t.app.state.borrow().progress.card("da");
    assert_eq!(card.state, 2);
    let iv = card.interval_days();
    assert!(iv > 3.0 && iv <= 9.5, "first FSRS interval {iv}");
    t.app.ui.invoke_open_list();
    assert!(t.levels().iter().take(5).all(|l| l == "Seasoned" || l == "Adept"), "{:?}", &t.levels()[..5]);

    // next review: get one point wrong
    t.wait(10 * DAY);
    assert_eq!(t.app.ui.get_home().due, 5);
    t.press("Start reviews");
    t.finish_quiz(&["da"]);
    t.press("Home");
    let st = t.app.state.borrow();
    let da = st.progress.card("da");
    assert_eq!((da.state, da.lapses), (1, 1));
    assert_eq!(da.level_name(), "Beginner");
    let other = st.progress.card("desu");
    assert!(other.interval_days() > 9.0, "the others keep growing: {}", other.interval_days());
    drop(st);
    // an hour later only the missed point is due
    t.wait(HOUR + 60_000);
    assert_eq!(t.app.ui.get_home().due, 1);
    clock::reset();
}

#[test]
fn every_screen_renders_without_panicking() {
    let t = setup();
    t.learn_lesson();
    for f in [AppWindow::invoke_open_list, AppWindow::invoke_open_settings, AppWindow::invoke_go_home] {
        f(&t.app.ui);
        t.app.ui.window().request_redraw();
    }
    t.app.ui.invoke_open_detail("te_kudasai".into());
    t.app.ui.set_show_notes(true);
    t.app.ui.set_confirm_reset(true);
    assert!(t.exists("Reset"));
    t.app.ui.set_confirm_reset(false);
}

#[test]
fn resume_refreshes_due_counts() {
    let t = setup();
    t.learn_lesson();
    assert_eq!(t.app.ui.get_home().due, 0);
    clock::advance(5 * HOUR);
    t.rec.clear();
    on_resume();
    assert_eq!(t.app.ui.get_home().due, 5, "counts refresh when the app comes back");
    assert!(t.rec.last().starts_with("schedule"), "reminder re-armed: {:?}", t.rec.0.borrow());
    clock::reset();
}

#[test]
fn progress_per_level_and_list_headers() {
    use slint::Model;
    let t = setup();
    let rows = t.app.ui.get_home().level_rows;
    let names: Vec<String> = (0..rows.row_count()).map(|i| rows.row_data(i).unwrap().name.to_string()).collect();
    assert_eq!(names, ["N5", "N4", "N3", "N2", "N1"]);
    let total: i32 = (0..rows.row_count()).map(|i| rows.row_data(i).unwrap().total).sum();
    assert_eq!(total, t.app.ui.get_home().total);
    t.learn_lesson();
    let n5 = t.app.ui.get_home().level_rows.row_data(0).unwrap();
    assert_eq!(n5.learned, 5);

    let list = t.app.ui.get_grammar_list();
    let headers: Vec<String> = (0..list.row_count())
        .map(|i| list.row_data(i).unwrap().header.to_string())
        .filter(|h| !h.is_empty())
        .collect();
    assert_eq!(headers, ["JLPT N5", "JLPT N4", "JLPT N3", "JLPT N2", "JLPT N1"]);
    // numbering restarts per level
    let first_n4 = (0..list.row_count()).map(|i| list.row_data(i).unwrap()).find(|r| r.header == "JLPT N4").unwrap();
    assert_eq!(first_n4.num, "1");
}

#[test]
fn original_sentences_are_not_credited_to_tatoeba() {
    let t = setup();
    let mut originals = 0;
    for s in t.app.content.points.iter().flat_map(|p| &p.sentences) {
        let a = s.attribution();
        if s.src == "app" {
            originals += 1;
            assert_eq!(a, "Example written for this app");
        } else {
            assert!(a.starts_with("Tatoeba #"), "{a}");
            assert!(s.id < 900_000_000, "Tatoeba ids are real ids: {}", s.id);
        }
    }
    assert!(originals > 100, "{originals}");
}

#[test]
fn stats_screen_pies_and_per_level_counts() {
    use slint::Model;
    let t = setup();
    t.learn_lesson();
    t.press("Stats");
    assert_eq!(t.screen(), SCREEN_STATS);
    let pies = t.app.ui.get_level_pies();
    assert_eq!(pies.row_count(), 5);
    let n5 = pies.row_data(0).unwrap();
    let counts: Vec<i32> = (0..6).map(|i| n5.counts.row_data(i).unwrap()).collect();
    assert_eq!(counts.iter().sum::<i32>(), n5.total, "every point is in exactly one stage");
    assert_eq!(counts[0], n5.total - 5, "the rest of N5 is still New");
    assert_eq!(counts[1], 5, "the five learned points are Beginners");
    assert_eq!(n5.learned, 5);
    assert_eq!(n5.slices.row_count(), 2, "two non-empty stages → two slices");
    let n4 = pies.row_data(1).unwrap();
    assert_eq!(n4.slices.row_count(), 1, "all New → one full grey circle");
    assert_eq!(t.app.ui.get_stage_colors().row_count(), 6);
    assert!(t.app.ui.invoke_go_back());
    assert_eq!(t.screen(), SCREEN_HOME);
}
