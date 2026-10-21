# PadippuPal test regression checklist

Run this checklist for every tutor-screen change; do not mark the release green from a build-only result.

1. **Backend contract first**: run the curriculum/tutor pytest suite; preserve chapter counts, unique lesson IDs, source references, minimum step counts, and challenge answer/options/hint integrity.
2. **Chapter 1 curriculum coverage**: verify every required concept label exists and lesson text explicitly contains counting, odd/even, triangular, square, cube, Virahanka, powers of 2/3, hexagonal, regular polygon, complete graph, stacked squares/triangles, Koch snowflake and the 192-edge stage.
3. **API against deployed service**: confirm CBSE Class 6 Mathematics outline returns 10 chapters, Chapter 1 is Patterns in Mathematics, and its topic list is non-empty. Keep API success separate from UI success.
4. **Fast Android checks before emulator**: run Kotlin/JVM tests, assemble the debug APK, and compile/run smoke-test helper unit tests before allocating the emulator.
5. **UI flow, not just screen presence**: verify profile -> tutor -> feedback action -> settings -> Mathematics -> Chapter 1 -> select a numbered concept -> lesson actually opens -> spoken caption visible -> highlight appears in captured frames.
6. **Accessibility selector resilience**: Android XML may omit clickable/enabled flags for Compose rows. Select only visible numbered rows with valid non-zero bounds; prefer clickable nodes when present, but verify the tap by observing the next state. Never interpret a visible option as proof selection succeeded.
7. **Failure diagnosis**: preserve XML/screenshots/logs; classify failure as app behavior, test harness, API/data, emulator/ADB, or timing. Fix the cause before rerun; do not simply loosen assertions or skip the failed step.
8. **Bounded waits**: every emulator/ADB action has a timeout; detect emulator/ADB unavailability and fail with a diagnostic rather than waiting indefinitely.
9. **Release gate**: report each layer independently (backend tests, deployed API, JVM tests, APK build, emulator flow, inline highlight). Any required layer failing means overall status is not passed.
