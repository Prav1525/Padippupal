#!/usr/bin/env python3
"""Beyond Earth emulator fixture: keeps original PDF image bytes from the live curriculum API."""
from __future__ import annotations
import importlib.util, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = os.environ.get("PADIPPUPAL_PRODUCTION_API", "https://padippupal-curriculum-api.onrender.com").rstrip("/")
LESSON_ID = "10d13a36-87e9-5f3b-8210-f62eb95e8854"
spec = importlib.util.spec_from_file_location("tutor_smoke_api", ROOT / ".github/scripts/tutor_smoke_api.py")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)

def fetch(url):
    """Fetch a live asset robustly; Render may be cold-starting after inactivity."""
    last_error = None
    for attempt in range(1, 5):
        try:
            req = Request(url, headers={"Accept": "application/json, image/*", "User-Agent": "PadippuPal-BeyondEarth-Acceptance/1.0"})
            with urlopen(req, timeout=90) as response:
                body = response.read()
                return response.status, response.headers.get("Content-Type", ""), body
        except Exception as exc:
            last_error = exc
            print(f"Live asset fetch attempt {attempt}/4 failed for {url}: {type(exc).__name__}: {exc}", flush=True)
            if attempt < 4:
                time.sleep(min(5 * attempt, 15))
    raise RuntimeError(f"Could not fetch live asset after 4 attempts: {url}: {last_error}") from last_error

status, manifest_type, manifest_bytes = fetch(f"{BASE_URL}/chapter-lessons/{LESSON_ID}/images")
if status != 200:
    raise SystemExit(f"Production Beyond Earth image manifest returned HTTP {status}")
manifest = json.loads(manifest_bytes)
images = manifest.get("images", [])
if len(images) != 19:
    raise SystemExit(f"Expected 19 original PDF-derived images, got {len(images)}")
# Fetch independent image blobs concurrently. The previous serial loop could spend
# up to 4 x 90 seconds per image on a cold/slow production service, while the
# fixture's HTTP server (including /health) remained unavailable until all 19
# downloads completed. Bound concurrency to avoid hammering the read-only API.
image_paths = []
for image in images:
    url_path = urlparse(image.get("url", "")).path
    if not url_path.startswith("/chapter-lessons/"):
        raise SystemExit(f"Unexpected image URL in manifest: {url_path}")
    image_paths.append(url_path)

blob_by_path = {}
with ThreadPoolExecutor(max_workers=6) as pool:
    futures = {pool.submit(fetch, BASE_URL + path): path for path in image_paths}
    for future in as_completed(futures):
        url_path = futures[future]
        blob_status, mime, blob = future.result()
        if blob_status != 200 or not mime.startswith("image/") or not blob:
            raise SystemExit(f"Original image fetch failed for {url_path}: HTTP {blob_status}, {mime}, {len(blob)} bytes")
        blob_by_path[url_path] = (mime, blob)
        print(f"Fetched original image {len(blob_by_path)}/{len(image_paths)}: {url_path} ({len(blob)} bytes)", flush=True)
if len(blob_by_path) != 19:
    raise SystemExit(f"Expected 19 original image blobs, fetched {len(blob_by_path)}")

def interactive(module_key):
    return {
      "id": "beyond-earth-original-pdf-" + module_key,
      "lesson_id": LESSON_ID,
      "chapter": "Beyond Earth",
      "topic": "Beyond Earth",
      "module_key": module_key,
      "title": "Beyond Earth",
      "scene_type": "synthesis_static",
      "caption": "",
      "visual_kind": "textbook_page",
      "steps": [{"id": "beyond-earth-" + module_key, "label": "", "caption": "", "visual_kind": "textbook_page", "nodes": [], "source_chunk_ids": [], "reference_page_numbers": [], "actions": [], "narration_sync": [], "animation_plan": {"mode": "static", "duration_ms": 0, "loop": False}}]
    }

segments = []
module_texts = [
 "Our universe contains many objects beyond Earth. Astronomers study the sky to learn about them.",
 "Stars are huge, hot objects that produce their own light. The Sun is the star closest to Earth.",
 "The Moon is Earth's natural satellite. It appears bright because sunlight reflects from its surface.",
 "Planets travel around stars. Our solar system includes the Sun and the planets that orbit it.",
 "Constellations are patterns of stars that people identify in the night sky.",
 "Telescopes collect light and help us observe distant objects in space.",
 "Space exploration uses spacecraft and scientific instruments to learn more about the universe."
]
for i, text in enumerate(module_texts, 1):
    segments.append({
      "id": f"beyond-earth-module-{i}",
      "spoken_text": text,
      "caption_text": text,
      "source_chunk_ids": [],
      "visual_action": {"type": "none", "target": "", "value": ""},
      "checkpoint": None,
      "interactive_lesson": interactive(f"module-{i}")
    })
lesson = {
  "lesson_id": LESSON_ID, "grounded": True, "provider": "beyond_earth_emulator_fixture",
  "language": "English", "subject": "Science",
  "sources": [{"chunk_id": "beyond-earth-live-image-fixture", "title": "Beyond Earth textbook image manifest", "page_start": 1, "page_end": 19}],
  "interactive_lesson": interactive("module-1"),
  "segments": segments
}

class Handler(base.Handler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, {"status":"ok","service":"beyond-earth-emulator-fixture","live_original_images":len(images)})
            return
        if path == "/curriculum/outline":
            from urllib.parse import parse_qs
            q = parse_qs(urlparse(self.path).query)
            subject = q.get("subject", [""])[0].casefold()
            if subject == "science":
                self._send(200, {"board":"CBSE","class_level":6,"subject":"Science","chapters":[{"title":"Beyond Earth","topics":["Beyond Earth"]}]})
            else:
                self._send(200, {"board":"CBSE","class_level":6,"subject":q.get("subject",["Science"])[0],"chapters":[{"title":"Beyond Earth","topics":["Beyond Earth"]}]})
            return
        prefix = f"/chapter-lessons/{LESSON_ID}/images"
        if path == prefix:
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(manifest_bytes)))
            self.end_headers()
            self.wfile.write(manifest_bytes)
            return
        if path.startswith(prefix + "/"):
            original_path = path.replace(prefix, f"/chapter-lessons/{LESSON_ID}/images", 1)
            # The manifest URLs are authoritative; match their exact URL path.
            item = blob_by_path.get(original_path)
            if item is None:
                # Some API versions expose asset URLs without /images in the suffix.
                item = blob_by_path.get(path)
            if item is None:
                self._send(404, {"detail":"Original image not present in fetched live manifest"})
                return
            mime, blob = item
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)
            return
        super().do_GET()
    def do_POST(self):
        if urlparse(self.path).path == "/tutor/lesson-plan":
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            if str(body.get("chapter","")).casefold() != "beyond earth" or str(body.get("subject","")).casefold() != "science":
                self._send(422, {"detail":"Beyond Earth acceptance fixture only; wrong selected lesson"})
                return
            self._send(200, lesson)
            return
        super().do_POST()

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8765"))), Handler)
    print(f"Beyond Earth fixture ready: {len(images)} original images, {len(blob_by_path)} image blobs", flush=True)
    server.serve_forever()
