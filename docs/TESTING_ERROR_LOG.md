# PadippuPal Testing Error Log

**Purpose:** Durable record of every meaningful testing mistake, failed verification, test-harness defect, and regression discovered during development. This log is append-only in spirit: never delete a resolved entry; update its status while preserving the lesson.

## Mandatory use

Before every test run, read this document and `.github/testing-regression-checklist.md`. For the planned run, identify applicable entries and confirm their prevention checks are present. If a failure occurs, add an entry here **before rerunning**. Never repeat an unchanged failed run unless it is explicitly a diagnostic reproduction with a stated question. Tie every verification to the exact commit SHA.

Each entry should record:
- Date and affected branch/commit
- Test/check and expected versus actual result
- Evidence (workflow/run/job/log/screenshot)
- Root cause and confidence (confirmed, hypothesis, unknown)
- Correction made (or next diagnostic action)
- Prevention rule and regression coverage
- Status: OPEN, FIXED—AWAITING VERIFICATION, or VERIFIED FIX

## Error history

### TE-001 — All 1s validator accepted generic unrelated speech

- **Date discovered:** 2026-10-23
- **Affected branch:** `fix/live-lesson-coordinated-flow`
- **Known commit at discovery:** `dcc70153daf0123841ff51007272b70d6537243e`
- **Check:** Curriculum Engine Tests, run [39880904470](https://github.com/Prav1525/Padippupal/actions/runs/39880904470)
- **Expected:** A generic unrelated later segment causes the lesson plan to be rejected and the single allowed retry to occur; valid supporting explanations remain allowed.
- **Actual:** `test_lesson_plan_retries_when_a_later_segment_is_generic_not_all_ones` failed because only one generation request occurred instead of two. Test summary: 1 failed, 53 passed.
- **Evidence:** Job `120177759315`; failing assertion expected `len(requests) == 2`, actual was 1. Android APK build run [39880904476](https://github.com/Prav1525/Padippupal/actions/runs/39880904476) passed on that head, but this does not override the backend failure.
- **Root cause:** **Confirmed from code/test evidence.** A change broadened All 1s validation from per-segment relevance to lesson-level relevance, allowing one relevant segment to mask a later generic segment. A related Android guard was loosened similarly, creating cross-layer inconsistency.
- **Correction required:** Restore per-segment validation in backend and Android; explicitly allow genuine concept-supporting explanations such as “A pattern can repeat without increasing or decreasing”; still reject generic unrelated sentences such as “Mathematics is the search for patterns and explanations.” Require at least one topic-relevant spoken segment and retain forbidden-content checks.
- **Prevention rule:** Any lesson-level semantic guard must check every segment independently. One matching segment must never mask unrelated speech, captions, or visuals in another segment. Backend and Android acceptance rules must stay aligned.
- **Required regression coverage before rerun:** Keep the generic-later-segment retry test; keep the valid supporting-explanation test; keep off-topic-segment rejection and all-neutral rejection tests; add/retain assertions that visual labels cannot make unrelated speech pass. Run backend curriculum tests, Android build, and UI smoke against the same latest commit.
- **Status:** OPEN — fix and fresh verification not yet confirmed when this entry was written.

## Future entries

Append the next ID (TE-002, TE-003, …). Do not overwrite historical entries. If a failure reveals multiple independent mistakes, create separate entries and cross-reference them.
