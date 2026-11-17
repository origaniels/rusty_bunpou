package dev.local.bunpo.ui

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import dev.local.bunpo.data.Card
import dev.local.bunpo.data.Content
import dev.local.bunpo.data.GrammarPoint
import dev.local.bunpo.data.Progress
import dev.local.bunpo.data.Scheduler
import dev.local.bunpo.data.Sentence
import dev.local.bunpo.srs.Kana

sealed interface Screen {
    data object Home : Screen
    data class Learn(val points: List<String>) : Screen
    data class Quiz(val session: Session) : Screen
    data object GrammarList : Screen
    data class Detail(val pointId: String) : Screen
    data object Settings : Screen
}

class Settings(ctx: Context) {
    private val prefs = ctx.getSharedPreferences("settings", Context.MODE_PRIVATE)
    var furigana by mutableStateOf(prefs.getBoolean("furigana", true)); private set
    var english by mutableStateOf(prefs.getBoolean("english", true)); private set
    var romaji by mutableStateOf(prefs.getBoolean("romaji", true)); private set
    var batchSize by mutableIntStateOf(prefs.getInt("batch", 5)); private set
    var retention by mutableStateOf(prefs.getFloat("retention", 0.9f)); private set

    fun updateFurigana(v: Boolean) { furigana = v; prefs.edit().putBoolean("furigana", v).apply() }
    fun updateEnglish(v: Boolean) { english = v; prefs.edit().putBoolean("english", v).apply() }
    fun updateRomaji(v: Boolean) { romaji = v; prefs.edit().putBoolean("romaji", v).apply() }
    fun updateBatchSize(v: Int) { batchSize = v; prefs.edit().putInt("batch", v).apply() }
    fun updateRetention(v: Float) { retention = v; prefs.edit().putFloat("retention", v).apply() }
}

class AppState(ctx: Context) {
    val content = Content.load(ctx)
    val progress = Progress(ctx)
    val settings = Settings(ctx)
    val cards = mutableStateMapOf<String, Card>().apply { putAll(progress.all()) }
    var screen by mutableStateOf<Screen>(Screen.Home)
    private val backStack = ArrayDeque<Screen>()

    /** Ticks when time-dependent counts (due reviews) should be recomputed. */
    var now by mutableStateOf(System.currentTimeMillis())

    fun card(id: String) = cards[id] ?: Card(id)

    fun navigate(s: Screen) { backStack.addLast(screen); screen = s }
    fun back(): Boolean {
        val prev = backStack.removeLastOrNull() ?: return false
        screen = prev; now = System.currentTimeMillis(); return true
    }
    fun home() { backStack.clear(); screen = Screen.Home; now = System.currentTimeMillis() }

    fun dueIds(at: Long = now): List<String> =
        content.points.map { it.id }.filter { val c = cards[it]; c != null && c.state > 0 && c.due <= at }
            .sortedBy { cards[it]!!.due }

    fun newIds(): List<String> = content.points.map { it.id }.filter { cards[it]?.isNew ?: true }

    fun nextDue(): Long? = cards.values.filter { it.state > 0 }.minOfOrNull { it.due }

    fun startLearn() {
        val ids = newIds().take(settings.batchSize)
        if (ids.isNotEmpty()) navigate(Screen.Learn(ids))
    }

    fun startQuizAfterLearn(ids: List<String>) {
        backStack.clear(); backStack.addLast(Screen.Home)
        screen = Screen.Quiz(Session(this, ids, lesson = true))
    }

    fun startReviews() {
        val ids = dueIds(System.currentTimeMillis()).shuffled()
        if (ids.isNotEmpty()) navigate(Screen.Quiz(Session(this, ids, lesson = false)))
    }

    fun grade(pointId: String, sentence: Sentence, correct: Boolean, answer: String) {
        val now = System.currentTimeMillis()
        val updated = Scheduler.grade(card(pointId), correct, now, settings.retention.toDouble(), sentence.id)
        cards[pointId] = updated
        progress.save(updated)
        progress.log(pointId, sentence.id, if (correct) 3 else 1, answer)
    }

    fun resetPoint(id: String) { cards.remove(id); progress.delete(id) }
    fun resetAll() { cards.clear(); progress.resetAll() }

    fun pickSentence(p: GrammarPoint, avoid: Set<Long>): Sentence {
        val last = cards[p.id]?.lastSentence
        val pool = p.sentences.filter { it.id != last && it.id !in avoid }.ifEmpty { p.sentences }
        return pool.random()
    }
}

enum class Verdict { Correct, Wrong }

const val LESSON_EXAMPLES = 4

/**
 * One quiz run. Each grammar point is graded on its first attempt. Missed points come back at the end
 * of the session with a different sentence (practice only, not graded again) until answered correctly.
 */
class Session(private val app: AppState, ids: List<String>, val lesson: Boolean) {
    private val queue = ArrayDeque(ids)
    private val graded = HashSet<String>()
    /** In lesson quizzes, skip the examples that were just shown on the lesson pages. */
    private val seen = HashSet<Long>().apply {
        if (lesson) ids.forEach { id -> app.content.byId[id]?.sentences?.take(LESSON_EXAMPLES)?.forEach { add(it.id) } }
    }
    val total = ids.size
    var doneCount by mutableIntStateOf(0); private set
    var correctFirstTry by mutableIntStateOf(0); private set

    var point by mutableStateOf<GrammarPoint?>(null); private set
    var sentence by mutableStateOf<Sentence?>(null); private set
    var input by mutableStateOf("")
    var verdict by mutableStateOf<Verdict?>(null); private set
    var lastAnswer by mutableStateOf(""); private set
    val finished get() = point == null

    init { advance() }

    private fun advance() {
        val id = queue.removeFirstOrNull()
        if (id == null) { point = null; sentence = null; return }
        val p = app.content.byId.getValue(id)
        point = p
        sentence = app.pickSentence(p, seen).also { seen.add(it.id) }
        input = ""
        verdict = null
    }

    fun onInput(raw: String) {
        input = if (app.settings.romaji) Kana.romajiToHiragana(raw, final = false) else raw
    }

    fun submit() {
        val s = sentence ?: return
        if (verdict != null) { next(); return }
        val norm = Kana.normalize(input)
        if (norm.isEmpty()) return
        lastAnswer = input
        verdict = if (s.answers.any { Kana.normalize(it) == norm }) Verdict.Correct else Verdict.Wrong
    }

    /** SRS-style "I made a typo": flip a wrong verdict to correct before it is committed. */
    fun overrideCorrect() { if (verdict == Verdict.Wrong) verdict = Verdict.Correct }

    /** Clear the verdict and try again (e.g. the answer was valid but not the targeted grammar). */
    fun retry() { verdict = null; input = "" }

    fun next() {
        val p = point ?: return
        val s = sentence ?: return
        val v = verdict ?: return
        val correct = v == Verdict.Correct
        if (p.id !in graded) {
            graded.add(p.id)
            app.grade(p.id, s, correct, lastAnswer)
            if (correct) correctFirstTry++
        }
        if (correct) doneCount++ else queue.addLast(p.id)
        advance()
    }
}
