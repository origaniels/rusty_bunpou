//! Layout audit: checks what is on screen right now, with the fonts and the window size in use.
//! Used by the headless UI tests and, through [`command`], by the emulator end-to-end tests
//! (where it runs on the real device: real fonts, real screen, real keyboard).
//!
//! An issue is reported when a visible label (button, text, field):
//! - sticks out of the window (left or right; also top/bottom for screens that don't scroll);
//! - says it doesn't fit (`FitText` in the UI sets its accessible description to "clipped" when
//!   its text is wider than the room it got: cut off or running into its neighbours);
//! - is a button smaller than a usable tap target, or overlaps another button;
//! - overlaps another text;
//! - is the answer field or its button, hidden by the on-screen keyboard.

use crate::AppWindow;
use i_slint_backend_testing::{AccessibleRole, ElementHandle, ElementQuery};
use slint::ComponentHandle;

/// Smallest acceptable tap target (logical pixels).
pub const MIN_TAP: f32 = 32.0;

/// Labels of the bottom menu bar buttons: content scrolled under the bar is clipped by it.
const NAV: [&str; 4] = ["Home", "Grammar list", "Stats", "Settings"];

#[derive(Debug, Clone)]
pub struct El {
    pub role: AccessibleRole,
    pub label: String,
    pub clipped: bool,
    pub enabled: bool,
    pub x: f32,
    pub y: f32,
    pub w: f32,
    pub h: f32,
}

impl El {
    fn right(&self) -> f32 {
        self.x + self.w
    }
    fn bottom(&self) -> f32 {
        self.y + self.h
    }
    fn overlap(&self, o: &El) -> f32 {
        let w = self.right().min(o.right()) - self.x.max(o.x);
        let h = self.bottom().min(o.bottom()) - self.y.max(o.y);
        if w > 1.0 && h > 1.0 { w * h } else { 0.0 }
    }
    fn contains(&self, o: &El) -> bool {
        o.x >= self.x - 0.5 && o.right() <= self.right() + 0.5 && o.y >= self.y - 0.5 && o.bottom() <= self.bottom() + 0.5
    }
    fn short(&self) -> String {
        let l: String = self.label.chars().take(40).collect();
        format!("{:?} {l:?} at {:.0},{:.0} {:.0}x{:.0}", self.role, self.x, self.y, self.w, self.h)
    }
}

/// Window size in logical pixels.
pub fn window_size(ui: &AppWindow) -> (f32, f32) {
    let w = ui.window();
    let s = w.size().to_logical(w.scale_factor());
    (s.width, s.height)
}

/// Every element with a label that is drawn (non-zero size, not transparent); when a dialog is
/// open (a group labelled "dialog"), only what is inside it: the rest is covered.
pub fn elements(ui: &AppWindow) -> Vec<El> {
    let all = ElementQuery::from_root(ui).find_all();
    let dialog = all
        .iter()
        .filter(|e| e.accessible_role() == Some(AccessibleRole::Groupbox) && e.accessible_label().is_some_and(|l| l == "dialog"))
        .last()
        .cloned();
    let candidates = match dialog {
        Some(d) => d.query_descendants().find_all(),
        None => all,
    };
    candidates
        .into_iter()
        .filter_map(|e: ElementHandle| {
            let label = e.accessible_label()?.trim().to_string();
            if label.is_empty() {
                return None;
            }
            let (p, s) = (e.absolute_position(), e.size());
            if s.width <= 0.0 || s.height <= 0.0 || e.computed_opacity() <= 0.01 {
                return None;
            }
            Some(El {
                role: e.accessible_role().unwrap_or(AccessibleRole::None),
                clipped: e.accessible_description().is_some_and(|d| d == "clipped"),
                enabled: e.accessible_enabled().unwrap_or(true),
                label,
                x: p.x,
                y: p.y,
                w: s.width,
                h: s.height,
            })
        })
        .collect()
}

#[derive(Debug, Clone, Copy, Default)]
pub struct Options {
    /// Nothing may stick out at the top or bottom either (dialogs, screens that don't scroll).
    pub strict_vertical: bool,
}

/// What is wrong with the screen as it is now (empty: all good).
pub fn audit(ui: &AppWindow, opts: Options) -> Vec<String> {
    let (ww, wh) = window_size(ui);
    let kb = ui.get_kb_height();
    let els = elements(ui);
    let mut issues = vec![];
    // the visible area for content: above the bottom bars (menu bar, answer field) and the keyboard
    let bars_top = els
        .iter()
        .filter(|e| e.role == AccessibleRole::TextInput || (e.role == AccessibleRole::Button && NAV.contains(&e.label.as_str())))
        .map(|e| e.y)
        .fold(wh - kb, f32::min);
    let in_view = |e: &El| e.y >= -0.5 && e.bottom() <= wh + 0.5;
    for e in &els {
        if e.x < -0.5 || e.right() > ww + 0.5 {
            issues.push(format!("off-screen (window {ww:.0} wide): {}", e.short()));
        }
        if opts.strict_vertical && (e.y < -0.5 || e.bottom() > wh - kb + 0.5) {
            issues.push(format!("off-screen (window {wh:.0} high, keyboard {kb:.0}): {}", e.short()));
        }
        if e.clipped && in_view(e) {
            issues.push(format!("text doesn't fit: {}", e.short()));
        }
        if e.role == AccessibleRole::Button && (e.w < MIN_TAP || e.h < MIN_TAP) {
            issues.push(format!("tap target too small: {}", e.short()));
        }
        // the answer field and its button must stay above the keyboard
        if kb > 0.0 && (e.role == AccessibleRole::TextInput) && e.bottom() > wh - kb + 0.5 {
            issues.push(format!("hidden by the keyboard ({kb:.0} high): {}", e.short()));
        }
    }
    let visible = |e: &El| in_view(e) && (e.bottom() <= bars_top + 0.5 || e.y >= bars_top - 0.5);
    let buttons: Vec<&El> = els.iter().filter(|e| e.role == AccessibleRole::Button && visible(e)).collect();
    for (i, a) in buttons.iter().enumerate() {
        for b in &buttons[i + 1..] {
            if a.overlap(b) > 0.0 && !a.contains(b) && !b.contains(a) {
                issues.push(format!("buttons overlap: {} / {}", a.short(), b.short()));
            }
        }
    }
    let texts: Vec<&El> = els.iter().filter(|e| e.role == AccessibleRole::Text && visible(e)).collect();
    for (i, a) in texts.iter().enumerate() {
        for b in &texts[i + 1..] {
            if a.overlap(b) > 2.0 {
                issues.push(format!("texts overlap: {} / {}", a.short(), b.short()));
            }
        }
    }
    issues
}

/// The element labelled `label` to tap: the first one fully on screen, else the first one.
pub fn find<'a>(els: &'a [El], label: &str, ww: f32, wh: f32) -> Option<&'a El> {
    let all: Vec<&El> = els.iter().filter(|e| e.label == label).collect();
    // prefer buttons (the same text may also be a plain text elsewhere)
    let pick = |v: Vec<&'a El>| -> Option<&'a El> {
        v.iter().find(|e| e.x >= 0.0 && e.right() <= ww && e.y >= 0.0 && e.bottom() <= wh).copied().or(v.first().copied())
    };
    let buttons: Vec<&El> = all.iter().copied().filter(|e| e.role != AccessibleRole::Text).collect();
    if buttons.is_empty() { pick(all) } else { pick(buttons) }
}

/// One emulator test command, answered on one line (logged by the caller):
/// - `where <label>`: center of the element in physical pixels (`x y w h`), `offscreen x y`, or `none`;
/// - `audit <name> [strict]`: `ok` or the issues separated by ` | `;
/// - `buttons`: labels of the enabled buttons fully on screen, separated by ` | `;
/// - `texts`: all labels on screen with their kind.
pub fn command(ui: &AppWindow, cmd: &str) -> String {
    let (ww, wh) = window_size(ui);
    let scale = ui.window().scale_factor();
    let (verb, arg) = cmd.trim().split_once(' ').unwrap_or((cmd.trim(), ""));
    let els = elements(ui);
    match verb {
        "where" => match find(&els, arg, ww, wh) {
            Some(e) => {
                let (cx, cy) = ((e.x + e.w / 2.0) * scale, (e.y + e.h / 2.0) * scale);
                let on = e.y >= 0.0 && e.bottom() <= wh - ui.get_kb_height();
                format!("where {} {:.0} {:.0} {:.0} {:.0} {:?}", if on { "on" } else { "offscreen" }, cx, cy, e.w * scale, e.h * scale, arg)
            }
            None => format!("where none {arg:?}"),
        },
        "audit" => {
            let (name, strict) = match arg.strip_suffix(" strict") {
                Some(n) => (n, true),
                None => (arg, false),
            };
            let issues = audit(ui, Options { strict_vertical: strict });
            if issues.is_empty() {
                format!("audit {name} ok")
            } else {
                format!("audit {name} FAIL {}", issues.join(" | "))
            }
        }
        "buttons" => {
            let v: Vec<String> = els
                .iter()
                .filter(|e| e.role == AccessibleRole::Button && e.enabled && e.y >= 0.0 && e.bottom() <= wh - ui.get_kb_height() && e.x >= 0.0 && e.right() <= ww)
                .map(|e| e.label.clone())
                .collect();
            format!("buttons {}", v.join(" | "))
        }
        "texts" => {
            let v: Vec<String> = els.iter().map(|e| format!("{:?}:{}", e.role, e.label)).collect();
            format!("texts {}", v.join(" | "))
        }
        _ => format!("unknown command {cmd:?}"),
    }
}
