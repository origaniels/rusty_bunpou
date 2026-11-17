package dev.local.bunpo

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.material3.Surface
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.foundation.layout.fillMaxSize
import dev.local.bunpo.ui.AppRoot
import dev.local.bunpo.ui.AppState
import dev.local.bunpo.ui.AppTheme
import dev.local.bunpo.ui.Screen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val app = remember { AppState(applicationContext) }
            BackHandler(enabled = app.screen != Screen.Home) {
                if (app.screen is Screen.Quiz) app.home() else if (!app.back()) app.home()
            }
            AppTheme {
                Surface(Modifier.fillMaxSize()) { AppRoot(app) }
            }
        }
    }
}
