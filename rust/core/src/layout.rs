//! Furigana sentence layout: computes absolute positions for every character so the UI
//! toolkit only has to draw them. Lines wrap anywhere except before closing punctuation.

use crate::content::Sentence;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ClozeMode {
    /// Whole sentence, cloze part highlighted (lessons, detail pages).
    Highlight,
    /// Empty box of at least `min_width` for typed text.
    Blank,
    /// Answer shown inside a frame (after checking).
    Revealed,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Glyph {
    pub x: f32,
    /// Top of the main text line (furigana is drawn above it, inside the ruby band).
    pub y: f32,
    pub w: f32,
    pub text: String,
    pub ruby: String,
    pub in_cloze: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct Rect {
    pub x: f32,
    pub y: f32,
    pub w: f32,
    pub h: f32,
}

#[derive(Debug, Clone, Default)]
pub struct Layout {
    pub glyphs: Vec<Glyph>,
    /// Frame around the cloze's main text line (box in Blank mode).
    pub cloze: Rect,
    pub height: f32,
    pub main_h: f32,
    pub ruby_h: f32,
}

#[derive(Debug, Clone, Copy)]
pub struct Metrics {
    pub font: f32,
    pub ruby_font: f32,
    pub furigana: bool,
}

impl Metrics {
    pub fn new(font: f32, furigana: bool) -> Metrics {
        Metrics { font, ruby_font: font * 0.45, furigana }
    }
    pub fn main_h(&self) -> f32 {
        self.font * 1.4
    }
    pub fn ruby_h(&self) -> f32 {
        if self.furigana { self.ruby_font * 1.4 } else { 0.0 }
    }
}

/// Advance width of a character in em. CJK characters (kanji, kana, full-width punctuation)
/// are square in Japanese fonts; ASCII and half-width forms are roughly half.
pub fn char_em(c: char) -> f32 {
    match c as u32 {
        0x20..=0x7e => {
            if c.is_ascii_digit() || c.is_ascii_lowercase() { 0.58 } else if c.is_ascii_uppercase() { 0.68 } else { 0.4 }
        }
        0xff61..=0xff9f => 0.5,
        _ => 1.0,
    }
}

pub fn text_width(s: &str, font: f32) -> f32 {
    s.chars().map(char_em).sum::<f32>() * font
}

const NO_LINE_START: &str = "。、！？!?」』）)・ー…ゃゅょっぁぃぅぇぉャュョッァィゥェォ";

enum Piece {
    Ch { text: String, ruby: String, cloze: bool },
}

/// Per-character pieces (ruby segments stay whole), each tagged with whether it's in the blank.
fn pieces(s: &Sentence) -> Vec<Piece> {
    let mut out = Vec::new();
    let mut pos = 0usize;
    let [cs, ce] = s.cloze;
    for seg in &s.furi {
        let start = pos;
        let n = seg.0.chars().count();
        pos += n;
        if !seg.1.is_empty() {
            out.push(Piece::Ch { text: seg.0.clone(), ruby: seg.1.clone(), cloze: start >= cs && start < ce });
        } else {
            for (k, ch) in seg.0.chars().enumerate() {
                let i = start + k;
                out.push(Piece::Ch { text: ch.to_string(), ruby: String::new(), cloze: i >= cs && i < ce });
            }
        }
    }
    out
}

struct Unit {
    items: Vec<(String, String, bool, f32)>, // text, ruby, in_cloze, width
    width: f32,
    is_blank: bool,
    /// width of the blank box itself (excluding attached punctuation)
    blank_w: f32,
}

pub fn layout(s: &Sentence, max_width: f32, m: Metrics, mode: ClozeMode, typed: &str) -> Layout {
    let main_h = m.main_h();
    let ruby_h = m.ruby_h();
    let line_h = ruby_h + main_h;
    let gap = m.font * 0.25;
    let pad = m.font * 0.15; // horizontal padding inside the cloze frame

    // 1) group into unbreakable units
    let mut units: Vec<Unit> = Vec::new();
    let mut blank_added = false;
    for Piece::Ch { text, ruby, cloze } in pieces(s) {
        if cloze && mode == ClozeMode::Blank {
            if !blank_added {
                let w = (text_width(typed, m.font) + 2.0 * pad).max(m.font * 3.0);
                units.push(Unit { items: vec![], width: w, is_blank: true, blank_w: w });
                blank_added = true;
            }
            continue;
        }
        let w = text_width(&text, m.font).max(if m.furigana { text_width(&ruby, m.ruby_font) } else { 0.0 });
        let first = text.chars().next().unwrap_or(' ');
        let attach = NO_LINE_START.contains(first) && !units.is_empty();
        // cloze characters in Highlight/Revealed stay together as one unit
        let join_cloze = cloze
            && units.last().is_some_and(|u| !u.is_blank && u.items.last().is_some_and(|it| it.2));
        if attach || join_cloze {
            let u = units.last_mut().unwrap();
            u.items.push((text, ruby, cloze, w));
            u.width += w;
        } else {
            units.push(Unit { items: vec![(text, ruby, cloze, w)], width: w, is_blank: false, blank_w: 0.0 });
        }
    }

    // 2) place units, wrapping lines
    let framed = mode != ClozeMode::Highlight;
    let p = if framed { pad } else { 0.0 };
    let mut out = Layout { main_h, ruby_h, ..Default::default() };
    let (mut x, mut y) = (0.0f32, 0.0f32);
    // cloze frame: 0 = not reached, 1 = open, 2 = closed
    let mut frame = 0u8;
    let (mut cmin, mut cmax) = (0.0f32, 0.0f32);
    for u in units {
        let has_cloze = u.is_blank || u.items.iter().any(|it| it.2);
        let extra = if has_cloze { 2.0 * p } else { 0.0 };
        if x > 0.0 && x + u.width + extra > max_width {
            x = 0.0;
            y += line_h + gap;
        }
        if u.is_blank {
            out.cloze = Rect { x, y: y + ruby_h, w: u.blank_w, h: main_h };
            x += u.blank_w;
        }
        for (text, ruby, in_cloze, w) in u.items {
            if in_cloze && frame == 0 {
                frame = 1;
                x += p;
                cmin = x;
                out.cloze.y = y + ruby_h;
            } else if !in_cloze && frame == 1 {
                frame = 2;
                x += p;
            }
            out.glyphs.push(Glyph { x, y: y + ruby_h, w, text, ruby, in_cloze });
            x += w;
            if in_cloze {
                cmax = x;
            }
        }
    }
    if mode != ClozeMode::Blank && frame > 0 {
        out.cloze = Rect { x: cmin - p, y: out.cloze.y, w: cmax - cmin + 2.0 * p, h: main_h };
    }
    out.height = y + line_h;
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::Content;

    #[test]
    fn layout_all_sentences() {
        let c = Content::bundled();
        for p in &c.points {
            for s in &p.sentences {
                for mode in [ClozeMode::Highlight, ClozeMode::Blank, ClozeMode::Revealed] {
                    let l = layout(s, 300.0, Metrics::new(24.0, true), mode, "");
                    // every glyph stays inside the width (single over-wide units aside)
                    for g in &l.glyphs {
                        assert!(g.x + g.w <= 300.0 + 30.0, "{} overflows", s.ja);
                    }
                    assert!(l.cloze.w > 0.0, "no cloze rect for {}", s.ja);
                    // rebuilt text matches (blank mode drops the cloze chars)
                    let text: String = l.glyphs.iter().map(|g| g.text.as_str()).collect();
                    if mode == ClozeMode::Blank {
                        let mut expect: String = s.ja.chars().take(s.cloze[0]).collect();
                        expect.extend(s.ja.chars().skip(s.cloze[1]));
                        assert_eq!(text, expect);
                    } else {
                        assert_eq!(text, s.ja);
                    }
                    // no line starts with closing punctuation
                    for g in &l.glyphs {
                        let starts_line = g.x < 0.5 && !(mode == ClozeMode::Blank && l.cloze.x < 0.5 && l.cloze.y == g.y);
                        if starts_line {
                            assert!(!"。、！？".contains(g.text.chars().next().unwrap()), "{}", s.ja);
                        }
                    }
                }
            }
        }
    }
}
