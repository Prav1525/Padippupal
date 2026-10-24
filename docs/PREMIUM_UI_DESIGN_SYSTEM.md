# PadippuPal Premium UI Design System

## Direction
Premium and modern first; warm, welcoming and child-friendly second. The product should feel like a calm personal learning companion, not a game or an administrative dashboard.

## Core palette
- Midnight navy: `#0F2742` — primary text, strong surfaces and brand anchor.
- Accessible teal: `#0F766E` — primary actions, active navigation and tutor identity.
- Soft mint: `#D8F5F0` — subtle selected states and supportive surfaces.
- Page background: `#F7FAFC` — quiet, low-glare neutral.
- Secondary text: `#526477` — readable supporting copy.
- Indigo: `#6366F1` — limited secondary emphasis, never competing with teal.
- Warm highlight: `#F4C96B` — sparing encouragement and progress accents.
- Soft peach: `#FFF0E5`; pale lilac: `#EEF2FF` — optional low-intensity category surfaces.

## Visual rules
1. Use neutral page backgrounds and white cards; avoid rainbow-heavy screens.
2. Teal is the primary action color. Navy establishes hierarchy and brand confidence.
3. Use one dominant action per screen and consistent component shapes.
4. Keep typography sans-serif, readable, and consistent. Use clear heading/body hierarchy.
5. Keep whitespace intentional; align cards, headings, and actions to a common spacing rhythm.
6. Use icons consistently and always provide meaningful content descriptions for interactive controls.
7. Prioritize contrast, larger tap targets, and readable English/Tamil/Tanglish content on small Android devices.
8. Dark mode should use navy surfaces and carefully checked contrast, not simply invert every color.

## Screen hierarchy
- Home: greeting, one Continue Learning action, subject shortcuts, a compact progress summary.
- Learn/subjects: consistent subject rows/cards with restrained category accents.
- Chapter/lesson lists: clear hierarchy, completion states, and one obvious next action.
- Tutor: uninterrupted explanation, readable captions, source-aware examples, accessible playback controls, and a quiet question composer.
- Diary scan: a clear camera/gallery entry point, capture preview, retake/crop controls, OCR text review, and an explicit confirm/edit step before detected homework is saved. Handle blurry or unreadable pages with a helpful retry state; do not silently invent missing text.
- Exam question bank: browse by class/grade, subject, chapter/topic, question type, and difficulty where data supports it; support practice mode and exam-paper assembly. Keep answers/solutions distinct from the student question view.
- Printable papers and parent answer keys: allow a generated paper and its answer key to be reviewed separately before printing/exporting. Label generated material honestly; never imply it is an official board paper unless its provenance is verified.
- Progress: meaningful progress summaries without gamified clutter.
- Profile/settings: simple grouped preferences and clear language/board/medium distinctions.

## Feature guardrails
### Diary scanning and homework identification
- Scan a diary/homework page using camera or an existing image.
- Extract text with OCR, preserve the captured image for checking, and show detected homework in an editable review screen before saving.
- Let the learner/parent correct OCR mistakes and confirm class/subject/date/task details when those are available.
- Distinguish low-confidence or unreadable text from confirmed homework; never fabricate a task or claim OCR accuracy without validation.
- Keep image/text handling private and disclose any upload or cloud processing before it happens.

### Exam question bank
- Organize available questions by grade/class, subject, chapter/topic, format, and difficulty where metadata exists.
- Provide practice questions with feedback and answers/solutions, plus a separate exam-paper builder with configurable selection/count and marks when supported by the question data.
- Provide printable question papers and a separate parent/teacher answer key.
- Track question source/provenance and avoid presenting generated or unverified questions as official past-board questions.
- Test that selected filters, question counts, marks, answer-key mapping, and print layout remain correct.

## Functional guardrails
This design system must not change lesson selection, curriculum grounding, voice provider behavior, playback state, session persistence, progress data, navigation destinations, or API contracts. Diary scanning and question-bank features are required product scope, but this design document alone does not mean their end-to-end implementation is complete. Visual changes require screenshot review and the repository regression checklist. Do not mark the redesign complete from a successful build alone.

## Implementation plan
1. Establish palette and component tokens.
2. Apply shared styles screen-by-screen while preserving behavior.
3. Implement/review diary scan OCR and homework confirmation flow.
4. Implement/review question bank filters, practice, paper generation, answer keys, and print/export.
5. Review emulator screenshots on a small viewport and verify accessibility/contrast.
6. Run backend contract tests, JVM tests, APK build, smoke helper tests, feature-specific tests, and emulator flow before merge.
