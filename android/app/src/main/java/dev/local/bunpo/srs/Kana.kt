package dev.local.bunpo.srs

/** Romaji → hiragana conversion (IME-like) and answer normalization. */
object Kana {
    private val table: Map<String, String> = buildMap {
        val rows = listOf(
            "" to listOf("あ", "い", "う", "え", "お"),
            "k" to listOf("か", "き", "く", "け", "こ"),
            "g" to listOf("が", "ぎ", "ぐ", "げ", "ご"),
            "s" to listOf("さ", "し", "す", "せ", "そ"),
            "z" to listOf("ざ", "じ", "ず", "ぜ", "ぞ"),
            "t" to listOf("た", "ち", "つ", "て", "と"),
            "d" to listOf("だ", "ぢ", "づ", "で", "ど"),
            "n" to listOf("な", "に", "ぬ", "ね", "の"),
            "h" to listOf("は", "ひ", "ふ", "へ", "ほ"),
            "b" to listOf("ば", "び", "ぶ", "べ", "ぼ"),
            "p" to listOf("ぱ", "ぴ", "ぷ", "ぺ", "ぽ"),
            "m" to listOf("ま", "み", "む", "め", "も"),
            "r" to listOf("ら", "り", "る", "れ", "ろ"),
            "l" to listOf("ら", "り", "る", "れ", "ろ"),
        )
        val vowels = "aiueo"
        for ((c, ks) in rows) for (i in 0..4) put(c + vowels[i], ks[i])
        putAll(
            mapOf(
                "ya" to "や", "yu" to "ゆ", "yo" to "よ", "wa" to "わ", "wo" to "を", "wi" to "うぃ", "we" to "うぇ",
                "shi" to "し", "chi" to "ち", "tsu" to "つ", "fu" to "ふ", "ji" to "じ", "si" to "し", "ti" to "ち",
                "tu" to "つ", "hu" to "ふ", "zi" to "じ", "di" to "ぢ", "du" to "づ", "n'" to "ん",
                "xa" to "ぁ", "xi" to "ぃ", "xu" to "ぅ", "xe" to "ぇ", "xo" to "ぉ", "xtu" to "っ", "xtsu" to "っ",
                "xya" to "ゃ", "xyu" to "ゅ", "xyo" to "ょ", "ltu" to "っ", "lya" to "ゃ", "lyu" to "ゅ", "lyo" to "ょ",
                "fa" to "ふぁ", "fi" to "ふぃ", "fe" to "ふぇ", "fo" to "ふぉ", "ja" to "じゃ", "ju" to "じゅ",
                "je" to "じぇ", "jo" to "じょ", "sha" to "しゃ", "shu" to "しゅ", "she" to "しぇ", "sho" to "しょ",
                "cha" to "ちゃ", "chu" to "ちゅ", "che" to "ちぇ", "cho" to "ちょ", "tsa" to "つぁ",
                "-" to "ー", "va" to "ゔぁ", "vi" to "ゔぃ", "vu" to "ゔ", "ve" to "ゔぇ", "vo" to "ゔぉ",
                "dhi" to "でぃ", "thi" to "てぃ", "dyu" to "でゅ",
            )
        )
        val yRows = mapOf(
            "k" to "き", "g" to "ぎ", "n" to "に", "h" to "ひ", "b" to "び", "p" to "ぴ", "m" to "み", "r" to "り",
            "s" to "し", "z" to "じ", "t" to "ち", "c" to "ち", "j" to "じ", "d" to "ぢ",
        )
        for ((c, k) in yRows) {
            put(c + "ya", k + "ゃ"); put(c + "yu", k + "ゅ"); put(c + "yo", k + "ょ")
        }
    }
    private val maxKey = table.keys.maxOf { it.length }

    private fun isConsonant(c: Char) = c in 'a'..'z' && c !in "aiueon"

    /**
     * Convert romaji to hiragana. If [final] is false, a trailing incomplete chunk (e.g. "k", "sh", "n")
     * is left as romaji so the user can keep typing.
     */
    fun romajiToHiragana(input: String, final: Boolean): String {
        val s = input.lowercase()
        val out = StringBuilder()
        var i = 0
        while (i < s.length) {
            val c = s[i]
            if (c !in 'a'..'z' && c != '-' && c != '\'') { out.append(input[i]); i++; continue }
            // double consonant → っ
            if (i + 1 < s.length && s[i + 1] == c && isConsonant(c)) { out.append('っ'); i++; continue }
            if (c == 'n') {
                val next = s.getOrNull(i + 1)
                if (next == null) {
                    if (final) out.append('ん') else out.append(input[i])
                    i++; continue
                }
                if (next == 'n') {
                    val after = s.getOrNull(i + 2)
                    when {
                        after == null -> { if (final) out.append('ん') else out.append(input, i, i + 2); i += 2 }
                        after in "aiueoy" -> { out.append('ん'); i += 1 } // "nni" → ん + に
                        else -> { out.append('ん'); i += 2 }
                    }
                    continue
                }
                if (next !in "aiueoy'") { out.append('ん'); i++; continue }
            }
            var matched = false
            for (len in minOf(maxKey, s.length - i) downTo 1) {
                val key = s.substring(i, i + len)
                val v = table[key]
                if (v != null) {
                    out.append(v); i += len; matched = true; break
                }
            }
            if (!matched) { out.append(input.substring(i)); break }
        }
        return out.toString()
    }

    fun kataToHira(s: String) = buildString {
        for (c in s) append(if (c in 'ァ'..'ヶ') c - 0x60 else c)
    }

    private val strip = Regex("[\\s　。、．，！？!?.,・「」『』()（）~〜]")

    fun normalize(s: String): String = kataToHira(romajiToHiragana(s.trim(), final = true)).replace(strip, "")
}
