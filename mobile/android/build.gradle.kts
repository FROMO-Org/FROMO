allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
}

// Some transitive plugins (e.g. passkeys_doctor pulled in by supabase_flutter) pin an
// older compileSdk than dependencies like device_info_plus/package_info_plus require.
// Force every Android subproject to compile against at least SDK 36. Done via reflection
// so it stays AGP-version agnostic.
val minimumCompileSdk = 36
fun forceCompileSdk(project: org.gradle.api.Project) {
    val androidExtension = project.extensions.findByName("android") ?: return
    runCatching {
        val current = androidExtension.javaClass.methods
            .firstOrNull { it.name == "getCompileSdk" && it.parameterCount == 0 }
            ?.invoke(androidExtension) as? Int ?: 0
        if (current < minimumCompileSdk) {
            androidExtension.javaClass.methods
                .firstOrNull {
                    it.name == "setCompileSdk" && it.parameterCount == 1 &&
                        it.parameterTypes[0] == Integer::class.java
                }
                ?.invoke(androidExtension, minimumCompileSdk)
        }
    }
}
subprojects {
    // :app already targets SDK 36 and gets force-evaluated above, so only patch the plugins.
    if (project.name != "app") {
        if (state.executed) forceCompileSdk(project) else afterEvaluate { forceCompileSdk(project) }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
