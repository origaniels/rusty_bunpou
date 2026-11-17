//! When to remind the user about reviews.

use crate::store::Card;

const MIN: i64 = 60_000;
/// If reviews are already due when the app goes away, nag again after this long.
pub const ALREADY_DUE_DELAY: i64 = 120 * MIN;
/// Reviews becoming due shortly after the reminder are counted in it.
pub const GROUPING_WINDOW: i64 = 30 * MIN;

/// `(time_ms, count)` of the next reminder, or `None` when nothing is learned yet.
pub fn next_reminder<'a>(cards: impl IntoIterator<Item = &'a Card>, now: i64) -> Option<(i64, usize)> {
    let dues: Vec<i64> = cards.into_iter().filter(|c| c.state > 0).map(|c| c.due).collect();
    let earliest = *dues.iter().min()?;
    let first = if earliest <= now { now + ALREADY_DUE_DELAY } else { earliest };
    // group reviews that become due shortly after, and fire once they are all due,
    // so the count in the notification matches what the app shows
    let grouped: Vec<i64> = dues.iter().copied().filter(|&d| d <= first + GROUPING_WINDOW).collect();
    let at = grouped.iter().copied().max().unwrap_or(first).max(first);
    Some((at, grouped.len()))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn card(due: i64) -> Card {
        Card { state: 1, due, ..Default::default() }
    }

    #[test]
    fn nothing_learned_no_reminder() {
        assert_eq!(next_reminder(&[Card::default()], 0), None);
        assert_eq!(next_reminder(&[], 0), None);
    }

    #[test]
    fn reminds_at_earliest_due_and_groups_close_ones() {
        let now = 1_000 * MIN;
        let cards = [card(now + 60 * MIN), card(now + 80 * MIN), card(now + 200 * MIN)];
        // fires when the second one is due too, so "2 waiting" is true when it shows
        assert_eq!(next_reminder(&cards, now), Some((now + 80 * MIN, 2)));
    }

    #[test]
    fn already_due_reviews_remind_later_not_now() {
        let now = 1_000 * MIN;
        let cards = [card(now - 5 * MIN), card(now + 10 * MIN), card(now + 500 * MIN)];
        let (at, count) = next_reminder(&cards, now).unwrap();
        assert_eq!(at, now + ALREADY_DUE_DELAY);
        assert_eq!(count, 2);
    }
}
