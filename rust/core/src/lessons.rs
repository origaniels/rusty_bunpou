//! Which grammar points new lessons come from.

use crate::content::Content;
use crate::store::Progress;

/// JLPT levels in teaching order.
pub const LEVELS: [&str; 5] = ["N5", "N4", "N3", "N2", "N1"];

fn level_rank(level: &str) -> usize {
    LEVELS.iter().position(|l| *l == level).unwrap_or(0)
}

/// Ids of the points new lessons will teach, in order: points not learned yet, at the chosen
/// start level or above (N5 → N1). Lower levels are skipped (they stay "New" and can be learned
/// by choosing a lower start level); after N1 there is nothing more, no wrap-around.
pub fn lesson_queue(content: &Content, progress: &Progress) -> Vec<String> {
    let from = level_rank(&progress.settings.start_level);
    content
        .points
        .iter()
        .filter(|p| level_rank(&p.level) >= from && progress.card(&p.id).is_new())
        .map(|p| p.id.clone())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::store::Card;

    fn level_of<'a>(c: &'a Content, id: &str) -> &'a str {
        &c.get(id).unwrap().level
    }

    #[test]
    fn default_starts_at_n5_in_content_order() {
        let c = Content::bundled();
        let p = Progress::in_memory();
        let q = lesson_queue(&c, &p);
        assert_eq!(q.len(), c.points.len());
        assert_eq!(q[0], c.points[0].id);
    }

    #[test]
    fn starting_at_n2_skips_lower_levels_and_stops_after_n1() {
        let c = Content::bundled();
        let mut p = Progress::in_memory();
        p.settings.start_level = "N2".into();
        let q = lesson_queue(&c, &p);
        assert!(!q.is_empty());
        assert_eq!(level_of(&c, &q[0]), "N2");
        assert!(q.iter().all(|id| ["N2", "N1"].contains(&level_of(&c, id))));
        assert_eq!(level_of(&c, q.last().unwrap()), "N1", "ends with N1, no wrap-around to N5");
        // skipped levels are untouched: still New, not marked as known
        assert!(c.points.iter().filter(|x| x.level == "N5").all(|x| p.card(&x.id).is_new()));
    }

    #[test]
    fn learned_points_are_not_offered_again() {
        let c = Content::bundled();
        let mut p = Progress::in_memory();
        p.settings.start_level = "N3".into();
        let first = lesson_queue(&c, &p)[0].clone();
        p.cards.insert(first.clone(), Card { state: 1, ..Default::default() });
        assert!(!lesson_queue(&c, &p).contains(&first));
    }

    #[test]
    fn unknown_level_falls_back_to_n5() {
        let c = Content::bundled();
        let mut p = Progress::in_memory();
        p.settings.start_level = "N9".into();
        assert_eq!(lesson_queue(&c, &p).len(), c.points.len());
    }
}
