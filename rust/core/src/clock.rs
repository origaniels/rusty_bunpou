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

const DAY_MS: i64 = 86_400_000;

/// The phone's offset from UTC at `at_ms` (time zone and summer time), in milliseconds.
pub fn utc_offset_ms(at_ms: i64) -> i64 {
    #[cfg(unix)]
    {
        let t = at_ms.div_euclid(1000) as libc::time_t;
        let mut tm: libc::tm = unsafe { std::mem::zeroed() };
        // localtime_r is thread-safe and reads the system time zone (TZ, or Android's setting)
        if !unsafe { libc::localtime_r(&t, &mut tm) }.is_null() {
            return tm.tm_gmtoff as i64 * 1000;
        }
    }
    let _ = at_ms;
    0
}

/// Local calendar day number (days since 1970-01-01 in the phone's time zone).
pub fn local_day(ms: i64) -> i64 {
    (ms + utc_offset_ms(ms)).div_euclid(DAY_MS)
}

/// The study day of `ms` when the day starts at `start_hour` (0 = midnight; 4 = a review at
/// 1 AM still counts for the day before). Daily goal, streak, activity and forecast use it.
pub fn study_day(ms: i64, start_hour: u32) -> i64 {
    local_day(ms - start_hour.min(23) as i64 * 3_600_000)
}

/// (year, month, day) of a day number (Howard Hinnant's civil-from-days).
pub fn civil_date(day: i64) -> (i64, u32, u32) {
    let z = day + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32;
    (yoe + era * 400 + if m <= 2 { 1 } else { 0 }, m, d)
}

/// Local date as YYYY-MM-DD.
pub fn date_string(ms: i64) -> String {
    let (y, m, d) = civil_date(local_day(ms));
    format!("{y:04}-{m:02}-{d:02}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn civil_dates() {
        assert_eq!(civil_date(0), (1970, 1, 1));
        assert_eq!(civil_date(-1), (1969, 12, 31));
        assert_eq!(civil_date(11_016), (2000, 2, 29));
        assert_eq!(civil_date(20_775), (2026, 11, 18));
    }

    #[test]
    fn local_day_follows_the_offset() {
        let noon_utc = 20_775 * DAY_MS + DAY_MS / 2;
        // whatever the test machine's zone, a local day is within a day of the UTC one
        assert!((local_day(noon_utc) - 20_775).abs() <= 1);
        assert_eq!(local_day(noon_utc), (noon_utc + utc_offset_ms(noon_utc)).div_euclid(DAY_MS));
    }

    #[test]
    fn a_study_day_starts_at_the_chosen_hour() {
        let noon_utc = 20_775 * DAY_MS + DAY_MS / 2;
        let day = local_day(noon_utc);
        // the first hour of that local day, found by walking back an hour at a time
        let mut m = noon_utc;
        while local_day(m - 3_600_000) == day {
            m -= 3_600_000;
        }
        let one_am = m + 3_600_000;
        assert_eq!(study_day(one_am, 0), day);
        assert_eq!(study_day(one_am, 4), day - 1, "1 AM is still the day before");
        assert_eq!(study_day(m + 5 * 3_600_000, 4), day);
        assert_eq!(study_day(noon_utc, 0), local_day(noon_utc));
    }

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
