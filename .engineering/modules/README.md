# Module Documentation Index

Module records must be based on source inspection, not filenames alone. For each module, record:
- inspected commit SHA and date;
- responsibility and entry points;
- public interfaces and callers/callees;
- request/response/data schemas;
- persistence and external dependencies;
- error handling and observability;
- tests and coverage gaps;
- security/privacy considerations;
- known limitations and open questions.

Current module inventory:
- Android tutor and visual experience — `app/src/main/java/com/padippupal/app/TutorScreen.kt`
- Android app entry/navigation — `app/src/main/java/com/padippupal/app/MainActivity.kt`
- Android curriculum connection — `app/src/main/java/com/padippupal/app/CurriculumConnection.kt`
- Backend API/tutor — `backend/app.py`
- Curriculum synthesis — `backend/syllabus_synthesis.py`
- Lesson visuals — `backend/lesson_visuals.py`
- Exam Master — `backend/exam_master.py`

These are starting pointers, not completed architecture specifications.
