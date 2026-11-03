#!/usr/bin/env python3
"""Deterministic local HTTP API used only by the Android emulator smoke workflow."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import uuid


DIARY_TASKS: dict[str, list[dict]] = {}
DIARY_PARSE_REQUESTS: list[dict] = []

LESSON = {
    "lesson_id": "smoke-all-ones",
    "grounded": True,
    "provider": "smoke_fixture",
    "language": "English",
    "subject": "Mathematics",
    "sources": [{"chunk_id": "smoke-source", "title": "Smoke-test fixture", "page_start": 1, "page_end": 1}],
    # Original compact 2D visual, mapped to this exact synthesized All 1s lesson.
    # It deliberately models the learning relationship (repeated equal terms), not a copied textbook illustration.
    "interactive_lesson": {
        "id": "synth-smoke-all-ones",
        "chapter": "Patterns in Mathematics",
        "topic": "All 1s",
        "title": "All 1s pattern visual",
        "scene_type": "synthesis_static",
        "caption": "Each term stays 1. The pattern repeats without growing.",
        "visual_kind": "sequence",
        "visual_subtype": "sequence",
        "animation": "narration_synced_2d",
        "objects": [
            {"label": "1", "position": [0.06, 0.30]},
            {"label": "1", "position": [0.25, 0.30]},
            {"label": "1", "position": [0.44, 0.30]},
            {"label": "1", "position": [0.63, 0.30]},
            {"label": "1", "position": [0.82, 0.30]}
        ],
        "steps": [{
            "id": "all-ones-rule",
            "label": "Every term is 1",
            "caption": "Each term stays 1. The pattern repeats without growing.",
            "visual_kind": "sequence",
            "visual_subtype": "sequence",
            "nodes": ["1", "1", "1", "1", "1"],
            "source_chunk_ids": ["smoke-source"],
            "reference_page_numbers": [1],
            "actions": ["Reveal the repeated 1s from left to right"],
            "narration_sync": ["every term is the number 1", "repeats the same number"],
            "animation_plan": {"mode": "staggered_reveal", "duration_ms": 850, "loop": False}
        }]
    },
    "segments": [
        {
            "id": "all-ones-definition",
            "spoken_text": "The All 1s pattern is a sequence where every term is the number 1. It looks like this: 1, 1, 1, 1. The number does not increase or decrease. The rule is simple: write 1 again each time.",
            "caption_text": "The All 1s pattern is a sequence where every term is the number 1. It looks like this: 1, 1, 1, 1. The number does not increase or decrease. The rule is simple: write 1 again each time.",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "none", "target": "", "value": ""},
            "checkpoint": None,
        },
        {
            "id": "all-ones-example",
            "spoken_text": "For example, if we write the pattern in five spaces, each space contains 1: 1, 1, 1, 1, 1. We can predict the next term is also 1 because the rule repeats the same number each time. The pattern can have three terms, five terms, or ten terms, and the rule stays the same.",
            "caption_text": "For example, if we write the pattern in five spaces, each space contains 1: 1, 1, 1, 1, 1. We can predict the next term is also 1 because the rule repeats the same number each time. The pattern can have three terms, five terms, or ten terms, and the rule stays the same.",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "none", "target": "", "value": ""},
            "checkpoint": None,
        },
        {
            "id": "all-ones-common-mistake",
            "spoken_text": "A common mistake is to think every number pattern must grow. This one does not grow; it repeats 1 each time. Even if the list becomes longer, the value of each term does not change. In an All 1s pattern, each term is the number 1, so we should not replace it with a different number.",
            "caption_text": "A common mistake is to think every number pattern must grow. This one does not grow; it repeats 1 each time. Even if the list becomes longer, the value of each term does not change. In an All 1s pattern, each term is the number 1, so we should not replace it with a different number.",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "none", "target": "", "value": ""},
            "checkpoint": None,
        },
        {
            "id": "all-ones-recap",
            "spoken_text": "Here is another way to check the rule: cover the last term and ask what should come next. Since the rule repeats 1, the missing term must also be 1. Adding more terms changes the length of the list, not the value of each term. Remember, in the All 1s pattern, every term is 1. Quick recap: 1, 1, 1, 1 always follows the same rule. What number comes next after 1, 1, 1?",
            "caption_text": "Here is another way to check the rule: cover the last term and ask what should come next. Since the rule repeats 1, the missing term must also be 1. Adding more terms changes the length of the list, not the value of each term. Remember, in the All 1s pattern, every term is 1. Quick recap: 1, 1, 1, 1 always follows the same rule. What number comes next after 1, 1, 1?",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "none", "target": "", "value": ""},
            "checkpoint": None,
        },
    ],
}

# The live Android player reads the visual from the active segment. Keep the
# deterministic fixture faithful to that contract instead of relying only on
# the response-level visual, which chat mode uses.
for _segment in LESSON["segments"]:
    _segment["interactive_lesson"] = LESSON["interactive_lesson"]



BEYOND_EARTH_LESSON_ID = "10d13a36-87e9-5f3b-8210-f62eb95e8854"
BEYOND_EARTH_MANIFEST_FILE = os.getenv("PADIPPUPAL_BEYOND_EARTH_MANIFEST_FILE", "beyond-earth-image-manifest.json")
IMAGE_SOURCE_BASE = os.getenv("PADIPPUPAL_IMAGE_SOURCE_BASE", "https://padippupal-curriculum-api.onrender.com").rstrip("/")


def beyond_earth_manifest() -> dict:
    path = Path(BEYOND_EARTH_MANIFEST_FILE)
    if not path.is_file():
        raise RuntimeError(f"Missing live Beyond Earth manifest fixture: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("lesson_id") != BEYOND_EARTH_LESSON_ID or len(payload.get("images", [])) != 19:
        raise RuntimeError("Beyond Earth fixture must contain the 19 production images for the approved lesson.")
    return payload


def beyond_earth_lesson() -> dict:
    images = beyond_earth_manifest()["images"]
    counts: dict[str, int] = {}
    for image in images:
        counts[str(image.get("module_key", ""))] = counts.get(str(image.get("module_key", "")), 0) + 1
    module_key = max(counts, key=counts.get)
    module_images = [item for item in images if item.get("module_key") == module_key]
    step_counts: dict[str, int] = {}
    for image in module_images:
        for step in image.get("step_ids", []):
            step_counts[str(step)] = step_counts.get(str(step), 0) + 1
    step_id = max(step_counts, key=step_counts.get) if step_counts else ""
    if not module_key or not step_id:
        raise RuntimeError("Production image manifest has no usable module_key/step_ids mapping.")
    words = [
        "Beyond Earth helps us understand the objects and patterns in space.",
        "Scientists use observations and evidence to explain what they see beyond our planet.",
        "The labelled textbook pictures help us connect each idea with its real visual example.",
        "Look carefully at the picture and its labels, then remember how the parts relate to one another."
    ]
    steps = [{"id": step_id, "label": "Beyond Earth module " + str(index + 1), "caption": words[index],
              "visual_kind": "textbook_image", "nodes": [], "source_chunk_ids": ["production-image-manifest"],
              "reference_page_numbers": [], "actions": ["Inspect the mapped textbook image"],
              "narration_sync": ["look carefully at the picture"]} for index in range(4)]
    visual = {"id": "beyond-earth-production-image-smoke", "lesson_id": BEYOND_EARTH_LESSON_ID,
              "chapter": "Beyond Earth", "topic": "Exploring Beyond Earth",
              "module_key": module_key, "title": "Beyond Earth — original textbook images",
              "scene_type": "synthesis_static", "caption": words[0], "steps": steps}
    segments = [{"id": "beyond-earth-" + str(i+1), "spoken_text": words[i], "caption_text": words[i],
                 "source_chunk_ids": ["production-image-manifest"],
                 "interactive_lesson": visual, "visual_action": {"type": "none", "target": "", "value": ""},
                 "checkpoint": None} for i in range(4)]
    return {"lesson_id": BEYOND_EARTH_LESSON_ID, "grounded": True, "provider": "production_image_smoke_fixture",
            "language": "English", "subject": "Science",
            "sources": [{"chunk_id": "production-image-manifest", "title": "Beyond Earth production image manifest",
                         "page_start": 1, "page_end": 1}],
            "interactive_lesson": visual, "segments": segments}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"status": "ok", "service": "padippupal-smoke-fixture", "fixture_version": 2})
            return
        if path == "/curriculum/outline":
            query = parse_qs(urlparse(self.path).query)
            subject = query.get("subject", [""])[0]
            if subject.casefold() == "science":
                self._send(200, {"board": "CBSE", "class_level": 6, "subject": "Science",
                                 "chapters": [{"title": "Beyond Earth", "topics": ["Exploring Beyond Earth"]}]})
            else:
                self._send(200, {"board": "CBSE", "class_level": 6, "subject": "Mathematics",
                                 "chapters": [{"title": "Patterns in Mathematics", "topics": ["All 1s"]}]})
            return
        if path == f"/chapter-lessons/{BEYOND_EARTH_LESSON_ID}/images":
            self._send(200, beyond_earth_manifest())
            return
        image_prefix = f"/chapter-lessons/{BEYOND_EARTH_LESSON_ID}/images/"
        if path.startswith(image_prefix):
            asset_id = path[len(image_prefix):]
            record = next((item for item in beyond_earth_manifest()["images"] if str(item.get("id")) == asset_id), None)
            if record is None:
                self._send(404, {"detail": "Unknown production image asset"})
                return
            upstream = IMAGE_SOURCE_BASE + str(record["url"])
            request = Request(upstream, headers={"Accept": str(record.get("content_type", "image/*"))})
            with urlopen(request, timeout=20) as response:
                payload = response.read()
                self.send_response(200)
                self.send_header("Content-Type", response.headers.get("Content-Type", record.get("content_type", "application/octet-stream")))
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            return
        if path == "/health/voice":
            self._send(200, {"configured": False, "provider": "android-tts", "fallback": "android-tts"})
            return
        if path == "/planner/tasks":
            profile_id = parse_qs(urlparse(self.path).query).get("profile_id", [""])[0]
            self._send(200, {"tasks": DIARY_TASKS.get(profile_id, [])})
            return
        self._send(404, {"detail": "Not found in deterministic smoke fixture"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        if path == "/diary/parse":
            image = str(body.get("image_base64", ""))
            today_date = str(body.get("today_date", ""))
            if len(image) < 100 or len(today_date) != 10:
                self._send(422, {"detail": "Diary test request is missing image bytes or device-local today_date"})
                return
            DIARY_PARSE_REQUESTS.append({"today_date": today_date, "image_chars": len(image), "mime_type": body.get("mime_type")})
            # Deterministic mock of the Gemini contract: only today's tasks are returned.
            self._send(200, {
                "diary_date": today_date,
                "match_status": "matched",
                "tasks": [
                    {"title": "Complete Q1-5", "subject": "Mathematics", "details": "Class 6 CBSE Mathematics: Patterns in Mathematics", "due_date": today_date, "minutes": 15, "confidence": "high"},
                    {"title": "Revise Components of Food", "subject": "Science", "details": "Class 6 CBSE Science: nutrients and balanced diet", "due_date": today_date, "minutes": 15, "confidence": "high"},
                ],
                "count": 2,
                "model": "deterministic-diary-fixture",
            })
            return
        if path == "/planner/tasks/import":
            profile_id = str(body.get("profile_id", ""))
            saved = []
            for task in body.get("tasks", []):
                if task.get("profile_id") != profile_id:
                    self._send(400, {"detail": "profile_id mismatch"})
                    return
                item = {
                    "id": str(uuid.uuid4()), "profile_id": profile_id,
                    "title": str(task.get("title", "")), "subject": str(task.get("subject", "General")),
                    "details": str(task.get("details", "")), "due_date": str(task.get("due_date", "")),
                    "minutes": int(task.get("minutes", 15)), "completed": False, "source": "diary",
                    "created_at": 0,
                }
                saved.append(item)
            DIARY_TASKS.setdefault(profile_id, []).extend(saved)
            self._send(201, {"saved": len(saved), "tasks": saved})
            return
        if path == "/tutor/lesson-plan":
            if str(body.get("chapter", "")).casefold() == "beyond earth" and str(body.get("subject", "")).casefold() == "science":
                self._send(200, beyond_earth_lesson())
                return
            if str(body.get("topic", "")).casefold() not in {"all 1s", "all ones", "all one's"}:
                self._send(200, {
                    "lesson_id": "smoke-off-topic",
                    "grounded": False,
                    "segments": [],
                    "sources": [],
                    "warning": "No fixture lesson exists for the selected topic.",
                })
                return
            self._send(200, LESSON)
            return
        if path == "/tutor/speech":
            self._send(503, {"detail": "Cloud voice disabled in deterministic smoke fixture"})
            return
        if path == "/tutor/chat":
            self._send(200, {
                "answer": "The smoke-test tutor is ready to help with the selected topic.",
                "grounded": True,
                "sources": [],
                "provider": "smoke_fixture",
            })
            return
        self._send(404, {"detail": "Not found in deterministic smoke fixture"})

    def log_message(self, format: str, *args) -> None:
        # Avoid noisy request logs; workflow artifacts already record the UI path.
        return


def self_test() -> None:
    assert len(LESSON["segments"]) == 4
    assert "All 1s" in LESSON["segments"][0]["spoken_text"]
    assert "repeats" in LESSON["segments"][1]["spoken_text"]
    assert all(segment["checkpoint"] is None for segment in LESSON["segments"])
    assert LESSON["interactive_lesson"]["scene_type"] == "synthesis_static"
    assert LESSON["interactive_lesson"]["steps"][0]["nodes"] == ["1", "1", "1", "1", "1"]
    assert LESSON["interactive_lesson"]["steps"][0]["source_chunk_ids"] == ["smoke-source"]
    full_lesson = " ".join(segment["spoken_text"] for segment in LESSON["segments"])
    assert len(full_lesson) >= 220
    assert len(full_lesson.split()) >= 140
    assert "square" not in json.dumps(LESSON).casefold()
    print("smoke API fixture self-test passed: topic-valid lesson with source-mapped inline 2D visual")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
