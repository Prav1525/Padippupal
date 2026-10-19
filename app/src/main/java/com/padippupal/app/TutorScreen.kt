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
import androidx.compose.foundation.layout.*
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
    var subject by remember { mutableStateOf("Science") }
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
                Text("Your AI study buddy", fontSize = 23.sp, fontWeight = FontWeight.ExtraBold, color = TutorDeep)
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
                Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 15.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Box(Modifier.size(52.dp).background(Color.White.copy(alpha = 0.16f), RoundedCornerShape(17.dp)), contentAlignment = Alignment.Center) {
                    Icon(Icons.Default.GraphicEq, contentDescription = null, tint = Color.White, modifier = Modifier.size(31.dp))
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text("Talk or type to learn", fontSize = 17.sp, fontWeight = FontWeight.Bold, color = Color.White)
                    Text("Ask in English, Tanglish or Tamil", fontSize = 12.sp, color = Color.White.copy(alpha = 0.9f))
                }
                if (listening) CircularProgressIndicator(Modifier.size(24.dp), color = Color.White, strokeWidth = 2.dp)
                else Icon(Icons.Default.Mic, contentDescription = "Voice input available", tint = Color.White, modifier = Modifier.size(26.dp))
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
