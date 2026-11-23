//! Update check against the project's GitHub releases: versions, the API answer, when to ask.
//!
//! Only full releases count: GitHub's `/releases/latest` leaves out drafts and pre-releases, so a
//! test build can be published as a pre-release without telling anyone. The repository
//! ("owner/name") is given at build time (`BUNPO_UPDATE_REPO`, set by `release.sh`); builds
//! without it have no update check at all.

use serde::{Deserialize, Serialize};

/// Name of the APK attached to each release (see `release.sh`).
pub const APK_NAME: &str = "bunpo-srs-arm64.apk";

/// At most one check a day (GitHub allows 60 unauthenticated requests an hour per address).
pub const CHECK_EVERY_MS: i64 = 24 * 3_600_000;

/// The newest release seen, and where to get it.
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
pub struct Release {
    /// "0.4.0" (the tag without its "v", completed to three numbers)
    pub version: String,
    /// Release notes, as written for the release.
    pub notes: String,
    /// The APK to download, or the release page when the APK isn't attached.
    pub url: String,
}

/// What the update check remembers between runs (kept by a progress reset).
#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(default)]
pub struct UpdateState {
    /// Last time GitHub answered (ms), whatever the answer.
    pub checked_at: i64,
    /// ETag of the last answer: GitHub answers 304 (and it doesn't count) when nothing changed.
    pub etag: String,
    pub latest: Option<Release>,
    /// A version the user said "Not now" to: not offered again (a newer one is).
    pub skipped: String,
}

/// "v1.2.3", "1.2" or "v1" as [major, minor, patch]; None for anything else.
pub fn parse_version(s: &str) -> Option<[u32; 3]> {
    let s = s.trim();
    let s = s.strip_prefix('v').unwrap_or(s);
    let parts: Vec<&str> = s.split('.').collect();
    if parts.is_empty() || parts.len() > 3 {
        return None;
    }
    let mut v = [0u32; 3];
    for (i, p) in parts.iter().enumerate() {
        if p.is_empty() || !p.bytes().all(|b| b.is_ascii_digit()) {
            return None;
        }
        v[i] = p.parse().ok()?;
    }
    Some(v)
}

/// Whether `version` is newer than `current` (false if either can't be read).
pub fn is_newer(version: &str, current: &str) -> bool {
    match (parse_version(version), parse_version(current)) {
        (Some(a), Some(b)) => a > b,
        _ => false,
    }
}

/// The API address of the latest full release of `repo` ("owner/name").
pub fn latest_url(repo: &str) -> String {
    format!("https://api.github.com/repos/{repo}/releases/latest")
}

/// Only GitHub addresses are opened from a release.
fn trusted(url: &str) -> bool {
    url.starts_with("https://github.com/")
}

/// Read GitHub's answer for the latest release. None for a draft, a pre-release, a tag that
/// isn't a version, or no usable address.
pub fn parse_latest(json: &str) -> Option<Release> {
    #[derive(Deserialize)]
    struct Asset {
        name: String,
        browser_download_url: String,
    }
    #[derive(Deserialize)]
    struct Answer {
        tag_name: String,
        #[serde(default)]
        draft: bool,
        #[serde(default)]
        prerelease: bool,
        #[serde(default)]
        body: Option<String>,
        #[serde(default)]
        html_url: String,
        #[serde(default)]
        assets: Vec<Asset>,
    }
    let a: Answer = serde_json::from_str(json).ok()?;
    if a.draft || a.prerelease {
        return None;
    }
    let [x, y, z] = parse_version(&a.tag_name)?;
    let apk = a.assets.iter().find(|s| s.name == APK_NAME).map(|s| s.browser_download_url.clone());
    let url = apk.filter(|u| trusted(u)).or_else(|| Some(a.html_url.clone()).filter(|u| trusted(u)))?;
    Some(Release { version: format!("{x}.{y}.{z}"), notes: a.body.unwrap_or_default().trim().to_string(), url })
}

/// The release to offer: newer than `current` and not skipped.
pub fn offer<'a>(state: &'a UpdateState, current: &str) -> Option<&'a Release> {
    state.latest.as_ref().filter(|r| is_newer(&r.version, current) && r.version != state.skipped)
}

/// Whether it is time for the daily check.
pub fn due(state: &UpdateState, now: i64) -> bool {
    now - state.checked_at >= CHECK_EVERY_MS || now < state.checked_at
}

/// What to do with an answer from GitHub (`status` 0 = no answer: offline, timeout).
/// Returns whether the answer was usable.
pub fn apply_answer(state: &mut UpdateState, status: i32, etag: &str, body: &str, now: i64) -> bool {
    match status {
        200 => {
            state.checked_at = now;
            state.etag = etag.to_string();
            // a pre-release or unreadable answer leaves what we knew
            if let Some(r) = parse_latest(body) {
                state.latest = Some(r);
            }
            true
        }
        // nothing changed (304), or no full release yet (404)
        304 | 404 => {
            state.checked_at = now;
            true
        }
        // rate-limited: try again tomorrow
        403 | 429 => {
            state.checked_at = now;
            false
        }
        // offline or a server error: try again next time the app opens
        _ => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn answer(tag: &str, pre: bool, assets: &str) -> String {
        format!(
            r#"{{"tag_name":"{tag}","draft":false,"prerelease":{pre},"body":"Fixes\n",
                "html_url":"https://github.com/o/r/releases/tag/{tag}","assets":[{assets}]}}"#
        )
    }
    const APK: &str = r#"{"name":"bunpo-srs-arm64.apk","browser_download_url":"https://github.com/o/r/releases/download/v0.4.0/bunpo-srs-arm64.apk"}"#;

    #[test]
    fn versions_are_compared_as_numbers() {
        assert_eq!(parse_version("v0.4.0"), Some([0, 4, 0]));
        assert_eq!(parse_version("0.3"), Some([0, 3, 0]));
        assert_eq!(parse_version("v1"), Some([1, 0, 0]));
        for bad in ["", "v", "0.4.0-beta", "1..2", "1.2.3.4", "latest", "v0.x"] {
            assert_eq!(parse_version(bad), None, "{bad}");
        }
        assert!(is_newer("v0.10.0", "0.9.0"));
        assert!(is_newer("0.4", "0.3.9"));
        assert!(!is_newer("v0.3", "0.3.0"));
        assert!(!is_newer("v0.2.9", "0.3.0"));
        assert!(!is_newer("garbage", "0.3.0"));
    }

    #[test]
    fn a_full_release_gives_its_apk_and_notes() {
        let r = parse_latest(&answer("v0.4.0", false, APK)).unwrap();
        assert_eq!(r.version, "0.4.0");
        assert_eq!(r.notes, "Fixes");
        assert!(r.url.ends_with("/v0.4.0/bunpo-srs-arm64.apk"));
        // no APK attached: the release page
        let r = parse_latest(&answer("v0.4", false, "")).unwrap();
        assert_eq!((r.version.as_str(), r.url.as_str()), ("0.4.0", "https://github.com/o/r/releases/tag/v0.4"));
    }

    #[test]
    fn pre_releases_odd_tags_and_foreign_links_are_ignored() {
        assert_eq!(parse_latest(&answer("v0.4.0", true, APK)), None);
        assert_eq!(parse_latest(&answer("nightly", false, APK)), None);
        assert_eq!(parse_latest("not json"), None);
        let elsewhere = r#"{"name":"bunpo-srs-arm64.apk","browser_download_url":"https://example.com/x.apk"}"#;
        let r = parse_latest(&answer("v0.4.0", false, elsewhere)).unwrap();
        assert!(r.url.starts_with("https://github.com/"), "falls back to the release page");
        let json = r#"{"tag_name":"v1.0.0","html_url":"http://github.com/o/r","assets":[]}"#;
        assert_eq!(parse_latest(json), None, "not https");
    }

    #[test]
    fn a_skipped_or_older_release_is_not_offered() {
        let mut s = UpdateState { latest: parse_latest(&answer("v0.4.0", false, APK)), ..Default::default() };
        assert!(offer(&s, "0.3.0").is_some());
        assert!(offer(&s, "0.4.0").is_none());
        s.skipped = "0.4.0".into();
        assert!(offer(&s, "0.3.0").is_none());
        s.latest = parse_latest(&answer("v0.5.0", false, APK));
        assert!(offer(&s, "0.3.0").is_some(), "a newer one is offered again");
    }

    #[test]
    fn checks_once_a_day_and_keep_what_they_knew() {
        let mut s = UpdateState::default();
        let t = 1_700_000_000_000; // ms since 1970
        assert!(due(&s, t), "never checked");
        assert!(apply_answer(&mut s, 200, "\"e1\"", &answer("v0.4.0", false, APK), t));
        assert_eq!((s.etag.as_str(), s.checked_at), ("\"e1\"", t));
        assert!(!due(&s, t + CHECK_EVERY_MS - 1));
        assert!(due(&s, t + CHECK_EVERY_MS));
        assert!(due(&s, t - 10), "a clock set back doesn't block checks");
        // nothing new
        assert!(apply_answer(&mut s, 304, "", "", t + 5));
        assert_eq!(s.checked_at, t + 5);
        assert_eq!(s.latest.as_ref().unwrap().version, "0.4.0");
        // a pre-release doesn't replace it
        apply_answer(&mut s, 200, "\"e2\"", &answer("v0.5.0", true, APK), t + 6);
        assert_eq!(s.latest.as_ref().unwrap().version, "0.4.0");
        // offline: nothing changes, so the next opening tries again
        assert!(!apply_answer(&mut s, 0, "", "", t + 7));
        assert_eq!(s.checked_at, t + 6);
        // rate-limited: tomorrow
        assert!(!apply_answer(&mut s, 403, "", "", t + 8));
        assert_eq!(s.checked_at, t + 8);
        // no full release at all yet: nothing to offer, not a failure
        assert!(apply_answer(&mut s, 404, "", "", t + 9));
    }
}
