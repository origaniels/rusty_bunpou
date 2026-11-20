//! Quiz sessions: each point is graded on its first attempt; misses come back at the end
//! with another sentence (practice only) until answered correctly.

use crate::content::{Content, GrammarPoint, Sentence};
use crate::kana;
use crate::store::{scheduler, Progress};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};

pub const LESSON_EXAMPLES: usize = 4;

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum Verdict {
    Correct,
    Wrong,
}

pub use crate::clock::now_ms;

/// A session is saved with the progress (see `Progress::paused`) so it can be resumed;
/// the answer being typed is not.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(default)]
pub struct Session {
    pub lesson: bool,
    pub total: usize,
    pub done: usize,
    pub correct_first_try: usize,
    queue: VecDeque<String>,
    graded: HashSet<String>,
    seen: HashSet<u64>,
    /// The sentence each point was asked with in this session: a missed point comes back with the
    /// same sentence (the next session picks another one).
    chosen: HashMap<String, u64>,
    pub point: Option<String>,
    pub sentence: Option<u64>,
    /// What the user typed into the field (may be romaji).
    #[serde(skip)]
    pub raw: String,
    /// Kana preview of `raw` (shown inside the blank).
    #[serde(skip)]
    pub input: String,
    #[serde(skip)]
    pub verdict: Option<Verdict>,
    #[serde(skip)]
    pub last_answer: String,
    /// The answer was wrong and is being edited: a typo fix (a right answer then counts as right).
    #[serde(skip)]
    pub fixing_typo: bool,
    /// Retry was used after a wrong answer: the item counts as missed whatever comes next.
    #[serde(skip)]
    pub missed: bool,
    /// "Almost" hint shown for the last answer (not graded: try again).
    #[serde(skip)]
    pub nudge: Option<crate::hints::Nudge>,
    /// The free retry of this item was used.
    #[serde(skip)]
    pub nudged: bool,
}

pub fn find_sentence<'a>(p: &'a GrammarPoint, id: u64) -> Option<&'a Sentence> {
    p.sentences.iter().find(|s| s.id == id)
}

impl Session {
    pub fn new(content: &Content, progress: &Progress, ids: Vec<String>, lesson: bool) -> Session {
        let mut seen = HashSet::new();
        if lesson {
            for id in &ids {
                if let Some(p) = content.get(id) {
                    seen.extend(p.sentences.iter().take(LESSON_EXAMPLES).map(|s| s.id));
                }
            }
        }
        let mut s = Session {
            lesson,
            total: ids.len(),
            done: 0,
            correct_first_try: 0,
            queue: ids.into(),
            graded: HashSet::new(),
            seen,
            chosen: HashMap::new(),
            point: None,
            sentence: None,
            raw: String::new(),
            input: String::new(),
            verdict: None,
            last_answer: String::new(),
            fixing_typo: false,
            missed: false,
            nudge: None,
            nudged: false,
        };
        s.advance(content, progress);
        s
    }

    pub fn finished(&self) -> bool {
        self.point.is_none()
    }

    /// Points answered at least once (graded), out of `total`.
    pub fn answered(&self) -> usize {
        self.graded.len()
    }

    /// Items still to answer correctly, the current one included.
    pub fn remaining(&self) -> usize {
        self.queue.len() + usize::from(self.point.is_some())
    }

    /// The current item was already graded (missed earlier): this is practice, not graded again.
    pub fn practising(&self) -> bool {
        self.point.as_ref().is_some_and(|p| self.graded.contains(p))
    }

    /// A saved session can be resumed if all its points still exist (content may have changed).
    pub fn resumable(&self, content: &Content) -> bool {
        !self.finished()
            && self.current(content).is_some()
            && self.queue.iter().all(|id| content.get(id).is_some())
    }

    /// Leaving the quiz: an answer already checked counts, as if Next had been pressed.
    pub fn commit_pending(&mut self, content: &Content, progress: &mut Progress) {
        if self.verdict.is_some() {
            self.next(content, progress);
        }
    }

    fn advance(&mut self, content: &Content, progress: &Progress) {
        self.input.clear();
        self.raw.clear();
        self.verdict = None;
        self.fixing_typo = false;
        self.missed = false;
        self.nudge = None;
        self.nudged = false;
        let Some(id) = self.queue.pop_front() else {
            self.point = None;
            self.sentence = None;
            return;
        };
        let p = content.get(&id).expect("known point");
        if let Some(&sid) = self.chosen.get(&id) {
            if find_sentence(p, sid).is_some() {
                self.point = Some(id);
                self.sentence = Some(sid);
                return;
            }
        }
        let last = progress.card(&id).last_sentence;
        let pool: Vec<&Sentence> =
            p.sentences.iter().filter(|s| s.id != last && !self.seen.contains(&s.id)).collect();
        let pick = if pool.is_empty() {
            &p.sentences[fastrand::usize(..p.sentences.len())]
        } else {
            pool[fastrand::usize(..pool.len())]
        };
        self.seen.insert(pick.id);
        self.chosen.insert(id.clone(), pick.id);
        self.point = Some(id);
        self.sentence = Some(pick.id);
    }

    pub fn current<'a>(&self, content: &'a Content) -> Option<(&'a GrammarPoint, &'a Sentence)> {
        let p = content.get(self.point.as_deref()?)?;
        let s = find_sentence(p, self.sentence?)?;
        Some((p, s))
    }

    pub fn on_input(&mut self, raw: &str, romaji: bool) {
        self.on_input_composing(raw, raw, romaji);
    }

    /// `field` is the text in the answer field, `full` the same with the keyboard's composition
    /// (not confirmed yet) inserted: the blank and the check use `full`.
    pub fn on_input_composing(&mut self, field: &str, full: &str, romaji: bool) {
        self.raw = field.to_string();
        self.input = if romaji { kana::romaji_to_hiragana(full, false) } else { full.to_string() };
    }

    /// The user edits a wrong answer: back to answering, as a typo fix. Returns true if it switched.
    pub fn edit_after_wrong(&mut self) -> bool {
        if self.verdict == Some(Verdict::Wrong) {
            self.verdict = None;
            self.fixing_typo = true;
            return true;
        }
        false
    }

    /// Check the answer; returns false if there was nothing to check. An "almost" answer sets
    /// `nudge` instead of a verdict (once per item).
    pub fn submit(&mut self, content: &Content) -> bool {
        if self.verdict.is_some() {
            return false;
        }
        let Some((_, s)) = self.current(content) else { return false };
        let norm = kana::normalize(&self.input);
        if norm.is_empty() {
            return false;
        }
        self.last_answer = self.input.clone();
        let ok = s.answers.iter().any(|a| kana::normalize(a) == norm);
        self.nudge = None;
        if !ok && !self.nudged {
            // almost right: say what to look at and let them try again, once per item
            if let Some(n) = crate::hints::nudge(s, &self.input) {
                self.nudge = Some(n);
                self.nudged = true;
                return true;
            }
        }
        self.verdict = Some(if ok { Verdict::Correct } else { Verdict::Wrong });
        true
    }

    /// SRS-style "I made a typo".
    pub fn override_correct(&mut self) {
        if self.verdict == Some(Verdict::Wrong) {
            self.verdict = Some(Verdict::Correct);
        }
    }

    /// Try again after a wrong answer; the item still counts as missed.
    pub fn retry(&mut self) {
        if self.verdict == Some(Verdict::Wrong) {
            self.missed = true;
        }
        self.fixing_typo = false;
        self.verdict = None;
        self.input.clear();
        self.raw.clear();
    }

    /// Commit the verdict (grading on first attempt) and move to the next item.
    pub fn next(&mut self, content: &Content, progress: &mut Progress) {
        let (Some(pid), Some(sid), Some(v)) = (self.point.clone(), self.sentence, self.verdict) else { return };
        let correct = v == Verdict::Correct && !self.missed;
        if self.graded.insert(pid.clone()) {
            let now = now_ms();
            let card = scheduler::grade(&progress.card(&pid), correct, now, progress.settings.retention, sid);
            progress.cards.insert(pid.clone(), card);
            progress.log.push(crate::store::LogEntry {
                point: pid.clone(),
                sentence: sid,
                ts: now,
                grade: if correct { 3 } else { 1 },
                answer: self.last_answer.clone(),
            });
            progress.save();
            if correct {
                self.correct_first_try += 1;
            }
        }
        if correct {
            self.done += 1;
        } else {
            self.queue.push_back(pid);
        }
        self.advance(content, progress);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_answer_accepts_itself() {
        let c = Content::bundled();
        let mut n = 0;
        for p in &c.points {
            for s in &p.sentences {
                let norm: Vec<String> = s.answers.iter().map(|a| kana::normalize(a)).collect();
                assert!(norm.contains(&kana::normalize(&s.answer())), "{}", s.ja);
                let rebuilt: String = s.furi.iter().map(|g| g.0.as_str()).collect();
                assert_eq!(rebuilt, s.ja);
                n += 1;
            }
        }
        assert!(n > 500);
    }

    #[test]
    fn a_missed_point_comes_back_with_the_same_sentence_then_another_next_time() {
        let c = Content::bundled();
        let mut prog = Progress::in_memory();
        let ids: Vec<String> = c.points.iter().filter(|p| p.sentences.len() > 3).take(3).map(|p| p.id.clone()).collect();
        for _ in 0..20 {
            let mut s = Session::new(&c, &prog, ids.clone(), false);
            let (first, sid) = (s.point.clone().unwrap(), s.sentence.unwrap());
            s.on_input("xxx", false);
            assert!(s.submit(&c));
            s.next(&c, &mut prog);
            // answer the others until the missed one is back
            while s.point.as_ref() != Some(&first) {
                let a = s.current(&c).unwrap().1.answer();
                s.on_input(&a, false);
                s.submit(&c);
                s.next(&c, &mut prog);
            }
            assert_eq!(s.sentence, Some(sid), "same sentence within the session");
            // a later session: another sentence for that point
            let s2 = Session::new(&c, &prog, vec![first.clone()], false);
            assert_ne!(s2.sentence, Some(sid), "another sentence next time");
        }
    }

    #[test]
    fn lesson_flow() {
        let c = Content::bundled();
        let mut prog = Progress::in_memory();
        let ids: Vec<String> = c.points.iter().take(3).map(|p| p.id.clone()).collect();
        let mut s = Session::new(&c, &prog, ids, true);
        // first item wrong, then everything right
        let mut first = true;
        let mut steps = 0;
        while !s.finished() {
            let (p, sent) = s.current(&c).unwrap();
            assert!(p.sentences.iter().take(LESSON_EXAMPLES).all(|x| x.id != sent.id || p.sentences.len() <= LESSON_EXAMPLES));
            let ans = if first { "xxx".to_string() } else { sent.answer() };
            first = false;
            s.on_input(&ans, false);
            assert!(s.submit(&c));
            s.next(&c, &mut prog);
            steps += 1;
            assert!(steps < 10);
        }
        assert_eq!(steps, 4);
        assert_eq!(s.correct_first_try, 2);
        assert_eq!(prog.cards.len(), 3);
        assert_eq!(prog.log.len(), 3);
    }
}
