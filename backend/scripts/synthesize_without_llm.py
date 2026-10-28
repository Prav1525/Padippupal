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
CURRICULUM_VERSION = "extractive-v1"
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

def clean_sentences(text: str) -> list[str]:
    text = re.sub(r"Chapter\s+\d+[^\n]{0,80}(?:indd|pdf)[^\n]*", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    # Avoid copying exercise answer keys as the main teaching explanation.
    text = re.sub(r"\b(?:Figure it Out|Math Talk|Try This)\b", "Practice prompt", text, flags=re.I)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip(" -|") for p in parts if len(p.strip()) >= 35]

def short_summary(text: str) -> str:
    sentences = clean_sentences(text)
    if not sentences:
        return "Read the cited source passage carefully and identify its main idea."
    # A short extractive synopsis keeps the wording anchored in the supplied text.
    selected = sentences[:2]
    return " ".join(s[:450] for s in selected)[:850]

def build_lesson(subject: str, chapter: str, chunks: list[dict]) -> tuple[dict, dict]:
    allowed = {str(c["id"]) for c in chunks}
    if not allowed:
        raise ValueError(f"No source chunks for {chapter}")
    # One teachable step per chunk ensures no supplied chunk disappears from citations.
    objectives = []
    concept_map = []
    sequence = []
    for i, c in enumerate(chunks, 1):
        cid = str(c["id"])
        summary = short_summary(str(c["text"]))
        heading = chapter if i == 1 else f"{chapter}: source section {i}"
        objective = f"Identify and explain the main idea in source section {i} of {chapter}."
        objectives.append(objective)
        concept_map.append({
            "concept": heading,
            "prerequisite": "Connect the idea to what the learner already knows, then read the cited passage.",
            "source_chunk_ids": [cid],
        })
        sequence.append({
            "id": f"step_{i}",
            "title": heading,
            "teacher_says": f"Let's study this part of {chapter}. The source says: {summary}",
            "caption": summary[:500],
            "example": "Use an example or diagram from the cited textbook passage and explain why it fits.",
            "misconception": "Do not guess beyond the cited passage; check the source wording and worked examples.",
            "checkpoint": f"In your own words, explain the main idea from page {c.get('page_start') or 'shown'} and point to the evidence.",
            "source_chunk_ids": [cid],
            "visual": {"type": "table", "objects": [], "actions": [], "narration_sync": True},
        })
    lesson = {
        "chapter_title": chapter,
        "overview": (
            f"This is an automatically assembled, source-grounded study draft for Class 6 {subject}. "
            "It organizes the recorded textbook chunks into a sequence and preserves chunk-level citations. "
            "Explanations are extractive summaries, so a teacher must review clarity, correctness, examples, "
            "and age appropriateness before approval."
        ),
        "learning_objectives": objectives,
        "concept_map": concept_map,
        "teaching_sequence": sequence,
        "draft_method": "deterministic-extractive-v1",
        "human_review_required": True,
    }
    validation = validate_chapter_lesson_payload(lesson, allowed)
    if not validation["valid"]:
        raise ValueError(f"{chapter}: " + "; ".join(validation["errors"][:5]))
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
                         "deterministic-extractive-v1", now, now),
                    )
                    conn.execute(
                        """INSERT INTO syllabus_synthesis_rounds
                        (id,source_id,board,class_level,subject,chapter,curriculum_version,status,model,prompt_version,
                         source_chunk_ids_json,evidence_fingerprint,validation_json,error_message,created_at,updated_at)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,'draft',%s,%s,%s,%s,%s,'',%s,%s)
                        ON CONFLICT(id) DO UPDATE SET status='draft',model=excluded.model,
                          source_chunk_ids_json=excluded.source_chunk_ids_json,validation_json=excluded.validation_json,updated_at=excluded.updated_at""",
                        (round_id, str(source["id"]), BOARD, CLASS_LEVEL, subject, chapter, CURRICULUM_VERSION,
                         "deterministic-extractive-v1", CURRICULUM_VERSION,
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
                                         "misconception": step["misconception"], "checkpoint": step["checkpoint"]}, ensure_ascii=False),
                             json.dumps([step["example"]], ensure_ascii=False), json.dumps([step["checkpoint"]], ensure_ascii=False),
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
