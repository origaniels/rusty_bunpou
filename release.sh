#!/bin/bash
# Publish a release of the app on GitHub: set the version, run the tests, build the phone APK and
# check it, then commit, tag, push and create the GitHub release with the APK attached.
#
#   ./release.sh X.Y.Z "What changed"            a release: apps that check for updates offer it
#   ./release.sh X.Y.Z "What changed" --pre      a pre-release: a test build nobody is told about
#   ./release.sh X.Y.Z "What changed" --dry-run  everything up to the checked APK, nothing published
#   --skip-tests                                  don't run the test suite first
#
# Versions are X.Y.Z (rust/app/Cargo.toml is the only place they are written; Android's
# versionCode is X*10000 + Y*100 + Z). Bump Z for fixes, Y for new features, X for big changes.
# The release notes are shown in the app ("Version X.Y.Z is available"): keep them short.
#
# Needs: gh logged in, the release keystore set up in ~/.gradle/gradle.properties (see
# rust/android/app/build.gradle.kts), the Android SDK/NDK as for ./rust/build-android.sh.
set -euo pipefail
cd "$(dirname "$0")"

die() { echo "release: $*" >&2; exit 1; }
step() { echo; echo "### $*"; }

[ $# -ge 2 ] || die "usage: ./release.sh X.Y.Z \"release notes\" [--pre] [--dry-run] [--skip-tests]"
version=$1 notes=$2
shift 2
pre=0 dry=0 tests=1
for a in "$@"; do
  case $a in
    --pre) pre=1 ;;
    --dry-run) dry=1 ;;
    --skip-tests) tests=0 ;;
    *) die "unknown option $a" ;;
  esac
done
[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "the version must be X.Y.Z (numbers), not '$version'"
[ -n "${notes// /}" ] || die "the release notes are empty"
tag=v$version

export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
build_tools=$(ls -d "$ANDROID_HOME"/build-tools/* | sort -V | tail -1)
apk=bunpo-srs-arm64.apk
cargo_files=(rust/app/Cargo.toml rust/Cargo.lock)

# ------------------------------------------------------------------ checks before anything changes
step "checks"
command -v gh >/dev/null || die "gh (GitHub CLI) is not installed"
gh auth status >/dev/null 2>&1 || die "gh is not logged in (gh auth login)"
repo=$(gh repo view --json nameWithOwner -q .nameWithOwner) || die "can't find the GitHub repository"
[ "$(git rev-parse --abbrev-ref HEAD)" = main ] || die "not on main"
git diff --quiet && git diff --cached --quiet || die "there are uncommitted changes"
git fetch -q origin
git merge-base --is-ancestor origin/main HEAD || die "origin/main has commits that aren't here: pull first"
git rev-parse -q --verify "refs/tags/$tag" >/dev/null && die "tag $tag exists already"
[ -z "$(git ls-remote --tags origin "refs/tags/$tag")" ] || die "tag $tag exists on GitHub already"

# the new version must be above every earlier tag (v0.3 counts as 0.3.0)
three() { local v=${1#v}; while [[ $(tr -cd . <<<"$v" | wc -c) -lt 2 ]]; do v=$v.0; done; echo "$v"; }
last=$(git tag -l 'v[0-9]*' --sort=-v:refname | head -1)
if [ -n "$last" ]; then
  last3=$(three "$last")
  [ "$last3" != "$version" ] && [ "$(printf '%s\n%s\n' "$last3" "$version" | sort -V | tail -1)" = "$version" ] ||
    die "$version is not above the last release ($last)"
fi
echo "  $repo, ${last:-no release yet} -> $tag ($([ $pre = 1 ] && echo pre-release || echo release))"

# ------------------------------------------------------------------ tests
if [ $tests = 1 ]; then
  step "tests"
  ./test-all.sh
fi

# ------------------------------------------------------------------ version and build
committed=0
restore() { [ $committed = 1 ] || git checkout -q -- "${cargo_files[@]}" 2>/dev/null || true; }
trap restore EXIT

step "version $version"
sed -i "0,/^version = \".*\"/s//version = \"$version\"/" rust/app/Cargo.toml
grep -q "^version = \"$version\"" rust/app/Cargo.toml || die "couldn't set the version in rust/app/Cargo.toml"

step "build (arm64, update check on $repo)"
# BUNPO_UPDATE_REPO is read at compile time: only release builds look for new versions
(cd rust && BUNPO_UPDATE_REPO="$repo" ./build-android.sh release arm64-v8a)
rm -rf rust/android/app/src/main/jniLibs/x86_64
(cd rust/android && ./gradlew -q assembleRelease -PskipCargo)
cp rust/android/app/build/outputs/apk/release/app-release.apk "$apk"

step "checking the APK"
cert=$("$build_tools"/apksigner verify --print-certs "$apk" | sed -n 's/.*certificate SHA-256 digest: //p' | head -1)
want=$(grep -v '^#' rust/android/release-cert.sha256 | tr -d '[:space:]')
[ "$cert" = "$want" ] || die "the APK is signed with another key ($cert): installed apps would refuse it as an update"
echo "  signed with the release key"
badging=$("$build_tools"/aapt2 dump badging "$apk" | head -1)
grep -q "versionName='$version'" <<<"$badging" || die "the APK's version isn't $version: $badging"
echo "  $(grep -o "versionCode='[0-9]*' versionName='[^']*'" <<<"$badging")"
libs=$(unzip -l "$apk" | grep -o 'lib/[^/]*/' | sort -u | tr '\n' ' ')
[ "$libs" = "lib/arm64-v8a/ " ] || die "the APK should only hold the arm64 library, not: $libs"
unzip -p "$apk" lib/arm64-v8a/libbunpo_app.so | grep -qa "$repo" || die "the update check's repository isn't in the build"
echo "  arm64 only, update check on $repo"
echo "  $(du -h "$apk" | cut -f1)  sha256 $(sha256sum "$apk" | cut -d' ' -f1)"

step "summary"
echo "  release:  $tag$([ $pre = 1 ] && echo ' (pre-release: the app will not offer it)')"
echo "  notes:    $notes"
echo "  commits since ${last:-the start}: $(git rev-list --count ${last:+$last..}HEAD)"
echo "  will push main and $tag to $repo, then create the release with $apk"
if [ $dry = 1 ]; then
  echo; echo "dry run: nothing committed or published (the APK is in ./$apk)"
  exit 0
fi
read -r -p "Publish $tag? [y/N] " answer
[[ $answer == [yY]* ]] || { echo "nothing published"; exit 1; }

# ------------------------------------------------------------------ publish
step "publish"
git add "${cargo_files[@]}"
git commit -q -m "release: $tag" -m "$notes"
committed=1
git tag -a "$tag" -m "$tag" -m "$notes"
git push --atomic origin main "$tag"
flags=(--title "$tag" --notes "$notes" --verify-tag)
[ $pre = 1 ] && flags+=(--prerelease) || flags+=(--latest)
gh release create "$tag" "$apk" "${flags[@]}" ||
  die "main and $tag are pushed but the release wasn't created; retry with: gh release create $tag $apk ${flags[*]}"
echo; echo "published: $(gh release view "$tag" --json url -q .url)"
