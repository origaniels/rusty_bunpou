//! Numbers for the Stats screen, computed from the cards and the review log: upcoming reviews,
//! leeches, the daily streak and past activity. Days are local (the phone's time zone) and start
//! at the hour chosen in the settings (`Settings::day_start`).

use crate::clock::study_day;
use crate::store::{LogEntry, Progress};
use std::collections::HashMap;

/// A point is a leech when at least this many of its last [`LEECH_WINDOW`] reviews were wrong.
pub const LEECH_WRONG: usize = 3;
pub const LEECH_WINDOW: usize = 5;

/// Reviews due on each of the next `days` local days; today includes everything already due.
pub fn forecast(p: &Progress, now: i64, days: usize) -> Vec<usize> {
    let day = |ms| study_day(ms, p.settings.day_start);
    let today = day(now);
    let mut out = vec![0; days];
    for c in p.cards.values().filter(|c| !c.is_new()) {
        let d = (day(c.due) - today).max(0);
        if (d as usize) < days {
            out[d as usize] += 1;
        }
    }
    out
}

/// The reviews of one point that count for leeches: after its lesson (the lesson quiz is
/// not a review), and only since it was last (re)learned. `entries` = its log, oldest first.
fn counted<'a>(p: &Progress, point: &str, mut entries: Vec<&'a LogEntry>) -> Vec<&'a LogEntry> {
    let card = p.card(point);
    entries.retain(|e| !e.practice);
    if card.learned_at > 0 {
        entries.retain(|e| e.ts > card.learned_at);
    } else if !entries.is_empty() {
        entries.remove(0); // older files: the first entry was the lesson
    }
    entries
}

fn mistakes_in(entries: &[&LogEntry]) -> usize {
    entries.iter().rev().take(LEECH_WINDOW).filter(|e| e.grade < 3).count()
}

/// Wrong answers among the point's last [`LEECH_WINDOW`] reviews.
pub fn recent_mistakes(p: &Progress, point: &str) -> usize {
    mistakes_in(&counted(p, point, p.log.iter().filter(|e| e.point == point).collect()))
}

/// Points the user keeps getting wrong lately (most mistakes first, then by id).
pub fn leeches(p: &Progress) -> Vec<(String, usize)> {
    // one pass over the log (it grows with every review)
    let mut by_point: HashMap<&str, Vec<&LogEntry>> = HashMap::new();
    for e in p.log.iter().filter(|e| !e.practice) {
        by_point.entry(e.point.as_str()).or_default().push(e);
    }
    let mut out: Vec<(String, usize)> = by_point
        .into_iter()
        .filter(|(id, _)| p.cards.get(*id).is_some_and(|c| !c.is_new()))
        .map(|(id, entries)| (id.to_string(), mistakes_in(&counted(p, id, entries))))
        .filter(|(_, n)| *n >= LEECH_WRONG)
        .collect();
    out.sort_by(|a, b| b.1.cmp(&a.1).then(a.0.cmp(&b.0)));
    out
}

/// Answers per local day for the `days` days ending today (oldest first).
pub fn activity(p: &Progress, now: i64, days: usize) -> Vec<usize> {
    let day = |ms| study_day(ms, p.settings.day_start);
    let today = day(now);
    let mut out = vec![0; days];
    for e in p.log.iter().filter(|e| !e.practice) {
        let back = today - day(e.ts);
        if back >= 0 && (back as usize) < days {
            out[days - 1 - back as usize] += 1;
        }
    }
    out
}

/// (current, longest) run of consecutive days with at least one answer. The current streak
/// still counts when today has nothing yet but yesterday had (the day isn't over).
pub fn streak(p: &Progress, now: i64) -> (usize, usize) {
    let day = |ms| study_day(ms, p.settings.day_start);
    let mut days: Vec<i64> = p.log.iter().filter(|e| !e.practice).map(|e| day(e.ts)).collect();
    days.sort_unstable();
    days.dedup();
    let mut longest = 0;
    let mut run = 0;
    let mut prev = i64::MIN;
    for &d in &days {
        run = if d == prev + 1 { run + 1 } else { 1 };
        longest = longest.max(run);
        prev = d;
    }
    let today = day(now);
    let current = if prev == today || prev == today - 1 { run } else { 0 };
    (current, longest)
}
