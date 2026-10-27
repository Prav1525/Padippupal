"""Source-grounded syllabus synthesis primitives for PadippuPal.

This module prepares chapter evidence from already-ingested textbook chunks and
validates synthesis payloads before persistence. Human review against the source
text remains necessary for factual and pedagogical correctness.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class EvidenceChunk:
    id: str
    source_id: str
    chapter: str
    chunk_no: int
    page_start: int | None
    page_end: int | None
    text: str


def evidence_fingerprint(chunks: Sequence[EvidenceChunk]) -> str:
    """Stable digest: changed source text or chunk ordering creates a new run."""
    payload = [
        {"id": c.id, "source_id": c.source_id, "chapter": c.chapter,
         "chunk_no": c.chunk_no, "page_start": c.page_start,
         "page_end": c.page_end, "text": c.text}
        for c in sorted(chunks, key=lambda x: (x.page_start or 0, x.chunk_no, x.id))
    ]
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def group_chapter_evidence(chunks: Iterable[Mapping[str, Any]]) -> dict[str, list[EvidenceChunk]]:
    """Group existing DB chunk rows by their recorded chapter; never guess a chapter."""
    grouped: dict[str, list[EvidenceChunk]] = {}
    for row in chunks:
        chapter = str(row.get("chapter") or "").strip()
        text = str(row.get("text") or "").strip()
        if not chapter or not text:
            continue
        item = EvidenceChunk(
            id=str(row["id"]), source_id=str(row["source_id"]), chapter=chapter,
            chunk_no=int(row.get("chunk_no") or 0),
            page_start=int(row["page_start"]) if row.get("page_start") is not None else None,
            page_end=int(row["page_end"]) if row.get("page_end") is not None else None,
            text=text,
        )
        grouped.setdefault(chapter, []).append(item)
    for items in grouped.values():
        items.sort(key=lambda x: (x.page_start or 0, x.chunk_no, x.id))
    return grouped


def build_evidence_packet(chunks: Sequence[EvidenceChunk]) -> dict[str, Any]:
    """Build a compact, traceable packet for one complete recorded chapter."""
    if not chunks:
        raise ValueError("Cannot synthesize a chapter without source evidence")
    chapter_names = {c.chapter for c in chunks}
    source_ids = {c.source_id for c in chunks}
    if len(chapter_names) != 1 or len(source_ids) != 1:
        raise ValueError("Evidence packet must contain one chapter from one source")
    return {
        "source_id": next(iter(source_ids)), "chapter": next(iter(chapter_names)),
        "chunk_ids": [c.id for c in chunks],
        "page_start": min((c.page_start for c in chunks if c.page_start is not None), default=None),
        "page_end": max((c.page_end for c in chunks if c.page_end is not None), default=None),
        "evidence_fingerprint": evidence_fingerprint(chunks),
        "evidence": [{"chunk_id": c.id, "page_start": c.page_start,
                      "page_end": c.page_end, "text": c.text} for c in chunks],
    }


def validate_synthesis_payload(payload: Mapping[str, Any], allowed_chunk_ids: set[str]) -> dict[str, Any]:
    """Reject empty or unsupported chapter/topic outputs before persistence."""
    errors: list[str] = []
    topics = payload.get("topics")
    if not isinstance(topics, list) or not topics:
        errors.append("topics must be a non-empty list")
        topics = []
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(topics):
        if not isinstance(raw, Mapping):
            errors.append(f"topics[{index}] must be an object")
            continue
        title = re.sub(r"\s+", " ", str(raw.get("topic") or "")).strip()
        if not title:
            errors.append(f"topics[{index}] is missing topic")
            continue
        key = title.casefold()
        if key in seen:
            errors.append(f"duplicate topic: {title}")
            continue
        seen.add(key)
        objectives = raw.get("learning_objectives", [])
        explanation = raw.get("explanation", {})
        citations = raw.get("citation_refs", [])
        if not isinstance(objectives, list) or not objectives:
            errors.append(f"{title}: learning_objectives must be a non-empty list")
            objectives = []
        if not isinstance(explanation, (str, Mapping)) or not explanation:
            errors.append(f"{title}: explanation must be non-empty text or object")
            explanation = {}
        if not isinstance(citations, list) or not citations:
            errors.append(f"{title}: citation_refs must be a non-empty list")
            citations = []
        unknown = [str(cid) for cid in citations if str(cid) not in allowed_chunk_ids]
        if unknown:
            errors.append(f"{title}: citations reference unknown chunks: {', '.join(unknown)}")
        normalized.append({
            "topic": title, "learning_objectives": objectives, "explanation": explanation,
            "examples": raw.get("examples", []) if isinstance(raw.get("examples", []), list) else [],
            "practice_questions": raw.get("practice_questions", []) if isinstance(raw.get("practice_questions", []), list) else [],
            "citation_refs": [str(cid) for cid in citations],
        })
    return {"valid": not errors, "errors": errors, "topics": normalized}


def validate_lesson_content_consistency(payload: Mapping[str, Any]) -> list[str]:
    """Catch known high-impact lesson/visual contradictions before a draft is saved.

    These targeted editorial guardrails supplement, but do not replace, human
    review against cited textbook pages.
    """
    errors: list[str] = []
    chapter = str(payload.get("chapter_title") or "").casefold()
    steps = payload.get("teaching_sequence")
    if not isinstance(steps, list):
        return errors
    for index, step in enumerate(steps):
        if not isinstance(step, Mapping):
            continue
        title = str(step.get("title") or "").casefold()
        teacher = str(step.get("teacher_says") or "").casefold()
        visual = step.get("visual") if isinstance(step.get("visual"), Mapping) else {}
        visual_text = " ".join(str(value).casefold() for value in (
            visual.get("narration_sync", []), visual.get("objects", []),
            visual.get("actions", []), step.get("caption", ""), step.get("example", ""),
        ))
        where = f"teaching_sequence[{index}] ({step.get('title') or 'untitled'})"
        if "fractions" in chapter and "parts of a whole" in title:
            if "6 equal parts" in teacher and "3 equal pieces" in visual_text:
                errors.append(f"{where}: visual says thirds while narration teaches sixths; align the fraction example.")
        if "fractions" in chapter and "number line" in title:
            if "2 equal parts" in teacher and "3 equal parts" in teacher and "5 equal parts" in visual_text:
                errors.append(f"{where}: number-line visual teaches fifths while narration teaches halves and thirds.")
        if "fractions" in chapter and "history" in title:
            if "rig veda" in teacher and ("similar to ours" in teacher or "similar to modern" in teacher):
                errors.append(
                    f"{where}: do not conflate the Rig Veda's tri-pada reference with later fraction notation; "
                    "separate and independently cite historical claims."
                )
        if "data handling" in chapter and "tally" in title:
            if "every fifth mark" in teacher and "||||" in teacher:
                errors.append(
                    f"{where}: tally example shows only four vertical strokes; explicitly show four strokes crossed by the fifth."
                )
        if "perimeter and area" in chapter and "diagonal" in title:
            if "a diagonal line is longer than a straight grid unit" in teacher:
                errors.append(
                    f"{where}: qualify the claim to a diagonal across a unit square (length sqrt(2) units)."
                )
        if "perimeter and area" in chapter and "area of triangles" in title:
            if "any rectangle" in teacher and "half the area" in teacher:
                errors.append(
                    f"{where}: state that the rectangle has the same base and corresponding height as the triangle."
                )
    return errors


def validate_chapter_lesson_payload(payload: Mapping[str, Any], allowed_chunk_ids: set[str]) -> dict[str, Any]:
    """Validate the complete lesson contract before any draft is persisted."""
    errors: list[str] = []
    for field in ("chapter_title", "overview"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            errors.append(f"{field} must be non-empty text")
    objectives = payload.get("learning_objectives")
    if not isinstance(objectives, list) or not objectives or any(
        not isinstance(item, str) or not item.strip() for item in objectives
    ):
        errors.append("learning_objectives must contain non-empty strings")
    cited_chunk_ids: set[str] = set()
    concepts = payload.get("concept_map")
    if not isinstance(concepts, list) or not concepts:
        errors.append("concept_map must be a non-empty list")
        concepts = []
    for index, concept in enumerate(concepts):
        if not isinstance(concept, Mapping) or not str(concept.get("concept") or "").strip():
            errors.append(f"concept_map[{index}] must include a concept")
            continue
        citations = concept.get("source_chunk_ids")
        if not isinstance(citations, list) or not citations:
            errors.append(f"concept_map[{index}] must cite source chunks")
        else:
            citation_ids = {str(value) for value in citations}
            unknown_ids = sorted(citation_ids - allowed_chunk_ids)
            if unknown_ids:
                errors.append(f"concept_map[{index}] cites unknown source chunk IDs: {', '.join(unknown_ids[:20])}")
            cited_chunk_ids.update(citation_ids & allowed_chunk_ids)
    steps = payload.get("teaching_sequence")
    if not isinstance(steps, list) or not steps:
        errors.append("teaching_sequence must be a non-empty list")
        steps = []
    allowed_visuals = {"number_pattern", "number_line", "geometry", "compare", "process", "table", "diagram", "none"}
    for index, step in enumerate(steps):
        if not isinstance(step, Mapping):
            errors.append(f"teaching_sequence[{index}] must be an object")
            continue
        for field in ("title", "teacher_says", "caption", "checkpoint"):
            if not isinstance(step.get(field), str) or not step[field].strip():
                errors.append(f"teaching_sequence[{index}].{field} must be non-empty text")
        citations = step.get("source_chunk_ids")
        if not isinstance(citations, list) or not citations:
            errors.append(f"teaching_sequence[{index}] must cite source chunks")
        else:
            citation_ids = {str(value) for value in citations}
            unknown_ids = sorted(citation_ids - allowed_chunk_ids)
            if unknown_ids:
                errors.append(f"teaching_sequence[{index}] cites unknown source chunk IDs: {', '.join(unknown_ids[:20])}")
            cited_chunk_ids.update(citation_ids & allowed_chunk_ids)
        visual = step.get("visual") or {}
        if not isinstance(visual, Mapping) or visual.get("type", "none") not in allowed_visuals:
            errors.append(f"teaching_sequence[{index}] has an unsupported visual recipe")
    errors.extend(validate_lesson_content_consistency(payload))
    missing_citations = allowed_chunk_ids - cited_chunk_ids
    if missing_citations:
        errors.append(
            "lesson leaves supplied source chunks uncited; include these exact IDs: "
            + ", ".join(sorted(missing_citations)[:40])
            + (f" (and {len(missing_citations) - 40} more)" if len(missing_citations) > 40 else "")
        )
    return {
        "valid": not errors, "errors": errors,
        "checks": [
            "chapter title and overview are present",
            "learning objectives and concept map are non-empty",
            "every concept and teaching step cites supplied source chunks",
            "teaching steps include learner-facing explanation, caption, checkpoint, and supported visual recipe",
            "known high-impact content/visual contradictions are rejected",
        ] if not errors else [],
        "topic_count": len(steps), "source_chunk_count": len(allowed_chunk_ids),
        "cited_chunk_count": len(cited_chunk_ids), "uncited_chunk_count": len(missing_citations),
    }


def make_run_id(source_id: str, chapter: str, curriculum_version: str, fingerprint: str) -> str:
    """Deterministic ID supports safe retries without duplicate chapter runs."""
    raw = "|".join((source_id, chapter.strip(), curriculum_version, fingerprint))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
