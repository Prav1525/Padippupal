# PadippuPal Project Charter

## Product mission
Build a trustworthy, child-centred learning companion that helps school students understand concepts, apply them in unfamiliar situations, identify misconceptions, and create useful revision material. PadippuPal is not merely a chapter summarizer or answer generator.

## Product principles
1. **Learning before content volume:** optimize for demonstrated understanding, not lesson length or number of generated assets.
2. **Curriculum integrity:** ground syllabus-specific claims in approved, edition-matched sources. Distinguish sourced material from generated examples and practice.
3. **Teacher-quality explanations:** use age-appropriate language, small teaching steps, relevant examples, useful visuals and adaptive reteaching.
4. **Bilingual separation:** textbook medium and explanation/app language are separate settings. English/Tanglish preference must not silently change curriculum terminology or facts.
5. **Visuals must teach:** diagrams and animations should explain relationships or processes, be labelled, readable and synchronized with narration where applicable.
6. **Trust over confidence:** when source evidence, runtime behaviour or test evidence is missing, say so.
7. **Safe releases:** production data changes, deployments with production impact and PR merges require the project owner's explicit approval.

## Engineering partnership
The engineering partner is expected to investigate before changing, challenge weak assumptions, prefer small evidence-backed changes, test actual user journeys, maintain durable records and report uncertainty honestly. It must not claim background execution, memory, test success, deployment or release that did not occur.

## Non-negotiable change controls
- Never merge a PR without explicit owner approval.
- Never modify production database data or trigger a production-impacting release without explicit owner approval.
- Keep test/staging and production data clearly distinguished.
- Do not combine unrelated feature work in one PR.
- Preserve existing investigation history; append new evidence rather than rewriting history.

## Status vocabulary
- **IMPLEMENTED:** change exists in the inspected source or target environment.
- **TESTED:** named checks actually ran; report each check independently.
- **DEPLOYED:** the expected commit is verified in the named environment.
- **LEARNER-READY:** relevant end-to-end acceptance checks, including runtime/user experience, passed.
- **UNVERIFIED:** evidence is insufficient.
- **BLOCKED:** a concrete external or technical blocker prevents the next check.

These statuses are not interchangeable.
