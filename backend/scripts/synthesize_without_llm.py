"""Build source-grounded Class 6 draft lessons without an external LLM.

This deliberately creates EXTRACTIVE/STRUCTURED drafts, not teacher-approved prose.
Every lesson step points to the source chunks used. Human review remains mandatory.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import psycopg
from psycopg.rows import dict_row

from syllabus_synthesis import EvidenceChunk, evidence_fingerprint, make_run_id, validate_chapter_lesson_payload

BOARD = "CBSE"
CLASS_LEVEL = 6
MEDIUM = "English"
CURRICULUM_VERSION = "extractive-v5-tanglish"
MATH_IDS = [
    "6cd135e7-63e4-4350-9b7c-02fe1f566ec3", "189326ea-8ba7-4992-8322-96d988039d03",
    "ed0a6261-c9e2-483b-813a-bec262393ab9", "b1fe815a-ceac-4fde-85dc-fd90eba18450",
    "c0305350-d5ba-44ed-9a75-b19399423fa7", "a5a51061-ac8b-40d5-b9ea-1424f83613d8",
    "0d12f9e0-f7c0-4df3-b790-cc4ffb0bcb02", "1476f7b0-39ec-44af-b947-95a8871f7539",
    "2679d57b-bed5-462e-ba07-1d948f8dc07a", "13641871-39ce-469f-894a-12f56e5b7545",
]
SCIENCE_IDS = [
    "28077c43-b7fe-4a40-85c8-663b8ac326a2", "a9b2b9e9-2a18-4795-af67-0387ebf9436a",
    "bfee8bb2-18e4-47dd-97e3-4158246b2546", "f823bf8d-654a-4b7c-8fdd-e8838ea0b47f",
    "577d4aa1-c76a-4e3e-91c0-cc18b0b39d1e", "c7364059-4a0d-4257-a7d7-472a39f5c8f0",
    "9e340817-5ddb-4ef0-a529-b7b3354beec1", "ed0b5f40-e9e0-474d-82ac-9681b0f4c1cd",
    "c77231b4-a609-4e39-b4aa-76cbe8bf72f3", "0409c4be-893b-40af-ae0e-0ff380099363",
    "0d4e12b6-57ae-4f74-b1b2-be5644fa2483", "86bbabde-ec5d-455a-b4da-a1de78fad0d7",
]

HEADER_PATTERNS = [
    re.compile(r"\b(?:Ganita\s+Prakash|Curiosity)\s*\|\s*(?:Textbook of Science\s*\|\s*)?Grade\s*6\s*\d{1,4}\b", re.I),
    re.compile(r"\bChapter\s+\d{1,2}\s+(?=(?:On a bright|Activity|Let us|In this|We can|Aavi|Thirav)\b)", re.I),
    re.compile(r"\b(?:Grade|Class)\s*6\s*\|\s*(?:Textbook of Science\s*\|\s*)?\d{1,4}\b", re.I),
    re.compile(r"[\uFFFD\u0080-\u009F]"),
]
PLACEHOLDER_PATTERNS = [
    re.compile(r"identify and explain the main idea in source section", re.I),
    re.compile(r"use an example or diagram from the cited textbook passage", re.I),
    re.compile(r"explain the main idea from page .* and point to the evidence", re.I),
    re.compile(r"read the cited source passage carefully and identify its main idea", re.I),
]

def clean_source_text(text: str, chapter: str | None = None) -> str:
    """Remove known PDF running headers, control/OCR noise, and duplicate whitespace."""
    text = text.replace("\uFFFD", " ").replace("\u008B", " ").replace("\x8b", " ")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", " ", text)
    # Known running headers are embedded in some chunk text, so clean inline as well as at line starts.
    if chapter:
        text = re.sub(rf"\b{re.escape(chapter)}\s*\d{{0,3}}\s*Chapter\b", " ", text, flags=re.I)
    text = re.sub(r"(?:Ganita\s+Prakash|Curiosity)\s*\|\s*(?:Textbook of Science\s*\|\s*)?Grade\s*6\s*\d{1,4}", " ", text, flags=re.I)
    text = re.sub(r"\b(?:Figure it Out|Math Talk|Try This)\b", "Practice prompt", text, flags=re.I)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" \t\n-|")
    return text

def clean_sentences(text: str, chapter: str | None = None) -> list[str]:
    text = clean_source_text(text, chapter)
    # Split around sentence boundaries, retaining short but meaningful textbook questions.
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9“‘])", text)
    cleaned = []
    seen = set()
    for part in parts:
        sentence = part.strip(" -|")
        if len(sentence) < 28:
            continue
        if re.fullmatch(r"(?:chapter\s*)?\d{1,4}", sentence, re.I):
            continue
        key = re.sub(r"\W+", " ", sentence).casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(sentence)
    return cleaned

def short_summary(text: str, chapter: str | None = None) -> str:
    sentences = clean_sentences(text, chapter)
    if not sentences:
        return ""
    # Keep the first two readable, source-grounded sentences; avoid unbounded page dumps.
    return " ".join(s[:420] for s in sentences[:2])[:700].strip()

def summarize_group(group: list[dict], chapter: str, max_chars: int = 560) -> str:
    """Select a few readable source sentences instead of concatenating entire PDF chunks."""
    candidates: list[str] = []
    seen: set[str] = set()
    for chunk in group:
        for sentence in clean_sentences(str(chunk.get("clean_summary") or chunk.get("text") or ""), chapter):
            sentence = re.sub(r"\s+", " ", sentence).strip()
            if len(sentence) < 35 or len(sentence) > 300:
                continue
            if re.search(r"\b(?:Practice prompt|Fill in the blanks|Figure it Out)\b", sentence, re.I):
                continue
            key = re.sub(r"\W+", " ", sentence).casefold()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(sentence)
    selected: list[str] = []
    used = 0
    for sentence in candidates:
        addition = len(sentence) + (1 if selected else 0)
        if used + addition > max_chars:
            continue
        selected.append(sentence)
        used += addition
        if len(selected) >= 4:
            break
    if not selected:
        raise ValueError(f"{chapter}: no concise, readable sentences for a teaching stage")
    return " ".join(selected)


def specific_objective(summary: str, chapter: str) -> str:
    """Create a short, source-specific objective without pasting a whole page."""
    sentence = summary.strip().rstrip(".!?")
    if len(sentence) > 105:
        sentence = sentence[:102].rsplit(" ", 1)[0] + "..."
    if not sentence:
        raise ValueError(f"{chapter}: no readable source text for learning objective")
    return f"Explain the textbook idea or situation: {sentence}"

def tanglish_explanation(summary: str, chapter: str, stage: int) -> str:
    """Write a warm, spoken Tanglish bridge around the source excerpt, not formal translation."""
    openings = [
        "Seri, idha easy-aa paapom.",
        "Okay, indha part-a serndhu purinjukalaam.",
        "Nalla gavaninga, inga oru mukkiyamaana idea irukku.",
        "Ippo indha concept-a simple-aa break panni paapom.",
        "Sari, indha example enna solludhu-nu paapom.",
        "Konjam yosichu paarunga; idhu namma daily life-layum varalaam.",
        "Super, ippo next idea-ku polaam.",
        "Oru chinna recap pannitu idha paapom.",
    ]
    opener = openings[(stage - 1) % len(openings)]
    excerpt = summary.strip().rstrip()
    return (
        f"{opener} Textbook-la ippadi sollirukkaanga: “{excerpt}” "
        "Idha padichuttu, ungalukku enna purinjadhu-nu unga style-la sollunga. "
        "English term konjam pudhusa irundhaalum parava illa; adha namma context-oda purinjukalaam."
    )


def tanglish_checkpoint(summary: str, page: int | None, chapter: str, stage: int) -> str:
    """Ask a conversational check-for-understanding question grounded in the excerpt."""
    text = summary.casefold()
    page_hint = f" Textbook page {page}-la indha part irukku." if page is not None else ""
    if any(term in text for term in ("fraction", "roti", "equal share", "numerator", "denominator")):
        question = "Idha equal-aa share panninaa ovvorutharukku evlo kidaikkum? Eppadi decide panneenga?"
    elif any(term in text for term in ("ice", "water vapour", "evaporat", "condens", "melt", "boil", "solid", "liquid", "gas")):
        question = "Indha change-la enna nadakkudhu? Start-la enna irundhuchu, apram enna aachu?"
    elif any(term in text for term in ("magnet", "attract", "iron", "metal")):
        question = "Indha example-la edhu attract aagudhu? Textbook example-la irundhu sollunga."
    elif any(term in text for term in ("plant", "root", "leaf", "seed", "flower")):
        question = "Indha plant part enna velai seyyudhu? Passage-la irukkura example vechu sollunga."
    elif any(term in text for term in ("number", "digit", "place value", "pattern", "multiple")):
        question = "Indha number/pattern-la enna rule theriyudhu? Oru example vechu explain pannunga."
    else:
        question = "Indha part-la main idea enna? Unga vaarthaigal-la oru chinna explanation sollunga."
    return (
        f"Seri, oru quick check. {question}{page_hint} "
        "Answer theriyalana parava illa—passage-a innoru thadava paarthu try pannalaam."
    )


def tanglish_objective(summary: str, chapter: str) -> str:
    """Keep objectives learner-friendly and spoken, avoiding word-for-word English translation."""
    return (
        "Indha part padichadhukku apram, main idea enna-nu unga vaarthaigal-la simple-aa solla mudiyanum. "
        "Adha oru example-oda connect panna mudinja, concept innum clear aagum."
    )

def source_based_example(summary: str) -> str:
    """Turn actual cited text into a learner task without inventing facts."""
    sentence = summary.strip()
    if len(sentence) > 240:
        sentence = sentence[:237].rsplit(" ", 1)[0] + "..."
    if not sentence:
        raise ValueError("Cannot build an example from empty source text")
    return (
        f"Textbook-based application: read this passage — “{sentence}” "
        "— then identify the key idea and explain it using evidence from the passage."
    )

def quality_gate(lesson: dict, chunks: list[dict]) -> list[str]:
    """Reject placeholder content, weak Tanglish scaffolds, OCR noise, and citation gaps."""
    errors: list[str] = []
    allowed = {str(c["id"]) for c in chunks}
    objectives = lesson.get("learning_objectives", [])
    if len(objectives) < 3:
        errors.append("need at least three chapter-specific learning objectives")
    if len(lesson.get("learning_objectives_tanglish", [])) != len(objectives):
        errors.append("English and Tanglish objective counts must match")
    for objective in objectives:
        if any(pattern.search(objective) for pattern in PLACEHOLDER_PATTERNS):
            errors.append("generic/placeholder learning objective detected")
            break
    steps = lesson.get("teaching_sequence", [])
    if not 3 <= len(steps) <= 10:
        errors.append("lesson must have 3–10 coherent teaching steps, not one step per PDF chunk")
    cited_all: set[str] = set()
    for i, step in enumerate(steps):
        tanglish = step.get("tanglish")
        if not isinstance(tanglish, dict):
            errors.append(f"step {i + 1}: missing Tanglish scaffold")
        else:
            for field in ("teacher_says", "caption", "example", "checkpoint"):
                if not isinstance(tanglish.get(field), str) or len(tanglish[field].strip()) < 35:
                    errors.append(f"step {i + 1}: Tanglish {field} missing or too short")
        for field in ("teacher_says", "caption", "example", "checkpoint"):
            value = str(step.get(field) or "").strip()
            if len(value) < 35:
                errors.append(f"step {i + 1}: {field} is too short")
            if any(pattern.search(value) for pattern in PLACEHOLDER_PATTERNS):
                errors.append(f"step {i + 1}: placeholder {field} detected")
        combined = " ".join(str(step.get(k, "")) for k in ("teacher_says", "caption", "example", "checkpoint"))
        if re.search(r"[\uFFFD\u0080-\u009F]", combined):
            errors.append(f"step {i + 1}: control/OCR replacement character remains")
        cited = {str(cid) for cid in step.get("source_chunk_ids", [])}
        if not cited or not cited.issubset(allowed):
            errors.append(f"step {i + 1}: invalid or missing source citation")
        cited_all.update(cited)
    if cited_all != allowed:
        errors.append(f"teaching sequence citation coverage mismatch: {len(allowed - cited_all)} source chunks not cited")
    variants = lesson.get("language_variants", {})
    if not variants.get("Tanglish", {}).get("available"):
        errors.append("Tanglish variant must be explicitly available")
    return errors


def build_lesson(subject: str, chapter: str, chunks: list[dict]) -> tuple[dict, dict]:
    allowed = {str(c["id"]) for c in chunks}
    if not allowed:
        raise ValueError(f"No source chunks for {chapter}")

    # Turn a long PDF chunk list into a manageable lesson sequence of at most eight stages.
    # Each stage cites every source chunk it summarizes, preserving full traceability.
    prepared = []
    for c in chunks:
        summary = short_summary(str(c["text"]), chapter)
        if not summary:
            raise ValueError(f"{chapter}: source chunk {c['id']} has no readable text after cleanup")
        prepared.append({**c, "clean_summary": summary})
    group_size = max(1, (len(prepared) + 7) // 8)
    groups = [prepared[i:i + group_size] for i in range(0, len(prepared), group_size)]

    objectives: list[str] = []
    objectives_tanglish: list[str] = []
    concept_map = []
    sequence = []
    for i, group in enumerate(groups, 1):
        chunk_ids = [str(c["id"]) for c in group]
        summary = summarize_group(group, chapter)
        if len(summary) > 600:
            errors_summary = True
            raise ValueError(f"{chapter}: teaching stage summary exceeds 600 characters")
        objective = specific_objective(summary, chapter)
        if objective not in objectives and len(objectives) < 6:
            objectives.append(objective)
            objective_core = objective.removeprefix("Explain the textbook idea or situation: ")
            objectives_tanglish.append(tanglish_objective(summary, chapter))
        heading = f"{chapter}: stage {i}"
        concept_map.append({
            "concept": f"{heading} — {summary[:130]}",
            "prerequisite": "Connect this cited passage group to the chapter's central question, using only source evidence.",
            "source_chunk_ids": chunk_ids,
            "tanglish_support": {
                "concept": f"{heading}: indha passages-la varra mukkiya idea — {summary[:100]}",
                "prerequisite": "Indha idea-va munnaadi padicha concept-oda connect pannunga; source-la illaadha details-ai add panna vendaam.",
            },
        })
        pages = [c.get("page_start") for c in group if c.get("page_start") is not None]
        page_text = f" (textbook pages {min(pages)}–{max(pages)})" if pages else ""
        checkpoint_text = summary[:200].rstrip(" .!?")
        sequence.append({
            "id": f"step_{i}",
            "title": f"{chapter} — Part {i}",
            "teacher_says": f"Let's work through Part {i} of {chapter}. Read the cited textbook passages and notice the main idea: {summary}",
            "caption": summary[:500],
            "example": source_based_example(summary),
            "misconception": "Distinguish what the source states from an inference. Verify any worked calculation, diagram, or scientific claim before teaching.",
            "checkpoint": f"Explain the main idea in your own words{page_text}: “{checkpoint_text}”. Which evidence in these passages supports your explanation?",
            "source_chunk_ids": chunk_ids,
            "tanglish": {
                "teacher_says": tanglish_explanation(summary, chapter, i),
                "caption": f"Indha part-oda main point: {summary[:320]}",
                "example": (
                    f"{'Seri, indha Maths idea-va oru chinna example-la try panni paakalam.' if subject.lower() in {'mathematics', 'maths', 'math'} else 'Seri, indha Science idea-va namma daily life-oda connect panni paakalam.'} "
                    f"Textbook-la irukkura point: {summary[:180]} "
                    "Idha un words-la explain pannu; example yosikkumbodhu textbook-la illaadha facts-ai guess panna vendaam."
                ),
                "checkpoint": tanglish_checkpoint(summary, min(pages) if pages else None, chapter, i),
                "misconception": (
                    "Idhu konjam confusing-aa irundhaalum parava illa. Textbook clue-oda thirumba paakalam; "
                    "term puriyalana adha first clear pannittu continue pannalaam."
                ),
            },
            "visual": {"type": "table", "objects": [], "actions": [], "narration_sync": True},
        })

    lesson = {
        "chapter_title": chapter,
        "overview": (
            f"Class 6 {subject}: {chapter}. This source-grounded draft organizes textbook material into "
            f"{len(sequence)} manageable teaching stages. Each stage uses a short extractive summary and preserves "
            "source-chunk citations. Tanglish fields provide learner instructions, not a complete translation. "
            "Worked solutions and factual accuracy still require domain review."
        ),
        "learning_objectives": objectives,
        "learning_objectives_tanglish": objectives_tanglish,
        "concept_map": concept_map,
        "teaching_sequence": sequence,
        "draft_method": "deterministic-extractive-v5-tanglish",
        "language_variants": {
            "English": {"language": "English", "available": True},
            "Tanglish": {
                "language": "Tanglish",
                "script": "Tamil written in Latin characters, retaining English subject terms",
                "available": True,
                "method": "natural conversational Tanglish teacher prompts, learner-friendly objectives, and topic-aware checkpoints around cited English source excerpts; not a full textbook translation",
                "human_review_required": True,
            },
        },
        "human_review_required": True,
    }
    validation = validate_chapter_lesson_payload(lesson, allowed)
    if not validation["valid"]:
        raise ValueError(f"{chapter}: " + "; ".join(validation["errors"][:5]))
    quality_errors = quality_gate(lesson, chunks)
    if quality_errors:
        raise ValueError(f"{chapter}: quality gate failed: " + "; ".join(quality_errors[:8]))
    validation["quality_gate"] = {"passed": True, "errors": []}
    validation["teaching_stage_count"] = len(sequence)
    validation["tanglish_scaffold"] = True
    return lesson, validation

def main() -> None:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        raise SystemExit("DATABASE_URL is required (use isolated prototype DB only).")
    source_groups = [("Mathematics", MATH_IDS, 10), ("Science", SCIENCE_IDS, 12)]
    totals = {"drafts": 0, "failed": 0}
    with psycopg.connect(database_url, connect_timeout=10, row_factory=dict_row) as conn:
        for subject, source_ids, expected in source_groups:
            placeholders = ",".join(["%s"] * len(source_ids))
            sources = conn.execute(
                f"SELECT id, title, board, class_level, subject, medium FROM sources WHERE status='ready' AND id IN ({placeholders})",
                source_ids,
            ).fetchall()
            if len(sources) != expected:
                raise RuntimeError(f"{subject}: expected {expected} ready source PDFs, found {len(sources)}")
            for source in sources:
                rows = conn.execute(
                    "SELECT id, source_id, chunk_no, chapter, page_start, page_end, text FROM chunks WHERE source_id=%s AND trim(coalesce(chapter,''))<>'' ORDER BY chunk_no, page_start, id",
                    (source["id"],),
                ).fetchall()
                grouped: dict[str, list[dict]] = {}
                for row in rows:
                    grouped.setdefault(re.sub(r"\s+", " ", str(row["chapter"])).strip(), []).append(dict(row))
                if len(grouped) != 1:
                    # The syllabus inventory is chapter-PDF based; do not silently combine/split titles.
                    raise RuntimeError(f"{source['title']}: expected one recorded chapter, found {list(grouped)}")
                chapter, chunk_rows = next(iter(grouped.items()))
                evidence = [EvidenceChunk(
                    id=str(c["id"]), source_id=str(c["source_id"]), chapter=chapter,
                    chunk_no=int(c["chunk_no"] or 0),
                    page_start=int(c["page_start"]) if c["page_start"] is not None else None,
                    page_end=int(c["page_end"]) if c["page_end"] is not None else None,
                    text=str(c["text"]),
                ) for c in chunk_rows]
                fingerprint = evidence_fingerprint(evidence)
                round_id = make_run_id(str(source["id"]), chapter, CURRICULUM_VERSION, fingerprint)
                lesson, validation = build_lesson(subject, chapter, chunk_rows)
                refs = [{"chunk_id": str(c["id"]), "source_id": str(source["id"]), "title": source["title"],
                         "page_start": c["page_start"], "page_end": c["page_end"], "chunk_no": c["chunk_no"]} for c in chunk_rows]
                lesson_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "padippupal:chapter-lesson:" + round_id + ":"))
                now = time.time()
                with conn.transaction():
                    conn.execute(
                        """INSERT INTO chapter_lessons
                        (id,board,class_level,subject,medium,chapter,topic,status,lesson_json,source_refs_json,model,review_feedback,created_at,updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,'','draft',%s,%s,%s,'',%s,%s)
                        ON CONFLICT(id) DO UPDATE SET lesson_json=excluded.lesson_json,source_refs_json=excluded.source_refs_json,
                          model=excluded.model,updated_at=excluded.updated_at
                        WHERE chapter_lessons.status='draft'""",
                        (lesson_id, BOARD, CLASS_LEVEL, subject, MEDIUM, chapter,
                         json.dumps(lesson, ensure_ascii=False), json.dumps(refs, ensure_ascii=False),
                         "deterministic-extractive-v5-tanglish", now, now),
                    )
                    conn.execute(
                        """INSERT INTO syllabus_synthesis_rounds
                        (id,source_id,board,class_level,subject,chapter,curriculum_version,status,model,prompt_version,
                         source_chunk_ids_json,evidence_fingerprint,validation_json,error_message,created_at,updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,'draft',%s,%s,%s,%s,%s,'',%s,%s)
                        ON CONFLICT(id) DO UPDATE SET status='draft',model=excluded.model,
                          source_chunk_ids_json=excluded.source_chunk_ids_json,validation_json=excluded.validation_json,updated_at=excluded.updated_at""",
                        (round_id, str(source["id"]), BOARD, CLASS_LEVEL, subject, chapter, CURRICULUM_VERSION,
                         "deterministic-extractive-v5-tanglish", CURRICULUM_VERSION,
                         json.dumps([c.id for c in evidence]), fingerprint, json.dumps(validation), now, now),
                    )
                    conn.execute("DELETE FROM syllabus_topic_syntheses WHERE round_id=%s", (round_id,))
                    for i, step in enumerate(lesson["teaching_sequence"]):
                        citations = step["source_chunk_ids"]
                        topic_id = hashlib.sha256(f"{round_id}|{i}|{step['title']}".encode()).hexdigest()
                        conn.execute(
                            """INSERT INTO syllabus_topic_syntheses
                            (id,round_id,source_id,topic,page_start,page_end,learning_objectives_json,explanation_json,
                             examples_json,practice_questions_json,citation_refs_json,validation_status,validation_notes_json,
                             approval_status,created_at,updated_at)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'passed',%s,'draft',%s,%s)""",
                            (topic_id, round_id, str(source["id"]), step["title"],
                             next((c.page_start for c in evidence if c.id in citations), None),
                             next((c.page_end for c in evidence if c.id in citations), None),
                             json.dumps([step["title"]], ensure_ascii=False),
                             json.dumps({"teacher_says": step["teacher_says"], "caption": step["caption"],
                                         "misconception": step["misconception"], "checkpoint": step["checkpoint"],
                                         "tanglish": step["tanglish"]}, ensure_ascii=False),
                             json.dumps([step["example"], step["tanglish"]["example"]], ensure_ascii=False),
                             json.dumps([step["checkpoint"], step["tanglish"]["checkpoint"]], ensure_ascii=False),
                             json.dumps(citations), json.dumps(["All citations verified against this source"]), now, now),
                        )
                totals["drafts"] += 1
                print(json.dumps({"subject": subject, "chapter": chapter, "status": "draft",
                                  "lesson_id": lesson_id, "round_id": round_id,
                                  "source_chunks": len(chunk_rows), "cited_chunks": validation["cited_chunk_count"]}))
    print(json.dumps({"summary": totals, "human_review_required": True}))
    if totals["drafts"] != 22:
        raise SystemExit(f"Expected 22 drafts, wrote {totals['drafts']}")

if __name__ == "__main__":
    main()
