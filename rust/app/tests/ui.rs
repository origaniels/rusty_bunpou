//! Headless UI tests: the real Slint UI and app wiring, driven through Slint's testing backend.
//! Run with `cargo test -p bunpo-app`.

use bunpo_app::*;
use bunpo_core::clock;
use bunpo_core::store::Progress;
use i_slint_backend_testing::ElementHandle;
use i_slint_core::input::TouchPhase;
use i_slint_core::lengths::LogicalPoint;
use i_slint_core::platform::{InternalEvent, WindowEvent};
use slint::{ComponentHandle, Model};
use std::cell::RefCell;
use std::rc::Rc;

const HOUR: i64 = 3_600_000;
const DAY: i64 = 24 * HOUR;

/// Records platform calls instead of talking to Android.
#[derive(Default)]
struct Recorder(RefCell<Vec<String>>);
impl Platform for Recorder {
    fn schedule_reminder(&self, at_ms: i64, count: usize, _text: &str, _channel: &str) {
        self.0.borrow_mut().push(format!("schedule {at_ms} {count}"));
    }
    fn cancel_reminder(&self) {
        self.0.borrow_mut().push("cancel".into());
    }
    fn request_notification_permission(&self) {
        self.0.borrow_mut().push("permission".into());
    }
    fn export_progress(&self, path: &str, name: &str) {
        self.0.borrow_mut().push(format!("export {path} {name}"));
    }
    fn pick_import(&self) {
        self.0.borrow_mut().push("pick-import".into());
    }
    fn lookup_word(&self, word: &str) {
        self.0.borrow_mut().push(format!("lookup {word}"));
    }
    fn haptic(&self, correct: bool) {
        self.0.borrow_mut().push(format!("haptic {correct}"));
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
        let label = self.app.ui.get_home().learn_label.to_string();
        self.press(&label);
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
        (0..l.row_count())
            .map(|i| l.row_data(i).unwrap())
            .filter(|r| r.header.is_empty())
            .map(|r| r.level.to_string())
            .collect()
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
fn romaji_preview_and_field_is_locked_after_a_right_answer() {
    let t = setup();
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    let shown = t.app.ui.invoke_quiz_edited("deshi".into());
    assert_eq!(shown, "deshi", "the field keeps the raw romaji");
    assert_eq!(t.app.ui.get_quiz_preview(), "でし", "the blank shows kana");
    let a = t.correct_answer();
    t.type_and_enter(&a);
    assert_eq!(t.app.ui.get_quiz().verdict, 1);
    // typing after a right answer is undone
    assert_eq!(t.app.ui.invoke_quiz_edited(format!("{a}x").into()), a.as_str());
    assert_eq!(t.app.ui.get_quiz().verdict, 1);
}

fn start_lesson_quiz(t: &T) {
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
}

fn last_grade(t: &T) -> u8 {
    t.app.state.borrow().progress.log.last().unwrap().grade
}

#[test]
fn editing_a_wrong_answer_is_a_typo_fix() {
    let t = setup();
    start_lesson_quiz(&t);
    let a = t.correct_answer();
    let typo = format!("{a}x");
    t.type_and_enter(&typo);
    assert_eq!(t.app.ui.get_quiz().verdict, 2);
    // delete the extra character: back to answering, as a typo fix
    assert_eq!(t.app.ui.invoke_quiz_edited(a.as_str().into()), a.as_str());
    let q = t.app.ui.get_quiz();
    assert_eq!(q.verdict, 0);
    assert!(q.fixing_typo);
    assert!(t.exists("Fixing a typo: if the answer is right now, it counts as right."));
    t.app.ui.invoke_quiz_submit();
    assert_eq!(t.app.ui.get_quiz().verdict, 1);
    t.app.ui.invoke_quiz_submit();
    assert_eq!(last_grade(&t), 3, "counted as right");
}

#[test]
fn retry_after_a_wrong_answer_still_counts_as_missed() {
    let t = setup();
    start_lesson_quiz(&t);
    let point = t.app.state.borrow().session.as_ref().unwrap().point.clone().unwrap();
    t.type_and_enter("ぜんぜんちがう");
    t.press("Retry");
    assert_eq!(t.app.ui.get_quiz().verdict, 0);
    assert_eq!(t.app.ui.get_quiz_input(), "");
    let a = t.correct_answer();
    t.type_and_enter(&a);
    assert_eq!(t.app.ui.get_quiz().verdict, 1);
    t.app.ui.invoke_quiz_submit();
    assert_eq!(last_grade(&t), 1, "missed");
    assert_eq!(t.app.ui.get_quiz().done, 0, "it comes back later");
    let st = t.app.state.borrow();
    assert!(st.session.as_ref().unwrap().point.as_deref() != Some(point.as_str()));
}

#[test]
fn text_being_composed_on_the_keyboard_shows_and_counts() {
    let t = setup();
    start_lesson_quiz(&t);
    let a = t.correct_answer();
    let split = a.char_indices().nth(1).map(|(i, _)| i).unwrap_or(a.len());
    let (done, composing) = a.split_at(split);
    // the first kana confirmed, the rest still being composed (underlined on the keyboard)
    t.app.ui.set_quiz_input(done.into());
    t.app.ui.invoke_quiz_edited(done.into());
    t.app.ui.invoke_quiz_composing(done.into(), composing.into(), done.len() as i32);
    assert_eq!(t.app.ui.get_quiz_preview(), a.as_str(), "the blank shows the composition too");
    assert_eq!(t.app.ui.get_quiz_input(), done, "the field text itself is left alone");
    t.app.ui.invoke_quiz_submit();
    assert_eq!(t.app.ui.get_quiz().verdict, 1, "checked with the composition");
}

/// Regression: Check commits the composition into the field (Android does it when the field loses
/// focus) and the answer was checked with the composition added a second time (だ → だだ).
#[test]
fn a_composition_committed_by_check_is_not_counted_twice() {
    let t = setup();
    start_lesson_quiz(&t);
    let a = t.correct_answer();
    // all of it still being composed, nothing confirmed
    t.app.ui.invoke_quiz_composing("".into(), a.as_str().into(), 0);
    assert_eq!(t.app.ui.get_quiz_preview(), a.as_str());
    // Check: the keyboard's text lands in the field, then the answer is checked before the
    // "composition is empty now" notice arrives
    t.app.ui.set_quiz_input(a.as_str().into());
    t.app.ui.invoke_quiz_edited(a.as_str().into());
    assert_eq!(t.app.ui.get_quiz_preview(), a.as_str(), "not doubled in the blank either");
    t.app.ui.invoke_quiz_submit();
    let q = t.app.ui.get_quiz();
    assert_eq!((q.verdict, q.last_answer.as_str()), (1, a.as_str()));
}

#[test]
fn composition_goes_where_the_cursor_is() {
    let at = |p: &str, i| (p.to_string(), i);
    assert_eq!(with_composition("たべ", &at("", 3)), "たべ");
    assert_eq!(with_composition("たべ", &at("ます", 6)), "たべます");
    assert_eq!(with_composition("たべ", &at("ます", 3)), "たますべ");
    assert_eq!(with_composition("たべ", &at("ます", 99)), "たべます");
    assert_eq!(with_composition("たべ", &at("ま", 4)), "たまべ", "inside a character: before it");
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
    assert!(t.exists("Learn 3 extra"), "5 learned today: the new goal of 3 is already reached");
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
    // headers are their own rows with "learned / total"; numbering restarts per level
    let rows: Vec<_> = (0..list.row_count()).map(|i| list.row_data(i).unwrap()).collect();
    assert_eq!(rows[0].num, "5 / 74", "N5 header counts learned points");
    let n4 = rows.iter().position(|r| r.header == "JLPT N4").unwrap();
    assert_eq!(rows[n4 + 1].num, "1");
}

#[test]
fn original_sentences_are_not_credited_to_tatoeba() {
    let t = setup();
    let mut originals = 0;
    for s in t.app.content.points.iter().flat_map(|p| &p.sentences) {
        let a = s.attribution(bunpo_core::i18n::Lang::En);
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

#[test]
fn start_level_choice_skips_lower_levels() {
    let t = setup();
    let total_new = t.app.ui.get_home().new_count;
    t.press("Settings");
    t.press("N2");
    assert_eq!(t.app.ui.get_start_level_index(), 3);
    assert_eq!(t.app.state.borrow().progress.settings.start_level, "N2");
    t.app.ui.invoke_go_home();
    let h = t.app.ui.get_home();
    assert_eq!(h.start_level, "N2");
    assert!(h.new_count < total_new && h.new_count == 105 + 95, "only N2 + N1 are offered: {}", h.new_count);
    // the first lesson is an N2 point, and skipped levels stay untouched
    t.press("Learn 5 new");
    let first = t.app.ui.get_lesson_point();
    assert_eq!(first.level, "N2");
    t.app.ui.invoke_go_home();
    t.learn_lesson();
    let st = t.app.state.borrow();
    assert_eq!(st.progress.cards.len(), 5);
    assert!(st.progress.cards.keys().all(|id| t.app.content.get(id).unwrap().level == "N2"));
    drop(st);
    let h = t.app.ui.get_home();
    assert_eq!(h.learned, 5);
    // switching back to N5 offers N5 again
    t.app.ui.invoke_set_start_level(0);
    t.app.ui.invoke_go_home();
    assert_eq!(t.app.ui.get_home().new_count, total_new - 5);
}

#[test]
fn nothing_left_from_chosen_level_shows_hint() {
    let mut p = Progress::in_memory();
    p.settings.start_level = "N1".into();
    let c = bunpo_core::content::Content::bundled();
    for pt in c.points.iter().filter(|x| x.level == "N1") {
        p.cards.insert(pt.id.clone(), bunpo_core::store::Card { state: 2, due: i64::MAX / 2, ..Default::default() });
    }
    let t = setup_with(p);
    let h = t.app.ui.get_home();
    assert_eq!(h.new_count, 0, "no wrap-around to lower levels");
    assert!(!t.find("Learn 0 new").accessible_enabled().unwrap());
}

#[test]
fn switching_to_french_translates_the_ui_and_is_remembered() {
    let t = setup();
    t.press("Settings");
    t.press("Français");
    assert_eq!(t.app.state.borrow().progress.settings.language, "fr");
    assert_eq!(t.app.ui.get_language_index(), 1);
    // @tr strings come from the bundled .po, Rust-built ones from the app
    // Slint strings (@tr) come from the bundled .po: the menu bar shows "Accueil"
    assert!(t.exists("Accueil") && t.exists("Réglages"), "Slint strings are translated");
    assert!(!t.exists("Home"));
    t.app.ui.invoke_go_home();
    assert!(t.exists("Réglages") && t.exists("Grammaire"));
    assert!(t.exists("Apprendre 5 nouveaux"), "Rust-built label is translated");
    // stage names in the grammar list
    t.press("Grammaire");
    let list = t.app.ui.get_grammar_list();
    use slint::Model;
    assert_eq!(list.row_data(1).unwrap().level, "Nouveau"); // row 0 is the JLPT N5 header

    // the setting survives a restart
    let progress = std::mem::replace(&mut t.app.state.borrow_mut().progress, Progress::in_memory());
    let rec = t.rec.clone();
    drop(t);
    let app = build(progress, rec.clone()).expect("rebuild ui");
    app.ui.show().unwrap();
    let t = T { app, rec };
    assert!(t.exists("Réglages"));
    t.press("Réglages");
    t.press("English");
    assert!(t.exists("Home") && !t.exists("Accueil"));
}

#[test]
fn reminder_text_and_relative_times_in_french() {
    use bunpo_core::i18n::Lang;
    assert_eq!(reminder_text(Lang::Fr, 1), "1 révision de grammaire vous attend");
    assert_eq!(reminder_text(Lang::Fr, 3), "3 révisions de grammaire vous attendent");
    assert_eq!(reminder_text(Lang::En, 3), "3 grammar reviews are waiting");
    let h = 3_600_000;
    assert_eq!(rel_time(Lang::Fr, 3 * h + 5 * 60_000, 0), "dans 3 h 5 min");
    assert_eq!(rel_time(Lang::Fr, 72 * h, 0), "dans 3 jours");
    assert_eq!(rel_time(Lang::En, 72 * h, 0), "in 3 days");
}

#[test]
fn every_ui_string_has_a_french_translation() {
    // every @tr("...") in the .slint must have a non-empty msgstr in the French catalog
    let slint = include_str!("../ui/app.slint");
    let po = include_str!("../lang/fr/LC_MESSAGES/bunpo-app.po");
    let unescape = |s: &str| s.replace("\\\"", "\"");
    let mut catalog = std::collections::HashMap::new();
    let mut id = None;
    for line in po.lines() {
        if let Some(rest) = line.strip_prefix("msgid \"") {
            id = Some(unescape(rest.trim_end_matches('"')));
        } else if let Some(rest) = line.strip_prefix("msgstr \"") {
            catalog.insert(id.take().unwrap(), unescape(rest.trim_end_matches('"')));
        }
    }
    let mut missing = vec![];
    for part in slint.split("@tr(\"").skip(1) {
        let mut end = 0;
        let b = part.as_bytes();
        while !(b[end] == b'"' && (end == 0 || b[end - 1] != b'\\')) {
            end += 1;
        }
        let msgid = unescape(&part[..end]);
        if catalog.get(&msgid).is_none_or(|s| s.is_empty()) {
            missing.push(msgid);
        }
    }
    assert!(missing.is_empty(), "no French for: {missing:?}");
}

#[test]
fn menu_bar_switches_tabs_and_back_goes_home() {
    let t = setup();
    t.press("Stats");
    assert_eq!(t.screen(), SCREEN_STATS);
    t.press("Settings");
    assert_eq!(t.screen(), SCREEN_SETTINGS);
    t.press("Grammar list");
    assert_eq!(t.screen(), SCREEN_LIST);
    // a grammar point opens on top of the list; Back returns to the list, then home
    t.press("だ");
    assert_eq!(t.screen(), SCREEN_DETAIL);
    assert!(t.app.ui.invoke_go_back());
    assert_eq!(t.screen(), SCREEN_LIST);
    assert!(t.app.ui.invoke_go_back());
    assert_eq!(t.screen(), SCREEN_HOME, "tabs don't stack up history");
    t.press("Settings");
    t.press("Home");
    assert_eq!(t.screen(), SCREEN_HOME);
}

#[test]
fn grammar_levels_fold_and_unfold() {
    use slint::Model;
    let t = setup();
    t.press("Grammar list");
    let count = |t: &T| t.app.ui.get_grammar_list().row_count();
    let all = count(&t);
    assert_eq!(all, 456 + 5, "every point plus one header per level");
    // fold N5: its points disappear, its header stays (and can still be tapped)
    t.press("JLPT N5");
    assert_eq!(count(&t), all - 74);
    assert!(t.app.ui.get_grammar_list().row_data(0).unwrap().collapsed);
    assert!(!t.exists("だ"));
    // folding survives leaving the tab
    t.press("Home");
    t.press("Grammar list");
    assert_eq!(count(&t), all - 74);
    t.press("JLPT N5");
    assert_eq!(count(&t), all);
    t.press("だ");
    assert_eq!(t.screen(), SCREEN_DETAIL);
}

// ------------------------------------------------------------------ layout (English and French)

/// Every button, text and list row must lie inside the window horizontally: a label that
/// is too long for its row pushes something off the side (as the quiz buttons once did in French).
fn assert_fits(t: &T, ctx: &str) {
    audit_ok(t, ctx, false);
}

/// The layout audit (see `bunpo_app::audit`) finds nothing wrong on screen.
fn audit_ok(t: &T, ctx: &str, strict_vertical: bool) {
    let issues = audit::audit(&t.app.ui, audit::Options { strict_vertical });
    let (w, h) = audit::window_size(&t.app.ui);
    assert!(issues.is_empty(), "{ctx} (window {w}x{h}):\n  {}", issues.join("\n  "));
}

/// Visit every screen and state of the app at the given window width and language.
fn check_every_screen(width: f32, french: bool) {
    let mut p = Progress::in_memory();
    p.settings.language = if french { "fr" } else { "en" }.into();
    let t = setup_with(p);
    // tall enough that long screens (settings, grammar points) are laid out completely: the
    // element search only sees what is inside the window, not what is scrolled away
    t.app.ui.window().set_size(slint::LogicalSize::new(width, 4000.0));
    let lang = if french { "fr" } else { "en" };
    let check = |what: &str| assert_fits(&t, &format!("[{lang}] {what}"));
    check("home");

    // a lesson: every page, then the quiz in every state
    t.app.ui.invoke_start_learn();
    let pages = t.app.ui.get_lesson_count();
    for i in 0..pages {
        check(&format!("lesson page {}", i + 1));
        t.app.ui.invoke_lesson_next();
    }
    assert_eq!(t.screen(), SCREEN_QUIZ);
    check("quiz, unanswered");
    // the longest grammar hint there is, in the bubble under the translation
    {
        let lang = if french { bunpo_core::i18n::Lang::Fr } else { bunpo_core::i18n::Lang::En };
        let c = &t.app.content;
        let longest = c
            .points
            .iter()
            .flat_map(|p| p.sentences.iter().map(move |s| s.hint(lang).unwrap_or_else(|| p.meaning_in(lang).to_string())))
            .max_by_key(|h| h.chars().count())
            .unwrap();
        let mut q = t.app.ui.get_quiz();
        q.hint = longest.as_str().into();
        t.app.ui.set_quiz(q);
        check("quiz, longest hint");
        let text = ElementHandle::find_by_accessible_label(&t.app.ui, &longest).next().expect("hint text");
        assert!(text.size().height > 25.0, "a hint this long wraps: {longest}");
    }
    t.app.ui.invoke_go_home();
    check("home with a lesson quiz to resume");
    t.app.ui.invoke_resume();
    assert_eq!(t.screen(), SCREEN_QUIZ);
    t.type_and_enter("ぜんぜんちがう");
    check("quiz, wrong answer");
    // the longest "almost" hint there is
    {
        let longest = t.app.content.points.iter().filter_map(|p| p.nuance.clone()).map(|(e, f)| if french { f } else { e }).max_by_key(|n| n.chars().count()).unwrap();
        let mut q = t.app.ui.get_quiz();
        q.verdict = 0;
        q.nudge = format!("Ça pourrait aller, mais ici on cherche {longest}.").into();
        t.app.ui.set_quiz(q);
        check("quiz, longest nuance hint");
        t.type_and_enter("ぜんぜんちがう");
    }
    t.app.ui.set_show_notes(true);
    check("quiz, grammar notes");
    t.app.ui.set_show_notes(false);
    t.app.ui.invoke_open_report();
    t.app.ui.set_report_reason(3);
    check("quiz, report dialog");
    t.app.ui.set_show_report(false);
    t.app.ui.invoke_quiz_retry();
    let a = t.correct_answer();
    t.type_and_enter(&a);
    check("quiz, correct answer");
    t.app.ui.invoke_quiz_submit();
    t.finish_quiz(&[]);
    check("quiz finished");
    t.app.ui.invoke_go_home();
    check("home after a lesson");

    // reviews (some due a few hours later)
    clock::advance(5 * HOUR);
    t.app.ui.invoke_go_home();
    check("home with reviews due");
    t.app.ui.invoke_start_reviews();
    check("reviews");
    t.app.ui.invoke_go_home();
    check("home with reviews to resume");
    t.app.ui.invoke_resume();
    t.type_and_enter("ぜんぜんちがう");
    t.app.ui.invoke_quiz_submit();
    // answer the others until the missed one comes back as practice
    while !t.app.ui.get_quiz().practising {
        let a = t.correct_answer();
        t.type_and_enter(&a);
        t.app.ui.invoke_quiz_submit();
    }
    check("reviews, practising a missed point");
    t.app.ui.invoke_go_home();

    // tabs
    t.app.ui.invoke_open_list();
    check("grammar list");
    let first = t.app.content.points[0].id.clone();
    t.app.ui.invoke_open_detail(first.into());
    check("grammar point");
    t.app.ui.set_confirm_reset(true);
    check("reset point dialog");
    t.app.ui.set_confirm_reset(false);
    t.app.ui.invoke_toggle_level("N5".into());
    t.app.ui.invoke_open_list();
    check("grammar list, N5 folded");
    t.app.ui.invoke_open_stats();
    check("stats");
    // a leech with the longest title and meaning there is
    {
        let lang = if french { bunpo_core::i18n::Lang::Fr } else { bunpo_core::i18n::Lang::En };
        let p = t.app.content.points.iter().max_by_key(|p| p.title_in(lang).chars().count() + p.meaning_in(lang).chars().count()).unwrap();
        let mut st = t.app.state.borrow_mut();
        make_leech(&mut st.progress, &p.id);
    }
    t.app.ui.invoke_go_home();
    t.app.ui.invoke_open_stats();
    check("stats with a leech");
    t.app.ui.invoke_open_settings();
    check("settings");
    t.app.ui.set_confirm_reset(true);
    check("reset all dialog");
    t.app.ui.set_confirm_reset(false);
    t.app.ui.set_confirm_import(true);
    check("import dialog");
    t.app.ui.set_confirm_import(false);
    t.app.ui.set_backup_status("Une erreur s'est produite, rien n'a été modifié.".into());
    check("settings with a backup message");
    // start level above N5: the learn card gets its extra lines
    t.app.ui.invoke_set_start_level(4);
    t.app.ui.invoke_go_home();
    check("home, lessons from N1");
}

#[test]
fn every_screen_fits_pixel_8a_english() {
    check_every_screen(411.0, false);
}

#[test]
fn every_screen_fits_pixel_8a_french() {
    check_every_screen(411.0, true);
}

#[test]
fn every_screen_fits_narrow_phone_english() {
    check_every_screen(360.0, false);
}

#[test]
fn every_screen_fits_narrow_phone_french() {
    check_every_screen(360.0, true);
}

// ------------------------------------------------------------------ export / import

fn tmp_dir(name: &str) -> std::path::PathBuf {
    let d = std::env::temp_dir().join(format!("bunpo-ui-{}-{name}", std::process::id()));
    let _ = std::fs::remove_dir_all(&d);
    std::fs::create_dir_all(&d).unwrap();
    d
}

#[test]
fn export_saves_then_hands_the_file_to_the_platform() {
    let dir = tmp_dir("export");
    let t = setup_with(Progress::load(&dir.join("progress.json")));
    t.app.ui.window().set_size(slint::LogicalSize::new(400.0, 3000.0)); // whole settings page in view
    t.app.state.borrow_mut().progress.settings.batch_size = 3; // unsaved change
    t.press("Settings");
    t.press("Export progress");
    let last = t.rec.last();
    assert!(last.starts_with("export ") && last.contains("progress.json bunpo-progress-20"), "{last}");
    assert!(last.ends_with(".json"));
    // saved first, so the exported file is up to date
    assert_eq!(Progress::load(&dir.join("progress.json")).settings.batch_size, 3);
    // the picker reports back through backup-result.txt, read when the app resumes
    std::fs::write(dir.join("backup-result.txt"), "exported").unwrap();
    on_resume();
    assert_eq!(t.app.ui.get_backup_status(), "Progress exported.");
    assert!(!dir.join("backup-result.txt").exists());
}

#[test]
fn import_asks_first_then_loads_the_picked_file() {
    let dir = tmp_dir("import");
    let t = setup_with(Progress::load(&dir.join("progress.json")));
    t.app.ui.window().set_size(slint::LogicalSize::new(400.0, 3000.0)); // whole settings page in view
    t.press("Settings");
    t.press("Import progress");
    assert!(t.app.ui.get_confirm_import(), "asks before replacing anything");
    assert_ne!(t.rec.last(), "pick-import");
    t.press("Choose a file");
    assert_eq!(t.rec.last(), "pick-import");

    // the picked file: another phone's progress, in French, with two learned points
    let mut other = Progress::in_memory();
    other.settings.language = "fr".into();
    for id in ["da", "desu"] {
        other.cards.insert(id.into(), bunpo_core::store::Card { state: 2, due: i64::MAX / 2, ..Default::default() });
    }
    std::fs::write(dir.join("progress.import.json"), serde_json::to_string(&other).unwrap()).unwrap();
    on_resume();
    assert_eq!(t.app.ui.get_backup_status(), "Progression importée\u{a0}: 2 points appris.".replace('\u{a0}', " "));
    assert_eq!(t.app.ui.get_home().learned, 2);
    assert_eq!(t.app.ui.get_language_index(), 1, "imported settings apply at once");
    assert!(t.exists("Accueil"), "UI switched to French");
    assert!(!dir.join("progress.import.json").exists());
    assert!(dir.join("progress.json.before-import").exists());
}

#[test]
fn importing_a_wrong_file_changes_nothing() {
    let dir = tmp_dir("bad-import");
    let mut p = Progress::load(&dir.join("progress.json"));
    p.settings.batch_size = 10;
    p.save();
    let t = setup_with(Progress::load(&dir.join("progress.json")));
    std::fs::write(dir.join("progress.import.json"), "my shopping list").unwrap();
    on_resume();
    assert_eq!(t.app.ui.get_backup_status(), "Import failed: this is not a progress file.");
    assert_eq!(t.app.state.borrow().progress.settings.batch_size, 10);
    assert!(!dir.join("progress.import.json").exists());
}


// ------------------------------------------------------------------ sentence reports

#[test]
fn report_a_sentence_then_export_the_reports() {
    let dir = tmp_dir("report");
    let t = setup_with(Progress::load(&dir.join("progress.json")));
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    assert!(!t.exists("Report"), "only after answering");
    t.type_and_enter("ぜんぜんちがう");
    t.press("Report");
    assert!(t.app.ui.get_show_report());
    let (point, sentence) = {
        let st = t.app.state.borrow();
        let (p, s) = st.session.as_ref().unwrap().current(&t.app.content).unwrap();
        (p.id.clone(), s.clone())
    };
    assert_eq!(t.app.ui.get_report_sentence(), sentence.ja.as_str());
    assert!(!t.find("Save report").accessible_enabled().unwrap_or(true), "a reason is needed first");
    t.press("My answer should have been accepted");
    t.app.ui.set_report_note("  maybe a valid variant  ".into());
    t.press("Save report");
    assert!(!t.app.ui.get_show_report());
    assert!(t.exists("Reported") && !t.exists("Report"), "can't report the same sentence twice");

    let r = t.app.state.borrow().progress.reports[0].clone();
    assert_eq!((r.point.as_str(), r.sentence), (point.as_str(), sentence.id));
    assert_eq!((r.reason.as_str(), r.note.as_str(), r.answer.as_str()), ("answer-rejected", "maybe a valid variant", "ぜんぜんちがう"));
    assert_eq!(Progress::load(&dir.join("progress.json")).reports.len(), 1, "saved at once");

    t.app.ui.invoke_go_home();
    t.app.ui.window().set_size(slint::LogicalSize::new(400.0, 3000.0));
    t.press("Settings");
    t.press("Export reports (1)");
    let last = t.rec.last();
    assert!(last.contains("reports-export.json bunpo-reports-20"), "{last}");
    let json: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(dir.join("reports-export.json")).unwrap()).unwrap();
    let item = &json["reports"][0];
    assert_eq!(item["japanese"], sentence.ja.as_str());
    assert_eq!(item["reason"], "answer-rejected");
    assert!(item["point_title"].as_str().unwrap().len() > 0);
    std::fs::write(dir.join("backup-result.txt"), "exported").unwrap();
    on_resume();
    assert_eq!(t.app.ui.get_backup_status(), "Reports exported.");
}

#[test]
fn no_export_reports_button_without_reports() {
    let t = setup();
    t.app.ui.window().set_size(slint::LogicalSize::new(400.0, 3000.0));
    t.press("Settings");
    assert!(t.exists("Export progress"));
    assert!(!t.exists("Export reports (0)"));
}

// ------------------------------------------------------------------ stats: streak, forecast, leeches

fn make_leech(p: &mut Progress, id: &str) {
    let now = clock::now_ms();
    p.cards.insert(id.into(), bunpo_core::store::Card { state: 1, due: now + HOUR, learned_at: now - 10 * DAY, ..Default::default() });
    for i in 0..4 {
        p.log.push(bunpo_core::store::LogEntry { point: id.into(), sentence: 1, ts: now - 9 * DAY + i * DAY, grade: if i == 2 { 3 } else { 1 }, answer: "".into() });
    }
}

#[test]
fn stats_show_streak_forecast_and_leeches() {
    let t = setup();
    t.app.ui.window().set_size(slint::LogicalSize::new(400.0, 3000.0));
    t.learn_lesson(); // today: 5 answers, 5 cards due in 4 hours
    make_leech(&mut t.app.state.borrow_mut().progress, "da");
    t.press("Stats");
    // today, plus the leech's reviews 9 to 6 days ago
    assert_eq!(t.app.ui.get_streak_line(), "Streak: 1 day · best: 4 days");
    let fc: Vec<i32> = t.app.ui.get_forecast().iter().map(|b| b.count).collect();
    assert_eq!(fc.len(), 7);
    assert_eq!(fc.iter().sum::<i32>(), 5, "the leech is due in an hour, the 4 others in 4 hours: {fc:?}");
    let cells = t.app.ui.get_activity();
    assert_eq!(cells.row_count(), ACTIVITY_WEEKS * 7);
    let today = cells.iter().filter(|c| c.level >= 0).last().unwrap();
    assert!(today.label.ends_with(": 5 reviews"), "{}", today.label);
    let leeches = t.app.ui.get_leeches();
    assert_eq!(leeches.row_count(), 1);
    assert_eq!(leeches.row_data(0).unwrap().mistakes, "3 / 5");
    t.press(&leeches.row_data(0).unwrap().title);
    assert_eq!(t.screen(), SCREEN_DETAIL);
    assert_eq!(t.app.ui.get_notes().title, leeches.row_data(0).unwrap().title);
}

#[test]
fn no_leech_section_without_leeches() {
    let t = setup();
    t.learn_lesson();
    t.press("Stats");
    assert_eq!(t.app.ui.get_leeches().row_count(), 0);
    assert!(!t.exists("Leeches"));
}

// ------------------------------------------------------------------ dictionary lookups

#[test]
fn word_chips_after_answering_open_the_dictionary() {
    let t = setup();
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    let words = {
        let st = t.app.state.borrow();
        st.session.as_ref().unwrap().current(&t.app.content).unwrap().1.words.clone()
    };
    assert!(!words.is_empty());
    assert!(!t.exists("Look up a word in Takoboto:"), "no chips before answering (they would give hints)");
    let a = t.correct_answer();
    t.type_and_enter(&a);
    assert!(t.exists("Look up a word in Takoboto:"));
    // the word may also be a text in the sentence: press the chip (a button)
    ElementHandle::find_by_accessible_label(&t.app.ui, &words[0])
        .find(|e| e.accessible_role() == Some(i_slint_core::items::AccessibleRole::Button))
        .expect("a chip for the first word")
        .invoke_accessible_default_action();
    assert_eq!(t.rec.last(), format!("lookup {}", words[0]));
}

#[test]
fn chip_rows_fit_the_width_and_keep_the_order() {
    let words: Vec<String> = ["私", "お金", "返す", "頼む", "彼", "聞こえる", "ふり", "タクシー", "ストレス"].iter().map(|s| s.to_string()).collect();
    for width in [120.0, 200.0, 330.0, 1000.0] {
        let rows = chip_rows(&words, width, 16.0);
        assert_eq!(rows.concat(), words);
        for r in &rows {
            let w: f32 = r.iter().map(|w| w.chars().count() as f32 * 16.0 + 24.0).sum::<f32>() + 8.0 * (r.len() as f32 - 1.0);
            assert!(r.len() == 1 || w <= width, "{r:?} is {w} wide, more than {width}");
        }
    }
    assert_eq!(chip_rows(&words, 1000.0, 16.0).len(), 1);
}

// ------------------------------------------------------------------ haptics

#[test]
fn checked_answers_vibrate_unless_turned_off() {
    let t = setup();
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    t.type_and_enter("ぜんぜんちがう");
    assert_eq!(t.rec.last(), "haptic false");
    t.app.ui.invoke_quiz_retry();
    let a = t.correct_answer();
    t.type_and_enter(&a);
    assert_eq!(t.rec.last(), "haptic true");
    t.app.ui.invoke_quiz_submit();

    assert!(t.app.ui.get_haptics(), "on by default");
    t.app.ui.invoke_set_haptics(false);
    assert!(!t.app.state.borrow().progress.settings.haptics);
    t.rec.clear();
    let a = t.correct_answer();
    t.type_and_enter(&a);
    assert!(!t.rec.0.borrow().iter().any(|e| e.starts_with("haptic")));
}

// ------------------------------------------------------------------ leaving reviews halfway

fn due_reviews_setup(path: &std::path::Path) -> T {
    let t = setup_with(Progress::load(path));
    for _ in 0..3 {
        t.learn_lesson();
    }
    t.wait(5 * HOUR);
    assert_eq!(t.app.ui.get_home().due, 15);
    t
}

#[test]
fn leaving_reviews_halfway_can_be_resumed_even_after_a_restart() {
    let dir = tmp_dir("resume");
    let path = dir.join("progress.json");
    let t = due_reviews_setup(&path);
    t.press("Start reviews");
    // 4 answered and moved on, the 5th answered but left on screen: it counts too
    for i in 0..5 {
        let a = t.correct_answer();
        t.type_and_enter(&a);
        if i < 4 {
            t.app.ui.invoke_quiz_submit();
        }
    }
    assert_eq!(t.app.ui.get_quiz().answered, 4);
    assert!(t.app.ui.invoke_go_back());
    assert_eq!(t.screen(), SCREEN_HOME);
    let home = t.app.ui.get_home();
    assert_eq!((home.due, home.resume_reviews), (10, 10));
    assert!(t.exists("Resume reviews (10 left)"));
    assert!(!t.exists("Start reviews"));

    // the app is closed and opened again
    drop(t);
    // (one platform per thread: rebuild the app only)
    let rec = Rc::new(Recorder::default());
    let app = build(Progress::load(&path), rec.clone()).expect("build ui");
    app.ui.window().set_size(slint::LogicalSize::new(400.0, 860.0));
    app.ui.show().unwrap();
    let t = T { app, rec };
    assert_eq!(t.app.ui.get_home().resume_reviews, 10);
    t.press("Resume reviews (10 left)");
    assert_eq!(t.screen(), SCREEN_QUIZ);
    assert_eq!((t.app.ui.get_quiz().answered, t.app.ui.get_quiz().total), (5, 15));
    t.finish_quiz(&[]);
    t.press("Home");
    let home = t.app.ui.get_home();
    assert_eq!((home.due, home.resume_reviews), (0, 0));
    assert!(t.exists("Start reviews"));
    std::fs::remove_dir_all(dir).ok();
}

#[test]
fn a_missed_review_comes_back_as_practice_and_can_be_resumed() {
    let dir = tmp_dir("practice");
    let t = due_reviews_setup(&dir.join("progress.json"));
    t.press("Start reviews");
    let first = t.app.state.borrow().session.as_ref().unwrap().point.clone().unwrap();
    t.type_and_enter("ぜんぜんちがう");
    t.app.ui.invoke_quiz_submit();
    for _ in 0..14 {
        assert!(!t.app.ui.get_quiz().practising);
        let a = t.correct_answer();
        t.type_and_enter(&a);
        t.app.ui.invoke_quiz_submit();
    }
    // every point was answered once; the missed one is practice now
    assert_eq!(t.app.state.borrow().session.as_ref().unwrap().point.clone().unwrap(), first);
    assert_eq!(t.app.ui.get_quiz().answered, 15);
    assert!(t.app.ui.get_quiz().practising);
    assert!(t.exists("Missed earlier: practice only, not graded again."));
    t.app.ui.invoke_go_home();
    let home = t.app.ui.get_home();
    assert_eq!((home.due, home.resume_reviews), (0, 1), "graded, but it can still be practised");
    t.press("Resume reviews (1 left)");
    let a = t.correct_answer();
    t.type_and_enter(&a);
    t.app.ui.invoke_quiz_submit();
    assert!(t.app.ui.get_quiz().finished);
    std::fs::remove_dir_all(dir).ok();
}

#[test]
fn a_lesson_quiz_left_halfway_can_be_resumed() {
    let t = setup();
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    let a = t.correct_answer();
    t.type_and_enter(&a);
    t.app.ui.invoke_quiz_submit();
    t.app.ui.invoke_go_home();
    assert_eq!(t.app.ui.get_home().resume_lesson, 4);
    t.press("Resume the lesson quiz (4 left)");
    assert_eq!(t.screen(), SCREEN_QUIZ);
    assert!(t.app.ui.get_quiz().lesson);
    t.finish_quiz(&[]);
    t.press("Home");
    assert_eq!(t.app.ui.get_home().learned, 5);
    assert_eq!(t.app.ui.get_home().resume_lesson, 0);
}

// ------------------------------------------------------------------ daily goal

#[test]
fn lesson_size_is_a_daily_goal_then_extra_lessons() {
    let t = setup();
    let home = t.app.ui.get_home();
    assert_eq!(home.learn_label, "Learn 5 new");
    assert_eq!(home.goal_line, "Today: 0 / 5 new points");
    // a lesson quiz left after 2 points: 3 left for today
    t.press("Learn 5 new");
    for _ in 0..4 {
        t.press("Next");
    }
    t.press("Start quiz");
    for _ in 0..2 {
        let a = t.correct_answer();
        t.type_and_enter(&a);
        t.app.ui.invoke_quiz_submit();
    }
    t.app.ui.invoke_go_home();
    t.app.state.borrow_mut().progress.paused = None; // not resumed: a new lesson
    t.app.ui.invoke_go_home();
    let home = t.app.ui.get_home();
    assert_eq!((home.learn_label.as_str(), home.goal_line.as_str()), ("Learn 3 new", "Today: 2 / 5 new points"));
    t.learn_lesson();
    let home = t.app.ui.get_home();
    assert_eq!(home.learn_label, "Learn 5 extra");
    assert!(home.goal_line.starts_with("Daily goal reached (5 / 5)"), "{}", home.goal_line);
    t.learn_lesson();
    assert_eq!(t.app.ui.get_home().learned, 10);
    assert!(t.app.ui.get_home().goal_line.starts_with("Daily goal reached (10 / 5)"));
    // the next day the goal starts again
    t.wait(24 * HOUR);
    assert_eq!(t.app.ui.get_home().learn_label, "Learn 5 new");
}

// ------------------------------------------------------------------ "almost" hints

/// Open a review of `pid` on the first of its sentences that `pick` accepts.
fn quiz_on(t: &T, pid: &str, pick: impl Fn(&bunpo_core::content::Sentence) -> bool) -> bunpo_core::content::Sentence {
    let p = t.app.content.get(pid).unwrap();
    let s = p.sentences.iter().find(|s| pick(s)).unwrap_or_else(|| panic!("no fitting sentence for {pid}")).clone();
    {
        let mut st = t.app.state.borrow_mut();
        let mut sess = bunpo_core::session::Session::new(&t.app.content, &st.progress, vec![pid.to_string()], false);
        sess.sentence = Some(s.id);
        st.progress.paused = Some(sess);
    }
    t.app.ui.invoke_resume();
    assert_eq!(t.screen(), SCREEN_QUIZ);
    s
}

#[test]
fn another_point_that_fits_gets_a_nuance_hint_once() {
    let t = setup();
    let s = quiz_on(&t, "node", |s| !s.alts.is_empty());
    t.type_and_enter(&s.alts[0]);
    let q = t.app.ui.get_quiz();
    assert_eq!(q.verdict, 0, "not graded: try again");
    assert!(q.nudge.starts_with("That could work, but here we're looking for the softer"), "{}", q.nudge);
    assert!(!q.nudge.contains("ので"), "the hint doesn't give the answer away");
    // the free retry is used: the same answer again is wrong
    t.type_and_enter(&s.alts[0]);
    assert_eq!(t.app.ui.get_quiz().verdict, 2);
}

#[test]
fn missing_particle_and_wrong_form_get_a_hint_then_count_if_right() {
    let t = setup();
    let s = quiz_on(&t, "temo_ii", |s| s.parts.iter().any(|(k, _)| k == "も"));
    let without: String = s.parts.iter().filter(|(k, _)| k != "も").map(|(k, _)| k.as_str()).collect();
    t.type_and_enter(&without);
    let q = t.app.ui.get_quiz();
    assert_eq!((q.verdict, q.nudge.as_str()), (0, "Almost! Check the particle."));
    let a = t.correct_answer();
    t.type_and_enter(&a);
    assert_eq!(t.app.ui.get_quiz().verdict, 1);
    t.app.ui.invoke_quiz_submit();
    assert_eq!(last_grade(&t), 3, "a free retry: right on the second try counts as right");

    let t2 = &t;
    // a verb long enough to recognise (み of 見る alone is too short to tell)
    let s = quiz_on(t2, "mashita", |s| s.answers.iter().any(|a| a.ends_with("ました") && a.chars().count() >= 6 && a.chars().all(bunpo_core::kana::is_kana)));
    let kana = s.answers.iter().find(|a| a.chars().all(bunpo_core::kana::is_kana)).unwrap();
    let present = format!("{}ます", kana.strip_suffix("ました").unwrap());
    t.type_and_enter(&present);
    assert_eq!(t.app.ui.get_quiz().nudge, "Almost! Right word, check the form: tense.");
}

// ------------------------------------------------------------------ layout audit and e2e hook

#[test]
fn e2e_commands_find_buttons_and_audit_the_screen() {
    let t = setup();
    let scale = t.app.ui.window().scale_factor();
    let r = audit::command(&t.app.ui, "where Learn 5 new");
    let parts: Vec<&str> = r.split(' ').collect();
    assert_eq!(&parts[..2], ["where", "on"], "{r}");
    let (x, y): (f32, f32) = (parts[2].parse().unwrap(), parts[3].parse().unwrap());
    let (w, h) = audit::window_size(&t.app.ui);
    assert!(x > 0.0 && x < w * scale && y > 0.0 && y < h * scale, "{r}");
    assert_eq!(audit::command(&t.app.ui, "where Nothing like this"), "where none \"Nothing like this\"");
    let b = audit::command(&t.app.ui, "buttons");
    for l in ["Learn 5 new", "Home", "Grammar list", "Stats", "Settings"] {
        assert!(b.contains(l), "{l} missing from {b}");
    }
    assert!(!b.contains("Start reviews"), "disabled buttons are not listed: {b}");
    assert_eq!(audit::command(&t.app.ui, "audit home"), "audit home ok");
    assert_eq!(audit::command(&t.app.ui, "audit home strict"), "audit home ok");
}

#[test]
fn the_audit_catches_what_doesnt_fit() {
    let t = setup();
    // far too narrow: things stick out and texts don't fit
    t.app.ui.window().set_size(slint::LogicalSize::new(150.0, 860.0));
    let r = audit::command(&t.app.ui, "audit narrow");
    assert!(r.starts_with("audit narrow FAIL") && r.contains("off-screen"), "{r}");
    // the hint bubble of a quiz, open over the screen: only the dialog is checked
    t.app.ui.window().set_size(slint::LogicalSize::new(400.0, 860.0));
    start_lesson_quiz(&t);
    t.app.ui.set_show_notes(true);
    let els = audit::elements(&t.app.ui);
    assert!(els.iter().any(|e| e.label == "Close"));
    assert!(!els.iter().any(|e| e.label == "Check"), "the quiz under the dialog is not checked");
}

#[test]
fn the_e2e_hook_runs_only_with_its_marker() {
    let t = setup();
    let dir = tmp_dir("e2e-hook");
    assert!(start_e2e_hook(&t.app.ui, dir.clone()).is_none(), "off without the marker");
    std::fs::write(dir.join("e2e.on"), "").unwrap();
    let hook = start_e2e_hook(&t.app.ui, dir.clone());
    assert!(hook.is_some());
    std::fs::write(dir.join("e2e.cmd"), "where Stats\naudit home\n").unwrap();
    i_slint_backend_testing::mock_elapsed_time(std::time::Duration::from_millis(300));
    assert!(!dir.join("e2e.cmd").exists(), "the command was read");
    drop(hook);
    std::fs::remove_dir_all(dir).ok();
}

// ------------------------------------------------------------------ every button, pressed

/// A progress like the emulator tests use: points learned, reviews due, a leech, a report.
fn crawl_progress(french: bool) -> Progress {
    let t = setup();
    t.learn_lesson();
    let mut p = std::mem::replace(&mut t.app.state.borrow_mut().progress, Progress::in_memory());
    drop(t);
    for c in p.cards.values_mut() {
        c.due = clock::now_ms() - 1000;
    }
    let leech = p.cards.keys().next().unwrap().clone();
    make_leech(&mut p, &leech);
    p.reports.push(bunpo_core::store::Report { point: leech, reason: "translation".into(), ..Default::default() });
    p.settings.language = if french { "fr" } else { "en" }.into();
    p.paused = None;
    p
}

/// Something observable about the app: what is on screen, platform calls, saved progress.
fn fingerprint(t: &T) -> String {
    let st = t.app.state.borrow();
    format!(
        "{} | {} calls | {} cards {} reports {:?}",
        audit::command(&t.app.ui, "digest"),
        t.rec.0.borrow().len(),
        st.progress.cards.len(),
        st.progress.reports.len(),
        serde_json::to_string(&st.progress.settings).unwrap_or_default()
    )
}

/// The control with this label and role; inside the open dialog if there is one (the screen
/// behind it may have a button with the same label).
fn find_control(t: &T, label: &str, role: i_slint_core::items::AccessibleRole) -> Option<ElementHandle> {
    use i_slint_backend_testing::ElementQuery;
    let all = ElementQuery::from_root(&t.app.ui).find_all();
    let dialog = all
        .iter()
        .filter(|e| e.accessible_role() == Some(i_slint_core::items::AccessibleRole::Groupbox) && e.accessible_label().is_some_and(|l| l == "dialog"))
        .last()
        .cloned();
    let scope = match dialog {
        Some(d) => d.query_descendants().find_all(),
        None => all,
    };
    scope.into_iter().find(|e| e.accessible_role() == Some(role) && e.accessible_label().is_some_and(|l| l.trim() == label))
}

/// Press every enabled button and switch of every state, each on a fresh app in that state:
/// nothing panics, something changes, and the screen it leads to passes the layout audit.
fn press_every_control(french: bool) {
    let progress = crawl_progress(french);
    let json = serde_json::to_string(&progress).unwrap();
    type Goto = Box<dyn Fn(&T)>;
    let wrong = |t: &T| {
        t.app.ui.invoke_start_reviews();
        t.type_and_enter("ぜんぜんちがう");
    };
    let states: Vec<(&str, Goto)> = vec![
        ("home", Box::new(|_| {})),
        ("settings", Box::new(|t| t.app.ui.invoke_open_settings())),
        ("grammar list", Box::new(|t| t.app.ui.invoke_open_list())),
        ("grammar point", Box::new(|t| t.app.ui.invoke_open_detail(t.app.content.points[0].id.clone().into()))),
        ("stats", Box::new(|t| t.app.ui.invoke_open_stats())),
        ("lesson", Box::new(|t| t.app.ui.invoke_start_learn())),
        ("reviews", Box::new(|t| t.app.ui.invoke_start_reviews())),
        ("reviews, wrong answer", Box::new(wrong)),
        ("reviews, right answer", Box::new(move |t| {
            wrong(t);
            t.app.ui.invoke_quiz_typo();
        })),
        ("grammar notes", Box::new(move |t| {
            wrong(t);
            t.app.ui.set_show_notes(true);
        })),
        ("report dialog", Box::new(move |t| {
            wrong(t);
            t.app.ui.invoke_open_report();
        })),
        ("reset point dialog", Box::new(|t| {
            let id = t.app.state.borrow().progress.cards.keys().next().unwrap().clone();
            t.app.ui.invoke_open_detail(id.into());
            t.app.ui.set_confirm_reset(true);
        })),
        ("reset all dialog", Box::new(|t| {
            t.app.ui.invoke_open_settings();
            t.app.ui.set_confirm_reset(true);
        })),
    ];
    // a real file: export needs one
    let dir = tmp_dir(if french { "crawl-fr" } else { "crawl-en" });
    let path = dir.join("progress.json");
    let fresh = |goto: &Goto| -> T {
        std::fs::write(&path, &json).unwrap();
        fastrand::seed(7); // the same review order and sentences every time
        let rec = Rc::new(Recorder::default());
        let app = build(Progress::load(&path), rec.clone()).expect("build ui");
        app.ui.window().set_size(slint::LogicalSize::new(400.0, 4000.0));
        app.ui.show().unwrap();
        let t = T { app, rec };
        goto(&t);
        t
    };
    let mut pressed = 0;
    for (name, goto) in &states {
        let t = fresh(goto);
        audit_ok(&t, &format!("{name}"), false);
        let controls: Vec<audit::El> =
            audit::elements(&t.app.ui).into_iter().filter(|e| audit::is_control(e.role) && e.enabled).collect();
        assert!(!controls.is_empty(), "{name}: no buttons?");
        drop(t);
        for c in controls {
            let t = fresh(goto);
            let before = fingerprint(&t);
            let e = find_control(&t, &c.label, c.role).unwrap_or_else(|| panic!("{name}: '{}' is gone", c.label));
            e.invoke_accessible_default_action();
            let after = fingerprint(&t);
            assert!(after != before || c.checked, "{name}: '{}' did nothing", c.label);
            audit_ok(&t, &format!("{name}, after '{}'", c.label), false);
            pressed += 1;
        }
    }
    assert!(pressed > 60, "only {pressed} controls pressed");
    std::fs::remove_dir_all(dir).ok();
}

#[test]
fn every_control_on_every_screen_does_something_english() {
    press_every_control(false);
}

#[test]
fn every_control_on_every_screen_does_something_french() {
    press_every_control(true);
}

/// Sentences with Latin letters or digits: each character has its own box, sized from an estimate
/// of its width; the glyph must fit it (else it runs into its neighbour).
#[test]
fn latin_letters_and_digits_fit_their_boxes() {
    let t = setup();
    let mut n = 0;
    let points: Vec<(String, Vec<u64>)> = t
        .app
        .content
        .points
        .iter()
        .map(|p| (p.id.clone(), p.sentences.iter().filter(|s| s.ja.chars().any(|c| c.is_ascii_alphanumeric())).map(|s| s.id).collect()))
        .collect();
    for (pid, ids) in points {
        for sid in ids {
            quiz_on(&t, &pid, |s| s.id == sid);
            let a = t.correct_answer();
            t.type_and_enter(&a); // revealed: the whole sentence is drawn
            assert_fits(&t, &format!("{pid} sentence {sid}"));
            n += 1;
        }
    }
    assert!(n > 20, "only {n} sentences with Latin letters or digits");
}
