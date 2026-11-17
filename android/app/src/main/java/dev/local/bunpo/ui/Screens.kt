package dev.local.bunpo.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import dev.local.bunpo.data.GrammarPoint
import kotlinx.coroutines.delay
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun AppRoot(app: AppState) {
    // refresh "due" counts every minute
    LaunchedEffect(Unit) { while (true) { delay(60_000); app.now = System.currentTimeMillis() } }
    Column(Modifier.fillMaxSize().safeDrawingPadding()) {
        when (val s = app.screen) {
            Screen.Home -> HomeScreen(app)
            is Screen.Learn -> LearnScreen(app, s.points)
            is Screen.Quiz -> QuizScreen(app, s.session)
            Screen.GrammarList -> GrammarListScreen(app)
            is Screen.Detail -> DetailScreen(app, app.content.byId.getValue(s.pointId))
            Screen.Settings -> SettingsScreen(app)
        }
    }
}

@Composable
private fun TopBar(title: String, onBack: (() -> Unit)?, right: @Composable () -> Unit = {}) {
    Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        if (onBack != null) TextButton(onClick = onBack) { Text("‹ Back") } else Spacer(Modifier.width(12.dp))
        Text(title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
        right()
    }
}

// ---------------------------------------------------------------- home

private fun relTime(ms: Long, now: Long): String {
    val d = ms - now
    if (d <= 0) return "now"
    val m = d / 60_000
    return when {
        m < 60 -> "in ${m + 1} min"
        m < 60 * 24 -> "in ${m / 60} h ${m % 60} min"
        else -> SimpleDateFormat("EEE d MMM, HH:mm", Locale.getDefault()).format(Date(ms))
    }
}

@Composable
fun HomeScreen(app: AppState) {
    val now = app.now
    val due = app.dueIds(now).size
    val newCount = app.newIds().size
    val learned = app.content.points.size - newCount
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("文法 SRS", fontSize = 34.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        Text("Japanese grammar, one sentence at a time.", style = MaterialTheme.typography.bodyMedium)

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Reviews", style = MaterialTheme.typography.titleMedium)
                Text("$due due", fontSize = 40.sp, fontWeight = FontWeight.Bold)
                if (due == 0) app.nextDue()?.let { Text("Next review ${relTime(it, now)}") }
                Button(onClick = { app.startReviews() }, enabled = due > 0, modifier = Modifier.fillMaxWidth()) {
                    Text("Start reviews")
                }
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Learn", style = MaterialTheme.typography.titleMedium)
                Text("$newCount new grammar points available")
                val next = app.newIds().take(app.settings.batchSize).mapNotNull { app.content.byId[it]?.title }
                if (next.isNotEmpty()) Text("Next: " + next.joinToString("  ·  "), style = MaterialTheme.typography.bodySmall)
                Button(
                    onClick = { app.startLearn() }, enabled = newCount > 0, modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary),
                ) { Text("Learn ${minOf(app.settings.batchSize, newCount)} new") }
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("N5 progress: $learned / ${app.content.points.size}", style = MaterialTheme.typography.titleMedium)
                LinearProgressIndicator(progress = { learned.toFloat() / app.content.points.size }, modifier = Modifier.fillMaxWidth())
                val levels = listOf("Beginner", "Adept", "Seasoned", "Expert", "Mastered")
                val counts = app.cards.values.groupingBy { it.levelName }.eachCount()
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    levels.forEach { l ->
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("${counts[l] ?: 0}", fontWeight = FontWeight.Bold, fontSize = 20.sp)
                            Text(l, style = MaterialTheme.typography.labelSmall)
                        }
                    }
                }
                val today = System.currentTimeMillis() - 24 * 3_600_000L
                Text("Reviews in the last 24 h: ${app.progress.reviewsSince(today)}", style = MaterialTheme.typography.bodySmall)
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick = { app.navigate(Screen.GrammarList) }, modifier = Modifier.weight(1f)) { Text("Grammar list") }
            OutlinedButton(onClick = { app.navigate(Screen.Settings) }, modifier = Modifier.weight(1f)) { Text("Settings") }
        }
        Text(
            "Example sentences: ${app.content.source}",
            style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline,
        )
    }
}

// ---------------------------------------------------------------- grammar explanation (shared)

@Composable
private fun GrammarBody(app: AppState, p: GrammarPoint, maxExamples: Int) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Pill(p.level)
            Text(p.title, fontSize = 30.sp, fontWeight = FontWeight.Bold)
        }
        Text(p.meaning, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary)
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(12.dp)) {
                Text("Structure", style = MaterialTheme.typography.labelMedium)
                Text(p.structure, fontSize = 18.sp)
            }
        }
        Text(p.explanation.replace("\n", " "), style = MaterialTheme.typography.bodyLarge)
        HorizontalDivider()
        Text("Examples", style = MaterialTheme.typography.titleMedium)
        p.sentences.take(maxExamples).forEach { s ->
            Column(Modifier.padding(vertical = 4.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                SentenceView(s, ClozeStyle.Highlight, app.settings.furigana, fontSize = 20.sp)
                Text(s.en, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.outline)
            }
        }
    }
}

// ---------------------------------------------------------------- learn

@Composable
fun LearnScreen(app: AppState, ids: List<String>) {
    var idx by remember(ids) { mutableIntStateOf(0) }
    val p = app.content.byId.getValue(ids[idx])
    Column(Modifier.fillMaxSize()) {
        TopBar("Lesson ${idx + 1} / ${ids.size}", onBack = { app.back() })
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
            GrammarBody(app, p, maxExamples = LESSON_EXAMPLES)
            Spacer(Modifier.height(16.dp))
        }
        Row(Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick = { idx-- }, enabled = idx > 0, modifier = Modifier.weight(1f)) { Text("Previous") }
            if (idx < ids.size - 1) Button(onClick = { idx++ }, modifier = Modifier.weight(1f)) { Text("Next") }
            else Button(onClick = { app.startQuizAfterLearn(ids) }, modifier = Modifier.weight(1f)) { Text("Start quiz") }
        }
    }
}

// ---------------------------------------------------------------- quiz

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun QuizScreen(app: AppState, session: Session) {
    var showGrammar by remember { mutableStateOf(false) }
    if (session.finished) {
        Column(Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text(if (session.lesson) "Lesson complete!" else "Reviews done!", fontSize = 30.sp, fontWeight = FontWeight.Bold)
            Text("${session.correctFirstTry} / ${session.total} correct on the first try.")
            Button(onClick = { app.home() }, modifier = Modifier.fillMaxWidth()) { Text("Home") }
        }
        return
    }
    val p = session.point!!
    val s = session.sentence!!
    val v = session.verdict
    val focus = remember { FocusRequester() }
    LaunchedEffect(s.id) { runCatching { focus.requestFocus() } }

    Column(Modifier.fillMaxSize().imePadding()) {
        TopBar(
            (if (session.lesson) "Lesson quiz" else "Reviews") + "  ${session.doneCount} / ${session.total}",
            onBack = { app.home() },
        )
        LinearProgressIndicator(
            progress = { session.doneCount.toFloat() / session.total },
            modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp),
        )
        Column(
            Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            SentenceView(
                s,
                if (v == null) ClozeStyle.Blank(session.input) else ClozeStyle.Revealed(v == Verdict.Correct),
                app.settings.furigana,
                fontSize = 26.sp,
            )
            if (app.settings.english || v != null) {
                Text(s.en, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.outline)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Pill(s.hint ?: p.meaning)
            }
            if (v != null) {
                val good = v == Verdict.Correct
                Text(
                    if (good) "Correct!" else "Not quite. You wrote: ${session.lastAnswer}",
                    color = if (good) Good else Bad, fontWeight = FontWeight.Bold, fontSize = 20.sp,
                )
                Text("Answer: ${s.answers.take(2).joinToString("  /  ")}", fontSize = 18.sp)
                Text("Grammar: ${p.title} — ${p.meaning}", style = MaterialTheme.typography.bodyMedium)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    OutlinedButton(onClick = { showGrammar = true }) { Text("Grammar notes") }
                    if (!good) {
                        OutlinedButton(onClick = { session.overrideCorrect() }) { Text("Typo — mark correct") }
                        OutlinedButton(onClick = { session.retry() }) { Text("Retry") }
                    }
                }
                Text(
                    "Tatoeba #${s.id}" + if (s.owner.isNotEmpty()) " by ${s.owner}" else "",
                    style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.outline,
                )
            }
        }
        Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = session.input,
                onValueChange = { if (v == null) session.onInput(it) },
                modifier = Modifier.weight(1f).focusRequester(focus),
                singleLine = true,
                readOnly = v != null,
                placeholder = { Text(if (app.settings.romaji) "type in kana or romaji" else "type the answer") },
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done, autoCorrectEnabled = false),
                keyboardActions = KeyboardActions(onDone = { session.submit() }),
                textStyle = MaterialTheme.typography.titleLarge,
            )
            Button(onClick = { session.submit() }) { Text(if (v == null) "Check" else "Next") }
        }
    }
    if (showGrammar) {
        AlertDialog(
            onDismissRequest = { showGrammar = false },
            confirmButton = { TextButton(onClick = { showGrammar = false }) { Text("Close") } },
            text = { Column(Modifier.verticalScroll(rememberScrollState())) { GrammarBody(app, p, maxExamples = 3) } },
        )
    }
}

// ---------------------------------------------------------------- grammar list & detail

@Composable
fun GrammarListScreen(app: AppState) {
    Column(Modifier.fillMaxSize()) {
        TopBar("Grammar — N5", onBack = { app.back() })
        LazyColumn(contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)) {
            items(app.content.points, key = { it.id }) { p ->
                val c = app.card(p.id)
                Row(
                    Modifier.fillMaxWidth().clickable { app.navigate(Screen.Detail(p.id)) }.padding(vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("${p.order + 1}", Modifier.width(36.dp), color = MaterialTheme.colorScheme.outline)
                    Column(Modifier.weight(1f)) {
                        Text(p.title, fontSize = 20.sp, fontWeight = FontWeight.Medium)
                        Text(p.meaning, style = MaterialTheme.typography.bodySmall)
                    }
                    Pill(c.levelName)
                }
                HorizontalDivider()
            }
        }
    }
}

@Composable
fun DetailScreen(app: AppState, p: GrammarPoint) {
    val c = app.card(p.id)
    var confirmReset by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize()) {
        TopBar(p.title, onBack = { app.back() })
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
            Card(Modifier.fillMaxWidth()) {
                Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Status: ${c.levelName}", fontWeight = FontWeight.Bold)
                        if (!c.isNew) Text(
                            "Next review ${relTime(c.due, System.currentTimeMillis())} · reviews ${c.reps} · lapses ${c.lapses}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                    if (!c.isNew) TextButton(onClick = { confirmReset = true }) { Text("Reset") }
                }
            }
            Spacer(Modifier.height(12.dp))
            GrammarBody(app, p, maxExamples = p.sentences.size)
            Spacer(Modifier.height(24.dp))
        }
    }
    if (confirmReset) {
        AlertDialog(
            onDismissRequest = { confirmReset = false },
            confirmButton = { TextButton(onClick = { app.resetPoint(p.id); confirmReset = false }) { Text("Reset") } },
            dismissButton = { TextButton(onClick = { confirmReset = false }) { Text("Cancel") } },
            text = { Text("Move \"${p.title}\" back to unlearned?") },
        )
    }
}

// ---------------------------------------------------------------- settings

@Composable
private fun ToggleRow(label: String, sub: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.titleMedium)
            Text(sub, style = MaterialTheme.typography.bodySmall)
        }
        Switch(checked = value, onCheckedChange = onChange)
    }
}

@Composable
private fun ChoiceRow(label: String, options: List<Pair<String, Boolean>>, onPick: (Int) -> Unit) {
    Column(Modifier.padding(vertical = 8.dp)) {
        Text(label, style = MaterialTheme.typography.titleMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            options.forEachIndexed { i, (text, selected) ->
                if (selected) Button(onClick = { onPick(i) }) { Text(text) }
                else OutlinedButton(onClick = { onPick(i) }) { Text(text) }
            }
        }
    }
}

@Composable
fun SettingsScreen(app: AppState) {
    val st = app.settings
    var confirm by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize()) {
        TopBar("Settings", onBack = { app.back() })
        Column(Modifier.verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
            ToggleRow("Furigana", "Show readings above kanji", st.furigana, st::updateFurigana)
            ToggleRow("English translation", "Show the translation before answering", st.english, st::updateEnglish)
            ToggleRow("Romaji → kana", "Convert typed romaji to hiragana as you type", st.romaji, st::updateRomaji)
            val batches = listOf(3, 5, 10)
            ChoiceRow("New points per lesson", batches.map { "$it" to (st.batchSize == it) }) { st.updateBatchSize(batches[it]) }
            val rets = listOf(0.85f, 0.9f, 0.95f)
            ChoiceRow(
                "Target retention (FSRS)",
                rets.map { "${(it * 100).toInt()}%" to (kotlin.math.abs(st.retention - it) < 0.001f) },
            ) { st.updateRetention(rets[it]) }
            Text(
                "Higher retention = more frequent reviews. 90% is a good default.",
                style = MaterialTheme.typography.bodySmall,
            )
            Spacer(Modifier.height(24.dp))
            OutlinedButton(onClick = { confirm = true }, colors = ButtonDefaults.outlinedButtonColors(contentColor = Bad)) {
                Text("Reset all progress")
            }
            Spacer(Modifier.height(24.dp))
            Text(
                "Example sentences come from Tatoeba (tatoeba.org) and are licensed CC-BY 2.0 FR. " +
                    "Each sentence shows its Tatoeba number and contributor.",
                style = MaterialTheme.typography.bodySmall, textAlign = TextAlign.Start,
            )
        }
    }
    if (confirm) {
        AlertDialog(
            onDismissRequest = { confirm = false },
            confirmButton = { TextButton(onClick = { app.resetAll(); confirm = false }) { Text("Reset everything") } },
            dismissButton = { TextButton(onClick = { confirm = false }) { Text("Cancel") } },
            text = { Text("This deletes all SRS progress and review history.") },
        )
    }
}
