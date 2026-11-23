//! Scheduling behaviour over long simulated periods.

use bunpo_core::fsrs::{self, DAY_MS};
use bunpo_core::store::scheduler::{grade, LEARNING_STEPS, MAX_GROWTH, RELEARN_DELAY, RELEARN_FROM_STEP};
use bunpo_core::store::Card;

const T0: i64 = 1_800_000_000_000;
const HOUR: i64 = 3_600_000;

/// Review a card exactly when due, `n` times, always correct. Returns the intervals in days.
fn perfect_run(mut card: Card, mut t: i64, n: usize, retention: f64) -> (Card, Vec<f64>, i64) {
    let mut ivs = vec![];
    for _ in 0..n {
        t = card.due.max(t);
        let next = grade(&card, true, t, retention, 1);
        ivs.push((next.due - t) as f64 / DAY_MS as f64);
        card = next;
    }
    (card, ivs, t)
}

fn learned_card(t: i64) -> Card {
    grade(&Card::default(), true, t, 0.9, 1)
}

#[test]
fn learning_steps_then_fsrs() {
    let c = learned_card(T0);
    assert_eq!((c.state, c.step), (1, 1));
    assert_eq!(c.due - T0, LEARNING_STEPS[0]);
    let c2 = grade(&c, true, c.due, 0.9, 1);
    assert_eq!(c2.due - c.due, LEARNING_STEPS[1]);
    let mut c = c2;
    for k in 2..LEARNING_STEPS.len() {
        let n = grade(&c, true, c.due, 0.9, 1);
        assert_eq!(n.due - c.due, LEARNING_STEPS[k]);
        c = n;
    }
    let g = grade(&c, true, c.due, 0.9, 1);
    assert_eq!(g.state, 2, "graduates to FSRS after the learning steps");
    assert!(g.due - c.due >= DAY_MS);
}

#[test]
fn intervals_never_grow_more_than_the_cap() {
    let (_, ivs, _) = perfect_run(Card::default(), T0, 15, 0.9);
    for w in ivs.windows(2) {
        assert!(w[1] <= w[0].max(1.0) * MAX_GROWTH * 1.06 + 1e-9, "{ivs:?}");
    }
}

#[test]
fn perfect_recall_intervals_grow_and_levels_progress() {
    let (card, ivs, _) = perfect_run(Card::default(), T0, 14, 0.9);
    // after the two learning steps, intervals strictly increase until the cap
    let fsrs_part = &ivs[LEARNING_STEPS.len()..];
    for w in fsrs_part.windows(2) {
        assert!(w[1] > w[0] || (w[1] - 365.0).abs() < 20.0, "intervals {ivs:?}");
    }
    assert!(fsrs_part[1] > 7.0, "a week+ soon after graduating: {ivs:?}");
    assert!(*ivs.last().unwrap() > 100.0, "months after 12 reviews: {ivs:?}");
    assert_eq!(card.level_name(), "Mastered");
}

#[test]
fn level_names_follow_stability() {
    let mut names = vec![];
    let mut card = Card::default();
    let mut t = T0;
    names.push(card.level_name());
    for _ in 0..14 {
        t = card.due.max(t);
        card = grade(&card, true, t, 0.9, 1);
        names.push(card.level_name());
    }
    let order = ["New", "Beginner", "Adept", "Seasoned", "Expert", "Mastered"];
    let idx: Vec<usize> = names.iter().map(|n| order.iter().position(|o| o == n).unwrap()).collect();
    assert!(idx.windows(2).all(|w| w[1] >= w[0]), "levels never go down on success: {names:?}");
    assert_eq!(names.last().copied(), Some("Mastered"));
}

#[test]
fn intervals_are_capped() {
    let (_, ivs, _) = perfect_run(Card::default(), T0, 25, 0.9);
    assert!(ivs.iter().all(|&d| d <= 365.0 * 1.06), "cap 365 days (+fuzz): {ivs:?}");
}

#[test]
fn lapse_resets_to_relearning_and_recovers() {
    let (card, _, t) = perfect_run(Card::default(), T0, 9, 0.9);
    assert_eq!(card.state, 2);
    let before = card.stability;
    let t = card.due.max(t);
    let lapsed = grade(&card, false, t, 0.9, 1);
    assert_eq!((lapsed.state, lapsed.step, lapsed.lapses), (1, RELEARN_FROM_STEP, 1));
    assert_eq!(lapsed.due - t, RELEARN_DELAY);
    assert!(lapsed.stability < before, "stability drops after forgetting");
    assert_eq!(lapsed.level_name(), "Beginner", "an hour away = Beginner");
    // relearning: learning steps again, then back to FSRS
    let (rec, ivs, _) = perfect_run(lapsed, t, 4, 0.9);
    assert_eq!(rec.state, 2);
    assert_eq!(rec.lapses, 1, "lapses are only counted from the review state");
    assert_eq!(ivs[0] * 24.0, 24.0, "relearning resumes at the 1-day step: {ivs:?}");
    assert!(ivs[2] <= 3.0 * MAX_GROWTH * 1.06, "no jump back to months right away: {ivs:?}");
}

#[test]
fn failing_during_learning_is_not_a_lapse() {
    let c = learned_card(T0);
    let f = grade(&c, false, c.due, 0.9, 1);
    assert_eq!((f.state, f.step, f.lapses), (1, 0, 0));
}

#[test]
fn higher_retention_means_shorter_intervals() {
    let (_, lo, _) = perfect_run(Card::default(), T0, 12, 0.85);
    let (_, hi, _) = perfect_run(Card::default(), T0, 12, 0.95);
    // compare the underlying formula (fuzz makes single runs noisy)
    for s in [3.0, 10.0, 40.0] {
        assert!(fsrs::interval_days(s, 0.95, 365.0) < fsrs::interval_days(s, 0.85, 365.0));
    }
    assert!(hi.iter().sum::<f64>() < lo.iter().sum::<f64>(), "{hi:?} vs {lo:?}");
}

#[test]
fn reviewing_late_still_increases_stability() {
    let (card, _, t) = perfect_run(Card::default(), T0, 7, 0.9);
    let late = card.due + 30 * DAY_MS;
    let next = grade(&card, true, late.max(t), 0.9, 1);
    assert!(next.stability > card.stability);
}

#[test]
fn fuzz_stays_within_five_percent() {
    let (card, _, _) = perfect_run(Card::default(), T0, 10, 0.9);
    let t = card.due;
    for _ in 0..200 {
        let n = grade(&card, true, t, 0.9, 1);
        let days = (n.due - t) as f64 / DAY_MS as f64;
        let prev = (t - card.last_review) as f64 / DAY_MS as f64;
        let base = fsrs::interval_days(n.stability, 0.9, 365.0).min(prev * MAX_GROWTH);
        assert!((days / base - 1.0).abs() <= 0.051, "{days} vs {base}");
    }
}

#[test]
fn fsrs_reference_values() {
    // first-review stability equals the default weights for each grade
    let s: Vec<f64> = (1..=4).map(|g| fsrs::review(None, 0.0, g).stability).collect();
    assert!((s[0] - 0.40255).abs() < 1e-9 && (s[2] - 3.173).abs() < 1e-9, "{s:?}");
    // retrievability is 90% after exactly S days
    assert!((fsrs::retrievability(10.0, 10.0) - 0.9).abs() < 1e-9);
    // interval at 90% retention equals stability
    assert!((fsrs::interval_days(20.0, 0.9, 365.0) - 20.0).abs() < 1e-9);
    // difficulty stays within bounds whatever happens
    let mut m = fsrs::review(None, 0.0, 1);
    for g in [1, 1, 1, 4, 4, 4, 4, 1, 3] {
        m = fsrs::review(Some(m), 2.0, g);
        assert!((1.0..=10.0).contains(&m.difficulty));
        assert!(m.stability > 0.0);
    }
}

/// A month of realistic use: 5 new points a day, reviews done once a day, 85% accuracy.
/// The daily workload must stay reasonable and nothing may be left overdue for long.
#[test]
fn month_of_daily_use_has_bounded_workload() {
    let mut cards: Vec<Card> = vec![];
    let mut rng = fastrand::Rng::with_seed(42);
    let mut max_per_day = 0;
    for day in 0..30 {
        let t = T0 + day * DAY_MS + 9 * HOUR;
        // two sessions a day (morning + evening) like a typical user
        for session_t in [t, t + 10 * HOUR] {
            let mut done = 0;
            for c in cards.iter_mut() {
                if c.due <= session_t {
                    let ok = rng.f64() < 0.85;
                    *c = grade(c, ok, session_t, 0.9, 1);
                    done += 1;
                }
            }
            max_per_day = max_per_day.max(done);
        }
        if cards.len() < 74 {
            for _ in 0..5 {
                cards.push(grade(&Card::default(), true, t, 0.9, 1));
            }
        }
        // nothing should be overdue by more than a day at the end of a day
        let end = t + 14 * HOUR;
        let stale = cards.iter().filter(|c| c.due < end - DAY_MS).count();
        assert_eq!(stale, 0, "day {day}");
    }
    assert!(max_per_day < 60, "max reviews in one session: {max_per_day}");
    let mastered_or_expert = cards.iter().filter(|c| c.stability >= 30.0).count();
    let beginners = cards.iter().filter(|c| c.level_name() == "Beginner").count();
    assert!(beginners < cards.len() / 2, "most cards progressed past Beginner");
    let _ = mastered_or_expert;
}

// ------------------------------------------------------------------ self-graded (flashcards)

use bunpo_core::store::scheduler::grade_self;

/// Review a card when due with the same self-grade every time; returns it and how many reviews.
fn run_with(grade_: u8, until_days: f64) -> (Card, usize) {
    let (mut card, mut t, mut n) = (Card::default(), T0, 0);
    while card.state < 2 || (card.due - t) as f64 / (DAY_MS as f64) < until_days {
        t = card.due.max(t);
        card = grade_self(&card, grade_, t, 0.9);
        n += 1;
        assert!(n < 200, "never got there");
    }
    (card, n)
}

#[test]
fn out_of_range_self_grades_are_clamped() {
    let new = Card::default();
    assert_eq!(grade_self(&new, 0, T0, 0.9).due, grade_self(&new, 1, T0, 0.9).due);
    assert_eq!(grade_self(&new, 9, T0, 0.9).due, grade_self(&new, 4, T0, 0.9).due);
}

#[test]
fn easy_reaches_long_intervals_in_fewer_reviews_than_good() {
    let (_, easy) = run_with(4, 30.0);
    let (_, good) = run_with(3, 30.0);
    assert!(easy < good, "easy {easy} vs good {good}");
}

#[test]
fn hard_never_graduates_a_card_from_the_learning_steps() {
    let mut card = Card::default();
    let mut t = T0;
    for _ in 0..10 {
        t = card.due.max(t);
        card = grade_self(&card, 2, t, 0.9);
        assert_eq!((card.state, card.step), (1, 0));
        assert!(card.due - t < LEARNING_STEPS[0]);
    }
}

#[test]
fn self_graded_intervals_respect_the_growth_cap_too() {
    let mut card = learned_card(T0);
    let mut last = 0.0f64;
    for _ in 0..12 {
        let t = card.due;
        card = grade_self(&card, 4, t, 0.9);
        let iv = (card.due - t) as f64 / DAY_MS as f64;
        if card.state == 2 && last >= 1.0 {
            assert!(iv <= last * MAX_GROWTH * 1.06, "{last} -> {iv}");
        }
        last = iv;
    }
}

#[test]
fn again_on_a_graduated_card_is_a_lapse_that_resumes_relearning() {
    let (card, _) = run_with(3, 5.0);
    let t = card.due;
    let lapsed = grade_self(&card, 1, t, 0.9);
    assert_eq!((lapsed.state, lapsed.step, lapsed.lapses), (1, RELEARN_FROM_STEP, card.lapses + 1));
    assert_eq!(lapsed.due, t + RELEARN_DELAY);
    // memory drops but isn't wiped
    assert!(lapsed.stability < card.stability && lapsed.stability > 0.0);
    // a grammar-style wrong answer does exactly the same
    let wrong = grade(&card, false, t, 0.9, 0);
    assert_eq!((wrong.state, wrong.step, wrong.due), (lapsed.state, lapsed.step, lapsed.due));
}
