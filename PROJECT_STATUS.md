# PadippuPal Project Status

**Snapshot date:** 2026-10-30  
**Default branch:** `main`  
**Main commit at inspection:** `407844ea458799eadc99b9af1e7364939902e9dd`  
**Engineering OS branch:** `chore/persistent-engineering-os-phase1`  
**Repository:** https://github.com/Prav1525/Padippupal

> Dated handoff only, not a live dashboard. Re-fetch GitHub, CI and deployed environments before relying on this snapshot.

## Verified repository facts
- Android client: Kotlin + Jetpack Compose.
- Backend: Python FastAPI under `backend/`.
- Tutor UI and inline lesson presentation are primarily in `app/src/main/java/com/padippupal/app/TutorScreen.kt`.
- Existing mandatory engineering rules: `AGENTS.md` and `TESTING_GUIDANCE.md`.
- Existing regression and incident records: `.github/testing-regression-checklist.md`, `docs/TESTING_ERRORS.md`, and `TEST_INVESTIGATION.md`.
- Existing CI workflows include Android build, Android emulator smoke, curriculum-engine tests, deployed API smoke and investigation-guidance validation.
- Product documentation explicitly distinguishes prototype/roadmap capability from verified shipped capability. See `README.md`, `docs/CONCEPT_MASTERY.md`, `docs/LIVE_TEACHING_DESIGN.md`, and `docs/SYNTHESIS_VISUAL_MAPPING.md`.

## Current GitHub snapshot
- `main`: `407844ea458799eadc99b9af1e7364939902e9dd`.
- Beyond Earth PR #59 is open and unmerged: https://github.com/Prav1525/Padippupal/pull/59
- PR #59 head at inspection: `0383b1fe9690ff3c97dcc901c64710be04ddba14`.
- Latest runs for that head:
  - [Android APK run 40989118308](https://github.com/Prav1525/Padippupal/actions/runs/40989118308): **PASS**.
  - [Curriculum Engine Tests run 40989118292](https://github.com/Prav1525/Padippupal/actions/runs/40989118292): **PASS**.
  - [Investigation Guidance Gate run 40989118330](https://github.com/Prav1525/Padippupal/actions/runs/40989118330): **PASS**.
  - [Android UI smoke run 40989118437](https://github.com/Prav1525/Padippupal/actions/runs/40989118437): **FAIL** at “Validate smoke-test scripts”; emulator allocation and app navigation were skipped. This is a harness preflight failure, not evidence of app runtime failure or success.
- Latest UI smoke job steps show APK build and fast JVM tests passed before script validation failed.

## Phase 1 — Persistent Engineering Operating System
- **Scope:** repository-backed charter, architecture/system map, decision log, known issues, acceptance criteria, current status and active-work handoff.
- **Implementation branch:** `chore/persistent-engineering-os-phase1`.
- **Base:** `main@407844ea458799eadc99b9af1e7364939902e9dd`.
- **No application source, CI workflow behavior, deployment or production database changes are in scope.**
- **Verification target:** read back every document, validate internal links and inspect branch diff; then open a review PR.
- **Merge:** requires explicit founder approval.

## Priority after Phase 1
Resume Beyond Earth PR #59: inspect the smoke preflight failure, repair the evidenced test harness issue, rerun emulator validation and inspect all eight visuals in the actual tutor UI. Do not treat a successful APK build or database seed as learner-ready proof.

## Approval and safety constraints
- No PR merges without explicit founder approval.
- No production deployment, production database write, destructive action or public release without explicit founder approval.
- Preserve unrelated PRs and branches.
- Never commit API keys, access tokens, production connection strings or private learner data.
- Before code/test/build/deploy actions, read `AGENTS.md` and `TESTING_GUIDANCE.md`; consult relevant incident records and exact current evidence.

## Resume procedure
1. Read `PROJECT_CHARTER.md` and `.engineering/README.md`.
2. Re-fetch main, active branch, PRs and relevant workflow runs.
3. Read mandatory guidance and the relevant known-issue/task record.
4. Reconcile this snapshot against actual state.
5. Continue only the active objective in `.engineering/tasks/active-work.md`.