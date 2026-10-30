# Architecture Inventory

> This is an evidence-labelled inventory, not a claim that every runtime dependency has been traced. Expand it by inspecting source and tests before making architectural changes.

## Repository-observed structure
| Area | Observed location | Verified responsibility / evidence |
|---|---|---|
| Android application | `app/src/main/java/com/padippupal/app/` | Kotlin/Jetpack Compose app. README identifies Kotlin + Jetpack Compose. Source includes `MainActivity.kt`, `TutorScreen.kt`, `CurriculumConnection.kt`, `ExamMasterScreen.kt`, `StudyFeatures.kt`. |
| Android unit tests | `app/src/test/` | Kotlin tests currently include `AllOnesTopicValidatorTest.kt`. Inspect test coverage before relying on it. |
| Backend API and tutor | `backend/app.py` | Main Python backend entry point; README documents tutor chat and speech endpoints. Exact route/service decomposition requires source inspection. |
| Curriculum synthesis | `backend/syllabus_synthesis.py` | Synthesis module by filename; detailed call graph and persistence contract require source inspection. |
| Lesson visuals | `backend/lesson_visuals.py`, `backend/textbook_visual_refs.py` | Visual-related backend modules; renderer/data contracts require source inspection. |
| Exam Master | `backend/exam_master.py` | Exam Master backend module. |
| Backend tests | `backend/test_*.py` | Unit/API/consistency test files cover app, lessons, visuals, synthesis, tutor and study features. |
| Curriculum/source configuration | `backend/interactive_lessons.json`, `backend/source_registry.json` | JSON configuration/data files; verify schema and rights/provenance before modifying or ingesting content. |
| Auxiliary app | `kokoro-space/` | Separate directory with its own `requirements.txt`; purpose and deployment lifecycle require further inspection. |
| Product/engineering docs | `docs/` | Includes concept mastery, live teaching design, synthesis/visual mapping, release acceptance and test investigation records. |

## Build/toolchain facts from README
- README documents JDK 17, Android SDK platform 35 and Gradle 8.9.
- README documents `gradle assembleDebug`.
- Verify whether a Gradle wrapper exists and inspect CI setup before selecting a build command. Do not infer wrapper availability from the README.

## Known product constraints from README
- Textbook medium and explanation language are separate settings.
- Tutor reasoning is documented as Gemini via server-side `GEMINI_API_KEY`; keys belong in backend/hosting environment, not app source.
- Speech fallback is documented as Sarvam, Gemini TTS when configured, then Android TTS.
- Official source registry currently approves no official curriculum text for ingestion (per README at reconciliation); do not claim official textbook-grounded coverage without re-verifying the registry.
- Diary OCR, full chapter lesson generation, concept mastery and PDF export are described as incomplete in README. Reconcile this statement with current source before planning those areas.

## Architecture questions intentionally left open
These require source-level tracing before being treated as facts:
1. Exact Android-to-backend request/response contracts and error handling.
2. Exact synthesis trigger, orchestration, persistence and cache invalidation path.
3. Visual asset schema, generation path, retrieval path and Android renderer mapping.
4. Database schema, branch strategy and production/test separation.
5. Authentication, authorization and student data privacy boundaries.
6. Background jobs, retries, idempotency and observability.
7. Deployment topology, environment variables and release rollback path.

## Update protocol
For each module, document entry points, public interfaces, callers/callees, data contracts, persistence, external services, failure modes, tests and source file/line references. Mark each statement VERIFIED, INFERRED or UNKNOWN and include the commit inspected.
