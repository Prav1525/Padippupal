# PadippuPal CI automation and safe repair loop

## What runs automatically

1. The existing Android APK, Android UI smoke, and curriculum-engine workflows run their configured checks.
2. After each completed run, the CI triage workflow records the workflow name, conclusion, exact commit SHA, job results, run URL, and timestamp in PROJECT_STATUS.md on the same-repository branch when write access is available.
3. On a failed run, it appends an open TE entry to docs/TESTING_ERRORS.md and opens a GitHub issue linking to the run. The root cause is explicitly marked undiagnosed until logs/artifacts are inspected. It never invents a diagnosis.
4. A separate AI-assisted repair workflow is enabled only for failures on the trusted main branch. If OPENAI_API_KEY is configured, Codex reads the project guides and failure logs, may propose a narrow fix with regression protection, and opens a separate PR. Its resulting PR must pass normal CI and human review.
5. PR/fork failures are recorded, but the secret-bearing AI repair worker does not run on them. This avoids exposing an API key to code from an untrusted PR.
6. The change-governance workflow requires code/automation PRs to update both PROJECT_STATUS.md and docs/TESTING_ERRORS.md. AGENTS.md and the PR template require a fresh review of every Markdown guide under docs/ before each code-change batch.

## Required one-time setup for AI repair

In GitHub, open **Settings → Secrets and variables → Actions → New repository secret** and create:

- Name: OPENAI_API_KEY
- Value: an OpenAI API key created by the project owner

The secret is optional for the basic CI recordkeeping. Without it, CI history, failure issues, and testing-error entries still run; the AI repair step is skipped. API usage may incur charges under the key owner's account. Never put the key in source code, workflow YAML literals, app resources, or logs.

## Safety boundaries and limitations

- No workflow merges a PR, deploys a service, or publishes a release as part of repair.
- The AI repair worker only runs against the trusted main branch. It does not run with secrets on PR branches or forks.
- The generated fix is a proposal, not a verified fix. Its new PR must pass all required checks; UI screenshots still require inspection from the exact tested SHA.
- CI metadata is automatically recorded, but a failure's actual root cause still needs evidence-based diagnosis. The first TE entry is deliberately marked Open until confirmed and fixed.
- For a fork PR, automation cannot write to that fork's branch; the run issue is the durable fallback.
- GitHub may not run workflows triggered by pushes made with GITHUB_TOKEN. The recordkeeping workflow therefore writes records directly and does not rely on those writes to launch another test run.
- The workflow-run event only records the configured workflows. Add any new required CI workflow name to .github/workflows/failure-triage.yml and .github/workflows/ai-autofix-main.yml.
