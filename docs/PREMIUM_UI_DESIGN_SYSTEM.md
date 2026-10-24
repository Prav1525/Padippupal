# PadippuPal Premium UI Design System

## Direction
Premium and modern first; warm, welcoming and child-friendly second. The product should feel like a calm personal learning companion, not a game or an administrative dashboard.

## Core palette
- Midnight navy: `#0F2742` — primary text, strong surfaces and brand anchor.
- Teal: `#14B8A6` — primary actions, active navigation and tutor identity.
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
- Progress: meaningful progress summaries without gamified clutter.
- Profile/settings: simple grouped preferences and clear language/board/medium distinctions.

## Functional guardrails
This design system must not change lesson selection, curriculum grounding, voice provider behavior, playback state, session persistence, progress data, navigation destinations, or API contracts. Visual changes require screenshot review and the repository regression checklist. Do not mark the redesign complete from a successful build alone.

## Implementation plan
1. Establish palette and component tokens.
2. Apply shared styles screen-by-screen while preserving behavior.
3. Review emulator screenshots on a small viewport and verify accessibility/contrast.
4. Run backend contract tests, JVM tests, APK build, smoke helper tests, and emulator flow before merge.
