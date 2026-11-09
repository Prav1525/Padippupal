from __future__ import annotations
import json
from pathlib import Path
import sys

import pytest
from tools import ingest_rendered_originals as client


def test_upload_client_refuses_without_explicit_confirmation(monkeypatch, tmp_path):
    manifest = tmp_path / "rendered-manifest.json"
    manifest.write_text('{"images":[]}', encoding="utf-8")
    monkeypatch.setenv("PADIPPUPAL_CONFIRM_PENDING_INGESTION", "false")
    with pytest.raises(SystemExit, match="Refusing upload"):
        client.main()


def test_upload_client_sends_png_and_requires_pending_response(monkeypatch, tmp_path, capsys):
    png = tmp_path / "sample.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"sample")
    manifest = tmp_path / "rendered-manifest.json"
    manifest.write_text(json.dumps({"images":[{
        "lesson_id":"lesson-1","module_key":"module-2","step_ids":["step_2"],
        "title":"Sample","alt_text":"A simple sample diagram","files":[str(png)]
    }]}), encoding="utf-8")
    monkeypatch.setenv("PADIPPUPAL_CONFIRM_PENDING_INGESTION", "true")
    monkeypatch.setenv("PADIPPUPAL_API_BASE_URL", "https://example.test")
    monkeypatch.setenv("PADIPPUPAL_ADMIN_TOKEN", "secret")

    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {"status":"pending_review","student_visible":False,"asset_id":"asset-1",
                    "lesson_id":"lesson-1","module_key":"module-2"}

    def fake_post(url, headers, data, files, timeout):
        assert url == "https://example.test/admin/lesson-images/ingest-original"
        assert headers == {"x-admin-token":"secret"}
        assert data["lesson_id"] == "lesson-1"
        assert data["module_key"] == "module-2"
        assert data["step_ids_json"] == '["step_2"]'
        assert files["file"][2] == "image/png"
        assert files["file"][1].read().startswith(b"\x89PNG")
        assert timeout == 45
        return Response()

    monkeypatch.setattr(client.requests, "post", fake_post)
    monkeypatch.setattr(sys, "argv", ["ingest_rendered_originals.py", str(manifest)])
    assert client.main() == 0
    output = json.loads(capsys.readouterr().out)
    assert output["uploaded_pending"] == 1
    assert output["published"] == 0


def test_upload_client_rejects_non_pending_server_response(monkeypatch, tmp_path):
    png = tmp_path / "sample.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"sample")
    manifest = tmp_path / "rendered-manifest.json"
    manifest.write_text(json.dumps({"images":[{
        "lesson_id":"lesson-1","module_key":"module-2","step_ids":["step_2"],
        "title":"Sample","alt_text":"A simple sample diagram","files":[str(png)]
    }]}), encoding="utf-8")
    monkeypatch.setenv("PADIPPUPAL_CONFIRM_PENDING_INGESTION", "true")
    monkeypatch.setenv("PADIPPUPAL_API_BASE_URL", "https://example.test")
    monkeypatch.setenv("PADIPPUPAL_ADMIN_TOKEN", "secret")
    class Response:
        def raise_for_status(self): pass
        def json(self): return {"status":"ready","student_visible":True}
    monkeypatch.setattr(client.requests, "post", lambda *args, **kwargs: Response())
    monkeypatch.setattr(sys, "argv", ["ingest_rendered_originals.py", str(manifest)])
    with pytest.raises(SystemExit, match="did not confirm safe pending storage"):
        client.main()
