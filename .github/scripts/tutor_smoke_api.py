#!/usr/bin/env python3
"""Deterministic local HTTP API used only by the Android emulator smoke workflow."""
from __future__ import annotations

import argparse
import base64
import json
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse
import uuid
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


DIARY_TASKS: dict[str, list[dict]] = {}
DIARY_PARSE_REQUESTS: list[dict] = []

LESSON = {
    "lesson_id": "smoke-all-ones",
    "grounded": True,
    "provider": "approved_chapter_lesson",
    "language": "English",
    "subject": "Mathematics",
    "sources": [{"chunk_id": "smoke-source", "title": "Smoke-test fixture", "page_start": 1, "page_end": 1}],
    # Original compact 2D visual, mapped to this exact synthesized All 1s lesson.
    # It deliberately models the learning relationship (repeated equal terms), not a copied textbook illustration.
    "interactive_lesson": {
        "id": "synth-smoke-all-ones",
        "lesson_id": "smoke-all-ones",
        "module_key": "module-1",
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
            "spoken_text": "The All 1s pattern is a sequence where every term is the number 1. Each term stays 1. The pattern repeats without growing. It looks like this: 1, 1, 1, 1. The number does not increase or decrease. The rule is simple: write 1 again each time.",
            "caption_text": "The All 1s pattern is a sequence where every term is the number 1. Each term stays 1. The pattern repeats without growing. It looks like this: 1, 1, 1, 1. The number does not increase or decrease. The rule is simple: write 1 again each time.",
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

# Keep each spoken segment paired with its own exact module/step visual.
# Reusing the response-level module-1 visual for every segment makes the
# live-player fixture ambiguous and correctly causes the client to fail closed.
for _index, _segment in enumerate(LESSON["segments"], start=1):
    _module_key = f"module-{_index}"
    _step_id = _segment["id"]
    _segment["module_key"] = _module_key
    _segment["interactive_lesson"] = {
        **LESSON["interactive_lesson"],
        "module_key": _module_key,
        "step_id": _step_id,
        "title": [
            "What is an All 1s pattern",
            "An All 1s example",
            "A common mistake",
            "Quick recap",
        ][_index - 1],
        "steps": [{
            **LESSON["interactive_lesson"]["steps"][0],
            "id": _step_id,
            "label": [
                "What is an All 1s pattern",
                "An All 1s example",
                "A common mistake",
                "Quick recap",
            ][_index - 1],
        }],
    }





def _make_smoke_lesson_png(module_index: int) -> bytes:
    """Create a distinct, topic-correct visual for each module in the UI fixture."""
    titles = {
        1: "What is an All 1s pattern",
        2: "An All 1s example",
        3: "A common mistake",
        4: "Quick recap",
    }
    image = Image.new("RGB", (1080, 720), "#FFFDF7")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 24, 1056, 696), radius=30, fill="#FFFFFF", outline="#DCE5EA", width=4)
    draw.rounded_rectangle((52, 48, 1028, 158), radius=22, fill="#E8F4F8")
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_path = bold_path if __import__("os").path.exists(bold_path) else None
    title_font = ImageFont.truetype(font_path, 34) if font_path else ImageFont.load_default()
    number_font = ImageFont.truetype(font_path, 100) if font_path else ImageFont.load_default()
    body_font = ImageFont.truetype(font_path, 42) if font_path else ImageFont.load_default()
    draw.text((82, 88), titles[module_index], font=title_font, fill="#24324A")

    if module_index in (1, 2):
        values = ["1", "1", "1"] if module_index == 1 else ["1", "1", "1", "1", "1"]
        positions = [540] if len(values) == 1 else [160 + i * (760 // (len(values) - 1)) for i in range(len(values))]
        for x, value in zip(positions, values):
            draw.rounded_rectangle((x - 62, 300, x + 62, 470), radius=24, fill="#EAF4E4", outline="#277DA1", width=5)
            draw.text((x, 382), value, font=number_font, fill="#24324A", anchor="mm")
        draw.text((540, 555), "EVERY TERM IS 1" if module_index == 1 else "FIVE TERMS, SAME RULE",
                  font=body_font, fill="#277DA1", anchor="mm")
    elif module_index == 3:
        draw.text((280, 340), "1, 1, 1, 1", font=body_font, fill="#277DA1", anchor="mm")
        draw.text((800, 340), "1, 2, 3", font=body_font, fill="#B3261E", anchor="mm")
        draw.line((650, 275, 950, 405), fill="#B3261E", width=12)
        draw.line((950, 275, 650, 405), fill="#B3261E", width=12)
        draw.text((540, 555), "THE VALUE DOES NOT GROW", font=body_font, fill="#24324A", anchor="mm")
    else:
        draw.text((540, 345), "1   1   1   ?", font=number_font, fill="#24324A", anchor="mm")
        draw.text((540, 555), "NEXT TERM = 1", font=body_font, fill="#277DA1", anchor="mm")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


SMOKE_LESSON_PNGS = {index: _make_smoke_lesson_png(index) for index in range(1, 5)}
SMOKE_AUDIO_DURATION_MS = 20_000

def _make_smoke_speech(text: str) -> tuple[bytes, list[dict]]:
    duration_ms = SMOKE_AUDIO_DURATION_MS
    sample_rate = 16000
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(sample_rate * duration_ms // 1000 * 2))
    words = text.split()
    count = max(1, len(words))
    timings = [
        {"start_ms": duration_ms * index // count, "end_ms": duration_ms * (index + 1) // count}
        for index in range(count)
    ]
    return buffer.getvalue(), timings




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
        if path == "/chapter-lessons/smoke-all-ones/images":
            module_images = [
                ("smoke-asset-1", "module-1", "all-ones-definition", "What is an All 1s pattern"),
                ("smoke-asset-2", "module-2", "all-ones-example", "An All 1s example"),
                ("smoke-asset-3", "module-3", "all-ones-common-mistake", "A common mistake"),
                ("smoke-asset-4", "module-4", "all-ones-recap", "Quick recap"),
            ]
            self._send(200, {"lesson_id": "smoke-all-ones", "images": [
                {
                    "id": asset_id, "module_key": module_key, "title": title,
                    "step_ids": [step_id], "content_type": "image/png",
                    "alt_text": title + " diagram",
                    "url": f"/chapter-lessons/smoke-all-ones/images/{asset_id}"
                }
                for asset_id, module_key, step_id, title in module_images
            ]})
            return
        if path.startswith("/chapter-lessons/smoke-all-ones/images/smoke-asset-"):
            if path.rsplit("-", 1)[-1] not in {"1", "2", "3", "4"}:
                self._send(404, {"detail": "Unknown smoke image"})
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            image_bytes = SMOKE_LESSON_PNGS[int(path.rsplit("-", 1)[-1])]
            self.send_header("Content-Length", str(len(image_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(image_bytes)
            return
        if path == "/curriculum/outline":
            self._send(200, {
                "board": "CBSE",
                "class_level": 6,
                "subject": "Mathematics",
                "chapters": [
                    {
                        "title": "Patterns in Mathematics",
                        "topics": ["All 1s"],
                    },
                    {
                        "title": "Growing Number Patterns",
                        "topics": ["Square Numbers"],
                    },
                ],
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
            # Deterministic local audio keeps UI smoke independent of emulator TTS speed.
            speech_text = str(body.get("text", "")).strip()
            if not speech_text:
                self._send(422, {"detail": "Speech text is required"})
                return
            speech_wav, word_timings = _make_smoke_speech(speech_text)
            self._send(200, {
                "audio_base64": base64.b64encode(speech_wav).decode("ascii"),
                "word_timings": word_timings,
                "provider": "deterministic_silent_smoke_audio",
            })
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
    assert len(LESSON["segments"]) == 4\n    assert len({hash(payload) for payload in SMOKE_LESSON_PNGS.values()}) == 4, "each module must have a distinct visual asset"
    assert "All 1s" in LESSON["segments"][0]["spoken_text"]
    assert "repeats" in LESSON["segments"][1]["spoken_text"]
    smoke_wav, smoke_timings = _make_smoke_speech(LESSON["segments"][0]["spoken_text"])
    with wave.open(BytesIO(smoke_wav), "rb") as wav:
        assert wav.getnframes() * 1000 // wav.getframerate() == 20000
    assert len(smoke_timings) == len(LESSON["segments"][0]["spoken_text"].split())
    assert smoke_timings[0]["start_ms"] == 0
    assert smoke_timings[-1]["end_ms"] == SMOKE_AUDIO_DURATION_MS
    assert all(left["end_ms"] == right["start_ms"] for left, right in zip(smoke_timings, smoke_timings[1:]))
    assert all(item["end_ms"] > item["start_ms"] for item in smoke_timings)
    assert all(segment["checkpoint"] is None for segment in LESSON["segments"])
    assert [segment["module_key"] for segment in LESSON["segments"]] == [f"module-{i}" for i in range(1, 5)]
    assert all(segment["interactive_lesson"]["module_key"] == segment["module_key"] for segment in LESSON["segments"])
    assert all(segment["interactive_lesson"]["step_id"] == segment["id"] for segment in LESSON["segments"])
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
