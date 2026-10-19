package com.padippupal.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Book
import androidx.compose.material.icons.filled.CalendarMonth
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.EmojiEvents
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.School
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val Leaf = Color(0xFF2F7D54)
private val PaleGreen = Color(0xFFEAF5ED)
private val Ink = Color(0xFF1D3025)
private val Muted = Color(0xFF68786E)
private val Warm = Color(0xFFFFF4DD)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { PadippuPalApp() }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PadippuPalApp() {
    var tamil by remember { mutableStateOf(false) }
    var selectedTab by remember { mutableIntStateOf(0) }
    val title = if (tamil) "படிப்புபால்" else "PadippuPal"

    MaterialTheme(
        colorScheme = MaterialTheme.colorScheme.copy(
            primary = Leaf,
            onPrimary = Color.White,
            background = Color(0xFFF7FAF7),
            surface = Color.White,
            onSurface = Ink
        )
    ) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(40.dp)
                                    .background(PaleGreen, CircleShape),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(Icons.Default.MenuBook, contentDescription = null, tint = Leaf)
                            }
                            Column(Modifier.padding(start = 10.dp)) {
                                Text(title, fontWeight = FontWeight.Bold, fontSize = 21.sp)
                                Text(
                                    if (tamil) "உங்கள் படிப்பு நண்பன்" else "Your personal study buddy",
                                    fontSize = 11.sp,
                                    color = Muted
                                )
                            }
                        }
                    },
                    actions = {
                        androidx.compose.material3.IconButton(onClick = { tamil = !tamil }) {
                            Icon(Icons.Default.Language, contentDescription = "Change language")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFFF7FAF7))
                )
            },
            bottomBar = {
                NavigationBar(containerColor = Color.White) {
                    val items = listOf(
                        Triple(if (tamil) "முகப்பு" else "Home", Icons.Default.Home, 0),
                        Triple(if (tamil) "பாடங்கள்" else "Subjects", Icons.Default.Book, 1),
                        Triple(if (tamil) "திட்டம்" else "Planner", Icons.Default.CalendarMonth, 2),
                        Triple(if (tamil) "நான்" else "Profile", Icons.Default.Person, 3)
                    )
                    items.forEach { (label, icon, index) ->
                        NavigationBarItem(
                            selected = selectedTab == index,
                            onClick = { selectedTab = index },
                            icon = { Icon(icon, contentDescription = label) },
                            label = { Text(label, fontSize = 10.sp) }
                        )
                    }
                }
            },
            containerColor = Color(0xFFF7FAF7)
        ) { padding ->
            when (selectedTab) {
                0 -> HomeScreen(tamil, Modifier.padding(padding))
                1 -> SubjectsScreen(tamil, Modifier.padding(padding))
                2 -> PlannerScreen(tamil, Modifier.padding(padding))
                else -> ProfileScreen(tamil, onLanguage = { tamil = !tamil }, modifier = Modifier.padding(padding))
            }
        }
    }
}

@Composable
private fun HomeScreen(tamil: Boolean, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            if (tamil) "வணக்கம், மாணவரே! 👋" else "Hey, learner! 👋",
            fontSize = 26.sp, fontWeight = FontWeight.Bold, color = Ink
        )
        Text(
            if (tamil) "சிறிய படிகள், பெரிய முன்னேற்றம்." else "Small steps today, big progress tomorrow.",
            color = Muted
        )
        Card(
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = Leaf),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.EmojiEvents, contentDescription = null, tint = Color(0xFFFFD978))
                    Text(
                        if (tamil) "  இன்றைய இலக்கு" else "  YOUR DAILY GOAL",
                        color = Color.White.copy(alpha = .9f), fontSize = 12.sp, fontWeight = FontWeight.Bold
                    )
                }
                Text(
                    if (tamil) "இன்றைய படிப்பை தொடங்குவோம்!" else "Ready for a little learning?",
                    color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold
                )
                Text(
                    if (tamil) "ஒரு பாடத்தைத் தேர்ந்தெடுத்து தொடங்குங்கள்." else "Pick a subject and build your study streak.",
                    color = Color.White.copy(alpha = .9f)
                )
                Button(onClick = { }) {
                    Text(if (tamil) "படிக்கத் தொடங்கு" else "Start studying")
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            StatCard(if (tamil) "பாடங்கள்" else "Subjects", "6", Icons.Default.School, Modifier.weight(1f))
            StatCard(if (tamil) "இன்றைய பணிகள்" else "Tasks today", "3", Icons.Default.CheckCircle, Modifier.weight(1f))
        }
        SectionTitle(if (tamil) "இன்றைய திட்டம்" else "Today's study plan")
        TaskRow("Mathematics", if (tamil) "பயிற்சி: 10 கணக்குகள்" else "Practice: 10 problems", "20 min", PaleGreen)
        TaskRow("Science", if (tamil) "ஒரு பாடத்தை மீள்பார்க்கவும்" else "Revise one chapter", "15 min", Warm)
        TaskRow("English", if (tamil) "5 புதிய சொற்கள்" else "Learn 5 new words", "10 min", Color(0xFFEBEEFF))
        SectionTitle(if (tamil) "உங்கள் படிப்பு நண்பர்" else "Your study buddy")
        Card(colors = CardDefaults.cardColors(containerColor = Color.White)) {
            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.MenuBook, contentDescription = null, tint = Leaf, modifier = Modifier.size(34.dp))
                Column(Modifier.weight(1f).padding(start = 12.dp)) {
                    Text(if (tamil) "உதவி வேண்டுமா?" else "Need help with a topic?", fontWeight = FontWeight.Bold)
                    Text(
                        if (tamil) "உங்கள் கேள்விகளை விரைவில் இங்கே கேட்கலாம்." else "AI explanations and practice questions are coming next.",
                        color = Muted, fontSize = 13.sp
                    )
                }
            }
        }
        Text(
            if (tamil) "குறிப்பு: இது தொடக்க மாதிரி; உங்கள் முன்னேற்றம் இன்னும் சேமிக்கப்படவில்லை." else "Preview data only — your progress isn't saved yet.",
            color = Muted, fontSize = 11.sp
        )
        Spacer(Modifier.height(8.dp))
    }
}

@Composable
private fun SubjectsScreen(tamil: Boolean, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Text(if (tamil) "என் பாடங்கள்" else "My subjects", fontSize = 26.sp, fontWeight = FontWeight.Bold)
        Text(if (tamil) "உங்கள் பாடங்களைக் கண்காணிக்கவும்." else "Your learning journey, one subject at a time.", color = Muted)
        listOf(
            Triple("Mathematics", if (tamil) "கணிதம் · 4 அத்தியாயங்கள்" else "4 chapters · Practice regularly", PaleGreen),
            Triple("Science", if (tamil) "அறிவியல் · 6 அத்தியாயங்கள்" else "6 chapters · Revise concepts", Warm),
            Triple("English", if (tamil) "ஆங்கிலம் · 5 அத்தியாயங்கள்" else "5 chapters · Reading and writing", Color(0xFFEBEEFF)),
            Triple("Tamil", "தமிழ் · 5 அத்தியாயங்கள்", Color(0xFFFBE7F0)),
            Triple("Social Science", if (tamil) "சமூக அறிவியல்" else "History, geography and civics", PaleGreen),
            Triple("Computer Science", if (tamil) "கணினி அறிவியல்" else "Concepts and practical skills", Warm)
        ).forEach { (name, detail, color) ->
            Card(colors = CardDefaults.cardColors(containerColor = Color.White)) {
                Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(Modifier.size(44.dp).background(color, RoundedCornerShape(14.dp)), contentAlignment = Alignment.Center) {
                        Icon(Icons.Default.Book, contentDescription = null, tint = Leaf)
                    }
                    Column(Modifier.weight(1f).padding(start = 12.dp)) {
                        Text(name, fontWeight = FontWeight.Bold)
                        Text(detail, color = Muted, fontSize = 12.sp)
                    }
                }
            }
        }
        Text(if (tamil) "மாதிரி பாடங்கள்; உங்கள் வகுப்பு மற்றும் பாடத்திட்டத்தைத் தேர்ந்தெடுத்த பின் மாற்றப்படும்." else "Sample subjects. Curriculum mapping will be personalized after setup.", color = Muted, fontSize = 11.sp)
    }
}

@Composable
private fun PlannerScreen(tamil: Boolean, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(if (tamil) "படிப்பு திட்டம்" else "Study planner", fontSize = 26.sp, fontWeight = FontWeight.Bold)
        Text(if (tamil) "உங்கள் நாளை எளிதாகத் திட்டமிடுங்கள்." else "A manageable plan beats a stressful one.", color = Muted)
        Card(colors = CardDefaults.cardColors(containerColor = PaleGreen)) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(if (tamil) "இன்றைய பரிந்துரை" else "Today's suggested plan", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Text(if (tamil) "45 நிமிடங்கள் · 3 சிறிய பணிகள்" else "45 minutes · 3 small tasks")
                Text(if (tamil) "இது ஒரு மாதிரி திட்டம். தனிப்பயன் திட்டம் அடுத்த கட்டத்தில் உருவாக்கப்படும்." else "This is a sample plan. Personalized scheduling is a next milestone.", color = Muted, fontSize = 12.sp)
            }
        }
        TaskRow("1. Mathematics", if (tamil) "பயிற்சி கேள்விகள்" else "Practice questions", "20 min", Color.White)
        TaskRow("2. Science", if (tamil) "முக்கிய கருத்துகளை மீள்பார்க்கவும்" else "Review key concepts", "15 min", Color.White)
        TaskRow("3. English", if (tamil) "சொற்களஞ்சியம்" else "Vocabulary practice", "10 min", Color.White)
    }
}

@Composable
private fun ProfileScreen(tamil: Boolean, onLanguage: () -> Unit, modifier: Modifier = Modifier) {
    Column(modifier.fillMaxSize().padding(18.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(if (tamil) "என் சுயவிவரம்" else "Your profile", fontSize = 26.sp, fontWeight = FontWeight.Bold)
        Card(colors = CardDefaults.cardColors(containerColor = Color.White)) {
            Column(Modifier.fillMaxWidth().padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Icon(Icons.Default.Person, contentDescription = null, tint = Leaf, modifier = Modifier.size(42.dp))
                Text(if (tamil) "மாணவர் சுயவிவரம்" else "Student profile", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                Text(if (tamil) "வகுப்பு, கல்வி வாரியம் மற்றும் இலக்குகள் விரைவில் அமைக்கலாம்." else "Class, board, language and study goals will be configurable in onboarding.", color = Muted)
                Button(onClick = onLanguage) {
                    Icon(Icons.Default.Language, contentDescription = null)
                    Text(if (tamil) "  Switch to English" else "  தமிழுக்கு மாற்று")
                }
            }
        }
        Text("PadippuPal · 0.1.0", color = Muted)
    }
}

@Composable
private fun SectionTitle(text: String) {
    Text(text, fontSize = 19.sp, fontWeight = FontWeight.Bold, color = Ink)
}

@Composable
private fun StatCard(title: String, value: String, icon: androidx.compose.ui.graphics.vector.ImageVector, modifier: Modifier = Modifier) {
    Card(modifier, colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(18.dp)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Icon(icon, contentDescription = null, tint = Leaf)
            Text(value, fontSize = 27.sp, fontWeight = FontWeight.Bold)
            Text(title, color = Muted, fontSize = 12.sp)
        }
    }
}

@Composable
private fun TaskRow(subject: String, detail: String, duration: String, color: Color) {
    Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(18.dp)) {
        Row(Modifier.fillMaxWidth().padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(10.dp).background(color.takeUnless { it == Color.White } ?: Leaf, CircleShape))
            Column(Modifier.weight(1f).padding(start = 12.dp)) {
                Text(subject, fontWeight = FontWeight.SemiBold)
                Text(detail, color = Muted, fontSize = 12.sp)
            }
            Text(duration, color = Leaf, fontWeight = FontWeight.SemiBold, fontSize = 12.sp)
        }
    }
}
