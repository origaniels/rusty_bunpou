//! Vocabulary: the JLPT words (data/build/vocab.json), learned with two flashcards each and
//! graded by the learner, like Anki: "forward" shows the word and asks its meaning, "reverse"
//! shows the meaning and asks the word. Both are scheduled like grammar points (`grade_self`).
//! Each word has a few example sentences from Tatoeba, the word marked in them.

use crate::content::Sentence;
use crate::i18n::Lang;
use crate::store::{scheduler, Card, LogEntry, Progress};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};

pub const BUNDLED: &str = include_str!("../../../data/build/vocab.json");

#[derive(Debug, Clone, Deserialize)]
pub struct Word {
    /// "expression|reading" as in the word lists; never changes (progress is keyed by it)
    pub id: String,
    pub level: String,
    pub word: String,
    /// in kana
    pub reading: String,
    /// other spellings ("脚" for 足)
    #[serde(default)]
    pub also: String,
    /// what can follow the word ("する" for 結婚)
    #[serde(default)]
    pub suffix: String,
    pub en: String,
    #[serde(default)]
    pub fr: String,
    /// examples: (index in `Vocab::sentences`, first char of the word in it, char after it)
    #[serde(default)]
    pub ex: Vec<(usize, usize, usize)>,
}

impl Word {
    /// Meaning in `lang` (English when there is no French one).
    pub fn meaning(&self, lang: Lang) -> &str {
        if lang == Lang::Fr && !self.fr.is_empty() { &self.fr } else { &self.en }
    }

    /// The word with its reading over each kanji (none for a word in kana).
    pub fn ruby(&self) -> Vec<(String, String)> {
        if self.word == self.reading {
            return vec![(self.word.clone(), String::new())];
        }
        crate::content::ruby_split(&self.word, &self.reading)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Side {
    /// the word is shown, its meaning is asked
    Forward,
    /// the meaning is shown, the word is asked
    Reverse,
}

pub fn card_id(word: &str, side: Side) -> String {
    format!("{word}#{}", if side == Side::Forward { "f" } else { "r" })
}

pub fn split_card_id(id: &str) -> Option<(&str, Side)> {
    match id.rsplit_once('#')? {
        (w, "f") => Some((w, Side::Forward)),
        (w, "r") => Some((w, Side::Reverse)),
        _ => None,
    }
}

pub struct Vocab {
    pub words: Vec<Word>,
    pub source: String,
    pub source_fr: String,
    /// the example sentences, shared by the words using them
    pub sentences: Vec<Sentence>,
    index: HashMap<String, usize>,
}

impl Vocab {
    pub fn parse(json: &str) -> Result<Vocab, serde_json::Error> {
        #[derive(Deserialize)]
        struct File {
            source: String,
            #[serde(default)]
            source_fr: String,
            #[serde(default)]
            sentences: Vec<Sentence>,
            words: Vec<Word>,
        }
        let mut f: File = serde_json::from_str(json)?;
        // an example out of range (a file edited by hand) is left out rather than shown wrong
        for w in &mut f.words {
            let sentences = &f.sentences;
            w.ex.retain(|&(i, a, b)| sentences.get(i).is_some_and(|s| a < b && b <= s.ja.chars().count()));
        }
        let index = f.words.iter().enumerate().map(|(i, w)| (w.id.clone(), i)).collect();
        Ok(Vocab { words: f.words, source: f.source, source_fr: f.source_fr, sentences: f.sentences, index })
    }

    /// The `n`th example of `word`, the word marked (as a grammar example marks its point).
    pub fn example(&self, word: &Word, n: usize) -> Option<Sentence> {
        let &(i, a, b) = word.ex.get(n)?;
        let mut s = self.sentences.get(i)?.clone();
        s.cloze = [a, b];
        Some(s)
    }

    pub fn bundled() -> Vocab {
        Self::parse(BUNDLED).expect("bundled vocab.json is valid")
    }

    pub fn get(&self, id: &str) -> Option<&Word> {
        self.index.get(id).map(|&i| &self.words[i])
    }

    /// The word a card is about.
    pub fn word_of(&self, card: &str) -> Option<(&Word, Side)> {
        let (w, side) = split_card_id(card)?;
        Some((self.get(w)?, side))
    }

    /// Credits line for the word lists.
    pub fn source_in(&self, lang: Lang) -> &str {
        if lang == Lang::Fr && !self.source_fr.is_empty() { &self.source_fr } else { &self.source }
    }

    /// Words not learned yet, from `start_level` up, in the order they are taught.
    pub fn new_words(&self, progress: &Progress) -> Vec<&Word> {
        let levels = &crate::lessons::LEVELS;
        let start = levels.iter().position(|l| *l == progress.settings.start_level).unwrap_or(0);
        self.words
            .iter()
            .filter(|w| levels.iter().position(|l| *l == w.level).is_some_and(|i| i >= start))
            .filter(|w| !learned(progress, &w.id))
            .collect()
    }

    /// Cards due now, the most overdue first.
    pub fn due_cards(&self, progress: &Progress, now: i64) -> Vec<String> {
        let mut v: Vec<(i64, &String)> = progress
            .vocab
            .iter()
            .filter(|(id, c)| c.state > 0 && c.due <= now && self.word_of(id).is_some())
            .map(|(id, c)| (c.due, id))
            .collect();
        v.sort();
        v.into_iter().map(|(_, id)| id.clone()).collect()
    }

    /// Words learned, by level (N5 … N1).
    pub fn learned_per_level(&self, progress: &Progress) -> [usize; 5] {
        let mut out = [0; 5];
        for w in &self.words {
            if learned(progress, &w.id) {
                if let Some(i) = crate::lessons::LEVELS.iter().position(|l| *l == w.level) {
                    out[i] += 1;
                }
            }
        }
        out
    }
}

/// A word counts as learned once its first card was answered.
pub fn learned(progress: &Progress, word: &str) -> bool {
    progress.vocab.get(&card_id(word, Side::Forward)).is_some_and(|c| !c.is_new())
}

/// Words first learned today (the day starting at the chosen hour), against the daily goal.
pub fn learned_today(progress: &Progress, now: i64) -> usize {
    let day = |ms| crate::clock::study_day(ms, progress.settings.day_start);
    let today = day(now);
    progress
        .vocab
        .iter()
        .filter(|(id, c)| id.ends_with("#f") && c.learned_at > 0 && day(c.learned_at) == today)
        .count()
}

/// Size of the next word lesson: what is left of today's goal, or a whole goal once it is
/// reached (extra). Returns (size, extra).
pub fn next_lesson_size(progress: &Progress, now: i64) -> (usize, bool) {
    let goal = progress.settings.vocab_goal.max(1) as usize;
    let left = goal.saturating_sub(learned_today(progress, now));
    if left > 0 { (left, false) } else { (goal, true) }
}

/// A run of flashcards: the cards of a word lesson, or the reviews due. Each card is graded on
/// its first answer; a card answered "Again" comes back at the end until it is answered otherwise
/// (practice, not graded again), like a missed grammar point.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct VocabSession {
    pub lesson: bool,
    pub queue: VecDeque<String>,
    pub total: usize,
    /// cards cleared (answered anything but Again)
    pub done: usize,
    /// cards already graded in this session
    pub graded: HashSet<String>,
    /// first answers that were "Again"
    pub missed: usize,
    /// the answer side of the current card is shown
    pub revealed: bool,
}

impl VocabSession {
    pub fn new(cards: Vec<String>, lesson: bool) -> VocabSession {
        VocabSession { lesson, total: cards.len(), queue: cards.into(), ..Default::default() }
    }

    /// A lesson on `words`: every word's forward card, then every reverse card.
    pub fn lesson(words: &[&Word]) -> VocabSession {
        let cards = [Side::Forward, Side::Reverse]
            .iter()
            .flat_map(|&side| words.iter().map(move |w| card_id(&w.id, side)))
            .collect();
        Self::new(cards, true)
    }

    pub fn current(&self) -> Option<&str> {
        self.queue.front().map(|s| s.as_str())
    }

    pub fn finished(&self) -> bool {
        self.queue.is_empty()
    }

    /// Whether the current card's answer will be graded (its first answer in the session).
    pub fn grading(&self) -> bool {
        self.current().is_some_and(|c| !self.graded.contains(c))
    }

    /// Answer the current card with a self-grade (1 Again … 4 Easy).
    pub fn answer(&mut self, progress: &mut Progress, grade: u8, now: i64) {
        let Some(id) = self.queue.pop_front() else { return };
        self.revealed = false;
        if self.graded.insert(id.clone()) {
            let card = progress.vocab.get(&id).cloned().unwrap_or_default();
            let next = scheduler::grade_self(&card, grade, now, progress.settings.retention);
            progress.vocab.insert(id.clone(), next);
            progress.vocab_log.push(LogEntry { point: id.clone(), sentence: 0, ts: now, grade, answer: String::new() });
            if grade == 1 {
                self.missed += 1;
            }
            progress.save();
        }
        if grade == 1 {
            self.queue.push_back(id);
        } else {
            self.done += 1;
        }
    }
}

/// When a card would be due next for each grade (Again … Easy), without the random fuzz's effect
/// mattering much: for the labels under the grade buttons.
pub fn next_due(card: &Card, now: i64, retention: f64) -> [i64; 4] {
    [1, 2, 3, 4].map(|g| scheduler::grade_self(card, g, now, retention).due)
}

/// A delay as the grade buttons show it: "1 h", "4 h", "3 d", "2 mo", "1 y".
pub fn short_delay(ms: i64, lang: Lang) -> String {
    let min = (ms as f64 / 60_000.0).round() as i64;
    let hours = ms as f64 / 3_600_000.0;
    let days = hours / 24.0;
    let fr = lang == Lang::Fr;
    match () {
        _ if min < 60 => format!("{} min", min.max(1)),
        _ if hours < 23.5 => format!("{} h", hours.round() as i64),
        _ if days < 30.0 => format!("{} {}", days.round() as i64, if fr { "j" } else { "d" }),
        _ if days < 365.0 => format!("{} {}", (days / 30.0).round() as i64, if fr { "mois" } else { "mo" }),
        _ => format!("{:.1} {}", days / 365.0, if fr { "an" } else { "y" }).replace(".0 ", " "),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const DAY: i64 = 86_400_000;

    #[test]
    fn the_bundled_words_load_with_readings_on_their_kanji() {
        let v = Vocab::bundled();
        assert!(v.words.len() > 7000);
        let w = v.get("会う|あう").unwrap();
        assert_eq!(w.ruby(), vec![("会".to_string(), "あ".to_string()), ("う".to_string(), String::new())]);
        assert_eq!(w.meaning(Lang::Fr), "rencontrer, voir (quelqu'un)");
        // word parts (お～, ～円) are for a kanji section, not here
        assert!(v.words.iter().all(|w| !w.word.contains('～')));
        let kana = v.get("あそこ|あそこ").unwrap();
        assert_eq!(kana.ruby(), vec![("あそこ".to_string(), String::new())]);
        // N3 and up have no French yet: English
        let n3 = v.words.iter().find(|w| w.level == "N3").unwrap();
        assert_eq!(n3.meaning(Lang::Fr), n3.en);
    }

    #[test]
    fn examples_mark_the_word() {
        let v = Vocab::bundled();
        let w = v.get("会う|あう").unwrap();
        assert!(!w.ex.is_empty());
        for n in 0..w.ex.len() {
            let s = v.example(w, n).unwrap();
            let marked: String = s.ja.chars().skip(s.cloze[0]).take(s.cloze[1] - s.cloze[0]).collect();
            assert!(marked.starts_with('会') || marked.starts_with('あ'), "{marked} in {}", s.ja);
            assert!(s.attribution(Lang::En).starts_with("Tatoeba #"));
        }
        assert!(v.example(w, w.ex.len()).is_none());
    }

    #[test]
    fn examples_out_of_range_are_left_out() {
        let json = r#"{"source":"s","sentences":[{"id":1,"ja":"猫だ。","en":"A cat.","furi":[["猫","ねこ"],["だ。",""]]}],
            "words":[{"id":"猫|ねこ","level":"N5","word":"猫","reading":"ねこ","en":"cat","ex":[[0,0,1],[0,2,9],[3,0,1],[0,1,1]]}]}"#;
        let v = Vocab::parse(json).unwrap();
        let w = &v.words[0];
        assert_eq!(w.ex, [(0, 0, 1)]);
        assert_eq!(v.example(w, 0).unwrap().cloze, [0, 1]);
    }

    #[test]
    fn card_ids_name_the_word_and_the_side() {
        let id = card_id("会う|あう", Side::Reverse);
        assert_eq!(id, "会う|あう#r");
        assert_eq!(split_card_id(&id), Some(("会う|あう", Side::Reverse)));
        assert_eq!(split_card_id("会う|あう"), None);
    }

    #[test]
    fn a_lesson_asks_every_word_both_ways_and_missed_cards_come_back() {
        let v = Vocab::bundled();
        let mut p = Progress::in_memory();
        let words: Vec<&Word> = v.new_words(&p).into_iter().take(2).collect();
        let mut s = VocabSession::lesson(&words);
        assert_eq!(s.total, 4);
        assert_eq!(s.current(), Some(card_id(&words[0].id, Side::Forward).as_str()));
        let t = 1_700_000_000_000;
        s.answer(&mut p, 1, t); // Again: back at the end
        s.answer(&mut p, 3, t);
        s.answer(&mut p, 4, t);
        s.answer(&mut p, 2, t);
        assert_eq!((s.done, s.missed, s.queue.len()), (3, 1, 1));
        assert!(!s.grading(), "the missed card is practice now");
        s.answer(&mut p, 1, t + 1); // still Again: not graded again, back once more
        s.answer(&mut p, 3, t + 2);
        assert!(s.finished());
        assert_eq!(s.done, 4);
        assert_eq!(p.vocab_log.len(), 4, "each card graded once");
        assert!(words.iter().all(|w| learned(&p, &w.id)));
        assert_eq!(learned_today(&p, t), 2);
        assert!(v.new_words(&p).iter().all(|w| w.id != words[0].id));
        // the missed card is due again in an hour, the others later
        let first = &p.vocab[&card_id(&words[0].id, Side::Forward)];
        assert_eq!(first.due, t + scheduler::RELEARN_DELAY);
        assert!(v.due_cards(&p, t + DAY).len() == 4);
        assert!(v.due_cards(&p, t).is_empty());
    }

    #[test]
    fn lessons_start_at_the_chosen_level_and_follow_the_daily_goal() {
        let v = Vocab::bundled();
        let mut p = Progress::in_memory();
        p.settings.start_level = "N3".into();
        assert!(v.new_words(&p).iter().all(|w| w.level != "N5" && w.level != "N4"));
        p.settings.vocab_goal = 10;
        let t = 1_700_000_000_000;
        assert_eq!(next_lesson_size(&p, t), (10, false));
        let words: Vec<&Word> = v.new_words(&p).into_iter().take(4).collect();
        let mut s = VocabSession::lesson(&words);
        while !s.finished() {
            s.answer(&mut p, 3, t);
        }
        assert_eq!(next_lesson_size(&p, t), (6, false));
    }

    #[test]
    fn delays_are_short_and_readable() {
        let h = 3_600_000;
        assert_eq!(short_delay(h, Lang::En), "1 h");
        assert_eq!(short_delay(4 * h, Lang::En), "4 h");
        assert_eq!(short_delay(3 * DAY, Lang::En), "3 d");
        assert_eq!(short_delay(3 * DAY, Lang::Fr), "3 j");
        assert_eq!(short_delay(65 * DAY, Lang::En), "2 mo");
        assert_eq!(short_delay(365 * DAY, Lang::En), "1 y");
        assert_eq!(short_delay(500 * DAY, Lang::Fr), "1.4 an");
    }
}

