//! App language, and French for the strings built in Rust (the Slint UI has its own .po file).

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum Lang {
    #[default]
    En,
    Fr,
}

impl Lang {
    pub fn from_code(code: &str) -> Lang {
        if code == "fr" { Lang::Fr } else { Lang::En }
    }
    pub fn code(self) -> &'static str {
        match self {
            Lang::En => "en",
            Lang::Fr => "fr",
        }
    }
}

/// English → French for strings assembled in Rust. Unknown strings stay in English.
const FR: &[(&str, &str)] = &[
    // grammatical tags in sentence hints
    ("polite", "poli"),
    ("past", "passé"),
    ("negative", "négatif"),
    // SRS stages
    ("New", "Nouveau"),
    ("Beginner", "Débutant"),
    ("Adept", "Apprenti"),
    ("Seasoned", "Confirmé"),
    ("Expert", "Expert"),
    ("Mastered", "Maîtrisé"),
];

/// `text` in `lang` (see [`FR`]).
pub fn tr(lang: Lang, text: &str) -> &str {
    match lang {
        Lang::En => text,
        Lang::Fr => FR.iter().find(|(en, _)| *en == text).map_or(text, |(_, fr)| fr),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn codes_and_fallback() {
        assert_eq!(Lang::from_code("fr"), Lang::Fr);
        assert_eq!(Lang::from_code("en"), Lang::En);
        assert_eq!(Lang::from_code(""), Lang::En);
        assert_eq!(tr(Lang::Fr, "past"), "passé");
        assert_eq!(tr(Lang::En, "past"), "past");
        assert_eq!(tr(Lang::Fr, "unknown"), "unknown");
    }
}
