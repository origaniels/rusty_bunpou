//! Romaji → hiragana conversion (IME-like) and answer normalization.

use std::collections::HashMap;
use std::sync::OnceLock;

fn table() -> &'static HashMap<&'static str, &'static str> {
    static T: OnceLock<HashMap<&'static str, &'static str>> = OnceLock::new();
    T.get_or_init(|| {
        let mut m: HashMap<&'static str, &'static str> = HashMap::new();
        let rows: [(&str, [&str; 5]); 14] = [
            ("", ["あ", "い", "う", "え", "お"]),
            ("k", ["か", "き", "く", "け", "こ"]),
            ("g", ["が", "ぎ", "ぐ", "げ", "ご"]),
            ("s", ["さ", "し", "す", "せ", "そ"]),
            ("z", ["ざ", "じ", "ず", "ぜ", "ぞ"]),
            ("t", ["た", "ち", "つ", "て", "と"]),
            ("d", ["だ", "ぢ", "づ", "で", "ど"]),
            ("n", ["な", "に", "ぬ", "ね", "の"]),
            ("h", ["は", "ひ", "ふ", "へ", "ほ"]),
            ("b", ["ば", "び", "ぶ", "べ", "ぼ"]),
            ("p", ["ぱ", "ぴ", "ぷ", "ぺ", "ぽ"]),
            ("m", ["ま", "み", "む", "め", "も"]),
            ("r", ["ら", "り", "る", "れ", "ろ"]),
            ("l", ["ら", "り", "る", "れ", "ろ"]),
        ];
        const VOWELS: [&str; 5] = ["a", "i", "u", "e", "o"];
        for (c, ks) in rows {
            for i in 0..5 {
                m.insert(Box::leak(format!("{c}{}", VOWELS[i]).into_boxed_str()), ks[i]);
            }
        }
        for (k, v) in [
            ("ya", "や"), ("yu", "ゆ"), ("yo", "よ"), ("wa", "わ"), ("wo", "を"), ("wi", "うぃ"), ("we", "うぇ"),
            ("shi", "し"), ("chi", "ち"), ("tsu", "つ"), ("fu", "ふ"), ("ji", "じ"), ("si", "し"), ("ti", "ち"),
            ("tu", "つ"), ("hu", "ふ"), ("zi", "じ"), ("di", "ぢ"), ("du", "づ"), ("n'", "ん"),
            ("xa", "ぁ"), ("xi", "ぃ"), ("xu", "ぅ"), ("xe", "ぇ"), ("xo", "ぉ"), ("xtu", "っ"), ("xtsu", "っ"),
            ("xya", "ゃ"), ("xyu", "ゅ"), ("xyo", "ょ"), ("ltu", "っ"), ("lya", "ゃ"), ("lyu", "ゅ"), ("lyo", "ょ"),
            ("fa", "ふぁ"), ("fi", "ふぃ"), ("fe", "ふぇ"), ("fo", "ふぉ"), ("ja", "じゃ"), ("ju", "じゅ"),
            ("je", "じぇ"), ("jo", "じょ"), ("sha", "しゃ"), ("shu", "しゅ"), ("she", "しぇ"), ("sho", "しょ"),
            ("cha", "ちゃ"), ("chu", "ちゅ"), ("che", "ちぇ"), ("cho", "ちょ"), ("tsa", "つぁ"),
            ("-", "ー"), ("va", "ゔぁ"), ("vi", "ゔぃ"), ("vu", "ゔ"), ("ve", "ゔぇ"), ("vo", "ゔぉ"),
            ("dhi", "でぃ"), ("thi", "てぃ"), ("dyu", "でゅ"),
        ] {
            m.insert(k, v);
        }
        for (c, k) in [
            ("k", "き"), ("g", "ぎ"), ("n", "に"), ("h", "ひ"), ("b", "び"), ("p", "ぴ"), ("m", "み"), ("r", "り"),
            ("s", "し"), ("z", "じ"), ("t", "ち"), ("c", "ち"), ("j", "じ"), ("d", "ぢ"),
        ] {
            for (y, small) in [("ya", "ゃ"), ("yu", "ゅ"), ("yo", "ょ")] {
                let key: &'static str = Box::leak(format!("{c}{y}").into_boxed_str());
                let val: &'static str = Box::leak(format!("{k}{small}").into_boxed_str());
                m.insert(key, val);
            }
        }
        m
    })
}

fn is_consonant(c: char) -> bool {
    c.is_ascii_lowercase() && !"aiueon".contains(c)
}

/// Convert romaji to hiragana. With `final_ == false`, a trailing incomplete chunk
/// ("k", "sh", "n", "nn") is left as romaji so the user can keep typing.
pub fn romaji_to_hiragana(input: &str, final_: bool) -> String {
    let orig: Vec<char> = input.chars().collect();
    let s: Vec<char> = input.chars().map(|c| c.to_ascii_lowercase()).collect();
    let t = table();
    let max_key = 4;
    let mut out = String::new();
    let mut i = 0;
    while i < s.len() {
        let c = s[i];
        if !c.is_ascii_lowercase() && c != '-' && c != '\'' {
            out.push(orig[i]);
            i += 1;
            continue;
        }
        // "tch" (matcha) → っち
        if c == 't' && s.get(i + 1) == Some(&'c') && s.get(i + 2) == Some(&'h') {
            out.push('っ');
            i += 1;
            continue;
        }
        if i + 1 < s.len() && s[i + 1] == c && is_consonant(c) {
            out.push('っ');
            i += 1;
            continue;
        }
        if c == 'n' {
            match s.get(i + 1) {
                None => {
                    out.push(if final_ { 'ん' } else { orig[i] });
                    i += 1;
                    continue;
                }
                Some('n') => {
                    match s.get(i + 2) {
                        None => {
                            if final_ { out.push('ん') } else { out.extend(&orig[i..i + 2]) }
                            i += 2;
                        }
                        Some(a) if "aiueoy".contains(*a) => { out.push('ん'); i += 1; }
                        Some(_) => { out.push('ん'); i += 2; }
                    }
                    continue;
                }
                Some(n) if !"aiueoy'".contains(*n) => {
                    out.push('ん');
                    i += 1;
                    continue;
                }
                _ => {}
            }
        }
        let mut matched = false;
        for len in (1..=max_key.min(s.len() - i)).rev() {
            let key: String = s[i..i + len].iter().collect();
            if let Some(v) = t.get(key.as_str()) {
                out.push_str(v);
                i += len;
                matched = true;
                break;
            }
        }
        if !matched {
            out.extend(&orig[i..]);
            break;
        }
    }
    out
}

pub fn kata_to_hira(s: &str) -> String {
    s.chars()
        .map(|c| if ('ァ'..='ヶ').contains(&c) { char::from_u32(c as u32 - 0x60).unwrap_or(c) } else { c })
        .collect()
}

const STRIP: &str = " 　。、．，！？!?.,・「」『』()（）~〜\t\n";

/// Hiragana, katakana or the long-vowel mark.
pub fn is_kana(c: char) -> bool {
    matches!(c, '\u{3041}'..='\u{309F}' | '\u{30A0}'..='\u{30FF}')
}

pub fn normalize(s: &str) -> String {
    kata_to_hira(&romaji_to_hiragana(s.trim(), true)).chars().filter(|c| !STRIP.contains(*c)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn romaji() {
        for (r, k) in [
            ("konnichiha", "こんにちは"), ("tabetekudasai", "たべてください"), ("itta", "いった"),
            ("kyou", "きょう"), ("shinbun", "しんぶん"), ("zasshi", "ざっし"),
            ("benkyoushinakereba", "べんきょうしなければ"), ("hon'ya", "ほんや"), ("onna", "おんな"),
            ("jidousha", "じどうしゃ"), ("chotto", "ちょっと"), ("nn", "ん"), ("ikitakatta", "いきたかった"),
            ("wo", "を"), ("kanojo", "かのじょ"), ("minna", "みんな"),
        ] {
            assert_eq!(romaji_to_hiragana(r, true), k, "{r}");
        }
        assert_eq!(romaji_to_hiragana("kon", false), "こn");
        assert_eq!(romaji_to_hiragana("konn", false), "こnn");
        assert_eq!(romaji_to_hiragana("こnni", false), "こんに");
        assert_eq!(romaji_to_hiragana("tabesh", false), "たべsh");
        assert_eq!(romaji_to_hiragana("カタカナ", false), "カタカナ");
        assert_eq!(normalize(" タベタ。 "), "たべた");
    }
}
