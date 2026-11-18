plugins {
    id("com.android.application")
}

android {
    namespace = "dev.local.bunpo.rust"
    compileSdk = 37
    defaultConfig {
        applicationId = "dev.local.bunpo.rust"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "0.1-rust"
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
