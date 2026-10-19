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
import android.os.Looper
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
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
import java.util.concurrent.Executors

private val TutorGreen = Color(0xFF24734B)
private val TutorDeep = Color(0xFF173D2A)
private val TutorGrey = Color(0xFF718075)
private val TutorPaper = Color(0xFFF7F9F5)
private val tutorExecutor = Executors.newSingleThreadExecutor()
private val tutorMainHandler = Handler(Looper.getMainLooper())


private data class TutorMessage(val role: String, val content: String, val visualLesson: JSONObject? = null, val interactiveLesson: JSONObject? = null)
private data class TutorSource(val title: String, val url: String)

private data class MoveItem(val icon: String, val name: String, val x: Float, val y: Float)

@Composable
private fun InteractiveLessonLab(chapter: String, topic: String, explanation: String) {
    val key = "$chapter $topic $explanation".lowercase()
    val title: String
    val hint: String
    val items: List<MoveItem>
    when {
        listOf("fraction", "numerator", "denominator", "half", "quarter").any { it in key } -> {
            title = "Build a fraction"; hint = "Drag equal pieces together to make one whole."
            items = listOf(MoveItem("🟩","1/4",.08f,.25f),MoveItem("🟩","1/4",.30f,.25f),MoveItem("🟩","1/4",.52f,.25f),MoveItem("⬜","1/4",.74f,.25f))
        }
        listOf("magnet","magnetic","attract","repel").any { it in key } -> {
            title = "Explore magnets"; hint = "Move the magnet near the metal objects and compare."
            items = listOf(MoveItem("🧲","Magnet",.08f,.28f),MoveItem("📎","Metal",.70f,.18f),MoveItem("📎","Metal",.70f,.56f),MoveItem("🪵","Wood",.38f,.58f))
        }
        listOf("water cycle","evaporation","condensation","precipitation","states of water").any { it in key } -> {
            title = "Move water through the cycle"; hint = "Drag water, vapour, clouds and rain through the stages."
            items = listOf(MoveItem("🌊","Water",.04f,.56f),MoveItem("💧","Vapour",.28f,.18f),MoveItem("☁️","Cloud",.52f,.18f),MoveItem("🌧️","Rain",.76f,.56f))
        }
        listOf("number line","negative","integer","zero","other side of zero").any { it in key } -> {
            title = "Explore the number line"; hint = "Drag the point left or right of zero."
            items = listOf(MoveItem("🔵","−3",.08f,.32f),MoveItem("🟢","0",.44f,.32f),MoveItem("🟠","+3",.76f,.32f))
        }
        listOf("solar system","planet","orbit","beyond earth").any { it in key } -> {
            title = "Explore planetary motion"; hint = "Drag a planet around the Sun to explore its position."
            items = listOf(MoveItem("☀️","Sun",.40f,.30f),MoveItem("🌍","Earth",.70f,.12f),MoveItem("🪐","Planet",.12f,.56f))
        }
        listOf("photosynthesis","plant","living creature","diversity in the living").any { it in key } -> {
            title = "Explore a plant"; hint = "Move sunlight, water and the leaf to explore the process."
            items = listOf(MoveItem("☀️","Sunlight",.06f,.12f),MoveItem("💧","Water",.30f,.55f),MoveItem("🌱","Plant",.50f,.30f),MoveItem("🍃","Leaf",.76f,.12f))
        }
        listOf("angle","lines and angles","ray").any { it in key } -> {
            title = "Explore angles"; hint = "Drag the ray markers to change their positions."
            items = listOf(MoveItem("📍","Vertex",.42f,.42f),MoveItem("➡️","Ray 1",.72f,.42f),MoveItem("↗️","Ray 2",.60f,.10f))
        }
        listOf("perimeter","area","symmetry","shape","square","rectangle").any { it in key } -> {
            title = "Explore shapes"; hint = "Drag the corners and compare the shape you make."
            items = listOf(MoveItem("🔹","Corner",.12f,.16f),MoveItem("🔹","Corner",.72f,.16f),MoveItem("🔹","Corner",.72f,.56f),MoveItem("🔹","Corner",.12f,.56f))
        }
        else -> {
            title = "Interactive concept lab"; hint = "Drag the objects around while the tutor explains this idea."
            items = listOf(MoveItem("🔵","Explore",.10f,.20f),MoveItem("🟢","Observe",.40f,.46f),MoveItem("🟠","Try it",.72f,.18f))
        }
    }
    var positions by remember(key) { mutableStateOf(items.map { Offset(it.x,it.y) }) }
    val motion = rememberInfiniteTransition(label = "lab-motion")
    val moving by motion.animateFloat(0f,1f,infiniteRepeatable(tween(2200),RepeatMode.Reverse),label="moving-particle")
    Surface(Modifier.fillMaxWidth().padding(top=8.dp), color=Color(0xFFEAF5EE), shape=RoundedCornerShape(18.dp), border=BorderStroke(1.dp,Color(0xFFD1E7D8))) {
        Column(Modifier.padding(12.dp), verticalArrangement=Arrangement.spacedBy(7.dp)) {
            Row(verticalAlignment=Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("TOUCH & EXPLORE",color=TutorGreen,fontSize=10.sp,fontWeight=FontWeight.Bold)
                    Text(title,color=TutorDeep,fontSize=14.sp,fontWeight=FontWeight.SemiBold)
                }
                TextButton(onClick={positions=items.map{Offset(it.x,it.y)}}){Text("Reset",color=TutorGreen)}
            }
            BoxWithConstraints(Modifier.fillMaxWidth().height(190.dp).background(Color.White,RoundedCornerShape(14.dp))) {
                val w=maxWidth; val h=maxHeight
                Canvas(Modifier.fillMaxSize()) {
                    drawLine(Color(0xFFB8D7C3),Offset(size.width*.05f,size.height*.84f),Offset(size.width*.95f,size.height*.84f),2.dp.toPx())
                    drawCircle(Color(0xFF58A66C),7.dp.toPx(),Offset(size.width*(.10f+.78f*moving),size.height*.84f))
                }
                items.forEachIndexed { index, item ->
                    val p=positions[index]
                    Column(
                        Modifier.offset { IntOffset((p.x*(w-68.dp).toPx()).roundToInt(),(p.y*(h-64.dp).toPx()).roundToInt()) }
                            .width(68.dp)
                            .pointerInput(key,index,w,h) {
                                detectDragGestures { change, drag ->
                                    change.consume()
                                    val maxX=(w-68.dp).toPx().coerceAtLeast(1f)
                                    val maxY=(h-64.dp).toPx().coerceAtLeast(1f)
                                    positions=positions.toMutableList().also { list ->
                                        val old=list[index]
                                        list[index]=Offset((old.x+drag.x/maxX).coerceIn(0f,1f),(old.y+drag.y/maxY).coerceIn(0f,1f))
                                    }
                                }
                            },
                        horizontalAlignment=Alignment.CenterHorizontally
                    ) {
                        Surface(color=Color(0xFFF4FAF6),shape=RoundedCornerShape(12.dp),border=BorderStroke(1.dp,Color(0xFFD1E7D8))) {
                            Text(item.icon,Modifier.padding(horizontal=10.dp,vertical=5.dp),fontSize=25.sp)
                        }
                        Text(item.name,color=TutorDeep,fontSize=10.sp,maxLines=1)
                    }
                }
            }
            Text(hint,color=TutorGrey,fontSize=12.sp,lineHeight=16.sp)
            Text("Touch and hold an object, then drag it. Use Reset to start again.",color=TutorGreen,fontSize=10.sp)
        }
    }
}


@Composable
private fun DatabaseInteractiveLessonLab(lesson: JSONObject) {
    val scene = lesson.optString("scene_type", "explore")
    val caption = lesson.optString("caption", "Move the objects and observe what changes.")
    val title = lesson.optString("title", lesson.optString("topic", "Explore this concept"))
    val key = lesson.optString("id", title)
    val raw = lesson.optJSONArray("objects")
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
            "angle_builder" -> listOf(
                MoveItem("📍", "Vertex", .42f, .43f), MoveItem("➡️", "Ray A", .76f, .43f),
                MoveItem("↗️", "Ray B", .60f, .12f)
            )
            "integer_line" -> listOf(
                MoveItem("🔵", "−3", .15f, .30f), MoveItem("🟢", "0", .48f, .30f),
                MoveItem("🟠", "+3", .80f, .30f)
            )
            "measure_length" -> listOf(MoveItem("📍", "Start", .12f, .30f), MoveItem("📍", "End", .72f, .30f))
            "motion_track" -> listOf(MoveItem("🏁", "Start", .08f, .30f), MoveItem("🚗", "Toy", .45f, .30f), MoveItem("🏁", "Finish", .84f, .30f))
            "bar_chart" -> listOf(MoveItem("A", "Group A", .18f, .12f), MoveItem("B", "Group B", .46f, .12f), MoveItem("C", "Group C", .74f, .12f))
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
    var feedback by remember(key) { mutableStateOf("Touch an object, drag it, and notice what changes.") }
    var activeStep by remember(key) { mutableIntStateOf(0) }
    var heatLevel by remember(key) { mutableFloatStateOf(.28f) }
    var chartValue by remember(key) { mutableFloatStateOf(.62f) }
    val steps = lesson.optJSONArray("steps")
    val stepCount = (steps?.length() ?: 0).coerceAtLeast(1)
    val motion = rememberInfiniteTransition(label = "interactive-db-motion")
    val pulse by motion.animateFloat(0f, 1f, infiniteRepeatable(tween(1800), RepeatMode.Reverse), label = "pulse")
    val vertex = positions.getOrNull(0) ?: Offset(.5f, .5f)
    val angle = if (scene == "angle_builder" && positions.size >= 3) {
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
    Surface(Modifier.fillMaxWidth().padding(top=8.dp), color=Color(0xFFEAF5EE), shape=RoundedCornerShape(18.dp), border=BorderStroke(1.dp, Color(0xFFD1E7D8))) {
        Column(Modifier.padding(12.dp), verticalArrangement=Arrangement.spacedBy(7.dp)) {
            Row(verticalAlignment=Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("DATABASE INTERACTIVE LESSON", color=TutorGreen, fontSize=10.sp, fontWeight=FontWeight.Bold)
                    Text(title, color=TutorDeep, fontSize=14.sp, fontWeight=FontWeight.SemiBold)
                }
                TextButton(onClick={ positions=items.map { Offset(it.x,it.y) }; feedback="Reset. Try another arrangement."; activeStep=0 }) { Text("Reset", color=TutorGreen) }
            }
            BoxWithConstraints(Modifier.fillMaxWidth().height(190.dp).background(Color.White, RoundedCornerShape(14.dp))) {
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
                            drawCircle(Color(0xFFB9DCC5), radius, center, style=androidx.compose.ui.graphics.drawscope.Stroke(2.dp.toPx()))
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
                                drawRect(Color(0xFF7CB58E),Offset(left,baseY-size.height*heights[i]),androidx.compose.ui.geometry.Size(barWidth,size.height*heights[i]))
                            }
                            drawLine(Color(0xFF578368),Offset(size.width*.08f,baseY),Offset(size.width*.94f,baseY),2.dp.toPx())
                        }
                        "factor_tree" -> if (positions.size >= 3) {
                            val root=positions[0]
                            positions.drop(1).forEach { p -> drawLine(Color(0xFF24734B),Offset(root.x*size.width,root.y*size.height),Offset(p.x*size.width,p.y*size.height),2.dp.toPx()) }
                        }
                        "pattern_builder" -> if (positions.size >= 2) {
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
                        "angle_builder" -> if (positions.size >= 3) {
                            val v=positions[0]
                            positions.drop(1).take(2).forEach { p -> drawLine(Color(0xFF24734B), Offset(v.x*size.width,v.y*size.height), Offset(p.x*size.width,p.y*size.height), 3.dp.toPx()) }
                            drawCircle(Color(0xFF24734B), 5.dp.toPx(), Offset(v.x*size.width,v.y*size.height))
                        }
                        "symmetry_mirror" -> drawLine(Color(0xFF7F9BFF), Offset(size.width*.5f,0f), Offset(size.width*.5f,size.height), 2.dp.toPx())
                        "area_grid" -> {
                            for (i in 1..8) drawLine(Color(0xFFE1E9E3),Offset(size.width*i/9f,0f),Offset(size.width*i/9f,size.height),1.dp.toPx())
                            for (i in 1..4) drawLine(Color(0xFFE1E9E3),Offset(0f,size.height*i/5f),Offset(size.width,size.height*i/5f),1.dp.toPx())
                        }
                        else -> {
                            drawLine(Color(0xFFB8D7C3),Offset(size.width*.05f,size.height*.86f),Offset(size.width*.95f,size.height*.86f),2.dp.toPx())
                            drawCircle(Color(0xFF58A66C),6.dp.toPx(),Offset(size.width*(.1f+.78f*pulse),size.height*.86f))
                        }
                    }
                }
                items.forEachIndexed { index, item ->
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
                                        "magnet_test" -> if (magnetic) "Attraction! Iron and steel are pulled toward the magnet; wood is not." else "Bring an iron or steel object close to the magnet."
                                        "fraction_builder" -> "Move equal pieces together. Each piece is one-quarter of the same whole."
                                        "angle_builder" -> "The angle is about $angle°. Move Ray B to make it wider or narrower."
                                        "integer_line" -> "Numbers to the left are smaller; numbers to the right are greater."
                                        "area_grid" -> "Count the unit squares covered by the shape to estimate its area."
                                        "symmetry_mirror" -> "Compare the two sides of the mirror line."
                                        else -> caption
                                    }
                                }
                            },
                        horizontalAlignment=Alignment.CenterHorizontally
                    ) {
                        Surface(color=if(scene=="fraction_builder" && item.name=="1/4") Color(0xFFB9E2C5) else Color(0xFFF4FAF6),shape=RoundedCornerShape(12.dp),border=BorderStroke(1.dp,Color(0xFFD1E7D8))) {
                            Text(item.icon,Modifier.padding(horizontal=10.dp,vertical=5.dp),fontSize=24.sp)
                        }
                        Text(item.name,color=TutorDeep,fontSize=10.sp,maxLines=1)
                    }
                }
            }
            if (scene=="angle_builder") Text("Current angle: $angle°", color=TutorGreen, fontSize=12.sp, fontWeight=FontWeight.Bold)
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
            if (steps != null && steps.length()>0) {
                val current=steps.optJSONObject(activeStep.coerceIn(0,steps.length()-1))
                Text("Step ${activeStep+1}/$stepCount · ${current?.optString("title","Try")}: ${current?.optString("text","Explore the objects.")}", color=TutorGreen, fontSize=11.sp)
                Row(horizontalArrangement=Arrangement.spacedBy(8.dp), verticalAlignment=Alignment.CenterVertically) {
                    OutlinedButton(onClick={activeStep=(activeStep-1).coerceAtLeast(0)}, enabled=activeStep>0) { Text("Previous") }
                    Button(onClick={activeStep=(activeStep+1).coerceAtMost(stepCount-1)}, enabled=activeStep<stepCount-1, colors=ButtonDefaults.buttonColors(containerColor=TutorGreen)) { Text("Next step") }
                }
            }
            val challenge=lesson.optJSONObject("challenge")
            if(challenge!=null && challenge.optString("question").isNotBlank()) Text("Try this: ${challenge.optString("question")}", color=TutorDeep, fontSize=12.sp, fontWeight=FontWeight.SemiBold)
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
        color = Color(0xFFEAF5EE),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, Color(0xFFD1E7D8))
    ) {
        Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
            Text("SEE IT HAPPEN", color = TutorGreen, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            Text(lesson.optString("title", lesson.optString("topic", "Explore this idea")), color = TutorDeep, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(3.dp), verticalAlignment = Alignment.CenterVertically) {
                visibleSteps.forEachIndexed { index, step ->
                    if (index > 0) Text("→", color = TutorGreen, fontSize = 13.sp)
                    Column(
                        Modifier.weight(1f).background(if (index == activeIndex) Color.White else Color(0xFFDDEDE2), RoundedCornerShape(10.dp)).padding(horizontal = 3.dp, vertical = 7.dp),
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
        color = Color(0xFFEAF5EE),
        shape = RoundedCornerShape(18.dp),
        border = BorderStroke(1.dp, Color(0xFFD1E7D8))
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
internal fun TutorScreen(
    grade: Int,
    board: String,
    medium: String,
    appLanguage: String,
    studentName: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val messages = remember {
        mutableStateListOf(
            TutorMessage(
                "assistant",
                when (appLanguage) {
                    "Tanglish" -> "Hi" + (if (studentName.isBlank()) "" else ", " + studentName) + "! Namma onna konjam konjama kathukkalaam. Enna concept purinjukkanum?"
                    "தமிழ்" -> "வணக்கம்" + (if (studentName.isBlank()) "" else ", " + studentName) + "! நிதானமாக ஒவ்வொரு படியாகவும் கற்றுக்கொள்ளலாம். இன்று என்ன புரிந்துகொள்ள வேண்டும்?"
                    else -> "Hi" + (if (studentName.isBlank()) "" else ", " + studentName) + "! I'm here to help. We'll take it one small step at a time. What would you like to understand today?"
                }
            )
        )
    }
    var input by remember { mutableStateOf("") }
    var subject by remember { mutableStateOf("General") }
    var chapter by remember { mutableStateOf("") }
    var topic by remember { mutableStateOf("") }
    var chapterMenuExpanded by remember { mutableStateOf(false) }
    var topicMenuExpanded by remember { mutableStateOf(false) }
    var chapterOptions by remember { mutableStateOf<List<Pair<String, List<String>>>>(emptyList()) }
    var outlineLoading by remember { mutableStateOf(false) }
    var loading by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("") }
    var speakReplies by remember { mutableStateOf(true) }
    var speechActive by remember { mutableStateOf(false) }
    var voiceReady by remember { mutableStateOf(false) }
    var selectedLanguage by remember { mutableStateOf(appLanguage) }
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
    fun loadCurriculumOutline(forSubject: String) {
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
                        val topics = (0 until topicsJson.length()).map { topicsJson.optString(it) }
                            .filter { it.isNotBlank() }.distinct().take(20)
                        title to topics
                    }
                } finally {
                    connection.disconnect()
                }
            }
            tutorMainHandler.post {
                chapterOptions = result.getOrDefault(emptyList())
                outlineLoading = false
            }
        }
    }

    LaunchedEffect(subject) {
        chapter = ""
        topic = ""
        loadCurriculumOutline(subject)
    }

    LaunchedEffect(chapter, topic, selectedLanguage) {
        if (messages.size == 1 && messages.firstOrNull()?.role == "assistant") {
            val greeting = when (selectedLanguage) {
                "Tanglish" -> when {
                    topic.isNotBlank() -> "Seri! Ippo $topic pathi padikkalaam. Indha topic-la enna therinjukkanum?"
                    chapter.isNotBlank() -> "$chapter chapter open panniyachu. Endha topic-a first kathukkanum?"
                    else -> "Hi" + (if (studentName.isBlank()) "" else ", $studentName") + "! Namma onna konjam konjama kathukkalaam. Enna concept purinjukkanum?"
                }
                "தமிழ்" -> when {
                    topic.isNotBlank() -> "சரி! இப்போது $topic பற்றி கற்கலாம். இந்தத் தலைப்பில் எதை முதலில் தெரிந்துகொள்ள விரும்புகிறாய்?"
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

    DisposableEffect(context) {
        val engine = TextToSpeech(context) { result ->
            tutorMainHandler.post { voiceReady = result == TextToSpeech.SUCCESS }
        }
        engine.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {}
            override fun onDone(utteranceId: String?) {
                tutorMainHandler.post { speechActive = false }
            }
            @Deprecated("Deprecated in Java")
            override fun onError(utteranceId: String?) {
                tutorMainHandler.post { speechActive = false }
            }
        })
        ttsState.value = engine
        onDispose {
            engine.stop()
            engine.shutdown()
            ttsState.value = null
            audioPlayer.value?.release()
            audioPlayer.value = null
        }
    }

    fun speakWithDeviceTts(text: String) {
        status = "Gemini voice unavailable; using device voice."
        val engine = ttsState.value ?: run { speechActive = false; return }
        val locale = when (selectedLanguage) {
            "Tanglish" -> Locale("en", "IN")
            "தமிழ்" -> Locale("ta", "IN")
            else -> Locale("en", "IN")
        }
        val availability = engine.isLanguageAvailable(locale)
        if (availability < TextToSpeech.LANG_AVAILABLE) {
            status = if (selectedLanguage == "தமிழ்") {
                "Natural voice unavailable and Tamil voice isn't installed on this phone."
            } else {
                "Natural voice unavailable and an Indian English voice isn't installed."
            }
            speechActive = false
            return
        }
        engine.language = locale
        engine.setSpeechRate(0.88f)
        engine.setPitch(1.02f)
        engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, "padippupal-tutor")
    }

    fun speak(text: String) {
        // Auto-read and the manual speaker button must not launch overlapping
        // Gemini requests/players, which can sound like a stuck repeating tutor.
        if (speechActive || text.isBlank()) return
        speechActive = true
        val base = BuildConfig.CURRICULUM_API_BASE_URL.trim().trimEnd('/')
        if (!base.startsWith("https://")) {
            speakWithDeviceTts(text)
            return
        }
        tutorExecutor.execute {
            val audioFile = File(context.cacheDir, "padippupal-voice-${System.nanoTime()}.wav")
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
                        runCatching {
                            audioPlayer.value?.release()
                            val player = MediaPlayer()
                            audioPlayer.value = player
                            player.setDataSource(audioFile.absolutePath)
                            player.setOnCompletionListener {
                                it.release()
                                if (audioPlayer.value === it) audioPlayer.value = null
                                audioFile.delete()
                                speechActive = false
                            }
                            player.setOnErrorListener { failedPlayer, _, _ ->
                                failedPlayer.release()
                                if (audioPlayer.value === failedPlayer) audioPlayer.value = null
                                audioFile.delete()
                                speakWithDeviceTts(text)
                                true
                            }
                            player.prepare()
                            player.start()
                            status = "Speaking with Gemini natural voice."
                        }.onFailure {
                            audioFile.delete()
                            speakWithDeviceTts(text)
                        }
                    },
                    onFailure = {
                        audioFile.delete()
                        status = "Gemini voice request failed; using device voice. Check network and voice service configuration."
                        speakWithDeviceTts(text)
                    }
                )
            }
        }
    }

    fun sendMessage() {
        val question = input.trim()
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
                require(base.startsWith("https://")) { "The secure PadippuPal API URL is not configured." }
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
                    val answer = response.optString("answer").trim()
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
                        if (speakReplies) speak(answer)
                    },
                    onFailure = { error ->
                        status = error.message ?: "Couldn't reach the tutor. Please try again."
                    }
                )
            }
        }
    }

    Column(
        modifier = modifier.fillMaxSize().background(TutorPaper).padding(horizontal = 16.dp).imePadding(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
            Column(Modifier.weight(1f)) {
                Text("Your AI study buddy", fontSize = 20.sp, fontWeight = FontWeight.ExtraBold, color = TutorDeep, maxLines = 1)
                Text("Class $grade · $board", fontSize = 11.sp, color = TutorGrey)
            }
            Icon(Icons.Default.GraphicEq, contentDescription = "Voice tutor", tint = TutorGreen, modifier = Modifier.size(30.dp))
        }
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = TutorGreen,
            shape = RoundedCornerShape(22.dp),
            shadowElevation = 4.dp
        ) {
            Row(
                Modifier.fillMaxWidth().padding(horizontal = 13.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Box(Modifier.size(42.dp).background(Color.White.copy(alpha = 0.16f), RoundedCornerShape(14.dp)), contentAlignment = Alignment.Center) {
                    Icon(Icons.Default.GraphicEq, contentDescription = null, tint = Color.White, modifier = Modifier.size(26.dp))
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text("Talk or type to learn", fontSize = 15.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    Text("English, Tanglish or Tamil", fontSize = 11.sp, color = Color.White.copy(alpha = 0.9f))
                }
                if (listening) CircularProgressIndicator(Modifier.size(24.dp), color = Color.White, strokeWidth = 2.dp)
                else Icon(Icons.Default.Mic, contentDescription = "Voice input available", tint = Color.White, modifier = Modifier.size(26.dp))
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
            Text("1 · Choose a subject", color = TutorGrey, fontSize = 12.sp)
            Row(
                modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(7.dp)
            ) {
                listOf("Mathematics", "Science", "English", "Tamil", "Social Science", "Computer Science", "General").forEach { option ->
                    FilterChip(
                        selected = subject == option,
                        onClick = { if (subject != option) subject = option },
                        label = { Text(option, fontSize = 11.sp) }
                    )
                }
            }
            Box(Modifier.fillMaxWidth()) {
                OutlinedButton(
                    onClick = { chapterMenuExpanded = true },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !outlineLoading && chapterOptions.isNotEmpty(),
                    shape = RoundedCornerShape(10.dp),
                    contentPadding = PaddingValues(horizontal = 14.dp, vertical = 15.dp)
                ) {
                    Text(
                        if (chapter.isBlank()) "2 · Choose a chapter" else chapter,
                        modifier = Modifier.weight(1f),
                        color = if (chapter.isBlank()) TutorGrey else TutorDeep,
                        maxLines = 2
                    )
                    Icon(Icons.Default.ArrowBack, contentDescription = null, modifier = Modifier.size(18.dp))
                }
                DropdownMenu(
                    expanded = chapterMenuExpanded,
                    onDismissRequest = { chapterMenuExpanded = false },
                    modifier = Modifier.fillMaxWidth(.9f).heightIn(max = 340.dp)
                ) {
                    chapterOptions.forEachIndexed { index, option ->
                        DropdownMenuItem(
                            text = { Text("${index + 1}. ${option.first}", maxLines = 2) },
                            onClick = {
                                chapter = option.first
                                topic = ""
                                chapterMenuExpanded = false
                            }
                        )
                    }
                }
            }
            if (outlineLoading) {
                LinearProgressIndicator(Modifier.fillMaxWidth(), color = TutorGreen)
            } else if (chapterOptions.isEmpty() && subject != "General") {
                Text("No chapter list is available yet for this subject and class.", color = TutorGrey, fontSize = 11.sp)
            }
            val topicOptions = chapterOptions.firstOrNull { it.first == chapter }?.second.orEmpty()
            Box(Modifier.fillMaxWidth()) {
                OutlinedButton(
                    onClick = { topicMenuExpanded = true },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = chapter.isNotBlank() && topicOptions.isNotEmpty(),
                    shape = RoundedCornerShape(10.dp),
                    contentPadding = PaddingValues(horizontal = 14.dp, vertical = 15.dp)
                ) {
                    Text(
                        if (topic.isBlank()) "3 · Choose a concept" else topic,
                        modifier = Modifier.weight(1f),
                        color = if (topic.isBlank()) TutorGrey else TutorDeep,
                        maxLines = 2
                    )
                }
                DropdownMenu(
                    expanded = topicMenuExpanded,
                    onDismissRequest = { topicMenuExpanded = false },
                    modifier = Modifier.fillMaxWidth(.9f).heightIn(max = 340.dp)
                ) {
                    topicOptions.forEachIndexed { index, topicTitle ->
                        DropdownMenuItem(
                            text = { Text("${index + 1}. $topicTitle", maxLines = 2) },
                            onClick = {
                                topic = topicTitle
                                topicMenuExpanded = false
                            }
                        )
                    }
                }
            }
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text("Explain in", color = TutorGrey, fontSize = 12.sp)
            listOf("English", "Tanglish", "தமிழ்").forEach { option ->
                FilterChip(
                    selected = selectedLanguage == option,
                    onClick = { selectedLanguage = option },
                    label = { Text(option, fontSize = 11.sp) }
                )
            }
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Read replies aloud", modifier = Modifier.weight(1f), color = TutorDeep, fontSize = 13.sp)
            Switch(checked = speakReplies, onCheckedChange = { speakReplies = it })
            IconButton(onClick = {
                val lastAnswer = messages.lastOrNull { it.role == "assistant" }?.content
                if (lastAnswer != null) speak(lastAnswer)
            }) {
                Icon(if (speakReplies) Icons.Default.VolumeUp else Icons.Default.VolumeOff, contentDescription = "Speak latest reply", tint = TutorGreen)
            }
        }
        LazyColumn(
            modifier = Modifier.weight(1f).fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 6.dp)
        ) {
            items(messages) { message ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = if (message.role == "user") Arrangement.End else Arrangement.Start
                ) {
                    Surface(
                        color = if (message.role == "user") TutorGreen else Color.White,
                        shape = RoundedCornerShape(
                            topStart = 18.dp, topEnd = 18.dp,
                            bottomStart = if (message.role == "user") 18.dp else 5.dp,
                            bottomEnd = if (message.role == "user") 5.dp else 18.dp
                        ),
                        shadowElevation = 1.dp,
                        modifier = Modifier.widthIn(max = 320.dp)
                    ) {
                        Column(Modifier.padding(14.dp)) {
                            Text(
                                message.content,
                                color = if (message.role == "user") Color.White else TutorDeep,
                                fontSize = 15.sp,
                                lineHeight = 23.sp
                            )
                            if (message.role == "assistant") {
                                val lessonAnimation = message.visualLesson ?: message.interactiveLesson
                                if (lessonAnimation != null) DatabaseLessonVisual(lessonAnimation)
                            }
                        }
                    }
                }
            }
            if (loading) {
                item {
                    Surface(color = Color.White, shape = RoundedCornerShape(16.dp)) {
                        Row(Modifier.padding(13.dp), verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp, color = TutorGreen)
                            Text("  Let's work it out together…", color = TutorGrey, fontSize = 13.sp)
                        }
                    }
                }
            }
        }
        if (status.isNotBlank()) Text(status, color = TutorGrey, fontSize = 11.sp, lineHeight = 15.sp)
        if (lastSources.isNotEmpty()) {
            Text("Curriculum: " + lastSources.joinToString { it.title }, color = TutorGreen, fontSize = 10.sp, maxLines = 2)
        }
        Row(
            modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
            verticalAlignment = Alignment.Bottom,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedTextField(
                value = input,
                onValueChange = { input = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Type a question or tap the mic…") },
                shape = RoundedCornerShape(18.dp),
                maxLines = 4,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = { sendMessage() })
            )
            FilledIconButton(
                onClick = {
                    if (listening) {
                        speechRecognizer?.stopListening()
                        listening = false
                    } else if (context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                        startVoiceInput()
                    } else {
                        voicePermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    }
                },
                enabled = !loading,
                modifier = Modifier.size(52.dp),
                colors = IconButtonDefaults.filledIconButtonColors(
                    containerColor = if (listening) Color(0xFFB3261E) else TutorGreen,
                    contentColor = Color.White
                )
            ) {
                Icon(if (listening) Icons.Default.MicOff else Icons.Default.Mic, contentDescription = if (listening) "Stop voice input" else "Ask by voice")
            }
            FilledIconButton(
                onClick = { sendMessage() },
                enabled = !loading && input.isNotBlank(),
                modifier = Modifier.size(52.dp)
            ) {
                Icon(Icons.Default.Send, contentDescription = "Send question")
            }
        }
        if (!voiceReady) {
            Text("Voice replies use Gemini when available; voice input uses your phone's speech service.", color = TutorGrey, fontSize = 10.sp)
        }
    }
}
}
