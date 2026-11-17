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
