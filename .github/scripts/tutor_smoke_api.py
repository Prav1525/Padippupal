#!/usr/bin/env python3
"""Deterministic local HTTP API used only by the Android emulator smoke workflow."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import uuid


DIARY_TASKS: dict[str, list[dict]] = {}
DIARY_PARSE_REQUESTS: list[dict] = []

LESSON = {
    "lesson_id": "smoke-beyond-earth",
    "grounded": True,
    "provider": "smoke_fixture",
    "language": "English",
    "subject": "Science",
    "sources": [{"chunk_id": "smoke-beyond-earth-source", "title": "Beyond Earth smoke fixture", "page_start": 1, "page_end": 1}],
    "interactive_lesson": {
        "id": "synth-smoke-beyond-earth",
        "chapter": "Beyond Earth",
        "topic": "Day and Night",
        "title": "Beyond Earth — Day and Night",
        "scene_type": "synthesis_static",
        "caption": "The Sun lights one half of Earth. Rotation causes day and night.",
        "visual_kind": "beyond_earth",
        "visual_subtype": "beyond_earth_sky_watching",
        "animation": "narration_synced_2d",
        "objects": [{"label": "North Star", "position": [0.78, 0.20]}, {"label": "Star pattern", "position": [0.45, 0.55]}, {"label": "Ursa Major", "position": [0.18, 0.78]}],
        "steps": [{"id": "step_2", "label": "Explain day and night", "caption": "The Sun lights one half of Earth. Rotation causes day and night.", "visual_kind": "beyond_earth", "visual_subtype": "beyond_earth_sky_watching", "nodes": ["Sun", "Sunlight", "Earth", "Day", "Night"], "source_chunk_ids": ["smoke-beyond-earth-source"], "reference_page_numbers": [1], "actions": ["Reveal sunlight, day and night hemispheres, then Earth rotation"], "narration_sync": ["Sunlight", "day and night", "rotates"], "animation_plan": {"mode": "staggered_reveal", "duration_ms": 850, "loop": False}}]
    },
    "segments": [
        {"id": "beyond-earth-definition", "spoken_text": "The Sun is a star. It gives Earth light and heat. Sunlight travels through space and reaches Earth. The half of Earth facing the Sun has day, while the opposite half has night.", "caption_text": "A constellation is a pattern of stars seen in the night sky.", "source_chunk_ids": ["smoke-beyond-earth-source"], "visual_action": {"type": "none", "target": "", "value": ""}, "checkpoint": None},
        {"id": "beyond-earth-example", "spoken_text": "Earth is always rotating on an imaginary line called its axis. As Earth rotates, different places turn towards the Sun and then away from it. This is why day changes to night.", "caption_text": "Ursa Major is a familiar constellation pattern.", "source_chunk_ids": ["smoke-beyond-earth-source"], "visual_action": {"type": "none", "target": "", "value": ""}, "checkpoint": None},
        {"id": "beyond-earth-misconception", "spoken_text": "The Sun does not move around Earth to make day and night. Earth rotates from west to east. One complete rotation takes about 24 hours.", "caption_text": "The pattern is how stars appear from Earth, not their true distances.", "source_chunk_ids": ["smoke-beyond-earth-source"], "visual_action": {"type": "none", "target": "", "value": ""}, "checkpoint": None},
        {"id": "beyond-earth-recap", "spoken_text": "Let us recap. Sunlight illuminates the half of Earth facing the Sun. That side has day; the other side has night. Earth rotation causes the cycle to continue.", "caption_text": "Constellation means a recognisable pattern of stars.", "source_chunk_ids": ["smoke-beyond-earth-source"], "visual_action": {"type": "none", "target": "", "value": ""}, "checkpoint": None}
    ]
}
for _segment in LESSON["segments"]:
    _segment["interactive_lesson"] = LESSON["interactive_lesson"]


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
            self._send(200, {"status": "ok", "service": "padippupal-smoke-fixture", "fixture_version": 1})
            return
        if path == "/curriculum/outline":
            self._send(200, {
                "board": "CBSE",
                "class_level": 6,
                "subject": "Science",
                "chapters": [{
                    "title": "Beyond Earth",
                    "topics": ["Constellations", "Day and Night"],
                }],
            })
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
            if str(body.get("topic", "")).casefold() not in {"day and night", "day/night"}:
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
    assert "sunlight" in LESSON["segments"][0]["spoken_text"].casefold()
    assert "ursa major" in LESSON["segments"][1]["spoken_text"].casefold()
    assert all(segment["checkpoint"] is None for segment in LESSON["segments"])
    assert LESSON["interactive_lesson"]["scene_type"] == "synthesis_static"
    assert LESSON["interactive_lesson"]["steps"][0]["nodes"] == ["Sun", "Sunlight", "Earth", "Day", "Night"]
    assert LESSON["interactive_lesson"]["steps"][0]["source_chunk_ids"] == ["smoke-beyond-earth-source"]
    full_lesson = " ".join(segment["spoken_text"] for segment in LESSON["segments"])
    assert len(full_lesson) >= 220
    assert len(full_lesson.split()) >= 140
    assert "square" not in json.dumps(LESSON).casefold()
    print("smoke API fixture self-test passed: Beyond Earth Day/Night lesson with native Canvas visual")


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
