# PadippuPal tutor release acceptance

This is the end-to-end release gate for the Gemini-first tutor. A successful CI build or mocked API test is not sufficient to call the app complete.

## 1. Backend checks

- [ ] `GET /health` responds successfully.
- [ ] `GET /health/voice` reports configuration without exposing credentials.
- [ ] `POST /tutor/chat` uses Gemini and returns `provider: gemini`.
- [ ] A missing Gemini key fails clearly; it does not switch reasoning to Groq.
- [ ] A question with a matching approved curriculum source returns source metadata and `grounded: true`.
- [ ] A question with no approved source does not claim official NCERT verification.
- [ ] A selected chapter/topic and lesson blueprint constrain the response to the current learning step.
- [ ] `POST /tutor/speech` returns playable audio when configured; Android TTS remains the final device fallback.

## 2. Target-phone checks

Test on the user's actual Android phone with the release candidate installed.

1. Open a selected subject, chapter and topic; start the tutor.
2. Ask a question and wait for the response and speech to finish.
3. Ask a follow-up such as “why?” that only makes sense in the prior exchange. Confirm the tutor answers the follow-up rather than greeting/restarting.
4. Navigate back to the home screen, reopen the tutor, and confirm the same-day lesson, messages, selected subject/chapter/topic and language are restored.
5. Force-close and reopen the app; confirm the same-day session restores.
6. Switch explanation language to English/Tanglish/Tamil and confirm the syllabus selection does not change.
7. Open the matching interactive lesson, drag a meaningful object/point, and confirm the visual changes as described by the tutor. Reset the visual and try the lesson checkpoint.
8. Confirm speech is natural enough to understand, does not read raw LaTeX/JSON, and does not speak internal instructions or errors.
9. Turn off network access and confirm the app fails gracefully without showing stack traces or falsely claiming Gemini answered.
10. Reopen the app on the next local day and confirm the product's intended daily-session policy is clear and does not silently present yesterday's transcript as today's lesson.

## 3. Curriculum truth checks

- [ ] Verify board, class, subject, textbook medium, academic year/edition and chapter against the current official source.
- [ ] Check exact definitions, scope, examples, exercise ordering and diagram labels against that source.
- [ ] Keep the lesson blueprint separate from evidence that a fact is in the textbook.
- [ ] Do not ingest or redistribute copyrighted textbook text without appropriate permission/legal review.
- [ ] If an exact source is not approved/indexed, label the answer as general concept help rather than official textbook-grounded content.

## 4. Gemini Live

Gemini Live is intentionally deferred. Do not add it to the release gate until the core turn-based tutor, context restoration, source boundaries, interactive diagrams and speech playback all pass. Then evaluate latency, interruption/barge-in, microphone permissions, reconnection, privacy and usage costs as a separate feature.

## Release decision

Mark complete only after backend/CI checks and target-phone checks have actual recorded results. If the phone has not been tested, status remains **not yet end-to-end verified**.
