# PadippuPal Tutor Teaching Quality Test Plan

Scope: Class 6 CBSE/NCERT Mathematics, Chapter 1 — *Patterns in Mathematics*. This plan evaluates teaching quality and the tutor screen, not merely whether the app opens.

## Automated emulator acceptance tests

These run in `.github/scripts/android-ui-smoke.sh` against the built debug APK:

1. Select a Class 6 CBSE learner profile.
2. Open Mathematics and verify Chapter 1 is *Patterns in Mathematics*.
3. Select the first available concept and start a live lesson.
4. Verify the live lesson contains readable text, segment progress, and inline spoken-word highlighting.
5. Wait up to 60 seconds for a live “Quick check” checkpoint; fail with `LIVE_CHECKPOINT_MISSING` if none appears.
6. Verify checkpoint prompt and the **I understand**, **Explain again**, and **I have a question** controls.
7. Tap **Explain again** and verify the tutor returns to “Was that explanation clearer?”.
8. Tap **I understand** and verify the tutor acknowledges the learner and advances beyond the checkpoint.
9. Stop the lesson and verify navigation back to Home.
10. Collect screenshot, UI-tree, logcat and ANR diagnostics on failure.

## Teaching-quality test cases

| ID | Priority | Test / setup | Expected result | Evidence |
|---|---|---|---|---|
| TQ-01 | P0 | Start Chapter 1 lesson with no previous chat | Opens with the selected chapter/concept and a child-friendly overview; does not begin with an unrelated question | Transcript + screenshot |
| TQ-02 | P0 | Teach the concept “Patterns” | Uses the sequence: familiar concrete example → invite observation/prediction → explain the rule → recap | Ordered lesson segments |
| TQ-03 | P0 | Inspect every segment's source IDs | Every factual teaching segment cites retrieved curriculum chunks; no fabricated IDs or unsupported claims | Backend validation result |
| TQ-04 | P0 | Reach the first checkpoint | Speech pauses; checkpoint is visible and remains on screen without being hidden by scrolling or keyboard | UI tree + screen recording |
| TQ-05 | P0 | Tap **Explain again** at checkpoint | Explains the same idea more simply with a concrete example, then asks whether it is clearer | Transcript + second checkpoint |
| TQ-06 | P0 | Tap **I understand** after checkpoint | Acknowledges the learner and advances to the next segment exactly once | Segment index/status before and after |
| TQ-07 | P0 | Tap **I have a question** | Lesson stops safely; question composer is prefilled with the current checkpoint context; no stale speech continues | UI tree + status |
| TQ-08 | P0 | Observe visual while tutor speaks | Visual represents the same concept, numbers, shapes and step mentioned in current spoken segment | Paired audio transcript + screenshots |
| TQ-09 | P0 | Capture screen throughout spoken segment | Highlighted word appears inside the displayed lesson text, follows speech timing, and does not appear in a separate duplicate passage | Frame sequence |
| TQ-10 | P1 | Use a long segment on a small screen | Caption scroll follows the active spoken word; fixed checkpoint and composer remain usable | Frame sequence + bounds |
| TQ-11 | P1 | Let a lesson continue across several segments | One idea per segment; concise sentences; no duplicated paragraphs or sudden jump to an advanced example | Transcript review |
| TQ-12 | P1 | Select each available Chapter 1 concept | Concept list follows curriculum order and labels concepts clearly; no arbitrary free-text topic is required | Chapter/concept menu dump |
| TQ-13 | P1 | Compare spoken content with source chunks | Examples stay inside the selected syllabus and do not drift into another class/chapter | Source-to-segment review |
| TQ-14 | P1 | Reopen Tutor after navigating away | Current chapter/concept and conversation context are preserved as designed; no accidental restart from an unrelated opening | Navigation sequence |
| TQ-15 | P1 | Run with network/API unavailable | Shows a recoverable explanation/error state, does not leave an endless spinner, and preserves typed input | Network-disabled emulator run |
| TQ-16 | P1 | TTS is slow or fails to initialize | Visible text remains readable; progress/status recovers; no permanent “speaking” state | Logcat + UI tree |
| TQ-17 | P1 | Deny microphone permission and tap voice question | Clear permission/fallback message; text entry remains available | UI tree |
| TQ-18 | P1 | Rotate or recreate activity during lesson (if supported) | No duplicate speech, lost selected chapter, or stuck checkpoint | Lifecycle test + logs |
| TQ-19 | P2 | Review teacher voice pacing | Short pauses after key ideas/questions; speech is not rushed; text/highlight and audio remain synchronized | Audio recording + timing notes |
| TQ-20 | P2 | Check visual panel and caption at different font/display sizes | No clipped labels, overlapping passage, inaccessible buttons, or horizontal overflow | Screenshots at two display scales |

## Important coverage gap to keep visible

The current live checkpoint offers **I understand**, **Explain again**, and **I have a question**. It does not yet collect a student's actual answer to a checkpoint question and evaluate whether that answer is correct, incomplete, or mistaken. Therefore, adaptive feedback to a wrong answer is **not testable as a pass yet**. It needs a student-answer input/voice-answer flow and backend behavior before that acceptance test can be automated.

## Pass criteria

- All P0 automated tests pass on the same commit as the APK.
- No ungrounded curriculum claims or mismatched visual actions.
- No checkpoint, animation, or speech deadlock; all waits have hard timeouts and diagnostics.
- Manual audio/pedagogy review passes before claiming teacher-quality behavior. A successful build or UI smoke test alone is not evidence that the teaching is pedagogically correct.
