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
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("debug")
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
