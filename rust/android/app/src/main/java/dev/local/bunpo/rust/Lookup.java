package dev.local.bunpo.rust;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;

/**
 * Show a word in the Takoboto dictionary: in the Takoboto app when it is installed (through the
 * standard "process text" or "share" actions, whichever it accepts), otherwise on its website.
 */
public class Lookup {
    private static final String TAKOBOTO = "jp.takoboto";

    public static void open(Activity from, String word) {
        Intent[] tries = {
            new Intent(Intent.ACTION_PROCESS_TEXT).setType("text/plain")
                    .putExtra(Intent.EXTRA_PROCESS_TEXT, word).putExtra(Intent.EXTRA_PROCESS_TEXT_READONLY, true)
                    .setPackage(TAKOBOTO),
            new Intent(Intent.ACTION_SEND).setType("text/plain")
                    .putExtra(Intent.EXTRA_TEXT, word).setPackage(TAKOBOTO),
            new Intent(Intent.ACTION_VIEW, Uri.parse("https://takoboto.jp/?q=" + Uri.encode(word))),
        };
        PackageManager pm = from.getPackageManager();
        for (Intent i : tries) {
            if (i.resolveActivity(pm) == null) continue;
            try {
                from.startActivity(i);
                return;
            } catch (Exception ignored) {
                // try the next way
            }
        }
    }
}
