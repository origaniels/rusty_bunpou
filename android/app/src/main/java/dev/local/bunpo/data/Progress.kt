package dev.local.bunpo.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import dev.local.bunpo.srs.Fsrs
import kotlin.random.Random

/**
 * SRS state of one grammar point.
 * state: 0 = new, 1 = learning (short fixed steps), 2 = review (FSRS intervals).
 */
data class Card(
    val pointId: String,
    val state: Int = 0,
    val stability: Double = 0.0,
    val difficulty: Double = 0.0,
    val due: Long = 0,
    val lastReview: Long = 0,
    val reps: Int = 0,
    val lapses: Int = 0,
    val step: Int = 0,
    val lastSentence: Long = 0,
) {
    val isNew get() = state == 0

    /** SRS-style level name derived from FSRS stability. */
    val levelName: String
        get() = when {
            state == 0 -> "New"
            state == 1 || stability < 1 -> "Beginner"
            stability < 7 -> "Adept"
            stability < 30 -> "Seasoned"
            stability < 120 -> "Expert"
            else -> "Mastered"
        }
}

class Progress(ctx: Context) : SQLiteOpenHelper(ctx, "progress.db", null, 1) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """CREATE TABLE cards(point_id TEXT PRIMARY KEY, state INTEGER, stability REAL, difficulty REAL,
               due INTEGER, last_review INTEGER, reps INTEGER, lapses INTEGER, step INTEGER, last_sentence INTEGER)"""
        )
        db.execSQL(
            """CREATE TABLE reviews(id INTEGER PRIMARY KEY AUTOINCREMENT, point_id TEXT, sentence_id INTEGER,
               ts INTEGER, grade INTEGER, answer TEXT)"""
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {}

    fun all(): Map<String, Card> {
        val out = HashMap<String, Card>()
        readableDatabase.rawQuery("SELECT * FROM cards", null).use { c ->
            while (c.moveToNext()) {
                val card = Card(
                    pointId = c.getString(0), state = c.getInt(1), stability = c.getDouble(2),
                    difficulty = c.getDouble(3), due = c.getLong(4), lastReview = c.getLong(5),
                    reps = c.getInt(6), lapses = c.getInt(7), step = c.getInt(8), lastSentence = c.getLong(9),
                )
                out[card.pointId] = card
            }
        }
        return out
    }

    fun save(card: Card) {
        val v = ContentValues().apply {
            put("point_id", card.pointId); put("state", card.state); put("stability", card.stability)
            put("difficulty", card.difficulty); put("due", card.due); put("last_review", card.lastReview)
            put("reps", card.reps); put("lapses", card.lapses); put("step", card.step)
            put("last_sentence", card.lastSentence)
        }
        writableDatabase.insertWithOnConflict("cards", null, v, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun delete(pointId: String) {
        writableDatabase.delete("cards", "point_id = ?", arrayOf(pointId))
    }

    fun log(pointId: String, sentenceId: Long, grade: Int, answer: String) {
        val v = ContentValues().apply {
            put("point_id", pointId); put("sentence_id", sentenceId); put("ts", System.currentTimeMillis())
            put("grade", grade); put("answer", answer)
        }
        writableDatabase.insert("reviews", null, v)
    }

    fun reviewsSince(ts: Long): Int =
        readableDatabase.rawQuery("SELECT COUNT(*) FROM reviews WHERE ts >= ?", arrayOf(ts.toString())).use {
            it.moveToFirst(); it.getInt(0)
        }

    fun resetAll() {
        writableDatabase.execSQL("DELETE FROM cards")
        writableDatabase.execSQL("DELETE FROM reviews")
    }
}

/** Scheduling policy: short learning steps first (like the early levels of typical SRS apps), then FSRS. */
object Scheduler {
    private const val HOUR = 3_600_000L
    val LEARNING_STEPS = longArrayOf(4 * HOUR, 8 * HOUR)
    const val RELEARN_DELAY = 1 * HOUR

    fun grade(card: Card, correct: Boolean, now: Long, retention: Double, sentenceId: Long): Card {
        val g = if (correct) 3 else 1
        val elapsed = if (card.lastReview == 0L) 0.0 else (now - card.lastReview).toDouble() / Fsrs.DAY_MS
        val prev = if (card.reps == 0) null else Fsrs.Memory(card.stability, card.difficulty)
        val mem = Fsrs.review(prev, elapsed, g)
        val base = card.copy(
            stability = mem.stability, difficulty = mem.difficulty, lastReview = now,
            reps = card.reps + 1, lastSentence = sentenceId,
        )
        return when {
            !correct -> base.copy(
                state = 1, step = 0, due = now + RELEARN_DELAY,
                lapses = if (card.state == 2) card.lapses + 1 else card.lapses,
            )
            card.state <= 1 && card.step < LEARNING_STEPS.size ->
                base.copy(state = 1, step = card.step + 1, due = now + LEARNING_STEPS[card.step])
            else -> {
                val fuzz = Random.nextDouble(-0.05, 0.05)
                base.copy(state = 2, due = now + Fsrs.intervalMs(mem.stability, retention, fuzz))
            }
        }
    }
}
