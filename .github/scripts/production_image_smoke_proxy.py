#!/usr/bin/env python3
"""Read-only production image proxy for the Android paired-image acceptance test.

The tutor lesson response and curriculum outline are deterministic local fixtures.
Only GET requests for the approved Exploring Magnets image manifest and its PNG
bytes are forwarded to production. No production POST/PUT/DELETE is possible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

PRODUCTION_BASE = "https://padippupal-curriculum-api.onrender.com"
TARGET_LESSON_ID = "958addf6-1ff1-54c3-934e-d8d67548759f"
TARGET_CHAPTER = "Exploring Magnets"
TARGET_MODULE_KEY = "module-6"
TARGET_STEP_ID = "step_6"

STATE_LOCK = threading.Lock()
STATE = {
    "manifest_requests": 0,
    "verified_image_ids": [],
    "expected_titles": [],
    "errors": [],
    "upstream_get_paths": [],
    "production_writes": 0,
}
ALLOWED_IMAGES: dict[str, dict] = {}


def validate_pair_manifest(payload: dict) -> list[dict]:
    if payload.get("lesson_id") != TARGET_LESSON_ID:
        raise ValueError("Production image manifest returned the wrong lesson_id")
    images = payload.get("images")
    if not isinstance(images, list):
        raise ValueError("Production image manifest has no images array")
    pair = [
        item for item in images
        if isinstance(item, dict)
        and item.get("module_key") == TARGET_MODULE_KEY
        and TARGET_STEP_ID in (item.get("step_ids") or [])
    ]
    if len(pair) != 2:
        raise ValueError(
            f"Expected exactly two production images for {TARGET_MODULE_KEY}/{TARGET_STEP_ID}; got {len(pair)}"
        )
    allowed: dict[str, dict] = {}
    for item in pair:
        path = urlsplit(str(item.get("url") or "")).path
        prefix = f"/chapter-lessons/{TARGET_LESSON_ID}/images/"
        if not path.startswith(prefix) or path == prefix or ".." in path:
            raise ValueError(f"Production image URL is outside the approved lesson: {path!r}")
        if path in allowed:
            raise ValueError(f"Duplicate production image URL: {path}")
        if not item.get("sha256") or not isinstance(item.get("byte_length"), int):
            raise ValueError("Production image manifest is missing integrity metadata")
        allowed[path] = {
            "id": str(item.get("id") or ""),
            "title": str(item.get("title") or item.get("alt_text") or "Lesson image"),
            "sha256": str(item["sha256"]),
            "byte_length": int(item["byte_length"]),
        }
    with STATE_LOCK:
        ALLOWED_IMAGES.clear()
        ALLOWED_IMAGES.update(allowed)
        STATE["expected_titles"] = [item["title"] for item in allowed.values()]
        STATE["manifest_requests"] += 1
    return pair


def build_lesson_plan() -> dict:
    spoken = (
        "In Exploring Magnets, a freely suspended magnet settles along the north–south direction. "
        "The end that points north is called the north pole, and the other end is the south pole. "
        "When two like poles are brought close, they repel; unlike poles attract. "
        "A compass needle is a small magnet that indicates the north–south direction. "
        "The two labelled diagrams show how the poles interact and how a compass points."
    )
    visual = {
        "id": "synth-" + TARGET_LESSON_ID,
        "lesson_id": TARGET_LESSON_ID,
        "chapter": TARGET_CHAPTER,
        "topic": "Magnet poles and compass direction",
        "title": "Magnet Poles and Compass Direction",
        "scene_type": "synthesis_static",
        "caption": "Like poles repel, unlike poles attract, and a compass needle points north–south.",
        "visual_kind": "diagram",
        "visual_subtype": "paired_lesson_images",
        "animation": "narration_synced_2d",
        "module_key": TARGET_MODULE_KEY,
        "objects": [
            {"label": "North pole", "position": [0.18, 0.35]},
            {"label": "South pole", "position": [0.48, 0.35]},
            {"label": "Compass", "position": [0.78, 0.35]},
        ],
        "steps": [{
            "id": TARGET_STEP_ID,
            "label": "Magnet poles and compass direction",
            "caption": "Like poles repel; unlike poles attract. A compass needle points north–south.",
            "visual_kind": "diagram",
            "visual_subtype": "paired_lesson_images",
            "nodes": ["Like poles repel", "Unlike poles attract", "Compass points north–south"],
            "source_chunk_ids": ["production-approved-exploring-magnets-step-6"],
            "reference_page_numbers": [14, 15, 16],
            "actions": ["Compare like and unlike poles", "Read the compass directions"],
            "narration_sync": ["like poles repel", "unlike poles attract", "compass points north south"],
            "animation_plan": {"mode": "static", "duration_ms": 0, "loop": False},
        }],
    }
    segment = {
        "id": TARGET_STEP_ID,
        "spoken_text": spoken,
        "caption_text": spoken,
        "source_chunk_ids": ["production-approved-exploring-magnets-step-6"],
        "visual_action": {"type": "none", "target": "", "value": ""},
        "interactive_lesson": visual,
        "checkpoint": None,
    }
    return {
        "lesson_id": TARGET_LESSON_ID,
        "grounded": True,
        "sources": [{"chunk_id": "production-approved-exploring-magnets-step-6", "title": "Approved Exploring Magnets lesson"}],
        "language": "English",
        "subject": "Science",
        "provider": "android_production_image_smoke_fixture",
        "model": "deterministic-test-fixture",
        "timing_mode": "segment",
        "word_timestamps_available": False,
        "chapter_title": TARGET_CHAPTER,
        "interactive_lesson": visual,
        "segments": [segment],
    }


def _send(handler: BaseHTTPRequestHandler, status: int, body: bytes, content_type: str) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _json(handler: BaseHTTPRequestHandler, status: int, payload: dict) -> None:
    _send(handler, status, json.dumps(payload).encode("utf-8"), "application/json; charset=utf-8")


def _upstream_get(path_and_query: str) -> tuple[int, bytes, str]:
    if not path_and_query.startswith(f"/chapter-lessons/{TARGET_LESSON_ID}/images"):
        raise ValueError("Only the approved lesson image manifest and PNG paths may reach production")
    request = Request(
        PRODUCTION_BASE + path_and_query,
        headers={"Accept": "application/json, image/png"},
        method="GET",
    )
    last_error = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=90) as response:
                body = response.read()
                content_type = response.headers.get_content_type()
                return response.status, body, content_type
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Production GET failed after retries: {type(last_error).__name__}: {last_error}")


def make_handler():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/health":
                _json(self, 200, {"status": "ok", "service": "production-image-smoke-proxy"})
                return
            if path == "/planner/tasks":
                _json(self, 200, {"tasks": []})
                return
            if path == "/health/voice":
                _json(self, 200, {"configured": False, "provider": "android-tts", "fallback": "android-tts"})
                return
            if path == "/curriculum/outline":
                _json(self, 200, {
                    "board": "CBSE",
                    "class_level": 6,
                    "subject": "Science",
                    "chapter_count": 1,
                    "chapters": [{
                        "title": TARGET_CHAPTER,
                        "topics": ["Magnet poles and compass direction"],
                    }],
                })
                return
            if path == "/__test/report":
                with STATE_LOCK:
                    report = dict(STATE)
                    report["verified_image_ids"] = list(STATE["verified_image_ids"])
                    report["expected_titles"] = list(STATE["expected_titles"])
                    report["errors"] = list(STATE["errors"])
                    report["upstream_get_paths"] = list(STATE["upstream_get_paths"])
                    report["production_writes"] = STATE["production_writes"]
                    report["expected_pair_count"] = 2
                _json(self, 200, report)
                return
            prefix = f"/chapter-lessons/{TARGET_LESSON_ID}/images"
            if path == prefix:
                try:
                    status, body, content_type = _upstream_get(self.path)
                    if status != 200 or content_type != "application/json":
                        raise ValueError(f"Unexpected production manifest response: HTTP {status}, {content_type}")
                    payload = json.loads(body)
                    validate_pair_manifest(payload)
                    with STATE_LOCK:
                        STATE["upstream_get_paths"].append(path)
                    _send(self, status, body, content_type)
                except Exception as exc:
                    with STATE_LOCK:
                        STATE["errors"].append(str(exc))
                    _json(self, 502, {"detail": str(exc)})
                return
            if path.startswith(prefix + "/"):
                try:
                    with STATE_LOCK:
                        metadata = ALLOWED_IMAGES.get(path)
                    if metadata is None:
                        raise ValueError("Image path was not listed in the approved production manifest")
                    status, body, content_type = _upstream_get(self.path)
                    if status != 200 or content_type != "image/png":
                        raise ValueError(f"Unexpected production image response: HTTP {status}, {content_type}")
                    if not body.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise ValueError("Production image payload is not a PNG")
                    width, height = struct.unpack(">II", body[16:24])
                    if (width, height) != (1080, 720):
                        raise ValueError(f"Unexpected production image dimensions: {width}x{height}")
                    if len(body) != metadata["byte_length"]:
                        raise ValueError("Production image byte length differs from manifest")
                    if hashlib.sha256(body).hexdigest() != metadata["sha256"]:
                        raise ValueError("Production image SHA-256 differs from manifest")
                    with STATE_LOCK:
                        STATE["verified_image_ids"].append(metadata["id"])
                        STATE["upstream_get_paths"].append(path)
                    _send(self, status, body, content_type)
                except Exception as exc:
                    with STATE_LOCK:
                        STATE["errors"].append(str(exc))
                    _json(self, 502, {"detail": str(exc)})
                return
            _json(self, 404, {"detail": "Not found in production-image test proxy"})

        def do_POST(self) -> None:
            path = urlsplit(self.path).path
            length = int(self.headers.get("Content-Length", "0"))
            request_body = self.rfile.read(length) if length else b"{}"
            if path == "/tutor/lesson-plan":
                try:
                    request = json.loads(request_body or b"{}")
                    if request.get("board") != "CBSE" or request.get("class_level") != 6:
                        raise ValueError("Smoke fixture only accepts CBSE Class 6")
                    if request.get("subject") != "Science" or request.get("chapter") != TARGET_CHAPTER:
                        raise ValueError("Smoke fixture only accepts the approved Exploring Magnets test chapter")
                    _json(self, 200, build_lesson_plan())
                except Exception as exc:
                    _json(self, 422, {"detail": str(exc)})
                return
            if path == "/tutor/speech":
                _json(self, 503, {"detail": "Cloud voice is disabled in this read-only UI test"})
                return
            if path == "/tutor/chat":
                _json(self, 200, {"answer": "The production image smoke fixture is ready.", "grounded": True, "sources": []})
                return
            with STATE_LOCK:
                STATE["production_writes"] += 1
            _json(self, 404, {"detail": "POST route is local-only; no production writes are allowed"})

        def log_message(self, fmt: str, *args) -> None:
            print("PROXY " + (fmt % args), flush=True)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), make_handler())
    print(f"Production image smoke proxy listening on {args.host}:{args.port}; production upstream is GET-only", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
