package com.padippupal.app

import android.speech.tts.TextToSpeech
import android.os.Handler
import android.os.Looper
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.GraphicEq
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.VolumeUp
import androidx.compose.material.icons.filled.VolumeOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
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
import java.nio.charset.StandardCharsets
import java.util.Locale
import java.util.concurrent.Executors

private val TutorGreen = Color(0xFF24734B)
private val TutorDeep = Color(0xFF173D2A)
private val TutorGrey = Color(0xFF718075)
private val TutorPaper = Color(0xFFF7F9F5)
private val tutorExecutor = Executors.newSingleThreadExecutor()
private val tutorMainHandler = Handler(Looper.getMainLooper())

private data class TutorMessage(val role: String, val content: String)
private data class TutorSource(val title: String, val url: String)

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
    var loading by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("") }
    var speakReplies by remember { mutableStateOf(true) }
    var voiceReady by remember { mutableStateOf(false) }
    var selectedLanguage by remember { mutableStateOf(appLanguage) }
    var lastSources by remember { mutableStateOf<List<TutorSource>>(emptyList()) }
    val ttsState = remember { mutableStateOf<TextToSpeech?>(null) }

    DisposableEffect(context) {
        val engine = TextToSpeech(context) { result ->
            tutorMainHandler.post { voiceReady = result == TextToSpeech.SUCCESS }
        }
        ttsState.value = engine
        onDispose {
            engine.stop()
            engine.shutdown()
            ttsState.value = null
        }
    }

    fun speak(text: String) {
        val engine = ttsState.value ?: return
        val locale = when (selectedLanguage) {
            "Tanglish" -> Locale("en", "IN")
            "தமிழ்" -> Locale("ta", "IN")
            else -> Locale("en", "IN")
        }
        val availability = engine.isLanguageAvailable(locale)
        if (availability < TextToSpeech.LANG_AVAILABLE) {
            status = if (selectedLanguage == "தமிழ்") {
                "Tamil voice isn't installed on this phone yet. Install a Tamil voice in Android text-to-speech settings."
            } else {
                "An Indian English voice isn't available. Check Android text-to-speech settings."
            }
            return
        }
        engine.language = locale
        engine.setSpeechRate(0.88f)
        engine.setPitch(1.02f)
        engine.speak(text, TextToSpeech.QUEUE_FLUSH, null, "padippupal-tutor")
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
                    .put("subject", "General")
                    .put("medium", medium)
                    .put("app_language", selectedLanguage)
                    .put("student_name", studentName)
                    .put("message", question)
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
                    val sources = mutableListOf<TutorSource>()
                    val array = response.optJSONArray("sources")
                    if (array != null) for (i in 0 until array.length()) {
                        val item = array.optJSONObject(i) ?: continue
                        sources += TutorSource(item.optString("title", "Curriculum source"), item.optString("url", ""))
                    }
                    answer to sources
                } finally {
                    connection.disconnect()
                }
            }
            tutorMainHandler.post {
                loading = false
                outcome.fold(
                    onSuccess = { (answer, sources) ->
                        messages.add(TutorMessage("assistant", answer))
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
        modifier = modifier.fillMaxSize().background(TutorPaper).padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
            Column(Modifier.weight(1f)) {
                Text("Your gentle tutor", fontSize = 23.sp, fontWeight = FontWeight.ExtraBold, color = TutorDeep)
                Text("Class $grade · $board", fontSize = 11.sp, color = TutorGrey)
            }
            Icon(Icons.Default.GraphicEq, contentDescription = "Voice tutor", tint = TutorGreen, modifier = Modifier.size(28.dp))
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
                        Text(
                            message.content,
                            modifier = Modifier.padding(14.dp),
                            color = if (message.role == "user") Color.White else TutorDeep,
                            fontSize = 15.sp,
                            lineHeight = 23.sp
                        )
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
                placeholder = { Text("Ask anything you're learning…") },
                shape = RoundedCornerShape(18.dp),
                maxLines = 4,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = { sendMessage() })
            )
            FilledIconButton(
                onClick = { sendMessage() },
                enabled = !loading && input.isNotBlank(),
                modifier = Modifier.size(52.dp)
            ) {
                Icon(Icons.Default.Send, contentDescription = "Send question")
            }
        }
        if (!voiceReady) {
            Text("Voice availability depends on the speech engine installed on this phone.", color = TutorGrey, fontSize = 10.sp)
        }
    }
}
