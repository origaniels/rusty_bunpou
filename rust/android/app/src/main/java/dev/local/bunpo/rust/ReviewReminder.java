package dev.local.bunpo.rust;

import android.Manifest;
import android.app.Activity;
import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;

/**
 * Review reminders. The only Java in the app: Android needs a component it can wake up
 * when the app isn't running. Called from Rust over JNI (see app/src/android.rs).
 */
public class ReviewReminder extends BroadcastReceiver {
    private static final String ACTION = "dev.local.bunpo.rust.REMIND";
    private static final String CHANNEL = "reviews";
    private static final String PREFS = "reminder";
    private static final int NOTIFICATION_ID = 1;
    private static final long WINDOW_MS = 10 * 60 * 1000;

    /** Schedule (or replace) the reminder at {@code atMillis} for {@code count} due reviews. */
    public static void schedule(Context ctx, long atMillis, int count) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
                .putLong("at", atMillis).putInt("count", count).apply();
        AlarmManager am = ctx.getSystemService(AlarmManager.class);
        // a 10-minute delivery window: punctual enough for a reminder, no exact-alarm permission needed
        am.setWindow(AlarmManager.RTC_WAKEUP, atMillis, WINDOW_MS, alarmIntent(ctx));
    }

    public static void cancel(Context ctx) {
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().clear().apply();
        ctx.getSystemService(AlarmManager.class).cancel(alarmIntent(ctx));
        ctx.getSystemService(NotificationManager.class).cancel(NOTIFICATION_ID);
    }

    /** Clear a shown reminder (the user opened the app). */
    public static void dismiss(Context ctx) {
        ctx.getSystemService(NotificationManager.class).cancel(NOTIFICATION_ID);
    }

    public static boolean hasPermission(Context ctx) {
        return Build.VERSION.SDK_INT < 33
                || ctx.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    public static void requestPermission(Activity activity) {
        if (!hasPermission(activity)) {
            activity.requestPermissions(new String[] {Manifest.permission.POST_NOTIFICATIONS}, 1);
        }
    }

    private static PendingIntent alarmIntent(Context ctx) {
        Intent i = new Intent(ctx, ReviewReminder.class).setAction(ACTION);
        return PendingIntent.getBroadcast(ctx, 0, i, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    @Override
    public void onReceive(Context ctx, Intent intent) {
        SharedPreferences p = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        long at = p.getLong("at", 0);
        int count = p.getInt("count", 0);
        if (at == 0) return;
        String action = intent.getAction();
        if (Intent.ACTION_BOOT_COMPLETED.equals(action) || Intent.ACTION_MY_PACKAGE_REPLACED.equals(action)) {
            // alarms don't survive a reboot/update: re-arm (or fire right away if it's already past)
            schedule(ctx, Math.max(at, System.currentTimeMillis() + 60_000), count);
            return;
        }
        if (!ACTION.equals(action) || !hasPermission(ctx)) return;
        NotificationManager nm = ctx.getSystemService(NotificationManager.class);
        nm.createNotificationChannel(new NotificationChannel(CHANNEL, "Review reminders", NotificationManager.IMPORTANCE_DEFAULT));
        Intent open = ctx.getPackageManager().getLaunchIntentForPackage(ctx.getPackageName());
        PendingIntent tap = PendingIntent.getActivity(ctx, 0, open, PendingIntent.FLAG_IMMUTABLE);
        String text = count == 1 ? "1 grammar review is waiting" : count + " grammar reviews are waiting";
        Notification n = new Notification.Builder(ctx, CHANNEL)
                .setSmallIcon(R.drawable.ic_notify)
                .setContentTitle("文法 SRS")
                .setContentText(text)
                .setContentIntent(tap)
                .setAutoCancel(true)
                .build();
        nm.notify(NOTIFICATION_ID, n);
        p.edit().clear().apply();
    }
}
