#!/bin/bash
# Cross-compile the Slint app into ../rust/android/app/src/main/jniLibs
# usage: ./build-android.sh [debug|release] [abi...]   (default: release arm64-v8a x86_64)
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.cargo/bin:$PATH"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export ANDROID_NDK_HOME="${ANDROID_NDK_HOME:-$(ls -d "$ANDROID_HOME"/ndk/* | sort -V | tail -1)}"
export ANDROID_JAR="${ANDROID_JAR:-$(ls "$ANDROID_HOME"/platforms/*/android.jar | sort -V | tail -1)}"
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/default}"
profile="${1:-release}"; shift || true
abis=("$@"); [ ${#abis[@]} -eq 0 ] && abis=(arm64-v8a x86_64)
targs=(); for a in "${abis[@]}"; do targs+=(-t "$a"); done
flag=(); [ "$profile" = release ] && flag=(--release)
cargo ndk "${targs[@]}" -P 26 -o android/app/src/main/jniLibs build -p bunpo-app "${flag[@]}"
