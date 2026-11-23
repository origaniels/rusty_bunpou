package dev.local.bunpo.rust;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * The daily update check: fetch GitHub's answer about the latest release on a background thread
 * (the app polls {@link #result()}), and open the new version's download in the browser.
 * Nothing is sent but the request itself.
 */
public class Updates {
    private static volatile String result;

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
}
