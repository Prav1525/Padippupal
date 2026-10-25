import base64
import json

import pytest
from fastapi.testclient import TestClient

import app as curriculum


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "padippupal-test.sqlite3")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    with TestClient(curriculum.app) as test_client:
        yield test_client


def test_planner_tasks_persist_and_can_be_completed(client):
    profile_id = "test-profile-0001"
    created = client.post("/planner/tasks", json={
        "profile_id": profile_id, "title": "Revise fractions",
        "subject": "Mathematics", "minutes": 20,
    })
    assert created.status_code == 201
    task = created.json()["task"]
    assert task["completed"] is False

    listed = client.get("/planner/tasks", params={"profile_id": profile_id})
    assert listed.status_code == 200
    assert len(listed.json()["tasks"]) == 1
    assert listed.json()["tasks"][0]["title"] == "Revise fractions"

    updated = client.put(f"/planner/tasks/{task['id']}", json={
        "profile_id": profile_id, "completed": True,
    })
    assert updated.status_code == 200
    assert updated.json()["task"]["completed"] is True

    deleted = client.delete(f"/planner/tasks/{task['id']}", params={"profile_id": profile_id})
    assert deleted.status_code == 200
    assert client.get("/planner/tasks", params={"profile_id": profile_id}).json()["tasks"] == []


def test_diary_import_is_idempotent_and_preserves_completion(client):
    profile_id = "diary-dedupe-profile"
    payload = {
        "profile_id": profile_id,
        "tasks": [{
            "profile_id": profile_id, "title": "Complete exercise 2",
            "subject": "Mathematics", "details": "Questions 1-5",
            "due_date": "2026-10-24", "minutes": 20, "source": "diary",
        }],
    }
    first = client.post("/planner/tasks/import", json=payload)
    assert first.status_code == 201
    assert first.json()["saved"] == 1
    task_id = first.json()["tasks"][0]["id"]

    completed = client.put(f"/planner/tasks/{task_id}", json={
        "profile_id": profile_id, "completed": True,
    })
    assert completed.status_code == 200

    second = client.post("/planner/tasks/import", json=payload)
    assert second.status_code == 201
    assert second.json()["saved"] == 0
    listed = client.get("/planner/tasks", params={"profile_id": profile_id}).json()["tasks"]
    assert len(listed) == 1
    assert listed[0]["id"] == task_id
    assert listed[0]["completed"] is True


def test_diary_scan_reports_missing_gemini_key(client):
    response = client.post("/diary/parse", json={
        "image_base64": base64.b64encode(b"fake-image-content" * 10).decode(),
        "mime_type": "image/jpeg",
        "board": "CBSE",
        "class_level": 6,
        "medium": "English",
        "app_language": "Tanglish",
    })
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


def test_diary_scan_extracts_reviewable_tasks(monkeypatch, client):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{
                "text": json.dumps({"diary_date": "2026-10-24", "match_status": "matched", "tasks": [{
                    "title": "Complete exercise 2", "subject": "Mathematics",
                    "details": "Questions 1–5", "due_date": "", "minutes": 20,
                }]})
            }]}}]}).encode()

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", fake_urlopen)
    response = client.post("/diary/parse", json={
        "image_base64": base64.b64encode(b"fake-image-content" * 10).decode(),
        "mime_type": "image/jpeg", "board": "CBSE", "class_level": 6,
        "medium": "English", "app_language": "Tanglish", "today_date": "2026-10-24",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["needs_review"] is True
    assert body["count"] == 1
    assert body["tasks"][0]["title"] == "Complete exercise 2"
    assert body["tasks"][0]["confidence"] == "medium"
    assert body["diary_date"] == "2026-10-24"
    assert body["match_status"] == "matched"
    prompt = captured["payload"]["contents"][0]["parts"][0]["text"].lower()
    assert "children's handwriting" in prompt
    assert "date/day column" in prompt
    assert "do not assume the photo date" in prompt
    assert "only the row for the supplied local date" in prompt
    assert "google lens style" in prompt
    assert "vertical position" in prompt
    assert "baselines" in prompt
    assert "substantial blank gap" in prompt
    assert "next date marker" in prompt
    assert "whitespace as one layout cue, not the only cue" in prompt
    assert "dd/mm/yyyy" in prompt
    assert "dd.mm.yyyy" in prompt
    assert captured["payload"]["contents"][0]["parts"][1]["inlineData"]["mimeType"] == "image/jpeg"
    assert captured["timeout"] == 35


def test_diary_scan_discards_tasks_when_today_row_needs_crop(monkeypatch, client):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{
                "text": json.dumps({"diary_date": "", "match_status": "needs_crop", "tasks": [
                    {"title": "WRONG ROW MUST NOT IMPORT", "subject": "Maths"}
                ]})
            }]}}]}).encode()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", lambda request, timeout: FakeResponse())
    response = client.post("/diary/parse", json={
        "image_base64": base64.b64encode(b"fake-image-content" * 10).decode(),
        "mime_type": "image/jpeg", "today_date": "2026-10-24",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["match_status"] == "needs_crop"
    assert body["tasks"] == []
    assert body["count"] == 0



def test_diary_scan_rejects_model_match_for_wrong_date(monkeypatch, client):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [{
                "text": json.dumps({"diary_date": "2026-10-23", "match_status": "matched", "tasks": [
                    {"title": "WRONG DATE MUST NOT IMPORT", "subject": "Maths"}
                ]})
            }]}}]}).encode()

    monkeypatch.setattr(curriculum.urllib.request, "urlopen", lambda request, timeout: FakeResponse())
    response = client.post("/diary/parse", json={
        "image_base64": base64.b64encode(b"fake-image-content" * 10).decode(),
        "mime_type": "image/jpeg", "today_date": "2026-10-24",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["match_status"] == "needs_crop"
    assert body["tasks"] == []
    assert body["count"] == 0
