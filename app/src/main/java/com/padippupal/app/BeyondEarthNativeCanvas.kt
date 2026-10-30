package com.padippupal.app

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import kotlin.math.cos
import kotlin.math.sin

/**
 * Native, offline Day/Night teaching board. The active tutor synthesis step
 * progressively reveals the same cumulative illustration; there are no lesson
 * navigation controls inside the drawing.
 */
@Composable
internal fun BeyondEarthNativeCanvas(
    step: Int,
    compact: Boolean,
    narrationText: String,
    narrationWordIndex: Int,
    narrationActive: Boolean,
    modifier: Modifier = Modifier
) {
    val narrationWords = narrationText.trim().split(Regex("\\s+")).filter { it.isNotBlank() }
    val wordProgress = if (narrationWords.isEmpty()) 1f else
        ((narrationWordIndex + if (narrationActive) 1 else narrationWords.size).toFloat() / narrationWords.size).coerceIn(0f, 1f)
    // Reveal each part in sync with the live spoken sentence; no manual stage control.
    val reveal = when {
        narrationWords.isEmpty() -> step.coerceIn(0, 3)
        wordProgress < .18f -> 0
        wordProgress < .43f -> 1
        wordProgress < .70f -> 2
        else -> 3
    }
    val rotation = rememberInfiniteTransition(label = "earth-rotation")
    val angle by rotation.animateFloat(
        initialValue = 0f,
        targetValue = if (reveal >= 3) 360f else 0f,
        animationSpec = infiniteRepeatable(tween(18000, easing = LinearEasing)),
        label = "earth-angle"
    )
    Column(modifier = modifier, verticalArrangement = Arrangement.spacedBy(5.dp)) {
        Canvas(
            Modifier.fillMaxWidth().height(if (compact) 178.dp else 245.dp)
                .clip(RoundedCornerShape(14.dp)).background(Color(0xFFFFFBF2))
        ) {
            val w = size.width
            val h = size.height
            val ink = Color(0xFF173D70)
            val gold = Color(0xFFFFC83D)
            val sunX = w * .17f
            val sunY = h * .48f
            val sunR = h * .105f
            val earthX = w * .69f
            val earthY = h * .49f
            val earthR = h * .235f

            // Paper-like margin and heading.
            drawLine(Color(0xFFD8D2C6), Offset(0f, h * .13f), Offset(w, h * .13f), 1.dp.toPx())
            drawContext.canvas.nativeCanvas.apply {
                val p = android.graphics.Paint(android.graphics.Paint.ANTI_ALIAS_FLAG).apply {
                    color = android.graphics.Color.rgb(23, 61, 112)
                    textSize = h * .065f
                    typeface = android.graphics.Typeface.create("cursive", android.graphics.Typeface.NORMAL)
                }
                drawText("Beyond Earth  |  Day and Night", w * .035f, h * .09f, p)
                p.textSize = h * .045f
                drawText("Class 6 · Science", w * .78f, h * .09f, p)
            }

            // Sun: layered warm marker fill and imperfect double outline.
            drawCircle(Color(0xFFFFE39A), sunR * 1.14f, Offset(sunX, sunY))
            drawCircle(gold, sunR, Offset(sunX, sunY))
            drawCircle(Color(0xFFFFA52E), sunR, Offset(sunX, sunY), style = Stroke(2.2.dp.toPx()))
            drawCircle(Color(0xFFFFB83F), sunR * .94f, Offset(sunX + 1.dp.toPx(), sunY - 1.dp.toPx()), style = Stroke(1.dp.toPx()))
            for (i in 0 until 16) {
                val a = i * Math.PI / 8.0
                val r1 = sunR * 1.22f
                val r2 = sunR * (1.48f + if (i % 3 == 0) .08f else 0f)
                drawLine(gold, Offset(sunX + cos(a).toFloat() * r1, sunY + sin(a).toFloat() * r1),
                    Offset(sunX + cos(a).toFloat() * r2, sunY + sin(a).toFloat() * r2), 2.dp.toPx(), cap = androidx.compose.ui.graphics.StrokeCap.Round)
            }
            drawContext.canvas.nativeCanvas.apply {
                val p = android.graphics.Paint(3).apply { color = android.graphics.Color.rgb(23,61,112); textSize = h*.055f; typeface = android.graphics.Typeface.create("cursive", 0) }
                drawText("Sun", sunX - sunR*.3f, sunY + sunR*1.7f, p)
                p.textSize = h*.042f
                drawText("The Sun is a star.", w*.035f, h*.88f, p)
            }

            if (reveal >= 1) {
                // Sunlight rays progressively appear between Sun and Earth.
                for (i in -1..2) {
                    val y = earthY + i * earthR * .48f
                    val start = sunX + sunR * 1.35f
                    val end = earthX - earthR * 1.12f
                    drawLine(gold, Offset(start, y), Offset(end, y - h*.025f), 2.4.dp.toPx(), cap = androidx.compose.ui.graphics.StrokeCap.Round)
                    val tip = Offset(end, y - h*.025f)
                    drawLine(gold, tip, Offset(end - 9.dp.toPx(), tip.y - 5.dp.toPx()), 2.dp.toPx())
                    drawLine(gold, tip, Offset(end - 9.dp.toPx(), tip.y + 5.dp.toPx()), 2.dp.toPx())
                }
                drawContext.canvas.nativeCanvas.apply {
                    val p = android.graphics.Paint(3).apply { color = android.graphics.Color.rgb(23,61,112); textSize = h*.052f; typeface = android.graphics.Typeface.create("cursive", 0) }
                    drawText("Sunlight", w*.39f, h*.31f, p)
                    p.textSize = h*.034f
                    drawText("(travels in straight lines)", w*.35f, h*.37f, p)
                }
            }

            if (reveal >= 2) {
                // Earth base and illuminated hemisphere.
                drawCircle(Color(0xFF244A78), earthR, Offset(earthX, earthY))
                val dayClip = Path().apply {
                    moveTo(earthX, earthY - earthR)
                    arcTo(androidx.compose.ui.geometry.Rect(earthX-earthR, earthY-earthR, earthX+earthR, earthY+earthR), -90f, -180f, false)
                    close()
                }
                clipPath(dayClip) {
                    drawCircle(Color(0xFF57B7D7), earthR, Offset(earthX, earthY))
                    // Rotate the surface details beneath the fixed sunlight boundary.
                    rotate(angle, pivot = Offset(earthX, earthY)) {
                    // Simplified continent silhouettes with organic curves.
                    val land = Path().apply {
                        moveTo(earthX-earthR*.65f, earthY-earthR*.55f)
                        cubicTo(earthX-earthR*.15f, earthY-earthR*.9f, earthX-earthR*.08f, earthY-earthR*.28f, earthX-earthR*.42f, earthY-earthR*.12f)
                        cubicTo(earthX-earthR*.8f, earthY+earthR*.12f, earthX-earthR*.48f, earthY+earthR*.55f, earthX-earthR*.18f, earthY+earthR*.8f)
                        cubicTo(earthX-earthR*.05f, earthY+earthR*.35f, earthX-earthR*.35f, earthY+earthR*.15f, earthX-earthR*.25f, earthY-earthR*.08f)
                        close()
                    }
                    drawPath(land, Color(0xFF78C78B))
                    drawPath(land, Color(0xFF398B68), style = Stroke(1.5.dp.toPx()))
                    for (i in 0 until 12) {
                        val sx = earthX + earthR*.2f + (i%3)*earthR*.22f
                        val sy = earthY - earthR*.72f + i*earthR*.12f
                        drawCircle(Color(0xFFEAF4FF), 1.4.dp.toPx(), Offset(sx, sy))
                    }
                    }
                }
                drawCircle(Color(0xFF153C68), earthR, Offset(earthX, earthY), style = Stroke(2.4.dp.toPx()))
                drawContext.canvas.nativeCanvas.apply {
                    val p = android.graphics.Paint(3).apply { color = android.graphics.Color.rgb(23,61,112); textSize = h*.05f; typeface = android.graphics.Typeface.create("cursive", 0) }
                    drawText("Day", earthX-earthR*1.45f, earthY+earthR*1.28f, p)
                    drawText("Night", earthX+earthR*.92f, earthY+earthR*1.28f, p)
                }
            }

            if (reveal >= 3) {
                // Tilted axis and curved rotation cue; animation is continuous.
                rotate(-12f, Offset(earthX, earthY)) {
                    drawLine(ink, Offset(earthX, earthY-earthR*1.48f), Offset(earthX, earthY+earthR*1.48f), 2.dp.toPx(), pathEffect = androidx.compose.ui.graphics.PathEffect.dashPathEffect(floatArrayOf(7.dp.toPx(), 5.dp.toPx())))
                }
                drawArc(Color(0xFFE45D7A), -35f + angle*.12f, 100f, false,
                    topLeft = Offset(earthX-earthR*1.35f, earthY-earthR*1.35f), size = Size(earthR*2.7f, earthR*2.7f), style = Stroke(2.dp.toPx()))
                drawContext.canvas.nativeCanvas.apply {
                    val p = android.graphics.Paint(3).apply { color = android.graphics.Color.rgb(23,61,112); textSize = h*.047f; typeface = android.graphics.Typeface.create("cursive", 0) }
                    drawText("Earth's axis", earthX+earthR*.35f, earthY-earthR*1.5f, p)
                    p.color = android.graphics.Color.rgb(220,75,108)
                    drawText("Earth rotates on its axis", earthX+earthR*.85f, earthY-earthR*.95f, p)
                }
            }
        }
        Text(
            when (reveal) {
                0 -> "The Sun is a star. It gives Earth light and heat."
                1 -> "Sunlight travels through space and reaches Earth."
                2 -> "The side facing the Sun has day. The opposite side has night."
                else -> "Earth rotates on its axis. This makes day and night change."
            },
            color = Color(0xFF173D70),
            fontFamily = FontFamily.Cursive,
            fontSize = if (compact) 13.sp else 15.sp,
            fontWeight = FontWeight.Medium,
            lineHeight = if (compact) 18.sp else 22.sp
        )
    }
}
