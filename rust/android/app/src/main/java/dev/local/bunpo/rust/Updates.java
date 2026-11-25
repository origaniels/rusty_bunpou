package dev.local.bunpo.rust;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;

import android.content.pm.PackageInfo;
import android.os.Handler;
import android.os.Looper;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * The daily update check: fetch GitHub's answer about the latest release on a background thread
 * (the app polls {@link #result()}). The new version is downloaded by the app itself
 * ({@link #download}), checked (this app, the version expected) and handed to Android's installer,
 * which asks the user to confirm (and, the first time, to allow this app to install updates).
 * Nothing is sent but the requests themselves.
 */
public class Updates {
    private static volatile String result;
    /** "" (nothing under way), "downloading N" (percent, -1 if unknown), "installing", "failed" */
    private static volatile String download = "";
    static final String APK_TYPE = "application/vnd.android.package-archive";
    static final String APK_FILE = "update.apk";

    /** Start fetching {@code url}; {@code etag} (if not empty) lets GitHub answer 304. */
    public static void get(final String url, final String etag) {
        result = null;
        new Thread(() -> {
            int status = 0;
            String tag = "", body = "";
            HttpURLConnection c = null;
            try {
                c = (HttpURLConnection) new URL(url).openConnection();
                c.setConnectTimeout(15000);
                c.setReadTimeout(15000);
                c.setRequestProperty("Accept", "application/vnd.github+json");
                c.setRequestProperty("User-Agent", "bunpo-srs");
                if (!etag.isEmpty()) c.setRequestProperty("If-None-Match", etag);
                status = c.getResponseCode();
                String e = c.getHeaderField("ETag");
                if (e != null) tag = e;
                if (status == 200) {
                    try (InputStream in = c.getInputStream()) {
                        ByteArrayOutputStream out = new ByteArrayOutputStream();
                        byte[] buf = new byte[8192];
                        // a release answer is a few kB; stop at 1 MB whatever comes
                        for (int n; (n = in.read(buf)) > 0 && out.size() < (1 << 20); ) out.write(buf, 0, n);
                        body = out.toString("UTF-8");
                    }
                }
            } catch (Exception ex) {
                android.util.Log.w("bunpo", "update check failed: " + ex);
                status = 0;
            } finally {
                if (c != null) c.disconnect();
            }
            result = status + "\n" + tag + "\n" + body;
        }, "update-check").start();
    }

    /** "status\netag\nbody" once the answer is there (then cleared), else null. */
    public static String result() {
        String r = result;
        if (r != null) result = null;
        return r;
    }

    /** Open a web address (the new version's download) in the browser. */
    public static void open(Activity from, String url) {
        try {
            from.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (Exception e) {
            android.util.Log.w("bunpo", "can't open " + url + ": " + e);
        }
    }

    /** Where the download stands, see {@link #download}. */
    public static String downloadState() {
        return download;
    }

    /**
     * Download the APK at {@code url} (a GitHub release asset) into the files shared with other
     * apps ({@link SharedFiles}), check it is this app at {@code version}, then open the installer.
     */
    public static void download(final Activity from, final String url, final String version) {
        if (download.startsWith("downloading")) return;
        download = "downloading -1";
        new Thread(() -> {
            File dir = new File(from.getFilesDir(), SharedFiles.DIR);
            File part = new File(dir, APK_FILE + ".part"), apk = new File(dir, APK_FILE);
            HttpURLConnection c = null;
            try {
                dir.mkdirs();
                c = (HttpURLConnection) new URL(url).openConnection();
                c.setConnectTimeout(15000);
                c.setReadTimeout(30000);
                c.setRequestProperty("User-Agent", "bunpo-srs");
                int status = c.getResponseCode();
                if (status != 200) throw new Exception("HTTP " + status);
                long total = c.getContentLengthLong();
                try (InputStream in = c.getInputStream(); FileOutputStream out = new FileOutputStream(part)) {
                    byte[] buf = new byte[1 << 16];
                    long got = 0;
                    for (int n; (n = in.read(buf)) > 0; ) {
                        out.write(buf, 0, n);
                        got += n;
                        // an APK of this app is some tens of MB: stop at 200 MB whatever comes
                        if (got > 200L << 20) throw new Exception("too big");
                        download = "downloading " + (total > 0 ? (int) (got * 100 / total) : -1);
                    }
                }
                if (!part.renameTo(apk)) throw new Exception("can't keep the file");
                PackageInfo info = from.getPackageManager().getPackageArchiveInfo(apk.getPath(), 0);
                if (info == null || !from.getPackageName().equals(info.packageName) || !version.equals(info.versionName)) {
                    throw new Exception("not version " + version + " of this app: "
                            + (info == null ? "unreadable" : info.packageName + " " + info.versionName));
                }
                download = "installing";
                new Handler(Looper.getMainLooper()).post(() -> install(from));
            } catch (Exception e) {
                android.util.Log.w("bunpo", "update download failed: " + e);
                part.delete();
                apk.delete();
                download = "failed";
            } finally {
                if (c != null) c.disconnect();
            }
        }, "update-download").start();
    }

    private static void install(Activity from) {
        try {
            Intent i = new Intent(Intent.ACTION_VIEW);
            i.setDataAndType(Uri.parse("content://" + SharedFiles.AUTHORITY + "/" + APK_FILE), APK_TYPE);
            i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            from.startActivity(i);
            download = "";
        } catch (Exception e) {
            android.util.Log.w("bunpo", "can't open the installer: " + e);
            download = "failed";
        }
    }

    /** Remove a downloaded update (once installed, or left over). */
    public static void cleanUp(Activity from) {
        if (!download.isEmpty()) return;
        new File(new File(from.getFilesDir(), SharedFiles.DIR), APK_FILE).delete();
    }
}
