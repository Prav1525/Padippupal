# PadippuPal Decision Log

Record durable product and architecture choices with date, rationale, and consequences. Do not treat an assistant suggestion as an accepted user decision unless the user approved it.

## D-001 — Curriculum-grounded tutor content

- **Status:** Accepted.
- **Decision:** Teach from the approved curriculum/textbook content held by the app/backend. Do not silently substitute unrelated topics or arbitrary web content when the selected approved source is missing.
- **Reason:** Correctness and class/board alignment are core requirements.
- **Consequence:** Topic resolution must be explicit; missing matches should fail closed instead of falling back to a chapter-wide or unrelated lesson.

## D-002 — Live animation, not video-first teaching

- **Status:** Accepted.
- **Decision:** Use live/movable in-app concept animations synchronized with teacher narration and highlighted words; not video clips, static images, or unnecessary interactive activities as substitutes.
- **Reason:** Visuals should directly reinforce the concept being explained.
- **Consequence:** The narration, selected topic, animation/action, inline highlighting, and checkpoint need a shared segment identity and coordinated state.

## D-003 — Teacher-like segmented lesson flow

- **Status:** Accepted.
- **Decision:** Start with key concepts and a simple overview, explain in short segments with examples/visuals, then pause to ask whether the student understands. Offer explain-again and ask-a-question paths.
- **Reason:** Support short attention spans and meaningful comprehension checks.
- **Consequence:** Continuation must be gated by student response; avoid one long generated passage and unrelated activity screens.

## D-004 — Keep teaching screen focused and usable

- **Status:** Accepted.
- **Decision:** Choose subject/topic before entering the teaching screen so the lesson screen is devoted to teaching; use available screen space effectively; show the understanding controls in the lower part of the screen.
- **Reason:** The teaching screen should prioritize lesson content and avoid wasted space or duplicate overlays.
- **Consequence:** Regression tests should cover screen layout, inline highlighting, scrolling, and checkpoint placement.

## D-005 — Development process is evidence-led

- **Status:** Accepted as the working protocol; repository enforcement begins with the protocol PR.
- **Decision:** Diagnose root cause, define acceptance criteria before implementation, protect regressions, and distinguish code/build/unit/integration/emulator verification.
- **Reason:** Repeated symptom patches and unsupported completion claims waste time and cause regressions.
- **Consequence:** Follow `DEVELOPMENT_PROTOCOL.md`; maintain `PROJECT_STATE.md` and `docs/REGRESSION_CHECKLIST.md` on each task.
