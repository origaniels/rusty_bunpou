package dev.local.bunpo.rust;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Export / import of the progress file through Android's file picker (no storage permission).
 * Started from Rust over JNI; it has no UI of its own: it opens the picker, copies the file and
 * finishes. The result is left in a small file next to the progress, which the app reads when it
 * comes back to the foreground:
 *   export: files/backup-result.txt = "exported" | "failed" | "cancelled"
 *   import: files/progress.import.json (the picked file), or backup-result.txt = "failed" | "cancelled"
 */
public class Backup extends Activity {
    private static final int EXPORT = 1, IMPORT = 2;

    /** Save a copy of {@code path} wherever the user picks, suggesting {@code name}. */
    public static void export(Activity from, String path, String name) {
        from.startActivity(new Intent(from, Backup.class)
                .putExtra("mode", EXPORT).putExtra("path", path).putExtra("name", name));
    }

    /** Let the user pick a file; it is copied to files/progress.import.json. */
    public static void pickImport(Activity from) {
        from.startActivity(new Intent(from, Backup.class).putExtra("mode", IMPORT));
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (state != null) return; // recreated while the picker is open: the result still comes
        int mode = getIntent().getIntExtra("mode", 0);
        Intent pick;
        if (mode == EXPORT) {
            pick = new Intent(Intent.ACTION_CREATE_DOCUMENT)
                    .addCategory(Intent.CATEGORY_OPENABLE)
                    .setType("application/json")
                    .putExtra(Intent.EXTRA_TITLE, getIntent().getStringExtra("name"));
        } else {
            // some file managers report .json as octet-stream: accept anything, the app validates it
            pick = new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");
        }
        startActivityForResult(pick, mode);
    }

    @Override
    protected void onActivityResult(int request, int result, Intent data) {
        Uri uri = data == null ? null : data.getData();
        String outcome;
        if (result != RESULT_OK || uri == null) {
            outcome = "cancelled";
        } else {
            try {
                if (request == EXPORT) {
                    try (InputStream in = new FileInputStream(getIntent().getStringExtra("path"));
                         OutputStream out = getContentResolver().openOutputStream(uri, "wt")) {
                        copy(in, out);
                    }
                    outcome = "exported";
                } else {
                    File tmp = new File(getFilesDir(), "progress.import.tmp");
                    try (InputStream in = getContentResolver().openInputStream(uri);
                         OutputStream out = new FileOutputStream(tmp)) {
                        copy(in, out);
                    }
                    tmp.renameTo(new File(getFilesDir(), "progress.import.json"));
                    outcome = null; // the app reports the import itself
                }
            } catch (Exception e) {
                outcome = "failed";
            }
        }
        if (outcome != null) {
            try (OutputStream out = new FileOutputStream(new File(getFilesDir(), "backup-result.txt"))) {
                out.write(outcome.getBytes("UTF-8"));
            } catch (Exception ignored) {
            }
        }
        finish();
    }

    private static void copy(InputStream in, OutputStream out) throws java.io.IOException {
        byte[] buf = new byte[64 * 1024];
        for (int n; (n = in.read(buf)) > 0; ) out.write(buf, 0, n);
    }
}
