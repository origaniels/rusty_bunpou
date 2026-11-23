//! Vocabulary: the bundled words, their cards, sessions and daily goal, at their edges.

use bunpo_core::i18n::Lang;
use bunpo_core::store::{Card, Progress};
use bunpo_core::vocab::{self, card_id, learned, next_lesson_size, short_delay, split_card_id, Side, Vocab, VocabSession, Word};

const HOUR: i64 = 3_600_000;
const DAY: i64 = 24 * HOUR;
/// a fixed time: 2026-11-23 12:00 UTC
const T: i64 = 1_795_435_200_000;

fn vocab() -> Vocab {
    Vocab::bundled()
}

fn learn(p: &mut Progress, words: &[&Word], grade: u8, now: i64) {
    let mut s = VocabSession::lesson(words);
    while !s.finished() {
        s.answer(p, grade, now);
    }
}

#[test]
fn every_word_has_readings_that_rebuild_it() {
    let v = vocab();
    for w in &v.words {
        let ruby = w.ruby();
        let text: String = ruby.iter().map(|(t, _)| t.as_str()).collect();
        assert_eq!(text, w.word, "{}", w.id);
        // kana carry no reading; every kanji run does
        for (t, r) in &ruby {
            if t.chars().all(|c| bunpo_core::kana::is_kana(c) || "～ー・".contains(c)) {
                assert!(r.is_empty(), "{}: {t} read {r}", w.id);
            }
        }
    }
}

#[test]
fn ids_are_unique_and_every_card_names_a_word() {
    let v = vocab();
    let mut ids: Vec<&str> = v.words.iter().map(|w| w.id.as_str()).collect();
    ids.sort();
    ids.dedup();
    assert_eq!(ids.len(), v.words.len());
    for w in v.words.iter().take(50) {
        for side in [Side::Forward, Side::Reverse] {
            let (found, s) = v.word_of(&card_id(&w.id, side)).unwrap();
            assert_eq!((found.id.as_str(), s), (w.id.as_str(), side));
        }
    }
}

#[test]
fn odd_card_ids_are_refused() {
    for id in ["", "#", "会う|あう", "会う|あう#x", "会う|あう#fr"] {
        assert_eq!(split_card_id(id), None, "{id:?}");
    }
    assert!(vocab().word_of("no such word#f").is_none());
    // a word id may itself hold a '#': only the last one separates the side
    assert_eq!(split_card_id("a#b#r"), Some(("a#b", Side::Reverse)));
}

#[test]
fn notes_and_other_spellings_come_through() {
    let v = vocab();
    let marriage = v.get("結婚|けっこん (する)").unwrap();
    assert_eq!((marriage.word.as_str(), marriage.suffix.as_str()), ("結婚", "する"));
    let foot = v.get("足; 脚|あし").unwrap();
    assert_eq!((foot.word.as_str(), foot.also.as_str()), ("足", "脚"));
    assert_eq!(foot.meaning(Lang::Fr), "pied ; jambe");
}

#[test]
fn french_covers_n5_and_n4_and_english_the_rest() {
    let v = vocab();
    for w in &v.words {
        match w.level.as_str() {
            "N5" | "N4" => assert!(!w.fr.is_empty(), "{} has no French", w.id),
            _ => assert_eq!(w.meaning(Lang::Fr), w.en),
        }
        assert_eq!(w.meaning(Lang::En), w.en);
    }
    assert!(v.source_in(Lang::Fr).contains("écrits pour cette appli"));
    assert!(v.source_in(Lang::En).contains("CC BY"));
}

#[test]
fn new_words_go_level_by_level_from_the_start_level() {
    let v = vocab();
    let mut p = Progress::in_memory();
    let all = v.new_words(&p);
    assert_eq!(all.len(), v.words.len());
    let levels: Vec<&str> = all.iter().map(|w| w.level.as_str()).collect();
    let first_n4 = levels.iter().position(|l| *l == "N4").unwrap();
    assert!(levels[..first_n4].iter().all(|l| *l == "N5"));
    p.settings.start_level = "N1".into();
    assert!(v.new_words(&p).iter().all(|w| w.level == "N1"));
    // an unknown level in old settings: from N5
    p.settings.start_level = "N9".into();
    assert_eq!(v.new_words(&p).len(), v.words.len());
}

#[test]
fn due_cards_leave_out_new_cards_future_cards_and_words_no_longer_listed() {
    let v = vocab();
    let mut p = Progress::in_memory();
    let w = &v.words[0];
    p.vocab.insert(card_id(&w.id, Side::Forward), Card { state: 1, due: T - 10, ..Default::default() });
    p.vocab.insert(card_id(&w.id, Side::Reverse), Card { state: 1, due: T - 20, ..Default::default() });
    p.vocab.insert(card_id(&v.words[1].id, Side::Forward), Card { state: 1, due: T + 10, ..Default::default() });
    p.vocab.insert(card_id(&v.words[2].id, Side::Forward), Card::default());
    p.vocab.insert("gone|ない#f".into(), Card { state: 2, due: T - 99, ..Default::default() });
    let due = v.due_cards(&p, T);
    assert_eq!(due, [card_id(&w.id, Side::Reverse), card_id(&w.id, Side::Forward)], "most overdue first");
}

#[test]
fn learned_counts_per_level_and_only_after_a_first_answer() {
    let v = vocab();
    let mut p = Progress::in_memory();
    assert_eq!(v.learned_per_level(&p), [0; 5]);
    let n5: Vec<&Word> = v.words.iter().filter(|w| w.level == "N5").take(3).collect();
    let n3: Vec<&Word> = v.words.iter().filter(|w| w.level == "N3").take(2).collect();
    learn(&mut p, &n5, 3, T);
    learn(&mut p, &n3, 4, T);
    assert_eq!(v.learned_per_level(&p), [3, 0, 2, 0, 0]);
    // a card that exists but was never answered isn't learned
    p.vocab.insert(card_id(&v.words[100].id, Side::Forward), Card::default());
    assert!(!learned(&p, &v.words[100].id));
}

#[test]
fn todays_words_follow_the_hour_the_day_starts_at() {
    let v = vocab();
    let mut p = Progress::in_memory();
    p.settings.day_start = 4;
    // learned at 2 AM local time: still "yesterday" for a day starting at 4
    let local_midnight = T - bunpo_core::clock::utc_offset_ms(T) - (T - bunpo_core::clock::utc_offset_ms(T)).rem_euclid(DAY);
    let two_am = local_midnight + DAY + 2 * HOUR - bunpo_core::clock::utc_offset_ms(local_midnight + DAY);
    let words: Vec<&Word> = v.words.iter().take(2).collect();
    learn(&mut p, &words, 3, two_am);
    assert_eq!(vocab::learned_today(&p, two_am + HOUR), 2, "same study day at 3 AM");
    assert_eq!(vocab::learned_today(&p, two_am + 3 * HOUR), 0, "a new day at 5 AM");
}

#[test]
fn the_daily_goal_sizes_lessons() {
    let v = vocab();
    let mut p = Progress::in_memory();
    p.settings.vocab_goal = 0; // nonsense in a file: one word at least
    assert_eq!(next_lesson_size(&p, T), (1, false));
    p.settings.vocab_goal = 5;
    let words: Vec<&Word> = v.words.iter().take(5).collect();
    learn(&mut p, &words, 3, T);
    assert_eq!(next_lesson_size(&p, T), (5, true), "goal reached: an extra lesson of a whole goal");
    assert_eq!(next_lesson_size(&p, T + 2 * DAY), (5, false), "a new day");
}

#[test]
fn every_grade_but_again_clears_a_card() {
    let v = vocab();
    let mut p = Progress::in_memory();
    let words: Vec<&Word> = v.words.iter().take(2).collect();
    let mut s = VocabSession::lesson(&words);
    for g in [2, 3, 4, 3] {
        assert!(s.grading());
        s.answer(&mut p, g, T);
    }
    assert!(s.finished() && !s.grading());
    assert_eq!((s.done, s.missed, s.total), (4, 0, 4));
    // nothing left: answering does nothing
    s.answer(&mut p, 1, T);
    assert_eq!((s.done, p.vocab_log.len()), (4, 4));
    // the log keeps each grade
    let grades: Vec<u8> = p.vocab_log.iter().map(|l| l.grade).collect();
    assert_eq!(grades, [2, 3, 4, 3]);
}

#[test]
fn an_empty_session_is_finished_at_once() {
    let s = VocabSession::new(vec![], false);
    assert!(s.finished() && s.current().is_none() && !s.grading());
}

#[test]
fn reviews_move_cards_on_and_again_brings_them_back_soon() {
    let v = vocab();
    let mut p = Progress::in_memory();
    let words: Vec<&Word> = v.words.iter().take(1).collect();
    learn(&mut p, &words, 3, T);
    let due = v.due_cards(&p, T + 5 * HOUR);
    assert_eq!(due.len(), 2);
    let mut s = VocabSession::new(due, false);
    let first = s.current().unwrap().to_string();
    s.answer(&mut p, 1, T + 5 * HOUR);
    s.answer(&mut p, 3, T + 5 * HOUR);
    assert_eq!(p.vocab[&first].due, T + 5 * HOUR + bunpo_core::store::scheduler::RELEARN_DELAY);
    assert_eq!(p.vocab[&first].step, 0, "back to the first step");
    assert!(v.due_cards(&p, T + 6 * HOUR + 60_000).contains(&first));
}

#[test]
fn the_grade_buttons_say_when_the_card_comes_back() {
    let new = Card::default();
    let due = vocab::next_due(&new, T, 0.9);
    let delays: Vec<String> = due.iter().map(|d| short_delay(d - T, Lang::En)).collect();
    assert_eq!(delays, ["1 h", "3 h", "4 h", "8 h"]);
    // a card in review: days, longer for easier grades
    let rev = Card { state: 2, step: 4, reps: 6, stability: 5.0, difficulty: 5.0, last_review: T - 3 * DAY, due: T, ..Default::default() };
    let due = vocab::next_due(&rev, T, 0.9);
    assert!(due[0] < due[1] && due[1] < due[2], "{due:?}");
    assert!(short_delay(due[2] - T, Lang::Fr).ends_with(" j"));
}

#[test]
fn delays_round_at_their_boundaries() {
    let min = 60_000;
    let cases = [
        (0, "1 min"),
        (59 * min, "59 min"),
        (HOUR, "1 h"),
        (23 * HOUR, "23 h"),
        (DAY, "1 d"),
        (29 * DAY, "29 d"),
        (30 * DAY, "1 mo"),
        (364 * DAY, "12 mo"),
        (365 * DAY, "1 y"),
        (730 * DAY, "2 y"),
    ];
    for (ms, want) in cases {
        assert_eq!(short_delay(ms, Lang::En), want, "{ms}");
    }
    assert_eq!(short_delay(60 * DAY, Lang::Fr), "2 mois");
    assert_eq!(short_delay(730 * DAY, Lang::Fr), "2 an");
}
