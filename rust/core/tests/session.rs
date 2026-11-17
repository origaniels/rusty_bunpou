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
fn wrong_answers_come_back_with_another_sentence_but_grade_once() {
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
    // the missed point is back, with a different sentence
    let (p1, s1) = s.current(&c).map(|(p, s)| (p.id.clone(), s.id)).unwrap();
    assert_eq!(p1, p0);
    assert_ne!(s1, s0);
    answer_current(&mut s, &c, true);
    s.next(&c, &mut prog);
    assert!(s.finished());
    assert_eq!(prog.log.len(), 2, "each point graded once");
    assert_eq!(prog.log.iter().find(|e| e.point == p0).unwrap().grade, 1);
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
