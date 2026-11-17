//! Print how one grammar point is scheduled when always answered correctly,
//! and what happens after a mistake. Run: cargo run -p bunpo-core --example simulate
use bunpo_core::fsrs::DAY_MS;
use bunpo_core::store::{scheduler::grade, Card};

fn fmt(ms: i64) -> String {
    let h = ms as f64 / 3_600_000.0;
    if h < 24.0 { format!("{h:.0} h") } else { format!("{:.1} days", ms as f64 / DAY_MS as f64) }
}

fn main() {
    let retention = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(0.9);
    println!("target retention {retention}\n\nreview  result  next review in   level");
    let mut card = Card::default();
    let mut t = 0i64;
    let mut elapsed = 0i64;
    for i in 1..=14 {
        let ok = i != 9; // forget once, at the 9th review
        let next = grade(&card, ok, t, retention, 1);
        println!("{:>4}    {:<6}  {:<15}  {}", i, if ok { "ok" } else { "MISS" }, fmt(next.due - t), next.level_name());
        elapsed += next.due - t;
        t = next.due;
        card = next;
    }
    println!("\ntotal time covered: {}", fmt(elapsed));
}
