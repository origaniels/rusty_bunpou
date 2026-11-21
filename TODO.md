# Ideas for later

## Read sentences aloud (text-to-speech)
Android's built-in TTS (Google's Japanese voice) could read the example sentences after answering,
offline and with no extra content. Caveats to check on a real phone before committing to it:
- pitch accent is often unnatural, and the voice can sound flat on long sentences;
- kanji with several readings are sometimes misread (the app knows the readings from the furigana,
  so it could pass the kana text instead of the kanji);
- the Japanese voice data may need to be downloaded in the system settings first.
A setting to turn it off would be needed.

## Themes
A light theme and maybe a few colour themes.

## Check for updates (GitHub releases)
Plan only, not started. Tell the user when a newer release is published on the project's GitHub
repo, and let them download it.

**Constraint: the app is offline today.** The manifest has no INTERNET permission. Adding it changes
what the app is, so updates are checked only if the user agrees:
- a "Check for updates" switch in Settings, off by default;
- or a one-time question on first start ("Check GitHub for new versions? Nothing else is sent").

When the check is off, nothing touches the network.

**Where the release comes from**
- `GET https://api.github.com/repos/<owner>/<repo>/releases/latest`, unauthenticated, with a
  generic `User-Agent: bunpo-srs`. Read `tag_name`, `html_url`, `body` (release notes),
  `assets[].name` and `browser_download_url`.
- Owner/repo comes from a build-time constant (gradle property or `env!`), not hard-coded in
  several places.
- The rate limit is 60 requests/hour per IP, so check at most once a day. Send the last response's
  `ETag` as `If-None-Match`: a 304 costs nothing and changes nothing.
- Pre-releases and drafts are not returned by `/latest`, so test builds can be published without
  bothering anyone.

**Versions**
- Tags are `vX.Y.Z`, compared numerically with the running version.
- That needs one source of truth for the version: `Cargo.toml` `version`, with gradle's
  `versionName`/`versionCode` derived from it (`versionCode = X*10000 + Y*100 + Z`). Today
  versionCode = 1 and versionName = "0.1-rust", which are out of sync.
- Rust side: `fn newer(tag: &str, current: &str) -> bool` in core, unit-tested (v-prefix, missing
  patch number, garbage tags give false).

**Doing the request**
- Java side (`Updates.java`, like `Share.java`): `HttpsURLConnection` on a background thread. That
  adds no dependency and keeps rustls/ureq out of the .so (APK size).
- The result goes back to Rust through JNI (a callback or a polled result) as the raw JSON string.
  Rust parses it with serde_json.
- `Platform::check_updates()` in lib.rs, so the UI tests can fake a release with the Recorder.
- When: on app start/resume, if the check is on and the last check is more than 24h old. No
  background job, no alarm. Store `last_update_check`, `etag` and `skipped_version` in Settings.
- Any failure (offline, timeout, 403 rate limit, bad JSON) is silent. Log an event only.

**UI**
- Home: a small card "Version X.Y.Z is available", with "What's new" (release notes, plain text,
  truncated, in a dialog), "Download" and "Not now".
- "Not now" means skip this version: no reminder until a newer tag.
- Settings: the switch, "Check now", and "Current version X.Y.Z" (useful in bug reports too; also
  add the version to the shared reports JSON).
- Strings go in the French .po file as well.

**Installing**
- Step 1 (simple): "Download" opens the APK asset URL (the asset named `bunpo-srs-arm64.apk`; if
  missing, the release page) with ACTION_VIEW in the browser. Android's installer takes over. The
  user must allow "install unknown apps" for their browser once.
- Step 2 (maybe later): download in the app and hand it to `PackageInstaller`. That needs the
  REQUEST_INSTALL_PACKAGES permission and a FileProvider (SharedFiles can serve it). More code,
  more permissions; only worth it if step 1 is annoying.
- Only open https URLs on github.com / objects.githubusercontent.com.

**Release process (prerequisite)**
- Every release must be signed with the **same release keystore**, otherwise Android refuses the
  update ("package conflicts") and the user must uninstall, losing progress unless exported first.
  Builds that fell back to the debug key cannot be updated by release builds. So:
  - check which key the user's installed APK has before the first release;
  - make the release build fail instead of falling back to debug signing.
- Steps: bump the version, tag `vX.Y.Z`, create a GitHub release with notes and attach the arm64
  APK under a fixed name. Later, a GitHub Actions workflow could build and attach it. The keystore
  would then live in repo secrets, never in the repo.

**Tests**
- core: version comparison; parsing a saved `/releases/latest` fixture (fake values only).
- UI: the Recorder returns a newer release, so the home card shows up, "Not now" hides it for that
  version, and an older or equal tag shows nothing. Also check that the switch off means no
  `check_updates` call at all.
- Crawler: "Download" counts as "opens another app".
- e2e: no real network. Inject a fake release through the e2e hook.

**If the app is ever on F-Droid**, F-Droid handles updates and frowns on self-updaters: make the
checker a build flag that F-Droid builds turn off.
