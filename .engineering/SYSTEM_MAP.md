# System Map

> Initial repository-level map. Arrows below show conceptual product flow, not a fully verified call graph. Confirm each connection in source before changing interfaces.

## Intended learner flow (product-level)
`Student / Android UI` → `Chapter and curriculum selection` → `Curriculum retrieval and synthesis` → `Tutor explanation and visual lesson` → `Understanding checks / practice` → `Learning history and revision outputs`.

The README describes these as product capabilities and roadmap; it explicitly notes that several remain incomplete. Do not treat this conceptual flow as proof that every stage is currently implemented end-to-end.

## Repository components
- Android UI and navigation: `MainActivity.kt`, `TutorScreen.kt`, `CurriculumConnection.kt`, `ExamMasterScreen.kt`, `StudyFeatures.kt`.
- Backend entry point: `backend/app.py`.
- Curriculum/synthesis: `backend/syllabus_synthesis.py`, `backend/source_registry.json`.
- Visual support: `backend/lesson_visuals.py`, `backend/textbook_visual_refs.py`, `backend/interactive_lessons.json`.
- Exam and study features: `backend/exam_master.py` and related modules/tests.
- Test layers: Android JVM tests, backend Python tests, GitHub Actions Android UI smoke, deployed API smoke and curriculum workflows.

## Required verified maps (not yet completed)
- Android screen/navigation map with state ownership.
- API endpoint and DTO map.
- Synthesis/visual orchestration sequence and persistence diagram.
- Database ERD with test vs production branch identifiers.
- External service and secret-boundary map.
- Deployment and rollback topology.

Do not add arrows, dependencies or runtime guarantees to this map until confirmed from code, tests or deployed telemetry.
