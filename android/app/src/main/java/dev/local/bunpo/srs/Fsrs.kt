package dev.local.bunpo.srs

import kotlin.math.exp
import kotlin.math.max
import kotlin.math.min
import kotlin.math.pow
import kotlin.math.roundToLong

/**
 * FSRS-5 scheduler (https://github.com/open-spaced-repetition), default parameters.
 * Grades: 1 = Again, 2 = Hard, 3 = Good, 4 = Easy. The app uses Again/Good (typed answers).
 */
object Fsrs {
    private val w = doubleArrayOf(
        0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046, 1.54575, 0.1192,
        1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898, 0.51655, 0.6621,
    )
    private const val DECAY = -0.5
    private val FACTOR = 0.9.pow(1 / DECAY) - 1 // = 19/81

    const val DAY_MS = 86_400_000L

    data class Memory(val stability: Double, val difficulty: Double)

    fun retrievability(elapsedDays: Double, stability: Double): Double =
        (1 + FACTOR * elapsedDays / stability).pow(DECAY)

    private fun initStability(g: Int) = max(w[g - 1], 0.1)
    private fun initDifficulty(g: Int) = (w[4] - exp(w[5] * (g - 1)) + 1).coerceIn(1.0, 10.0)

    private fun nextDifficulty(d: Double, g: Int): Double {
        val delta = -w[6] * (g - 3)
        val dp = d + delta * (10 - d) / 9
        return (w[7] * initDifficulty(4) + (1 - w[7]) * dp).coerceIn(1.0, 10.0)
    }

    private fun recallStability(d: Double, s: Double, r: Double, g: Int): Double {
        val hard = if (g == 2) w[15] else 1.0
        val easy = if (g == 4) w[16] else 1.0
        return s * (1 + exp(w[8]) * (11 - d) * s.pow(-w[9]) * (exp(w[10] * (1 - r)) - 1) * hard * easy)
    }

    private fun forgetStability(d: Double, s: Double, r: Double): Double {
        val sf = w[11] * d.pow(-w[12]) * ((s + 1).pow(w[13]) - 1) * exp(w[14] * (1 - r))
        return min(sf, s)
    }

    private fun shortTermStability(s: Double, g: Int) = s * exp(w[17] * (g - 3 + w[18]))

    /** New memory state after a review. [prev] is null for the very first review. */
    fun review(prev: Memory?, elapsedDays: Double, grade: Int): Memory {
        if (prev == null) return Memory(initStability(grade), initDifficulty(grade))
        val d = nextDifficulty(prev.difficulty, grade)
        val s = when {
            elapsedDays < 1.0 -> shortTermStability(prev.stability, grade)
            grade == 1 -> forgetStability(prev.difficulty, prev.stability, retrievability(elapsedDays, prev.stability))
            else -> recallStability(prev.difficulty, prev.stability, retrievability(elapsedDays, prev.stability), grade)
        }
        return Memory(s.coerceIn(0.05, 36500.0), d)
    }

    /** Interval in days for the desired retention. */
    fun intervalDays(stability: Double, retention: Double, maxDays: Double = 365.0): Double {
        val i = stability / FACTOR * (retention.pow(1 / DECAY) - 1)
        return i.coerceIn(1.0, maxDays)
    }

    fun intervalMs(stability: Double, retention: Double, fuzz: Double): Long =
        (intervalDays(stability, retention) * (1 + fuzz) * DAY_MS).roundToLong()
}
