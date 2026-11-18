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
    /// Width of the reading; may exceed `w` (it overhangs neighbouring kana).
    pub ruby_w: f32,
    /// Left edge of the reading relative to `x` (negative when it overhangs to the left).
    pub ruby_x: f32,
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
    /// Frame around the cloze's main text line (box in Blank mode); the first line if it wraps.
    pub cloze: Rect,
    /// One frame per line the cloze occupies (a long cloze may wrap).
    pub cloze_rects: Vec<Rect>,
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

struct Piece {
    text: String,
    ruby: String,
    cloze: bool,
}

/// How far a reading may stick out over a neighbour without furigana (per side, in em).
const OVERHANG_EM: f32 = 0.3;

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
            out.push(Piece { text: seg.0.clone(), ruby: seg.1.clone(), cloze: start >= cs && start < ce });
        } else {
            for (k, ch) in seg.0.chars().enumerate() {
                let i = start + k;
                out.push(Piece { text: ch.to_string(), ruby: String::new(), cloze: i >= cs && i < ce });
            }
        }
    }
    out
}

struct Unit {
    items: Vec<(String, String, bool, f32, f32, f32)>, // text, ruby, in_cloze, width, ruby width, ruby x
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
    let ps = pieces(s);
    // a cloze that fits on one line stays together; a longer one may wrap like normal text
    let cloze_w: f32 = ps.iter().filter(|p| p.cloze).map(|p| text_width(&p.text, m.font)).sum();
    // (leave room for one closing punctuation mark that sticks to the cloze)
    let keep_cloze_together = cloze_w + 2.0 * pad + m.font <= max_width;
    let has_ruby = |i: usize| m.furigana && ps.get(i).is_some_and(|p| !p.ruby.is_empty());
    for (i, Piece { text, ruby, cloze }) in ps.iter().enumerate() {
        let (text, ruby, cloze) = (text.clone(), ruby.clone(), *cloze);
        if cloze && mode == ClozeMode::Blank {
            if !blank_added {
                let w = (text_width(typed, m.font) + 2.0 * pad).max(m.font * 3.0).min(max_width);
                units.push(Unit { items: vec![], width: w, is_blank: true, blank_w: w });
                blank_added = true;
            }
            continue;
        }
        let text_w = text_width(&text, m.font);
        let ruby_w = if m.furigana { text_width(&ruby, m.ruby_font) } else { 0.0 };
        // a long reading may overhang neighbours that have no reading of their own
        let room = |j: Option<usize>| match j {
            Some(j) if j < ps.len() && !has_ruby(j) => OVERHANG_EM * m.font,
            _ => 0.0,
        };
        let (left_room, right_room) = (room(i.checked_sub(1)), room(Some(i + 1)));
        let w = text_w.max(ruby_w - left_room - right_room);
        // spread the overhang over both sides, shifting toward the side that has room
        let over = (ruby_w - w).max(0.0);
        let mut left = (over / 2.0).min(left_room);
        let right = (over - left).min(right_room);
        left = over - right;
        let ruby_x = if ruby_w > w { -left } else { (w - ruby_w) / 2.0 };
        let first = text.chars().next().unwrap_or(' ');
        let attach = NO_LINE_START.contains(first) && !units.is_empty();
        // cloze characters in Highlight/Revealed stay together as one unit
        let join_cloze = cloze
            && keep_cloze_together
            && units.last().is_some_and(|u| !u.is_blank && u.items.last().is_some_and(|it| it.2));
        if attach || join_cloze {
            let u = units.last_mut().unwrap();
            u.items.push((text, ruby, cloze, w, ruby_w, ruby_x));
            u.width += w;
        } else {
            units.push(Unit { items: vec![(text, ruby, cloze, w, ruby_w, ruby_x)], width: w, is_blank: false, blank_w: 0.0 });
        }
    }

    // 2) place units, wrapping lines
    let framed = mode != ClozeMode::Highlight;
    let p = if framed { pad } else { 0.0 };
    let mut out = Layout { main_h, ruby_h, ..Default::default() };
    let (mut x, mut y) = (0.0f32, 0.0f32);
    // cloze frame: 0 = not reached, 1 = open, 2 = closed
    let mut frame = 0u8;
    // per line: (y, min x, max x)
    let mut segs: Vec<(f32, f32, f32)> = vec![];
    for u in units {
        let has_cloze = u.is_blank || u.items.iter().any(|it| it.2);
        // padding of the cloze frame: both sides if the unit holds the cloze, the closing side
        // if the frame is still open and this unit comes right after it
        let extra = if has_cloze { 2.0 * p } else if frame == 1 { p } else { 0.0 };
        if x > 0.0 && x + u.width + extra > max_width {
            x = 0.0;
            y += line_h + gap;
        }
        if u.is_blank {
            out.cloze = Rect { x, y: y + ruby_h, w: u.blank_w, h: main_h };
            out.cloze_rects.push(out.cloze);
            x += u.blank_w;
        }
        for (text, ruby, in_cloze, w, ruby_w, ruby_x) in u.items {
            if in_cloze && frame == 0 {
                frame = 1;
                x += p;
            } else if !in_cloze && frame == 1 {
                frame = 2;
                x += p;
            }
            let gy = y + ruby_h;
            if in_cloze {
                match segs.last_mut() {
                    Some(seg) if seg.0 == gy => seg.2 = x + w,
                    _ => segs.push((gy, x, x + w)),
                }
            }
            out.glyphs.push(Glyph { x, y: gy, w, text, ruby, ruby_w, ruby_x, in_cloze });
            x += w;
        }
    }
    if mode != ClozeMode::Blank && !segs.is_empty() {
        let n = segs.len();
        out.cloze_rects = segs
            .iter()
            .enumerate()
            .map(|(k, &(sy, a, b))| {
                let left = if k == 0 { p } else { 0.0 };
                let right = if k == n - 1 { p } else { 0.0 };
                Rect { x: a - left, y: sy, w: b - a + left + right, h: main_h }
            })
            .collect();
        out.cloze = out.cloze_rects[0];
    }
    out.height = y + line_h;
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::content::Content;

    #[test]
    fn readings_never_overlap_and_glyphs_dont_collide() {
        let c = Content::bundled();
        let m = Metrics::new(24.0, true);
        for s in c.points.iter().flat_map(|p| &p.sentences) {
            for mode in [ClozeMode::Highlight, ClozeMode::Revealed, ClozeMode::Blank] {
                let l = layout(s, 330.0, m, mode, "");
                let line = |g: &Glyph| (g.y * 10.0) as i64;
                for (a, b) in l.glyphs.iter().zip(l.glyphs.iter().skip(1)) {
                    if line(a) != line(b) {
                        continue;
                    }
                    assert!(a.x + a.w <= b.x + 0.01, "glyphs overlap in {}", s.ja);
                }
                let rubies: Vec<(f32, f32, i64)> = l
                    .glyphs
                    .iter()
                    .filter(|g| !g.ruby.is_empty())
                    .map(|g| (g.x + g.ruby_x, g.x + g.ruby_x + g.ruby_w, line(g)))
                    .collect();
                for w in rubies.windows(2) {
                    if w[0].2 == w[1].2 {
                        assert!(w[0].1 <= w[1].0 + 0.01, "readings overlap in {}", s.ja);
                    }
                }
            }
        }
    }

    #[test]
    fn short_kanji_with_long_reading_overhangs_kana() {
        let c = Content::bundled();
        // 私 (わたし) between kana: no extra gap, the reading overhangs
        let s = c
            .points
            .iter()
            .flat_map(|p| &p.sentences)
            .find(|s| s.ja.contains("は私の") || s.ja.contains("が私の"))
            .unwrap();
        let l = layout(s, 2000.0, Metrics::new(24.0, true), ClozeMode::Highlight, "");
        let g = l.glyphs.iter().find(|g| g.text == "私").unwrap();
        assert_eq!(g.w, 24.0);
        assert!(g.ruby_w > g.w);
    }

    #[test]
    fn layout_all_sentences() {
        let c = Content::bundled();
        for p in &c.points {
            for s in &p.sentences {
                for mode in [ClozeMode::Highlight, ClozeMode::Blank, ClozeMode::Revealed] {
                    let l = layout(s, 300.0, Metrics::new(24.0, true), mode, "");
                    // every glyph stays inside the width (single over-wide units aside)
                    for g in &l.glyphs {
                        assert!(g.x + g.w <= 300.0 + 0.5, "{} overflows", s.ja);
                    }
                    assert!(l.cloze.w > 0.0, "no cloze rect for {}", s.ja);
                    for r in &l.cloze_rects {
                        assert!(r.x >= -0.5 && r.x + r.w <= 300.0 + 0.5, "frame overflows in {}", s.ja);
                    }
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
