# Engineering Operating System — Acceptance Criteria

## Phase 1 — Persistent project memory
- [x] Inspect repository identity, default branch and current main commit.
- [x] Inspect existing agent instructions, testing guidance, README, repository tree, open PR and recent CI runs.
- [x] Preserve existing rules rather than creating a conflicting parallel protocol.
- [x] Create a project charter and evidence-labelled architecture/system inventory.
- [x] Record current PR/CI state, failure evidence and next action.
- [x] Verify required documents by GitHub branch read-back and expose the work through a reviewable PR (#60).
- [ ] Obtain passing CI/documentation checks on PR #60 (pending).
- [ ] Complete source-level call graphs and database/API contracts (deferred; only add when evidence-backed).

## Phase 2 — Workflow enforcement (future)
- [ ] Add/verify PR template fields for scope, acceptance criteria, test evidence, data migrations, rollback and release authorization.
- [ ] Add a lightweight documentation-integrity check for required project records and status vocabulary.
- [ ] Ensure CI never treats APK compilation as emulator acceptance.
- [ ] Ensure production deployment and PR merge are not automated without explicit owner authorization.
- [ ] Add automated links from PR/run to the tested commit and release evidence.

## Phase 3 — Automated status and architecture reporting (future)
- [ ] Generate status snapshots from GitHub PRs, branches and workflow runs.
- [ ] Add source-backed API/module/dependency maps.
- [ ] Add deployment/database environment inventory without exposing secrets.
- [ ] Add regression and learning-quality metrics where reliable measurements exist.

## Phase 1 done definition
Phase 1 is complete when all required documents are present in a reviewable branch/PR, current facts are traceable to source evidence, existing guidance is preserved, no production resources are changed, and the PR is not merged without explicit owner approval. CI review remains a pending validation item.
