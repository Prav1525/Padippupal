# PadippuPal Project Status

**Snapshot date:** 2026-10-30  
**Default branch:** `main`  
**Snapshot base commit:** `407844ea458799eadc99b9af1e7364939902e9dd`  
**Repository:** https://github.com/Prav1525/Padippupal

> This is a dated, evidence-based handoff snapshot, not a live dashboard. Re-check GitHub, CI, and deployed services at the start of each resumed task.

## Product and codebase snapshot
- Android client: Kotlin + Jetpack Compose; main application screens include home/profile/curriculum/tutor and study features.
- Backend: Python FastAPI curriculum/tutor service under `backend/`.
- Curriculum/synthesis modules include `backend/syllabus_synthesis.py`, source registry and lesson-content/visual modules. Inspect current implementation before assuming any specific pipeline is fully operational.
- Android tutor and inline lesson rendering are primarily in `app/src/main/java/com/padippupal/app/TutorScreen.kt`.
- The repository contains Python backend tests and Android JVM tests plus GitHub Actions workflows for Android builds, emulator smoke, curriculum tests, deployed API smoke, and investigation-guidance validation.
- The README explicitly describes the project as a prototype and records material gaps in approved official-source coverage, OCR, complete chapter generation, concept mastery and PDF export. Verify current implementation before changing these claims.

## Verified GitHub facts at snapshot time
- Main commit: `407844ea458799eadc99b9af1e7364939902e9dd` (Beyond Earth astronomy visuals inline, PR #58).
- Default branch: `main`.
- Repository metadata reported 33 open issues/PRs combined in the open_issues count; a separate open-PR listing returned numerous active PRs. Re-fetch the list; do not treat this snapshot as current.
- PR #59, **Add native labelled whiteboard visuals for Beyond Earth**, was open at head `0383b1fe9690ff3c97dcc901c64710be04ddba14`. Its own description says Android build and chapter-specific visual verification are still required. https://github.com/Prav1525/Padippupal/pull/59
- Other open visual work at snapshot: PR #57 (inline teacher-drawing pilot) and PR #56 (topic-aware visual generation engine). These overlap in product area; review their scope and dependencies before combining or duplicating work.
- Process/automation PRs #14 (persistent development protocol), #15 (CI failure triage), #18 (AutoPilot triage), and #22 (repository work entry point) were open. They are not merged into main at this snapshot. Review before creating overlapping automation.
- No PR has been merged and no production environment/database has been changed as part of creating this Phase 1 handbook.

## Active objective at handoff
**Objective:** Establish a repository-backed Persistent Engineering Operating System (Phase 1: durable project memory and task handoff).

**Phase 1 acceptance:** charter, architecture map, decision log, known-issue register, acceptance gates, active-work handoff, and this status record exist in the repository; content is grounded in inspected files and labels uncertainty.

**Current user-facing product work to resume after Phase 1:** Beyond Earth native inline whiteboard pilot, PR #59. Do not infer that it is ready to merge or release from the database pilot alone.

## Important constraints
- No PR merges without explicit founder approval.
- No production deployments or production database changes without explicit founder approval.
- Preserve existing open PRs and unrelated branches.
- Never expose API keys, tokens, student data, or other secrets in documentation, logs, or commits.
- Read `AGENTS.md` and `TESTING_GUIDANCE.md` before code/test/build/deploy actions. Read `.github/testing-regression-checklist.md` and `docs/TESTING_ERRORS.md` before relevant tutor/UI tests.

## Resume procedure
1. Re-fetch main and the active branch heads.
2. Re-fetch the active PR and latest CI runs/artifacts for its exact head SHA.
3. Read the mandatory guidance and relevant incident records.
4. Compare actual state with this snapshot; update this file with dated evidence.
5. Continue the one active objective in `.engineering/tasks/active-work.md`.
