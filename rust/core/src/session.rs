//! Quiz sessions: each point is graded on its first attempt; misses come back at the end
//! with another sentence (practice only) until answered correctly.

use crate::content::{Content, GrammarPoint, Sentence};
use crate::kana;
use crate::store::{scheduler, Progress};
use std::collections::{HashSet, VecDeque};

pub const LESSON_EXAMPLES: usize = 4;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Verdict {
    Correct,
    Wrong,
}

pub fn now_ms() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis() as i64)
        .unwrap_or(0)
}

pub struct Session {
    pub lesson: bool,
    pub total: usize,
    pub done: usize,
    pub correct_first_try: usize,
    queue: VecDeque<String>,
    graded: HashSet<String>,
    seen: HashSet<u64>,
    pub point: Option<String>,
    pub sentence: Option<u64>,
    /// What the user typed into the field (may be romaji).
    pub raw: String,
    /// Kana preview of `raw` (shown inside the blank).
    pub input: String,
    pub verdict: Option<Verdict>,
    pub last_answer: String,
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
            point: None,
            sentence: None,
            raw: String::new(),
            input: String::new(),
            verdict: None,
            last_answer: String::new(),
        };
        s.advance(content, progress);
        s
    }

    pub fn finished(&self) -> bool {
        self.point.is_none()
    }

    fn advance(&mut self, content: &Content, progress: &Progress) {
        self.input.clear();
        self.raw.clear();
        self.verdict = None;
        let Some(id) = self.queue.pop_front() else {
            self.point = None;
            self.sentence = None;
            return;
        };
        let p = content.get(&id).expect("known point");
        let last = progress.card(&id).last_sentence;
        let pool: Vec<&Sentence> =
            p.sentences.iter().filter(|s| s.id != last && !self.seen.contains(&s.id)).collect();
        let pick = if pool.is_empty() {
            &p.sentences[fastrand::usize(..p.sentences.len())]
        } else {
            pool[fastrand::usize(..pool.len())]
        };
        self.seen.insert(pick.id);
        self.point = Some(id);
        self.sentence = Some(pick.id);
    }

    pub fn current<'a>(&self, content: &'a Content) -> Option<(&'a GrammarPoint, &'a Sentence)> {
        let p = content.get(self.point.as_deref()?)?;
        let s = find_sentence(p, self.sentence?)?;
        Some((p, s))
    }

    pub fn on_input(&mut self, raw: &str, romaji: bool) {
        self.raw = raw.to_string();
        self.input = if romaji { kana::romaji_to_hiragana(raw, false) } else { raw.to_string() };
    }

    /// Check the answer; returns false if there was nothing to check.
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
        self.verdict = Some(if ok { Verdict::Correct } else { Verdict::Wrong });
        true
    }

    /// SRS-style "I made a typo".
    pub fn override_correct(&mut self) {
        if self.verdict == Some(Verdict::Wrong) {
            self.verdict = Some(Verdict::Correct);
        }
    }

    pub fn retry(&mut self) {
        self.verdict = None;
        self.input.clear();
        self.raw.clear();
    }

    /// Commit the verdict (grading on first attempt) and move to the next item.
    pub fn next(&mut self, content: &Content, progress: &mut Progress) {
        let (Some(pid), Some(sid), Some(v)) = (self.point.clone(), self.sentence, self.verdict) else { return };
        let correct = v == Verdict::Correct;
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
