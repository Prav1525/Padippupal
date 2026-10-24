package com.padippupal.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import java.util.UUID

private val Green=Color(0xFF0F766E)
private val Deep=Color(0xFF0F2742)
private val Mint=Color(0xFFD8F5F0)
private val Paper=Color(0xFFF7FAFC)
private val Grey=Color(0xFF526477)
private val Yellow=Color(0xFFF4C96B)
private val Peach=Color(0xFFFFF0E5)
private val Lilac=Color(0xFFEEF2FF)

class MainActivity:ComponentActivity(){
 override fun onCreate(savedInstanceState:Bundle?){super.onCreate(savedInstanceState)
 window.statusBarColor=android.graphics.Color.rgb(247,250,252)
 window.navigationBarColor=android.graphics.Color.rgb(247,250,252)
 window.decorView.systemUiVisibility=android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR or android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
 setContent{PadippuPalApp()}
 }
}
private enum class Page{HOME,SUBJECTS,PLANNER,PROFILE,CURRICULUM,LESSON_SETUP,TUTOR,SCAN,LESSON,QUESTIONS,PDF,EXAM_MASTER,SETUP}

@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun PadippuPalApp(){
 val context = LocalContext.current
 val prefs = remember { context.getSharedPreferences("padippupal_profile", android.content.Context.MODE_PRIVATE) }
 val profileId = remember {
   prefs.getString("profile_id", null) ?: UUID.randomUUID().toString().also { prefs.edit().putString("profile_id", it).apply() }
 }
 var page by remember{mutableStateOf(Page.HOME)}
 BackHandler(enabled = page != Page.HOME) { page = Page.HOME }
 var language by remember{mutableStateOf(prefs.getString("language", "English") ?: "English")}
 var name by remember{mutableStateOf(prefs.getString("student_name", "") ?: "")}
 var grade by remember{mutableStateOf(prefs.getString("grade", "6") ?: "6")}
 var board by remember{mutableStateOf(prefs.getString("board", "Tamil Nadu State Board") ?: "Tamil Nadu State Board")}
 var medium by remember{mutableStateOf(prefs.getString("medium", "English") ?: "English")}
 LaunchedEffect(name, grade, board, medium, language) {
   prefs.edit().putString("student_name", name).putString("grade", grade)
     .putString("board", board).putString("medium", medium).putString("language", language).apply()
 }
 var lesson by remember{mutableStateOf("Crop Production and Management")}
 var done by remember{mutableStateOf(setOf<String>())}
 val tamil=language=="தமிழ்"
 MaterialTheme(colorScheme = lightColorScheme(primary = Green, onPrimary = Color.White, secondary = Color(0xFF6366F1), onSecondary = Deep, background = Paper, surface = Color(0xFFFFFFFF), onSurface = Deep, surfaceVariant = Color(0xFFE2E8F0), onSurfaceVariant = Grey, outline = Color(0xFFD8E3EA))) {
  Scaffold(
    containerColor = Paper,
    topBar = {
      if (page !in listOf(Page.TUTOR, Page.LESSON_SETUP, Page.SCAN, Page.LESSON, Page.QUESTIONS, Page.PDF, Page.EXAM_MASTER, Page.SETUP)) {
        TopAppBar(
          title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
              Logo(36)
              Column(Modifier.padding(start = 10.dp)) {
                Text("PadippuPal", fontSize = 19.sp, fontWeight = FontWeight.SemiBold, fontFamily = androidx.compose.ui.text.font.FontFamily.SansSerif, color = Deep)
                Text(if (tamil) "உன் படிப்பு நண்பன்" else "A thoughtful study companion", fontSize = 10.sp, color = Grey)
              }
            }
          },
          actions = {
            IconButton(onClick = { language = if (tamil) "English" else "தமிழ்" }) {
              Icon(Icons.Default.Translate, contentDescription = "Change language", tint = Green)
            }
          },
          colors = TopAppBarDefaults.topAppBarColors(containerColor = Paper),
          windowInsets = WindowInsets.statusBars
        )
      }
    },
    bottomBar = {
      if (page in listOf(Page.HOME, Page.SUBJECTS, Page.PLANNER, Page.PROFILE, Page.CURRICULUM)) {
        NavigationBar(containerColor = Color.White) {
          listOf(
            Triple(Page.HOME, "Home", Icons.Default.Home),
            Triple(Page.SUBJECTS, "Learn", Icons.Default.MenuBook),
            Triple(Page.PLANNER, "Plan", Icons.Default.CalendarMonth),
            Triple(Page.PROFILE, "You", Icons.Default.Person)
          ).forEach { (p, label, icon) ->
            NavigationBarItem(
              selected = page == p,
              onClick = { page = p },
              icon = { Icon(icon, contentDescription = label) },
              label = {
                Text(
                  if (tamil) when (label) {
                    "Home" -> "முகப்பு"
                    "Learn" -> "கற்க"
                    "Plan" -> "திட்டம்"
                    else -> "நீ"
                  } else label,
                  fontSize = 10.sp,
                  fontWeight = if (page == p) FontWeight.SemiBold else FontWeight.Normal
                )
              },
              colors = NavigationBarItemDefaults.colors(
                selectedIconColor = Green,
                selectedTextColor = Green,
                indicatorColor = Mint,
                unselectedIconColor = Grey,
                unselectedTextColor = Grey
              )
            )
          }
        }
      }
    }
  ) { padding ->
    when (page) {
      Page.HOME -> Home(tamil, name, done, { page = it }, Modifier.padding(padding))
      Page.SUBJECTS -> Subjects(tamil, { lesson = it; page = Page.LESSON }, Modifier.padding(padding))
      Page.PLANNER -> PlannerScreen(profileId = profileId, onBack = { page = Page.HOME }, modifier = Modifier.padding(padding))
      Page.PROFILE -> Profile(name, grade, board, medium, language, { page = Page.SETUP }, Modifier.padding(padding))
      Page.CURRICULUM -> CurriculumConnectionScreen(grade = grade.toIntOrNull() ?: 6, board = board, medium = medium, onBack = { page = Page.HOME }, modifier = Modifier.padding(padding))
      Page.LESSON_SETUP -> TutorScreen(grade = grade.toIntOrNull() ?: 6, board = board, medium = medium, appLanguage = language, studentName = name, onBack = { page = Page.HOME }, modifier = Modifier.padding(padding), setupOnly = true, onStartTeaching = { page = Page.TUTOR })
      Page.TUTOR -> TutorScreen(grade = grade.toIntOrNull() ?: 6, board = board, medium = medium, appLanguage = language, studentName = name, onBack = { page = Page.HOME }, modifier = Modifier.padding(padding))
      Page.SCAN -> DiaryScanScreen(profileId = profileId, grade = grade.toIntOrNull() ?: 6, board = board, medium = medium, language = language, onBack = { page = Page.HOME }, onSaved = { page = Page.PLANNER })
      Page.LESSON -> Lesson(lesson, { page = Page.QUESTIONS }, { page = Page.SUBJECTS })
      Page.QUESTIONS -> Questions(lesson, { page = Page.LESSON }, { page = Page.PDF })
      Page.PDF -> RevisionPdfScreen(profileId = profileId, studentName = name, grade = grade.toIntOrNull() ?: 6, board = board, medium = medium, lessonTitle = lesson, onBack = { page = Page.HOME }, modifier = Modifier.padding(padding))
      Page.EXAM_MASTER -> ExamMasterScreen(studentName = name, board = board, medium = medium, onBack = { page = Page.HOME }, modifier = Modifier.padding(padding))
      Page.SETUP -> Setup(name, grade, board, medium, language, { name = it }, { grade = it }, { board = it }, { medium = it }, { language = it }, { page = Page.PROFILE })
    }
  }
 }
}

@Composable private fun Logo(size:Int){Box(Modifier.size(size.dp).background(Deep,RoundedCornerShape((size/3).dp)),contentAlignment=Alignment.Center){Icon(Icons.Default.MenuBook,null,tint=Color(0xFFF8FAFC),modifier=Modifier.size((size*.62f).dp));Box(Modifier.align(Alignment.TopEnd).padding(3.dp).size((size*.25f).dp).background(Color(0xFF14B8A6),CircleShape),contentAlignment=Alignment.Center){Icon(Icons.Default.AutoAwesome,null,tint=Deep,modifier=Modifier.size((size*.15f).dp))}}}
@Composable private fun Home(tamil:Boolean,name:String,done:Set<String>,go:(Page)->Unit,modifier:Modifier=Modifier){
 LazyColumn(
   modifier.fillMaxSize().background(Paper).padding(horizontal=22.dp),
   verticalArrangement=Arrangement.spacedBy(20.dp),
   contentPadding=PaddingValues(top=18.dp,bottom=28.dp)
 ){
   item {
     Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.Top,horizontalArrangement=Arrangement.SpaceBetween) {
       Column(Modifier.weight(1f)) {
         Text(if(tamil) "வணக்கம்" else "YOUR LEARNING DESK",fontSize=10.sp,fontWeight=FontWeight.Bold,color=Green,letterSpacing=2.sp)
         Text(if(name.isNotBlank()) "Hello, $name." else if(tamil) "வணக்கம், நண்பா." else "A little wiser today.",fontSize=31.sp,lineHeight=36.sp,fontWeight=FontWeight.Normal,fontFamily=androidx.compose.ui.text.font.FontFamily.Serif,color=Deep,modifier=Modifier.padding(top=7.dp))
         Text(if(tamil) "இன்றைய சிறு முயற்சி, நாளைய பெரிய வளர்ச்சி." else "A calmer way to learn, one idea at a time.",fontSize=13.sp,lineHeight=19.sp,color=Grey,modifier=Modifier.padding(top=7.dp))
       }
       Box(Modifier.padding(top=4.dp).size(44.dp).background(Mint,CircleShape),contentAlignment=Alignment.Center) {
         Text(if(name.isNotBlank()) name.take(1).uppercase() else "P",fontSize=18.sp,fontWeight=FontWeight.SemiBold,color=Green)
       }
     }
   }
   item {
     Card(
       Modifier.fillMaxWidth().clickable { go(Page.LESSON_SETUP) },
       shape=RoundedCornerShape(24.dp),
       colors=CardDefaults.cardColors(containerColor=Deep),
       elevation=CardDefaults.cardElevation(defaultElevation=0.dp)
     ) {
       Column(Modifier.fillMaxWidth().padding(21.dp),verticalArrangement=Arrangement.spacedBy(15.dp)) {
         Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.SpaceBetween) {
           Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(8.dp)) {
             Box(Modifier.size(31.dp).background(Color.White.copy(alpha=.12f),CircleShape),contentAlignment=Alignment.Center) {
               Icon(Icons.Default.AutoAwesome,null,tint=Color(0xFF14B8A6),modifier=Modifier.size(17.dp))
             }
             Text(if(tamil) "உன் தனிப்பட்ட ஆசிரியர்" else "YOUR PERSONAL TUTOR",fontSize=10.sp,fontWeight=FontWeight.Bold,color=Color(0xFF14B8A6),letterSpacing=1.2.sp)
           }
           Icon(Icons.Default.ArrowOutward,null,tint=Color.White.copy(alpha=.75f),modifier=Modifier.size(19.dp))
         }
         Text(if(tamil) "புரியும் வரை கற்போம்." else "Let’s make it\nmake sense.",fontSize=29.sp,lineHeight=33.sp,fontWeight=FontWeight.Normal,fontFamily=androidx.compose.ui.text.font.FontFamily.Serif,color=Color.White)
         Text(if(tamil) "கேள், பேசு, உன் வேகத்தில் கற்றுக்கொள்." else "Ask in English, Tamil or Tanglish. Learn at your own pace, with gentle explanations.",fontSize=13.sp,lineHeight=20.sp,color=Color.White.copy(alpha=.82f))
         Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.SpaceBetween) {
           Row(Modifier.background(Color(0xFF173B55),RoundedCornerShape(50)).padding(horizontal=11.dp,vertical=7.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(6.dp)) {
             Icon(Icons.Default.GraphicEq,null,tint=Color(0xFF14B8A6),modifier=Modifier.size(16.dp))
             Text(if(tamil) "குரல் அல்லது உரை" else "Voice or text",fontSize=11.sp,color=Color.White,fontWeight=FontWeight.Medium)
           }
           Text(if(tamil) "தொடங்கு  →" else "Begin lesson  →",fontSize=13.sp,color=Color(0xFFE0F7F4),fontWeight=FontWeight.SemiBold)
         }
       }
     }
   }
   item {
     Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.SpaceBetween) {
       Column {
         Text(if(tamil) "எங்கே தொடங்கலாம்?" else "A good place to start",fontSize=21.sp,fontWeight=FontWeight.Normal,fontFamily=androidx.compose.ui.text.font.FontFamily.Serif,color=Deep)
         Text(if(tamil) "உனக்குத் தேவையானதைத் தேர்வு செய்" else "Choose what you need today.",fontSize=12.sp,color=Grey,modifier=Modifier.padding(top=3.dp))
       }
       Text("01 / 04",fontSize=10.sp,color=Grey,letterSpacing=1.sp)
     }
   }
   item {
     Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(11.dp)) {
       Tile("My subjects","Chapters & concepts",Icons.Default.MenuBook,Mint,Modifier.weight(1f)){go(Page.SUBJECTS)}
       Tile("Study planner","A plan that fits",Icons.Default.CalendarMonth,Color(0xFFF1F5F9),Modifier.weight(1f)){go(Page.PLANNER)}
     }
   }
   item {
     Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(11.dp)) {
       Tile("Scan homework","Turn diary notes into a plan",Icons.Default.DocumentScanner,Color(0xFFFFF0E5),Modifier.weight(1f)){go(Page.SCAN)}
       Tile("Exam practice","Build a question paper",Icons.Default.Quiz,Color(0xFFEAF0FF),Modifier.weight(1f)){go(Page.EXAM_MASTER)}
     }
   }
   item {
     Card(
       Modifier.fillMaxWidth().clickable { go(Page.CURRICULUM) },
       shape=RoundedCornerShape(19.dp),
       colors=CardDefaults.cardColors(containerColor=Color(0xFFF1F5F9)),
       elevation=CardDefaults.cardElevation(defaultElevation=0.dp)
     ) {
       Row(Modifier.fillMaxWidth().padding(horizontal=16.dp,vertical=15.dp),verticalAlignment=Alignment.CenterVertically) {
         Box(Modifier.size(42.dp).background(Color.White.copy(alpha=.8f),RoundedCornerShape(13.dp)),contentAlignment=Alignment.Center) {
           Icon(Icons.Default.MenuBook,null,tint=Green,modifier=Modifier.size(22.dp))
         }
         Column(Modifier.weight(1f).padding(start=12.dp,end=8.dp)) {
           Text(if(tamil) "உன் பாடத்திட்டத்துடன் இணை" else "Learn from your syllabus",fontSize=14.sp,fontWeight=FontWeight.SemiBold,color=Deep)
           Text(if(tamil) "வகுப்பு மற்றும் பாடநூல் விவரங்கள்" else "Find lessons matched to your class and textbook.",fontSize=11.sp,lineHeight=16.sp,color=Grey,modifier=Modifier.padding(top=3.dp))
         }
         Icon(Icons.Default.ChevronRight,null,tint=Green)
       }
     }
   }
   item {
     Row(Modifier.fillMaxWidth().padding(top=1.dp),verticalAlignment=Alignment.CenterVertically) {
       Box(Modifier.width(3.dp).height(37.dp).background(Color(0xFF14B8A6),RoundedCornerShape(2.dp)))
       Column(Modifier.padding(start=12.dp)) {
         Text("A note to remember",fontSize=15.sp,fontWeight=FontWeight.Normal,fontFamily=androidx.compose.ui.text.font.FontFamily.Serif,color=Deep)
         Text("You don’t have to learn everything at once. Just the next thing.",fontSize=12.sp,lineHeight=18.sp,color=Grey,modifier=Modifier.padding(top=2.dp))
       }
     }
   }
 }
}
@Composable private fun Stat(label:String,value:String,icon:ImageVector,tint:Color,modifier:Modifier){Card(modifier,colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(20.dp)){Row(Modifier.padding(13.dp),verticalAlignment=Alignment.CenterVertically){Box(Modifier.size(36.dp).background(tint,CircleShape),contentAlignment=Alignment.Center){Icon(icon,null,tint=Green)};Column(Modifier.padding(start=9.dp)){Text(value,fontSize=18.sp,fontWeight=FontWeight.ExtraBold);Text(label,fontSize=11.sp,color=Grey)}}}}
@Composable private fun Heading(title:String,sub:String){Column{Text(title,fontSize=19.sp,fontWeight=FontWeight.Bold,color=Deep);Text(sub,fontSize=12.sp,color=Grey)}}
@Composable private fun Tile(title:String,sub:String,icon:ImageVector,tint:Color,modifier:Modifier,click:()->Unit){Card(modifier.clickable(onClick=click),colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(20.dp)){Column(Modifier.fillMaxWidth().padding(14.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){Box(Modifier.size(42.dp).background(tint,RoundedCornerShape(14.dp)),contentAlignment=Alignment.Center){Icon(icon,null,tint=Green,modifier=Modifier.size(23.dp))};Text(title,fontWeight=FontWeight.Bold);Text(sub,fontSize=11.sp,color=Grey)}}}

@Composable private fun Subjects(tamil:Boolean,open:(String)->Unit,modifier:Modifier=Modifier){val subjects=listOf(Triple("Mathematics","4 chapters · Practice regularly",Mint),Triple("Science","6 chapters · Understand concepts",Peach),Triple("English","5 chapters · Reading and writing",Lilac),Triple("Tamil","மொழிப்பயிற்சி",Color(0xFFFCE7F3)),Triple("Social Science","History, geography and civics",Color(0xFFE8F2FA)),Triple("Computer Science","Concepts and practical skills",Mint));LazyColumn(modifier.fillMaxSize().padding(horizontal=18.dp),verticalArrangement=Arrangement.spacedBy(12.dp),contentPadding=PaddingValues(top=15.dp,bottom=24.dp)){item{Text(if(tamil)"என் பாடங்கள்" else "My subjects",fontSize=27.sp,fontWeight=FontWeight.ExtraBold,color=Deep);Text("Choose a subject to explore a sample lesson.",color=Grey)};items(subjects){(s,d,c)->Card(Modifier.fillMaxWidth().clickable{open(if(s=="Science")"Crop Production and Management" else "$s · Sample concept")},colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(20.dp)){Row(Modifier.padding(15.dp),verticalAlignment=Alignment.CenterVertically){Box(Modifier.size(48.dp).background(c,RoundedCornerShape(15.dp)),contentAlignment=Alignment.Center){Icon(Icons.Default.MenuBook,null,tint=Green)};Column(Modifier.weight(1f).padding(start=13.dp)){Text(s,fontWeight=FontWeight.Bold);Text(d,color=Grey,fontSize=12.sp)};Icon(Icons.Default.ChevronRight,null,tint=Grey)}}};item{Text("Sample subjects until your class and board are configured.",color=Grey,fontSize=11.sp)}}}
@Composable private fun Planner(done:Set<String>,toggle:(String)->Unit,modifier:Modifier=Modifier){val tasks=listOf(Triple("Mathematics","Practice problems","20 min"),Triple("Science","Review a key concept","15 min"),Triple("English","Vocabulary practice","10 min"));LazyColumn(modifier.fillMaxSize().padding(horizontal=18.dp),verticalArrangement=Arrangement.spacedBy(14.dp),contentPadding=PaddingValues(top=15.dp,bottom=24.dp)){item{Text("Study planner",fontSize=27.sp,fontWeight=FontWeight.ExtraBold,color=Deep);Text("A manageable plan beats a stressful one.",color=Grey)};item{Card(colors=CardDefaults.cardColors(containerColor=Green),shape=RoundedCornerShape(24.dp)){Column(Modifier.padding(20.dp),verticalArrangement=Arrangement.spacedBy(8.dp)){Icon(Icons.Default.AutoAwesome,null,tint=Yellow);Text("Your plan, one step at a time",color=Color.White,fontWeight=FontWeight.Bold,fontSize=21.sp);Text(done.size.toString()+" of 3 sample tasks checked off",color=Color.White);LinearProgressIndicator(progress={done.size/3f},color=Yellow,trackColor=Color.White.copy(alpha=.25f),modifier=Modifier.fillMaxWidth())}}};item{Heading("Today's tasks","Tap a task to mark it complete")};items(tasks){(s,d,t)->Card(Modifier.fillMaxWidth().clickable{toggle(s)},colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(18.dp)){Row(Modifier.padding(16.dp),verticalAlignment=Alignment.CenterVertically){Icon(if(s in done)Icons.Default.CheckCircle else Icons.Default.RadioButtonUnchecked,null,tint=Green);Column(Modifier.weight(1f).padding(start=12.dp)){Text(s,fontWeight=FontWeight.Bold);Text(d,color=Grey,fontSize=12.sp)};Text(t,color=Green,fontSize=12.sp,fontWeight=FontWeight.Bold)}}};item{Text("Demo progress lasts only while the app is open.",color=Grey,fontSize=11.sp)}}}
@Composable private fun Profile(name:String,grade:String,board:String,medium:String,language:String,edit:()->Unit,modifier:Modifier=Modifier){Column(modifier.fillMaxSize().padding(18.dp),verticalArrangement=Arrangement.spacedBy(15.dp)){Text("Your profile",fontSize=27.sp,fontWeight=FontWeight.ExtraBold,color=Deep);Text("A few details help us teach at the right level.",color=Grey);Card(colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(22.dp)){Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(14.dp)){Row(verticalAlignment=Alignment.CenterVertically){Logo(52);Column(Modifier.padding(start=12.dp)){Text(name.ifBlank{"Your learner profile"},fontWeight=FontWeight.Bold,fontSize=18.sp);Text("PadippuPal study buddy",color=Grey,fontSize=12.sp)}};ProfileLine("Class","Grade $grade");ProfileLine("Board",board);ProfileLine("Textbook medium",medium);ProfileLine("App language",language);Button(onClick=edit,modifier=Modifier.fillMaxWidth()){Icon(Icons.Default.Edit,null);Text("  Edit student details")}}};Text("App language is separate from textbook language.",color=Grey,fontSize=12.sp)}}
@Composable private fun ProfileLine(a:String,b:String){Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text(a,color=Grey,fontSize=13.sp);Text(b,fontWeight=FontWeight.SemiBold,fontSize=13.sp)}}
@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun Setup(name:String,grade:String,board:String,medium:String,language:String,setName:(String)->Unit,setGrade:(String)->Unit,setBoard:(String)->Unit,setMedium:(String)->Unit,setLanguage:(String)->Unit,finish:()->Unit){Column(Modifier.fillMaxSize().background(Paper).padding(20.dp),verticalArrangement=Arrangement.spacedBy(12.dp)){Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=finish){Icon(Icons.Default.ArrowBack,null)};Logo(42);Text(" Set up your buddy",fontSize=21.sp,fontWeight=FontWeight.ExtraBold,color=Deep)};OutlinedTextField(value=name,onValueChange=setName,label={Text("Student name (optional)")},singleLine=true,modifier=Modifier.fillMaxWidth());Picker("Class / standard",grade,(1..12).map{it.toString()},setGrade);Picker("Education board",board,listOf("Tamil Nadu State Board","CBSE"),setBoard);Picker("Textbook medium",medium,listOf("English","Tamil"),setMedium);Picker("App explanation language",language,listOf("English","Tanglish","தமிழ்"),setLanguage);Spacer(Modifier.weight(1f));Button(onClick=finish,modifier=Modifier.fillMaxWidth().height(52.dp)){Text("Save my details");Icon(Icons.Default.ArrowForward,null,Modifier.padding(start=8.dp))}}}
@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun Picker(label:String,value:String,options:List<String>,pick:(String)->Unit){var expanded by remember{mutableStateOf(false)};ExposedDropdownMenuBox(expanded=expanded,onExpandedChange={expanded=!expanded}){OutlinedTextField(value=value,onValueChange={},readOnly=true,label={Text(label)},trailingIcon={ExposedDropdownMenuDefaults.TrailingIcon(expanded)},modifier=Modifier.fillMaxWidth().menuAnchor(),singleLine=true);ExposedDropdownMenu(expanded=expanded,onDismissRequest={expanded=false}){options.forEach{DropdownMenuItem(text={Text(it)},onClick={pick(it);expanded=false})}}}}

@Composable private fun Lesson(title:String,next:()->Unit,back:()->Unit){LazyColumn(Modifier.fillMaxSize().padding(horizontal=18.dp),verticalArrangement=Arrangement.spacedBy(14.dp),contentPadding=PaddingValues(top=10.dp,bottom=24.dp)){item{Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=back){Icon(Icons.Default.ArrowBack,null)};Text("Concept lesson",fontWeight=FontWeight.Bold,color=Grey)}};item{Text(title,fontSize=26.sp,fontWeight=FontWeight.ExtraBold,color=Deep)};item{Text("SCIENCE · SAMPLE LESSON",fontSize=11.sp,fontWeight=FontWeight.Bold,color=Green)};item{Card(colors=CardDefaults.cardColors(containerColor=Mint),shape=RoundedCornerShape(22.dp)){Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)){Icon(Icons.Default.Spa,null,tint=Green,modifier=Modifier.size(35.dp));Text("Big idea",fontWeight=FontWeight.ExtraBold,fontSize=20.sp,color=Deep);Text("Plants need suitable conditions and care to grow well. Farmers prepare soil, select seeds, sow them, add nutrients, irrigate, protect crops and harvest at the right time.",fontSize=15.sp,lineHeight=23.sp)}}};item{Heading("Learn it in steps","Understand why, not just what")};item{Concept("01","Preparation of soil","Loosening soil helps roots grow and allows air and water to reach them.",Peach)};item{Concept("02","Sowing seeds","Healthy seeds at suitable depth and spacing have a better chance to grow.",Lilac)};item{Concept("03","Irrigation and care","Plants need appropriate water and protection from weeds and pests.",Color(0xFFE8F2FA))};item{Card(colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(20.dp)){Column(Modifier.padding(17.dp)){Text("Think about it 💭",fontWeight=FontWeight.Bold,fontSize=17.sp);Text("What might happen if seeds are sown too close together? Explain why.",color=Grey)}}};item{Button(onClick=next,modifier=Modifier.fillMaxWidth().height(52.dp)){Text("Try concept questions");Icon(Icons.Default.ArrowForward,null,Modifier.padding(start=8.dp))}};item{Text("Illustrative sample only; match to the actual board, class and textbook before study use.",color=Grey,fontSize=11.sp)}}}
@Composable private fun Concept(n:String,t:String,d:String,c:Color){Row(verticalAlignment=Alignment.Top){Box(Modifier.size(38.dp).background(c,CircleShape),contentAlignment=Alignment.Center){Text(n,fontWeight=FontWeight.ExtraBold,color=Deep)};Column(Modifier.padding(start=12.dp)){Text(t,fontWeight=FontWeight.Bold,fontSize=16.sp);Text(d,color=Grey,fontSize=13.sp,lineHeight=19.sp)}}}
@Composable private fun Questions(title:String,back:()->Unit,pdf:()->Unit){var answer by remember{mutableStateOf("")};var show by remember{mutableStateOf(false)};LazyColumn(Modifier.fillMaxSize().padding(horizontal=18.dp),verticalArrangement=Arrangement.spacedBy(15.dp),contentPadding=PaddingValues(top=10.dp,bottom=24.dp)){item{Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=back){Icon(Icons.Default.ArrowBack,null)};Text("Practice & apply",fontWeight=FontWeight.Bold,color=Grey)}};item{Text("Can you explain the idea?",fontSize=26.sp,fontWeight=FontWeight.ExtraBold,color=Deep)};item{Text(title,color=Green,fontWeight=FontWeight.SemiBold)};item{Card(colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(22.dp)){Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(12.dp)){Text("1 · Predict",color=Green,fontWeight=FontWeight.Bold);Text("A farmer sows seeds very close together. Predict two problems the seedlings might face and explain why.",fontSize=17.sp,fontWeight=FontWeight.SemiBold,lineHeight=24.sp);OutlinedTextField(value=answer,onValueChange={answer=it},label={Text("Write your answer")},modifier=Modifier.fillMaxWidth(),minLines=3);Button(onClick={show=!show},modifier=Modifier.fillMaxWidth()){Text(if(show)"Hide example answer" else "Show example answer")};if(show){Text("Example answer",fontWeight=FontWeight.Bold,color=Green);Text("Seedlings may compete for sunlight, water, nutrients and space, limiting growth. The result depends on crop and conditions.",fontSize=14.sp,lineHeight=21.sp)}}}};item{Card(colors=CardDefaults.cardColors(containerColor=Peach),shape=RoundedCornerShape(20.dp)){Column(Modifier.padding(17.dp)){Text("2 · Apply it",fontWeight=FontWeight.Bold,fontSize=17.sp);Text("How could a farmer decide whether to water a field today? Name something to observe and explain why.",fontSize=14.sp,lineHeight=21.sp)}}};item{Button(onClick=pdf,modifier=Modifier.fillMaxWidth().height(50.dp)){Icon(Icons.Default.PictureAsPdf,null);Text("  Revision sheet preview")}};item{Text("Example questions, not predictions of a specific exam paper.",color=Grey,fontSize=11.sp)}}}
@Composable private fun Detail(title:String,desc:String,icon:ImageVector,note:String,back:()->Unit){Column(Modifier.fillMaxSize().padding(22.dp),verticalArrangement=Arrangement.spacedBy(16.dp)){Row(verticalAlignment=Alignment.CenterVertically){IconButton(onClick=back){Icon(Icons.Default.ArrowBack,null)};Text("PadippuPal",fontWeight=FontWeight.Bold,color=Grey)};Spacer(Modifier.height(12.dp));Box(Modifier.size(74.dp).background(Mint,RoundedCornerShape(24.dp)),contentAlignment=Alignment.Center){Icon(icon,null,tint=Green,modifier=Modifier.size(38.dp))};Text(title,fontSize=28.sp,fontWeight=FontWeight.ExtraBold,color=Deep);Text(desc,fontSize=15.sp,lineHeight=23.sp);Card(colors=CardDefaults.cardColors(containerColor=Color.White),shape=RoundedCornerShape(18.dp)){Text(note,Modifier.padding(16.dp),color=Grey,fontSize=13.sp,lineHeight=20.sp)};Spacer(Modifier.weight(1f));Button(onClick=back,modifier=Modifier.fillMaxWidth().height(52.dp)){Text("Back to home");Icon(Icons.Default.ArrowForward,null,Modifier.padding(start=8.dp))}}}
