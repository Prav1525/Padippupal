# Engineering Rules

These rules extend, and do not replace, the mandatory instructions in `AGENTS.md` and `TESTING_GUIDANCE.md`. In any conflict, follow the stricter requirement and preserve owner constraints.

## Context recovery gate
At the start of a resumed engineering task:
1. Read `PROJECT_CHARTER.md`, `PROJECT_STATUS.md`, `AGENTS.md` and `TESTING_GUIDANCE.md`.
2. Read relevant module documentation, active task notes, decision records and known issues.
3. Inspect live repository state: default branch HEAD, relevant branch/PR head, PR status, latest workflow runs/jobs and changed files.
4. For deployment/data tasks, inspect the actual target environment and identify it explicitly as test/staging/production.
5. Reconcile stale documentation. Actual source, CI and environment evidence take precedence over notes.

## Before-action record
Before each consequential edit, build, test or deployment action, record:
- branch and commit;
- exact requirement/failure and source of evidence;
- root-cause confidence: confirmed, probable or unknown;
- proposed smallest action and rationale;
- checks that will validate it;
- explicit authorization boundary.

Re-open `TESTING_GUIDANCE.md` before every new edit/test/build batch as it requires.

## Implementation discipline
- Inspect existing implementation and reuse its established patterns where sound.
- Avoid speculative rewrites, unrelated cleanup and broad refactors.
- Prefer isolated feature branches and focused PRs.
- Preserve existing test and investigation history.
- Never place credentials, tokens, private keys or production connection strings in repository files.
- Do not use mocks as proof of live integration behaviour.

## Evidence discipline
For each check, record exact workflow/run/job or command, tested commit, result, and what the result does and does not prove. Keep PASS, FAIL, BLOCKED and UNVERIFIED distinct. A green unrelated workflow cannot satisfy a feature's acceptance criteria.

## Owner-controlled operations
Explicit owner approval is required before:
- merging or closing a PR as part of release;
- writing/changing production database data or schema;
- triggering a production-impacting deployment or release;
- deleting production resources/data or rotating production credentials.

Creating a development branch, drafting docs, running read-only inspection and non-production tests are permitted within the requested task scope.

## Session completion
Before handing work back:
1. Update `PROJECT_STATUS.md` and the relevant task/issue record with evidence.
2. Record decisions and unresolved hypotheses.
3. List exact changed files and commit/PR links.
4. State what remains unverified and the next action.
5. Never report the overall feature as complete if a required acceptance layer is still failing or skipped.
