# Architecture — inspected repository map

**Inspected against:** `main@407844ea458799eadc99b9af1e7364939902e9dd`  
**Last inspected:** 2026-10-30

## Repository layers

### Android client
- Source root: `app/src/main/java/com/padippupal/app/`
- `MainActivity.kt`: Compose app entry point, top-level navigation, learner profile preferences, and app-level screen composition.
- `TutorScreen.kt`: tutor UI, tutor request/playback state, captions, speech integration, and inline lesson/visual presentation. This is a large, high-coupling file; inspect the exact call path before making changes.
- `CurriculumConnection.kt`: curriculum connection UI/API integration.
- `StudyFeatures.kt`, `ExamMasterScreen.kt`: study/planner and exam-oriented feature surfaces.
- `AllOnesTopicValidator.kt`: Android-side lesson-topic validation.
- Android JVM tests currently include `AllOnesTopicValidatorTest.kt`; inspect current test inventory before assuming coverage.

### Backend
- Source root: `backend/`
- `app.py`: FastAPI application and HTTP route composition.
- `syllabus_synthesis.py`: syllabus/chapter synthesis logic.
- `lesson_visuals.py`: visual blueprint generation/rendering helpers.
- `textbook_visual_refs.py`: textbook figure-reference analysis helpers.
- `exam_master.py`: exam-oriented functionality.
- `interactive_lessons.json`: interactive lesson blueprint data.
- Tests are colocated as `backend/test_*.py`.

The backend README describes a prototype curriculum service, persistent SQLite source/job storage, keyword-based retrieval, and a source registry whose entries were not approved for automatic ingestion at the time that file was inspected. Deployment-specific persistence and provider configuration must be checked against the live environment before database work; never infer production storage from local documentation alone.

### CI and quality checks
- `.github/workflows/android.yml`: Android build workflow.
- `.github/workflows/android-ui-smoke.yml`: Android emulator/UI smoke workflow.
- `.github/workflows/curriculum-engine.yml`: backend/curriculum test workflow.
- `.github/workflows/deployed-api-smoke.yml`: deployed API smoke workflow.
- `.github/workflows/investigation-guidance.yml`: guidance/ledger validation.
- `.github/scripts/`: smoke harnesses, fixtures, test helpers, and investigation tooling.
- `TESTING_GUIDANCE.md`, `.github/testing-regression-checklist.md`, `docs/TESTING_ERRORS.md`, and `TEST_INVESTIGATION.md` are mandatory or supporting quality records.

## Architectural boundaries and cautions
- Android should call backend APIs; provider credentials belong on the server, not in the APK.
- Model output must be schema-validated and mapped to allowlisted app behavior. Never execute arbitrary model-generated code.
- Visual data must remain bound to the exact lesson/topic/profile and source evidence; a topic name alone is not sufficient evidence.
- Curriculum provenance and copyright/permission are separate from the presence of a lesson blueprint.
- A CI workflow passing does not prove production deployment or target-phone behavior.
- Do not assume every branch has the same architecture or that open PR changes are part of `main`.

## What still needs deeper architecture extraction
- Exact API route/request/response schemas and client call sites.
- Runtime database provider, migrations/schema ownership, and environment-specific data flow.
- Synthesis-to-visual persistence triggers and idempotency behavior.
- Voice provider selection, audio lifecycle, interruption/recovery, and privacy boundaries.
- Authentication/authorization boundaries for admin ingestion and learner APIs.
- Deployment topology, service names, health checks, and rollback procedure.

Mark these as unknown until inspected from code/configuration and verified environment evidence. Update this map when those inspections are completed.
