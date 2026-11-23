plugins {
    id("com.android.application")
}

// The version comes from rust/app/Cargo.toml (the one place to change it, see release.sh):
// versionName "X.Y.Z", versionCode X*10000 + Y*100 + Z (Android only installs a higher code).
val versionParts = Regex("""(?m)^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"""")
    .find(rootDir.parentFile.resolve("app/Cargo.toml").readText())
    ?.destructured?.toList()?.map { it.toInt() }
    ?: error("no X.Y.Z version in rust/app/Cargo.toml")
val appVersion = versionParts.joinToString(".")
val appVersionCode = versionParts[0] * 10000 + versionParts[1] * 100 + versionParts[2]

android {
    namespace = "dev.local.bunpo.rust"
    compileSdk = 37
    defaultConfig {
        applicationId = "dev.local.bunpo.rust"
        minSdk = 26
        targetSdk = 37
        versionCode = appVersionCode
        versionName = appVersion
    }
    // Release signing key: set bunpoKeystore (+ bunpoKeystorePassword, bunpoKeyAlias,
    // bunpoKeyPassword) in ~/.gradle/gradle.properties, outside the repo. The key must never
    // change once the app is installed: Android refuses updates signed with another key.
    // Without it, the build falls back to this machine's debug key.
    val keystore = providers.gradleProperty("bunpoKeystore")
    signingConfigs {
        if (keystore.isPresent) {
            create("release") {
                storeFile = file(keystore.get())
                storePassword = providers.gradleProperty("bunpoKeystorePassword").get()
                keyAlias = providers.gradleProperty("bunpoKeyAlias").get()
                keyPassword = providers.gradleProperty("bunpoKeyPassword").get()
            }
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.findByName("release") ?: signingConfigs.getByName("debug")
        }
    }
    packaging { jniLibs { useLegacyPackaging = false } }
}

// Build the Rust library (cargo ndk) before packaging. Set -PskipCargo=true to reuse existing .so files.
val skipCargo = providers.gradleProperty("skipCargo").isPresent
val cargoBuild by tasks.registering(Exec::class) {
    workingDir = rootDir.parentFile
    commandLine("./build-android.sh", "release")
    enabled = !skipCargo
}
tasks.named("preBuild") { dependsOn(cargoBuild) }
