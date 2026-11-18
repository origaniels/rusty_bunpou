//! Progress persistence: round trips, corruption, forward compatibility.

use bunpo_core::store::{Card, LogEntry, Progress, Settings};
use std::path::PathBuf;

fn tmp(name: &str) -> PathBuf {
    let d = std::env::temp_dir().join(format!("bunpo-store-{}-{name}", std::process::id()));
    std::fs::create_dir_all(&d).unwrap();
    d.join("progress.json")
}

#[test]
fn missing_file_gives_defaults() {
    let p = Progress::load(&tmp("missing").with_file_name("nope.json"));
    assert!(p.cards.is_empty());
    assert_eq!(p.settings, Settings::default());
}

#[test]
fn corrupt_file_does_not_crash() {
    let path = tmp("corrupt");
    std::fs::write(&path, "{ this is not json").unwrap();
    let p = Progress::load(&path);
    assert!(p.cards.is_empty());
}

#[test]
fn older_files_without_new_fields_still_load() {
    let path = tmp("old");
    std::fs::write(&path, r#"{"cards":{"wa":{"state":2,"stability":5.0,"difficulty":5.0,"due":1,"last_review":0,"reps":3,"lapses":0,"step":2,"last_sentence":7}}}"#).unwrap();
    let p = Progress::load(&path);
    assert_eq!(p.card("wa").reps, 3);
    assert_eq!(p.settings, Settings::default());
    assert!(p.log.is_empty());
}

#[test]
fn save_round_trip_and_no_tmp_left() {
    let path = tmp("roundtrip");
    let mut p = Progress::load(&path);
    p.cards.insert("da".into(), Card { state: 2, stability: 12.5, due: 99, reps: 4, ..Default::default() });
    p.settings.retention = 0.95;
    p.settings.notifications = true;
    p.log.push(LogEntry { point: "da".into(), sentence: 1, ts: 5, grade: 3, answer: "だ".into() });
    p.save();
    assert!(!path.with_extension("tmp").exists());
    let q = Progress::load(&path);
    assert_eq!(q.card("da"), p.card("da"));
    assert_eq!(q.settings, p.settings);
    assert_eq!(q.log.len(), 1);
    assert_eq!(q.reviews_since(5), 1);
    assert_eq!(q.reviews_since(6), 0);
}

#[test]
fn resets() {
    let path = tmp("reset");
    let mut p = Progress::load(&path);
    p.cards.insert("a".into(), Card { state: 1, ..Default::default() });
    p.cards.insert("b".into(), Card { state: 1, ..Default::default() });
    p.reset_point("a");
    assert!(Progress::load(&path).card("a").is_new());
    assert!(!Progress::load(&path).card("b").is_new());
    p.settings.furigana = false;
    p.reset_all();
    let q = Progress::load(&path);
    assert!(q.cards.is_empty());
    assert!(!q.settings.furigana, "reset keeps settings");
}

#[test]
fn start_level_defaults_to_n5_and_round_trips() {
    let path = tmp("start_level");
    // files written before the setting existed load with the default
    std::fs::write(&path, r#"{"settings":{"furigana":false}}"#).unwrap();
    let mut p = Progress::load(&path);
    assert_eq!(p.settings.start_level, "N5");
    assert!(!p.settings.furigana);
    p.settings.start_level = "N2".into();
    p.save();
    assert_eq!(Progress::load(&path).settings.start_level, "N2");
}

#[test]
fn unreadable_progress_is_kept_aside_not_overwritten() {
    let path = tmp("corrupt");
    std::fs::write(&path, "{ not json").unwrap();
    let mut p = Progress::load(&path);
    assert!(p.cards.is_empty());
    let mut bad = path.as_os_str().to_owned();
    bad.push(".bad");
    assert_eq!(std::fs::read_to_string(&bad).unwrap(), "{ not json", "original kept as .bad");
    p.settings.furigana = false;
    p.save();
    assert_eq!(std::fs::read_to_string(&bad).unwrap(), "{ not json", "saving doesn't touch it");
    // a missing file is just a fresh start, nothing to keep
    let fresh = tmp("missing");
    let _ = std::fs::remove_file(&fresh);
    Progress::load(&fresh);
    let mut b = fresh.as_os_str().to_owned();
    b.push(".bad");
    assert!(!std::path::Path::new(&b).exists());
}
