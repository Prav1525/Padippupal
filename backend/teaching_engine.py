"""Local, deterministic teaching-method helpers for PadippuPal's curriculum-grounded tutor.

This module does not train a language model. It builds stable teaching contracts and
mastery decisions around Gemini-generated explanations.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

DATASET_PATH = Path(__file__).with_name("class6_teaching_dataset.json")


def load_teaching_dataset(path: Path | str = DATASET_PATH) -> dict[str, Any]:
    """Load and minimally validate the reviewed teaching scaffold catalogue."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("chapters"), list):
        raise ValueError("Unsupported or malformed teaching dataset")
    for chapter in data["chapters"]:
        if not chapter.get("subject") or not chapter.get("chapter"):
            raise ValueError("Every chapter needs subject and chapter")
        for topic in chapter.get("topics", []):
            if not topic.get("id") or not topic.get("title"):
                raise ValueError("Every topic needs a stable id and title")
    return data


def find_chapter(data: dict[str, Any], subject: str, chapter_name: str) -> dict[str, Any] | None:
    """Case-insensitive exact chapter lookup; never silently picks a similar chapter."""
    matches = [
        item for item in data["chapters"]
        if item["subject"].casefold() == subject.strip().casefold()
        and item["chapter"].casefold() == chapter_name.strip().casefold()
    ]
    return matches[0] if len(matches) == 1 else None


def build_teacher_instructions(
    *, subject: str, chapter: str, topic: str, app_language: str,
    source_evidence: Iterable[dict[str, Any]], learner_history: str = "",
) -> str:
    """Build a repeatable teaching contract; evidence is supplied separately from metadata."""
    language = app_language.strip().casefold()
    if language not in {"english", "tanglish"}:
        language = "english"
    evidence = list(source_evidence)
    evidence_text = "\\n".join(
        f"[source_id={item.get('source_id', 'unknown')}; pages={item.get('page_start', '?')}-{item.get('page_end', '?')}] "
        f"{item.get('text', '')}" for item in evidence
    ) or "No approved source passage was retrieved. Do not claim textbook verification."
    language_rule = (
        "Write natural Tamil-English code-switching in Latin script (Tanglish). It must not be English-only. "
        "Use Tamil connective phrases naturally, preserve core Science/Mathematics terms, and ensure captions "
        "are the exact text being spoken."
        if language == "tanglish" else
        "Use natural, warm, age-appropriate English. Captions must exactly match the spoken explanation."
    )
    return f"""You are a warm, patient Class 6 {subject} teacher.
CURRICULUM SCOPE: chapter={chapter}; concept={topic}. Teach only this concept and its prerequisites.
SOURCE OF TRUTH: use only the approved evidence below for curriculum-specific claims. Do not invent textbook facts, page numbers, or source references. Separate clearly labelled everyday examples from source-backed claims.
TEACHING METHOD:
1. Briefly connect to what the learner may already know.
2. Explain one idea at a time in original child-friendly words; do not read/copy source text verbatim.
3. Give one worked example or concrete activity, explaining why each step matters.
4. Address one likely misconception.
5. After teaching, ask 2-3 short questions, including one application/reasoning question. Do not reveal answers before the learner responds.
6. Evaluate the learner's actual answer. If wrong or uncertain, explain the misconception, give a hint, reteach using a different example, and ask a new question.
7. Never claim mastery from a correct guess alone. Do not move to the next concept until at least two answers are correct and the learner demonstrates explanation or application. Ask whether the learner is ready to continue after mastery.
LANGUAGE: {language_rule}
LEARNER CONTEXT (use only to adapt pacing, not syllabus level): {learner_history or 'No previous evidence supplied.'}
APPROVED SOURCE EVIDENCE:
{evidence_text}
Return structured JSON with: explanation_steps (array of objects with spoken_text, caption, source_ids, visual_action), likely_misconception, checkpoint_questions (2-3 objects with id, question, skill, expected_answer, hint, reteach_strategy), and source_limitations. Keep every source id traceable to the supplied evidence. If evidence is absent, explicitly disclose that the lesson is not textbook-verified."""


def mastery_decision(
    correct_answers: int, total_answers: int, demonstrated_explanation_or_application: bool,
    *, minimum_correct: int = 2,
) -> dict[str, Any]:
    """Pure local gate for progression. Invalid counts fail closed."""
    if total_answers < 1 or correct_answers < 0 or correct_answers > total_answers:
        raise ValueError("Answer counts are invalid")
    mastered = correct_answers >= minimum_correct and demonstrated_explanation_or_application
    return {
        "mastered": mastered,
        "can_advance": mastered,
        "correct_answers": correct_answers,
        "total_answers": total_answers,
        "next_action": "offer_next_concept" if mastered else "reteach_and_retest",
    }
