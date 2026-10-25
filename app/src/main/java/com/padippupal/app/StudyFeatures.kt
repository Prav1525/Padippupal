package com.padippupal.app

import android.content.Context
import android.graphics.Paint
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.window.Dialog
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

private val FeatureGreen = Color(0xFF4169E1)
private val FeatureInk = Color(0xFF172033)
private val FeatureGrey = Color(0xFF64748B)
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
    val confidence: String = "medium",
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
    var sourceBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var showCropEditor by remember { mutableStateOf(false) }
    var cropStart by remember { mutableStateOf<Offset?>(null) }
    var cropEnd by remember { mutableStateOf<Offset?>(null) }
    var diaryDate by remember { mutableStateOf("") }
    var drafts by remember { mutableStateOf<List<DiaryDraft>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var saving by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("Choose a clear photo of the diary page. Check every extracted task before saving.") }
    fun scanImage(bytes: ByteArray, mime: String, name: String) {
        selectedName = name
        loading = true
        status = "Reading the diary photo with AI…"
        drafts = emptyList()
        featureExecutor.execute {
            val result = runCatching {
                require(bytes.size <= 6_000_000) { "Please use a photo smaller than 6 MB." }
                val encoded = Base64.encodeToString(bytes, Base64.NO_WRAP)
                featureRequest("${featureBase()}/diary/parse", "POST",
                    JSONObject().put("image_base64", encoded).put("mime_type", mime)
                        .put("board", board).put("class_level", grade).put("medium", medium).put("app_language", language)
                        .put("today_date", java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).format(java.util.Date())))
            }
            featureMain.post {
                loading = false
                result.fold(onSuccess = { response ->
                    diaryDate = response.optString("diary_date").trim()
                    val matchStatus = response.optString("match_status", "needs_crop")
                    if (matchStatus != "matched") {
                        drafts = emptyList()
                        status = if (matchStatus == "no_today_row") {
                            "Today's date was not found in the diary. No homework was imported. Please choose a closer photo showing today's date and its homework row, then scan again."
                        } else {
                            "The date or row is unclear, so no homework was imported. Choose a closer photo showing the date and homework row, then scan again."
                        }
                        return@fold
                    }
                    val array = response.optJSONArray("tasks") ?: JSONArray()
                    drafts = (0 until array.length()).mapNotNull { i ->
                        val o = array.optJSONObject(i) ?: return@mapNotNull null
                        val title = o.optString("title").trim()
                        if (title.isBlank()) null else DiaryDraft(title, o.optString("subject", "General"),
                            o.optString("details"), o.optString("due_date"), o.optInt("minutes", 15), o.optString("confidence", "medium"))
                    }
                    status = if (drafts.isEmpty()) "No clear homework was detected. Try a closer, brighter photo or type the task into your planner." else "Found ${drafts.size} possible task(s). Review them carefully before saving."
                }, onFailure = { status = "Could not scan: ${it.message ?: "please try again"}" })
            }
        }
    }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri != null) {
            featureExecutor.execute {
                val result = runCatching {
                    val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                        ?: error("Could not open this image.")
                    val mime = context.contentResolver.getType(uri)?.takeIf { it in listOf("image/jpeg", "image/png", "image/webp") } ?: "image/jpeg"
                    val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: error("This image could not be decoded.")
                    Triple(bytes, mime, bitmap)
                }
                featureMain.post {
                    result.fold(onSuccess = { (bytes, mime, bitmap) ->
                        sourceBitmap = bitmap
                        scanImage(bytes, mime, "Diary photo selected")
                    },
                        onFailure = { status = "Could not open photo: ${it.message ?: "please try again"}" })
                }
            }
        }
    }
    val camera = rememberLauncherForActivityResult(ActivityResultContracts.TakePicturePreview()) { bitmap ->
        if (bitmap != null) {
            sourceBitmap = bitmap
            val output = java.io.ByteArrayOutputStream()
            bitmap.compress(Bitmap.CompressFormat.JPEG, 88, output)
            scanImage(output.toByteArray(), "image/jpeg", "Photo captured with camera")
        } else {
            status = "Camera capture cancelled. You can try again or choose a photo."
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
                    Button(onClick = { camera.launch(null) }, enabled = !loading, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Default.CameraAlt, null); Text("  Take photo")
                    }
                    OutlinedButton(onClick = { picker.launch(arrayOf("image/jpeg", "image/png", "image/webp")) }, enabled = !loading, modifier = Modifier.fillMaxWidth()) {
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
        if (sourceBitmap != null && !loading) {
            item { OutlinedButton(onClick = { showCropEditor = true; cropStart = null; cropEnd = null }, modifier = Modifier.fillMaxWidth()) { Text("Crop this photo and rescan") } }
        }
        if (drafts.isNotEmpty()) {
            item {
                Text("Review extracted homework", fontSize = 19.sp, fontWeight = FontWeight.Bold, color = FeatureInk)
                if (diaryDate.isNotBlank()) Text("Diary date detected: $diaryDate · Please verify", color = FeatureGrey, fontSize = 13.sp)
                Text("Check low-confidence words against the original diary before saving.", color = FeatureGrey, fontSize = 12.sp)
            }
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
                        Text("Handwriting confidence: ${draft.confidence.uppercase()}" + if (draft.confidence == "low") " · Please check the photo" else "", color = if (draft.confidence == "low") Color(0xFF9A3412) else FeatureGrey, fontSize = 12.sp)
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
                                    .put("subject", t.subject).put("details", t.details)
                                    .put("due_date", t.dueDate.ifBlank { java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).format(java.util.Date()) })
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
    if (showCropEditor && sourceBitmap != null) {
        val bitmap = sourceBitmap!!
        Dialog(onDismissRequest = { showCropEditor = false }) {
            Card(shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
                Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Crop today's diary row", fontWeight = FontWeight.Bold, fontSize = 20.sp)
                    Text("Drag across the date and homework for today. Include the date so it can be checked again.", color = FeatureGrey, fontSize = 13.sp)
                    Box(Modifier.fillMaxWidth().aspectRatio(bitmap.width.toFloat()/bitmap.height)) {
                        Image(bitmap.asImageBitmap(), contentDescription = "Diary crop", contentScale = ContentScale.FillBounds, modifier = Modifier.fillMaxSize().pointerInput(bitmap) { detectDragGestures(onDragStart = { val p = Offset(it.x / size.width * bitmap.width, it.y / size.height * bitmap.height); cropStart = p; cropEnd = p }, onDrag = { change, _ -> cropEnd = Offset(change.position.x / size.width * bitmap.width, change.position.y / size.height * bitmap.height) }) })
                        Canvas(Modifier.fillMaxSize()) {
                        val a = cropStart; val b = cropEnd
                        if (a != null && b != null) {
                            val l = minOf(a.x,b.x).coerceIn(0f,bitmap.width.toFloat()) / bitmap.width * size.width; val t = minOf(a.y,b.y).coerceIn(0f,bitmap.height.toFloat()) / bitmap.height * size.height
                            val rr = maxOf(a.x,b.x).coerceIn(0f,bitmap.width.toFloat()) / bitmap.width * size.width; val bb = maxOf(a.y,b.y).coerceIn(0f,bitmap.height.toFloat()) / bitmap.height * size.height
                            drawRect(Color(0x3334D399), topLeft=Offset(l,t), size=androidx.compose.ui.geometry.Size(rr-l,bb-t))
                            drawRect(Color(0xFF0F766E), topLeft=Offset(l,t), size=androidx.compose.ui.geometry.Size(rr-l,bb-t), style=Stroke(3.dp.toPx()))
                        }
                    }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { showCropEditor = false }, modifier = Modifier.weight(1f)) { Text("Cancel") }
                        Button(enabled = cropStart != null && cropEnd != null, onClick = {
                            val a = cropStart; val b = cropEnd
                            if (a != null && b != null) {
                                val l = minOf(a.x,b.x).coerceIn(0f,bitmap.width.toFloat()).toInt().coerceIn(0,bitmap.width-1)
                                val t = minOf(a.y,b.y).coerceIn(0f,bitmap.height.toFloat()).toInt().coerceIn(0,bitmap.height-1)
                                val rr = maxOf(a.x,b.x).coerceIn(0f,bitmap.width.toFloat()).toInt().coerceIn(l+1,bitmap.width)
                                val bb = maxOf(a.y,b.y).coerceIn(0f,bitmap.height.toFloat()).toInt().coerceIn(t+1,bitmap.height)
                                val cropped = Bitmap.createBitmap(bitmap,l,t,rr-l,bb-t)
                                val out = java.io.ByteArrayOutputStream(); cropped.compress(Bitmap.CompressFormat.JPEG,92,out)
                                showCropEditor = false; scanImage(out.toByteArray(),"image/jpeg","Cropped diary row")
                            }
                        }, modifier = Modifier.weight(1f)) { Text("Rescan crop") }
                    }
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
    val today = remember {
        java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).format(java.util.Date())
    }
    val todayTasks = tasks.filter { it.dueDate == today }
    val subjectProgress = todayTasks.groupBy { it.subject.ifBlank { "General" } }.toSortedMap()

    fun refresh() {
        loading = true
        featureExecutor.execute {
            val result = runCatching { parsePlannerTasks(featureRequest("${featureBase()}/planner/tasks?profile_id=${enc(profileId)}")) }
            featureMain.post {
                loading = false
                result.fold(onSuccess = {
                    tasks = it
                    status = if (it.isEmpty()) "No tasks yet. Scan your school diary to build today's homework checklist."
                        else "${it.count { t -> t.completed }} of ${it.size} saved tasks completed."
                }, onFailure = { status = "Could not load saved tasks: ${it.message ?: "network error"}" })
            }
        }
    }
    LaunchedEffect(profileId) { refresh() }

    LazyColumn(modifier.fillMaxSize().padding(horizontal = 18.dp), verticalArrangement = Arrangement.spacedBy(13.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp)) {
        item {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
                Column(Modifier.weight(1f)) {
                    Text("Today's homework", fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, color = FeatureInk)
                    Text("Your daily plan and subject progress", color = FeatureGrey)
                }
                IconButton(onClick = { refresh() }, enabled = !loading) { Icon(Icons.Default.Refresh, contentDescription = "Refresh") }
            }
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF0F2742)), shape = RoundedCornerShape(22.dp)) {
                Column(Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text("DAILY CHECKLIST", color = Color(0xFFD8F5F0), fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    Text("${todayTasks.count { it.completed }} / ${todayTasks.size} tasks complete",
                        color = Color.White, fontWeight = FontWeight.Bold, fontSize = 21.sp)
                    LinearProgressIndicator(
                        progress = { if (todayTasks.isEmpty()) 0f else todayTasks.count { it.completed }.toFloat() / todayTasks.size },
                        modifier = Modifier.fillMaxWidth(), color = Color(0xFFF4C96B), trackColor = Color.White.copy(alpha = .25f)
                    )
                    Text(if (todayTasks.isEmpty()) "Scan today's diary to create your homework checklist."
                        else if (todayTasks.all { it.completed }) "Everything on today's checklist is done. Great work!"
                        else "Tick each task when you finish it.", color = Color.White.copy(alpha = .88f), fontSize = 13.sp)
                }
            }
        }
        item { Text(status, color = FeatureGrey, fontSize = 13.sp) }
        if (todayTasks.isNotEmpty()) {
            item { Text("Progress by subject", fontWeight = FontWeight.Bold, fontSize = 18.sp, color = FeatureInk) }
            items(subjectProgress.entries.toList(), key = { "subject-${it.key}" }) { entry ->
                val subjectTasks = entry.value
                val completed = subjectTasks.count { it.completed }
                Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(16.dp)) {
                    Column(Modifier.fillMaxWidth().padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(entry.key, modifier = Modifier.weight(1f), color = FeatureInk, fontWeight = FontWeight.SemiBold)
                            Text("$completed / ${subjectTasks.size}", color = FeatureGrey, fontSize = 12.sp)
                        }
                        LinearProgressIndicator(
                            progress = { if (subjectTasks.isEmpty()) 0f else completed.toFloat() / subjectTasks.size },
                            modifier = Modifier.fillMaxWidth(), color = FeatureGreen,
                            trackColor = Color(0xFFD8F5F0)
                        )
                    }
                }
            }
            item { Text("Tick tasks as you finish", fontWeight = FontWeight.Bold, fontSize = 18.sp, color = FeatureInk) }
            items(todayTasks, key = { "today-${it.id}" }) { task ->
                PlannerTaskCard(task = task, profileId = profileId, onChanged = { refresh() }, onStatus = { status = it })
            }
        }
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
                                JSONObject().put("profile_id", profileId).put("title", title.trim())
                                    .put("subject", subject.trim().ifBlank { "General" })
                                    .put("due_date", today)
                                    .put("minutes", minutes.toIntOrNull()?.coerceIn(1, 600) ?: 15).put("source", "manual")) }
                            featureMain.post { loading = false; result.fold(onSuccess = { title = ""; refresh() }, onFailure = { status = "Could not save task: ${it.message ?: "network error"}" }) }
                        }
                    }, enabled = !loading, modifier = Modifier.fillMaxWidth()) { Icon(Icons.Default.Save, null); Text("  Add to today's checklist") }
                }
            }
        }
        val otherTasks = tasks.filter { it.dueDate != today }
        if (otherTasks.isNotEmpty()) {
            item { Text("Other saved tasks", fontWeight = FontWeight.Bold, fontSize = 18.sp, color = FeatureInk) }
            items(otherTasks, key = { "other-${it.id}" }) { task ->
                PlannerTaskCard(task = task, profileId = profileId, onChanged = { refresh() }, onStatus = { status = it })
            }
        }
    }
}

@Composable
private fun PlannerTaskCard(
    task: PlannerTask, profileId: String, onChanged: () -> Unit, onStatus: (String) -> Unit
) {
    Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(17.dp)) {
        Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Checkbox(checked = task.completed, onCheckedChange = { checked ->
                featureExecutor.execute {
                    val result = runCatching { featureRequest("${featureBase()}/planner/tasks/${task.id}", "PUT",
                        JSONObject().put("profile_id", profileId).put("completed", checked)) }
                    featureMain.post { result.fold(onSuccess = { onChanged() }, onFailure = { onStatus("Could not update progress: ${it.message}") }) }
                }
            })
            Column(Modifier.weight(1f).padding(start = 4.dp)) {
                Text(task.title, fontWeight = FontWeight.SemiBold, color = FeatureInk)
                Text("${task.subject} · ${task.minutes} min" + if (task.dueDate.isNotBlank()) " · Due ${task.dueDate}" else "",
                    color = FeatureGrey, fontSize = 12.sp)
                if (task.details.isNotBlank()) Text(task.details, color = FeatureGrey, fontSize = 12.sp)
            }
            IconButton(onClick = {
                featureExecutor.execute {
                    val result = runCatching { featureRequest("${featureBase()}/planner/tasks/${task.id}?profile_id=${enc(profileId)}", "DELETE") }
                    featureMain.post { result.fold(onSuccess = { onChanged() }, onFailure = { onStatus("Could not delete task: ${it.message}") }) }
                }
            }) { Icon(Icons.Default.Delete, contentDescription = "Delete task", tint = FeatureGrey) }
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
