# PadippuPal Concept Mastery Engine

## Product requirement

PadippuPal must teach understanding, not only reproduce textbook summaries or end-of-chapter answers. Exams can assess concepts using unfamiliar wording, scenarios, diagrams, reasoning, and applications. Concept mastery is a core learning flow, not an optional add-on.

## Inputs used to personalize a lesson

Every lesson request should carry:
- Student profile: class/standard, board, medium of instruction, preferred app language (English or Tanglish), and learning history.
- Source identity: textbook/curriculum version, term where applicable, subject, chapter, topic, page/section references when available.
- Learning intent: first-time learning, homework help, revision, or exam preparation.
- Evidence of understanding: answers to diagnostic and practice questions, recurring mistakes, and requested level of help.

Do not treat all students alike. Standard and curriculum determine expected depth, vocabulary, mathematical prerequisites, diagram complexity, examples, and answer length. Performance data should tune pacing and scaffolding without silently changing the syllabus level.

## Chapter analysis pipeline

1. Resolve the exact curriculum using board + standard + subject + term (if applicable) + textbook edition + chapter. If ambiguous, ask the student to choose; never guess silently.
2. Retrieve relevant saved library sections and record provenance for every source-backed claim.
3. Build a chapter concept map: core concepts, sub-concepts, definitions, principles, cause/effect, relationships, processes, formulas, diagrams, examples, prerequisites, misconceptions, and textbook exercises.
4. Rank concepts for learning priority using syllabus emphasis, recurrence in supplied/approved past papers when available, foundational importance, teacher/diary cues, and the student's weak areas. Label priority as a reasoned estimate, never a guarantee of exam appearance.
5. Generate a lesson sequence from foundational ideas to applications. Match all content to the student's standard and medium.
6. Assess understanding with varied questions, inspect mistakes, reteach weak concepts in a different way, and re-test.
7. Generate a print-ready A4 revision pack from the same reviewed lesson and question set.

## Required teaching experience for each selected chapter

- Chapter overview and learning goals.
- Interactive concept map / chapter roadmap.
- Small, ordered lessons with simple explanation and a clear "why this matters".
- Visuals chosen to fit the concept: labelled diagrams, process flowcharts, comparisons, timelines, worked steps, tables, or generated illustrations. Avoid decorative visuals that do not teach.
- Familiar real-life examples and, where useful, counterexamples.
- "Explain it another way" support.
- Key terms, definitions, formulas, and common misconceptions.
- Checkpoint questions after each concept, with feedback that explains why an answer is right or wrong.
- Chapter-level practice with difficulty progression.
- Printable PDF with lesson notes, useful visuals, key points, textbook-style questions, novel concept questions, answer key, and self-check checklist.

## Question coverage beyond the textbook

Create a balanced bank that covers:
- Recall and terminology
- Understanding in the student's own words
- Explain why / give reasons
- Compare, classify, and distinguish
- Cause-and-effect and predict what happens if
- Apply a concept to a new everyday scenario
- Interpret a diagram, table, graph, map, experiment, or data set when relevant
- Multi-step reasoning and problem solving
- Find and correct a misconception or incorrect solution
- Exam-style short and extended responses using the expected answer structure

Questions must be new but remain grounded in concepts supported by the chosen syllabus. Do not imply that generated questions are leaked, certain, or guaranteed to appear in exams. Where official sample papers or past papers are available and licensed for use, use them as evidence and label their provenance.

## Standard-aware teaching policy

- Primary classes: concrete familiar examples, short sentences, limited new terms at once, simple labelled visuals, and one reasoning step at a time.
- Middle school: connect concrete examples to formal terms, show relationships and processes, and introduce multi-step explanations gradually.
- Secondary classes: precise subject vocabulary, deeper causal reasoning, data/diagram interpretation, multi-step application, and exam-appropriate answer structure.
- Higher secondary: greater abstraction and prerequisite linking, formal derivations or domain methods where appropriate, and more demanding multi-step application.

These are broad defaults, not rigid assumptions. Always follow the student's actual curriculum and adjust scaffolding based on demonstrated understanding. Do not lower the academic standard just because a student is struggling; explain more clearly and build prerequisites.

## Language rules

The app interface language (English or Tanglish) is distinct from the textbook medium (Tamil or English). Preserve required textbook terminology and provide a short equivalent/explanation when helpful. Tanglish should be natural Tamil written in Latin characters, not random English with Tamil words inserted. Let students switch explanation language without changing the curriculum or answer correctness.

## Accuracy, trust, and safety

- Prefer approved textbook/library sources for syllabus-specific facts.
- Track source references internally and show textbook/page references where available.
- Distinguish source-backed facts from additional illustrative examples and AI-generated practice.
- Never invent official syllabus content, page numbers, marking schemes, or exam predictions.
- If library coverage is missing or conflicting, say so and ask for the missing textbook/page instead of presenting guesses as official.
- Ensure generated diagrams and PDFs are readable, age-appropriate, and suitable for printing.
- Protect student profile, diary images, learning history, and generated work.

## Suggested release sequence

1. Student profile with board, standard, medium, and English/Tanglish preference.
2. Chapter selector backed by a real structured syllabus catalogue.
3. Chapter analysis schema and concept map for a small verified pilot set of textbooks.
4. Standard-aware lesson renderer with visual learning components.
5. Novel concept question generator plus diagnostic, feedback, and reteaching loop.
6. PDF export and source references.
7. Diary capture/OCR and automatic matching to chapters and assignments.
8. Expand the verified library across grades, subjects, terms, and boards; add learning-history-based personalization.

## Success criteria

A chapter is not complete just because a summary and a question list exist. Students should be able to explain key ideas, answer a question phrased differently from the textbook, apply a concept to a new scenario, and see corrections that help them understand their mistakes. Validate lesson quality against teachers and curriculum sources before broad release.
