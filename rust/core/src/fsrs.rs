//! FSRS-5 scheduler (https://github.com/open-spaced-repetition), default parameters.
//! Grades: 1 = Again, 2 = Hard, 3 = Good, 4 = Easy.

const W: [f64; 19] = [
    0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046, 1.54575, 0.1192,
    1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898, 0.51655, 0.6621,
];
const DECAY: f64 = -0.5;
pub const DAY_MS: i64 = 86_400_000;

fn factor() -> f64 {
    0.9f64.powf(1.0 / DECAY) - 1.0 // 19/81
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Memory {
    pub stability: f64,
    pub difficulty: f64,
}

pub fn retrievability(elapsed_days: f64, stability: f64) -> f64 {
    (1.0 + factor() * elapsed_days / stability).powf(DECAY)
}

fn init_stability(g: u8) -> f64 {
    W[g as usize - 1].max(0.1)
}

fn init_difficulty(g: u8) -> f64 {
    (W[4] - (W[5] * (g as f64 - 1.0)).exp() + 1.0).clamp(1.0, 10.0)
}

fn next_difficulty(d: f64, g: u8) -> f64 {
    let delta = -W[6] * (g as f64 - 3.0);
    let dp = d + delta * (10.0 - d) / 9.0;
    (W[7] * init_difficulty(4) + (1.0 - W[7]) * dp).clamp(1.0, 10.0)
}

fn recall_stability(d: f64, s: f64, r: f64, g: u8) -> f64 {
    let hard = if g == 2 { W[15] } else { 1.0 };
    let easy = if g == 4 { W[16] } else { 1.0 };
    s * (1.0 + W[8].exp() * (11.0 - d) * s.powf(-W[9]) * ((W[10] * (1.0 - r)).exp() - 1.0) * hard * easy)
}

fn forget_stability(d: f64, s: f64, r: f64) -> f64 {
    let sf = W[11] * d.powf(-W[12]) * ((s + 1.0).powf(W[13]) - 1.0) * (W[14] * (1.0 - r)).exp();
    sf.min(s)
}

fn short_term_stability(s: f64, g: u8) -> f64 {
    s * (W[17] * (g as f64 - 3.0 + W[18])).exp()
}

/// New memory state after a review. `prev` is `None` for the very first review.
pub fn review(prev: Option<Memory>, elapsed_days: f64, grade: u8) -> Memory {
    let Some(prev) = prev else {
        return Memory { stability: init_stability(grade), difficulty: init_difficulty(grade) };
    };
    let d = next_difficulty(prev.difficulty, grade);
    let s = if elapsed_days < 1.0 {
        short_term_stability(prev.stability, grade)
    } else {
        let r = retrievability(elapsed_days, prev.stability);
        if grade == 1 {
            forget_stability(prev.difficulty, prev.stability, r)
        } else {
            recall_stability(prev.difficulty, prev.stability, r, grade)
        }
    };
    Memory { stability: s.clamp(0.05, 36500.0), difficulty: d }
}

/// Interval in days for the desired retention.
pub fn interval_days(stability: f64, retention: f64, max_days: f64) -> f64 {
    let i = stability / factor() * (retention.powf(1.0 / DECAY) - 1.0);
    i.clamp(1.0, max_days)
}
