//! Romaji → kana conversion and answer normalization.

use bunpo_core::kana::{kata_to_hira, normalize, romaji_to_hiragana};

fn conv(s: &str) -> String {
    romaji_to_hiragana(s, true)
}

#[test]
fn gojuon_and_dakuten() {
    let cases = [
        ("aiueo", "あいうえお"), ("kakikukeko", "かきくけこ"), ("sashisuseso", "さしすせそ"),
        ("tachitsuteto", "たちつてと"), ("naninuneno", "なにぬねの"), ("hahifuheho", "はひふへほ"),
        ("mamimumemo", "まみむめも"), ("yayuyo", "やゆよ"), ("rarirurero", "らりるれろ"),
        ("wawo", "わを"), ("gagigugego", "がぎぐげご"), ("zajizuzezo", "ざじずぜぞ"),
        ("dadidudedo", "だぢづでど"), ("babibubebo", "ばびぶべぼ"), ("papipupepo", "ぱぴぷぺぽ"),
    ];
    for (r, k) in cases {
        assert_eq!(conv(r), k, "{r}");
    }
}

#[test]
fn alternative_spellings() {
    for (r, k) in [("si", "し"), ("ti", "ち"), ("tu", "つ"), ("hu", "ふ"), ("zi", "じ"), ("la", "ら")] {
        assert_eq!(conv(r), k, "{r}");
    }
}

#[test]
fn youon() {
    for (r, k) in [
        ("kya", "きゃ"), ("kyu", "きゅ"), ("kyo", "きょ"), ("sha", "しゃ"), ("shu", "しゅ"), ("sho", "しょ"),
        ("cha", "ちゃ"), ("chu", "ちゅ"), ("cho", "ちょ"), ("nya", "にゃ"), ("hyaku", "ひゃく"), ("myu", "みゅ"),
        ("ryokou", "りょこう"), ("gyuunyuu", "ぎゅうにゅう"), ("ja", "じゃ"), ("jo", "じょ"), ("jya", "じゃ"),
        ("bya", "びゃ"), ("pyo", "ぴょ"),
    ] {
        assert_eq!(conv(r), k, "{r}");
    }
}

#[test]
fn small_tsu() {
    for (r, k) in [
        ("kitte", "きって"), ("zasshi", "ざっし"), ("ippai", "いっぱい"), ("chotto", "ちょっと"),
        ("matcha", "まっちゃ"), ("kekkon", "けっこん"), ("motte", "もって"), ("issho", "いっしょ"),
    ] {
        assert_eq!(conv(r), k, "{r}");
    }
}

#[test]
fn syllabic_n() {
    for (r, k) in [
        ("hon", "ほん"), ("honn", "ほん"), ("shinbun", "しんぶん"), ("onna", "おんな"), ("konnichiha", "こんにちは"),
        ("kon'ya", "こんや"), ("kin'en", "きんえん"), ("minna", "みんな"), ("sanpo", "さんぽ"),
        ("benkyou", "べんきょう"), ("densha", "でんしゃ"),
    ] {
        assert_eq!(conv(r), k, "{r}");
    }
}

#[test]
fn partial_input_while_typing() {
    assert_eq!(romaji_to_hiragana("k", false), "k");
    assert_eq!(romaji_to_hiragana("ky", false), "ky");
    assert_eq!(romaji_to_hiragana("tabesh", false), "たべsh");
    assert_eq!(romaji_to_hiragana("hon", false), "ほn");
    assert_eq!(romaji_to_hiragana("honn", false), "ほnn");
    assert_eq!(romaji_to_hiragana("honnn", false), "ほんn");
    assert_eq!(romaji_to_hiragana("kit", false), "きt");
}

#[test]
fn kana_and_mixed_input_pass_through() {
    assert_eq!(conv("たべます"), "たべます");
    assert_eq!(conv("食べmasu"), "食べます");
    assert_eq!(conv("カタカナ"), "カタカナ");
    assert_eq!(conv("TABETA"), "たべた");
    assert_eq!(conv("-"), "ー");
}

#[test]
fn normalization() {
    assert_eq!(kata_to_hira("タベマシタ"), "たべました");
    assert_eq!(normalize(" タベタ。 "), "たべた");
    assert_eq!(normalize("tabeta!"), "たべた");
    assert_eq!(normalize("たべ た"), "たべた");
    assert_eq!(normalize("ではない？"), "ではない");
    assert_eq!(normalize("hon"), "ほん");
    assert_eq!(normalize(""), "");
    assert_eq!(normalize("   "), "");
}
