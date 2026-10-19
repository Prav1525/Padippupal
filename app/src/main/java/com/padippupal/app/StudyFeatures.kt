package com.padippupal.app

import android.content.Context
import android.graphics.Paint
import android.graphics.pdf.PdfDocument
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.util.Base64
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.UploadFile
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.util.UUID
import java.util.concurrent.Executors

private val FeatureGreen = Color(0xFF24734B)
private val FeatureInk = Color(0xFF173D2A)
private val FeatureGrey = Color(0xFF718075)
private val featureExecutor = Executors.newSingleThreadExecutor()
private val featureMain = Handler(Looper.getMainLooper())
private fun featureBase() = BuildConfig.CURRICULUM_API_BASE_URL.trimEnd('/')

private fun featureRequest(url: String, method: String = "GET", body: JSONObject? = null): JSONObject {
    val c = URL(url).openConnection() as HttpURLConnection
    c.requestMethod = method
    c.connectTimeout = 10000
    c.readTimeout = 40000
    c.setRequestProperty("Accept", "application/json")
    if (body != null) {
        c.doOutput = true
        c.setRequestProperty("Content-Type", "application/json; charset=utf-8")
        c.outputStream.use { it.write(body.toString().toByteArray(StandardCharsets.UTF_8)) }
    }
    try {
        val code = c.responseCode
        val stream = if (code in 200..299) c.inputStream else c.errorStream
        val text = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()
        if (code !in 200..299) {
            val detail = runCatching { JSONObject(text).optString("detail") }.getOrDefault(text)
            throw IllegalStateException("HTTP $code: ${detail.take(180)}")
        }
        return if (text.isBlank()) JSONObject() else JSONObject(text)
    } finally { c.disconnect() }
}
private fun enc(value: String) = URLEncoder.encode(value, "UTF-8")

private data class DiaryDraft(
    val title: String,
    val subject: String,
    val details: String,
    val dueDate: String,
    val minutes: Int,
    val checked: Boolean = true
)
private data class PlannerTask(
    val id: String, val title: String, val subject: String, val details: String,
    val dueDate: String, val minutes: Int, val completed: Boolean
)
private fun parsePlannerTasks(json: JSONObject): List<PlannerTask> {
    val array = json.optJSONArray("tasks") ?: JSONArray()
    return (0 until array.length()).mapNotNull { i ->
        val o = array.optJSONObject(i) ?: return@mapNotNull null
        PlannerTask(o.optString("id"), o.optString("title"), o.optString("subject", "General"),
            o.optString("details"), o.optString("due_date"), o.optInt("minutes", 15), o.optBoolean("completed"))
    }
}

@Composable
internal fun DiaryScanScreen(
    profileId: String, grade: Int, board: String, medium: String, language: String,
    onBack: () -> Unit, onSaved: () -> Unit, modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var selectedName by remember { mutableStateOf("") }
    var drafts by remember { mutableStateOf<List<DiaryDraft>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var saving by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("Choose a clear photo of the diary page. Check every extracted task before saving.") }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri: Uri? ->
        if (uri != null) {
            selectedName = uri.lastPathSegment ?: "Diary photo selected"
            loading = true
            status = "Reading the diary photo with AI…"
            drafts = emptyList()
            featureExecutor.execute {
                val result = runCatching {
                    val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                        ?: error("Could not open this image.")
                    require(bytes.size <= 6_000_000) { "Please select a photo smaller than 6 MB." }
                    val encoded = Base64.encodeToString(bytes, Base64.NO_WRAP)
                    val mime = context.contentResolver.getType(uri)?.takeIf { it in listOf("image/jpeg", "image/png", "image/webp") } ?: "image/jpeg"
                    featureRequest("${featureBase()}/diary/parse", "POST",
                        JSONObject().put("image_base64", encoded).put("mime_type", mime)
                            .put("board", board).put("class_level", grade).put("medium", medium).put("app_language", language))
                }
                featureMain.post {
                    loading = false
                    result.fold(onSuccess = { response ->
                        val array = response.optJSONArray("tasks") ?: JSONArray()
                        drafts = (0 until array.length()).mapNotNull { i ->
                            val o = array.optJSONObject(i) ?: return@mapNotNull null
                            val title = o.optString("title").trim()
                            if (title.isBlank()) null else DiaryDraft(title, o.optString("subject", "General"),
                                o.optString("details"), o.optString("due_date"), o.optInt("minutes", 15))
                        }
                        status = if (drafts.isEmpty()) "No clear homework was detected. Try a closer, brighter photo or type the task into your planner." else "Found ${drafts.size} possible task(s). Review them carefully before saving."
                    }, onFailure = { status = "Could not scan: ${it.message ?: "please try again"}" })
                }
            }
        }
    }

    LazyColumn(modifier.fillMaxSize().padding(horizontal = 18.dp), verticalArrangement = Arrangement.spacedBy(14.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp)) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
                Column { Text("Scan school diary", fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, color = FeatureInk); Text("Photo to homework plan", color = FeatureGrey) }
            }
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(22.dp)) {
                Column(Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(Icons.Default.CameraAlt, contentDescription = null, tint = FeatureGreen, modifier = Modifier.size(42.dp))
                    Text("Take or choose a diary photo", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                    Text("Keep the page flat, in focus and well lit. Only the selected image is sent for homework extraction.", color = FeatureGrey, fontSize = 13.sp)
                    Button(onClick = { picker.launch("image/*") }, enabled = !loading, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.UploadFile, null); Text("  Choose photo")
                    }
                    if (selectedName.isNotBlank()) Text("Photo selected", color = FeatureGrey, fontSize = 12.sp)
                }
            }
        }
        item {
            if (loading) LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
            Text(status, color = FeatureGrey, fontSize = 13.sp, lineHeight = 19.sp)
        }
        if (drafts.isNotEmpty()) {
            item { Text("Review extracted homework", fontSize = 19.sp, fontWeight = FontWeight.Bold, color = FeatureInk) }
            items(drafts) { draft ->
                val index = drafts.indexOf(draft)
                Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(16.dp)) {
                    Column(Modifier.fillMaxWidth().padding(13.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(checked = draft.checked, onCheckedChange = { checked ->
                                drafts = drafts.toMutableList().also { it[index] = draft.copy(checked = checked) }
                            })
                            OutlinedTextField(value = draft.title, onValueChange = { v ->
                                drafts = drafts.toMutableList().also { it[index] = draft.copy(title = v) }
                            }, modifier = Modifier.weight(1f), label = { Text("Homework task") })
                        }
                        Text("${draft.subject} · ${draft.minutes} min" + if (draft.dueDate.isNotBlank()) " · Due ${draft.dueDate}" else "", color = FeatureGreen, fontSize = 12.sp)
                        if (draft.details.isNotBlank()) Text(draft.details, color = FeatureGrey, fontSize = 12.sp)
                    }
                }
            }
            item {
                Button(onClick = {
                    val chosen = drafts.filter { it.checked && it.title.isNotBlank() }
                    if (chosen.isEmpty()) { status = "Select at least one task to save."; return@Button }
                    saving = true
                    status = "Saving tasks to your study planner…"
                    featureExecutor.execute {
                        val result = runCatching {
                            val array = JSONArray()
                            chosen.forEach { t ->
                                array.put(JSONObject().put("profile_id", profileId).put("title", t.title.trim())
                                    .put("subject", t.subject).put("details", t.details).put("due_date", t.dueDate)
                                    .put("minutes", t.minutes.coerceIn(1, 600)).put("source", "diary"))
                            }
                            featureRequest("${featureBase()}/planner/tasks/import", "POST",
                                JSONObject().put("profile_id", profileId).put("tasks", array))
                        }
                        featureMain.post {
                            saving = false
                            result.fold(onSuccess = { status = "Saved ${it.optInt("saved")} task(s) to your planner."; onSaved() },
                                onFailure = { status = "Save failed: ${it.message ?: "please try again"}" })
                        }
                    }
                }, enabled = !saving, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Save, null); Text(if (saving) "  Saving…" else "  Save selected tasks")
                }
            }
        }
    }
}

@Composable
internal fun PlannerScreen(
    profileId: String, onBack: () -> Unit, modifier: Modifier = Modifier
) {
    var tasks by remember { mutableStateOf<List<PlannerTask>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var title by remember { mutableStateOf("") }
    var subject by remember { mutableStateOf("General") }
    var minutes by remember { mutableStateOf("15") }
    var status by remember { mutableStateOf("Loading your saved tasks…") }

    fun refresh() {
        loading = true
        featureExecutor.execute {
            val result = runCatching { parsePlannerTasks(featureRequest("${featureBase()}/planner/tasks?profile_id=${enc(profileId)}")) }
            featureMain.post {
                loading = false
                result.fold(onSuccess = { tasks = it; status = if (it.isEmpty()) "No tasks yet. Add one or scan your school diary." else "${it.count { t -> t.completed }} of ${it.size} tasks completed." },
                    onFailure = { status = "Could not load saved tasks: ${it.message ?: "network error"}" })
            }
        }
    }
    LaunchedEffect(profileId) { refresh() }

    LazyColumn(modifier.fillMaxSize().padding(horizontal = 18.dp), verticalArrangement = Arrangement.spacedBy(13.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp)) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
                Column(Modifier.weight(1f)) { Text("Study planner", fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, color = FeatureInk); Text("Your progress is saved online", color = FeatureGrey) }
                IconButton(onClick = { refresh() }, enabled = !loading) { Icon(Icons.Default.Refresh, contentDescription = "Refresh") }
            }
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = FeatureGreen), shape = RoundedCornerShape(22.dp)) {
                Column(Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Icon(Icons.Default.CheckCircle, null, tint = Color.White)
                    Text("${tasks.count { it.completed }} / ${tasks.size} tasks completed", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 21.sp)
                    LinearProgressIndicator(progress = { if (tasks.isEmpty()) 0f else tasks.count { it.completed }.toFloat() / tasks.size },
                        modifier = Modifier.fillMaxWidth(), color = Color(0xFFFFD86B), trackColor = Color.White.copy(alpha = .3f))
                }
            }
        }
        item { Text(status, color = FeatureGrey, fontSize = 13.sp) }
        item { Text("Add a study task", fontWeight = FontWeight.Bold, fontSize = 18.sp, color = FeatureInk) }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("What will you study?") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                    OutlinedTextField(value = subject, onValueChange = { subject = it }, label = { Text("Subject") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                    OutlinedTextField(value = minutes, onValueChange = { minutes = it.filter(Char::isDigit).take(3) }, label = { Text("Minutes") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                    Button(onClick = {
                        if (title.isBlank()) { status = "Enter a task before saving."; return@Button }
                        loading = true
                        featureExecutor.execute {
                            val result = runCatching { featureRequest("${featureBase()}/planner/tasks", "POST",
                                JSONObject().put("profile_id", profileId).put("title", title.trim()).put("subject", subject.trim().ifBlank { "General" })
                                    .put("minutes", minutes.toIntOrNull()?.coerceIn(1, 600) ?: 15).put("source", "manual")) }
                            featureMain.post { loading = false; result.fold(onSuccess = { title = ""; refresh() }, onFailure = { status = "Could not save task: ${it.message ?: "network error"}" }) }
                        }
                    }, enabled = !loading, modifier = Modifier.fillMaxWidth()) { Icon(Icons.Default.Save, null); Text("  Save task") }
                }
            }
        }
        if (tasks.isNotEmpty()) item { Text("Your tasks", fontWeight = FontWeight.Bold, fontSize = 18.sp, color = FeatureInk) }
        items(tasks, key = { it.id }) { task ->
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(17.dp)) {
                Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = task.completed, onCheckedChange = { checked ->
                        featureExecutor.execute {
                            val result = runCatching { featureRequest("${featureBase()}/planner/tasks/${task.id}", "PUT",
                                JSONObject().put("profile_id", profileId).put("completed", checked)) }
                            featureMain.post { result.fold(onSuccess = { refresh() }, onFailure = { status = "Could not update progress: ${it.message}" }) }
                        }
                    })
                    Column(Modifier.weight(1f).padding(start = 4.dp)) {
                        Text(task.title, fontWeight = FontWeight.SemiBold, color = FeatureInk)
                        Text("${task.subject} · ${task.minutes} min" + if (task.dueDate.isNotBlank()) " · Due ${task.dueDate}" else "", color = FeatureGrey, fontSize = 12.sp)
                        if (task.details.isNotBlank()) Text(task.details, color = FeatureGrey, fontSize = 12.sp)
                    }
                    IconButton(onClick = {
                        featureExecutor.execute {
                            val result = runCatching { featureRequest("${featureBase()}/planner/tasks/${task.id}?profile_id=${enc(profileId)}", "DELETE") }
                            featureMain.post { result.fold(onSuccess = { refresh() }, onFailure = { status = "Could not delete task: ${it.message}" }) }
                        }
                    }) { Icon(Icons.Default.Delete, contentDescription = "Delete task", tint = FeatureGrey) }
                }
            }
        }
    }
}

@Composable
internal fun RevisionPdfScreen(
    profileId: String, studentName: String, grade: Int, board: String, medium: String,
    lessonTitle: String, onBack: () -> Unit, modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var status by remember { mutableStateOf("Create a printable revision sheet with your learner profile, concept recap, practice prompts and saved planner tasks.") }
    var pdfText by remember { mutableStateOf("") }
    var preparing by remember { mutableStateOf(false) }
    val savePicker = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/pdf")) { uri ->
        if (uri == null) { status = "PDF save cancelled."; return@rememberLauncherForActivityResult }
        val result = runCatching {
            val bytes = createRevisionPdf(studentName, grade, board, medium, lessonTitle, pdfText)
            context.contentResolver.openOutputStream(uri)?.use { it.write(bytes) } ?: error("Could not open the selected save location.")
        }
        status = result.fold(onSuccess = { "PDF saved successfully. Open it from the location you selected." },
            onFailure = { "Could not create the PDF: ${it.message ?: "please try again"}" })
    }
    LazyColumn(modifier.fillMaxSize().padding(horizontal = 18.dp), verticalArrangement = Arrangement.spacedBy(14.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp)) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
                Text("Revision sheet PDF", fontSize = 24.sp, fontWeight = FontWeight.ExtraBold, color = FeatureInk)
            }
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    Icon(Icons.Default.PictureAsPdf, null, tint = FeatureGreen, modifier = Modifier.size(40.dp))
                    Text("Ready to print or share", fontSize = 19.sp, fontWeight = FontWeight.Bold, color = FeatureInk)
                    Text("Includes learner details, a topic recap, revision prompts and the current saved study tasks. It is a study aid, not an official textbook extract.", color = FeatureGrey, fontSize = 13.sp, lineHeight = 19.sp)
                    Button(onClick = {
                        preparing = true
                        status = "Preparing your saved planner tasks…"
                        featureExecutor.execute {
                            val tasks = runCatching { parsePlannerTasks(featureRequest("${featureBase()}/planner/tasks?profile_id=${enc(profileId)}")) }
                            featureMain.post {
                                pdfText = tasks.fold(onSuccess = { list ->
                                    list.joinToString("\n") { "${if (it.completed) "[x]" else "[ ]"} ${it.title} — ${it.subject}, ${it.minutes} min" }
                                }, onFailure = { "Planner tasks could not be loaded: ${it.message}" })
                                preparing = false
                                status = "Choose a filename and save location to create the PDF."
                                savePicker.launch("PadippuPal-Revision-${lessonTitle.replace(Regex("[^A-Za-z0-9]+"), "-").trim('-').take(35)}.pdf")
                            }
                        }
                    }, enabled = !preparing, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.PictureAsPdf, null); Text(if (preparing) "  Preparing…" else "  Create and save PDF")
                    }
                }
            }
        }
        item { Text(status, color = FeatureGrey, fontSize = 13.sp, lineHeight = 19.sp) }
    }
}

private fun createRevisionPdf(name: String, grade: Int, board: String, medium: String, topic: String, tasks: String): ByteArray {
    val document = PdfDocument()
    val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { textSize = 11f; color = android.graphics.Color.rgb(35, 61, 42) }
    val titlePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { textSize = 21f; typeface = android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.BOLD); color = android.graphics.Color.rgb(36, 115, 75) }
    val boldPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply { textSize = 13f; typeface = android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.BOLD); color = android.graphics.Color.rgb(23, 61, 42) }
    val content = mutableListOf<Pair<String, Paint>>()
    content += "PadippuPal — Revision Sheet" to titlePaint
    content += "Learner: ${name.ifBlank { "Student" }}  |  Class: $grade" to paint
    content += "Board: $board  |  Textbook medium: $medium" to paint
    content += "Topic: $topic" to boldPaint
    content += "" to paint
    content += "CONCEPT RECAP" to boldPaint
    content += "Write the main idea in your own words. Identify the key terms, explain why the concept works, and add one example from everyday life." to paint
    content += "" to paint
    content += "QUICK REVISION" to boldPaint
    content += "1. What is the most important idea in this topic?" to paint
    content += "2. Explain the idea to a younger learner in two or three sentences." to paint
    content += "3. Give one example, diagram or labelled sequence that helps you remember it." to paint
    content += "4. Which part still feels confusing? Write one question to ask your tutor." to paint
    content += "" to paint
    content += "YOUR STUDY TASKS" to boldPaint
    if (tasks.isBlank()) content += "No saved tasks yet." to paint
    else tasks.lines().forEach { content += it to paint }
    content += "" to paint
    content += "Made for practice. Verify board-specific facts against your assigned textbook." to paint
    val pageWidth = 595
    val pageHeight = 842
    val margin = 48f
    var pageNumber = 1
    var page = document.startPage(PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNumber).create())
    var canvas = page.canvas
    var y = 58f
    canvas.drawRoundRect(margin, 25f, pageWidth - margin, 31f, 3f, 3f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = android.graphics.Color.rgb(255, 216, 107) })
    content.forEach { (line, style) ->
        val words = line.split(Regex("\\s+")).filter { it.isNotBlank() }
        if (words.isEmpty()) { y += 12f; return@forEach }
        var current = ""
        val lines = mutableListOf<String>()
        words.forEach { word ->
            val candidate = if (current.isBlank()) word else "$current $word"
            if (style.measureText(candidate) > pageWidth - 2 * margin && current.isNotBlank()) { lines += current; current = word }
            else current = candidate
        }
        if (current.isNotBlank()) lines += current
        lines.forEach { wrapped ->
            val lineHeight = style.textSize + 8f
            if (y + lineHeight > pageHeight - 45f) {
                document.finishPage(page)
                pageNumber++
                page = document.startPage(PdfDocument.PageInfo.Builder(pageWidth, pageHeight, pageNumber).create())
                canvas = page.canvas
                y = 52f
            }
            canvas.drawText(wrapped, margin, y, style)
            y += lineHeight
        }
        y += 5f
    }
    document.finishPage(page)
    val output = java.io.ByteArrayOutputStream()
    document.writeTo(output)
    document.close()
    return output.toByteArray()
}
