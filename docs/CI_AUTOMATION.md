# PadippuPal AutoPilot — free-first workflow

## Architecture

- **GitHub Actions** runs repository checks within the account's available free allowance and publishes run summaries with exact tested SHAs and job results.
- **Guide gate** dynamically checks that every Markdown file directly under docs/ is readable and verifies the required project records are present.
- **Durable project history** stays in PROJECT_STATUS.md and docs/TESTING_ERRORS.md; update them in the same repair/change PR. The CI observer does not commit after tests, because that would create a new untested SHA.
- **Deterministic local triage** classifies common runner/network/build/emulator log signatures without an external API.
- **Optional local AI** uses Ollama on the user's own computer. It receives a bounded log excerpt and prints advisory analysis only. It does not edit files, run commands, or merge PRs.
- **Code changes always require review** in a separate PR. This version does not apply model-generated patches.

## Commands

From the repository root:

```bash
python tools/padippupal_autopilot.py check-guides
python tools/padippupal_autopilot.py classify-log path/to/failed-job.log
python tools/padippupal_autopilot.py local-review path/to/failed-job.log
```

The default local model is qwen2.5-coder:7b; override with PADIPPUPAL_LOCAL_MODEL. The default endpoint is http://127.0.0.1:11434; override with OLLAMA_HOST. Install Ollama and pull a compatible model separately. The local model runs on your computer, so no OpenAI API key is required. Hardware performance and model quality vary.

## Safe repair policy

- The current automation does **not automatically edit application code, tests, curriculum, workflow logic, or project requirements**.
- The deterministic classifier reports known signatures only; it never treats a classification as proof of root cause.
- Unknown signatures require manual evidence-based diagnosis.
- Local model output is advice only. Reviewers verify the cause, implement a fix in a separate branch/PR, add regression protection, and update both project records.
- No automatic merge, deployment, release, or secret-bearing model call on untrusted PR code.

## Every change batch

Read AGENTS.md, README.md, PROJECT_STATUS.md, docs/TESTING_ERRORS.md, .github/testing-regression-checklist.md, every docs/*.md, and relevant workflows/scripts from the target branch before editing. Before each test cycle, reread the error log and checklist. A presence check cannot prove a human or agent actually understood each guide.

## Cost and limitations

No paid AI API is required. GitHub Actions usage, storage, and runner minutes are subject to GitHub's current plan limits. Ollama model download and local inference use the user's own disk, memory, electricity, and hardware. This first version records CI outcomes but does not autonomously repair arbitrary failures; use the evidence to prepare a reviewed repair PR.
