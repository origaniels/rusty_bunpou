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
}

impl Default for Settings {
    fn default() -> Self {
        Settings { furigana: true, english: true, romaji: true, batch_size: 5, retention: 0.9, notifications: true }
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

#[derive(Debug, Default, Serialize, Deserialize)]
#[serde(default)]
pub struct Progress {
    pub cards: HashMap<String, Card>,
    pub settings: Settings,
    pub log: Vec<LogEntry>,
    #[serde(skip)]
    path: Option<PathBuf>,
}

impl Progress {
    pub fn load(path: &Path) -> Progress {
        let mut p: Progress = std::fs::read_to_string(path)
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default();
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

    pub fn card(&self, id: &str) -> Card {
        self.cards.get(id).cloned().unwrap_or_default()
    }

    pub fn reviews_since(&self, ts: i64) -> usize {
        self.log.iter().filter(|e| e.ts >= ts).count()
    }

    pub fn reset_all(&mut self) {
        self.cards.clear();
        self.log.clear();
        self.save();
    }

    pub fn reset_point(&mut self, id: &str) {
        self.cards.remove(id);
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

    pub fn grade(card: &Card, correct: bool, now: i64, retention: f64, sentence: u64) -> Card {
        let g = if correct { 3 } else { 1 };
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
        if !correct {
            if card.state == 2 {
                c.lapses += 1;
                c.step = RELEARN_FROM_STEP;
            } else {
                c.step = 0;
            }
            c.state = 1;
            c.due = now + RELEARN_DELAY;
        } else if card.state <= 1 && (card.step as usize) < LEARNING_STEPS.len() {
            c.state = 1;
            c.due = now + LEARNING_STEPS[card.step as usize];
            c.step = card.step + 1;
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
