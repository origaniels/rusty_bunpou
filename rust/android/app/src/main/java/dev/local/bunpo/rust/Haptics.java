package dev.local.bunpo.rust;

import android.app.Activity;
import android.os.Build;
import android.view.HapticFeedbackConstants;
import android.view.View;

/**
 * Short vibrations for checked answers, through the system's haptic feedback (so they follow the
 * phone's "touch feedback" setting and need no vibration permission).
 */
public class Haptics {
    public static void answer(Activity activity, boolean correct) {
        activity.runOnUiThread(() -> {
            View view = activity.getWindow().getDecorView();
            int effect;
            if (Build.VERSION.SDK_INT >= 30) {
                effect = correct ? HapticFeedbackConstants.CONFIRM : HapticFeedbackConstants.REJECT;
            } else {
                effect = correct ? HapticFeedbackConstants.VIRTUAL_KEY : HapticFeedbackConstants.LONG_PRESS;
            }
            view.performHapticFeedback(effect);
        });
    }
}
