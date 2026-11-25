//! Quiz session flows (lessons and reviews) against the real content.

use bunpo_core::clock;
use bunpo_core::content::Content;
use bunpo_core::session::{Session, Verdict, LESSON_EXAMPLES};
use bunpo_core::store::Progress;

fn first_ids(c: &Content, n: usize) -> Vec<String> {
    c.points.iter().take(n).map(|p| p.id.clone()).collect()
}

fn answer_current(s: &mut Session, c: &Content, correct: bool) {
    let ans = if correct { s.current(c).unwrap().1.answer() } else { "ぜったいちがう".into() };
    s.on_input(&ans, true);
    assert!(s.submit(c));
}

#[test]
fn lesson_quiz_never_uses_lesson_examples() {
    let c = Content::bundled();
    let prog = Progress::in_memory();
    for _ in 0..30 {
        let s = Session::new(&c, &prog, first_ids(&c, 5), true);
        let (p, sent) = s.current(&c).unwrap();
        assert!(!p.sentences.iter().take(LESSON_EXAMPLES).any(|x| x.id == sent.id));
    }
}

#[test]
fn wrong_answers_come_back_with_the_same_sentence_and_grade_once() {
    let c = Content::bundled();
    let mut prog = Progress::in_memory();
    let mut s = Session::new(&c, &prog, first_ids(&c, 2), false);
    let (p0, s0) = s.current(&c).map(|(p, s)| (p.id.clone(), s.id)).unwrap();
    answer_current(&mut s, &c, false);
    assert_eq!(s.verdict, Some(Verdict::Wrong));
    s.next(&c, &mut prog);
    // second point, answered correctly
    answer_current(&mut s, &c, true);
    s.next(&c, &mut prog);
    // the missed point is back, with the same sentence
    let (p1, s1) = s.current(&c).map(|(p, s)| (p.id.clone(), s.id)).unwrap();
    assert_eq!(p1, p0);
    assert_eq!(s1, s0);
    answer_current(&mut s, &c, true);
    s.next(&c, &mut prog);
    assert!(s.finished());
    assert_eq!(prog.log.iter().filter(|e| !e.practice).count(), 2, "each point graded once");
    assert_eq!(prog.log.iter().find(|e| e.point == p0).unwrap().grade, 1);
    // the repeat is logged too, as practice
    let practice: Vec<_> = prog.log.iter().filter(|e| e.practice).collect();
    assert_eq!(practice.len(), 1);
    assert_eq!((practice[0].point.as_str(), practice[0].grade), (p0.as_str(), 3));
    assert_eq!(s.correct_first_try, 1);
    assert_eq!(s.done, 2);
}

#[test]
fn typo_override_counts_as_correct() {
    let c = Content::bundled();
    let mut prog = Progress::in_memory();
    let mut s = Session::new(&c, &prog, first_ids(&c, 1), false);
    answer_current(&mut s, &c, false);
    s.override_correct();
    assert_eq!(s.verdict, Some(Verdict::Correct));
    s.next(&c, &mut prog);
    assert!(s.finished());
    assert_eq!(prog.log[0].grade, 3);
}

#[test]
fn retry_clears_the_verdict() {
    let c = Content::bundled();
    let prog = Progress::in_memory();
    let mut s = Session::new(&c, &prog, first_ids(&c, 1), false);
    answer_current(&mut s, &c, false);
    s.retry();
    assert_eq!(s.verdict, None);
    assert!(s.input.is_empty() && s.raw.is_empty());
    answer_current(&mut s, &c, true);
    assert_eq!(s.verdict, Some(Verdict::Correct));
}

#[test]
fn empty_or_whitespace_input_is_not_submitted() {
    let c = Content::bundled();
    let prog = Progress::in_memory();
    let mut s = Session::new(&c, &prog, first_ids(&c, 1), false);
    s.on_input("   ", true);
    assert!(!s.submit(&c));
    assert_eq!(s.verdict, None);
}

#[test]
fn romaji_answers_are_accepted_and_preview_is_kana() {
    let c = Content::bundled();
    let prog = Progress::in_memory();
    let id = "deshita".to_string();
    let mut s = Session::new(&c, &prog, vec![id], false);
    s.on_input("deshi", true);
    assert_eq!(s.input, "でし");
    assert_eq!(s.raw, "deshi");
    s.on_input("deshita", true);
    assert!(s.submit(&c));
    assert_eq!(s.verdict, Some(Verdict::Correct));
}

#[test]
fn kanji_and_kana_answers_both_accepted() {
    let c = Content::bundled();
    let p = c.get("te_kudasai").unwrap();
    let s = p.sentences.iter().find(|s| s.answers.iter().any(|a| a.contains('下'))).unwrap();
    let norm: Vec<String> = s.answers.iter().map(|a| bunpo_core::kana::normalize(a)).collect();
    assert!(norm.iter().any(|a| a.contains("ください")));
    assert!(norm.iter().any(|a| a.contains("下さい")));
}

#[test]
fn reviews_avoid_repeating_the_last_sentence() {
    let c = Content::bundled();
    let mut prog = Progress::in_memory();
    let id = c.points[0].id.clone();
    let mut last = 0;
    for _ in 0..20 {
        let mut s = Session::new(&c, &prog, vec![id.clone()], false);
        let sid = s.current(&c).unwrap().1.id;
        assert_ne!(sid, last);
        answer_current(&mut s, &c, true);
        s.next(&c, &mut prog);
        last = sid;
    }
}

#[test]
fn grading_uses_the_clock() {
    let c = Content::bundled();
    let mut prog = Progress::in_memory();
    clock::advance(100 * 86_400_000);
    let mut s = Session::new(&c, &prog, first_ids(&c, 1), true);
    answer_current(&mut s, &c, true);
    s.next(&c, &mut prog);
    let card = prog.card(&c.points[0].id);
    assert!(card.last_review >= clock::now_ms() - 60_000);
    clock::reset();
    assert!(card.last_review > clock::now_ms() + 99 * 86_400_000);
}

// ------------------------------------------------------------------ guards

#[test]
fn checking_twice_or_with_nothing_left_does_nothing() {
    let c = Content::bundled();
    let prog = Progress::in_memory();
    let mut s = Session::new(&c, &prog, first_ids(&c, 1), false);
    let answer = s.current(&c).unwrap().1.answers[0].clone();
    s.on_input(&answer, false);
    assert!(s.submit(&c));
    assert_eq!(s.verdict, Some(Verdict::Correct));
    assert!(!s.submit(&c), "already checked");
    let mut empty = Session::new(&c, &prog, vec![], false);
    assert!(empty.finished() && !empty.submit(&c));
}

#[test]
fn typo_and_editing_only_apply_to_a_wrong_answer() {
    let c = Content::bundled();
    let prog = Progress::in_memory();
    let mut s = Session::new(&c, &prog, first_ids(&c, 1), false);
    // nothing checked yet
    s.override_correct();
    assert_eq!(s.verdict, None);
    assert!(!s.edit_after_wrong());
    // right: stays right
    let answer = s.current(&c).unwrap().1.answers[0].clone();
    s.on_input(&answer, false);
    s.submit(&c);
    assert!(!s.edit_after_wrong());
    s.override_correct();
    assert_eq!(s.verdict, Some(Verdict::Correct));
}

#[test]
fn editing_a_wrong_answer_reopens_it_as_a_typo_fix() {
    let c = Content::bundled();
    let prog = Progress::in_memory();
    let mut s = Session::new(&c, &prog, first_ids(&c, 1), false);
    s.on_input("ぜんぜんちがう", false);
    s.submit(&c);
    assert_eq!(s.verdict, Some(Verdict::Wrong));
    assert!(s.edit_after_wrong());
    assert_eq!(s.verdict, None, "open again for the fix");
    assert!(!s.edit_after_wrong(), "once");
}

#[test]
fn a_right_answer_waits_for_a_rating_that_is_logged_but_does_not_change_the_schedule() {
    let c = Content::bundled();
    let mut due = Vec::new();
    for rating in 1..=4u8 {
        clock::reset();
        let mut prog = Progress::in_memory();
        let mut s = Session::new(&c, &prog, first_ids(&c, 1), false);
        let id = s.point.clone().unwrap();
        clock::advance(4_200);
        answer_current(&mut s, &c, true);
        assert!(s.needs_rating());
        clock::advance(9_000); // reading the feedback is not thinking time
        s.rate(&c, &mut prog, rating);
        assert!(s.finished());
        let e = &prog.log[0];
        assert_eq!((e.rating, e.grade, e.level.as_str(), e.practice), (rating, 3, "New", false));
        assert!((4_200..5_000).contains(&e.ms), "thought for {} ms", e.ms);
        assert!(e.ts > 1_600_000_000_000, "a UTC timestamp in ms");
        due.push(prog.card(&id).due - e.ts);
    }
    clock::reset();
    assert!(due.windows(2).all(|w| w[0] == w[1]), "same schedule whatever the rating: {due:?}");
}

#[test]
fn wrong_and_retried_answers_are_logged_as_again_without_a_rating() {
    let c = Content::bundled();
    let mut prog = Progress::in_memory();
    let mut s = Session::new(&c, &prog, first_ids(&c, 2), false);
    answer_current(&mut s, &c, false);
    assert!(!s.needs_rating());
    s.rate(&c, &mut prog, 4); // ignored: nothing to rate
    assert!(prog.log.is_empty());
    s.retry();
    answer_current(&mut s, &c, true);
    assert!(!s.needs_rating(), "a retried item counts as missed");
    s.next(&c, &mut prog);
    assert_eq!((prog.log[0].rating, prog.log[0].grade), (1, 1));
    // a right answer left unrated (leaving the quiz) is logged with rating 0
    answer_current(&mut s, &c, true);
    s.commit_pending(&c, &mut prog);
    assert_eq!((prog.log[1].rating, prog.log[1].grade), (0, 3));
}

#[test]
fn the_level_logged_is_the_one_before_the_answer_and_history_survives_a_reset() {
    let c = Content::bundled();
    let mut prog = Progress::in_memory();
    let ids = first_ids(&c, 1);
    let mut levels = Vec::new();
    for _ in 0..4 {
        let mut s = Session::new(&c, &prog, ids.clone(), false);
        levels.push(prog.card(&ids[0]).level_name());
        answer_current(&mut s, &c, true);
        s.rate(&c, &mut prog, 3);
    }
    let logged: Vec<&str> = prog.history(&ids[0]).map(|e| e.level.as_str()).collect();
    assert_eq!(logged, levels);
    assert_ne!(levels[0], levels[3]);
    prog.reset_point(&ids[0]);
    assert_eq!(prog.history(&ids[0]).count(), 4);
}

#[test]
fn a_resumed_session_times_from_when_it_is_shown_again() {
    let c = Content::bundled();
    let prog = Progress::in_memory();
    let s = Session::new(&c, &prog, first_ids(&c, 1), false);
    let mut back: Session = serde_json::from_str(&serde_json::to_string(&s).unwrap()).unwrap();
    let mut prog = prog;
    answer_current(&mut back, &c, true);
    back.rate(&c, &mut prog, 3);
    assert_eq!(prog.log[0].ms, 0, "not timed: unknown");
    let mut back: Session = serde_json::from_str(&serde_json::to_string(&s).unwrap()).unwrap();
    back.start_clock();
    clock::advance(1_500);
    answer_current(&mut back, &c, true);
    back.rate(&c, &mut prog, 3);
    clock::reset();
    assert!(prog.log[1].ms >= 1_500);
}
