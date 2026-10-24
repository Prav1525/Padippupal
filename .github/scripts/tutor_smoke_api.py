#!/usr/bin/env python3
"""Deterministic local HTTP API used only by the Android emulator smoke workflow."""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


LESSON = {
    "lesson_id": "smoke-all-ones",
    "grounded": True,
    "provider": "smoke_fixture",
    "language": "English",
    "subject": "Mathematics",
    "sources": [{"chunk_id": "smoke-source", "title": "Smoke-test fixture", "page_start": 1, "page_end": 1}],
    "segments": [
        {
            "id": "all-ones-intro",
            "spoken_text": "Look at this sequence: 1, 1, 1, 1, 1.",
            "caption_text": "Look at this sequence: 1, 1, 1, 1, 1.",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "highlight", "target": "repeated-ones", "value": "1, 1, 1, 1, 1"},
            "checkpoint": None,
        },
        {
            "id": "all-ones-rule",
            "spoken_text": "Every term is one, so the number stays the same each time.",
            "caption_text": "Every term is one, so the number stays the same each time.",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "highlight", "target": "repeated-ones", "value": "same value"},
            "checkpoint": None,
        },
        {
            "id": "all-ones-example",
            "spoken_text": "If we add another term, we write one more 1; the value still does not change.",
            "caption_text": "If we add another term, we write one more 1; the value still does not change.",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "reveal", "target": "repeated-ones", "value": "add one more 1"},
            "checkpoint": None,
        },
        {
            "id": "all-ones-compare",
            "spoken_text": "Unlike 1, 2, 3, 4, this pattern does not increase; it repeats one.",
            "caption_text": "Unlike 1, 2, 3, 4, this pattern does not increase; it repeats one.",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "compare", "target": "repeated-ones", "value": "repeats one"},
            "checkpoint": None,
        },
        {
            "id": "all-ones-recap",
            "spoken_text": "Remember, an All 1s pattern repeats the same number in every position.",
            "caption_text": "Remember, an All 1s pattern repeats the same number in every position.",
            "source_chunk_ids": ["smoke-source"],
            "visual_action": {"type": "highlight", "target": "repeated-ones", "value": "same number"},
            "checkpoint": None,
        },
    ]
}


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
                "subject": "Mathematics",
                "chapters": [{
                    "title": "Patterns in Mathematics",
                    "topics": ["All 1s"],
                }],
            })
            return
        if path == "/health/voice":
            self._send(200, {"configured": False, "provider": "android-tts", "fallback": "android-tts"})
            return
        self._send(404, {"detail": "Not found in deterministic smoke fixture"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
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
    assert len(LESSON["segments"]) == 5
    assert "sequence" in LESSON["segments"][0]["spoken_text"].casefold()
    assert "stays the same" in LESSON["segments"][1]["spoken_text"].casefold()
    assert "repeats" in LESSON["segments"][4]["spoken_text"].casefold()
    assert all(segment["checkpoint"] is None for segment in LESSON["segments"])
    assert "worked" not in json.dumps(LESSON).casefold()
    assert "square" not in json.dumps(LESSON).casefold()
    print("smoke API fixture self-test passed: five teaching segments, no mid-lesson checkpoint, no square-number content")


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
