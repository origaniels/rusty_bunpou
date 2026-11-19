//! "Almost" hints for a wrong answer: a particle missing, extra or swapped, or the right word in
//! another form. They give one free retry and never say what the answer is.

use crate::content::Sentence;
use crate::kana::normalize;

/// Particles a learner may drop, add or swap.
pub const PARTICLES: [&str; 13] = ["は", "が", "を", "に", "で", "と", "へ", "も", "の", "や", "から", "まで", "より"];

/// An aspect of a verb or adjective form.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Aspect {
    /// past or not
    Tense,
    /// ます/です or plain
    Politeness,
    /// て-form or not
    TeForm,
    /// positive or negative
    Negative,
}

pub const ASPECTS: [Aspect; 4] = [Aspect::Tense, Aspect::Politeness, Aspect::TeForm, Aspect::Negative];

#[derive(Debug, Clone, PartialEq)]
pub enum Nudge {
    /// the rest is right, a particle is missing, extra or not the right one
    Particle,
    /// the right word in another form; which aspects differ (empty: some other form)
    Form(Vec<Aspect>),
    /// another grammar point that fits here too: possible, but not the one being practised
    Nuance,
}

/// The hint for a wrong answer (`typed`, kana), if it is "almost" right.
pub fn nudge(s: &Sentence, typed: &str) -> Option<Nudge> {
    let t = normalize(typed);
    if t.is_empty() || s.answers.iter().any(|a| normalize(a) == t) {
        return None;
    }
    if s.alts.iter().any(|a| normalize(a) == t) {
        return Some(Nudge::Nuance);
    }
    if particle_slip(s, &t) {
        return Some(Nudge::Particle);
    }
    form_slip(s, &t).map(Nudge::Form)
}

/// The answer with one particle dropped, swapped for another, or one particle added, is what was
/// typed. Only when the answer has more than particles: for a particle point, another particle is
/// just a wrong answer.
fn particle_slip(s: &Sentence, t: &str) -> bool {
    if s.parts.is_empty() {
        return false;
    }
    let kana: Vec<String> = s.parts.iter().map(|(k, _)| normalize(k)).collect();
    let is_p: Vec<bool> = s.parts.iter().map(|(_, kind)| kind == "p").collect();
    if is_p.iter().all(|p| *p) {
        return false;
    }
    let joined = |v: &[&str]| v.concat();
    let parts: Vec<&str> = kana.iter().map(|k| k.as_str()).collect();
    for i in 0..parts.len() {
        if !is_p[i] {
            continue;
        }
        let mut v = parts.clone();
        v.remove(i);
        if joined(&v) == t {
            return true;
        }
        for q in PARTICLES {
            if q != parts[i] {
                let mut v = parts.clone();
                v[i] = q;
                if joined(&v) == t {
                    return true;
                }
            }
        }
    }
    for j in 0..=parts.len() {
        for q in PARTICLES {
            let mut v = parts.clone();
            v.insert(j, q);
            if joined(&v) == t {
                return true;
            }
        }
    }
    false
}

/// The typed answer starts like the word in the hint (its stem: 話す → 話 / はな) but has another
/// form. Returns the aspects that differ from the expected form.
fn form_slip(s: &Sentence, t: &str) -> Option<Vec<Aspect>> {
    let hint = s.hint.as_ref()?;
    let word = hint.split(" · ").next()?;
    // "話す（はなす）" or just "いる"
    let (written, reading) = match word.split_once('（') {
        Some((w, r)) => (w, r.trim_end_matches('）')),
        None => (word, word),
    };
    let stems: Vec<String> = [written, reading].iter().filter_map(|w| stem(&normalize(w))).collect();
    if !stems.iter().any(|st| t.starts_with(st.as_str())) {
        return None;
    }
    let expected = s.answers.iter().map(|a| normalize(a)).find(|a| a.chars().all(crate::kana::is_kana))?;
    let (e, f) = (features(&expected), features(t));
    Some(ASPECTS.iter().enumerate().filter(|(i, _)| e[*i] != f[*i]).map(|(_, a)| *a).collect())
}

/// What stays the same whatever the form: 話す → 話, 食べる → 食べ, 勉強する → 勉強, 高い → 高.
/// None if nothing would be left (する, 来る, 見る written in kana: み is too short to tell).
fn stem(word: &str) -> Option<String> {
    let chars: Vec<char> = word.chars().collect();
    let cut = if word.ends_with("する") || word.ends_with("くる") || word.ends_with("来る") { 2 } else { 1 };
    if chars.len() <= cut {
        return None;
    }
    let st: String = chars[..chars.len() - cut].iter().collect();
    // a single kana is too weak a sign that it's the same word
    if st.chars().count() == 1 && st.chars().all(crate::kana::is_kana) {
        return None;
    }
    Some(st)
}

/// [past, polite, て-form, negative] of a kana answer.
fn features(k: &str) -> [bool; 4] {
    let past = ["ました", "でした", "かった"].iter().any(|e| k.contains(e)) || k.ends_with('た') || k.ends_with('だ');
    let polite = ["ます", "まし", "ませ", "です", "でし"].iter().any(|e| k.contains(e));
    let te = k.ends_with('て') || k.ends_with('で');
    let negative = ["ない", "なかっ", "ません", "ず"].iter().any(|e| k.contains(e));
    [past, polite, te, negative]
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sentence(answers: &[&str], hint: Option<&str>, parts: &[(&str, &str)]) -> Sentence {
        Sentence {
            answers: answers.iter().map(|a| a.to_string()).collect(),
            hint: hint.map(|h| h.to_string()),
            parts: parts.iter().map(|(k, p)| (k.to_string(), p.to_string())).collect(),
            ..Default::default()
        }
    }

    #[test]
    fn particles() {
        let s = sentence(&["には行きません", "にはいきません"], None, &[("に", "p"), ("は", "p"), ("いき", "v"), ("ませ", "v"), ("ん", "v")]);
        assert_eq!(nudge(&s, "にいきません"), Some(Nudge::Particle), "missing");
        assert_eq!(nudge(&s, "ではいきません"), Some(Nudge::Particle), "swapped");
        assert_eq!(nudge(&s, "にはをいきません"), Some(Nudge::Particle), "extra");
        assert_eq!(nudge(&s, "にはいきます"), None, "not a particle slip (and no hint for the form)");
        // a particle point: another particle is just wrong
        let s = sentence(&["には"], None, &[("に", "p"), ("は", "p")]);
        assert_eq!(nudge(&s, "には"), None);
        assert_eq!(nudge(&s, "では"), None);
        // でした is not the particle で
        let s = sentence(&["元気でした", "げんきでした"], None, &[("げんき", "o"), ("でし", "v"), ("た", "v")]);
        assert_eq!(nudge(&s, "げんきした"), None);
    }

    #[test]
    fn another_point_that_fits() {
        let mut s = sentence(&["から"], None, &[]);
        s.alts = vec!["ので".into()];
        assert_eq!(nudge(&s, "ので"), Some(Nudge::Nuance));
        assert_eq!(nudge(&s, "node"), Some(Nudge::Nuance), "romaji too");
        assert_eq!(nudge(&s, "けど"), None);
    }

    #[test]
    fn forms() {
        let s = sentence(&["話しました", "はなしました"], Some("話す（はなす） · polite, past"), &[("はなし", "v"), ("まし", "v"), ("た", "v")]);
        assert_eq!(nudge(&s, "はなします"), Some(Nudge::Form(vec![Aspect::Tense])));
        assert_eq!(nudge(&s, "hanashita"), Some(Nudge::Form(vec![Aspect::Politeness])));
        assert_eq!(nudge(&s, "はなして"), Some(Nudge::Form(vec![Aspect::Tense, Aspect::Politeness, Aspect::TeForm])));
        assert_eq!(nudge(&s, "はなしませんでした"), Some(Nudge::Form(vec![Aspect::Negative])));
        assert_eq!(nudge(&s, "話した"), Some(Nudge::Form(vec![Aspect::Politeness])), "typed in kanji");
        assert_eq!(nudge(&s, "たべました"), None, "another word");
        assert_eq!(nudge(&s, "はなしました"), None, "right");
        let s = sentence(&["勉強して", "べんきょうして"], Some("勉強する（べんきょうする）"), &[("べんきょう", "o"), ("し", "v"), ("て", "v")]);
        assert_eq!(nudge(&s, "べんきょうした"), Some(Nudge::Form(vec![Aspect::Tense, Aspect::TeForm])));
        // 見る: み alone is too short to tell it's the same word
        let s = sentence(&["見た", "みた"], Some("見る（みる） · past"), &[("み", "v"), ("た", "v")]);
        assert_eq!(nudge(&s, "みず"), None);
    }
}
