# Engineering acceptance criteria

A task is complete only when every applicable layer is explicitly classified. Not every task needs every test layer; omitted layers must be justified.

## Status vocabulary
- **Implemented:** code/config/docs changed on a named branch/commit.
- **Tested:** named checks ran; exact result and evidence are recorded.
- **Verified:** relevant acceptance criteria passed on the same tested commit, including runtime checks where required.
- **Deployed:** intended environment is confirmed to run the named commit/version.
- **Learner-ready:** child-facing experience passed content, accessibility/usability, API, and target-device acceptance.
- **Blocked:** required evidence, environment, permission, or dependency is unavailable.
- **Unverified:** plausible implementation exists but required proof has not been collected.

## Universal definition of done
- Scope and non-goals are explicit.
- Existing architecture, prior incidents, and affected interfaces were inspected.
- Root cause is labelled confirmed/probable/unknown where a defect is involved.
- Changes are isolated and avoid unrelated files/features.
- Regression tests protect the behavior and do not weaken valid assertions.
- Relevant tests ran on the exact final commit.
- Logs/artifacts/screenshots are linked and inspected when applicable.
- Documentation and active-work handoff are updated.
- Remaining risks and rollback considerations are stated.
- PR merge, production write, deploy, or release waits for explicit founder approval.

## Backend/API changes
- Request/response schema and compatibility are verified.
- Authorization and secret handling are reviewed.
- Source/profile scoping and safe failure behavior are tested.
- Persistence, idempotency, migrations, and rollback are checked where relevant.
- Tests cover success, invalid input, missing evidence, and cross-profile/chapter isolation.

## Synthesis/curriculum changes
- Board, class, subject, medium, edition/year, chapter, and topic are resolved unambiguously.
- Claims retain source chunk/page provenance.
- Textbook-backed claims are separated from examples and generated practice.
- Content is age-appropriate, accurate, complete, and reviewed against authorized sources.
- Tanglish is natural and preserves subject terminology.
- Unsupported or ambiguous source facts fail safely.

## Visual-engine changes
- Visual type is selected for the concept, not merely decorated from a title.
- Objects, labels, relationships, and reveal order are grounded in the corresponding teaching step.
- Visual asset is keyed to the exact lesson/topic/profile and source references.
- No stale or cross-topic asset can be attached.
- Visual is readable at phone width, accessible, and inline with tutor content.
- Narration synchronization uses real playback events/timestamps; no fabricated word timing.
- For the Beyond Earth native whiteboard pilot, obey the explicit PR scope: native Compose Canvas, no SVG, chapter-scoped changes, progressive reveal, and no production promotion without approval.

## Android/tutor changes
- Navigation, state restoration, language selection, playback, follow-up chat, error handling, and relevant screen-size/keyboard behavior are tested.
- A successful build is not treated as runtime proof.
- Emulator/target-phone screenshots and logs are inspected for UI acceptance.
- Natural voice and fallback behavior are tested where speech changes.

## Release criteria
- Required CI checks pass on the exact proposed head.
- Backend and deployed API checks pass where relevant.
- APK/package corresponds to the tested commit and intended variant.
- Emulator/target-phone journey passes.
- Content and source-rights gates pass.
- Founder explicitly approves merge/deploy/production data changes.
