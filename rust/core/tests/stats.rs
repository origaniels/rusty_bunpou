use bunpo_core::clock::local_day;
use bunpo_core::stats::*;
use bunpo_core::store::{Card, LogEntry, Progress};

const H: i64 = 3_600_000;
const D: i64 = 24 * H;

/// Local noon of some day, so ± whole days never cross midnight (even with summer time).
fn noon() -> i64 {
    let t = 20_000 * D;
    t - (t + bunpo_core::clock::utc_offset_ms(t)).rem_euclid(D) + 12 * H
}

fn log(p: &mut Progress, point: &str, ts: i64, correct: bool) {
    p.log.push(LogEntry { point: point.into(), sentence: 1, ts, grade: if correct { 3 } else { 1 }, ..Default::default() });
}

fn learned(p: &mut Progress, point: &str, at: i64) {
    p.cards.insert(point.into(), Card { state: 2, due: at + 30 * D, learned_at: at, ..Default::default() });
    log(p, point, at, true); // the lesson quiz
}

#[test]
fn forecast_counts_per_local_day_and_puts_overdue_today() {
    let now = noon();
    let mut p = Progress::in_memory();
    for (id, due) in [("a", now - 3 * D), ("b", now + H), ("c", now + D), ("d", now + 6 * D), ("e", now + 7 * D)] {
        p.cards.insert(id.into(), Card { state: 2, due, ..Default::default() });
    }
    p.cards.insert("new".into(), Card::default());
    assert_eq!(forecast(&p, now, 7), vec![2, 1, 0, 0, 0, 0, 1]);
}

#[test]
fn leech_needs_three_of_the_last_five_reviews_wrong() {
    let t = noon();
    let mut p = Progress::in_memory();
    learned(&mut p, "x", t);
    // mistakes spread over months, with successes in between: not a leech
    for (i, ok) in [false, true, true, false, true, true, false, true].into_iter().enumerate() {
        log(&mut p, "x", t + (i as i64 + 1) * 10 * D, ok);
    }
    assert_eq!(recent_mistakes(&p, "x"), 2);
    assert!(leeches(&p).is_empty());
    // then a bad patch: wrong, wrong (relearn step), right, wrong
    for (i, ok) in [false, false, true, false].into_iter().enumerate() {
        log(&mut p, "x", t + 100 * D + i as i64 * H, ok);
    }
    assert_eq!(leeches(&p), vec![("x".to_string(), 3)]);
    // three right in a row: no longer a leech
    for i in 0..3 {
        log(&mut p, "x", t + 110 * D + i * D, true);
    }
    assert!(leeches(&p).is_empty());
}

#[test]
fn lesson_quiz_and_mistakes_before_a_reset_do_not_count() {
    let t = noon();
    let mut p = Progress::in_memory();
    p.cards.insert("y".into(), Card { state: 2, due: t, ..Default::default() });
    // old file (no learned_at): the first entry is the lesson, failed twice there
    log(&mut p, "y", t, false);
    log(&mut p, "y", t + D, false);
    log(&mut p, "y", t + 2 * D, false);
    assert_eq!(recent_mistakes(&p, "y"), 2, "the lesson quiz is skipped");
    // the point is reset and learned again: only reviews after that count
    p.cards.get_mut("y").unwrap().learned_at = t + 3 * D;
    log(&mut p, "y", t + 3 * D, false);
    log(&mut p, "y", t + 4 * D, false);
    assert_eq!(recent_mistakes(&p, "y"), 1);
}

#[test]
fn learned_at_is_set_by_the_first_grade() {
    let c = bunpo_core::store::scheduler::grade(&Card::default(), false, 1234, 0.9, 1);
    assert_eq!(c.learned_at, 1234);
    let c2 = bunpo_core::store::scheduler::grade(&c, true, 9999, 0.9, 1);
    assert_eq!(c2.learned_at, 1234);
}

#[test]
fn streak_and_activity() {
    let now = noon();
    let mut p = Progress::in_memory();
    assert_eq!(streak(&p, now), (0, 0));
    // 4 days in a row long ago, a gap, then 3 days ending yesterday
    for d in [-20, -19, -18, -17, -3, -2, -1] {
        log(&mut p, "a", now + d * D, true);
    }
    log(&mut p, "a", now - D + H, false); // two answers yesterday
    assert_eq!(streak(&p, now), (3, 4), "today not done yet: the streak is still alive");
    log(&mut p, "a", now, true);
    assert_eq!(streak(&p, now), (4, 4));
    assert_eq!(streak(&p, now + 2 * D), (0, 4), "a missed day breaks it");
    assert_eq!(activity(&p, now, 4), vec![1, 1, 2, 1]);
    assert_eq!(local_day(now) - local_day(now - D), 1);
}

#[test]
fn a_late_session_counts_for_the_day_before_when_the_day_starts_later() {
    let mut p = Progress::in_memory();
    let day1 = noon();
    // reviews at noon on day 1, then 1 AM and noon on day 3 (nothing on day 2 before 1 AM)
    for ts in [day1, day1 + D + 13 * H, day1 + 2 * D] {
        log(&mut p, "x", ts, true);
    }
    let now = day1 + 2 * D;
    assert_eq!(streak(&p, now), (1, 1), "midnight start: day 2 is empty");
    p.settings.day_start = 4;
    assert_eq!(streak(&p, now), (3, 3), "4:00 start: the 1 AM session belongs to day 2");
    assert_eq!(activity(&p, now, 3), vec![1, 1, 1]);
}

#[test]
fn practice_repeats_are_not_reviews() {
    let t = noon();
    let mut p = Progress::in_memory();
    learned(&mut p, "x", t);
    for i in 0..3 {
        log(&mut p, "x", t + D + i * H, false);
    }
    assert_eq!(leeches(&p).len(), 1);
    let before = (activity(&p, t + D, 2), p.reviews_since(t));
    for i in 0..5 {
        p.log.push(LogEntry { point: "x".into(), ts: t + D + 5 * H + i, grade: 3, practice: true, ..Default::default() });
    }
    assert_eq!(leeches(&p).len(), 1, "practice right answers don't clear a leech");
    assert_eq!((activity(&p, t + D, 2), p.reviews_since(t)), before);
    assert_eq!(p.history("x").count(), 9);
}
