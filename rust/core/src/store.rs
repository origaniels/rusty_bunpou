//! SRS state, settings and review log, persisted as one JSON file.

use crate::fsrs::{self, DAY_MS};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::{Path, PathBuf};

/// state: 0 = new, 1 = learning (short fixed steps), 2 = review (FSRS intervals).
#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct Card {
    pub state: u8,
    pub stability: f64,
    pub difficulty: f64,
    pub due: i64,
    pub last_review: i64,
    pub reps: u32,
    pub lapses: u32,
    pub step: u32,
    pub last_sentence: u64,
    /// when the point was (re)learned in a lesson; 0 in files from before this was recorded
    #[serde(default)]
    pub learned_at: i64,
}

impl Card {
    pub fn is_new(&self) -> bool {
        self.state == 0
    }

    /// Current scheduled interval in days.
    pub fn interval_days(&self) -> f64 {
        (self.due - self.last_review) as f64 / DAY_MS as f64
    }

    /// SRS-style level name derived from the current interval.
    pub fn level_name(&self) -> &'static str {
        let iv = self.interval_days();
        match () {
            _ if self.state == 0 => "New",
            _ if iv < 0.99 => "Beginner",
            _ if iv < 7.0 => "Adept",
            _ if iv < 30.0 => "Seasoned",
            _ if iv < 120.0 => "Expert",
            _ => "Mastered",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(default)]
pub struct Settings {
    pub furigana: bool,
    pub english: bool,
    pub romaji: bool,
    pub batch_size: u32,
    pub retention: f64,
    /// Remind (Android notification) when reviews become due.
    pub notifications: bool,
    /// JLPT level new lessons start at ("N5" … "N1"); lower levels are skipped, not marked known.
    pub start_level: String,
    /// Language of the app, translations and explanations: "en" or "fr".
    pub language: String,
    /// Vibrate briefly when an answer is checked (different for right and wrong).
    pub haptics: bool,
    /// Hour (0-23) the day starts at, for the daily goal, streak and stats: with 4, a review at
    /// 1 AM still counts for the day before.
    pub day_start: u32,
    /// Look for a new version on GitHub once a day; None until the user was asked.
    pub check_updates: Option<bool>,
    /// New words a day (vocabulary lessons), like `batch_size` for grammar points.
    pub vocab_goal: u32,
}

impl Settings {
    pub fn lang(&self) -> crate::i18n::Lang {
        crate::i18n::Lang::from_code(&self.language)
    }
}

impl Default for Settings {
    fn default() -> Self {
        Settings { furigana: true, english: true, romaji: true, batch_size: 5, retention: 0.9, notifications: true, start_level: "N5".into(), language: "en".into(), haptics: true, day_start: 0, check_updates: None, vocab_goal: 10 }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogEntry {
    pub point: String,
    pub sentence: u64,
    pub ts: i64,
    pub grade: u8,
    pub answer: String,
}

/// A problem the user noticed with a sentence, to be fixed in the content later.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct Report {
    pub point: String,
    /// 0 for a lesson (the point's explanation and examples)
    pub sentence: u64,
    pub ts: i64,
    /// one of [`REPORT_REASONS`]
    pub reason: String,
    pub note: String,
    /// what the user typed, if they were answering
    pub answer: String,
    /// UI language at the time (which translation they saw)
    pub lang: String,
}

/// Report reasons, in the order the app shows them.
pub const REPORT_REASONS: [&str; 5] = ["wrong-grammar", "translation", "reading", "answer-rejected", "other"];
/// Reasons for reporting a lesson (a report with `sentence` 0).
pub const LESSON_REPORT_REASONS: [&str; 3] = ["explanation", "example", "other"];

#[derive(Debug, Default, Serialize, Deserialize)]
#[serde(default)]
pub struct Progress {
    pub cards: HashMap<String, Card>,
    pub settings: Settings,
    pub log: Vec<LogEntry>,
    /// sentence reports, kept across resets and merged on import
    pub reports: Vec<Report>,
    /// the unfinished quiz (lesson or reviews), to resume it
    pub paused: Option<crate::session::Session>,
    /// the update check's memory (last check, newest release seen, version skipped)
    pub update: crate::update::UpdateState,
    /// vocabulary flashcards, two per word (see `vocab::card_id`)
    pub vocab: HashMap<String, Card>,
    /// self-graded vocabulary answers (`point` is the card id, `grade` 1-4)
    pub vocab_log: Vec<LogEntry>,
    #[serde(skip)]
    path: Option<PathBuf>,
}

impl Progress {
    /// Load progress; a missing file means a fresh start. A file that exists but can't be read
    /// or parsed is moved aside to `<file>.bad` first, so the next save can't overwrite (lose) it.
    pub fn load(path: &Path) -> Progress {
        let mut p: Progress = match std::fs::read_to_string(path) {
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Progress::default(),
            read => match read.ok().and_then(|s| serde_json::from_str(&s).ok()) {
                Some(p) => p,
                None => {
                    let mut bad = path.as_os_str().to_owned();
                    bad.push(".bad");
                    let _ = std::fs::rename(path, &bad);
                    Progress::default()
                }
            },
        };
        p.path = Some(path.to_path_buf());
        p
    }

    pub fn in_memory() -> Progress {
        Progress::default()
    }

    /// Atomic write (tmp file + rename).
    pub fn save(&self) {
        let Some(path) = &self.path else { return };
        let tmp = path.with_extension("tmp");
        if let Ok(json) = serde_json::to_string(self) {
            if std::fs::write(&tmp, json).is_ok() {
                let _ = std::fs::rename(&tmp, path);
            }
        }
    }

    /// Where this progress is saved (None in memory).
    pub fn path(&self) -> Option<&Path> {
        self.path.as_deref()
    }

    /// Replace everything with an exported progress file (JSON text). The current progress is kept
    /// next to the file as `<file>.before-import`, so an import can be undone by hand.
    /// Returns the number of learned points in the imported file.
    pub fn import(&mut self, json: &str) -> Result<usize, String> {
        let value: serde_json::Value = serde_json::from_str(json).map_err(|e| format!("not a progress file: {e}"))?;
        if !value.get("cards").is_some_and(|c| c.is_object()) {
            return Err("not a progress file (no \"cards\")".into());
        }
        let new: Progress = serde_json::from_value(value).map_err(|e| format!("not a progress file: {e}"))?;
        if let Some(path) = &self.path {
            let mut keep = path.as_os_str().to_owned();
            keep.push(".before-import");
            let current = serde_json::to_string(self).map_err(|e| e.to_string())?;
            std::fs::write(&keep, current).map_err(|e| format!("could not keep the current progress: {e}"))?;
        }
        self.cards = new.cards;
        self.settings = new.settings;
        self.log = new.log;
        self.vocab = new.vocab;
        self.vocab_log = new.vocab_log;
        self.paused = None;
        for r in new.reports {
            if !self.reports.contains(&r) {
                self.reports.push(r);
            }
        }
        self.reports.sort_by_key(|r| r.ts);
        self.save();
        Ok(self.cards.values().filter(|c| !c.is_new()).count())
    }

    pub fn card(&self, id: &str) -> Card {
        self.cards.get(id).cloned().unwrap_or_default()
    }

    pub fn reviews_since(&self, ts: i64) -> usize {
        self.log.iter().filter(|e| e.ts >= ts).count()
    }

    pub fn reset_all(&mut self) {
        self.cards.clear();
        self.log.clear();
        self.vocab.clear();
        self.vocab_log.clear();
        self.paused = None;
        self.save();
    }

    pub fn add_report(&mut self, report: Report) {
        self.reports.push(report);
        self.save();
    }

    pub fn reset_point(&mut self, id: &str) {
        self.cards.remove(id);
        self.paused = None;
        self.save();
    }
}

/// Scheduling policy: short learning steps first (like the early levels of typical SRS apps), then FSRS.
pub mod scheduler {
    use super::*;
    const HOUR: i64 = 3_600_000;
    /// Fixed steps before FSRS takes over (SRS-like early levels).
    pub const LEARNING_STEPS: [i64; 4] = [4 * HOUR, 8 * HOUR, 24 * HOUR, 72 * HOUR];
    /// First retry after a mistake.
    pub const RELEARN_DELAY: i64 = HOUR;
    /// After a lapse (mistake on a graduated point), relearning resumes at this learning step.
    pub const RELEARN_FROM_STEP: u32 = 2;
    /// An FSRS interval may be at most this many times the previous interval.
    pub const MAX_GROWTH: f64 = 3.0;

    /// A typed answer (grammar): right is "Good", wrong is "Again".
    pub fn grade(card: &Card, correct: bool, now: i64, retention: f64, sentence: u64) -> Card {
        schedule(card, if correct { 3 } else { 1 }, now, retention, sentence)
    }

    /// A self-graded answer (vocabulary flashcards): 1 Again, 2 Hard, 3 Good, 4 Easy.
    /// Again and Good do what a wrong and a right grammar answer do; Hard stays at the current
    /// learning step (or gets a shorter FSRS interval), Easy skips a step (or a longer interval).
    pub fn grade_self(card: &Card, grade: u8, now: i64, retention: f64) -> Card {
        schedule(card, grade.clamp(1, 4), now, retention, 0)
    }

    fn schedule(card: &Card, g: u8, now: i64, retention: f64, sentence: u64) -> Card {
        let elapsed = if card.last_review == 0 { 0.0 } else { (now - card.last_review) as f64 / DAY_MS as f64 };
        let prev = (card.reps > 0).then_some(fsrs::Memory { stability: card.stability, difficulty: card.difficulty });
        let mem = fsrs::review(prev, elapsed, g);
        let mut c = Card {
            stability: mem.stability,
            difficulty: mem.difficulty,
            last_review: now,
            reps: card.reps + 1,
            last_sentence: sentence,
            ..card.clone()
        };
        if card.is_new() {
            c.learned_at = now;
        }
        let step = card.step as usize;
        let learning = card.state <= 1 && step < LEARNING_STEPS.len();
        if g == 1 {
            if card.state == 2 {
                c.lapses += 1;
                c.step = RELEARN_FROM_STEP;
            } else {
                c.step = 0;
            }
            c.state = 1;
            c.due = now + RELEARN_DELAY;
        } else if learning && g == 2 {
            // the current step again (the previous step's delay; the first one for a new card)
            c.state = 1;
            c.due = now + LEARNING_STEPS[step.saturating_sub(1)];
        } else if learning && (g == 3 || step + 1 < LEARNING_STEPS.len()) {
            // Good: the next step; Easy: the one after, while there is one
            let next = if g == 4 { step + 1 } else { step };
            c.state = 1;
            c.due = now + LEARNING_STEPS[next];
            c.step = next as u32 + 1;
        } else {
            let fuzz = 1.0 + (fastrand::f64() - 0.5) * 0.1;
            let days = fsrs::interval_days(mem.stability, retention, 365.0);
            let previous = if card.last_review == 0 { 1.0 } else { elapsed.max(1.0) };
            let days = days.min(previous * MAX_GROWTH).max(1.0);
            c.state = 2;
            c.due = now + (days * fuzz * DAY_MS as f64) as i64;
        }
        c
    }
}

#[cfg(test)]
mod tests {
    use super::scheduler::*;
    use super::*;

    #[test]
    fn scheduling() {
        let mut t = 1_000_000_000_000i64;
        let mut card = Card::default();
        card = grade(&card, true, t, 0.9, 1);
        assert_eq!((card.state, card.due), (1, t + LEARNING_STEPS[0]));
        t = card.due;
        card = grade(&card, true, t, 0.9, 1);
        assert_eq!(card.due, t + LEARNING_STEPS[1]);
        for _ in 2..LEARNING_STEPS.len() {
            t = card.due;
            card = grade(&card, true, t, 0.9, 1);
        }
        t = card.due;
        card = grade(&card, true, t, 0.9, 1);
        assert_eq!(card.state, 2);
        let mut last = card.due - t;
        assert!(last >= DAY_MS);
        for _ in 0..4 {
            t = card.due;
            card = grade(&card, true, t, 0.9, 1);
            let iv = card.due - t;
            assert!(iv > last, "intervals should grow: {last} -> {iv}");
            last = iv;
        }
        t = card.due;
        card = grade(&card, false, t, 0.9, 1);
        assert_eq!((card.state, card.lapses, card.due), (1, 1, t + RELEARN_DELAY));
    }

    #[test]
    fn self_grades_move_through_the_learning_steps() {
        let t = 1_000_000_000_000i64;
        let new = Card::default();
        // Good is a right typed answer, Again a wrong one
        assert_eq!(grade_self(&new, 3, t, 0.9).due, grade(&new, true, t, 0.9, 0).due);
        assert_eq!(grade_self(&new, 1, t, 0.9).due, t + RELEARN_DELAY);
        // Hard stays on the step, Easy skips one
        let hard = grade_self(&new, 2, t, 0.9);
        assert_eq!((hard.step, hard.due), (0, t + LEARNING_STEPS[0]));
        let easy = grade_self(&new, 4, t, 0.9);
        assert_eq!((easy.step, easy.due), (2, t + LEARNING_STEPS[1]));
        let good = grade_self(&new, 3, t, 0.9);
        let hard2 = grade_self(&good, 2, t + 10, 0.9);
        assert_eq!((hard2.step, hard2.due), (1, t + 10 + LEARNING_STEPS[0]));
        // Easy on the last step graduates
        let last = Card { state: 1, step: (LEARNING_STEPS.len() - 1) as u32, reps: 4, stability: 3.0, difficulty: 5.0, last_review: t, ..Default::default() };
        assert_eq!(grade_self(&last, 4, t + 3 * DAY_MS, 0.9).state, 2);
        // in review: Hard < Good < Easy
        let rev = Card { state: 2, step: 4, reps: 6, stability: 10.0, difficulty: 5.0, last_review: t, due: t + 10 * DAY_MS, ..Default::default() };
        let at = t + 10 * DAY_MS;
        let iv = |g| (0..20).map(|_| grade_self(&rev, g, at, 0.9).due - at).sum::<i64>();
        // (Good and Easy may both reach the growth cap; the fuzz then decides)
        let (hard, good, easy) = (iv(2), iv(3), iv(4));
        assert!(hard < good && easy * 100 >= good * 95, "{hard} {good} {easy}");
        assert_eq!(grade_self(&rev, 1, at, 0.9).lapses, 1);
    }

    #[test]
    fn roundtrip() {
        let dir = std::env::temp_dir().join(format!("bunpo-test-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("progress.json");
        let mut p = Progress::load(&path);
        p.cards.insert("wa".into(), Card { state: 1, due: 42, ..Default::default() });
        p.settings.furigana = false;
        p.save();
        let q = Progress::load(&path);
        assert_eq!(q.card("wa").due, 42);
        assert!(!q.settings.furigana);
        std::fs::remove_dir_all(dir).ok();
    }
}
