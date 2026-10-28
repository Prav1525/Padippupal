package com.padippupal.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.RecognitionListener
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.media.MediaPlayer
import android.util.Base64
import java.io.File
import android.os.Handler
import android.os.Build
import android.os.Looper
import android.os.SystemClock
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.relocation.BringIntoViewRequester
import androidx.compose.foundation.relocation.bringIntoViewRequester
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.ui.draw.alpha
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.ClickableText
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.GraphicEq
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.MicOff
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material.icons.filled.VolumeOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.IntOffset
import kotlin.math.roundToInt
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.withStyle
import kotlinx.coroutines.delay
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.util.Locale
import java.time.LocalDate
import java.util.concurrent.Executors

// Cool, high-contrast palette: midnight navy + electric teal for a modern learning interface.
private val TutorGreen = Color(0xFF4169E1)
private val TutorDeep = Color(0xFF172033)
private val TutorGrey = Color(0xFF64748B)
private val TutorPaper = Color(0xFFFFFFFF)
private val TutorNight = Color(0xFF0B1220)
private val TutorMutedOnNight = Color(0xFFB8C7D9)
private val TutorAccentSoft = Color(0xFFEAF0FF)
private val tutorExecutor = Executors.newSingleThreadExecutor()
private val tutorMainHandler = Handler(Looper.getMainLooper())


private data class TutorMessage(val role: String, val content: String, val visualLesson: JSONObject? = null, val interactiveLesson: JSONObject? = null)
private data class TutorSource(val title: String, val url: String)

private fun normalizedCheckpoint(raw: String?): String {
    val value = raw.orEmpty().trim()
    return if (value.isBlank() || value.equals("null", ignoreCase = true) || value.equals("undefined", ignoreCase = true) || value == "{}" || value == "[]") "Does that make sense so far?" else value
}

private fun cleanTutorDisplayText(raw: String): String {
    return raw
        .replace("\\text", "")
        .replace("\\angle", "∠")
        .replace("\\times", " × ")
        .replace("\\div", " ÷ ")
        .replace("\\cdot", " · ")
        .replace("\\circ", "°")
        .replace("\\left", "")
        .replace("\\right", "")
        .replace("$", "")
        .replace(Regex("\\s+"), " ")
        .trim()
}

private data class MoveItem(val icon: String, val name: String, val x: Float, val y: Float)

@Composable
private fun WordByWordCaption(
    text: String,
    active: Boolean,
    currentWordIndex: Int,
    modifier: Modifier = Modifier,
    expandToAvailableHeight: Boolean = false
) {
    // Keep the source's spaces and paragraph breaks. Word highlighting must not rewrite
    // the lesson into a new paragraph structure while speech is playing.
    val words = remember(text) { Regex("\\S+").findAll(text).toList() }
    val wordStarts = remember(text) { words.map { it.range.first } }
    val scrollState = rememberScrollState()
    var layoutResult by remember(text) { mutableStateOf<androidx.compose.ui.text.TextLayoutResult?>(null) }
    val density = LocalDensity.current
    val caption = remember(text, active, currentWordIndex) {
        buildAnnotatedString {
            var cursor = 0
            words.forEachIndexed { index, match ->
                val matchStart = match.range.first
                if (matchStart > cursor) append(text.substring(cursor, matchStart))
                val startOffset = length
                append(match.value)
                val endOffset = length
                if (active && index == currentWordIndex.coerceIn(0, (words.size - 1).coerceAtLeast(0))) {
                    addStyle(
                        SpanStyle(background = Color(0xFFDCE7FF), fontWeight = FontWeight.ExtraBold),
                        startOffset,
                        endOffset
                    )
                }
                addStringAnnotation(
                    "word",
                    match.value.trimEnd(',', '.', ';', ':', '?', '!'),
                    startOffset,
                    endOffset
                )
                cursor = match.range.last + 1
            }
            if (cursor < text.length) append(text.substring(cursor))
        }
    }
    LaunchedEffect(currentWordIndex, layoutResult, active, text) {
        val layout = layoutResult
        if (active && layout != null && words.isNotEmpty() && caption.isNotEmpty()) {
            val index = currentWordIndex.coerceIn(0, words.lastIndex)
            val displayOffset = wordStarts.getOrElse(index) { 0 }.coerceAtMost(caption.length - 1).coerceAtLeast(0)
            val line = layout.getLineForOffset(displayOffset)
            val target = (layout.getLineTop(line) - with(density) { 24.dp.toPx() }).coerceAtLeast(0f).toInt()
            runCatching { scrollState.animateScrollTo(target) }
        }
    }
    val captionModifier = if (expandToAvailableHeight) {
        modifier.fillMaxWidth().verticalScroll(scrollState)
    } else {
        modifier.fillMaxWidth().heightIn(max = 190.dp).verticalScroll(scrollState)
    }
    Box(captionModifier) {
        Text(
            text = caption,
            modifier = Modifier.fillMaxWidth(),
            style = androidx.compose.ui.text.TextStyle(
                color = TutorDeep,
                fontSize = 16.sp,
                lineHeight = 26.sp,
                letterSpacing = 0.1.sp,
                fontWeight = FontWeight.Normal,
                textAlign = androidx.compose.ui.text.style.TextAlign.Start
            ),
            onTextLayout = { layoutResult = it }
        )
    }
}

@Composable
private fun ChapterOneMathAnimation(
    scene: String,
    title: String,
    topic: String,
    caption: String,
    compact: Boolean = false
) {
    var stage by remember(scene, title) { mutableIntStateOf(0) }
    LaunchedEffect(scene, title) {
        stage = 0
        while (true) {
            delay(3000L)
            stage = (stage + 1) % 4
        }
    }
    val transition = rememberInfiniteTransition(label = "chapter-one-maths")
    val pulse by transition.animateFloat(
        initialValue = 0.94f,
        targetValue = 1.04f,
        animationSpec = infiniteRepeatable(tween(900), RepeatMode.Reverse),
        label = "pattern-pulse"
    )
    Column(Modifier.fillMaxWidth().padding(vertical = if (compact) 3.dp else 6.dp), verticalArrangement = Arrangement.spacedBy(if (compact) 5.dp else 9.dp)) {
            Text("WATCH THE PATTERN", color = TutorGreen, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
            Text(title, color = TutorDeep, fontSize = if (compact) 14.sp else 16.sp, fontWeight = FontWeight.Bold)
            when (scene) {
                "repeated_ones" -> {
                    if (!compact) Text("The number stays the same each time", color = TutorGrey, fontSize = 12.sp)
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(if (compact) 5.dp else 8.dp), verticalAlignment = Alignment.CenterVertically) {
                        repeat(5) { index ->
                            Box(
                                Modifier.weight(1f).then(if (compact) Modifier.height(38.dp) else Modifier.aspectRatio(1f)).background(
                                    if (index <= stage) Color(0xFFDCE7FF) else Color.White,
                                    RoundedCornerShape(12.dp)
                                ),
                                contentAlignment = Alignment.Center
                            ) {
                                Text("1", color = TutorDeep, fontSize = (if (compact) 18f else 22f * if (index == stage) pulse else 1f).sp, fontWeight = FontWeight.ExtraBold)
                            }
                        }
                    }
                    Text("1, 1, 1, 1, 1 …", color = TutorGreen, fontSize = if (compact) 14.sp else 17.sp, fontWeight = FontWeight.Bold)
                    if (!compact) Text("Each term is 1. The pattern repeats the same number; it does not grow.", color = TutorDeep, fontSize = 13.sp, lineHeight = 18.sp)
                }
                "number_pattern" -> {
                    Text("Numbers can follow a rule", color = TutorGrey, fontSize = 12.sp)
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                        listOf("1", "2", "3", "4", "5").forEachIndexed { index, number ->
                            Column(Modifier.weight(1f).background(if (index <= stage) Color(0xFFDCE7FF) else Color.White, RoundedCornerShape(10.dp)).padding(vertical = 10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(number, color = TutorDeep, fontSize = if (index == stage) (18 * pulse).sp else 17.sp, fontWeight = FontWeight.ExtraBold)
                            }
                        }
                    }
                    Text("Look for the rule that connects each number to the next.", color = TutorDeep, fontSize = 13.sp, lineHeight = 18.sp)
                }
                "shape_pattern" -> {
                    Text("A repeating unit makes a shape pattern", color = TutorGrey, fontSize = 12.sp)
                    val symbols = listOf("●", "▲", "■", "●", "▲", "■", "●", "▲", "■")
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                        symbols.forEachIndexed { index, symbol ->
                            Box(
                                Modifier.weight(1f).aspectRatio(1f).background(
                                    if (index / 3 <= stage) Color(0xFFDCE7FF) else Color.White,
                                    RoundedCornerShape(7.dp)
                                ),
                                contentAlignment = Alignment.Center
                            ) {
                                Text(symbol, color = listOf(Color(0xFF24734B), Color(0xFFDB8A2E), Color(0xFF4B78B8))[index % 3], fontSize = 17.sp, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                    Text(
                        listOf("The repeating unit is circle, triangle, square.", "Now the same three shapes repeat again.", "Look for the unit, not just the next shape.", "Circle, triangle, square — then the pattern starts again.")[stage],
                        color = TutorDeep, fontSize = 13.sp, lineHeight = 18.sp
                    )
                }
                "number_machine" -> {
                    val topicKey = topic.lowercase()
                    val sequenceMode = topicKey.contains("sequence") || topicKey.contains("relations among")
                    val digitMode = topicKey.contains("patterns in numbers")
                    val values = when {
                        sequenceMode -> listOf("1", "3", "6", "10", "15")
                        digitMode -> listOf("12", "21", "12", "21", "12")
                        else -> listOf("2", "4", "6", "8", "10")
                    }
                    val explanation = when {
                        sequenceMode -> listOf("Start with one dot.", "Add a row of two: 1 + 2 = 3.", "Add three more: 3 + 3 = 6.", "Keep adding the next row: 10, then 15.")[stage]
                        digitMode -> listOf("Look at the digits in 12.", "Reverse the digits: 21.", "The same digits can form a different number.", "A digit arrangement can create a repeating pattern.")[stage]
                        else -> listOf("Start with 2.", "Add 2 each time: 4, then 6.", "The rule is +2 at every step.", "Predict the next terms: 10, then 12.")[stage]
                    }
                    Text(
                        when {
                            sequenceMode -> "Triangular numbers: each term adds a new row"
                            digitMode -> "Digit patterns: observe how the digits change"
                            else -> "Number sequences: find the rule between terms"
                        },
                        color = TutorGrey, fontSize = 12.sp
                    )
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                        values.forEachIndexed { index, number ->
                            Column(
                                Modifier.weight(1f).background(if (index <= stage + 1) Color(0xFFDCE7FF) else Color.White, RoundedCornerShape(10.dp)).padding(vertical = 12.dp, horizontal = 2.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text(number, color = TutorDeep, fontSize = 17.sp, fontWeight = FontWeight.ExtraBold)
                                Text(if (sequenceMode) "△ ${index + 1}" else if (digitMode) "digits" else "term ${index + 1}", color = TutorGreen, fontSize = 9.sp)
                            }
                            if (index < values.lastIndex) Text("→", color = TutorGreen, fontWeight = FontWeight.Bold)
                        }
                    }
                    Text(explanation, color = TutorDeep, fontSize = 13.sp, lineHeight = 18.sp)
                }
            }
            if (!compact) {
                Text(caption, color = TutorGrey, fontSize = 11.sp, lineHeight = 16.sp)
                Row(horizontalArrangement = Arrangement.spacedBy(5.dp), verticalAlignment = Alignment.CenterVertically) {
                    repeat(4) { index ->
                        Box(Modifier.weight(1f).height(3.dp).background(if (index == stage) TutorGreen else Color(0xFFDCE3ED), RoundedCornerShape(3.dp)))
                    }
                    Text("AUTO", color = TutorGreen, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
}

@Composable
private fun SynthesizedVisualCard(lesson: JSONObject, compact: Boolean, activeStepOverride: Int?) {
    val title = lesson.optString("title", "Lesson visual")
    val caption = lesson.optString("caption", "")
    val objects = lesson.optJSONArray("objects")
    val labels = buildList {
        if (objects != null) for (index in 0 until objects.length()) {
            val item = objects.optJSONObject(index) ?: continue
            val label = item.optString("label").trim()
            if (label.isNotBlank()) add(label.take(72))
        }
    }.take(6)
    val steps = lesson.optJSONArray("steps")
    val stepCount = (steps?.length() ?: 0).coerceAtLeast(1)
    val active = (activeStepOverride ?: 0).coerceIn(0, stepCount - 1)
    val activeStep = steps?.optJSONObject(active)
    val activeCaption = activeStep?.optString("caption").orEmpty().ifBlank { caption }
    val activeKind = activeStep?.optString("visual_kind").orEmpty()
        .ifBlank { lesson.optString("visual_kind", "concept_card") }
    val activeSubtype = activeStep?.optString("visual_subtype").orEmpty()
        .ifBlank { lesson.optString("visual_subtype", activeKind) }.lowercase()
    val activeLabels = buildList {
        val stepNodes = activeStep?.optJSONArray("nodes")
        if (stepNodes != null) {
            for (index in 0 until stepNodes.length()) {
                val label = stepNodes.optString(index).trim()
                if (label.isNotBlank()) add(label.take(42))
            }
        }
        if (isEmpty()) addAll(labels)
    }.take(6)
    // Restart a short, one-shot reveal whenever speech progress moves to a new synthesis step.
    var revealStarted by remember(active) { mutableStateOf(false) }
    LaunchedEffect(active) {
        delay(40)
        revealStarted = true
    }
    val revealProgress by animateFloatAsState(
        targetValue = if (revealStarted) 1f else 0f,
        animationSpec = tween(durationMillis = 850),
        label = "synthesizedVisualReveal"
    )
    val revealCount = if (activeLabels.isEmpty()) 0 else
        (activeLabels.size * revealProgress).toInt().coerceAtLeast(1).coerceAtMost(activeLabels.size)
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFFF3F8FA), RoundedCornerShape(14.dp))
            .padding(if (compact) 10.dp else 14.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(title, color = Color(0xFF17324D), fontSize = if (compact) 13.sp else 15.sp, fontWeight = FontWeight.Bold)
        if (activeCaption.isNotBlank()) {
            Text(activeCaption, color = Color(0xFF526477), fontSize = if (compact) 11.sp else 12.sp, lineHeight = if (compact) 15.sp else 17.sp)
        }
        Canvas(
            Modifier.fillMaxWidth().height(if (compact) 82.dp else 104.dp)
                .background(Color.White, RoundedCornerShape(10.dp))
        ) {
            val stroke = 1.6.dp.toPx()
            val centerY = size.height * 0.52f
            when (activeKind) {
                "fraction" -> {
                    val count = when { activeLabels.any { it.contains("six", true) || it == "6" } -> 6; activeLabels.any { it.contains("five", true) || it == "5" } -> 5; activeLabels.any { it.contains("four", true) || it == "4" } -> 4; activeLabels.any { it.contains("three", true) || it == "3" } -> 3; activeLabels.any { it.contains("two", true) || it == "2" } -> 2; else -> activeLabels.size.coerceIn(2, 6) }
                    val gap = 5.dp.toPx()
                    val totalWidth = size.width * 0.78f
                    val cellWidth = (totalWidth - gap * (count - 1)) / count
                    val left = (size.width - totalWidth) / 2f
                    val top = size.height * 0.22f
                    val height = size.height * 0.56f
                    repeat(count) { index ->
                        drawRoundRect(
                            color = if (index == 0 && revealCount > 0) Color(0xFF5BB7A5) else Color(0xFFF3F8FA),
                            topLeft = Offset(left + index * (cellWidth + gap), top),
                            size = androidx.compose.ui.geometry.Size(cellWidth, height),
                            cornerRadius = androidx.compose.ui.geometry.CornerRadius(6.dp.toPx()),
                            style = androidx.compose.ui.graphics.drawscope.Fill
                        )
                        drawRoundRect(
                            color = Color(0xFF287F79),
                            topLeft = Offset(left + index * (cellWidth + gap), top),
                            size = androidx.compose.ui.geometry.Size(cellWidth, height),
                            cornerRadius = androidx.compose.ui.geometry.CornerRadius(6.dp.toPx()),
                            style = androidx.compose.ui.graphics.drawscope.Stroke(stroke)
                        )
                    }
                }
                "sequence", "process" -> {
                    val count = activeLabels.size.coerceIn(1, 4)
                    val gap = 7.dp.toPx()
                    val boxWidth = (size.width * 0.86f - gap * (count - 1)) / count
                    val left = size.width * 0.07f
                    val top = size.height * 0.28f
                    activeLabels.take(count).forEachIndexed { index, _ ->
                        if (index < revealCount) {
                            val x = left + index * (boxWidth + gap)
                            if (index > 0) drawLine(Color(0xFF7C91A0), Offset(x - gap, centerY), Offset(x - 2.dp.toPx(), centerY), stroke)
                            drawRoundRect(Color(0xFFDCEFEB), Offset(x, top), androidx.compose.ui.geometry.Size(boxWidth, size.height * 0.44f), androidx.compose.ui.geometry.CornerRadius(7.dp.toPx()))
                            drawRoundRect(Color(0xFF287F79), Offset(x, top), androidx.compose.ui.geometry.Size(boxWidth, size.height * 0.44f), androidx.compose.ui.geometry.CornerRadius(7.dp.toPx()), style = androidx.compose.ui.graphics.drawscope.Stroke(stroke))
                        }
                    }
                }
                "cycle" -> {
                    val points = listOf(
                        Offset(size.width * 0.50f, size.height * 0.18f),
                        Offset(size.width * 0.78f, size.height * 0.52f),
                        Offset(size.width * 0.50f, size.height * 0.84f),
                        Offset(size.width * 0.22f, size.height * 0.52f)
                    )
                    val count = activeLabels.size.coerceIn(2, 4)
                    repeat(count) { index ->
                        if (index < revealCount) {
                            drawLine(Color(0xFF7C91A0), points[index], points[(index + 1) % count], stroke)
                            drawCircle(Color(0xFFDCEFEB), 8.dp.toPx(), points[index])
                            drawCircle(Color(0xFF287F79), 8.dp.toPx(), points[index], style = androidx.compose.ui.graphics.drawscope.Stroke(stroke))
                        }
                    }
                }
                "compare" -> {
                    val count = activeLabels.size.coerceIn(1, 3)
                    val gap = 7.dp.toPx()
                    val panelWidth = (size.width * 0.82f - gap * (count - 1)) / count
                    val left = size.width * 0.09f
                    val top = size.height * 0.20f
                    repeat(count) { index ->
                        if (index < revealCount) {
                            val x = left + index * (panelWidth + gap)
                            drawRoundRect(Color(0xFFDCEFEB), Offset(x, top), androidx.compose.ui.geometry.Size(panelWidth, size.height * 0.58f), androidx.compose.ui.geometry.CornerRadius(7.dp.toPx()))
                            drawRoundRect(Color(0xFF7C91A0), Offset(x, top), androidx.compose.ui.geometry.Size(panelWidth, size.height * 0.58f), androidx.compose.ui.geometry.CornerRadius(7.dp.toPx()), style = androidx.compose.ui.graphics.drawscope.Stroke(stroke))
                        }
                    }
                }
                "geometry", "number_line" -> {
                    val left = size.width * 0.12f
                    val right = size.width * 0.88f
                    drawLine(Color(0xFF287F79), Offset(left, centerY), Offset(right, centerY), stroke)
                    val count = activeLabels.size.coerceIn(2, 5)
                    repeat(count) { index ->
                        val x = left + (right - left) * index / (count - 1)
                        if (index < revealCount) drawCircle(Color(0xFF5BB7A5), 5.dp.toPx(), Offset(x, centerY))
                    }
                    if (activeKind == "geometry" && revealCount >= 3) {
                        val p1 = Offset(size.width * 0.32f, size.height * 0.82f)
                        val p2 = Offset(size.width * 0.50f, size.height * 0.18f)
                        val p3 = Offset(size.width * 0.68f, size.height * 0.82f)
                        drawLine(Color(0xFF7CA9E8), p1, p2, stroke * 1.5f)
                        drawLine(Color(0xFF7CA9E8), p2, p3, stroke * 1.5f)
                        drawLine(Color(0xFF7CA9E8), p3, p1, stroke * 1.5f)
                    }
                }
                "table" -> {
                    val count = activeLabels.size.coerceIn(1, 3)
                    val colWidth = size.width * 0.78f / count
                    val left = size.width * 0.11f
                    val top = size.height * 0.20f
                    repeat(count) { index ->
                        if (index < revealCount) {
                            drawRect(Color(0xFFDCEFEB), Offset(left + index * colWidth, top), androidx.compose.ui.geometry.Size(colWidth - 2.dp.toPx(), size.height * 0.58f))
                            drawRect(Color(0xFF7C91A0), Offset(left + index * colWidth, top), androidx.compose.ui.geometry.Size(colWidth - 2.dp.toPx(), size.height * 0.58f), style = androidx.compose.ui.graphics.drawscope.Stroke(stroke))
                        }
                    }
                }
                else -> {
                    drawCircle(Color(0xFFDCEFEB), size.minDimension * 0.30f, Offset(size.width / 2f, centerY))
                    drawCircle(Color(0xFF287F79), size.minDimension * 0.30f, Offset(size.width / 2f, centerY), style = androidx.compose.ui.graphics.drawscope.Stroke(stroke))
                    if (activeLabels.size > 1) drawLine(Color(0xFF7CA9E8), Offset(size.width * 0.38f, centerY), Offset(size.width * 0.62f, centerY), stroke)
                }
            }
        }
        activeLabels.take(revealCount).chunked(3).forEach { group ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                group.forEach { label ->
                    Surface(
                        modifier = Modifier.weight(1f),
                        color = Color.White,
                        shape = RoundedCornerShape(9.dp),
                        border = BorderStroke(1.dp, Color(0xFFD9E5EC))
                    ) {
                        Text(
                            label,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = if (compact) 7.dp else 9.dp),
                            color = Color(0xFF17324D),
                            fontSize = if (compact) 10.sp else 12.sp,
                            lineHeight = if (compact) 13.sp else 16.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
                repeat((3 - group.size).coerceAtLeast(0)) { Spacer(Modifier.weight(1f)) }
            }
        }
        if (stepCount > 1) {
            Row(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalAlignment = Alignment.CenterVertically) {
                repeat(stepCount.coerceAtMost(8)) { index ->
                    Box(
                        Modifier
                            .weight(1f)
                            .height(3.dp)
                            .background(if (index == active) Color(0xFF0F766E) else Color(0xFFD5E1E8), RoundedCornerShape(3.dp))
                    )
                }
            }
        }
    }
}


@Composable
private fun DatabaseInteractiveLessonLab(lesson: JSONObject, sessionPrefs: android.content.SharedPreferences, sessionKey: String, todayKey: String, compact: Boolean = false, activeStepOverride: Int? = null) {
    val scene = lesson.optString("scene_type", "explore")
    val caption = lesson.optString("caption", "Move the objects and observe what changes.")
    val title = lesson.optString("title", lesson.optString("topic", "Explore this concept"))
    val key = lesson.optString("id", title)
    val raw = lesson.optJSONArray("objects")
    if (scene == "synthesis_static") {
        SynthesizedVisualCard(lesson, compact, activeStepOverride)
        return
    }
    if (lesson.optString("chapter") == "Patterns in Mathematics" && scene in setOf("number_pattern", "shape_pattern", "number_machine", "pattern_builder")) {
        val topicKey = lesson.optString("topic").lowercase()
        val mappedScene = when {
            topicKey.contains("all 1s") || topicKey.contains("all ones") -> "repeated_ones"
            scene == "pattern_builder" || topicKey.contains("shape") -> "shape_pattern"
            else -> scene
        }
        ChapterOneMathAnimation(mappedScene, title, lesson.optString("topic"), caption, compact = compact)
        return
    }
    val items = remember(key) {
        when (scene) {
            "fraction_builder" -> listOf(
                MoveItem("🟩", "1/4", .08f, .28f), MoveItem("🟩", "1/4", .29f, .28f),
                MoveItem("🟩", "1/4", .50f, .28f), MoveItem("⬜", "1/4", .71f, .28f)
            )
            "magnet_test" -> listOf(
                MoveItem("🧲", "Magnet", .08f, .32f), MoveItem("📎", "Iron clip", .70f, .18f),
                MoveItem("📎", "Steel pin", .70f, .55f), MoveItem("🪵", "Wood", .42f, .58f)
            )
            "angle_builder", "angle_classifier" -> listOf(
                MoveItem("📍", "Vertex", .42f, .43f), MoveItem("➡️", "Ray A", .76f, .43f),
                MoveItem("↗️", "Ray B", .60f, .12f)
            )
            "point_marker" -> listOf(MoveItem("📍", "Point A", .48f, .42f))
            "line_segment" -> listOf(MoveItem("A", "Endpoint A", .20f, .43f), MoveItem("B", "Endpoint B", .76f, .43f))
            "line" -> listOf(MoveItem("A", "Point A", .25f, .43f), MoveItem("B", "Point B", .70f, .43f))
            "ray" -> listOf(MoveItem("A", "Start", .22f, .43f), MoveItem("B", "Ray point", .70f, .43f))
            "line_ray_segment" -> listOf(MoveItem("AB", "Segment", .04f, .05f), MoveItem("→", "Ray", .04f, .36f), MoveItem("↔", "Line", .04f, .67f))
            "integer_line" -> listOf(
                MoveItem("🔵", "−3", .15f, .30f), MoveItem("🟢", "0", .48f, .30f),
                MoveItem("🟠", "+3", .80f, .30f)
            )
            "measure_length" -> listOf(MoveItem("📍", "Start", .12f, .30f), MoveItem("📍", "End", .72f, .30f))
            "motion_track" -> listOf(MoveItem("🏁", "Start", .08f, .30f), MoveItem("🚗", "Toy", .45f, .30f), MoveItem("🏁", "Finish", .84f, .30f))
            "bar_chart" -> listOf(MoveItem("A", "Group A", .18f, .12f), MoveItem("B", "Group B", .46f, .12f), MoveItem("C", "Group C", .74f, .12f))
            "number_pattern" -> listOf(
                MoveItem("1", "1 × 1", .04f, .30f), MoveItem("4", "2 × 2", .25f, .30f),
                MoveItem("9", "3 × 3", .46f, .30f), MoveItem("16", "4 × 4", .67f, .30f)
            )
            else -> {
                val parsed = mutableListOf<MoveItem>()
                if (raw != null) for (i in 0 until raw.length()) {
                    val obj = raw.optJSONObject(i) ?: continue
                    val pos = obj.optJSONArray("position")
                    parsed += MoveItem(
                        when (i % 5) { 0 -> "🔵"; 1 -> "🟢"; 2 -> "🟠"; 3 -> "🟣"; else -> "🟡" },
                        obj.optString("label", "Explore"),
                        (pos?.optDouble(0, .2) ?: .2).toFloat().coerceIn(0f, 1f),
                        (pos?.optDouble(1, .3) ?: .3).toFloat().coerceIn(0f, 1f)
                    )
                }
                parsed.ifEmpty { listOf(MoveItem("🔵", "Try it", .2f, .3f), MoveItem("🟢", "Observe", .6f, .4f)) }
            }
        }
    }
    var positions by remember(key) { mutableStateOf(items.map { Offset(it.x, it.y) }) }
    var feedback by remember(key) { mutableStateOf(if (scene == "number_pattern") "Notice the growing gaps: +3, +5, +7." else "Touch an object, drag it, and notice what changes.") }
    var selectedPatternAnswer by remember(key) { mutableStateOf<Int?>(null) }
    val steps = lesson.optJSONArray("steps")
    val stepCount = (steps?.length() ?: 0).coerceAtLeast(1)
    val stepPreferenceKey = "lesson_step_${sessionKey}_${key}"
    val stepDateKey = "${stepPreferenceKey}_date"
    val savedStep = if (sessionPrefs.getString(stepDateKey, "") == todayKey) sessionPrefs.getInt(stepPreferenceKey, 0) else 0
    var activeStep by remember(key) { mutableIntStateOf(savedStep.coerceIn(0, stepCount - 1)) }
    val displayStep = activeStepOverride?.coerceIn(0, stepCount - 1) ?: activeStep
    val setActiveStep: (Int) -> Unit = { nextStep ->
        activeStep = nextStep.coerceIn(0, stepCount - 1)
        sessionPrefs.edit().putInt(stepPreferenceKey, activeStep).putString(stepDateKey, todayKey).apply()
    }
    var heatLevel by remember(key) { mutableFloatStateOf(.28f) }
    var chartValue by remember(key) { mutableFloatStateOf(.62f) }
    val motion = rememberInfiniteTransition(label = "interactive-db-motion")
    val pulse by motion.animateFloat(0f, 1f, infiniteRepeatable(tween(1800), RepeatMode.Reverse), label = "pulse")
    val vertex = positions.getOrNull(0) ?: Offset(.5f, .5f)
    val angle = if (scene in listOf("angle_builder", "angle_classifier") && positions.size >= 3) {
        val a = positions[1]; val b = positions[2]
        val degA = Math.toDegrees(kotlin.math.atan2((a.y-vertex.y).toDouble(), (a.x-vertex.x).toDouble()))
        val degB = Math.toDegrees(kotlin.math.atan2((b.y-vertex.y).toDouble(), (b.x-vertex.x).toDouble()))
        (kotlin.math.abs(degA-degB).let { if (it > 180) 360-it else it }).toInt()
    } else 0
    val magnetic = scene == "magnet_test" && positions.size >= 2 &&
        positions.drop(1).withIndex().any { indexed ->
            val p = indexed.value
            val label = items.getOrNull(indexed.index+1)?.name.orEmpty().lowercase()
            (label.contains("iron") || label.contains("steel") || label.contains("metal")) &&
                kotlin.math.sqrt((p.x-positions[0].x)*(p.x-positions[0].x)+(p.y-positions[0].y)*(p.y-positions[0].y)) < .20f
        }
    Surface(Modifier.fillMaxWidth().padding(top=8.dp), color=Color(0xFFF8FAFC), shape=RoundedCornerShape(18.dp), border=BorderStroke(1.dp, Color(0xFFDCE3ED))) {
        Column(Modifier.padding(12.dp), verticalArrangement=Arrangement.spacedBy(7.dp)) {
            Row(verticalAlignment=Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(if (compact) "CONCEPT VISUAL" else "DATABASE INTERACTIVE LESSON", color=TutorGreen, fontSize=10.sp, fontWeight=FontWeight.Bold)
                    Text(title, color=TutorDeep, fontSize=14.sp, fontWeight=FontWeight.SemiBold)
                }
                if (!compact) TextButton(onClick={ positions=items.map { Offset(it.x,it.y) }; feedback="Reset. Try another arrangement."; setActiveStep(0) }) { Text("Reset", color=TutorGreen) }
            }
            BoxWithConstraints(Modifier.fillMaxWidth().height(if (compact) 104.dp else 190.dp).background(Color.White, RoundedCornerShape(14.dp))) {
                val w=maxWidth; val h=maxHeight
                Canvas(Modifier.fillMaxSize()) {
                    when (scene) {
                        "particle_states", "phase_change", "evap_condense" -> {
                            val spread = .12f + heatLevel * .34f
                            val count = 18
                            for (i in 0 until count) {
                                val col = i % 6
                                val row = i / 6
                                val x = size.width * (.5f + (col - 2.5f) * spread)
                                val y = size.height * (.47f + (row - 1f) * spread)
                                val wiggle = if (heatLevel > .66f) (pulse - .5f) * 14.dp.toPx() else 0f
                                drawCircle(Color(0xFF3987C9), 5.dp.toPx(), Offset((x+wiggle).coerceIn(8f,size.width-8f),(y-wiggle).coerceIn(8f,size.height-8f)))
                            }
                        }
                        "orbit_lab", "day_night", "moon_phase" -> {
                            val center = Offset(size.width*.5f, size.height*.48f)
                            val radius = minOf(size.width, size.height)*.34f
                            drawCircle(Color(0xFFCBD5E1), radius, center, style=androidx.compose.ui.graphics.drawscope.Stroke(2.dp.toPx()))
                            if (scene=="day_night") {
                                drawCircle(Color(0xFF3C91D6), radius*.55f, center)
                                drawArc(Color(0xFF23415F), 90f, 180f, true, Offset(center.x-radius*.55f,center.y-radius*.55f), androidx.compose.ui.geometry.Size(radius*1.1f,radius*1.1f))
                                drawLine(Color.White,Offset(center.x,center.y-radius*.55f),Offset(center.x,center.y+radius*.55f),1.dp.toPx())
                            } else {
                                drawCircle(Color(0xFFFFC857), radius*.18f, center)
                                if (scene=="moon_phase") drawCircle(Color(0xFF5F86C8), radius*.13f, Offset(center.x+radius*.75f,center.y))
                            }
                        }
                        "bar_chart" -> {
                            val baseY=size.height*.82f
                            val barWidth=size.width*.16f
                            val heights=listOf(.36f,.58f,chartValue)
                            for(i in 0..2) {
                                val left=size.width*(.18f+i*.28f)
                                drawRect(Color(0xFF6B8DE3),Offset(left,baseY-size.height*heights[i]),androidx.compose.ui.geometry.Size(barWidth,size.height*heights[i]))
                            }
                            drawLine(Color(0xFF578368),Offset(size.width*.08f,baseY),Offset(size.width*.94f,baseY),2.dp.toPx())
                        }
                        "factor_tree" -> if (positions.size >= 3) {
                            val root=positions[0]
                            positions.drop(1).forEach { p -> drawLine(Color(0xFF24734B),Offset(root.x*size.width,root.y*size.height),Offset(p.x*size.width,p.y*size.height),2.dp.toPx()) }
                        }
                        "fraction_builder" -> {
                            // A simple, original four-part fraction diagram; this is not a copied textbook image.
                            val left = size.width * .12f
                            val top = size.height * .58f
                            val cellWidth = size.width * .19f
                            val cellHeight = size.height * .22f
                            repeat(4) { index ->
                                val cell = Offset(left + index * cellWidth, top)
                                drawRect(
                                    color = if (index < 3) Color(0xFFB9E3C7) else Color(0xFFF8FAFC),
                                    topLeft = cell,
                                    size = androidx.compose.ui.geometry.Size(cellWidth - 3.dp.toPx(), cellHeight)
                                )
                                drawRect(
                                    color = Color(0xFF24734B),
                                    topLeft = cell,
                                    size = androidx.compose.ui.geometry.Size(cellWidth - 3.dp.toPx(), cellHeight),
                                    style = androidx.compose.ui.graphics.drawscope.Stroke(1.5.dp.toPx())
                                )
                            }
                        }
                        "pattern_builder", "number_pattern" -> if (positions.size >= 2) {
                            positions.zipWithNext().forEach { (a,b) -> drawLine(Color(0xFF83B695),Offset(a.x*size.width,a.y*size.height),Offset(b.x*size.width,b.y*size.height),2.dp.toPx()) }
                        }
                        "measure_length", "motion_track" -> {
                            drawLine(Color(0xFF91B9A0),Offset(size.width*.06f,size.height*.74f),Offset(size.width*.94f,size.height*.74f),3.dp.toPx())
                            if(scene=="motion_track") drawCircle(Color(0xFFE56B6F),8.dp.toPx(),Offset(size.width*(.1f+.78f*pulse),size.height*.74f))
                            for (i in 0..20) {
                                val x=size.width*(.06f+i*.044f)
                                val tick=if(i%5==0) 15.dp.toPx() else 7.dp.toPx()
                                drawLine(Color(0xFF578368),Offset(x,size.height*.74f-tick/2),Offset(x,size.height*.74f+tick/2),1.dp.toPx())
                            }
                        }
                        "thermometer_lab", "temperature_compare" -> {
                            drawLine(Color(0xFF91B9A0),Offset(size.width*.5f,size.height*.15f),Offset(size.width*.5f,size.height*.82f),10.dp.toPx())
                            drawCircle(Color(0xFFE56B6F),15.dp.toPx(),Offset(size.width*.5f,size.height*(.82f-heatLevel*.60f)))
                            drawCircle(Color(0xFFE56B6F),11.dp.toPx(),Offset(size.width*.5f,size.height*.82f))
                        }
                        "integer_line" -> {
                            drawLine(Color(0xFF91B9A0), Offset(size.width*.06f,size.height*.78f), Offset(size.width*.94f,size.height*.78f), 3.dp.toPx())
                            for (i in 0..10) drawLine(Color(0xFF91B9A0), Offset(size.width*(.08f+i*.084f),size.height*.73f), Offset(size.width*(.08f+i*.084f),size.height*.83f), 1.dp.toPx())
                        }
                        "point_marker" -> if (positions.isNotEmpty()) {
                            val p = positions[0]
                            drawCircle(Color(0xFF24734B), 7.dp.toPx(), Offset(p.x*size.width,p.y*size.height))
                        }
                        "line_segment" -> if (positions.size >= 2) {
                            val a = positions[0]; val b = positions[1]
                            drawLine(Color(0xFF24734B), Offset(a.x*size.width,a.y*size.height), Offset(b.x*size.width,b.y*size.height), 3.dp.toPx())
                            drawCircle(Color(0xFF24734B), 6.dp.toPx(), Offset(a.x*size.width,a.y*size.height))
                            drawCircle(Color(0xFF24734B), 6.dp.toPx(), Offset(b.x*size.width,b.y*size.height))
                        }
                        "line" -> if (positions.size >= 2) {
                            val y = ((positions[0].y + positions[1].y) / 2f) * size.height
                            drawLine(Color(0xFF24734B), Offset(size.width*.08f,y), Offset(size.width*.92f,y), 3.dp.toPx())
                            drawLine(Color(0xFF24734B), Offset(size.width*.08f,y), Offset(size.width*.16f,y-7.dp.toPx()), 2.dp.toPx())
                            drawLine(Color(0xFF24734B), Offset(size.width*.08f,y), Offset(size.width*.16f,y+7.dp.toPx()), 2.dp.toPx())
                            drawLine(Color(0xFF24734B), Offset(size.width*.92f,y), Offset(size.width*.84f,y-7.dp.toPx()), 2.dp.toPx())
                            drawLine(Color(0xFF24734B), Offset(size.width*.92f,y), Offset(size.width*.84f,y+7.dp.toPx()), 2.dp.toPx())
                        }
                        "ray" -> if (positions.size >= 2) {
                            val a = positions[0]; val b = positions[1]
                            val start = Offset(a.x*size.width,a.y*size.height)
                            val tip = Offset((b.x + .18f).coerceAtMost(.96f)*size.width,b.y*size.height)
                            drawLine(Color(0xFF24734B), start, tip, 3.dp.toPx())
                            drawCircle(Color(0xFF24734B), 6.dp.toPx(), start)
                            drawLine(Color(0xFF24734B), tip, Offset(tip.x-10.dp.toPx(),tip.y-6.dp.toPx()), 2.dp.toPx())
                            drawLine(Color(0xFF24734B), tip, Offset(tip.x-10.dp.toPx(),tip.y+6.dp.toPx()), 2.dp.toPx())
                        }
                        "line_ray_segment" -> {
                            val color = Color(0xFF24734B)
                            val x0 = size.width*.28f; val x1 = size.width*.60f; val x2 = size.width*.86f
                            val y1 = size.height*.24f; val y2 = size.height*.51f; val y3 = size.height*.78f
                            drawLine(color, Offset(x0,y1), Offset(x1,y1), 3.dp.toPx())
                            drawCircle(color, 5.dp.toPx(), Offset(x0,y1)); drawCircle(color, 5.dp.toPx(), Offset(x1,y1))
                            drawLine(color, Offset(x0,y2), Offset(x2,y2), 3.dp.toPx())
                            drawCircle(color, 5.dp.toPx(), Offset(x0,y2))
                            drawLine(color, Offset(x2,y2), Offset(x2-10.dp.toPx(),y2-6.dp.toPx()), 2.dp.toPx())
                            drawLine(color, Offset(x2,y2), Offset(x2-10.dp.toPx(),y2+6.dp.toPx()), 2.dp.toPx())
                            drawLine(color, Offset(size.width*.08f,y3), Offset(size.width*.92f,y3), 3.dp.toPx())
                            drawLine(color, Offset(size.width*.08f,y3), Offset(size.width*.16f,y3-6.dp.toPx()), 2.dp.toPx())
                            drawLine(color, Offset(size.width*.08f,y3), Offset(size.width*.16f,y3+6.dp.toPx()), 2.dp.toPx())
                            drawLine(color, Offset(size.width*.92f,y3), Offset(size.width*.84f,y3-6.dp.toPx()), 2.dp.toPx())
                            drawLine(color, Offset(size.width*.92f,y3), Offset(size.width*.84f,y3+6.dp.toPx()), 2.dp.toPx())
                        }
                        "angle_builder", "angle_classifier" -> if (positions.size >= 3) {
                            val v=positions[0]
                            val a=positions[1]
                            val b=positions[2]
                            positions.drop(1).take(2).forEach { p -> drawLine(Color(0xFF24734B), Offset(v.x*size.width,v.y*size.height), Offset(p.x*size.width,p.y*size.height), 3.dp.toPx()) }
                            val dxA = a.x - v.x
                            val dyA = a.y - v.y
                            val dxB = b.x - v.x
                            val dyB = b.y - v.y
                            val angleA = Math.toDegrees(kotlin.math.atan2(dyA.toDouble(), dxA.toDouble())).toFloat()
                            val angleB = Math.toDegrees(kotlin.math.atan2(dyB.toDouble(), dxB.toDouble())).toFloat()
                            var sweep = angleB - angleA
                            if (sweep > 180f) sweep -= 360f
                            if (sweep < -180f) sweep += 360f
                            val arcRadius = 24.dp.toPx()
                            drawArc(
                                color = Color(0xFF6B8DE3),
                                startAngle = angleA,
                                sweepAngle = sweep,
                                useCenter = false,
                                topLeft = Offset(v.x*size.width - arcRadius, v.y*size.height - arcRadius),
                                size = androidx.compose.ui.geometry.Size(arcRadius*2, arcRadius*2),
                                style = androidx.compose.ui.graphics.drawscope.Stroke(2.dp.toPx())
                            )
                            drawCircle(Color(0xFF24734B), 5.dp.toPx(), Offset(v.x*size.width,v.y*size.height))
                        }
                        "symmetry_mirror" -> drawLine(Color(0xFF7F9BFF), Offset(size.width*.5f,0f), Offset(size.width*.5f,size.height), 2.dp.toPx())
                        "area_grid" -> {
                            for (i in 1..8) drawLine(Color(0xFFE2E8F0),Offset(size.width*i/9f,0f),Offset(size.width*i/9f,size.height),1.dp.toPx())
                            for (i in 1..4) drawLine(Color(0xFFE2E8F0),Offset(0f,size.height*i/5f),Offset(size.width,size.height*i/5f),1.dp.toPx())
                        }
                        else -> {
                            drawLine(Color(0xFFCBD5E1),Offset(size.width*.05f,size.height*.86f),Offset(size.width*.95f,size.height*.86f),2.dp.toPx())
                            drawCircle(Color(0xFF4169E1),6.dp.toPx(),Offset(size.width*(.1f+.78f*pulse),size.height*.86f))
                        }
                    }
                }
                if (!compact) items.forEachIndexed { index, item ->
                    val p=positions[index]
                    Column(
                        Modifier.offset { IntOffset((p.x*(w-68.dp).toPx()).roundToInt(),(p.y*(h-62.dp).toPx()).roundToInt()) }
                            .width(68.dp)
                            .pointerInput(key,index,w,h) {
                                detectDragGestures { change, drag ->
                                    change.consume()
                                    val maxX=(w-68.dp).toPx().coerceAtLeast(1f)
                                    val maxY=(h-62.dp).toPx().coerceAtLeast(1f)
                                    positions=positions.toMutableList().also { list ->
                                        val old=list[index]
                                        var next=Offset((old.x+drag.x/maxX).coerceIn(0f,1f),(old.y+drag.y/maxY).coerceIn(0f,1f))
                                        if (scene=="fraction_builder" && index>0 && kotlin.math.abs(next.y-list[0].y)<.10f && kotlin.math.abs(next.x-list[0].x)<.16f) {
                                            next=Offset((list[0].x+index*.09f).coerceIn(0f,1f),list[0].y)
                                        }
                                        list[index]=next
                                    }
                                    feedback=when(scene) {
                                        "number_pattern" -> "These are square numbers: 1×1, 2×2, 3×3 and 4×4. The gaps are +3, +5 and +7."
                                        "magnet_test" -> if (magnetic) "Attraction! Iron and steel are pulled toward the magnet; wood is not." else "Bring an iron or steel object close to the magnet."
                                        "fraction_builder" -> "Move equal pieces together. Each piece is one-quarter of the same whole."
                                        "angle_builder", "angle_classifier" -> "The angle is about $angle°. Move Ray B to make it wider or narrower."
                                        "integer_line" -> "Numbers to the left are smaller; numbers to the right are greater."
                                        "area_grid" -> "Count the unit squares covered by the shape to estimate its area."
                                        "symmetry_mirror" -> "Compare the two sides of the mirror line."
                                        else -> caption
                                    }
                                }
                            },
                        horizontalAlignment=Alignment.CenterHorizontally
                    ) {
                        Surface(color=if(scene=="fraction_builder" && item.name=="1/4") Color(0xFFCBD5E1) else Color(0xFFF8FAFC),shape=RoundedCornerShape(12.dp),border=BorderStroke(1.dp,Color(0xFFDCE3ED))) {
                            Text(item.icon,Modifier.padding(horizontal=10.dp,vertical=5.dp),fontSize=24.sp)
                        }
                        Text(item.name,color=TutorDeep,fontSize=10.sp,maxLines=1)
                    }
                }
            }
            if (compact) {
                val currentStep = steps?.optJSONObject(displayStep)
                Text(
                    currentStep?.optString("text").orEmpty().ifBlank { caption },
                    color = TutorDeep,
                    fontSize = 10.sp,
                    lineHeight = 14.sp,
                    maxLines = 2
                )
                val sourceRef = lesson.optJSONArray("source_refs")?.optJSONObject(0)
                if (sourceRef != null) {
                    val pageStart = sourceRef.optInt("page_start", 0)
                    val pageEnd = sourceRef.optInt("page_end", pageStart)
                    val pageLabel = if (pageStart > 0 && pageEnd > pageStart) "Textbook pp. $pageStart–$pageEnd" else if (pageStart > 0) "Textbook p. $pageStart" else "Textbook reference"
                    Text(pageLabel, color = TutorGreen, fontSize = 9.sp, maxLines = 1)
                }
            } else {
            if (scene in listOf("angle_builder", "angle_classifier")) Text("Current angle: $angle°", color=TutorGreen, fontSize=12.sp, fontWeight=FontWeight.Bold)
            if (scene=="measure_length" && positions.size>=2) Text("Measured length: ${(kotlin.math.abs(positions[1].x-positions[0].x)*100).toInt()} model units", color=TutorGreen, fontSize=12.sp, fontWeight=FontWeight.Bold)
            if (scene=="motion_track") Text("Watch the toy move along the measured track. Drag the toy to compare positions.", color=TutorGreen, fontSize=11.sp)
            if (scene=="bar_chart") {
                Text("Adjust Group C and compare the bar heights.", color=TutorGreen, fontSize=11.sp)
                Slider(value=chartValue, onValueChange={chartValue=it}, valueRange = 0.1f..0.9f, colors=SliderDefaults.colors(thumbColor=TutorGreen, activeTrackColor=TutorGreen))
            }
            if (scene=="magnet_test") Text(if(magnetic) "Magnetic attraction detected" else "Try bringing iron or steel close to the magnet", color=TutorGreen, fontSize=11.sp)
            if (scene in listOf("particle_states", "phase_change", "evap_condense")) {
                Text("Heat level: ${(heatLevel*100).toInt()}%", color=TutorGreen, fontSize=12.sp, fontWeight=FontWeight.Bold)
                Slider(value=heatLevel, onValueChange={ heatLevel=it }, valueRange=0f..1f, colors=SliderDefaults.colors(thumbColor=TutorGreen, activeTrackColor=TutorGreen))
                Text(when { heatLevel < .33f -> "Solid: particles stay close and mainly vibrate."; heatLevel < .67f -> "Liquid: particles stay close but can move past each other."; else -> "Gas: particles spread out and move freely." }, color=TutorDeep, fontSize=11.sp)
            }
            if (scene in listOf("thermometer_lab", "temperature_compare")) {
                Text("Temperature scale: ${(heatLevel*100).toInt()}° (model units)", color=TutorGreen, fontSize=12.sp, fontWeight=FontWeight.Bold)
                Slider(value=heatLevel, onValueChange={ heatLevel=it }, valueRange=0f..1f, colors=SliderDefaults.colors(thumbColor=TutorGreen, activeTrackColor=TutorGreen))
                Text("Move the slider and watch the thermometer level change.", color=TutorDeep, fontSize=11.sp)
            }
            Text(feedback, color=TutorDeep, fontSize=12.sp, lineHeight=16.sp)
            Text(caption, color=TutorGrey, fontSize=11.sp, lineHeight=15.sp)
            val sourceRefs = lesson.optJSONArray("source_refs")
            val sourceRef = sourceRefs?.optJSONObject(0)
            if (sourceRef != null) {
                val pageStart = sourceRef.optInt("page_start", 0)
                val pageEnd = sourceRef.optInt("page_end", pageStart)
                val edition = sourceRef.optString("edition", "")
                val bookTitle = when (lesson.optString("subject")) {
                    "Mathematics" -> "NCERT Ganita Prakash"
                    "Science" -> "NCERT Curiosity"
                    else -> "NCERT textbook"
                }
                Text(
                    "$bookTitle · textbook reference",
                    color = TutorGreen,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.SemiBold
                )
                val pageLabel = if (pageStart > 0 && pageEnd > 0 && pageEnd != pageStart) {
                    "Pages $pageStart–$pageEnd"
                } else if (pageStart > 0) {
                    "Page $pageStart"
                } else {
                    "Chapter reference"
                }
                Text(
                    listOf(pageLabel, edition).filter { it.isNotBlank() }.joinToString(" · "),
                    color = TutorGrey,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
            if (steps != null && steps.length()>0) {
                val current=steps.optJSONObject(activeStep.coerceIn(0,steps.length()-1))
                Text("Step ${activeStep+1}/$stepCount · ${current?.optString("title","Try")}: ${current?.optString("text","Explore the objects.")}", color=TutorGreen, fontSize=11.sp)
                Row(horizontalArrangement=Arrangement.spacedBy(8.dp), verticalAlignment=Alignment.CenterVertically) {
                    OutlinedButton(onClick={setActiveStep(activeStep-1)}, enabled=activeStep>0) { Text("Previous") }
                    Button(onClick={setActiveStep(activeStep+1)}, enabled=activeStep<stepCount-1, colors=ButtonDefaults.buttonColors(containerColor=TutorGreen)) { Text("Next step") }
                }
            }
            val challenge=lesson.optJSONObject("challenge")
            if(challenge!=null && challenge.optString("question").isNotBlank()) Text("Try this: ${challenge.optString("question")}", color=TutorDeep, fontSize=12.sp, fontWeight=FontWeight.SemiBold)
            }
        }
    }
}

private enum class LessonVisualKind { FRACTIONS, ADDITION, PHOTOSYNTHESIS, WATER_CYCLE, SOLAR_SYSTEM, NONE }

private fun chooseLessonVisual(text: String): LessonVisualKind {
    val value = text.lowercase()
    return when {
        listOf("photosynthesis", "chlorophyll", "carbon dioxide", "sunlight", "சேர்க்கை ஒளி").any { it in value } -> LessonVisualKind.PHOTOSYNTHESIS
        listOf("water cycle", "evaporation", "condensation", "precipitation", "ஆவியாதல்").any { it in value } -> LessonVisualKind.WATER_CYCLE
        listOf("solar system", "planet", "orbit", "பூமி", "சூரிய குடும்பம்").any { it in value } -> LessonVisualKind.SOLAR_SYSTEM
        listOf("fraction", "one-half", "one half", "quarter", "numerator", "denominator", "பின்னம்").any { it in value } -> LessonVisualKind.FRACTIONS
        Regex("""\b(addition|plus|sum|altogether|equals|\d+\s*\+\s*\d+|கூட்டல்)\b""").containsMatchIn(value) -> LessonVisualKind.ADDITION
        else -> LessonVisualKind.NONE
    }
}

@Composable
private fun DatabaseLessonVisual(lesson: JSONObject) {
    val array = lesson.optJSONArray("steps")
    val steps = remember(lesson) {
        if (array == null) emptyList() else (0 until array.length()).mapNotNull { array.optJSONObject(it) }
    }
    if (steps.isEmpty()) return
    val transition = rememberInfiniteTransition(label = "database-lesson")
    val progress by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(animation = tween(2200), repeatMode = RepeatMode.Reverse),
        label = "database-lesson-progress"
    )
    val visibleSteps = steps.take(5)
    val activeIndex = (progress * visibleSteps.size).toInt().coerceIn(0, visibleSteps.lastIndex)
    Surface(
        modifier = Modifier.fillMaxWidth().padding(top = 4.dp),
        color = Color(0xFFF8FAFC),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, Color(0xFFDCE3ED))
    ) {
        Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
            Text("SEE IT HAPPEN", color = TutorGreen, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            Text(lesson.optString("title", lesson.optString("topic", "Explore this idea")), color = TutorDeep, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(3.dp), verticalAlignment = Alignment.CenterVertically) {
                visibleSteps.forEachIndexed { index, step ->
                    if (index > 0) Text("→", color = TutorGreen, fontSize = 13.sp)
                    Column(
                        Modifier.weight(1f).background(if (index == activeIndex) Color.White else Color(0xFFEAF0FF), RoundedCornerShape(10.dp)).padding(horizontal = 3.dp, vertical = 7.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(step.optString("icon", "✦"), fontSize = 20.sp, maxLines = 1)
                        Text(step.optString("label", step.optString("title", "Step " + (index + 1))), color = TutorDeep, fontSize = 9.sp, lineHeight = 11.sp, maxLines = 2, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
                    }
                }
            }
            Text(lesson.optString("caption", lesson.optString("description", "")), color = TutorGrey, fontSize = 12.sp, lineHeight = 17.sp)
            val activeStep = visibleSteps[activeIndex]
            val stepExplanation = activeStep.optString("text", activeStep.optString("description", ""))
            if (stepExplanation.isNotBlank()) Text(stepExplanation, color = TutorDeep, fontSize = 12.sp, lineHeight = 17.sp)
            Text("Live concept animation · matched from the lesson database", color = TutorGrey, fontSize = 9.sp)
        }
    }
}

@Composable
private fun LessonVisual(explanation: String, subject: String) {
    val kind = chooseLessonVisual(explanation)
    if (kind == LessonVisualKind.NONE) return
    val transition = rememberInfiniteTransition(label = "lesson-visual")
    val progress by transition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(animation = tween(1800), repeatMode = RepeatMode.Reverse),
        label = "lesson-progress"
    )
    Surface(
        modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
        color = Color(0xFFF8FAFC),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, Color(0xFFDCE3ED))
    ) {
        Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("SEE IT HAPPEN", color = TutorGreen, fontSize = 10.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
            when (kind) {
                LessonVisualKind.FRACTIONS -> {
                    Text("One whole, split into equal parts", color = TutorDeep, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                        repeat(4) { index ->
                            Box(
                                Modifier.weight(1f).height(48.dp)
                                    .background(if (index == (progress * 3.99f).toInt()) TutorGreen else Color.White, RoundedCornerShape(9.dp))
                                    .padding(4.dp),
                                contentAlignment = Alignment.Center
                            ) { Text(if (index == (progress * 3.99f).toInt()) "¼" else "¼", color = if (index == (progress * 3.99f).toInt()) Color.White else TutorDeep, fontWeight = FontWeight.Bold) }
                        }
                    }
                    Text("Each piece is one-quarter. Equal pieces make the whole.", color = TutorGrey, fontSize = 12.sp)
                }
                LessonVisualKind.ADDITION -> {
                    Text("Watch the groups join together", color = TutorDeep, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(5.dp), modifier = Modifier.fillMaxWidth()) {
                        repeat(3) { Box(Modifier.size(25.dp).background(TutorGreen, CircleShape), contentAlignment = Alignment.Center) { Text("•", color = Color.White, fontSize = 20.sp) } }
                        Text("+", color = TutorDeep, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                        repeat(2) { Box(Modifier.size(25.dp).background(Color(0xFFE8A23A), CircleShape), contentAlignment = Alignment.Center) { Text("•", color = Color.White, fontSize = 20.sp) } }
                        Text("=", color = TutorDeep, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                        Box(Modifier.size(30.dp).background(TutorGreen.copy(alpha = 0.65f + progress * 0.35f), CircleShape), contentAlignment = Alignment.Center) { Text("5", color = Color.White, fontWeight = FontWeight.Bold) }
                    }
                    Text("Count all the objects after the groups join.", color = TutorGrey, fontSize = 12.sp)
                }
                LessonVisualKind.PHOTOSYNTHESIS -> {
                    Text("How a plant makes its food", color = TutorDeep, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceEvenly, modifier = Modifier.fillMaxWidth()) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("☀️", fontSize = 25.sp); Text("Sunlight", color = TutorDeep, fontSize = 10.sp) }
                        Text("→", color = TutorGreen, fontSize = 20.sp)
                        Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("🌱", fontSize = 34.sp); Text("Plant", color = TutorDeep, fontSize = 10.sp) }
                        Text("→", color = TutorGreen, fontSize = 20.sp)
                        Column(horizontalAlignment = Alignment.CenterHorizontally) { Text("🍃", fontSize = 27.sp); Text("Food + oxygen", color = TutorDeep, fontSize = 10.sp) }
                    }
                    Text("Leaves use sunlight, water and carbon dioxide to make food.", color = TutorGrey, fontSize = 12.sp)
                }
                LessonVisualKind.WATER_CYCLE -> {
                    Text("Water keeps moving around Earth", color = TutorDeep, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                    Row(horizontalArrangement = Arrangement.spacedBy(5.dp), verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                        listOf("🌊", "⬆️", "☁️", "🌧️").forEachIndexed { index, symbol ->
                            if (index > 0) Text("→", color = TutorGreen, fontSize = 15.sp)
                            Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(symbol, fontSize = 24.sp, modifier = Modifier.alpha(if (index == (progress * 3.99f).toInt()) 1f else 0.65f))
                                Text(listOf("Water", "Vapour", "Clouds", "Rain")[index], color = TutorDeep, fontSize = 10.sp)
                            }
                        }
                    }
                    Text("The Sun warms water, vapour forms clouds, and rain returns water to Earth.", color = TutorGrey, fontSize = 12.sp)
                }
                LessonVisualKind.SOLAR_SYSTEM -> {
                    Text("Planets travel around the Sun", color = TutorDeep, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                    Row(horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
                        Text("☀️", fontSize = 28.sp)
                        repeat(4) { index ->
                            Box(Modifier.size((12 + index * 4).dp).background(
                                listOf(Color(0xFFB7A18A), Color(0xFF5B9BD5), Color(0xFF65A86E), Color(0xFFD59B63))[index].copy(alpha = 0.65f + progress * 0.35f),
                                CircleShape
                            ))
                        }
                    }
                    Text("Each planet follows its own path, called an orbit, around the Sun.", color = TutorGrey, fontSize = 12.sp)
                }
                LessonVisualKind.NONE -> Unit
            }
        }
    }
}

@Composable
private fun SpeakingCaption(text: String, active: Boolean, segmentKey: Int) {
    val words = remember(text) { text.trim().split(Regex("\\s+")).filter { it.isNotBlank() } }
    var currentWord by remember(text, segmentKey) { mutableIntStateOf(-1) }
    LaunchedEffect(text, active, segmentKey) {
        currentWord = if (active) 0 else -1
        if (active && words.isNotEmpty()) {
            val perWord = (24000L / words.size).coerceIn(180L, 650L)
            for (i in words.indices) { currentWord = i; delay(perWord) }
            currentWord = -1
        }
    }
    Text(buildAnnotatedString {
        words.forEachIndexed { index, word ->
            if (index > 0) append(" ")
            if (active && index == currentWord) withStyle(SpanStyle(background = Color(0xFFEAF0FF), color = TutorDeep, fontWeight = FontWeight.Bold)) { append(word) } else append(word)
        }
    }, color = TutorDeep, fontSize = 16.sp, lineHeight = 24.sp)
}

@Composable
internal fun TutorScreen(
    grade: Int,
    board: String,
    medium: String,
    appLanguage: String,
    studentName: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    setupOnly: Boolean = false,
    onStartTeaching: () -> Unit = {}
) {
    val context = LocalContext.current
    val sessionPrefs = remember(context) { context.getSharedPreferences("padippupal_tutor_sessions", 0) }
    val sessionKey = remember(grade, board, studentName) {
        "session_${grade}_${board.trim().lowercase().hashCode()}_${studentName.trim().lowercase().hashCode()}"
    }
    val todayKey = LocalDate.now().toString()
    val savedSession = remember(sessionPrefs, sessionKey, todayKey) {
        runCatching {
            val raw = sessionPrefs.getString(sessionKey, null)
            val parsed = if (raw.isNullOrBlank()) JSONObject() else JSONObject(raw)
            if (parsed.optString("date") == todayKey) parsed else JSONObject()
        }.getOrDefault(JSONObject())
    }
    val messages = remember(sessionPrefs, sessionKey, todayKey, appLanguage, studentName) {
        val restored = mutableStateListOf<TutorMessage>()
        val storedMessages = savedSession.optJSONArray("messages")
        if (storedMessages != null) {
            for (i in 0 until storedMessages.length()) {
                val item = storedMessages.optJSONObject(i) ?: continue
                val role = item.optString("role")
                val content = item.optString("content")
                if (role in listOf("user", "assistant") && content.isNotBlank()) {
                    restored.add(TutorMessage(role, cleanTutorDisplayText(content)))
                }
            }
        }
        if (restored.isEmpty()) {
            restored.add(TutorMessage("assistant", when (appLanguage) {
                "Tanglish" -> "Hi" + (if (studentName.isBlank()) "" else ", " + studentName) + "! Namma selected topic-a clear-a examples-oda kathukkalaam. Eppo venaalum kelvi kelunga."
                "தமிழ்" -> "வணக்கம்" + (if (studentName.isBlank()) "" else ", " + studentName) + "! தேர்ந்தெடுத்த தலைப்பை எளிய விளக்கங்களும் எடுத்துக்காட்டுகளும் கொண்டு கற்றுக்கொள்வோம். எப்போது வேண்டுமானாலும் கேள்வி கேளுங்கள்."
                else -> "Hi" + (if (studentName.isBlank()) "" else ", " + studentName) + "! I'll explain the selected topic clearly with examples. You can ask me questions whenever you need."
            }))
        }
        restored
    }
    var input by remember { mutableStateOf("") }
    var subject by remember { mutableStateOf(savedSession.optString("subject", "General")) }
    var chapter by remember { mutableStateOf(savedSession.optString("chapter", "")) }
    var topic by remember { mutableStateOf(savedSession.optString("topic", "")) }
    var chapterMenuExpanded by remember { mutableStateOf(false) }
    var topicMenuExpanded by remember { mutableStateOf(false) }
    var showLessonSettings by remember(setupOnly) { mutableStateOf(setupOnly) }
    var chapterOptions by remember { mutableStateOf<List<Pair<String, List<String>>>>(emptyList()) }
    var outlineLoading by remember { mutableStateOf(false) }
    var loading by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("") }
    var speakReplies by remember { mutableStateOf(true) }
    var preferOnDeviceVoice by remember(context) {
        mutableStateOf(context.getSharedPreferences("padippupal_settings", 0).getBoolean("prefer_on_device_voice", false))
    }
    var speechActive by remember { mutableStateOf(false) }
    var speechGeneration by remember { mutableIntStateOf(0) }
    var speechPlaybackObserved by remember { mutableStateOf(false) }
    var speechStartCallback by remember { mutableStateOf<(() -> Unit)?>(null) }
    var speechCompletion by remember { mutableStateOf<(() -> Unit)?>(null) }
    var liveSegments by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var liveInteractiveLesson by remember { mutableStateOf<JSONObject?>(null) }
    var liveCaption by remember { mutableStateOf("") }
    var liveWordIndex by remember { mutableIntStateOf(0) }
    var speechWordStarts by remember { mutableStateOf<List<Int>>(emptyList()) }
    // A stopped/replaced TTS utterance may still deliver a late callback. Only the
    // currently active utterance is allowed to move highlights or advance a lesson.
    var activeTtsUtteranceId by remember { mutableStateOf("") }
    // Index in the original displayed segment when device TTS resumes from a cloud
    // audio failure. Native TTS range offsets are relative to the resumed suffix.
    var speechWordIndexOffset by remember { mutableIntStateOf(0) }
    // Some Android TTS engines emit only an initial onRangeStart callback.
    // Keep a timestamp so elapsed-time highlighting can take over if callbacks stall.
    var lastNativeRangeAt by remember { mutableLongStateOf(0L) }
    var hostedWordTimings by remember { mutableStateOf<List<Pair<Long, Long>>>(emptyList()) }
    var liveVisualAction by remember { mutableStateOf("") }
    var liveVisualActionType by remember { mutableStateOf("none") }
    var liveVisualTarget by remember { mutableStateOf("") }
    var liveSegmentIndex by remember { mutableIntStateOf(0) }
    var liveLessonActive by remember { mutableStateOf(false) }
    var livePaused by remember { mutableStateOf(false) }
    var awaitingUnderstanding by remember { mutableStateOf(false) }
    var currentCheckpoint by remember { mutableStateOf("") }
    var voiceReady by remember { mutableStateOf(false) }
    var selectedLanguage by remember { mutableStateOf(savedSession.optString("language", appLanguage)) }
    var listening by remember { mutableStateOf(false) }
    val speechRecognizer = remember(context) {
        if (SpeechRecognizer.isRecognitionAvailable(context)) SpeechRecognizer.createSpeechRecognizer(context) else null
    }

    fun startVoiceInput() {
        val recognizer = speechRecognizer
        if (recognizer == null) {
            status = "Voice input isn't available on this phone. You can type your question instead."
            return
        }
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, when (selectedLanguage) {
                "தமிழ்" -> "ta-IN"
                "Tanglish" -> "en-IN"
                else -> "en-IN"
            })
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Ask your tutor a question")
        }
        runCatching {
            listening = true
            status = "Listening… speak your question."
            recognizer.startListening(intent)
        }.onFailure {
            listening = false
            status = "Couldn't start voice input. Please try again or type your question."
        }
    }

    val voicePermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) startVoiceInput()
        else status = "Microphone permission is needed for voice questions. You can still type."
    }

    DisposableEffect(speechRecognizer) {
        speechRecognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: android.os.Bundle?) { listening = true }
            override fun onBeginningOfSpeech() { listening = true }
            override fun onRmsChanged(rmsdB: Float) {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEndOfSpeech() { listening = false; status = "Got it — review your words, then tap send." }
            override fun onError(error: Int) {
                listening = false
                status = if (error == SpeechRecognizer.ERROR_NO_MATCH || error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT) {
                    "I didn't catch that. Tap the microphone and try again."
                } else {
                    "Voice input stopped. Please try again or type your question."
                }
            }
            override fun onResults(results: android.os.Bundle?) {
                listening = false
                val spoken = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull().orEmpty()
                if (spoken.isNotBlank()) {
                    input = listOf(input.trim(), spoken).filter { it.isNotBlank() }.joinToString(" ")
                    status = "Voice question added — review it and tap send."
                } else status = "I didn't catch that. Tap the microphone and try again."
            }
            override fun onPartialResults(partialResults: android.os.Bundle?) {
                val spoken = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.firstOrNull()
                if (!spoken.isNullOrBlank()) status = "Hearing: $spoken"
            }
            override fun onEvent(eventType: Int, params: android.os.Bundle?) {}
        })
        onDispose {
            speechRecognizer?.cancel()
            speechRecognizer?.destroy()
        }
    }
    fun loadCurriculumOutline(forSubject: String, attempt: Int = 1) {
        if (forSubject == "General") {
            chapterOptions = emptyList()
            outlineLoading = false
            return
        }
        outlineLoading = true
        tutorExecutor.execute {
            val result = runCatching {
                val base = BuildConfig.CURRICULUM_API_BASE_URL.trim().trimEnd('/')
                val query = "board=" + URLEncoder.encode(board, "UTF-8") +
                    "&class_level=$grade&subject=" + URLEncoder.encode(forSubject, "UTF-8") +
                    "&medium=" + URLEncoder.encode(medium, "UTF-8")
                val connection = URL("$base/curriculum/outline?$query").openConnection() as HttpURLConnection
                connection.connectTimeout = 7000
                connection.readTimeout = 10000
                try {
                    val code = connection.responseCode
                    val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                    val body = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()
                    if (code !in 200..299) throw IllegalStateException("Curriculum outline unavailable")
                    val chaptersJson = JSONObject(body).optJSONArray("chapters") ?: JSONArray()
                    (0 until chaptersJson.length()).mapNotNull { index ->
                        val item = chaptersJson.optJSONObject(index) ?: return@mapNotNull null
                        val title = item.optString("title").trim()
                        if (title.isBlank()) return@mapNotNull null
                        val topicsJson = item.optJSONArray("topics") ?: JSONArray()
                        val topics = (0 until topicsJson.length()).mapNotNull { topicIndex ->
                            val rawTopic = topicsJson.opt(topicIndex)
                            val topicTitle = when (rawTopic) {
                                is JSONObject -> rawTopic.optString("title").ifBlank {
                                    rawTopic.optString("name")
                                }
                                is String -> {
                                    val trimmed = rawTopic.trim()
                                    if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
                                        runCatching {
                                            val parsed = JSONObject(trimmed)
                                            parsed.optString("title").ifBlank { parsed.optString("name") }
                                        }.getOrDefault(trimmed)
                                    } else trimmed
                                }
                                else -> ""
                            }.trim()
                            topicTitle.takeIf { it.isNotBlank() }
                        }.distinct().take(30)
                        title to topics
                    }
                } finally {
                    connection.disconnect()
                }
            }
            tutorMainHandler.post {
                // A cold backend can briefly return an error/empty body while waking.
                // Retry boundedly instead of presenting a transient network failure as
                // a valid curriculum with no chapters. Ignore stale results if the
                // learner has changed subjects while the request was in flight.
                if (subject != forSubject) return@post
                val loaded = result.getOrNull().orEmpty()
                if (loaded.isNotEmpty()) {
                    chapterOptions = loaded
                    outlineLoading = false
                } else if (attempt < 3) {
                    outlineLoading = true
                    status = "Reconnecting to the curriculum…"
                    tutorMainHandler.postDelayed({
                        if (subject == forSubject) loadCurriculumOutline(forSubject, attempt + 1)
                    }, 700L * attempt)
                } else {
                    chapterOptions = emptyList()
                    outlineLoading = false
                    status = "Couldn't load the chapter list. Check your connection and tap Change to try again."
                }
            }
        }
    }

    var restoringSelection by remember { mutableStateOf(true) }
    LaunchedEffect(subject) {
        if (restoringSelection) {
            restoringSelection = false
        } else {
            chapter = ""
            topic = ""
        }
        loadCurriculumOutline(subject)
    }

    LaunchedEffect(messages.size, messages.lastOrNull()?.content, subject, chapter, topic, selectedLanguage) {
        val storedMessages = JSONArray()
        messages.takeLast(80).forEach { message ->
            storedMessages.put(JSONObject().put("role", message.role).put("content", message.content))
        }
        val snapshot = JSONObject()
            .put("date", todayKey)
            .put("subject", subject)
            .put("chapter", chapter)
            .put("topic", topic)
            .put("language", selectedLanguage)
            .put("messages", storedMessages)
        sessionPrefs.edit().putString(sessionKey, snapshot.toString()).apply()
    }

    LaunchedEffect(chapter, topic, selectedLanguage) {
        if (messages.size == 1 && messages.firstOrNull()?.role == "assistant") {
            val greeting = when (selectedLanguage) {
                "Tanglish" -> when {
                    topic.isNotBlank() -> "Seri! Ippo $topic-a full-a examples-oda kathukkalaam. Edhaavadhu doubt irundha kelunga."
                    chapter.isNotBlank() -> "$chapter chapter open panniyachu. Endha topic-a first kathukkanum?"
                    else -> "Hi" + (if (studentName.isBlank()) "" else ", $studentName") + "! Namma onna konjam konjama kathukkalaam. Enna concept purinjukkanum?"
                }
                "தமிழ்" -> when {
                    topic.isNotBlank() -> "சரி! இப்போது $topic-ஐ முழுமையாக எடுத்துக்காட்டுகளுடன் கற்போம். ஏதேனும் சந்தேகம் இருந்தால் கேளுங்கள்."
                    chapter.isNotBlank() -> "$chapter அத்தியாயத்தைத் தேர்ந்தெடுத்துள்ளோம். எந்தத் தலைப்பை முதலில் கற்கலாம்?"
                    else -> "வணக்கம்" + (if (studentName.isBlank()) "" else ", $studentName") + "! நிதானமாக ஒவ்வொரு படியாகவும் கற்றுக்கொள்ளலாம். இன்று என்ன புரிந்துகொள்ள வேண்டும்?"
                }
                else -> when {
                    topic.isNotBlank() -> "Let's learn $topic. What would you like me to explain first?"
                    chapter.isNotBlank() -> "We've opened $chapter. Which topic would you like to learn first?"
                    else -> "Hi" + (if (studentName.isBlank()) "" else ", $studentName") + "! I'm here to help. We'll take it one small step at a time. What would you like to understand today?"
                }
            }
            messages[0] = TutorMessage("assistant", greeting)
        }
    }

    var lastSources by remember { mutableStateOf<List<TutorSource>>(emptyList()) }
    val ttsState = remember { mutableStateOf<TextToSpeech?>(null) }
    val audioPlayer = remember { mutableStateOf<MediaPlayer?>(null) }

    fun finishSpeechSegment() {
        // Invalidate the per-utterance watchdog before invoking progression.
        activeTtsUtteranceId = ""
        speechGeneration += 1
        speechActive = false
        val callback = speechCompletion
        speechCompletion = null
        callback?.invoke()
    }

    DisposableEffect(context) {
        // A third-party or misconfigured TTS service can throw synchronously while
        // TextToSpeech binds to it. Never let an optional voice engine crash the
        // entire tutor screen; report the failure and keep the lesson UI usable.
        val engine = try {
            TextToSpeech(context) { result ->
                tutorMainHandler.post {
                    voiceReady = result == TextToSpeech.SUCCESS
                    if (result != TextToSpeech.SUCCESS) {
                        status = "Voice engine could not initialize. Check Android text-to-speech settings and try again."
                    }
                }
            }
        } catch (error: SecurityException) {
            voiceReady = false
            status = "Voice engine could not initialize. Check Android text-to-speech settings and try again."
            null
        } catch (error: RuntimeException) {
            voiceReady = false
            status = "Voice engine could not initialize. Check Android text-to-speech settings and try again."
            null
        }
        if (engine != null) engine.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {
                tutorMainHandler.post {
                    if (utteranceId != activeTtsUtteranceId || !speechActive) return@post
                    speechPlaybackObserved = true
                    val callback = speechStartCallback
                    speechStartCallback = null
                    callback?.invoke()
                }
            }
            override fun onDone(utteranceId: String?) {
                tutorMainHandler.post {
                    if (utteranceId != activeTtsUtteranceId || !speechActive) return@post
                    activeTtsUtteranceId = ""
                    finishSpeechSegment()
                }
            }
            override fun onRangeStart(utteranceId: String?, start: Int, end: Int, frame: Int) {
                if (Build.VERSION.SDK_INT >= 26) {
                    tutorMainHandler.post {
                        if (utteranceId != activeTtsUtteranceId || !speechActive) return@post
                        val index = speechWordStarts.indexOfLast { it <= start }.coerceAtLeast(0)
                        speechPlaybackObserved = true
                        liveWordIndex = speechWordIndexOffset + index
                        lastNativeRangeAt = System.currentTimeMillis()
                    }
                }
            }
            @Deprecated("Deprecated in Java")
            override fun onError(utteranceId: String?) {
                tutorMainHandler.post {
                    if (utteranceId != activeTtsUtteranceId || !speechActive) return@post
                    activeTtsUtteranceId = ""
                    // A failed utterance must not be treated as completed speech:
                    // doing so auto-advances the live lesson and skips its teaching.
                    speechActive = false
                    speechStartCallback = null
                    speechCompletion = null
                    speechGeneration += 1
                    if (liveLessonActive) {
                        livePaused = true
                        status = "Voice playback failed. Check the selected speech engine, then tap Resume to retry this step."
                    } else {
                        status = "Voice playback failed. Check the selected speech engine and try again."
                    }
                }
            }
        })
        ttsState.value = engine
        onDispose {
            runCatching { engine?.stop() }
            runCatching { engine?.shutdown() }
            ttsState.value = null
            audioPlayer.value?.release()
            audioPlayer.value = null
        }
    }

    fun speakWithDeviceTts(
        text: String,
        onStarted: (() -> Unit)? = null,
        onFinished: (() -> Unit)? = null,
        initWaitStartedAt: Long = SystemClock.elapsedRealtime()
    ) {
        // Reset observations from a failed hosted-audio attempt before observing
        // the device engine's own start/completion lifecycle.
        speechPlaybackObserved = false
        activeTtsUtteranceId = ""
        speechStartCallback = onStarted
        speechCompletion = onFinished
        status = if (preferOnDeviceVoice) {
            "Using this phone's TTS engine. Choose Sherpa-ONNX Kokoro in Android text-to-speech settings for local Kokoro speech."
        } else {
            "Natural voice unavailable; using this phone's TTS engine."
        }
        val engine = ttsState.value
        // TextToSpeech(context) is asynchronous. A hosted-TTS quota failure can
        // send us to this fallback before Android has bound its TTS service.
        // Querying availableLanguages before onInit completes returns no locale
        // and falsely reports that the phone has no voice. Wait briefly for the
        // engine to become ready; never treat a not-yet-bound engine as a finished
        // utterance (which would skip the student's lesson segment).
        if (!voiceReady || engine == null) {
            val elapsed = SystemClock.elapsedRealtime() - initWaitStartedAt
            if (elapsed < 8_000L) {
                val generation = speechGeneration
                status = "Preparing this phone's voice…"
                tutorMainHandler.postDelayed({
                    if (speechActive && speechGeneration == generation) {
                        speakWithDeviceTts(text, onStarted, onFinished, initWaitStartedAt)
                    }
                }, 250L)
            } else {
                speechStartCallback = null
                speechCompletion = null
                speechActive = false
                speechGeneration += 1
                if (liveLessonActive) livePaused = true
                status = "The phone's speech engine did not finish starting. Check Android text-to-speech settings, then tap Resume to retry this step."
            }
            return
        }
        // Prefer a natural British English voice when installed, then Indian
        // English and US English. Do not assume those three are the only English
        // locales a device engine can provide: Android engines may expose en-AU,
        // en-CA, or another downloaded English voice.
        val preferredLocales = when (selectedLanguage) {
            "Tanglish" -> listOf(Locale("en", "IN"), Locale.UK, Locale.US)
            "தமிழ்" -> listOf(Locale("ta", "IN"))
            else -> listOf(Locale.UK, Locale("en", "IN"), Locale.US)
        }
        val requiredLanguage = if (selectedLanguage == "தமிழ்") "ta" else "en"
        val installedLocales = engine.availableLanguages
            .orEmpty()
            .filter { it.language.equals(requiredLanguage, ignoreCase = true) }
            .sortedBy {
                when {
                    it == Locale.UK -> 0
                    it == Locale("en", "IN") -> 1
                    it == Locale.US -> 2
                    else -> 3
                }
            }
        val candidateLocales = (preferredLocales + installedLocales).distinct()
        val locale = candidateLocales.firstOrNull {
            engine.isLanguageAvailable(it) >= TextToSpeech.LANG_AVAILABLE
        }
        if (locale == null) {
            status = if (selectedLanguage == "தமிழ்") {
                "This selected voice engine has no Tamil voice. Choose Tanglish or install a Tamil-capable engine."
            } else {
                "No compatible English voice is available in the selected phone TTS engine. Install an English voice, then tap Resume to retry this step."
            }
            // Do not call finishSpeechSegment here: its completion callback would
            // skip every segment without audio and can make the whole lesson vanish.
            speechStartCallback = null
            speechCompletion = null
            speechActive = false
            if (liveLessonActive) livePaused = true
            speechGeneration += 1
            return
        }
        engine.language = locale
        engine.setSpeechRate(0.76f)
        engine.setPitch(1.02f)
        val utteranceId = "padippupal-tutor-$speechGeneration"
        activeTtsUtteranceId = utteranceId
        val result = engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, utteranceId)
        if (result == TextToSpeech.ERROR) {
            activeTtsUtteranceId = ""
            speechActive = false
            speechStartCallback = null
            speechCompletion = null
            speechGeneration += 1
            if (liveLessonActive) livePaused = true
            status = "The phone's speech engine rejected this step. Check Android text-to-speech settings, then tap Resume to retry."
        }
    }

    fun scheduleSpeechCompletionWatchdog(generation: Int, text: String) {
        val startedAt = SystemClock.elapsedRealtime()
        val estimatedSpeechMs = (Regex("\\S+").findAll(text).count() * 280L).coerceIn(4000L, 30000L)
        val hardDeadlineMs = (estimatedSpeechMs + 25000L).coerceAtMost(55000L)
        val check = object : Runnable {
            override fun run() {
                if (generation != speechGeneration || !speechActive) return
                // A paused MediaPlayer is intentionally not completion. Re-check
                // after the learner resumes instead of advancing while paused.
                if (liveLessonActive && livePaused) {
                    tutorMainHandler.postDelayed(this, 750L)
                    return
                }
                val player = audioPlayer.value
                val playerPlaying = runCatching { player?.isPlaying == true }.getOrDefault(false)
                val playerReachedEnd = player != null && runCatching {
                    !player.isPlaying && player.duration > 0 && player.currentPosition >= player.duration - 500
                }.getOrDefault(false)
                val ttsSpeaking = runCatching { ttsState.value?.isSpeaking == true }.getOrDefault(false)
                if (playerPlaying || ttsSpeaking) speechPlaybackObserved = true
                val elapsed = SystemClock.elapsedRealtime() - startedAt
                val ttsFinishedWithoutMedia = player == null && !ttsSpeaking
                if (speechPlaybackObserved && (playerReachedEnd || ttsFinishedWithoutMedia) && elapsed >= estimatedSpeechMs) {
                    // Recover only after playback was observed and the engine now
                    // reports it stopped; never skip merely because start was delayed.
                    finishSpeechSegment()
                    return
                }
                if (elapsed >= hardDeadlineMs && !speechPlaybackObserved) {
                    speechActive = false
                    speechStartCallback = null
                    speechCompletion = null
                    if (liveLessonActive) livePaused = true
                    status = "Voice playback did not start. Tap Resume to retry this step."
                    speechGeneration += 1
                    return
                }
                tutorMainHandler.postDelayed(this, 750L)
            }
        }
        tutorMainHandler.postDelayed(check, 1000L)
    }

    fun speak(text: String, onStarted: (() -> Unit)? = null, onFinished: (() -> Unit)? = null) {
        // Auto-read and the manual speaker button must not launch overlapping
        // Gemini requests/players, which can sound like a stuck repeating tutor.
        if (speechActive || text.isBlank()) return
        speechActive = true
        speechGeneration += 1
        speechPlaybackObserved = false
        val generation = speechGeneration
        scheduleSpeechCompletionWatchdog(generation, text)
        speechWordIndexOffset = 0
        speechWordStarts = Regex("\\S+").findAll(text).map { it.range.first }.toList()
        liveWordIndex = 0
        lastNativeRangeAt = 0L
        hostedWordTimings = emptyList()
        speechStartCallback = onStarted ?: { if (liveLessonActive) liveCaption = text }
        speechCompletion = onFinished
        // When enabled, bypass hosted TTS entirely. Android routes TextToSpeech
        // through the user's selected system engine (e.g. Sherpa-ONNX Kokoro).
        if (preferOnDeviceVoice) {
            speakWithDeviceTts(text, onStarted, onFinished)
            return
        }
        val base = BuildConfig.CURRICULUM_API_BASE_URL.trim().trimEnd('/')
        if (!base.startsWith("https://")) {
            speakWithDeviceTts(text, onStarted, onFinished)
            return
        }
        tutorExecutor.execute {
            val audioFile = File(context.cacheDir, "padippupal-voice-${System.nanoTime()}.wav")
            val audioWordTimings = mutableListOf<Pair<Long, Long>>()
            val outcome = runCatching {
                val requestBody = JSONObject()
                    .put("text", text.take(4500))
                    .put("app_language", selectedLanguage)
                val connection = URL("$base/tutor/speech").openConnection() as HttpURLConnection
                connection.requestMethod = "POST"
                connection.connectTimeout = 8000
                connection.readTimeout = 50000
                connection.setRequestProperty("Accept", "application/json")
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.doOutput = true
                val responseText: String
                try {
                    connection.outputStream.use {
                        it.write(requestBody.toString().toByteArray(StandardCharsets.UTF_8))
                    }
                    val code = connection.responseCode
                    val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                    responseText = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()
                    if (code !in 200..299) throw IllegalStateException("Natural voice unavailable")
                    runCatching {
                        val timingArray = JSONObject(responseText).optJSONArray("word_timings") ?: JSONArray()
                        for (i in 0 until timingArray.length()) {
                            val item = timingArray.optJSONObject(i) ?: continue
                            val startMs = item.optLong("start_ms", -1L)
                            val endMs = item.optLong("end_ms", -1L)
                            if (startMs >= 0L && endMs > startMs) audioWordTimings.add(startMs to endMs)
                        }
                    }
                } finally {
                    connection.disconnect()
                }
                val audio = JSONObject(responseText).getString("audio_base64")
                audioFile.writeBytes(Base64.decode(audio, Base64.DEFAULT))
                require(audioFile.length() > 44) { "Empty audio response" }
            }
            tutorMainHandler.post {
                outcome.fold(
                    onSuccess = {
                        hostedWordTimings = audioWordTimings.toList()
                        runCatching {
                            audioPlayer.value?.release()
                            val player = MediaPlayer()
                            audioPlayer.value = player
                            player.setDataSource(audioFile.absolutePath)
                            player.setOnCompletionListener {
                                it.release()
                                if (audioPlayer.value === it) audioPlayer.value = null
                                audioFile.delete()
                                finishSpeechSegment()
                            }
                            player.setOnErrorListener { failedPlayer, _, _ ->
                                // Continue at the current spoken word instead of replaying
                                // the entire segment after a mid-playback decoder/audio error.
                                val positionMs = runCatching { failedPlayer.currentPosition }.getOrDefault(0).toLong()
                                val durationMs = runCatching { failedPlayer.duration }.getOrDefault(0).toLong()
                                val words = Regex("\\S+").findAll(text).map { it.value }.toList()
                                val nextWordIndex = if (words.isEmpty() || positionMs <= 0L) {
                                    0
                                } else if (hostedWordTimings.isNotEmpty()) {
                                    hostedWordTimings.indexOfLast { it.first <= positionMs }
                                        .coerceIn(0, words.lastIndex)
                                } else if (durationMs > 0L) {
                                    val weights = words.map { word ->
                                        word.trimEnd(',', '.', ';', ':', '?', '!').length.coerceAtLeast(1).toFloat() +
                                            if (word.endsWith(",") || word.endsWith(";") || word.endsWith(":")) 1.8f
                                            else if (word.endsWith(".") || word.endsWith("?") || word.endsWith("!")) 3.2f else 0f
                                    }
                                    val targetWeight = (positionMs.toFloat() / durationMs.toFloat()).coerceIn(0f, 1f) * weights.sum().coerceAtLeast(1f)
                                    var accumulated = 0f
                                    var index = 0
                                    while (index < weights.lastIndex && accumulated + weights[index] < targetWeight) {
                                        accumulated += weights[index]
                                        index++
                                    }
                                    index
                                } else {
                                    0
                                }
                                failedPlayer.release()
                                if (audioPlayer.value === failedPlayer) audioPlayer.value = null
                                audioFile.delete()
                                val remainingText = words.drop(nextWordIndex).joinToString(" ")
                                if (remainingText.isBlank()) {
                                    finishSpeechSegment()
                                } else {
                                    speechWordIndexOffset = nextWordIndex
                                    speechWordStarts = Regex("\\S+").findAll(remainingText).map { it.range.first }.toList()
                                    hostedWordTimings = emptyList()
                                    liveWordIndex = nextWordIndex
                                    speakWithDeviceTts(remainingText, onStarted, onFinished)
                                }
                                true
                            }
                            player.prepare()
                            player.start()
                            speechPlaybackObserved = true
                            val startedCallback = speechStartCallback
                            speechStartCallback = null
                            startedCallback?.invoke()
                            status = "Speaking with Gemini natural voice."
                        }.onFailure {
                            audioFile.delete()
                            speakWithDeviceTts(text, onStarted, onFinished)
                        }
                    },
                    onFailure = {
                        audioFile.delete()
                        status = "Gemini voice request failed; using device voice. Check network and voice service configuration."
                        speakWithDeviceTts(text, onStarted, onFinished)
                    }
                )
            }
        }
    }

    fun playLiveSegment(index: Int) {
        if (!liveLessonActive || livePaused) return
        if (index >= liveSegments.size) {
            // Keep the completed explanation in chat history so the learner can reread it
            // and follow up after playback; otherwise it vanishes when the full-screen player closes.
            val completedLesson = liveCaption.trim()
            if (completedLesson.isNotBlank() && messages.none { it.role == "assistant" && it.content == completedLesson }) {
                messages.add(TutorMessage("assistant", completedLesson, interactiveLesson = liveInteractiveLesson))
            }
            liveLessonActive = false
            livePaused = false
            awaitingUnderstanding = false
            currentCheckpoint = ""
            status = "Live lesson complete."
            liveInteractiveLesson = null
            return
        }
        val segment = liveSegments[index]
        liveInteractiveLesson = segment.optJSONObject("interactive_lesson")
        awaitingUnderstanding = false
        // Normalize nullable API data before it enters UI state; optString may yield literal "null".
        // Complete-lesson mode never interrupts playback with per-segment feedback.
        currentCheckpoint = ""
        val caption = segment.optString("caption_text").ifBlank { segment.optString("spoken_text") }
        val action = segment.optJSONObject("visual_action")
        val visualCue = if (action == null || action.optString("type") == "none") "" else listOf(action.optString("type"), action.optString("target"), action.optString("value")).filter { it.isNotBlank() }.joinToString(" · ")
        status = "Preparing segment ${index + 1} of ${liveSegments.size}…"
        val words = segment.optString("spoken_text").trim()
        if (words.isBlank()) { playLiveSegment(index + 1); return }
        // Publish the full lesson before starting audio. Hosted audio can finish or fall
        // back without reliably delivering onStarted; initialize the caption before playback.
        // The word index still advances only with speech.
        liveCaption = words
        liveWordIndex = 0
        liveVisualAction = visualCue
        liveVisualActionType = action?.optString("type", "none") ?: "none"
        liveVisualTarget = action?.optString("target", "").orEmpty()
        liveSegmentIndex = index
        status = "Playing segment ${index + 1} of ${liveSegments.size}…"
        speak(words, onStarted = {
            // Audio has actually started: keep the exact same segment caption so
            // inline highlighting follows the spoken words rather than a separate overlay.
            liveCaption = words
            liveWordIndex = 0
            liveVisualAction = visualCue
            liveVisualActionType = action?.optString("type", "none") ?: "none"
            liveVisualTarget = action?.optString("target", "").orEmpty()
            liveSegmentIndex = index
            status = "Live lesson · segment ${index + 1} of ${liveSegments.size}"
        }) {
            if (!liveLessonActive) return@speak
            if (currentCheckpoint.isNotBlank()) {
                awaitingUnderstanding = true
                status = "Pause for understanding: continue when ready, or ask for a simpler explanation."
            } else {
                tutorMainHandler.postDelayed({ if (liveLessonActive) playLiveSegment(index + 1) }, 1150L)
            }
        }
    }

    fun startLiveLesson() {
        if (loading || liveLessonActive) return
        if (chapter.isBlank() && topic.isBlank()) { status = "Choose a chapter or concept first."; return }
        loading = true
        status = "Preparing a textbook-grounded live lesson…"
        tutorExecutor.execute {
            val outcome = runCatching {
                val base = BuildConfig.CURRICULUM_API_BASE_URL.trim().trimEnd('/')
                require(base.startsWith("https://") || (BuildConfig.DEBUG && base == "http://10.0.2.2:8765")) { "The secure PadippuPal API URL is not configured." }
                val allOnesTopic = topic.equals("All 1s", ignoreCase = true) ||
                    topic.equals("All ones", ignoreCase = true) ||
                    topic.equals("All one's", ignoreCase = true)
                val topicGuardrail = if (allOnesTopic) {
                    " TOPIC GUARDRAIL: All 1s means a sequence that repeats the number 1 only. Every teaching segment must explain that repeated-one sequence or its invariant (each term/value stays the same); short neutral classroom transitions are allowed. Do not introduce square numbers, counting up/down, or unrelated arithmetic. If the retrieved source cannot support All 1s, return no lesson instead of substituting another pattern."
                } else ""
                val lessonPrompt = "Teach the complete selected topic as one coherent lesson for class " + grade + ". Begin by naming chapter " + chapter + " and topic " + topic + ". Cover a simple definition, why or how it works, a concrete worked example, important rule or steps, one common mistake when relevant, and a short recap. Use familiar child-friendly language and text examples. Return 4-6 ordered speech segments only as a transport format; the app will join them into one uninterrupted explanation. Do not ask questions, request feedback, or insert checkpoints between segments. Put any optional single practice question only at the very end after the recap. Use an inline concept visual only when the selected chapter and topic have an exact matching blueprint; do not invent images or switch topics. Stay grounded only in retrieved textbook passages and make the explanation complete rather than stopping after the first small idea." + topicGuardrail
                val body = JSONObject().put("board", board).put("class_level", grade).put("subject", subject).put("medium", medium)
                    .put("app_language", selectedLanguage).put("student_name", studentName).put("chapter", chapter).put("topic", topic)
                    .put("message", lessonPrompt).put("max_segments", 6)
                val connection = URL("$base/tutor/lesson-plan").openConnection() as HttpURLConnection
                // The backend may retry Gemini once after schema validation; its two 45s
                // upstream attempts can exceed 50s in total. Keep the UI waiting for the
                // bounded backend response instead of reporting a false client timeout.
                connection.requestMethod = "POST"; connection.connectTimeout = 8000; connection.readTimeout = 120000
                connection.setRequestProperty("Accept", "application/json"); connection.setRequestProperty("Content-Type", "application/json; charset=utf-8"); connection.doOutput = true
                try {
                    connection.outputStream.use { it.write(body.toString().toByteArray(StandardCharsets.UTF_8)) }
                    val code = connection.responseCode
                    val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                    val responseText = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()
                    val response = JSONObject(responseText.ifBlank { "{}" })
                    if (code !in 200..299) throw IllegalStateException(response.optString("detail", "Could not prepare the live lesson."))
                    if (!response.optBoolean("grounded", false)) throw IllegalStateException(response.optString("warning", "No matching textbook passage was found."))
                    val array = response.optJSONArray("segments") ?: JSONArray()
                    val lessonSegments = (0 until array.length()).mapNotNull { array.optJSONObject(it) }
                    if (lessonSegments.isEmpty()) throw IllegalStateException("No textbook-backed lesson segments were returned.")
                    // Fail closed on the device too: a hosted API may be on an older
                    // deployment, so never let an unrelated segment reach speech playback.
                    if (topic.equals("All 1s", ignoreCase = true) ||
                        topic.equals("All ones", ignoreCase = true) ||
                        topic.equals("All one's", ignoreCase = true)) {
                        val validationError = AllOnesTopicValidator.failureReason(
                            lessonSegments.map { segment ->
                                segment.optString("spoken_text") to segment.optString("caption_text")
                            }
                        )
                        if (validationError != null) {
                            throw IllegalStateException(
                                "The lesson content did not stay on All 1s ($validationError). Please try again; no incorrect lesson was started."
                            )
                        }
                    }
                    // The API segments are transport chunks, not separate learner-facing steps.
                    // Join them into one caption/audio response so no checkpoint interrupts the explanation.
                    val completeText = lessonSegments.map { it.optString("spoken_text").trim() }
                        .filter { it.isNotBlank() }.joinToString(" ")
                    if (completeText.length < 220) {
                        throw IllegalStateException("The lesson was too short to explain the selected topic completely. Please try again.")
                    }
                    val completeLesson = JSONObject()
                        .put("id", "complete-lesson")
                        .put("spoken_text", completeText)
                        .put("caption_text", completeText)
                        .put("visual_action", JSONObject().put("type", "none").put("target", "").put("value", ""))
                        .put("interactive_lesson", response.optJSONObject("interactive_lesson") ?: JSONObject.NULL)
                        .put("checkpoint", JSONObject.NULL)
                    listOf(completeLesson)
                } finally { connection.disconnect() }
            }
            tutorMainHandler.post {
                loading = false
                outcome.fold(onSuccess = { segments -> liveSegments = segments; liveLessonActive = true; livePaused = false; playLiveSegment(0) },
                    onFailure = { error -> status = error.message ?: "Could not prepare the live lesson." })
            }
        }
    }

    fun stopLiveLesson() {
        liveLessonActive = false; livePaused = false; awaitingUnderstanding = false; currentCheckpoint = ""; liveSegments = emptyList(); liveInteractiveLesson = null; liveCaption = ""; liveVisualAction = ""
        liveVisualActionType = "none"; liveVisualTarget = ""; liveSegmentIndex = 0
        speechStartCallback = null
        audioPlayer.value?.let { player -> runCatching { player.stop() }; runCatching { player.release() } }
        audioPlayer.value = null; ttsState.value?.stop(); speechCompletion = null; speechActive = false
        status = "Live lesson stopped."
    }

    fun pauseLiveLesson() {
        if (!liveLessonActive || livePaused) return
        livePaused = true
        val player = audioPlayer.value
        if (player != null) {
            runCatching { player.pause() }
        } else {
            // Android TextToSpeech has no native pause API. Stop its current utterance;
            // Resume restarts this short teaching segment from its beginning.
            speechStartCallback = null
            speechCompletion = null
            ttsState.value?.stop()
            speechActive = false
        }
        status = "Lesson paused. Resume when you are ready."
    }

    fun resumeLiveLesson() {
        if (!liveLessonActive || !livePaused) return
        livePaused = false
        val player = audioPlayer.value
        if (player != null) {
            runCatching {
                player.start()
                speechActive = true
                status = "Lesson resumed."
            }.onFailure {
                playLiveSegment(liveSegmentIndex)
            }
        } else {
            playLiveSegment(liveSegmentIndex)
        }
    }

    fun sendMessage(startingMessage: String? = null) {
        val question = (startingMessage ?: input).trim()
        if (question.isEmpty() || loading) return
        val previous = messages.takeLast(8).map { it.role to it.content }
        messages.add(TutorMessage("user", question))
        input = ""
        loading = true
        status = "Thinking gently…"
        lastSources = emptyList()
        tutorExecutor.execute {
            val outcome = runCatching {
                val base = BuildConfig.CURRICULUM_API_BASE_URL.trim().trimEnd('/')
                require(base.startsWith("https://") || (BuildConfig.DEBUG && base == "http://10.0.2.2:8765")) { "The secure PadippuPal API URL is not configured." }
                val history = JSONArray()
                previous.forEach { (role, content) ->
                    history.put(JSONObject().put("role", role).put("content", content.take(2500)))
                }
                val body = JSONObject()
                    .put("board", board)
                    .put("class_level", grade)
                    .put("subject", subject)
                    .put("medium", medium)
                    .put("app_language", selectedLanguage)
                    .put("student_name", studentName)
                    .put("message", question)
                    .put("chapter", chapter)
                    .put("topic", topic)
                    .put("history", history)
                val connection = URL("$base/tutor/chat").openConnection() as HttpURLConnection
                connection.requestMethod = "POST"
                connection.connectTimeout = 8000
                connection.readTimeout = 35000
                connection.setRequestProperty("Accept", "application/json")
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.doOutput = true
                try {
                    connection.outputStream.use { it.write(body.toString().toByteArray(StandardCharsets.UTF_8)) }
                    val code = connection.responseCode
                    val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                    val responseText = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()
                    val response = JSONObject(responseText.ifBlank { "{}" })
                    if (code !in 200..299) {
                        val detail = response.optString("detail", "The tutor is temporarily unavailable.")
                        throw IllegalStateException(detail)
                    }
                    val answer = cleanTutorDisplayText(response.optString("answer").trim())
                    if (answer.isBlank()) throw IllegalStateException("The tutor returned an empty answer. Please try again.")
                    val visualLesson = response.optJSONObject("visual_lesson")
                    val interactiveLesson = response.optJSONObject("interactive_lesson")
                    val sources = mutableListOf<TutorSource>()
                    val array = response.optJSONArray("sources")
                    if (array != null) for (i in 0 until array.length()) {
                        val item = array.optJSONObject(i) ?: continue
                        sources += TutorSource(item.optString("title", "Curriculum source"), item.optString("url", ""))
                    }
                    listOf(answer, sources, visualLesson, interactiveLesson)
                } finally {
                    connection.disconnect()
                }
            }
            tutorMainHandler.post {
                loading = false
                outcome.fold(
                    onSuccess = { result ->
                        val answer = result[0] as String
                        @Suppress("UNCHECKED_CAST") val sources = result[1] as List<TutorSource>
                        val visualLesson = result[2] as JSONObject?
                        val interactiveLesson = result[3] as JSONObject?
                        messages.add(TutorMessage("assistant", answer, visualLesson, interactiveLesson))
                        lastSources = sources
                        status = if (sources.isEmpty()) "General explanation · no matching textbook passage was found yet." else "Answer checked against ${sources.size} curriculum source(s)."
                        if (speakReplies) speak(answer, onStarted = { liveCaption = answer })
                    },
                    onFailure = { error ->
                        status = error.message ?: "Couldn't reach the tutor. Please try again."
                    }
                )
            }
        }
    }

    val chatListState = androidx.compose.foundation.lazy.rememberLazyListState()
    LaunchedEffect(messages.size, loading, liveLessonActive) {
        // The live-teaching panel occupies list index 0 while it is visible.
        val livePanelOffset = if (liveCaption.isNotBlank() || liveLessonActive) 1 else 0
        val itemCount = livePanelOffset + messages.size + if (loading) 1 else 0
        if (itemCount > 0) chatListState.animateScrollToItem(itemCount - 1)
    }

    // Hosted audio uses playback position; Android TTS normally supplies exact
    // character offsets. Some engines emit only one range callback, however, so
    // keep a weighted elapsed-time fallback ready and use it whenever native ranges
    // stop arriving. This prevents a single callback freezing the inline highlight.
    LaunchedEffect(speechActive, liveCaption, liveLessonActive, livePaused, audioPlayer.value, hostedWordTimings, speechWordIndexOffset) {
        if (!speechActive || !liveLessonActive || liveCaption.isBlank()) {
            if (!speechActive) liveWordIndex = 0
            return@LaunchedEffect
        }
        val allTokens = Regex("\\S+").findAll(liveCaption).map { it.value }.toList()
        if (allTokens.isEmpty()) return@LaunchedEffect
        val offset = speechWordIndexOffset.coerceIn(0, allTokens.lastIndex)
        val tokens = allTokens.drop(offset)
        val weights = tokens.map { word ->
            word.trimEnd(',', '.', ';', ':', '?', '!').length.coerceAtLeast(1).toFloat() +
                if (word.endsWith(",") || word.endsWith(";") || word.endsWith(":")) 1.8f
                else if (word.endsWith(".") || word.endsWith("?") || word.endsWith("!")) 3.2f else 0f
        }
        val totalWeight = weights.sum().coerceAtLeast(1f)
        var elapsedMs = 0L
        while (speechActive && liveLessonActive) {
            // Keep the active-word highlight frozen while playback is paused.
            if (livePaused) {
                delay(45L)
                continue
            }
            val player = audioPlayer.value
            val duration = if (player != null) runCatching { player.duration }.getOrDefault(0).coerceAtLeast(0) else 0
            val position = if (player != null) runCatching { player.currentPosition }.getOrDefault(0).coerceAtLeast(0).toLong() else elapsedMs
            val index = if (player != null && hostedWordTimings.isNotEmpty()) {
                hostedWordTimings.indexOfLast { it.first <= position }.coerceAtLeast(0).coerceAtMost(tokens.lastIndex)
            } else {
                val progress = if (duration > 0) {
                    (position.toFloat() / duration.coerceAtLeast(1).toFloat()).coerceIn(0f, 1f)
                } else {
                    (elapsedMs.toFloat() / (tokens.size * 390L).coerceAtLeast(1L)).coerceIn(0f, 1f)
                }
                val weightAt = progress * totalWeight
                var sum = 0f
                var weightedIndex = 0
                while (weightedIndex < weights.lastIndex && sum + weights[weightedIndex] < weightAt) {
                    sum += weights[weightedIndex]
                    weightedIndex++
                }
                weightedIndex + offset
            }
            val nativeRangeIsFresh = lastNativeRangeAt > 0L &&
                System.currentTimeMillis() - lastNativeRangeAt < 900L
            if (!nativeRangeIsFresh) liveWordIndex = index
            delay(45L)
            elapsedMs += 45L
        }
    }
    LaunchedEffect(liveCaption, speechActive, awaitingUnderstanding, liveLessonActive, liveWordIndex) {
        if (liveLessonActive && (liveCaption.isNotBlank() || awaitingUnderstanding)) {
            chatListState.animateScrollToItem(0)
        } else if (!liveLessonActive && liveCaption.isNotBlank() && speechActive) {
            chatListState.animateScrollToItem(messages.lastIndex.coerceAtLeast(0))
        }
    }

    Column(
        modifier = modifier.fillMaxSize().background(TutorPaper).imePadding(),
        verticalArrangement = Arrangement.spacedBy(0.dp)
    ) {
        // Midnight command bar: persistent context and clear lesson controls.
        Row(
            modifier = Modifier.fillMaxWidth().background(TutorNight)
                .padding(start = 8.dp, end = 12.dp, top = 8.dp, bottom = 10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onBack) {
                Icon(Icons.Default.ArrowBack, contentDescription = "Back", tint = Color.White)
            }
            Box(
                modifier = Modifier.size(38.dp).background(TutorAccentSoft, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.GraphicEq, contentDescription = "PadippuPal AI tutor", tint = TutorNight, modifier = Modifier.size(23.dp))
            }
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text("PadippuPal", fontSize = 18.sp, fontWeight = FontWeight.ExtraBold, color = Color.White, maxLines = 1)
                Text(
                    if (topic.isNotBlank()) "$chapter · $topic" else if (chapter.isNotBlank()) chapter else "CLASS $grade  ·  $board",
                    fontSize = 10.sp, color = TutorMutedOnNight, maxLines = 1
                )
            }
            if (liveLessonActive) {
                TextButton(onClick = { if (livePaused) resumeLiveLesson() else pauseLiveLesson() }, contentPadding = PaddingValues(horizontal = 5.dp, vertical = 4.dp)) {
                    Text(if (livePaused) "Resume" else "Pause", color = TutorAccentSoft, fontWeight = FontWeight.SemiBold, fontSize = 11.sp)
                }
                TextButton(onClick = { stopLiveLesson() }, contentPadding = PaddingValues(horizontal = 5.dp, vertical = 4.dp)) {
                    Text("Stop", color = Color(0xFFFF9B9B), fontWeight = FontWeight.SemiBold, fontSize = 11.sp)
                }
            } else if (!setupOnly) {
                Button(
                    onClick = { startLiveLesson() },
                    enabled = !loading && (chapter.isNotBlank() || topic.isNotBlank()),
                    shape = RoundedCornerShape(12.dp),
                    contentPadding = PaddingValues(horizontal = 13.dp, vertical = 9.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = TutorGreen, contentColor = TutorNight)
                ) { Text("▶ Teach", fontWeight = FontWeight.ExtraBold, maxLines = 1) }
            }
        }

        if (showLessonSettings && !liveLessonActive) {
            Surface(Modifier.fillMaxWidth().weight(1f).padding(horizontal = 12.dp, vertical = 6.dp), color = Color.White, shape = RoundedCornerShape(18.dp), border = BorderStroke(1.dp, Color(0xFFE2E8F0))) {
                Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Column(Modifier.weight(1f).fillMaxWidth().verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Set up your lesson", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = TutorDeep)
                    Text("Choose what you want to learn. Your tutor will start when you tap Teach.", fontSize = 12.sp, color = TutorGrey)
                    Text("Subject", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = TutorGrey)
                    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("Mathematics", "Science", "English", "Tamil", "Social Science", "Computer Science").forEach { option ->
                            FilterChip(selected = subject == option, onClick = { subject = option; chapter = ""; topic = "" }, label = { Text(option, maxLines = 1) })
                        }
                    }
                    Text("Chapter", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = TutorGrey)
                    Box {
                        OutlinedButton(onClick = { chapterMenuExpanded = true }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp)) {
                            Text(chapter.ifBlank { if (outlineLoading) "Loading chapters…" else "Choose chapter" }, maxLines = 1)
                        }
                        DropdownMenu(expanded = chapterMenuExpanded, onDismissRequest = { chapterMenuExpanded = false }) {
                            chapterOptions.forEachIndexed { index, option ->
                                DropdownMenuItem(text = { Text("${index + 1}. ${option.first}") }, onClick = { chapter = option.first; topic = option.second.firstOrNull().orEmpty(); chapterMenuExpanded = false })
                            }
                            if (!outlineLoading && chapterOptions.isEmpty()) DropdownMenuItem(text = { Text("No chapter list is available") }, onClick = { chapterMenuExpanded = false }, enabled = false)
                        }
                    }
                    Text("Topic / concept", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = TutorGrey)
                    Box {
                        OutlinedButton(onClick = { topicMenuExpanded = true }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp)) {
                            Text(topic.ifBlank { "Choose concept" }, maxLines = 1)
                        }
                        DropdownMenu(expanded = topicMenuExpanded, onDismissRequest = { topicMenuExpanded = false }) {
                            val topics = chapterOptions.firstOrNull { it.first == chapter }?.second.orEmpty()
                            topics.forEachIndexed { index, option ->
                                DropdownMenuItem(text = { Text("${index + 1}. $option") }, onClick = { topic = option; topicMenuExpanded = false })
                            }
                            if (topics.isEmpty()) DropdownMenuItem(text = { Text("Choose a chapter first") }, onClick = { topicMenuExpanded = false }, enabled = false)
                        }
                    }
                    Text("Language", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = TutorGrey)
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf("English", "Tanglish", "தமிழ்").forEach { option ->
                            FilterChip(selected = selectedLanguage == option, onClick = { selectedLanguage = option }, label = { Text(option) })
                        }
                    }
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Text("Read replies aloud", modifier = Modifier.weight(1f), color = TutorDeep, fontSize = 13.sp)
                        Switch(checked = speakReplies, onCheckedChange = { speakReplies = it })
                    }
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Text("Prefer on-device voice", modifier = Modifier.weight(1f), color = TutorDeep, fontSize = 13.sp)
                        Switch(checked = preferOnDeviceVoice, onCheckedChange = {
                            preferOnDeviceVoice = it
                            context.getSharedPreferences("padippupal_settings", 0).edit().putBoolean("prefer_on_device_voice", it).apply()
                        })
                    }
                    }
                    Button(onClick = { if (setupOnly) onStartTeaching() else showLessonSettings = false }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp), enabled = subject.isNotBlank(), colors = ButtonDefaults.buttonColors(containerColor = TutorGreen)) { Text("Done") }
                }
            }
        }

        if (!liveLessonActive && !showLessonSettings) {
        // The chat owns the flexible space and scrolls independently of the fixed composer.
        LazyColumn(
            state = chatListState,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 12.dp),
            verticalArrangement = Arrangement.spacedBy(9.dp),
            contentPadding = PaddingValues(top = 6.dp, bottom = 10.dp)
        ) {
            if (!liveLessonActive) items(messages) { message ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = if (message.role == "user") Arrangement.End else Arrangement.Start) {
                    Surface(
                        color = if (message.role == "user") TutorGreen else Color.White,
                        shape = RoundedCornerShape(
                            topStart = 18.dp, topEnd = 18.dp,
                            bottomStart = if (message.role == "user") 18.dp else 5.dp,
                            bottomEnd = if (message.role == "user") 5.dp else 18.dp
                        ),
                        shadowElevation = 1.dp,
                        border = if (message.role == "assistant") BorderStroke(1.dp, Color(0xFFE2E8F0)) else null,
                        modifier = Modifier.widthIn(max = 340.dp)
                    ) {
                        Column(Modifier.padding(14.dp)) {
                            if (message.role == "assistant" && message.content == liveCaption && speechActive && !liveLessonActive) {
                                WordByWordCaption(liveCaption, true, liveWordIndex)
                            } else {
                                Text(message.content, color = if (message.role == "user") Color.White else TutorDeep, fontSize = 15.sp, lineHeight = 23.sp)
                            }
                            if (message.role == "assistant") {
                                val latestAssistant = messages.lastOrNull { it.role == "assistant" }
                                if (message.content == latestAssistant?.content) {
                                    when {
                                        message.interactiveLesson != null -> DatabaseInteractiveLessonLab(
                                            lesson = message.interactiveLesson,
                                            sessionPrefs = sessionPrefs,
                                            sessionKey = sessionKey,
                                            todayKey = todayKey
                                        )
                                        message.visualLesson != null -> DatabaseLessonVisual(message.visualLesson)
                                    }
                                }
                                // Feedback is intentionally deferred until the complete lesson flow is implemented.

                            }
                        }
                    }
                }
            }
            if (loading) {
                item {
                    Surface(color = Color.White, shape = RoundedCornerShape(16.dp), border = BorderStroke(1.dp, Color(0xFFE2E8F0))) {
                        Row(Modifier.padding(13.dp), verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp, color = TutorGreen)
                            Text("  Your tutor is preparing an explanation…", color = TutorGrey, fontSize = 13.sp)
                        }
                    }
                }
            }
        }

        }

        if (liveLessonActive) {
            // One continuous teaching canvas: no inset green card or floating lesson overlay.
            Column(
                modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 18.dp, vertical = 8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Column(
                    modifier = Modifier.weight(1f).fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.GraphicEq, contentDescription = null, tint = TutorGreen, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(7.dp))
                            Text(if (speechActive) "YOUR TEACHER IS SPEAKING" else if (awaitingUnderstanding) "LET'S CHECK YOUR UNDERSTANDING" else "LESSON", color = TutorGreen, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                            Spacer(Modifier.weight(1f))
                            if (liveSegments.size > 1) Text("${(liveSegmentIndex + 1).coerceAtMost(liveSegments.size)} / ${liveSegments.size}", color = TutorGrey, fontSize = 10.sp)
                        }
                        if (liveCaption.isNotBlank()) {
                            WordByWordCaption(
                                liveCaption, speechActive, liveWordIndex,
                                // At checkpoints, don't let the caption consume all remaining height:
                                // the compact concept animation and fixed answer card must stay visible.
                                modifier = if (awaitingUnderstanding) {
                                    Modifier.fillMaxWidth().heightIn(min = 64.dp, max = 108.dp)
                                } else {
                                    Modifier.weight(1f).fillMaxWidth()
                                },
                                expandToAvailableHeight = !awaitingUnderstanding
                            )
                        } else {
                            Box(Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                                CircularProgressIndicator(color = TutorGreen)
                            }
                        }
                        if (liveVisualAction.isNotBlank()) {
                            Text("Visual focus · $liveVisualAction", color = TutorGrey, fontSize = 10.sp)
                        }
                        // Keep the concept animation mounted during the checkpoint; compact it so
                        // the student can see both the pattern and the response choices together.
                        val liveVisualSteps = liveInteractiveLesson?.optJSONArray("steps")
                        val totalLiveWords = liveCaption.trim().split(Regex("\\s+")).count { it.isNotBlank() }.coerceAtLeast(1)
                        val liveVisualStep = if (liveVisualSteps != null && liveVisualSteps.length() > 0) {
                            ((liveWordIndex.toFloat() / totalLiveWords.toFloat()) * liveVisualSteps.length())
                                .toInt().coerceIn(0, liveVisualSteps.length() - 1)
                        } else 0
                        when {
                            liveCaption.isNotBlank() && liveInteractiveLesson != null -> DatabaseInteractiveLessonLab(
                                lesson = liveInteractiveLesson!!,
                                sessionPrefs = sessionPrefs,
                                sessionKey = sessionKey,
                                todayKey = todayKey,
                                compact = true,
                                activeStepOverride = liveVisualStep
                            )
                            liveCaption.isNotBlank() && chapter.contains("Patterns in Mathematics", ignoreCase = true) -> {
                                val topicKey = topic.lowercase(Locale.ROOT)
                                val scene = when {
                                    topicKey.contains("all 1s") || topicKey.contains("all ones") -> "repeated_ones"
                                    topicKey.contains("shape") || topicKey.contains("repeating") -> "shape_pattern"
                                    else -> "number_pattern"
                                }
                                ChapterOneMathAnimation(
                                    scene = scene,
                                    title = topic.ifBlank { "Patterns in Mathematics" },
                                    topic = topic,
                                    caption = "Watch the pattern change automatically as your teacher explains.",
                                    compact = awaitingUnderstanding
                                )
                            }
                        }
                    }
            }
        }

        // Inline learner checkpoint: part of the teaching flow, not a floating card.
        if (awaitingUnderstanding && liveLessonActive) {
            Column(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 18.dp, vertical = 4.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                Text(normalizedCheckpoint(currentCheckpoint), color = TutorDeep, fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = {
                        val nextIndex = liveSegmentIndex + 1
                        awaitingUnderstanding = false
                        currentCheckpoint = ""
                        livePaused = false
                        status = "Great! Let’s take the next small step."
                        tutorMainHandler.post { if (liveLessonActive) playLiveSegment(nextIndex) }
                    }, modifier = Modifier.weight(1f), colors = ButtonDefaults.buttonColors(containerColor = TutorGreen)) { Text("I understand", maxLines = 1) }
                    OutlinedButton(onClick = {
                        awaitingUnderstanding = false
                        val segment = liveSegments.getOrNull(liveSegmentIndex)
                        if (segment != null) {
                            val original = segment.optString("spoken_text")
                            speak("That is okay. Let me explain it more simply. " + original, onStarted = {
                                liveCaption = "Let me explain it more simply. " + original
                                liveWordIndex = 0
                            }) {
                                awaitingUnderstanding = true
                                currentCheckpoint = "Was that explanation clearer?"
                                status = "Tell your teacher whether that helped."
                            }
                        } else {
                            awaitingUnderstanding = true
                        }
                    }, modifier = Modifier.weight(1f)) { Text("Explain again", maxLines = 1) }
                }
                TextButton(
                    onClick = {
                        input = "I have a question about this part: " + currentCheckpoint
                        stopLiveLesson()
                        status = "Your question is ready below. Send it and I’ll explain this part."
                    },
                    modifier = Modifier.align(Alignment.End)
                ) { Text("I have a question", color = TutorGreen) }
            }
        }

        if (!liveLessonActive && status.isNotBlank()) {
            Text(status, modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 2.dp), color = TutorGrey, fontSize = 10.sp, lineHeight = 13.sp, maxLines = 2)
        }
        if (!liveLessonActive && lastSources.isNotEmpty()) {
            Text("Textbook sources · " + lastSources.joinToString { it.title }, modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 2.dp), color = TutorGreen, fontSize = 10.sp, maxLines = 1)
        }

        // Keep setup focused; show the question composer only after selection.
        if (!showLessonSettings && !liveLessonActive) {
        // Keep the question composer for regular tutor chat, not setup or full-screen teaching.
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = Color.White,
            shadowElevation = 8.dp
        ) {
            Row(
                modifier = Modifier.fillMaxWidth().padding(start = 12.dp, end = 12.dp, top = 8.dp, bottom = 8.dp),
                verticalAlignment = Alignment.Bottom,
                horizontalArrangement = Arrangement.spacedBy(7.dp)
            ) {
                OutlinedTextField(
                    value = input,
                    onValueChange = { input = it },
                    modifier = Modifier.weight(1f).heightIn(min = 52.dp, max = 112.dp),
                    placeholder = { Text("Ask your teacher…", fontSize = 14.sp) },
                    shape = RoundedCornerShape(20.dp),
                    minLines = 1,
                    maxLines = 4,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                    keyboardActions = KeyboardActions(onSend = { sendMessage() }),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = TutorGreen,
                        unfocusedBorderColor = Color(0xFFDCE3ED),
                        focusedContainerColor = Color(0xFFFFFFFF),
                        unfocusedContainerColor = Color(0xFFFFFFFF)
                    )
                )
                FilledIconButton(
                    onClick = {
                        if (listening) { speechRecognizer?.stopListening(); listening = false }
                        else if (context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) startVoiceInput()
                        else voicePermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    },
                    enabled = !loading,
                    modifier = Modifier.size(50.dp),
                    colors = IconButtonDefaults.filledIconButtonColors(containerColor = if (listening) Color(0xFFB3261E) else Color(0xFFEAF0FF), contentColor = if (listening) Color.White else TutorGreen)
                ) {
                    Icon(if (listening) Icons.Default.MicOff else Icons.Default.Mic, contentDescription = if (listening) "Stop voice input" else "Ask by voice")
                }
                FilledIconButton(
                    onClick = { sendMessage() }, enabled = !loading && input.isNotBlank(), modifier = Modifier.size(50.dp),
                    colors = IconButtonDefaults.filledIconButtonColors(containerColor = TutorGreen, contentColor = Color.White)
                ) { Icon(Icons.Default.Send, contentDescription = "Send question") }
            }
        }
        }
    }
}
