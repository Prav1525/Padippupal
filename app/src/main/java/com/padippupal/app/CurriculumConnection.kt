package com.padippupal.app

import android.os.Handler
import android.os.Looper
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.CloudDone
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URLEncoder
import java.net.URL
import java.nio.charset.StandardCharsets
import java.util.concurrent.Executors

private val ApiGreen = Color(0xFF24734B)
private val ApiInk = Color(0xFF173D2A)
private val ApiGrey = Color(0xFF718075)
private val apiExecutor = Executors.newSingleThreadExecutor()
private val apiMainHandler = Handler(Looper.getMainLooper())

private data class CurriculumMatch(
    val text: String,
    val title: String,
    val board: String,
    val classLevel: Int,
    val subject: String,
    val medium: String,
    val edition: String,
    val academicYear: String,
    val sourceUrl: String
)

@Composable
internal fun CurriculumConnectionScreen(
    grade: Int,
    board: String,
    medium: String,
    onBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    var baseUrl by remember { mutableStateOf(BuildConfig.CURRICULUM_API_BASE_URL) }
    var subject by remember { mutableStateOf("Science") }
    var query by remember { mutableStateOf("Explain the main idea of this chapter") }
    var chapter by remember { mutableStateOf("") }
    var synthesizedLessons by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var status by remember { mutableStateOf("Not checked yet") }
    var loading by remember { mutableStateOf(false) }
    var matches by remember { mutableStateOf<List<CurriculumMatch>>(emptyList()) }
    var searched by remember { mutableStateOf(false) }

    fun requestHealth() {
        val cleanBase = baseUrl.trim().trimEnd('/')
        if (!cleanBase.startsWith("https://")) {
            status = "Enter a valid deployed HTTPS API address."
            return
        }
        loading = true
        status = "Checking connection…"
        apiExecutor.execute {
            val result = runCatching { apiGet("$cleanBase/health") }
            apiMainHandler.post {
                loading = false
                status = result.fold(
                    onSuccess = { if (it.optString("status") == "ok") "Connected to PadippuPal curriculum engine." else "Server responded, but it is not the expected service." },
                    onFailure = { "Could not connect: ${it.message ?: "network error"}" }
                )
            }
        }
    }

    fun searchApprovedContent() {
        val cleanBase = baseUrl.trim().trimEnd('/')
        if (!cleanBase.startsWith("https://")) {
            status = "Enter a valid deployed HTTPS API address before searching."
            return
        }
        loading = true
        searched = true
        matches = emptyList()
        status = "Searching approved curriculum passages…"
        apiExecutor.execute {
            val result = runCatching {
                val body = JSONObject()
                    .put("board", board)
                    .put("class_level", grade)
                    .put("subject", subject)
                    .put("medium", medium)
                    .put("query", query)
                    .put("limit", 5)
                apiPost("$cleanBase/retrieve", body)
            }
            apiMainHandler.post {
                loading = false
                result.fold(
                    onSuccess = { response ->
                        val found = mutableListOf<CurriculumMatch>()
                        val rows = response.optJSONArray("matches")
                        if (rows != null) for (i in 0 until rows.length()) {
                            val row = rows.optJSONObject(i) ?: continue
                            val source = row.optJSONObject("source") ?: row
                            found += CurriculumMatch(
                                text = row.optString("text", ""),
                                title = source.optString("title", "Approved source"),
                                board = source.optString("board", board),
                                classLevel = source.optInt("class_level", grade),
                                subject = source.optString("subject", subject),
                                medium = source.optString("medium", medium),
                                edition = source.optString("edition", ""),
                                academicYear = source.optString("academic_year", ""),
                                sourceUrl = source.optString("url", source.optString("source_url", ""))
                            )
                        }
                        matches = found
                        status = if (found.isEmpty()) "Connected, but no matching approved passages are indexed yet." else "Found ${found.size} matching passage(s)."
                    },
                    onFailure = { status = "Search failed: ${it.message ?: "network error"}" }
                )
            }
        }
    }

    fun loadApprovedSynthesizedLessons() {
        val cleanBase = baseUrl.trim().trimEnd('/')
        if (!cleanBase.startsWith("https://")) {
            status = "Enter a valid deployed HTTPS API address before loading lessons."
            return
        }
        loading = true
        synthesizedLessons = emptyList()
        status = "Loading approved synthesized lessons…"
        apiExecutor.execute {
            val result = runCatching {
                val params = "board=${URLEncoder.encode(board, "UTF-8")}" +
                    "&class_level=$grade" +
                    "&subject=${URLEncoder.encode(subject, "UTF-8")}" +
                    "&medium=${URLEncoder.encode(medium, "UTF-8")}" +
                    if (chapter.trim().isNotEmpty()) "&chapter=${URLEncoder.encode(chapter.trim(), "UTF-8")}" else ""
                apiGet("$cleanBase/curriculum/synthesized-lessons?$params")
            }
            apiMainHandler.post {
                loading = false
                result.fold(
                    onSuccess = { response ->
                        val found = mutableListOf<JSONObject>()
                        val rows = response.optJSONArray("lessons")
                        if (rows != null) for (i in 0 until rows.length()) {
                            rows.optJSONObject(i)?.let(found::add)
                        }
                        synthesizedLessons = found
                        status = if (found.isEmpty()) {
                            "Connected, but no approved synthesized lessons match this profile and chapter."
                        } else {
                            "Loaded ${found.size} approved synthesized lesson(s)."
                        }
                    },
                    onFailure = { status = "Lesson load failed: ${it.message ?: "network error"}" }
                )
            }
        }
    }

    LazyColumn(
        modifier = modifier.fillMaxSize().padding(horizontal = 18.dp),
        verticalArrangement = Arrangement.spacedBy(13.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 24.dp)
    ) {
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, contentDescription = "Back") }
                Column(Modifier.weight(1f)) {
                    Text("Curriculum connection", fontSize = 25.sp, fontWeight = FontWeight.ExtraBold, color = ApiInk)
                    Text("Background source matching", color = ApiGrey, fontSize = 13.sp)
                }
                Icon(Icons.Default.CloudDone, contentDescription = null, tint = ApiGreen, modifier = Modifier.padding(top = 10.dp))
            }
        }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(20.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Student curriculum profile", fontWeight = FontWeight.Bold, color = ApiInk)
                    Text("Class $grade · $board · $medium medium", color = ApiGrey)
                    Text("Only documents approved and indexed by the curriculum administrator can appear here.", fontSize = 12.sp, color = ApiGrey)
                }
            }
        }
        item {
            OutlinedTextField(
                value = baseUrl,
                onValueChange = { baseUrl = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Curriculum API HTTPS URL") },
                placeholder = { Text("https://your-api.example.com") },
                singleLine = true
            )
            Text("Using the hosted PadippuPal curriculum service. Change this only if the API URL changes.", color = ApiGrey, fontSize = 11.sp)
        }
        item {
            Button(onClick = { requestHealth() }, enabled = !loading, modifier = Modifier.fillMaxWidth()) {
                if (loading) CircularProgressIndicator(modifier = Modifier.size(18.dp), strokeWidth = 2.dp)
                else Icon(Icons.Default.CloudDone, contentDescription = null)
                Text("  Check connection")
            }
        }
        item {
            Text(status, color = if (status.startsWith("Connected")) ApiGreen else ApiGrey, fontSize = 13.sp)
        }
        item { Divider() }
        item {
            Text("Approved synthesized lessons", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = ApiInk)
            Text("Loads reviewed lesson content from the curriculum API. Leave chapter blank to show all matching chapters.", color = ApiGrey, fontSize = 12.sp)
        }
        item {
            OutlinedTextField(
                value = chapter,
                onValueChange = { chapter = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Chapter (optional exact title)") },
                singleLine = true
            )
        }
        item {
            Button(
                onClick = { loadApprovedSynthesizedLessons() },
                enabled = !loading && subject.isNotBlank(),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("  Load approved lessons")
            }
        }
        items(synthesizedLessons, key = { it.optString("id") }) { lesson ->
            val objectives = lesson.optJSONArray("learning_objectives")
            val objectivesText = if (objectives == null) "" else
                (0 until objectives.length()).mapNotNull { objectives.optString(it).takeIf(String::isNotBlank) }.joinToString(" · ")
            val explanation = lesson.optJSONObject("explanation")?.toString().orEmpty()
            val examples = lesson.optJSONArray("examples")?.toString().orEmpty()
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text(lesson.optString("topic", "Approved topic"), fontWeight = FontWeight.Bold, color = ApiInk)
                    Text("${lesson.optString("chapter")} · pages ${lesson.optString("page_start")}–${lesson.optString("page_end")}", color = ApiGreen, fontSize = 11.sp)
                    if (objectivesText.isNotBlank()) Text("You will learn: $objectivesText", fontSize = 13.sp, color = ApiInk)
                    if (explanation.isNotBlank()) Text(explanation, fontSize = 14.sp, lineHeight = 20.sp, color = ApiInk)
                    if (examples.isNotBlank() && examples != "[]") Text("Examples: $examples", fontSize = 13.sp, color = ApiInk)
                    Text("Source: ${lesson.optString("source_title", "reviewed curriculum source")}", color = ApiGrey, fontSize = 11.sp)
                }
            }
        }
        item { Divider() }
        item { Text("Search indexed material", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = ApiInk) }
        item {
            OutlinedTextField(
                value = subject,
                onValueChange = { subject = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Subject (match source catalog)") },
                singleLine = true
            )
        }
        item {
            OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("What do you want to understand?") },
                minLines = 2
            )
        }
        item {
            Button(onClick = { searchApprovedContent() }, enabled = !loading && query.trim().length >= 2 && subject.isNotBlank(), modifier = Modifier.fillMaxWidth()) {
                Icon(Icons.Default.Search, contentDescription = null)
                Text("  Find approved passages")
            }
        }
        if (searched && matches.isEmpty() && !loading) {
            item {
                Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF4D8)), shape = RoundedCornerShape(16.dp)) {
                    Text("No source passages to show yet. This is not a generated answer; add approved curriculum documents to the backend first.", Modifier.padding(14.dp), color = ApiInk, fontSize = 13.sp)
                }
            }
        }
        items(matches) { match ->
            Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(15.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text(match.title, fontWeight = FontWeight.Bold, color = ApiInk)
                    Text("${match.board} · Class ${match.classLevel} · ${match.subject} · ${match.medium}", color = ApiGreen, fontSize = 11.sp)
                    Text(match.text, fontSize = 14.sp, lineHeight = 20.sp)
                    Text(listOf(match.academicYear, match.edition).filter { it.isNotBlank() }.joinToString(" · "), color = ApiGrey, fontSize = 11.sp)
                    if (match.sourceUrl.startsWith("https://")) Text(match.sourceUrl, color = ApiGrey, fontSize = 11.sp)
                }
            }
        }
        item { Text("This screen retrieves source passages only. It does not yet generate an AI lesson or verify the official status of a document.", color = ApiGrey, fontSize = 11.sp) }
    }
}

private fun apiGet(url: String): JSONObject = apiRequest(url, "GET", null)

private fun apiPost(url: String, body: JSONObject): JSONObject = apiRequest(url, "POST", body)

private fun apiRequest(url: String, method: String, body: JSONObject?): JSONObject {
    val connection = (URL(url).openConnection() as HttpURLConnection)
    connection.requestMethod = method
    connection.connectTimeout = 8000
    connection.readTimeout = 12000
    connection.setRequestProperty("Accept", "application/json")
    if (body != null) {
        connection.doOutput = true
        connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
        connection.outputStream.use { it.write(body.toString().toByteArray(StandardCharsets.UTF_8)) }
    }
    try {
        val code = connection.responseCode
        val stream = if (code in 200..299) connection.inputStream else connection.errorStream
        val responseText = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()
        if (code !in 200..299) throw IllegalStateException("HTTP $code: ${responseText.take(180)}")
        return JSONObject(responseText)
    } finally {
        connection.disconnect()
    }
}
