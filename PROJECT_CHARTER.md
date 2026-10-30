# PadippuPal Project Charter

**Status:** Living product charter  
**Last reconciled:** 2026-10-30  
**Repository:** https://github.com/Prav1525/Padippupal

## Mission
Build a trustworthy, child-friendly learning companion that helps school students understand concepts, apply them in unfamiliar situations, identify misconceptions, and create useful revision material. PadippuPal must teach understanding, not merely summarize textbooks or reproduce exercise answers.

## Product principles
1. **Learning before engagement:** every explanation, visual, interaction, and question must serve comprehension.
2. **Curriculum integrity:** distinguish approved textbook evidence, curriculum metadata, AI-generated explanations, and illustrative examples. Never invent official sources, page numbers, or exam predictions.
3. **Age-appropriate teaching:** adapt vocabulary, depth, examples, pace, and scaffolding to the learner's board, class, medium, and demonstrated understanding.
4. **Language separation:** textbook medium (Tamil/English) is distinct from explanation language (English/Tanglish/Tamil where supported).
5. **Visuals that teach:** choose diagrams, process flows, comparisons, worked steps, or illustrations based on the concept. Keep relevant visuals in the tutor's normal inline flow, not detached overlays.
6. **Honest AI:** fail safely when evidence is missing; do not imply that an answer is textbook-grounded when it is not.
7. **Child privacy and safety:** minimize student data, keep credentials server-side, and avoid unnecessary personal information in prompts/logs.
8. **Reliability over speed:** verify actual learner journeys, not just compilation or mocked tests.

## Intended learner journey
A learner selects or identifies a board/class/subject/chapter, receives a structured concept sequence, learns through clear explanations and useful visuals, checks understanding, receives misconception-aware feedback and reteaching, and can create revision material from reviewed content.

## Engineering partnership contract
The engineering partner is expected to:
- recover context from this repository before acting;
- inspect code, data contracts, CI, PRs, deployments, and prior incident records relevant to the task;
- state evidence separately from hypotheses;
- challenge weak product or technical assumptions and recommend better alternatives;
- make the smallest justified change that solves the confirmed problem;
- test at the narrowest layer first, then run relevant regression and end-to-end checks;
- update durable records with decisions, evidence, unresolved risks, and next steps;
- never claim implementation, testing, deployment, or learner readiness without evidence.

The founder owns product direction and must explicitly approve **all PR merges and production changes**, including production database writes, deployments, releases, and destructive operations. A request to build or test is not permission to merge or deploy.

## Product scope and truth boundaries
The README and domain documents describe both implemented prototype capabilities and planned capabilities. Do not treat roadmap statements as shipped features. Verify the current code and deployed environment before making product availability claims.

## Source-of-truth hierarchy
When records disagree, use this order:
1. Actual repository state, exact commit, CI run/artifacts, and verified deployed environment.
2. Current code, schemas, migrations, and explicit API contracts.
3. Current engineering and acceptance documents.
4. Prior conversation summaries and informal notes.

Record meaningful discrepancies rather than silently rewriting history.
