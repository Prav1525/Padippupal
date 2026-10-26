"""Source-grounded syllabus synthesis pipeline.

The pipeline extracts page-level evidence and embedded figures into a board/year/
medium/standard/subject hierarchy. It deliberately emits reviewable evidence
packages, not an assertion that an LLM has understood or verified a syllabus.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field, ValidationError

MAX_PDF_BYTES = 25 * 1024 * 1024
DEFAULT_OUTPUT_ROOT = Path(os.getenv("PADIPPUPAL_SYLLABUS_ROOT", "syllabus_library"))
router = APIRouter(prefix="/admin/syllabus", tags=["syllabus-synthesis"])


class CurriculumScope(BaseModel):
    board: str = Field(min_length=2, max_length=100)
    academic_year: str = Field(pattern=r"^\d{4}-\d{2,4}$")
    medium: str = Field(min_length=2, max_length=60)
    standard: str = Field(min_length=1, max_length=30)
    subject: str = Field(min_length=2, max_length=80)
    textbook_title: str = Field(min_length=2, max_length=200)
    edition: str = Field(min_length=1, max_length=80)
    source_url: str | None = Field(default=None, max_length=2048)
    source_authority: str = Field(min_length=2, max_length=200)
    rights_reviewed: bool = False
    rights_note: str = Field(default="", max_length=2000)


class SyllabusTopic(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    chapter: str = Field(default="", max_length=240)
    keywords: list[str] = Field(default_factory=list, max_length=40)
    syllabus_reference: str = Field(default="", max_length=500)


def slug(value: str) -> str:
    """Return a filesystem-safe, stable path segment."""
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip()).strip(".-_").lower()
    return value[:80] or "unknown"


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_pages(pdf_path: Path) -> list[dict[str, Any]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency installed in backend
        raise RuntimeError("Install backend requirements to extract PDF text") from exc
    reader = PdfReader(str(pdf_path))
    pages: list[dict[str, Any]] = []
    for number, page in enumerate(reader.pages, start=1):
        text = _normalise(page.extract_text() or "")
        pages.append({
            "page": number,
            "text": text,
            "word_count": len(text.split()),
            "needs_ocr": not bool(text),
        })
    if not pages:
        raise ValueError("PDF contains no readable pages")
    return pages


def _extract_images(pdf_path: Path, image_dir: Path) -> list[dict[str, Any]]:
    """Extract embedded PDF images when PyMuPDF is installed; preserve page provenance."""
    try:
        import fitz
    except ImportError:
        return []
    images: list[dict[str, Any]] = []
    document = fitz.open(str(pdf_path))
    try:
        for page_index in range(len(document)):
            page = document[page_index]
            for image_index, image_info in enumerate(page.get_images(full=True), start=1):
                xref = image_info[0]
                extracted = document.extract_image(xref)
                data = extracted.get("image", b"")
                if not data:
                    continue
                ext = re.sub(r"[^a-z0-9]", "", extracted.get("ext", "png").lower()) or "png"
                digest = hashlib.sha256(data).hexdigest()[:12]
                filename = f"page-{page_index + 1:04d}-image-{image_index:02d}-{digest}.{ext}"
                (image_dir / filename).write_bytes(data)
                images.append({
                    "id": f"p{page_index + 1}-i{image_index}",
                    "path": f"images/{filename}",
                    "page": page_index + 1,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "width": extracted.get("width"),
                    "height": extracted.get("height"),
                    "caption": "",
                    "topic_ids": [],
                    "review_status": "needs_topic_match",
                })
    finally:
        document.close()
    return images


def map_topics_to_pages(
    topics: list[SyllabusTopic | dict[str, Any]],
    pages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Map topic labels/keywords to page evidence with transparent lexical scores."""
    results: list[dict[str, Any]] = []
    for raw_topic in topics:
        topic = raw_topic if isinstance(raw_topic, SyllabusTopic) else SyllabusTopic.model_validate(raw_topic)
        terms = {t.casefold() for t in [topic.title, *topic.keywords] if len(t.strip()) >= 2}
        scored = []
        for page in pages:
            text = str(page.get("text", ""))
            folded = text.casefold()
            matches = sorted(term for term in terms if term in folded)
            if matches:
                scored.append({
                    "page": int(page["page"]),
                    "matched_terms": matches,
                    "score": round(len(matches) / max(len(terms), 1), 3),
                    "evidence_excerpt": text[:1200],
                })
        scored.sort(key=lambda item: (-item["score"], item["page"]))
        results.append({
            "topic_id": topic.id,
            "topic_title": topic.title,
            "chapter": topic.chapter,
            "syllabus_reference": topic.syllabus_reference,
            "page_matches": scored,
            "coverage_status": "evidence_found" if scored else "missing_source",
            "synthesis_status": "needs_review",
            "review_notes": [
                "Lexical matches are candidate evidence, not proof of syllabus completeness.",
                "Create and approve the teaching synthesis only after checking source pages.",
            ],
        })
    return results


def build_synthesis_prompt(scope: CurriculumScope, topic_package: dict[str, Any]) -> str:
    """Create a repeatable prompt contract for a separately configured synthesis model."""
    evidence = topic_package.get("page_matches", [])
    evidence_text = "\n".join(
        f"[source page {item['page']}; matched terms: {', '.join(item['matched_terms'])}] "
        f"{item['evidence_excerpt']}" for item in evidence
    ) or "No matching source evidence was found."
    return f"""Create an original, age-appropriate teaching synthesis for this syllabus topic.
CURRICULUM: board={scope.board}; year={scope.academic_year}; medium={scope.medium};
standard={scope.standard}; subject={scope.subject}; textbook={scope.textbook_title};
edition={scope.edition}.
TOPIC: {topic_package.get('topic_title', '')}; chapter={topic_package.get('chapter', '')}.
Use only the source evidence below for curriculum-specific claims. Do not invent page references,
official learning outcomes, facts, or examples. Clearly label any everyday
analogy as an analogy. Cover definitions, concept relationships, prerequisites, examples,
likely misconceptions, and 2-3 understanding checks. Cite the source page for each
supported claim. Explicitly list gaps and uncertainty. If evidence is absent or insufficient,
return needs_review rather than pretending the topic is complete.
SOURCE EVIDENCE:
{evidence_text}"""


def render_topic_review_sheet(topic_package: dict[str, Any]) -> str:
    """Render an auditable topic synthesis worksheet, never a falsely approved lesson."""
    lines = [
        f"# {topic_package.get('topic_title', 'Untitled topic')}",
        "",
        f"- Topic ID: `{topic_package.get('topic_id', '')}`",
        f"- Chapter: {topic_package.get('chapter', '') or 'Not supplied'}",
        f"- Syllabus reference: {topic_package.get('syllabus_reference', '') or 'Not supplied'}",
        f"- Evidence status: **{topic_package.get('coverage_status', 'missing_source')}**",
        "- Synthesis status: **needs_review**",
        "",
        "## Source evidence to review",
    ]
    matches = topic_package.get("page_matches", [])
    if not matches:
        lines += ["", "No candidate source pages matched this topic. Obtain the official source or revise the topic keywords."]
    else:
        for item in matches:
            lines += [
                "",
                f"### PDF page {item['page']} (lexical score {item['score']})",
                f"Matched terms: {', '.join(item['matched_terms'])}",
                "",
                item["evidence_excerpt"],
            ]
    lines += [
        "",
        "## Required synthesis review",
        "- [ ] Verify this topic is required by the selected official syllabus.",
        "- [ ] Check every factual claim against the cited source pages.",
        "- [ ] Write an original, age-appropriate explanation; do not copy textbook passages.",
        "- [ ] Add definitions, concept relationships, prerequisites and worked examples.",
        "- [ ] Add likely misconceptions and 2-3 understanding checks.",
        "- [ ] Match relevant figures to this topic and verify captions/page numbers.",
        "- [ ] Record missing evidence and approve only after review.",
        "",
        "## Synthesis prompt contract",
        "",
        topic_package.get("synthesis_prompt", "No prompt generated."),
        "",
        "This file is a review worksheet, not an approved teaching synthesis.",
        "",
    ]
    return "\n".join(lines)



def _synthesis_db_connect():
    """Connect to the same curriculum database used by backend/app.py."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        import psycopg
        from psycopg.rows import dict_row

        class _PostgresCompat:
            def __init__(self, raw):
                self.raw = raw
            def execute(self, sql, params=()):
                return self.raw.execute(sql.replace("?", "%s"), params)
            def commit(self):
                self.raw.commit()
            def close(self):
                self.raw.close()

        return _PostgresCompat(psycopg.connect(database_url, connect_timeout=10, row_factory=dict_row))
    import sqlite3
    db_path = Path(os.getenv("PADIPPUPAL_DB", "padippupal_curriculum.sqlite3"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_synthesis_schema(conn) -> None:
    """Keep durable synthesis data in the existing PadippuPal curriculum database."""
    statements = [
        """CREATE TABLE IF NOT EXISTS syllabus_sources (
            source_id TEXT PRIMARY KEY, board TEXT NOT NULL, academic_year TEXT NOT NULL,
            medium TEXT NOT NULL, standard TEXT NOT NULL, subject TEXT NOT NULL,
            textbook_title TEXT NOT NULL, edition TEXT NOT NULL, source_authority TEXT NOT NULL,
            source_url TEXT NOT NULL DEFAULT '', source_sha256 TEXT NOT NULL,
            rights_reviewed INTEGER NOT NULL, rights_note TEXT NOT NULL,
            page_count INTEGER NOT NULL, overall_status TEXT NOT NULL,
            manifest_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS syllabus_source_pages (
            source_id TEXT NOT NULL REFERENCES syllabus_sources(source_id) ON DELETE CASCADE,
            page_no INTEGER NOT NULL, page_text TEXT NOT NULL, needs_ocr INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(source_id, page_no)
        )""",
        """CREATE TABLE IF NOT EXISTS syllabus_source_images (
            source_id TEXT NOT NULL REFERENCES syllabus_sources(source_id) ON DELETE CASCADE,
            image_id TEXT NOT NULL, page_no INTEGER NOT NULL, image_json TEXT NOT NULL,
            PRIMARY KEY(source_id, image_id)
        )""",
        """CREATE TABLE IF NOT EXISTS syllabus_topics (
            source_id TEXT NOT NULL REFERENCES syllabus_sources(source_id) ON DELETE CASCADE,
            topic_id TEXT NOT NULL, chapter TEXT NOT NULL DEFAULT '', topic_title TEXT NOT NULL,
            syllabus_reference TEXT NOT NULL DEFAULT '', coverage_status TEXT NOT NULL,
            evidence_json TEXT NOT NULL, synthesis_status TEXT NOT NULL DEFAULT 'needs_review',
            PRIMARY KEY(source_id, topic_id)
        )""",
        """CREATE TABLE IF NOT EXISTS syllabus_topic_syntheses (
            source_id TEXT NOT NULL, topic_id TEXT NOT NULL, latest_status TEXT NOT NULL,
            latest_round INTEGER NOT NULL, synthesis_json TEXT, issues_json TEXT NOT NULL,
            approved INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(source_id, topic_id),
            FOREIGN KEY(source_id, topic_id) REFERENCES syllabus_topics(source_id, topic_id) ON DELETE CASCADE
        )""",
        """CREATE TABLE IF NOT EXISTS syllabus_synthesis_rounds (
            source_id TEXT NOT NULL, topic_id TEXT NOT NULL, round_no INTEGER NOT NULL,
            draft_json TEXT, validation_issues_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(source_id, topic_id, round_no),
            FOREIGN KEY(source_id, topic_id) REFERENCES syllabus_topics(source_id, topic_id) ON DELETE CASCADE
        )""",
    ]
    for statement in statements:
        conn.execute(statement)


def _persist_source_package(manifest: dict[str, Any], pages: list[dict[str, Any]]) -> None:
    """Persist the book hierarchy, page evidence, topic map and image provenance in app DB."""
    conn = _synthesis_db_connect()
    try:
        _ensure_synthesis_schema(conn)
        scope = manifest["scope"]
        conn.execute(
            """INSERT INTO syllabus_sources
            (source_id, board, academic_year, medium, standard, subject, textbook_title, edition,
             source_authority, source_url, source_sha256, rights_reviewed, rights_note,
             page_count, overall_status, manifest_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET manifest_json=excluded.manifest_json,
             overall_status=excluded.overall_status, page_count=excluded.page_count""",
            (manifest["source_id"], scope["board"], scope["academic_year"], scope["medium"],
             scope["standard"], scope["subject"], scope["textbook_title"], scope["edition"],
             scope["source_authority"], scope.get("source_url") or "", manifest["source_sha256"],
             int(bool(scope.get("rights_reviewed"))), scope.get("rights_note", ""),
             manifest["page_count"], manifest["overall_status"],
             json.dumps(manifest, ensure_ascii=False)),
        )
        for page in pages:
            conn.execute(
                """INSERT INTO syllabus_source_pages(source_id, page_no, page_text, needs_ocr)
                VALUES (?, ?, ?, ?) ON CONFLICT(source_id, page_no) DO UPDATE SET
                page_text=excluded.page_text, needs_ocr=excluded.needs_ocr""",
                (manifest["source_id"], page["page"], page.get("text", ""), int(bool(page.get("needs_ocr")))),
            )
        for image in manifest.get("images", []):
            conn.execute(
                """INSERT INTO syllabus_source_images(source_id, image_id, page_no, image_json)
                VALUES (?, ?, ?, ?) ON CONFLICT(source_id, image_id) DO UPDATE SET
                page_no=excluded.page_no, image_json=excluded.image_json""",
                (manifest["source_id"], image["id"], image["page"], json.dumps(image, ensure_ascii=False)),
            )
        for topic in manifest.get("topics", []):
            conn.execute(
                """INSERT INTO syllabus_topics
                (source_id, topic_id, chapter, topic_title, syllabus_reference, coverage_status, evidence_json, synthesis_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id, topic_id) DO UPDATE SET
                chapter=excluded.chapter, topic_title=excluded.topic_title,
                syllabus_reference=excluded.syllabus_reference, coverage_status=excluded.coverage_status,
                evidence_json=excluded.evidence_json, synthesis_status=excluded.synthesis_status""",
                (manifest["source_id"], topic["topic_id"], topic.get("chapter", ""),
                 topic["topic_title"], topic.get("syllabus_reference", ""), topic["coverage_status"],
                 json.dumps(topic, ensure_ascii=False), topic.get("synthesis_status", "needs_review")),
            )
        conn.commit()
    finally:
        conn.close()


def _persist_synthesis_result(source_id: str, topic_id: str, result: dict[str, Any]) -> None:
    """Store every synthesis round and the latest unapproved topic package in the curriculum DB."""
    conn = _synthesis_db_connect()
    try:
        _ensure_synthesis_schema(conn)
        rounds = result.get("rounds", [])
        for item in rounds:
            conn.execute(
                """INSERT INTO syllabus_synthesis_rounds
                (source_id, topic_id, round_no, draft_json, validation_issues_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_id, topic_id, round_no) DO UPDATE SET
                draft_json=excluded.draft_json, validation_issues_json=excluded.validation_issues_json""",
                (source_id, topic_id, item["round"],
                 json.dumps(item.get("draft"), ensure_ascii=False) if item.get("draft") is not None else None,
                 json.dumps(item.get("validation_issues", []), ensure_ascii=False)),
            )
        conn.execute(
            """INSERT INTO syllabus_topic_syntheses
            (source_id, topic_id, latest_status, latest_round, synthesis_json, issues_json, approved, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
            ON CONFLICT(source_id, topic_id) DO UPDATE SET
            latest_status=excluded.latest_status, latest_round=excluded.latest_round,
            synthesis_json=excluded.synthesis_json, issues_json=excluded.issues_json,
            approved=0, updated_at=CURRENT_TIMESTAMP""",
            (source_id, topic_id, result.get("status", "needs_review"), len(rounds),
             json.dumps(result.get("synthesis"), ensure_ascii=False) if result.get("synthesis") is not None else None,
             json.dumps(result.get("issues", []), ensure_ascii=False)),
        )
        conn.execute(
            """UPDATE syllabus_topics SET synthesis_status=?
            WHERE source_id=? AND topic_id=?""",
            (result.get("status", "needs_review"), source_id, topic_id),
        )
        conn.commit()
    finally:
        conn.close()


def create_source_package(
    pdf_path: Path,
    scope: CurriculumScope,
    topics: list[SyllabusTopic],
    output_root: Path = DEFAULT_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Extract a PDF into a versioned hierarchy and emit topic evidence packages."""
    if not scope.rights_reviewed or not scope.rights_note.strip():
        raise PermissionError(
            "Source ingestion is blocked until rights_reviewed=true and a rights_note is supplied"
        )
    if pdf_path.suffix.casefold() != ".pdf" or not pdf_path.is_file():
        raise ValueError("A readable PDF file is required")
    if pdf_path.stat().st_size > MAX_PDF_BYTES:
        raise ValueError("PDF exceeds the 25 MiB ingestion limit")

    source_id = hashlib.sha256(
        f"{scope.model_dump_json()}:{pdf_path.name}:{pdf_path.stat().st_size}".encode()
    ).hexdigest()[:16]
    base = (
        output_root / slug(scope.board) / slug(scope.academic_year) / slug(scope.medium)
        / f"standard-{slug(scope.standard)}" / slug(scope.subject)
        / f"{slug(scope.textbook_title)}-{slug(scope.edition)}" / source_id
    )
    if base.exists():
        raise FileExistsError("This source package already exists; use a new edition or remove it explicitly")
    base.mkdir(parents=True, exist_ok=False)
    try:
        source_copy = base / "source.pdf"
        shutil.copyfile(pdf_path, source_copy)
        pages = _extract_pages(source_copy)
        (base / "pages").mkdir()
        for page in pages:
            (base / "pages" / f"page-{page['page']:04d}.txt").write_text(
                page["text"], encoding="utf-8"
            )
        image_dir = base / "images"
        image_dir.mkdir()
        images = _extract_images(source_copy, image_dir)
        topic_packages = map_topics_to_pages(topics, pages)
        for topic_package in topic_packages:
            topic_package["synthesis_prompt"] = build_synthesis_prompt(scope, topic_package)
        manifest = {
            "schema_version": 1,
            "source_id": source_id,
            "scope": scope.model_dump(),
            "source_filename": pdf_path.name,
            "source_sha256": hashlib.sha256(source_copy.read_bytes()).hexdigest(),
            "page_count": len(pages),
            "pages_needing_ocr": [p["page"] for p in pages if p["needs_ocr"]],
            "images": images,
            "topics": topic_packages,
            "overall_status": "needs_review",
            "limitations": [
                "Keyword matching identifies candidate evidence; it does not prove full syllabus coverage.",
                "Scanned pages need OCR before their content can be matched to topics.",
                "Images need human or model-assisted topic/caption review before teaching use.",
                "Synthesis output must be reviewed against source pages before approval.",
            ],
        }
        (base / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        for package in topic_packages:
            topic_dir = base / "topics" / slug(package["topic_id"])
            topic_dir.mkdir(parents=True, exist_ok=True)
            (topic_dir / "evidence.json").write_text(
                json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            (topic_dir / "synthesis-review.md").write_text(
                render_topic_review_sheet(package), encoding="utf-8"
            )
        return {"package_path": str(base), "manifest": manifest}
    except Exception:
        shutil.rmtree(base, ignore_errors=True)
        raise


def _require_admin(x_admin_token: str | None) -> None:
    expected = os.getenv("PADIPPUPAL_ADMIN_TOKEN", "").strip()
    if not expected or not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="Admin authentication required")


@router.post("/ingest-pdf")
async def ingest_syllabus_pdf(
    metadata_json: str = Form(...),
    syllabus_json: str = Form(...),
    file: UploadFile = File(...),
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a review-only source package; no AI-generated content is auto-approved."""
    _require_admin(x_admin_token)
    try:
        scope = CurriculumScope.model_validate_json(metadata_json)
        raw_topics = json.loads(syllabus_json)
        if not isinstance(raw_topics, list) or not raw_topics:
            raise ValueError("syllabus_json must be a non-empty JSON array of topics")
        topics = [SyllabusTopic.model_validate(item) for item in raw_topics]
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid source metadata or syllabus topics: {exc}") from exc

    if not file.filename or not file.filename.casefold().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF textbooks and syllabus files are supported")
    payload = await file.read(MAX_PDF_BYTES + 1)
    if not payload or len(payload) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="PDF must be non-empty and at most 25 MiB")
    temp_dir = DEFAULT_OUTPUT_ROOT / ".incoming"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{uuid.uuid4().hex}.pdf"
    try:
        temp_path.write_bytes(payload)
        result = create_source_package(temp_path, scope, topics)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)
    return {
        "source_id": result["manifest"]["source_id"],
        "package_path": result["package_path"],
        "page_count": result["manifest"]["page_count"],
        "image_count": len(result["manifest"]["images"]),
        "topic_count": len(result["manifest"]["topics"]),
        "topics_missing_source": [
            item["topic_id"] for item in result["manifest"]["topics"]
            if item["coverage_status"] == "missing_source"
        ],
        "pages_needing_ocr": result["manifest"]["pages_needing_ocr"],
        "status": "needs_review",
    }



# ---------- Iterative, evidence-checked synthesis core ----------

SYNTHESIS_REQUIRED_SECTIONS = (
    "explanation",
    "key_points",
    "worked_examples",
    "misconceptions",
    "understanding_checks",
    "source_citations",
    "gaps",
)


def _validate_synthesis_draft(draft: Any, allowed_pages: set[int]) -> list[str]:
    """Return concrete quality-gate failures; never silently approve model output."""
    issues: list[str] = []
    if not isinstance(draft, dict):
        return ["draft must be a JSON object"]
    for section in SYNTHESIS_REQUIRED_SECTIONS:
        value = draft.get(section)
        if value is None or value == "" or value == []:
            issues.append(f"missing_required_section:{section}")
    citations = draft.get("source_citations", [])
    if not isinstance(citations, list):
        issues.append("source_citations_must_be_a_list")
    else:
        for citation in citations:
            if not isinstance(citation, dict):
                issues.append("citation_must_be_an_object")
                continue
            page = citation.get("page")
            if not isinstance(page, int) or page not in allowed_pages:
                issues.append(f"citation_page_not_in_evidence:{page}")
            if not str(citation.get("claim", "")).strip():
                issues.append("citation_missing_claim")
    checks = draft.get("understanding_checks")
    if isinstance(checks, list) and not 2 <= len(checks) <= 3:
        issues.append("understanding_checks_must_contain_2_or_3_items")
    return issues


def run_iterative_synthesis(
    scope: CurriculumScope,
    topic_package: dict[str, Any],
    generate_json: Any,
    *,
    max_rounds: int = 3,
) -> dict[str, Any]:
    """Run draft -> critique/refine passes through an injected model adapter.

    generate_json(prompt) must return a parsed JSON object. The engine never
    approves a synthesis automatically: even a passing draft is 'ready_for_review'.
    Each round is retained so omissions and refinements are auditable.
    """
    if not 1 <= max_rounds <= 5:
        raise ValueError("max_rounds must be between 1 and 5")
    evidence = topic_package.get("page_matches") or []
    allowed_pages = {
        int(item["page"]) for item in evidence
        if isinstance(item, dict) and str(item.get("page", "")).isdigit()
    }
    if not allowed_pages:
        return {
            "topic_id": topic_package.get("topic_id", ""),
            "status": "blocked_missing_evidence",
            "rounds": [],
            "synthesis": None,
            "issues": ["No candidate source pages exist; synthesis is blocked."],
        }

    history: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    issues: list[str] = []
    for round_number in range(1, max_rounds + 1):
        if previous is None:
            instruction = (
                "Create the first original, age-appropriate topic synthesis as strict JSON. "
                "Include: explanation, key_points, worked_examples, misconceptions, "
                "understanding_checks (2-3 items), source_citations (each has page and claim), "
                "and gaps. Cite only the supplied evidence pages. Do not reproduce long "
                "textbook passages; use your own words."
            )
        else:
            instruction = (
                "Improve the previous draft using the validation issues below. Keep every "
                "curriculum-specific claim grounded in the supplied pages. Return the complete "
                "revised JSON object, not a patch. If the evidence cannot support a claim, "
                "move it to gaps instead of guessing. Issues: " + json.dumps(issues)
            )
        prompt = build_synthesis_prompt(scope, topic_package) + (
            "\n\nITERATION " + str(round_number) + "\n" + instruction
        )
        if previous is not None:
            prompt += "\nPREVIOUS DRAFT:\n" + json.dumps(previous, ensure_ascii=False)
        candidate = generate_json(prompt)
        issues = _validate_synthesis_draft(candidate, allowed_pages)
        history.append({
            "round": round_number,
            "draft": candidate,
            "validation_issues": issues,
        })
        previous = candidate if isinstance(candidate, dict) else None
        if not issues:
            break

    passed = bool(history) and not history[-1]["validation_issues"]
    return {
        "topic_id": topic_package.get("topic_id", ""),
        "status": "ready_for_review" if passed else "needs_review",
        "rounds": history,
        "synthesis": previous,
        "issues": history[-1]["validation_issues"] if history else ["No synthesis rounds completed."],
        "approved": False,
        "approval_note": "Human source-page review is required before publishing to the tutor.",
    }



class SynthesisRequest(BaseModel):
    max_rounds: int = Field(default=3, ge=1, le=5)


def _gemini_json_generator():
    """Build a Gemini JSON adapter using the backend's existing secret/model settings."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="Syllabus synthesis needs GEMINI_API_KEY configured on the backend.",
        )
    model = os.getenv("PADIPPUPAL_GEMINI_CHAT_MODEL", "gemini-2.5-flash").strip()

    def generate(prompt: str) -> dict[str, Any]:
        body = json.dumps({
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.15,
                "maxOutputTokens": 5000,
            },
        }).encode("utf-8")
        request = urllib.request.Request(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            + model + ":generateContent",
            data=body,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
            raw = "".join(
                part.get("text", "")
                for part in result["candidates"][0]["content"]["parts"]
                if isinstance(part, dict)
            )
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError("Gemini synthesis response must be a JSON object")
            return parsed
        except urllib.error.HTTPError as exc:
            detail = exc.read(600).decode("utf-8", errors="replace")
            raise HTTPException(
                status_code=502,
                detail=f"Gemini synthesis request failed with HTTP {exc.code}: {detail[:240]}",
            ) from exc
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an invalid JSON synthesis draft.",
            ) from exc
        except urllib.error.URLError as exc:
            raise HTTPException(
                status_code=503,
                detail="Gemini synthesis could not reach the configured provider.",
            ) from exc

    return generate


@router.post("/sources/{source_id}/topics/{topic_id}/synthesize")
def synthesize_source_topic(
    source_id: str,
    topic_id: str,
    payload: SynthesisRequest,
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Run bounded multi-pass synthesis for an ingested topic; always leaves it unapproved."""
    _require_admin(x_admin_token)
    if not re.fullmatch(r"[a-f0-9]{16}", source_id):
        raise HTTPException(status_code=404, detail="Source package not found")
    safe_topic_id = slug(topic_id)
    if safe_topic_id == "unknown":
        raise HTTPException(status_code=422, detail="Topic id must contain ASCII letters or digits")
    root = DEFAULT_OUTPUT_ROOT
    matches = [path for path in root.rglob(source_id) if path.is_dir() and path.name == source_id]
    if len(matches) != 1:
        raise HTTPException(status_code=404, detail="Source package not found or ambiguous")
    base = matches[0]
    try:
        manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Source manifest is missing or unreadable") from exc
    topic = next(
        (item for item in manifest.get("topics", []) if slug(str(item.get("topic_id", ""))) == safe_topic_id),
        None,
    )
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found in source package")
    if topic.get("coverage_status") != "evidence_found" or not topic.get("page_matches"):
        return {
            "source_id": source_id,
            "topic_id": topic.get("topic_id"),
            "status": "blocked_missing_evidence",
            "synthesis": None,
            "approved": False,
            "issues": ["No candidate source pages exist; synthesis is blocked."],
        }
    scope = CurriculumScope.model_validate(manifest["scope"])
    result = run_iterative_synthesis(
        scope, topic, _gemini_json_generator(), max_rounds=payload.max_rounds
    )
    topic_dir = base / "topics" / safe_topic_id
    topic_dir.mkdir(parents=True, exist_ok=True)
    output_path = topic_dir / "synthesis.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "source_id": source_id,
        "topic_id": topic.get("topic_id"),
        "status": result["status"],
        "rounds_completed": len(result.get("rounds", [])),
        "synthesis_path": str(output_path),
        "synthesis": result.get("synthesis"),
        "issues": result.get("issues", []),
        "approved": False,
        "review_required": True,
    }
