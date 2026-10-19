# PadippuPal

**Your Personal Study Buddy · உங்கள் படிப்பு நண்பன்**

PadippuPal is an Android learning companion for school students, planned for CBSE and Tamil Nadu State Board learners with English and Tamil support.

## Current prototype

- Kotlin + Jetpack Compose Android app
- Home dashboard with sample daily tasks
- Subjects overview
- Study planner preview
- English/Tamil UI toggle
- GitHub Actions workflow to build and upload a debug APK

## Build

Requires JDK 17, Android SDK platform 35 and Gradle 8.9.

```bash
gradle assembleDebug
```

The debug APK is generated at `app/build/outputs/apk/debug/app-debug.apk`.

A successful GitHub Actions run uploads an artifact named **PadippuPal-debug-apk**. Open the repository's Actions tab, select a successful workflow run, and download the artifact.

## Important prototype notes

The displayed subjects and tasks are sample data. Progress is not persisted yet. Diary OCR, official syllabus data, student profiles, adaptive planning, assessments, and AI tutoring are planned milestones and are not implemented in this initial prototype.

## Roadmap

1. Student onboarding: class, board, language, available study time
2. Diary capture and assignment/test extraction
3. Structured syllabus and chapter mapping
4. Learning assessments and weak-chapter detection
5. Personalized study plan and progress persistence
6. English/Tamil AI tutoring and practice generation
7. Parent progress view and robust testing
