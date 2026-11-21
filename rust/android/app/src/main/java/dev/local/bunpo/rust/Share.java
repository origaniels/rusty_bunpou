package dev.local.bunpo.rust;

import android.app.Activity;
import android.content.ClipData;
import android.content.Intent;
import android.net.Uri;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Open Android's share menu with a file of the app (the reports): the user picks where it goes,
 * an app to send it with or one that saves it. The file is copied under its shared name into
 * files/share/, which {@link SharedFiles} serves to the app that was picked.
 */
public class Share {
    public static void file(Activity from, String path, String name, String title) {
        try {
            File dir = new File(from.getFilesDir(), SharedFiles.DIR);
            dir.mkdirs();
            File[] old = dir.listFiles();
            if (old != null) for (File f : old) f.delete();
            File out = new File(dir, name);
            try (InputStream in = new FileInputStream(path); OutputStream os = new FileOutputStream(out)) {
                byte[] buf = new byte[16384];
                for (int n; (n = in.read(buf)) > 0; ) os.write(buf, 0, n);
            }
            Uri uri = new Uri.Builder().scheme("content").authority(SharedFiles.AUTHORITY).appendPath(name).build();
            Intent send = new Intent(Intent.ACTION_SEND)
                    .setType(SharedFiles.TYPE)
                    .putExtra(Intent.EXTRA_STREAM, uri)
                    .putExtra(Intent.EXTRA_SUBJECT, name)
                    .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            // the permission reaches the picked app through the clip data
            send.setClipData(ClipData.newRawUri(name, uri));
            from.startActivity(Intent.createChooser(send, title));
        } catch (Exception e) {
            android.util.Log.w("bunpo", "share failed: " + e);
        }
    }
}
