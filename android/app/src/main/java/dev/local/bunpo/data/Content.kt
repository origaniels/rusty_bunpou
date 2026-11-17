package dev.local.bunpo.data

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** A [text, reading] piece of a sentence; reading is empty for kana-only parts. */
data class Seg(val text: String, val reading: String)

data class Sentence(
    val id: Long,
    val ja: String,
    val en: String,
    val owner: String,
    val furi: List<Seg>,
    val clozeStart: Int,
    val clozeEnd: Int,
    val answers: List<String>,
    val hint: String?,
) {
    val answer: String get() = ja.substring(clozeStart, clozeEnd)
}

data class GrammarPoint(
    val id: String,
    val level: String,
    val order: Int,
    val title: String,
    val meaning: String,
    val structure: String,
    val explanation: String,
    val sentences: List<Sentence>,
)

class Content(val points: List<GrammarPoint>, val source: String) {
    val byId: Map<String, GrammarPoint> = points.associateBy { it.id }

    companion object {
        fun load(ctx: Context): Content {
            val text = ctx.assets.open("content.json").bufferedReader(Charsets.UTF_8).use { it.readText() }
            val root = JSONObject(text)
            val pts = root.getJSONArray("points")
            val list = (0 until pts.length()).map { parsePoint(pts.getJSONObject(it)) }
                .filter { it.sentences.isNotEmpty() }
                .sortedBy { it.order }
            return Content(list, root.optString("source"))
        }

        private fun parsePoint(o: JSONObject) = GrammarPoint(
            id = o.getString("id"),
            level = o.getString("level"),
            order = o.getInt("order"),
            title = o.getString("title"),
            meaning = o.getString("meaning"),
            structure = o.getString("structure"),
            explanation = o.getString("explanation"),
            sentences = o.getJSONArray("sentences").let { a -> (0 until a.length()).map { parseSentence(a.getJSONObject(it)) } },
        )

        private fun parseSentence(o: JSONObject): Sentence {
            val furi = o.getJSONArray("furi")
            val cloze = o.getJSONArray("cloze")
            return Sentence(
                id = o.getLong("id"),
                ja = o.getString("ja"),
                en = o.getString("en"),
                owner = o.optString("owner"),
                furi = (0 until furi.length()).map { furi.getJSONArray(it).let { s -> Seg(s.getString(0), s.getString(1)) } },
                clozeStart = cloze.getInt(0),
                clozeEnd = cloze.getInt(1),
                answers = o.getJSONArray("answers").strings(),
                hint = if (o.isNull("hint")) null else o.getString("hint"),
            )
        }

        private fun JSONArray.strings() = (0 until length()).map { getString(it) }
    }
}
