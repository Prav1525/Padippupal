"""Transiently inspect textbook page figures and keep only structural descriptions.

Rendered page images are sent to the configured vision model for analysis, then discarded.
No textbook image or page screenshot is persisted. The saved result is a concise, source-page-
linked description that synthesis can use to create original teaching artwork.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any

MAX_REFERENCE_PAGES = 16
MAX_DESCRIPTION_CHARS = 900


def describe_pdf_visual_references(pdf_bytes: bytes) -> dict[int, str]:
    """Return page-number -> originalizable figure description; fail open on optional vision."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {}
    try:
        import fitz  # PyMuPDF, used only to render candidate pages transiently
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return {}

    model = os.getenv("PADIPPUPAL_GEMINI_CHAT_MODEL", "gemini-2.5-flash").strip()
    descriptions: dict[int, str] = {}
    try:
        candidates: list[tuple[int, Any]] = []
        for page_index, page in enumerate(document):
            try:
                images = page.get_images(full=True)
                drawings = page.get_drawings()
                # Embedded images and vector-heavy pages are likely to contain figures.
                if images or len(drawings) >= 8:
                    candidates.append((page_index + 1, page))
            except Exception:
                continue
        for page_no, page in candidates[:MAX_REFERENCE_PAGES]:
            try:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.15, 1.15), alpha=False)
                png_bytes = pixmap.tobytes("png")
                encoded = base64.b64encode(png_bytes).decode("ascii")
                prompt = (
                    "Analyze this textbook page only to help create a NEW educational illustration. "
                    "Return JSON with keys: has_teaching_visual (boolean), concept (short), "
                    "visual_kind (one of fraction, number_line, geometry, sequence, compare, process, "
                    "table, cycle, diagram, none), objects (array of concise labels), "
                    "spatial_relationships (array), teaching_order (array of short actions), "
                    "important_labels (array of readable labels), uncertainty (short string). "
                    "Describe the educational structure and relationships, not the artwork style or page layout. "
                    "Do not reproduce the illustration, decorative details, or long textbook text. "
                    "If there is no meaningful instructional figure, set has_teaching_visual=false. "
                    "Do not infer facts that are not visible."
                )
                payload = json.dumps({
                    "contents": [{"role": "user", "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": encoded}},
                    ]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.1,
                        "maxOutputTokens": 700,
                    },
                }).encode("utf-8")
                request = urllib.request.Request(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    data=payload,
                    headers={"x-goog-api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=35) as response:
                    result = json.loads(response.read().decode("utf-8"))
                raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(raw_text)
                if not isinstance(parsed, dict) or parsed.get("has_teaching_visual") is not True:
                    continue
                safe = {
                    "concept": str(parsed.get("concept") or "")[:160],
                    "visual_kind": str(parsed.get("visual_kind") or "diagram")[:32],
                    "objects": [str(value)[:90] for value in parsed.get("objects", [])[:8]]
                        if isinstance(parsed.get("objects"), list) else [],
                    "spatial_relationships": [str(value)[:120] for value in parsed.get("spatial_relationships", [])[:6]]
                        if isinstance(parsed.get("spatial_relationships"), list) else [],
                    "teaching_order": [str(value)[:100] for value in parsed.get("teaching_order", [])[:6]]
                        if isinstance(parsed.get("teaching_order"), list) else [],
                    "important_labels": [str(value)[:70] for value in parsed.get("important_labels", [])[:8]]
                        if isinstance(parsed.get("important_labels"), list) else [],
                    "uncertainty": str(parsed.get("uncertainty") or "")[:120],
                }
                if safe["concept"] or safe["objects"] or safe["spatial_relationships"]:
                    descriptions[page_no] = json.dumps(safe, ensure_ascii=False, separators=(",", ":"))[:MAX_DESCRIPTION_CHARS]
            except (KeyError, IndexError, TypeError, ValueError, urllib.error.URLError, TimeoutError):
                continue
    finally:
        document.close()
    return descriptions
