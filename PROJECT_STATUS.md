# PadippuPal — Verified Project Status

> Last reconciled: 2026-10-30 (UTC). This file is a point-in-time snapshot, not a live dashboard. Reconcile GitHub, CI, deployed services and database state before relying on it in a later session.

## Repository baseline
- Repository: `Prav1525/Padippupal`
- Default branch: `main`
- Verified main HEAD: `407844ea458799eadc99b9af1e7364939902e9dd`
- Latest main commit message: `Render Beyond Earth astronomy visuals inline in the tutor (#58)`
- Android app source: `app/src/main/java/com/padippupal/app/`
- Backend source: `backend/`
- Existing contributor rules: `AGENTS.md`
- Detailed mandatory test/build rules: `TESTING_GUIDANCE.md`

## Active feature work at reconciliation
### PR #59 — Beyond Earth native labelled whiteboard visuals
- URL: https://github.com/Prav1525/Padippupal/pull/59
- State: OPEN; not merged.
- Head branch: `feature/beyond-earth-whiteboard-native`
- Head SHA observed: `0383b1fe9690ff3c97dcc901c64710be04ddba14`
- Base: `main` at `407844ea458799eadc99b9af1e7364939902e9dd`
- Scope described by PR: chapter-scoped native Jetpack Compose Canvas scenes for Class 6 Science, Beyond Earth; no SVG; no other chapters changed.
- Test DB branch previously documented in PR body as containing 8 visual assets and an 8-step teaching sequence; production DB described as unchanged. Recheck the database before relying on this later.

### Latest observed CI for PR #59 head
| Workflow | Run | Outcome | What it proves |
|---|---:|---|---|
| Android APK | [40989118308](https://github.com/Prav1525/Padippupal/actions/runs/40989118308) | PASS | APK build workflow succeeded for the PR head SHA |
| Curriculum Engine Tests | [40989118292](https://github.com/Prav1525/Padippupal/actions/runs/40989118292) | PASS | Curriculum test workflow succeeded |
| Investigation Guidance Gate | [40989118330](https://github.com/Prav1525/Padippupal/actions/runs/40989118330) | PASS | Guidance gate succeeded |
| Android UI smoke | [40989118437](https://github.com/Prav1525/Padippupal/actions/runs/40989118437) | FAIL | Smoke-script validation failed; emulator E2E was skipped |

The failing smoke job was `emulator-smoke (35)`, job ID `123846977986`. Its failing test was `SynthesisInlineVisualContractTests.test_live_smoke_accepts_inline_visual_but_still_rejects_separate_visual_overlay`. The helper test expected the literal source fragment `"pattern of stars" in joined`, but the smoke script had a semantically equivalent check using `any(term in joined for term in ("pattern of stars", "stars in the night sky", "ursa major"))`. The log showed JVM unit tests and APK build succeeded, script validation failed, and Android emulator E2E was skipped. This is a test-harness contract mismatch, not evidence that the app visual itself failed. Do not infer the actual runtime visual passed from this run.

## Release and data safety
- No PR merge or production release is authorized by this status file.
- Production database state must be read back from the live production connection before any future claim about its contents.
- A successful APK build does not establish installation, runtime correctness or learner readiness.

## Next priority
Resolve the smoke-helper contract mismatch on the feature branch, rerun script validation, then obtain actual emulator E2E evidence and inspect the resulting screenshots/artifacts. Keep PR #59 open until its acceptance criteria are met and the owner explicitly approves a merge.
