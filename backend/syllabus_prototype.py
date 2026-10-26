"""Small admin-only browser prototype for testing synthesis against indexed Class 6 books."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from syllabus_synthesis import (
    DEFAULT_OUTPUT_ROOT,
    SynthesisRequest,
    _gemini_json_generator,
    _persist_synthesis_result,
    _synthesis_db_connect,
    create_package_from_existing_source,
    slug,
    run_iterative_synthesis,
    CurriculumScope,
    SyllabusTopic,
)

router = APIRouter(prefix="/admin/syllabus-prototype", tags=["syllabus-prototype"])


def _authorize(token: str | None) -> None:
    expected = os.getenv("PADIPPUPAL_ADMIN_TOKEN", "").strip()
    if not expected or not token or token != expected:
        raise HTTPException(status_code=401, detail="Admin token required")


class PackageRequest(BaseModel):
    topic_title: str = Field(min_length=2, max_length=240)
    keywords: list[str] = Field(default_factory=list, max_length=30)
    chapter: str = Field(default="", max_length=240)


def _find_manifest(package_id: str) -> tuple[Path, dict[str, Any]]:
    if not re.fullmatch(r"[a-f0-9]{16}", package_id):
        raise HTTPException(status_code=404, detail="Package not found")
    matches = [p for p in DEFAULT_OUTPUT_ROOT.rglob("manifest.json")
               if p.parent.name == package_id and p.is_file()]
    if len(matches) != 1:
        raise HTTPException(status_code=404, detail="Package not found or ambiguous")
    try:
        return matches[0].parent, json.loads(matches[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Package manifest is unreadable") from exc


@router.get("", response_class=HTMLResponse)
def prototype_page() -> str:
    """Serve a lightweight test UI; all data-changing APIs still require the admin token."""
    return _HTML


@router.get("/api/sources")
def list_existing_books(x_admin_token: str | None = Header(default=None)) -> dict[str, Any]:
    """List real, ready Class 6 Science/Maths sources that already have stored text."""
    _authorize(x_admin_token)
    conn = _synthesis_db_connect()
    try:
        rows = conn.execute(
            """SELECT s.id, s.board, s.academic_year, s.class_level, s.subject, s.medium,
                      s.edition, s.title, s.status, s.page_count,
                      LENGTH(sc.content) AS stored_characters,
                      (SELECT COUNT(*) FROM chunks c WHERE c.source_id=s.id) AS chunk_count
               FROM sources s
               JOIN source_content sc ON sc.source_id=s.id
               WHERE s.status='ready' AND s.class_level=6
                 AND LOWER(s.subject) IN ('science', 'mathematics')
               ORDER BY s.subject, s.title"""
        ).fetchall()
        return {"sources": [dict(row) for row in rows]}
    finally:
        conn.close()



@router.get("/api/sources/{existing_source_id}/preview")
def preview_existing_book(
    existing_source_id: str,
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Inspect page-marked text from the existing indexed source before synthesis."""
    _authorize(x_admin_token)
    from syllabus_synthesis import _read_existing_curriculum_source

    try:
        source, pages = _read_existing_curriculum_source(existing_source_id)
    except HTTPException:
        raise
    return {
        "source_id": existing_source_id,
        "title": source.get("title"),
        "subject": source.get("subject"),
        "status": source.get("status"),
        "page_count": len(pages),
        "pages_with_text": sum(bool(str(page.get("text", "")).strip()) for page in pages),
        "pages_needing_ocr": [int(page["page"]) for page in pages if page.get("needs_ocr")],
        "preview_pages": [{
            "page": int(page["page"]),
            "word_count": int(page.get("word_count", 0)),
            "text_preview": str(page.get("text", ""))[:1800],
        } for page in pages[:3]],
        "rights_reviewed": False,
        "approved": False,
    }


@router.post("/api/sources/{existing_source_id}/package")
def create_test_package(
    existing_source_id: str,
    payload: PackageRequest,
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Create a one-topic test package from the exact text already stored in the DB."""
    _authorize(x_admin_token)
    topic_id = slug(payload.topic_title)
    if topic_id == "unknown":
        raise HTTPException(status_code=422, detail="Use an ASCII topic title for the prototype topic ID")
    conn = _synthesis_db_connect()
    try:
        row = conn.execute(
            "SELECT board, academic_year, class_level, subject, medium, title FROM sources WHERE id=? AND status='ready'",
            (existing_source_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Ready existing book source not found")
        if str(row["subject"]).casefold() not in {"science", "mathematics"} or int(row["class_level"]) != 6:
            raise HTTPException(status_code=422, detail="Prototype is currently limited to Class 6 Science and Mathematics")
    finally:
        conn.close()

    topic = SyllabusTopic(
        id=topic_id,
        title=payload.topic_title,
        chapter=payload.chapter or str(row["title"]),
        keywords=payload.keywords,
    )
    try:
        result = create_package_from_existing_source(existing_source_id, [topic], output_root=DEFAULT_OUTPUT_ROOT)
    except HTTPException:
        raise
    except (PermissionError, ValueError, FileExistsError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    manifest = result["manifest"]
    item = manifest["topics"][0]
    return {
        "source_id": manifest["source_id"],
        "existing_curriculum_source_id": existing_source_id,
        "book_title": row["title"],
        "page_count": manifest["page_count"],
        "topic": {
            "topic_id": item["topic_id"],
            "topic_title": item["topic_title"],
            "coverage_status": item["coverage_status"],
            "matched_page_count": len(item.get("page_matches", [])),
            "page_matches": item.get("page_matches", [])[:8],
        },
        "status": "needs_review",
        "approved": False,
        "rights_reviewed": False,
    }


@router.get("/api/packages/{package_id}")
def get_test_package(
    package_id: str,
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _authorize(x_admin_token)
    _base, manifest = _find_manifest(package_id)
    return {
        "source_id": package_id,
        "book_title": manifest.get("scope", {}).get("textbook_title", ""),
        "page_count": manifest.get("page_count", 0),
        "topics": [{
            "topic_id": item.get("topic_id"),
            "topic_title": item.get("topic_title"),
            "coverage_status": item.get("coverage_status"),
            "matched_page_count": len(item.get("page_matches", [])),
            "page_matches": item.get("page_matches", [])[:8],
        } for item in manifest.get("topics", [])],
        "status": manifest.get("overall_status", "needs_review"),
        "approved": False,
    }


@router.post("/api/packages/{package_id}/topics/{topic_id}/synthesize")
def synthesize_test_topic(
    package_id: str,
    topic_id: str,
    payload: SynthesisRequest,
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    _authorize(x_admin_token)
    base, manifest = _find_manifest(package_id)
    topic = next((item for item in manifest.get("topics", [])
                  if slug(str(item.get("topic_id", ""))) == slug(topic_id)), None)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found in test package")
    if topic.get("coverage_status") != "evidence_found" or not topic.get("page_matches"):
        return {
            "source_id": package_id, "topic_id": topic_id,
            "status": "blocked_missing_evidence", "synthesis": None,
            "approved": False, "issues": ["No candidate source pages exist; synthesis is blocked."],
        }
    scope = CurriculumScope.model_validate(manifest["scope"])
    result = run_iterative_synthesis(scope, topic, _gemini_json_generator(), max_rounds=payload.max_rounds)
    topic_dir = base / "topics" / slug(str(topic.get("topic_id", "")))
    topic_dir.mkdir(parents=True, exist_ok=True)
    (topic_dir / "synthesis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _persist_synthesis_result(package_id, str(topic.get("topic_id", "")), result)
    return {
        "source_id": package_id,
        "topic_id": topic.get("topic_id"),
        "status": result["status"],
        "rounds_completed": len(result.get("rounds", [])),
        "synthesis": result.get("synthesis"),
        "issues": result.get("issues", []),
        "approved": False,
        "review_required": True,
    }


_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PadippuPal · Syllabus synthesis prototype</title>
<style>
:root{font-family:system-ui,sans-serif;color:#17212b;background:#f5f7fa}body{margin:0 auto;max-width:1000px;padding:20px}
h1{font-size:1.7rem;margin-bottom:.2rem}.muted{color:#596674}.panel{background:white;border:1px solid #dce3ea;border-radius:14px;padding:18px;margin:16px 0}
label{display:block;font-weight:650;margin:12px 0 5px}input,select,textarea,button{font:inherit;padding:10px;border:1px solid #b8c4d0;border-radius:8px;box-sizing:border-box;width:100%}
button{background:#145c49;color:white;border:0;font-weight:700;cursor:pointer;margin-top:12px}button.secondary{background:#34475a}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.status{padding:10px;background:#eef4f1;border-radius:8px;white-space:pre-wrap;overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:12px;border-radius:8px;max-height:450px;overflow:auto}.small{font-size:.9rem}
@media(max-width:650px){.grid{grid-template-columns:1fr}body{padding:12px}}
</style></head><body>
<h1>PadippuPal · Syllabus synthesis lab</h1>
<p class="muted">Prototype using existing Class 6 Science and Mathematics text. Imported content and generated lessons remain review-only.</p>
<section class="panel">
<label for="token">Admin token (held only in this page session)</label><input id="token" type="password" autocomplete="off" placeholder="PADIPPUPAL_ADMIN_TOKEN">
<button id="load">Load existing books from database</button>
<div id="status" class="status" style="margin-top:12px">Not connected.</div>
</section>
<section class="panel">
<div class="grid"><div><label for="book">Existing indexed book/chapter</label><select id="book"></select></div>
<div><label for="topic">Test topic</label><input id="topic" value="Patterns in Mathematics"></div></div>
<label for="keywords">Keywords (comma separated)</label><input id="keywords" value="patterns, number patterns, rules, mathematics">
<label for="chapter">Chapter label (optional)</label><input id="chapter" placeholder="Use selected book title if blank">
<button id="preview" class="secondary">Preview extracted pages first</button>\n<button id="prepare">Build evidence package from stored book text</button>
<button id="wholeChapter" class="secondary">Build whole-chapter package (all pages)</button>
<div id="evidence"></div>
</section>
<section class="panel">
<h2>Generate review draft</h2>
<p class="muted small">Requires GEMINI_API_KEY configured on the backend. This will not approve or publish the result.</p>
<label for="rounds">Maximum refinement rounds</label><select id="rounds"><option>1</option><option selected>3</option><option>5</option></select>
<button id="synthesize">Synthesize selected topic</button>
<div id="result"></div>
</section>
<script>
let activePackage=null, activeTopic=null;
const $=id=>document.getElementById(id);
const auth=()=>({'x-admin-token':$('token').value.trim(),'Content-Type':'application/json'});
async function call(url,options={}){const r=await fetch(url,{...options,headers:{...auth(),...(options.headers||{})}});const d=await r.json();if(!r.ok)throw Error(d.detail||JSON.stringify(d));return d}
function show(id,value){$(id).innerHTML='<pre>'+esc(typeof value==='string'?value:JSON.stringify(value,null,2))+'</pre>'}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
$('load').onclick=async()=>{try{const d=await call('/admin/syllabus-prototype/api/sources');$('book').innerHTML=d.sources.map(s=>'<option value="'+esc(s.id)+'">'+esc(s.subject+' · '+s.title+' · '+s.page_count+' pages · '+s.chunk_count+' chunks')+'</option>').join('');$('status').textContent='Found '+d.sources.length+' ready Class 6 Science/Mathematics source records with stored text.';if(!d.sources.length)$('status').textContent='No eligible source records found.'}catch(e){$('status').textContent=e.message}};
$('preview').onclick=async()=>{try{const d=await call('/admin/syllabus-prototype/api/sources/'+encodeURIComponent($('book').value)+'/preview');show('evidence',d)}catch(e){show('evidence',e.message)}};\n$('prepare').onclick=async()=>{try{const keywords=$('keywords').value.split(',').map(x=>x.trim()).filter(Boolean);const d=await call('/admin/syllabus-prototype/api/sources/'+encodeURIComponent($('book').value)+'/package',{method:'POST',body:JSON.stringify({topic_title:$('topic').value,keywords,chapter:$('chapter').value})});activePackage=d.source_id;activeTopic=d.topic.topic_id;show('evidence',d);$('result').textContent='Package ready for review. Synthesis has not run yet.'}catch(e){show('evidence',e.message)}};
$('wholeChapter').onclick=async()=>{try{const d=await call('/admin/syllabus-prototype/api/sources/'+encodeURIComponent($('book').value)+'/chapter-package',{method:'POST'});activePackage=d.source_id;activeTopic=d.topic.topic_id;show('evidence',d);$('result').textContent='Whole-chapter package ready. Synthesis has not run yet.'}catch(e){show('evidence',e.message)}};
$('synthesize').onclick=async()=>{if(!activePackage||!activeTopic){show('result','Build an evidence package first.');return}try{const d=await call('/admin/syllabus-prototype/api/packages/'+activePackage+'/topics/'+encodeURIComponent(activeTopic)+'/synthesize',{method:'POST',body:JSON.stringify({max_rounds:Number($('rounds').value)})});show('result',d)}catch(e){show('result',e.message)}};
</script></body></html>"""


@router.post("/api/sources/{existing_source_id}/chapter-package")
def create_whole_chapter_package(
    existing_source_id: str,
    x_admin_token: str | None = Header(default=None),
) -> dict[str, Any]:
    """Build one review package spanning every extracted page of an existing chapter PDF."""
    _authorize(x_admin_token)
    from syllabus_synthesis import (
        _read_existing_curriculum_source,
        _persist_source_package,
        build_synthesis_prompt,
        render_topic_review_sheet,
    )

    try:
        source, pages = _read_existing_curriculum_source(existing_source_id)
    except HTTPException:
        raise
    if str(source.get("subject", "")).casefold() not in {"science", "mathematics"} or int(source.get("class_level", 0)) != 6:
        raise HTTPException(status_code=422, detail="Prototype is currently limited to Class 6 Science and Mathematics")
    if not pages or not any(str(page.get("text", "")).strip() for page in pages):
        raise HTTPException(status_code=422, detail="No extracted page text is available for this chapter")

    title = str(source.get("title") or "Class 6 chapter")
    chapter_name = title.split("— Chapter PDF")[0].strip()
    topic = SyllabusTopic(
        id="whole-chapter-" + slug(title),
        title="Whole chapter: " + chapter_name,
        chapter=chapter_name,
        keywords=[],
    )
    try:
        result = create_package_from_existing_source(existing_source_id, [topic], output_root=DEFAULT_OUTPUT_ROOT)
    except HTTPException:
        raise
    except (PermissionError, ValueError, FileExistsError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    manifest = result["manifest"]
    item = manifest["topics"][0]
    # Whole-chapter mode deliberately includes every extracted page, rather than
    # relying on keyword matching which can silently omit sections.
    item["page_matches"] = [
        {
            "page": int(page["page"]),
            "matched_terms": ["whole_chapter_page"],
            "score": 1.0 if str(page.get("text", "")).strip() else 0.0,
            "evidence_excerpt": str(page.get("text", "")),
            "text_available": bool(str(page.get("text", "")).strip()),
        }
        for page in pages
    ]
    item["coverage_status"] = "evidence_found" if any(p["text_available"] for p in item["page_matches"]) else "missing_source"
    item["review_notes"] = [
        "All extracted pages are included; short excerpts are used for evidence previews.",
        "This is a chapter-wide evidence map, not proof of factual correctness or syllabus completeness.",
        "Check pages flagged as needing OCR and inspect diagrams separately.",
    ]
    scope = CurriculumScope.model_validate(manifest["scope"])
    item["synthesis_prompt"] = build_synthesis_prompt(scope, item)
    manifest["overall_status"] = "needs_review"
    (Path(result["package_path"]) / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    topic_dir = Path(result["package_path"]) / "topics" / slug(item["topic_id"])
    topic_dir.mkdir(parents=True, exist_ok=True)
    (topic_dir / "evidence.json").write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    (topic_dir / "synthesis-review.md").write_text(render_topic_review_sheet(item), encoding="utf-8")
    _persist_source_package(manifest, pages)
    return {
        "source_id": manifest["source_id"],
        "existing_curriculum_source_id": existing_source_id,
        "book_title": title,
        "chapter": chapter_name,
        "page_count": len(pages),
        "pages_with_text": sum(bool(str(page.get("text", "")).strip()) for page in pages),
        "pages_needing_ocr": [int(page["page"]) for page in pages if page.get("needs_ocr")],
        "topic": {
            "topic_id": item["topic_id"],
            "topic_title": item["topic_title"],
            "matched_page_count": len(item["page_matches"]),
            "page_matches": [
                {"page": p["page"], "text_available": p["text_available"], "preview": p["evidence_excerpt"][:180]}
                for p in item["page_matches"]
            ],
        },
        "status": "needs_review",
        "approved": False,
        "rights_reviewed": False,
        "next_step": "Run the synthesis endpoint for this whole-chapter topic, then review every claim and citation.",
    }
