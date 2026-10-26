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
Use only the source evidence below for curriculum-specific claims. Do not invent page
references, official learning outcomes, facts, or examples. Clearly label any everyday
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
