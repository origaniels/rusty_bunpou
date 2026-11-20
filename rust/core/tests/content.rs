//! Integrity checks on the bundled content (catches pipeline regressions).

use bunpo_core::content::Content;
use bunpo_core::kana::normalize;
use std::collections::HashSet;

fn is_kanji(c: char) -> bool {
    ('\u{3400}'..='\u{9fff}').contains(&c) || c == '々'
}

fn is_hiragana_reading(s: &str) -> bool {
    s.chars().all(|c| ('\u{3041}'..='\u{309f}').contains(&c) || c == 'ー')
}

#[test]
fn points_are_well_formed() {
    let c = Content::bundled();
    assert!(c.points.len() >= 400, "{} points", c.points.len());
    let mut ids = HashSet::new();
    let mut titles = HashSet::new();
    for (i, p) in c.points.iter().enumerate() {
        assert!(ids.insert(&p.id), "duplicate id {}", p.id);
        assert!(titles.insert(&p.title), "duplicate title {}", p.title);
        assert_eq!(p.order, i, "orders are contiguous");
        assert!(["N5", "N4", "N3", "N2", "N1"].contains(&p.level.as_str()));
        assert!(!p.meaning.is_empty() && !p.structure.is_empty());
        assert!(p.explanation.len() > 60, "explanation too short for {}", p.id);
        let min = if p.level == "N5" { 8 } else { 3 };
        assert!(p.sentences.len() >= min, "{} has only {} sentences", p.id, p.sentences.len());
        assert!(c.get(&p.id).is_some());
    }
}

#[test]
fn sentences_are_well_formed() {
    let c = Content::bundled();
    for p in &c.points {
        let mut seen = HashSet::new();
        for s in &p.sentences {
            let ctx = format!("{} / #{} {}", p.id, s.id, s.ja);
            assert!(seen.insert(s.id), "duplicate sentence {ctx}");
            let n = s.ja.chars().count();
            let [a, b] = s.cloze;
            assert!(a < b && b <= n, "bad cloze {ctx}");
            assert!(b - a < n, "cloze is the whole sentence {ctx}");
            assert!(!s.en.trim().is_empty(), "no translation {ctx}");
            // furigana segments rebuild the sentence and readings are only on kanji segments
            let rebuilt: String = s.furi.iter().map(|g| g.0.as_str()).collect();
            assert_eq!(rebuilt, s.ja, "{ctx}");
            for seg in &s.furi {
                if !seg.1.is_empty() {
                    assert!(seg.0.chars().any(is_kanji), "reading on non-kanji {seg:?} {ctx}");
                    assert!(is_hiragana_reading(&seg.1), "reading not hiragana {seg:?} {ctx}");
                }
            }
            // answers: non-empty, accept the blank itself, no accidental duplicates after normalizing
            assert!(!s.answers.is_empty());
            let norm: Vec<String> = s.answers.iter().map(|x| normalize(x)).collect();
            assert!(norm.iter().all(|x| !x.is_empty()), "{ctx}");
            assert!(norm.contains(&normalize(&s.answer())), "{ctx}");
        }
    }
}

#[test]
fn readings_known_to_be_tricky() {
    let c = Content::bundled();
    let mut checked = 0;
    for s in c.points.iter().flat_map(|p| &p.sentences) {
        for (i, seg) in s.furi.iter().enumerate() {
            let next = s.furi.get(i + 1).map(|g| g.0.as_str()).unwrap_or("");
            match seg.0.as_str() {
                "私" => { assert_eq!(seg.1, "わたし", "{}", s.ja); checked += 1 }
                "日本" => { assert_eq!(seg.1, "にほん", "{}", s.ja); checked += 1 }
                "何時" => { assert_eq!(seg.1, "なんじ", "{}", s.ja); checked += 1 }
                "何" if ["か", "を", "が", "も"].iter().any(|p| next.starts_with(p)) => {
                    assert_eq!(seg.1, "なに", "{}", s.ja);
                    checked += 1
                }
                _ => {}
            }
        }
    }
    assert!(checked > 10);
}

#[test]
fn verb_points_have_dictionary_form_hints() {
    let c = Content::bundled();
    for id in ["te_kudasai", "tai", "nai", "masu", "te_iru", "mae_ni"] {
        let p = c.get(id).unwrap();
        for s in &p.sentences {
            let h = s.hint.as_deref().unwrap_or("");
            assert!(!h.is_empty(), "{id}: {}", s.ja);
        }
    }
}

#[test]
fn fixed_form_points_blank_exactly_that_form() {
    // points whose blank is always the same word (catches e.g. でしたら sneaking into でした)
    let c = Content::bundled();
    for (id, forms) in [
        ("da", &["だ"][..]),
        ("desu", &["です"]),
        ("deshita", &["でした"]),
        ("datta", &["だった"]),
        ("deshou", &["でしょう"]),
        ("node", &["ので"]),
    ] {
        for s in &c.get(id).unwrap().sentences {
            assert!(forms.contains(&s.answer().as_str()), "{id}: blank {:?} in {}", s.answer(), s.ja);
        }
    }
}

#[test]
fn everything_has_french() {
    use bunpo_core::i18n::Lang;
    let c = Content::bundled();
    assert!(!c.source_fr.is_empty());
    for p in &c.points {
        let f = p.fr.as_ref().unwrap_or_else(|| panic!("no French for {}", p.id));
        assert!(!f.meaning.is_empty() && !f.structure.is_empty() && f.explanation.len() > 60, "{}", p.id);
        assert_ne!(p.explanation_in(Lang::Fr), p.explanation, "{}: French falls back to English", p.id);
        for s in &p.sentences {
            assert!(!s.fr.is_empty(), "no French for {} / #{} {}", p.id, s.id, s.ja);
            // the credit line always names the original sentence and, for Tatoeba French, its translation
            let a = s.attribution(Lang::Fr);
            if s.src != "app" {
                assert!(a.starts_with(&format!("Tatoeba #{}", s.id)), "{a}");
                if s.fr_src != "app" {
                    assert!(s.fr_id > 0 && a.contains(&format!("trad. #{}", s.fr_id)), "{a}");
                }
            }
        }
    }
}

#[test]
fn sentences_list_their_words_for_lookups() {
    let c = Content::bundled();
    let all: Vec<_> = c.points.iter().flat_map(|p| &p.sentences).collect();
    let without = all.iter().filter(|s| s.words.is_empty()).count();
    assert!(without * 100 < all.len(), "{without} of {} sentences have no words", all.len());
    for s in &all {
        for w in &s.words {
            assert!(!w.is_empty() && !w.contains(' '), "{:?} in {}", w, s.ja);
        }
    }
}

#[test]
fn almost_hints_on_real_answers() {
    use bunpo_core::hints::{nudge, Nudge};
    let c = Content::bundled();
    let (mut particle, mut form) = (0, 0);
    for s in c.points.iter().flat_map(|p| &p.sentences) {
        for a in &s.answers {
            assert_eq!(nudge(s, a), None, "a right answer is not 'almost': {a} in {}", s.ja);
        }
        let ps = &s.parts;
        if ps.iter().any(|(_, k)| k == "p") && ps.iter().any(|(_, k)| k != "p") {
            let i = ps.iter().position(|(_, k)| k == "p").unwrap();
            let typed: String = ps.iter().enumerate().filter(|(j, _)| *j != i).map(|(_, (k, _))| k.as_str()).collect();
            if s.answers.iter().all(|a| normalize(a) != normalize(&typed)) {
                assert_eq!(nudge(s, &typed), Some(Nudge::Particle), "{typed} for {}", s.ja);
                particle += 1;
            }
        }
        // the right verb, another ending
        let kana = s.answers.iter().map(|a| normalize(a)).find(|a| a.chars().all(bunpo_core::kana::is_kana));
        if let (Some(_), Some(k)) = (&s.hint, kana) {
            let stem: String = k.chars().take(k.chars().count().saturating_sub(1)).collect();
            if matches!(nudge(s, &format!("{stem}ました")), Some(Nudge::Form(_))) {
                form += 1;
            }
        }
    }
    assert!(particle > 100, "only {particle} answers with a particle to drop");
    assert!(form > 300, "only {form} verb answers get a form hint");
}

#[test]
fn another_point_that_fits_gets_a_nuance_hint_that_keeps_the_answer_hidden() {
    use bunpo_core::hints::{nudge, Nudge};
    let c = Content::bundled();
    let mut n = 0;
    for p in &c.points {
        for s in p.sentences.iter().filter(|s| !s.alts.is_empty()) {
            let (en, fr) = p.nuance.as_ref().unwrap_or_else(|| panic!("{} has alternatives but no nuance text", p.id));
            for alt in &s.alts {
                assert!(s.answers.iter().all(|a| normalize(a) != normalize(alt)), "{alt} is also accepted in {}", s.ja);
                assert_eq!(nudge(s, alt), Some(Nudge::Nuance), "{alt} in {}", s.ja);
                n += 1;
            }
            for a in &s.answers {
                assert!(!en.contains(a.as_str()) && !fr.contains(a.as_str()), "the {} hint gives away {a}", p.id);
            }
        }
    }
    assert!(n > 800, "only {n} alternative answers");
}
