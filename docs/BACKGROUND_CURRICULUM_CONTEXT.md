# Background Curriculum Context

## Product rule
Students must not manage syllabus PDFs, curriculum indexing, model context, or knowledge-base setup. Curriculum preparation is an internal system responsibility. The student-facing flow should stay focused on learning.

## Student experience
- Onboarding collects only the information needed to personalize learning: class/standard, board, textbook medium, and preferred explanation language. Name is optional.
- The home screen, diary scan, lesson, and question flows never require the student to upload curriculum documents.
- If a needed source is still being prepared, show a brief, non-technical status only when it affects the current task; do not block unrelated app use.
- If an exact curriculum match is unavailable, ask for the minimum clarification or transparently label the answer as general guidance. Never imply unverified material is official.

## Background curriculum pipeline
1. Maintain a catalog of curriculum sources by board, academic year, class, subject, textbook medium, term, edition, and source/license.
2. Ingest only approved or appropriately licensed sources. Verify file integrity, source identity, edition, and language.
3. Extract text from digital PDFs; run OCR for scanned pages. Preserve page numbers, headings, tables, diagram captions, and chapter boundaries where possible.
4. Normalize and split into retrieval chunks that retain source metadata and page references.
5. Index chunks for fast keyword and semantic retrieval. Cache processed content and reuse it across sessions.
6. Run quality checks: extraction coverage, empty pages, duplicate files, chapter ordering, metadata consistency, and spot-checks against the source.
7. Refresh in the background when a new edition is approved or the catalog changes. Keep the last known-good index available until the replacement passes validation.
8. At question time, filter by the student's board/class/subject/medium/edition, retrieve only relevant passages, and give the model those passages plus a task-specific prompt.
9. Store source references with generated lessons and questions so the app can distinguish textbook-backed statements from illustrative examples.
10. Monitor latency, retrieval relevance, source mismatches, and failures without exposing internal diagnostics to students.

## Performance requirements
- Never parse or index full textbooks on the main/UI thread.
- Do not re-process a source on every lesson request.
- Use bounded retrieval context, cache hot chapters, and paginate or stream lengthy work.
- Run large ingestion jobs on a backend worker/queue where possible. Android WorkManager is suitable for deferrable device-side synchronization, not as the only durable server-side job system.
- Provide cancellation, retry with backoff, and resumable jobs.
- Keep a usable app shell and cached lessons available when offline; show a friendly fallback if a required source is unavailable.

## Trust and safety
- Maintain source provenance and license/permission records. Do not redistribute copyrighted textbook files unless permitted.
- Keep student profile and learning data private; collect only what is necessary.
- Do not promise that generated questions will appear in an exam. Importance estimates must be explainable and treated as estimates.
- Never silently substitute another board, class, textbook medium, or edition when a match is missing.
- A syllabus upload alone does not train the model. Use retrieval-augmented generation (RAG) so only relevant verified content is supplied when needed.

## Acceptance criteria
- A student can ask a question without seeing or handling syllabus files.
- Retrieved passages match the profile's board, class, subject, and medium.
- Answers can cite chapter/page/source where source metadata exists.
- Indexing is performed outside the UI thread and repeated uploads are deduplicated.
- Failed or stale ingestion never replaces the last known-good index.
- Missing or ambiguous curriculum matches are handled honestly.
