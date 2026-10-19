# PadippuPal

**Your Personal Study Buddy · உங்கள் படிப்பு நண்பன்**

PadippuPal is an Android learning companion for school students, planned for CBSE and Tamil Nadu State Board learners. The student's textbook medium (Tamil or English) is separate from their chosen app/explanation language (English or Tanglish).

## Product vision

PadippuPal should take a student from a school diary entry or selected chapter to genuine understanding and print-ready revision material. It must teach concepts and applications—not just summarize a chapter or repeat textbook exercise answers. Exams may test the same idea in unfamiliar wording or new situations, so concept mastery is a core product requirement.

## Current prototype

- Kotlin + Jetpack Compose Android app
- Home dashboard with sample daily tasks
- Subjects overview
- Curriculum connection screen with HTTPS health checks and profile-filtered passage retrieval (requires a deployed API URL)
- Study planner preview
- English/Tamil UI toggle (prototype; Tanglish support is part of the product plan)
- GitHub Actions workflow to build and upload a debug APK

The current UI is a prototype. The curriculum connection screen calls the backend health and retrieval APIs when an HTTPS endpoint is configured. A gentle AI tutor chat screen and server-side Groq integration are now implemented on the feature branch; live AI answers require GROQ_API_KEY in the backend environment. No official curriculum files are loaded yet, and diary OCR, full chapter lesson generation, concept mastery, persistent progress, and PDF export are not yet implemented.

## Concept mastery: core learning flow

For a selected chapter, PadippuPal should:
1. Match the student's board, standard, subject, term (where relevant), textbook edition and chapter against the saved syllabus library. Ask for clarification if the match is ambiguous.
2. Analyse the full chapter into core concepts, sub-concepts, definitions, relationships, processes, formulas, diagrams, examples, prerequisites, common misconceptions and exercises.
3. Prioritize concepts using curriculum emphasis, approved past/sample papers when available, foundational importance, diary/test cues and the student's weak areas. Treat importance as an informed estimate, never a promise of what will appear in an exam.
4. Teach in small steps using age-appropriate language, relevant visuals, familiar examples, worked examples and "explain it another way" support.
5. Check understanding after each concept and create varied questions beyond the textbook: explain why, compare, predict what happens if, apply to a new scenario, interpret diagrams/data, solve multi-step problems and correct misconceptions.
6. Use wrong answers to identify the underlying misunderstanding, reteach the concept differently and provide a follow-up check.
7. Generate a print-ready A4 PDF with notes, useful visuals, key terms, textbook-style questions, novel concept questions, answers and a revision checklist.

## Personalization rules

- Class/standard controls depth, vocabulary, prerequisites, visual complexity, examples, question difficulty and answer length.
- Board and textbook edition control syllabus alignment.
- Medium of instruction controls official subject terminology.
- English/Tanglish preference controls the language of the app and explanations; it does not change the curriculum.
- Learning history adjusts pace and scaffolding while preserving the expected standard.
- Younger learners need concrete examples and short steps; older learners need deeper reasoning and more demanding applications. These are starting points, not substitutes for the actual curriculum.

## Accuracy principles

- Ground syllabus-specific claims in the saved, approved textbook/library and keep source references where possible.
- Clearly distinguish textbook-backed information from extra examples and AI-generated practice.
- Do not claim any generated question is guaranteed to appear in an exam.
- If the correct source is unavailable or ambiguous, say so instead of inventing chapter details, official answers, page numbers or marking schemes.
- Check the quality and readability of diagrams and PDFs before presenting them as finished study material.

Detailed requirements and release sequence: [Concept Mastery Engine](docs/CONCEPT_MASTERY.md).

## Build

Requires JDK 17, Android SDK platform 35 and Gradle 8.9.

```bash
gradle assembleDebug

# Optional: embed a deployed HTTPS curriculum API base URL at build time
gradle -PPADIPPUPAL_API_BASE_URL=https://your-deployed-api.example.com assembleDebug
```

The debug APK is generated at `app/build/outputs/apk/debug/app-debug.apk`.

A successful GitHub Actions run uploads an artifact named **PadippuPal-debug-apk**. Open the repository's Actions tab, select a successful workflow run, and download the artifact.

## Roadmap

1. Student onboarding: name, standard, board, medium, and English/Tanglish preference
2. Structured, versioned syllabus library and reliable chapter matching
3. Chapter concept analysis and a standard-aware visual lesson experience
4. Novel concept questions, diagnostic feedback, and adaptive reteaching
5. Print-ready PDF generation with answers and source references
6. Diary camera/OCR, homework/test extraction, and automatic chapter matching
7. Persistent learning history, weak-concept detection and personalized planning
8. Parent progress view, curriculum verification and robust testing


## Gentle AI tutor implementation

The tutor screen supports English, Tanglish and Tamil response preferences, a student-friendly teaching prompt, and short conversation context. Groq remains the tutor's chat/reasoning provider (`POST /tutor/chat`, server-side `GROQ_API_KEY`). Natural spoken replies use Gemini 3.8 Flash-Lite TTS through `POST /tutor/speech` (`GEMINI_API_KEY` stored only in the backend/Render environment), with Android text-to-speech as a fallback. Gemini quota and billing depend on the Google AI account; do not assume unlimited free usage.
