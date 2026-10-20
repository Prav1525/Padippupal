# Live Teaching: Speech-Synchronized Lesson Design

## Goal

PadippuPal must teach from the selected textbook chapter in a live, paced lesson. Spoken narration, on-screen words, interactive diagrams, and student checks should advance together. Do not generate a full passage, play it later, and leave the visuals static.

## Non-negotiable grounding rule

1. Retrieve only approved chapter chunks from PadippuPal's own database for the student's board, class, subject, medium, edition, and selected chapter.
2. Use retrieved chunks as the source of factual teaching claims. Interactive visuals are render instructions, not a new source of facts.
3. Every lesson segment carries source chunk IDs/page references. If retrieval cannot support a claim, do not teach it as textbook fact.
4. Never fetch an external textbook as a fallback.

## Recommended architecture

### 1. Lesson planner (Gemini reasoning)

Ask Gemini to turn retrieved passages into a short structured lesson plan, not a long free-form essay. Validate the output against a schema. Use small teachable segments, each typically one sentence or a short phrase:

```json
{
  "lesson_id": "stable-session-id",
  "segments": [
    {
      "id": "s1",
      "spoken_text": "A magnet has two poles.",
      "caption_text": "A magnet has two poles",
      "source_chunk_ids": ["chunk-id"],
      "visual_action": {
        "type": "highlight",
        "target": "north_south_poles"
      },
      "checkpoint": null
    }
  ]
}
```

Allowed visual actions must come from a versioned allowlist of app-supported diagram/animation commands (e.g. highlight, reveal, move, compare, label, draw-line, show-result). Do not execute arbitrary code emitted by the model. Validate target IDs against the selected visual blueprint.

### 2. Segment-based speech playback

For the first implementation, synthesize and play short segments sequentially through the existing server-side Gemini TTS provider. Preserve the warm teacher voice and use the existing configured fallback only when needed. Start the caption and visual action at the audio segment's actual playback start, then advance on playback completion. Keep the next segment pre-generated where practical to reduce gaps.

Do not play one long audio file while guessing the animation timing. Segment boundaries create reliable synchronization points.

### 3. Text synchronization levels

- **First release:** highlight the current sentence/phrase and reveal its visual action at the corresponding audio segment. This is reliable and achievable without pretending to know exact word timestamps.
- **Word-by-word karaoke highlighting:** require real alignment timestamps. Android's `UtteranceProgressListener.onRangeStart` exposes character ranges for Android TTS, but it will not align text to audio synthesized by Gemini. For Gemini-generated audio, either run a validated speech forced-alignment stage on the generated audio, or use a TTS provider that returns SSML mark timepoints. Do not estimate word timestamps from character count and present them as exact.
- Keep the transcript visible if timestamp alignment is unavailable; fall back to phrase-level synchronization.

### 4. Visual timeline

The app owns a small deterministic playback state machine:
- preparing -> playing segment N -> paused/interrupted -> playing segment N+1 -> checkpoint -> complete.
- Apply each visual action only when its segment starts; never let the model directly control UI state or run code.
- On pause, preserve audio position and current visual state.
- On interruption/student question, stop/discard queued audio immediately, preserve the lesson/session, answer the question within the selected chapter, then offer to resume from the current segment.
- On leaving the tutor, save lesson ID, segment index, current diagram state, and conversation context locally.

### 5. Gemini Live is a later interaction mode

Gemini Live is useful for free-form spoken conversation, interruptions, and low-latency audio turns. It is not the best first implementation for a deterministic textbook lesson timeline because the app needs a validated script and repeatable visual cues. Add Live after chapter grounding, segment playback, pause/resume, and interruption handling are reliable. If Live is added, treat its transcription as captions unless exact audio/text alignment is provided.

## Suggested implementation phases

1. Complete exact chapter-filter retrieval and tests against real stored chapter IDs.
2. Add a validated `/tutor/lesson-plan` response schema with segment IDs, source references, captions, and visual actions.
3. Add segment-level TTS/playback callbacks in Android and bind captions/visuals to playback start/completion.
4. Add pause/resume, session restoration, and interruption handling.
5. Add optional word-level alignment; keep phrase highlighting as the dependable fallback.
6. Only then evaluate Gemini Live for conversational detours.

## Acceptance criteria

- A selected chapter cannot retrieve chunks from another chapter.
- Each spoken segment has source chunk references.
- The visual action and caption start with the matching audio segment.
- No static full passage is presented as if it were synchronized narration.
- Pause/resume and leaving/returning do not restart the lesson.
- Student interruption stops queued narration and preserves progress.
- If no supporting source chunk exists, the system refuses to invent textbook content.
- Tests cover English and Tanglish text, short/long audio segments, failed TTS, pause/resume, interruption, and missing visual targets.
