package dev.local.bunpo

import dev.local.bunpo.data.Card
import dev.local.bunpo.data.Scheduler
import dev.local.bunpo.srs.Fsrs
import dev.local.bunpo.srs.Kana
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class CoreTest {
    @Test fun romaji() {
        val cases = mapOf(
            "konnichiha" to "こんにちは", "tabetekudasai" to "たべてください", "itta" to "いった",
            "kyou" to "きょう", "shinbun" to "しんぶん", "zasshi" to "ざっし", "benkyoushinakereba" to "べんきょうしなければ",
            "hon'ya" to "ほんや", "onna" to "おんな", "jidousha" to "じどうしゃ", "chotto" to "ちょっと", "nn" to "ん",
            "ikitakatta" to "いきたかった", "wo" to "を", "kanojo" to "かのじょ", "minna" to "みんな",
        )
        for ((r, k) in cases) assertEquals(r, k, Kana.romajiToHiragana(r, final = true))
        // while typing, a trailing n / partial consonant stays as romaji
        assertEquals("こn", Kana.romajiToHiragana("kon", final = false))
        assertEquals("こnn", Kana.romajiToHiragana("konn", final = false))
        assertEquals("こんに", Kana.romajiToHiragana("こnni", final = false))
        assertEquals("たべsh", Kana.romajiToHiragana("tabesh", final = false))
        assertEquals("カタカナ", Kana.romajiToHiragana("カタカナ", final = false))
        assertEquals("たべた", Kana.normalize(" タベタ。 "))
    }

    @Test fun everyAnswerAcceptsItself() {
        val f = File("src/main/assets/content.json")
        val root = JSONObject(f.readText())
        val pts = root.getJSONArray("points")
        var n = 0
        for (i in 0 until pts.length()) {
            val ss = pts.getJSONObject(i).getJSONArray("sentences")
            for (j in 0 until ss.length()) {
                val s = ss.getJSONObject(j)
                val ja = s.getString("ja")
                val c = s.getJSONArray("cloze")
                val blank = ja.substring(c.getInt(0), c.getInt(1))
                val answers = s.getJSONArray("answers").let { a -> (0 until a.length()).map { Kana.normalize(a.getString(it)) } }
                assertTrue("blank '$blank' not accepted in $ja", Kana.normalize(blank) in answers)
                // the furigana text must rebuild the sentence exactly
                val furi = s.getJSONArray("furi")
                val rebuilt = (0 until furi.length()).joinToString("") { furi.getJSONArray(it).getString(0) }
                assertEquals(ja, rebuilt)
                n++
            }
        }
        assertTrue(n > 500)
    }

    @Test fun scheduling() {
        val day = Fsrs.DAY_MS
        var t = 1_000_000_000_000L
        var card = Card("x")
        card = Scheduler.grade(card, true, t, 0.9, 1)
        assertEquals(1, card.state); assertEquals(t + 4 * 3_600_000L, card.due)
        t = card.due; card = Scheduler.grade(card, true, t, 0.9, 1)
        assertEquals(t + 8 * 3_600_000L, card.due)
        t = card.due; card = Scheduler.grade(card, true, t, 0.9, 1)
        assertEquals(2, card.state)
        var last = card.due - t
        assertTrue("first FSRS interval ${last / day.toDouble()} days", last >= day)
        repeat(4) {
            t = card.due; card = Scheduler.grade(card, true, t, 0.9, 1)
            val iv = card.due - t
            assertTrue("intervals should grow: $last -> $iv", iv > last)
            last = iv
        }
        t = card.due; card = Scheduler.grade(card, false, t, 0.9, 1)
        assertEquals(1, card.state); assertEquals(1, card.lapses); assertEquals(t + 3_600_000L, card.due)
        println("stability after lapse: ${card.stability}")
    }
}
