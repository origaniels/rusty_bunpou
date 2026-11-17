//! Wall clock with a test offset, so SRS behaviour can be checked by "travelling" in time.
//! The offset is per thread: parallel tests can't disturb each other, and the app (single UI
//! thread) is unaffected unless it calls [`advance`].

use std::cell::Cell;

thread_local! {
    static OFFSET_MS: Cell<i64> = const { Cell::new(0) };
}

/// Current time in milliseconds since the Unix epoch (plus this thread's test offset).
pub fn now_ms() -> i64 {
    let real = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis() as i64)
        .unwrap_or(0);
    real + OFFSET_MS.with(Cell::get)
}

/// Move this thread's clock by `ms`.
pub fn advance(ms: i64) {
    OFFSET_MS.with(|o| o.set(o.get() + ms));
}

pub fn reset() {
    OFFSET_MS.with(|o| o.set(0));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn advance_moves_time() {
        let a = now_ms();
        advance(3_600_000);
        let b = now_ms();
        assert!(b - a >= 3_600_000 && b - a < 3_700_000);
        reset();
        assert!(now_ms() - a < 100_000);
    }
}
