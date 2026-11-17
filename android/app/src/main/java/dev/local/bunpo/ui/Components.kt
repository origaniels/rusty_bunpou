package dev.local.bunpo.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.Spacer
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.isSystemInDarkTheme
import dev.local.bunpo.data.Sentence

val Accent = Color(0xFFC2453A)
val Good = Color(0xFF2E9D5B)
val Bad = Color(0xFFD64545)
val Highlight = Color(0xFFE0A100)

@Composable
fun AppTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    val scheme = if (dark) darkColorScheme(primary = Color(0xFFFF8A7A), secondary = Highlight)
    else lightColorScheme(primary = Accent, secondary = Highlight)
    MaterialTheme(colorScheme = scheme, content = content)
}

/** How the cloze part of a sentence should be drawn. */
sealed interface ClozeStyle {
    /** Show the whole sentence, cloze part highlighted (lessons / detail pages). */
    data object Highlight : ClozeStyle
    /** Blank box (review prompt); [typed] is shown live inside the box. */
    data class Blank(val typed: String) : ClozeStyle
    /** Show the answer in the box, colored by result. */
    data class Revealed(val correct: Boolean) : ClozeStyle
}

private sealed interface Piece {
    data class Ruby(val text: String, val reading: String) : Piece
    data class Cloze(val segs: List<Pair<String, String>>) : Piece
}

/** Split furigana segments into per-character pieces (so lines wrap anywhere) plus one cloze piece. */
private fun pieces(s: Sentence): List<Piece> {
    val out = mutableListOf<Piece>()
    val cloze = mutableListOf<Pair<String, String>>()
    var clozeAdded = false
    fun addCloze(t: String, r: String) {
        if (!clozeAdded) { out += Piece.Cloze(cloze); clozeAdded = true }
        cloze += t to r
    }
    var pos = 0
    for (seg in s.furi) {
        val start = pos
        pos += seg.text.length
        if (seg.reading.isNotEmpty()) {
            // ruby segments never cross cloze boundaries (they are token-internal)
            if (start >= s.clozeStart && start < s.clozeEnd) addCloze(seg.text, seg.reading)
            else out += Piece.Ruby(seg.text, seg.reading)
        } else {
            for ((k, ch) in seg.text.withIndex()) {
                val i = start + k
                if (i >= s.clozeStart && i < s.clozeEnd) addCloze(ch.toString(), "")
                else out += Piece.Ruby(ch.toString(), "")
            }
        }
    }
    return out
}

/** Fixed line metrics so CJK fallback fonts can't change line heights (keeps ruby/blank aligned). */
private fun fixedLine(size: TextUnit) = TextStyle(
    fontSize = size,
    lineHeight = (size.value * 1.4f).sp,
    lineHeightStyle = LineHeightStyle(LineHeightStyle.Alignment.Center, LineHeightStyle.Trim.None),
)

private class Metrics(val size: TextUnit, val rubySize: TextUnit, val mainH: Dp, val rubyH: Dp, val furigana: Boolean)

private const val NO_LINE_START = "。、！？!?」』）)・ー…ゃゅょっぁぃぅぇぉ"

private fun units(pieces: List<Piece>): List<List<Piece>> {
    val out = mutableListOf<MutableList<Piece>>()
    for (p in pieces) {
        val first = when (p) { is Piece.Ruby -> p.text.first(); is Piece.Cloze -> null }
        if (first != null && first in NO_LINE_START && out.isNotEmpty()) out.last() += p
        else out += mutableListOf(p)
    }
    return out
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun SentenceView(
    s: Sentence,
    style: ClozeStyle,
    furigana: Boolean,
    fontSize: TextUnit = 24.sp,
) {
    val rubySize = (fontSize.value * 0.45f).sp
    val density = LocalDensity.current
    val m = with(density) {
        Metrics(fontSize, rubySize, (fontSize.value * 1.4f).sp.toDp(), (rubySize.value * 1.4f).sp.toDp(), furigana)
    }
    val color = MaterialTheme.colorScheme.onSurface
    FlowRow(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        // a unit never breaks across lines: closing punctuation sticks to the piece before it
        for (unit in units(pieces(s))) Row { for (piece in unit) {
            when (piece) {
                is Piece.Ruby -> RubyChar(piece.text, piece.reading, m, color)
                is Piece.Cloze -> when (style) {
                    ClozeStyle.Highlight -> Row(Modifier.mainLine(m, fill = Highlight.copy(alpha = 0.25f))) {
                        piece.segs.forEach { (t, r) -> RubyChar(t, r, m, color, bold = true) }
                    }
                    is ClozeStyle.Revealed -> {
                        val c = if (style.correct) Good else Bad
                        Row(Modifier.mainLine(m, stroke = c).padding(horizontal = 2.dp)) {
                            piece.segs.forEach { (t, r) -> RubyChar(t, r, m, c, bold = true) }
                        }
                    }
                    is ClozeStyle.Blank -> Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        if (furigana) Spacer(Modifier.height(m.rubyH))
                        Box(
                            Modifier.height(m.mainH).widthIn(min = 72.dp)
                                .border(2.dp, MaterialTheme.colorScheme.primary, RoundedCornerShape(4.dp))
                                .padding(horizontal = 6.dp),
                            contentAlignment = Alignment.Center,
                        ) {
                            Text(style.typed, style = fixedLine(fontSize), color = MaterialTheme.colorScheme.primary, maxLines = 1)
                        }
                    }
                }
            }
        } }
    }
}

/** Decorate only the main text line of a cloze group (not the furigana line above it). */
private fun Modifier.mainLine(m: Metrics, fill: Color? = null, stroke: Color? = null) = drawBehind {
    val top = if (m.furigana) m.rubyH.toPx() else 0f
    val r = CornerRadius(4.dp.toPx())
    val size = Size(size.width, size.height - top)
    fill?.let { drawRoundRect(it, topLeft = Offset(0f, top), size = size, cornerRadius = r) }
    stroke?.let {
        val w = 2.dp.toPx()
        drawRoundRect(
            it, topLeft = Offset(w / 2, top + w / 2), size = Size(size.width - w, size.height - w),
            cornerRadius = r, style = Stroke(w),
        )
    }
}

@Composable
private fun RubyChar(text: String, reading: String, m: Metrics, color: Color, bold: Boolean = false) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        if (m.furigana) Box(Modifier.height(m.rubyH), contentAlignment = Alignment.BottomCenter) {
            if (reading.isNotEmpty()) Text(
                reading, style = fixedLine(m.rubySize), color = color.copy(alpha = 0.75f), maxLines = 1, softWrap = false,
            )
        }
        Box(Modifier.height(m.mainH), contentAlignment = Alignment.Center) {
            Text(
                text, style = fixedLine(m.size), color = color, maxLines = 1, softWrap = false,
                fontWeight = if (bold) FontWeight.Bold else FontWeight.Normal,
            )
        }
    }
}

@Composable
fun Pill(text: String, color: Color = MaterialTheme.colorScheme.secondaryContainer) {
    Text(
        text,
        Modifier.background(color, RoundedCornerShape(50)).padding(horizontal = 10.dp, vertical = 4.dp),
        style = MaterialTheme.typography.labelLarge,
    )
}
