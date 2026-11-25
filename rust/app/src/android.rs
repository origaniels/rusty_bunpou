//! Android glue: entry point, logcat events and review reminders (JNI → ReviewReminder.java).

use crate::Platform;
use jni::objects::{JClass, JObject, JValue};
use jni::JavaVM;
use slint::android::AndroidApp;
use std::rc::Rc;

const REMINDER_CLASS: &str = "dev.local.bunpo.rust.ReviewReminder";
const BACKUP_CLASS: &str = "dev.local.bunpo.rust.Backup";
const LOOKUP_CLASS: &str = "dev.local.bunpo.rust.Lookup";
const SHARE_CLASS: &str = "dev.local.bunpo.rust.Share";
const HAPTICS_CLASS: &str = "dev.local.bunpo.rust.Haptics";
const UPDATES_CLASS: &str = "dev.local.bunpo.rust.Updates";

pub fn log(msg: &str) {
    use std::ffi::CString;
    unsafe extern "C" {
        fn __android_log_write(prio: i32, tag: *const std::ffi::c_char, text: *const std::ffi::c_char) -> i32;
    }
    let (Ok(tag), Ok(text)) = (CString::new("bunpo"), CString::new(msg)) else { return };
    // 4 = ANDROID_LOG_INFO
    unsafe { __android_log_write(4, tag.as_ptr(), text.as_ptr()) };
}

pub struct AndroidPlatform {
    app: AndroidApp,
}

impl AndroidPlatform {
    /// Run `f` with a JNI env, the activity and the ReviewReminder class.
    fn with_reminder<R>(&self, f: impl FnOnce(&mut jni::JNIEnv, &JObject, &JClass) -> jni::errors::Result<R>) -> Option<R> {
        self.with_class(REMINDER_CLASS, f)
    }

    /// Run `f` with a JNI env, the activity and one of the app's Java classes.
    fn with_class<R>(
        &self,
        class_name: &str,
        f: impl FnOnce(&mut jni::JNIEnv, &JObject, &JClass) -> jni::errors::Result<R>,
    ) -> Option<R> {
        let res = (|| {
            let vm = unsafe { JavaVM::from_raw(self.app.vm_as_ptr() as *mut jni::sys::JavaVM)? };
            let mut env = vm.attach_current_thread()?;
            let activity = unsafe { JObject::from_raw(self.app.activity_as_ptr() as jni::sys::jobject) };
            // app classes are only visible through the activity's class loader (not FindClass)
            let loader = env.call_method(&activity, "getClassLoader", "()Ljava/lang/ClassLoader;", &[])?.l()?;
            let name = env.new_string(class_name)?;
            let class = env
                .call_method(&loader, "loadClass", "(Ljava/lang/String;)Ljava/lang/Class;", &[JValue::Object(&name)])?
                .l()?;
            let class = JClass::from(class);
            let r = f(&mut env, &activity, &class);
            if env.exception_check()? {
                env.exception_describe()?;
                env.exception_clear()?;
            }
            r
        })();
        match res {
            Ok(r) => Some(r),
            Err(e) => {
                log(&format!("jni error: {e}"));
                None
            }
        }
    }
}

impl Platform for AndroidPlatform {
    fn schedule_reminder(&self, at_ms: i64, count: usize, text: &str, channel: &str) {
        self.with_reminder(|env, act, cls| {
            let text = env.new_string(text)?;
            let channel = env.new_string(channel)?;
            env.call_static_method(
                cls,
                "schedule",
                "(Landroid/content/Context;JILjava/lang/String;Ljava/lang/String;)V",
                &[
                    JValue::Object(act),
                    JValue::Long(at_ms),
                    JValue::Int(count as i32),
                    JValue::Object(&text),
                    JValue::Object(&channel),
                ],
            )
            .map(|_| ())
        });
    }

    fn cancel_reminder(&self) {
        self.with_reminder(|env, act, cls| {
            env.call_static_method(cls, "cancel", "(Landroid/content/Context;)V", &[JValue::Object(act)]).map(|_| ())
        });
    }

    fn dismiss_reminder(&self) {
        self.with_reminder(|env, act, cls| {
            env.call_static_method(cls, "dismiss", "(Landroid/content/Context;)V", &[JValue::Object(act)]).map(|_| ())
        });
    }

    fn request_notification_permission(&self) {
        self.with_reminder(|env, act, cls| {
            env.call_static_method(cls, "requestPermission", "(Landroid/app/Activity;)V", &[JValue::Object(act)])
                .map(|_| ())
        });
    }

    fn export_progress(&self, path: &str, name: &str) {
        self.with_class(BACKUP_CLASS, |env, act, cls| {
            let path = env.new_string(path)?;
            let name = env.new_string(name)?;
            env.call_static_method(
                cls,
                "export",
                "(Landroid/app/Activity;Ljava/lang/String;Ljava/lang/String;)V",
                &[JValue::Object(act), JValue::Object(&path), JValue::Object(&name)],
            )
            .map(|_| ())
        });
    }

    fn share_file(&self, path: &str, name: &str, title: &str) {
        self.with_class(SHARE_CLASS, |env, act, cls| {
            let (path, name, title) = (env.new_string(path)?, env.new_string(name)?, env.new_string(title)?);
            env.call_static_method(
                cls,
                "file",
                "(Landroid/app/Activity;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V",
                &[JValue::Object(act), JValue::Object(&path), JValue::Object(&name), JValue::Object(&title)],
            )
            .map(|_| ())
        });
    }

    fn lookup_word(&self, word: &str) {
        self.with_class(LOOKUP_CLASS, |env, act, cls| {
            let word = env.new_string(word)?;
            env.call_static_method(cls, "open", "(Landroid/app/Activity;Ljava/lang/String;)V", &[JValue::Object(act), JValue::Object(&word)])
                .map(|_| ())
        });
    }

    fn haptic(&self, correct: bool) {
        self.with_class(HAPTICS_CLASS, |env, act, cls| {
            env.call_static_method(cls, "answer", "(Landroid/app/Activity;Z)V", &[JValue::Object(act), JValue::Bool(correct.into())])
                .map(|_| ())
        });
    }

    fn pick_import(&self) {
        self.with_class(BACKUP_CLASS, |env, act, cls| {
            env.call_static_method(cls, "pickImport", "(Landroid/app/Activity;)V", &[JValue::Object(act)]).map(|_| ())
        });
    }

    fn font_scale(&self) -> f32 {
        // activity.getResources().getConfiguration().fontScale
        let res = (|| -> jni::errors::Result<f32> {
            let vm = unsafe { JavaVM::from_raw(self.app.vm_as_ptr() as *mut jni::sys::JavaVM)? };
            let mut env = vm.attach_current_thread()?;
            let activity = unsafe { JObject::from_raw(self.app.activity_as_ptr() as jni::sys::jobject) };
            let resources = env.call_method(&activity, "getResources", "()Landroid/content/res/Resources;", &[])?.l()?;
            let config = env.call_method(&resources, "getConfiguration", "()Landroid/content/res/Configuration;", &[])?.l()?;
            env.get_field(&config, "fontScale", "F")?.f()
        })();
        match res {
            Ok(f) => f,
            Err(e) => {
                log(&format!("font scale: {e}"));
                1.0
            }
        }
    }

    fn http_get(&self, url: &str, etag: &str) {
        self.with_class(UPDATES_CLASS, |env, _act, cls| {
            let (url, etag) = (env.new_string(url)?, env.new_string(etag)?);
            env.call_static_method(cls, "get", "(Ljava/lang/String;Ljava/lang/String;)V", &[JValue::Object(&url), JValue::Object(&etag)])
                .map(|_| ())
        });
    }

    fn http_result(&self) -> Option<(i32, String, String)> {
        let r = self.with_class(UPDATES_CLASS, |env, _act, cls| {
            let r = env.call_static_method(cls, "result", "()Ljava/lang/String;", &[])?.l()?;
            if r.is_null() {
                return Ok(None);
            }
            let s: String = env.get_string(&jni::objects::JString::from(r))?.into();
            Ok(Some(s))
        })??;
        let mut parts = r.splitn(3, '\n');
        let status = parts.next()?.parse().unwrap_or(0);
        let etag = parts.next().unwrap_or("").to_string();
        Some((status, etag, parts.next().unwrap_or("").to_string()))
    }

    fn open_url(&self, url: &str) {
        self.with_class(UPDATES_CLASS, |env, act, cls| {
            let url = env.new_string(url)?;
            env.call_static_method(cls, "open", "(Landroid/app/Activity;Ljava/lang/String;)V", &[JValue::Object(act), JValue::Object(&url)])
                .map(|_| ())
        });
    }

    fn download_update(&self, url: &str, version: &str) {
        self.with_class(UPDATES_CLASS, |env, act, cls| {
            let (url, version) = (env.new_string(url)?, env.new_string(version)?);
            env.call_static_method(
                cls,
                "download",
                "(Landroid/app/Activity;Ljava/lang/String;Ljava/lang/String;)V",
                &[JValue::Object(act), JValue::Object(&url), JValue::Object(&version)],
            )
            .map(|_| ())
        });
    }

    fn download_state(&self) -> String {
        self.with_class(UPDATES_CLASS, |env, _act, cls| {
            let r = env.call_static_method(cls, "downloadState", "()Ljava/lang/String;", &[])?.l()?;
            let s: String = env.get_string(&jni::objects::JString::from(r))?.into();
            Ok(s)
        })
        // no answer from Java: treat it as failed rather than downloading forever
        .unwrap_or_else(|| "failed".into())
    }

    fn e2e_dir(&self) -> Option<std::path::PathBuf> {
        self.app.external_data_path()
    }

    fn on_started(&self) {
        // Android may restore the keyboard if the app was killed while it was open (e.g. mid-quiz)
        self.app.hide_soft_input(false);
        // an update downloaded earlier is installed (or was cancelled): its file can go
        self.with_class(UPDATES_CLASS, |env, act, cls| {
            env.call_static_method(cls, "cleanUp", "(Landroid/app/Activity;)V", &[JValue::Object(act)]).map(|_| ())
        });
    }
}

pub fn main(app: AndroidApp) {
    let data = app.internal_data_path();
    let platform = Rc::new(AndroidPlatform { app: app.clone() });
    slint::android::init_with_event_listener(app, |ev| {
        use slint::android::android_activity::{MainEvent, PollEvent};
        if let PollEvent::Main(MainEvent::Resume { .. }) = ev {
            // runs after the current event is processed, on the UI thread
            let _ = slint::invoke_from_event_loop(crate::on_resume);
        }
    })
    .expect("slint android init");
    let path = data.map(|d| d.join("progress.json"));
    crate::run(path, platform).expect("app runs");
}
