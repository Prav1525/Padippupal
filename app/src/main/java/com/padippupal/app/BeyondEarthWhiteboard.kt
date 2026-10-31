package com.padippupal.app

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

private val BoardPaper = Color(0xFFFFFEF8)
private val BoardInk = Color(0xFF27364B)
private val BoardBlue = Color(0xFF4387B8)
private val BoardTeal = Color(0xFF278477)
private val BoardGold = Color(0xFFE5AD43)
private val BoardPencil = Color(0xFF8B9AA8)

/**
 * Chapter-scoped, native Compose whiteboard. It intentionally uses imperfect
 * double strokes, pencil-like connectors, paper texture and annotation chips
 * rather than polished infographic geometry or SVG assets.
 */
@Composable
internal fun BeyondEarthWhiteboard(
    subtype: String,
    labels: List<String>,
    revealCount: Int,
    stepKey: Int,
    compact: Boolean
) {
    var manualReveal by remember(subtype, stepKey) { mutableIntStateOf(0) }
    val stage = maxOf(revealCount, manualReveal).coerceIn(0, 8)
    val heading = when (subtype) {
        "beyond_earth_constellation" -> "A PATTERN IN THE NIGHT SKY"
        "beyond_earth_sky_watching" -> "LOOK UP • OBSERVE • RECORD"
        "beyond_earth_sun_star" -> "OUR SUN IS A STAR"
        "beyond_earth_solar_system" -> "OUR SOLAR SYSTEM"
        "beyond_earth_planet_star" -> "PLANETS AND STARS"
        "beyond_earth_earth_moon" -> "EARTH AND ITS MOON"
        "beyond_earth_asteroid_comet" -> "SMALL BODIES IN SPACE"
        else -> "A GALAXY OF STARS"
    }

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(if (compact) 190.dp else 248.dp)
                .clip(RoundedCornerShape(18.dp))
                .background(BoardPaper)
                .border(1.dp, Color(0xFFE4DFD2), RoundedCornerShape(18.dp))
                .pointerInput(subtype) {
                    detectTapGestures {
                        manualReveal = (manualReveal + 1).coerceAtMost(8)
                    }
                }
        ) {
            Canvas(Modifier.fillMaxSize()) {
                val unit = size.minDimension / 220f
                val sw = 2.1f * unit
                // Faint ruled-paper guides and a hand-drawn frame.
                for (i in 1..5) {
                    val y = size.height * i / 6f
                    drawLine(Color(0xFFEDE9DF), Offset(12f, y), Offset(size.width - 12f, y), 0.7f * unit)
                }
                drawRoundRect(
                    BoardPencil.copy(alpha = 0.42f),
                    Offset(8f, 8f),
                    Size(size.width - 16f, size.height - 16f),
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(14f * unit),
                    style = Stroke(1f * unit)
                )
                when (subtype) {
                    "beyond_earth_constellation" -> drawConstellation(stage, sw, unit)
                    "beyond_earth_sky_watching" -> drawSkyWatcher(stage, sw, unit)
                    "beyond_earth_sun_star" -> drawSunStar(stage, sw, unit)
                    "beyond_earth_solar_system" -> drawSolarSystem(stage, sw, unit)
                    "beyond_earth_planet_star" -> drawPlanetStar(stage, sw, unit)
                    "beyond_earth_earth_moon" -> drawEarthMoon(stage, sw, unit)
                    "beyond_earth_asteroid_comet" -> drawAsteroidsComet(stage, sw, unit)
                    else -> drawGalaxy(stage, sw, unit)
                }
            }

            Column(
                modifier = Modifier.align(Alignment.TopStart).padding(start = 16.dp, top = 13.dp)
            ) {
                Text(
                    "SCIENCE FIELD NOTES  /  06",
                    color = BoardTeal,
                    fontSize = 8.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.1.sp
                )
                Text(
                    heading,
                    color = BoardInk,
                    fontSize = if (compact) 10.sp else 11.sp,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 0.4.sp
                )
            }

            Text(
                "TAP TO SKETCH  ↗",
                modifier = Modifier.align(Alignment.BottomEnd).padding(end = 15.dp, bottom = 11.dp),
                color = BoardPencil,
                fontSize = 8.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.8.sp
            )
        }

        if (labels.isNotEmpty()) {
            labels.take(6).chunked(3).forEach { group ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(7.dp)
                ) {
                    group.forEachIndexed { index, label ->
                        Row(
                            modifier = Modifier
                                .weight(1f)
                                .clip(RoundedCornerShape(8.dp))
                                .background(if ((index + stage) % 2 == 0) Color(0xFFF0F6F4) else Color(0xFFF5F3EC))
                                .padding(horizontal = 8.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(5.dp)
                        ) {
                            Spacer(
                                Modifier
                                    .height(6.dp)
                                    .weight(0.08f)
                                    .background(if (index % 2 == 0) BoardTeal else BoardGold, RoundedCornerShape(4.dp))
                            )
                            Text(
                                label,
                                modifier = Modifier.weight(0.92f),
                                color = BoardInk,
                                fontSize = if (compact) 9.sp else 10.sp,
                                fontWeight = FontWeight.SemiBold,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }
                    }
                    repeat((3 - group.size).coerceAtLeast(0)) { Spacer(Modifier.weight(1f)) }
                }
            }
        }
    }
}

private fun DrawScope.roughLine(a: Offset, b: Offset, color: Color, width: Float) {
    drawLine(color.copy(alpha = 0.45f), a + Offset(1.4f, 1.1f), b + Offset(1.4f, 1.1f), width * 1.45f, cap = StrokeCap.Round)
    drawLine(color, a, b, width, cap = StrokeCap.Round)
}

private fun DrawScope.roughCircle(center: Offset, radius: Float, color: Color, width: Float, fill: Boolean = false) {
    if (fill) drawCircle(color.copy(alpha = 0.15f), radius, center)
    drawCircle(color.copy(alpha = 0.48f), radius * 1.035f, center + Offset(1.1f, 0.8f), style = Stroke(width * 1.35f, cap = StrokeCap.Round))
    drawCircle(color, radius, center, style = Stroke(width, cap = StrokeCap.Round))
}

private fun DrawScope.roughPath(points: List<Offset>, color: Color, width: Float, close: Boolean = false) {
    if (points.size < 2) return
    val path = Path().apply {
        moveTo(points.first().x, points.first().y)
        points.drop(1).forEach { lineTo(it.x, it.y) }
        if (close) close()
    }
    drawPath(path, color.copy(alpha = 0.45f), style = Stroke(width * 1.55f, cap = StrokeCap.Round))
    drawPath(path, color, style = Stroke(width, cap = StrokeCap.Round))
}

private fun DrawScope.drawConstellation(stage: Int, sw: Float, u: Float) {
    val pts = listOf(
        Offset(size.width * .22f, size.height * .63f),
        Offset(size.width * .32f, size.height * .40f),
        Offset(size.width * .46f, size.height * .54f),
        Offset(size.width * .59f, size.height * .31f),
        Offset(size.width * .75f, size.height * .48f),
        Offset(size.width * .84f, size.height * .27f)
    )
    pts.take(stage.coerceAtLeast(1)).forEachIndexed { i, p ->
        if (i > 0) roughLine(pts[i - 1], p, BoardPencil, sw * .7f)
        roughCircle(p, (4.2f + (i % 2)) * u, BoardGold, sw, fill = true)
        for (ray in 0..3) {
            val a = ray * PI / 2
            roughLine(
                p + Offset(cos(a).toFloat() * 7f * u, sin(a).toFloat() * 7f * u),
                p + Offset(cos(a).toFloat() * 10f * u, sin(a).toFloat() * 10f * u),
                BoardGold,
                sw * .55f
            )
        }
    }
    roughLine(Offset(size.width * .18f, size.height * .76f), Offset(size.width * .82f, size.height * .76f), BoardBlue.copy(alpha = .6f), sw * .55f)
}

private fun DrawScope.drawSkyWatcher(stage: Int, sw: Float, u: Float) {
    val horizon = size.height * .76f
    roughLine(Offset(size.width * .12f, horizon), Offset(size.width * .88f, horizon), BoardTeal, sw)
    val head = Offset(size.width * .32f, size.height * .48f)
    roughCircle(head, 12f * u, BoardInk, sw, fill = true)
    roughPath(listOf(head + Offset(-9f*u, 12f*u), Offset(head.x - 18f*u, horizon), Offset(head.x + 18f*u, horizon), head + Offset(9f*u, 12f*u)), BoardInk, sw)
    roughLine(Offset(head.x + 8f*u, head.y - 5f*u), Offset(size.width * .64f, size.height * .31f), BoardBlue, sw * 2f)
    roughCircle(Offset(size.width * .66f, size.height * .30f), 8f*u, BoardGold, sw, fill = true)
    if (stage > 2) {
        roughLine(Offset(size.width * .64f, size.height * .34f), Offset(size.width * .51f, horizon), BoardPencil, sw)
        roughLine(Offset(size.width * .64f, size.height * .34f), Offset(size.width * .73f, horizon), BoardPencil, sw)
    }
    if (stage > 3) drawConstellation(stage - 2, sw * .7f, u)
}

private fun DrawScope.drawSunStar(stage: Int, sw: Float, u: Float) {
    val sun = Offset(size.width * .36f, size.height * .55f)
    roughCircle(sun, 30f*u, BoardGold, sw * 1.4f, fill = true)
    if (stage > 1) {
        repeat(12) { i ->
            val a = i * PI / 6
            roughLine(
                sun + Offset(cos(a).toFloat() * 37f*u, sin(a).toFloat() * 37f*u),
                sun + Offset(cos(a).toFloat() * 49f*u, sin(a).toFloat() * 49f*u),
                BoardGold,
                sw
            )
        }
    }
    if (stage > 2) {
        roughCircle(Offset(size.width * .72f, size.height * .55f), 15f*u, BoardBlue, sw, fill = true)
        roughLine(Offset(size.width * .58f, size.height * .55f), Offset(size.width * .65f, size.height * .55f), BoardPencil, sw)
    }
}

private fun DrawScope.drawSolarSystem(stage: Int, sw: Float, u: Float) {
    val sun = Offset(size.width * .50f, size.height * .58f)
    val radii = listOf(.12f, .20f, .28f, .36f)
    radii.forEachIndexed { i, r ->
        if (stage > i) {
            drawOval(
                BoardBlue.copy(alpha = .50f),
                Offset(sun.x - size.width*r, sun.y - size.height*r*.54f),
                Size(size.width*r*2f, size.height*r*1.08f),
                style = Stroke(sw * .65f)
            )
        }
    }
    roughCircle(sun, 13f*u, BoardGold, sw, fill = true)
    val planets = listOf(
        Offset(.63f,.58f) to 3.5f, Offset(.70f,.48f) to 5f,
        Offset(.78f,.58f) to 5.5f, Offset(.85f,.48f) to 4f,
        Offset(.17f,.58f) to 8f, Offset(.25f,.47f) to 6f,
        Offset(.34f,.58f) to 5f, Offset(.41f,.47f) to 5f
    )
    planets.take((stage + 1).coerceAtMost(planets.size)).forEachIndexed { i, pair ->
        val p = Offset(size.width * pair.first.x, size.height * pair.first.y)
        roughCircle(p, pair.second * u, if (i == 2) BoardTeal else BoardBlue, sw * .8f, fill = true)
    }
}

private fun DrawScope.drawPlanetStar(stage: Int, sw: Float, u: Float) {
    val star = Offset(size.width * .29f, size.height * .55f)
    val planet = Offset(size.width * .72f, size.height * .55f)
    roughCircle(star, 25f*u, BoardGold, sw * 1.4f, fill = true)
    if (stage > 1) {
        repeat(8) { i ->
            val a = i * PI / 4
            roughLine(star + Offset(cos(a).toFloat()*30f*u, sin(a).toFloat()*30f*u), star + Offset(cos(a).toFloat()*39f*u, sin(a).toFloat()*39f*u), BoardGold, sw)
        }
        roughCircle(planet, 18f*u, BoardBlue, sw, fill = true)
    }
    if (stage > 2) {
        roughLine(Offset(size.width*.43f, size.height*.55f), Offset(size.width*.58f, size.height*.55f), BoardPencil, sw)
        roughPath(listOf(Offset(size.width*.55f,size.height*.51f), Offset(size.width*.59f,size.height*.55f), Offset(size.width*.55f,size.height*.59f)), BoardPencil, sw)
    }
}

private fun DrawScope.drawEarthMoon(stage: Int, sw: Float, u: Float) {
    val earth = Offset(size.width * .48f, size.height * .56f)
    drawOval(BoardBlue.copy(alpha = .65f), Offset(earth.x - 74f*u, earth.y - 38f*u), Size(148f*u, 76f*u), style = Stroke(sw))
    roughCircle(earth, 22f*u, BoardTeal, sw * 1.2f, fill = true)
    if (stage > 1) {
        roughPath(listOf(earth + Offset(-13f*u,-5f*u), earth + Offset(-5f*u,-15f*u), earth + Offset(2f*u,-3f*u), earth + Offset(13f*u,4f*u), earth + Offset(5f*u,14f*u), earth + Offset(-8f*u,9f*u)), BoardTeal, sw * 1.2f, close = true)
        roughCircle(Offset(size.width*.81f, size.height*.56f), 9f*u, BoardPencil, sw, fill = true)
    }
    if (stage > 2) {
        roughPath(listOf(Offset(size.width*.70f,size.height*.37f), Offset(size.width*.78f,size.height*.30f), Offset(size.width*.84f,size.height*.38f)), BoardGold, sw)
    }
}

private fun DrawScope.drawAsteroidsComet(stage: Int, sw: Float, u: Float) {
    val rocks = listOf(.18f to .38f, .28f to .63f, .38f to .43f, .49f to .67f, .58f to .38f, .66f to .63f)
    rocks.take(stage.coerceAtLeast(1)).forEachIndexed { i, p ->
        val c = Offset(size.width*p.first, size.height*p.second)
        roughCircle(c, (4f + i%3) * u, BoardPencil, sw * .75f, fill = true)
    }
    if (stage > 1) {
        val comet = Offset(size.width*.78f, size.height*.48f)
        roughCircle(comet, 10f*u, BoardGold, sw, fill = true)
        roughPath(listOf(comet + Offset(-8f*u,0f), Offset(size.width*.62f,size.height*.40f), Offset(size.width*.49f,size.height*.35f)), BoardBlue, sw * 2f)
        roughPath(listOf(comet + Offset(-8f*u,4f*u), Offset(size.width*.63f,size.height*.56f), Offset(size.width*.54f,size.height*.64f)), BoardTeal, sw)
    }
}

private fun DrawScope.drawGalaxy(stage: Int, sw: Float, u: Float) {
    val center = Offset(size.width*.52f, size.height*.56f)
    roughCircle(center, 8f*u, BoardGold, sw, fill = true)
    if (stage > 1) {
        for (arm in 0..2) {
            val angle = arm * 2.0 * PI / 3.0
            val points = (0..24).map { i ->
                val t = i / 24f
                val r = (12f + t * 74f) * u
                val a = angle + t * 2.1 * PI
                Offset(center.x + cos(a).toFloat()*r, center.y + sin(a).toFloat()*r*.48f)
            }
            roughPath(points, if (arm == 1) BoardTeal else BoardBlue, sw * .9f)
        }
    }
    if (stage > 3) {
        repeat(18) { i ->
            val x = size.width * (.18f + ((i*37)%67)/100f)
            val y = size.height * (.28f + ((i*19)%43)/100f)
            roughCircle(Offset(x,y), (1.4f + (i%3)*.6f)*u, BoardGold, sw*.55f)
        }
    }
}
