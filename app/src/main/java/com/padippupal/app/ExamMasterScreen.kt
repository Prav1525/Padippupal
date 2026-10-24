package com.padippupal.app

import android.content.ContentValues
import android.content.Intent
import android.os.Build
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.Base64
import java.util.concurrent.Executors

private val examExecutor = Executors.newSingleThreadExecutor()
private val examHandler = Handler(Looper.getMainLooper())
private val examGreen = Color(0xFF4169E1)
private val examInk = Color(0xFF172033)
private val examGrey = Color(0xFF64748B)

private data class ExamChapter(val title: String, val count: Int)

@Composable
internal fun ExamMasterScreen(
    studentName: String,
    board: String,
    medium: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val baseUrl = BuildConfig.CURRICULUM_API_BASE_URL.trimEnd('/')
    var chapters by remember { mutableStateOf<List<ExamChapter>>(emptyList()) }
    var selected by remember { mutableStateOf(setOf<String>()) }
    var questionCount by remember { mutableIntStateOf(15) }
    var examTitle by remember { mutableStateOf("Science Practice Examination") }
    var loading by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("Loading the Class 6 Science question bank…") }
    var studentPdf by remember { mutableStateOf<ByteArray?>(null) }
    var parentPdf by remember { mutableStateOf<ByteArray?>(null) }
    var studentFile by remember { mutableStateOf<android.net.Uri?>(null) }
    var parentFile by remember { mutableStateOf<android.net.Uri?>(null) }
    var mixSummary by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        examExecutor.execute {
            val result = runCatching {
                val connection = (URL("$baseUrl/exam-master/catalog").openConnection() as HttpURLConnection)
                connection.connectTimeout = 15000
                connection.readTimeout = 20000
                try {
                    if (connection.responseCode !in 200..299) error("Question bank returned HTTP ${connection.responseCode}")
                    val json = JSONObject(connection.inputStream.bufferedReader().use { it.readText() })
                    val array = json.optJSONArray("chapters") ?: JSONArray()
                    val rows = (0 until array.length()).mapNotNull { i ->
                        val item = array.optJSONObject(i) ?: return@mapNotNull null
                        ExamChapter(item.optString("title"), item.optInt("question_count"))
                    }
                    rows to json.optInt("question_bank_count")
                } finally { connection.disconnect() }
            }
            examHandler.post {
                result.fold(
                    onSuccess = { (rows, count) ->
                        chapters = rows
                        selected = rows.take(3).map { it.title }.toSet()
                        status = "Ready · $count curated practice questions across ${rows.size} chapters."
                    },
                    onFailure = { status = "Could not load Exam Master: ${it.message ?: "connection error"}" }
                )
            }
        }
    }

    fun generate() {
        if (selected.isEmpty()) { status = "Choose at least one chapter."; return }
        loading = true
        studentPdf = null
        parentPdf = null
        studentFile = null
        parentFile = null
        status = "Preparing your question paper and parent answer key…"
        examExecutor.execute {
            val result = runCatching {
                val payload = JSONObject()
                    .put("board", "CBSE")
                    .put("class_level", 6)
                    .put("subject", "Science")
                    .put("medium", if (medium.isBlank()) "English" else medium)
                    .put("selected_chapters", JSONArray(selected.toList()))
                    .put("question_count", questionCount)
                    .put("student_name", studentName)
                    .put("exam_title", examTitle.ifBlank { "Science Practice Examination" })
                val connection = (URL("$baseUrl/exam-master/generate").openConnection() as HttpURLConnection)
                connection.requestMethod = "POST"
                connection.connectTimeout = 20000
                connection.readTimeout = 60000
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.setRequestProperty("Accept", "application/json")
                try {
                    connection.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) }
                    val code = connection.responseCode
                    val body = (if (code in 200..299) connection.inputStream else connection.errorStream)
                        ?.bufferedReader()?.use { it.readText() }.orEmpty()
                    if (code !in 200..299) {
                        val detail = runCatching { JSONObject(body).optString("detail", body) }.getOrDefault(body)
                        error("Generation failed (HTTP $code): $detail")
                    }
                    val json = JSONObject(body)
                    val student = android.util.Base64.decode(json.getString("student_pdf_base64"), android.util.Base64.DEFAULT)
                    val parent = android.util.Base64.decode(json.getString("parent_key_pdf_base64"), android.util.Base64.DEFAULT)
                    val mix = json.optJSONObject("source_mix")
                    Triple(student, parent, "${json.optInt("question_count")} questions · ${json.optInt("maximum_marks")} marks · ${mix?.optInt("syllabus_aligned_practice_variants") ?: 0} syllabus practice variants / ${mix?.optInt("chapter_context_practice_variants") ?: 0} chapter-context variants")
                } finally { connection.disconnect() }
            }
            examHandler.post {
                loading = false
                result.fold(
                    onSuccess = { (student, parent, mix) ->
                        studentPdf = student
                        parentPdf = parent
                        mixSummary = mix
                        status = "Both PDFs generated. Save each file to your Downloads folder."
                    },
                    onFailure = { status = it.message ?: "Could not generate the PDFs." }
                )
            }
        }
    }

    fun savePdf(bytes: ByteArray, filename: String, share: Boolean): android.net.Uri? {
        return runCatching {
            val resolver = context.contentResolver
            val values = ContentValues().apply {
                put(MediaStore.Downloads.DISPLAY_NAME, filename)
                put(MediaStore.Downloads.MIME_TYPE, "application/pdf")
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) put(MediaStore.Downloads.IS_PENDING, 1)
            }
            val uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)
                ?: error("Could not create a file in Downloads")
            resolver.openOutputStream(uri)?.use { it.write(bytes) } ?: error("Could not write the PDF")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val done = ContentValues().apply { put(MediaStore.Downloads.IS_PENDING, 0) }
                resolver.update(uri, done, null, null)
            }
            if (share) {
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "application/pdf"
                    putExtra(Intent.EXTRA_STREAM, uri)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                }
                context.startActivity(Intent.createChooser(intent, "Share $filename"))
            }
            uri
        }.getOrElse {
            status = "Could not save PDF: ${it.message ?: "storage error"}"
            null
        }
    }

    Column(modifier.fillMaxSize().padding(horizontal = 18.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
            Column(Modifier.weight(1f).padding(top = 10.dp)) {
                Text("Exam Master", fontSize = 26.sp, fontWeight = FontWeight.ExtraBold, color = examInk)
                Text("CBSE · Class 6 · Science", color = examGrey, fontSize = 12.sp)
            }
        }
        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(top = 6.dp, bottom = 18.dp)
        ) {
            item {
                Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFEAF0FF))) {
                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                        Text("Two separate printable PDFs", color = examInk, fontWeight = FontWeight.Bold, fontSize = 17.sp)
                        Text("1. Student paper with questions only\n2. Parent answer key with model answers, marking guidance and score sheet", color = examInk, fontSize = 13.sp, lineHeight = 19.sp)
                        Text("Target mix: 80% exercise-style practice variants and 20% inside-chapter questions. These are original practice questions, not copied book-back questions or exam predictions.", color = examGrey, fontSize = 11.sp, lineHeight = 16.sp)
                    }
                }
            }
            item {
                OutlinedTextField(value = examTitle, onValueChange = { examTitle = it }, label = { Text("Paper title") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            }
            item {
                Text("Choose chapters", fontSize = 18.sp, fontWeight = FontWeight.Bold, color = examInk)
                Text("The question bank currently covers the 12 NCERT Curiosity chapters.", color = examGrey, fontSize = 12.sp)
            }
            items(chapters.size) { index ->
                val chapter = chapters[index]
                Card(colors = CardDefaults.cardColors(containerColor = Color.White)) {
                    Row(Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 4.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                        Checkbox(checked = chapter.title in selected, onCheckedChange = { checked ->
                            selected = if (checked) selected + chapter.title else selected - chapter.title
                        })
                        Column(Modifier.weight(1f).padding(vertical = 8.dp)) {
                            Text("${index + 1}. ${chapter.title}", color = examInk, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                            Text("${chapter.count} available questions", color = examGrey, fontSize = 11.sp)
                        }
                    }
                }
            }
            item {
                Text("Number of questions: $questionCount", fontWeight = FontWeight.Bold, color = examInk)
                Slider(value = questionCount.toFloat(), onValueChange = { questionCount = it.toInt() }, valueRange = 5f..60f, steps = 10)
                Text("Questions available depend on the chapters selected.", color = examGrey, fontSize = 11.sp)
            }
            item {
                Button(onClick = { generate() }, enabled = !loading && chapters.isNotEmpty() && selected.isNotEmpty(), modifier = Modifier.fillMaxWidth().height(52.dp)) {
                    if (loading) CircularProgressIndicator(modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                    else Icon(Icons.Default.PictureAsPdf, contentDescription = null)
                    Text(if (loading) "  Generating…" else "  Generate both PDFs", fontWeight = FontWeight.Bold)
                }
            }
            item { Text(status, color = if (status.startsWith("Could not") || status.startsWith("Generation failed")) Color(0xFFB3261E) else examGrey, fontSize = 12.sp, lineHeight = 17.sp) }
            if (studentPdf != null && parentPdf != null) {
                item { Text(mixSummary, color = examInk, fontSize = 12.sp, fontWeight = FontWeight.SemiBold) }
                item {
                    Button(onClick = {
                        studentFile = savePdf(studentPdf!!, "PadippuPal_Student_Question_Paper.pdf", false)
                        if (studentFile != null) status = "Student question paper saved to Downloads."
                    }, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.PictureAsPdf, contentDescription = null)
                        Text("  Save student question paper")
                    }
                }
                item {
                    Button(onClick = {
                        parentFile = savePdf(parentPdf!!, "PadippuPal_Parent_Answer_Key.pdf", false)
                        if (parentFile != null) status = "Parent answer key saved to Downloads."
                    }, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.PictureAsPdf, contentDescription = null)
                        Text("  Save parent answer key")
                    }
                }
                item {
                    OutlinedButton(onClick = {
                        val bytes = studentPdf!!
                        savePdf(bytes, "PadippuPal_Student_Question_Paper.pdf", true)
                    }, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.Share, contentDescription = null)
                        Text("  Share student paper")
                    }
                }
                item {
                    OutlinedButton(onClick = {
                        val bytes = parentPdf!!
                        savePdf(bytes, "PadippuPal_Parent_Answer_Key.pdf", true)
                    }, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.Share, contentDescription = null)
                        Text("  Share parent answer key")
                    }
                }
            }
        }
    }
}
