import hashlib

from fastapi.testclient import TestClient

import app as curriculum


def setup_module():
    curriculum.DB_PATH = __import__("pathlib").Path(":memory:")
    # Use a temporary on-disk database because each connection is independent.
    import tempfile
    curriculum.DB_PATH = __import__("pathlib").Path(tempfile.mkstemp(suffix=".sqlite3")[1])
    curriculum.ADMIN_TOKEN = "test-token"
    curriculum.init_db()


def test_ingest_then_retrieve_is_profile_filtered():
    from app import SourceMetadata
    client = TestClient(curriculum.app)
    metadata = {
        "board": "CBSE", "academic_year": "2026-27", "class_level": 7,
        "subject": "Science", "medium": "English", "term": "Term 1",
        "edition": "2026", "title": "Crop Production sample",
        "source_url": "https://example.org/sample", "license_note": "Public-domain test fixture",
    }
    payload = {**metadata, "text": ("Crop production includes preparation of soil, sowing seeds, adding manure and fertilizers. " * 20)}
    response = client.post("/admin/ingest-text", json=payload, headers={"X-Admin-Token": "test-token"})
    assert response.status_code == 202
    # The payload is persisted before the job becomes visible to the worker.
    with curriculum.db() as conn:
        stored = conn.execute("SELECT content FROM source_content WHERE source_id=?", (response.json()["source_id"],)).fetchone()
    assert stored is not None and "Crop production" in stored["content"]
    # Process queue deterministically for the test.
    assert curriculum.process_one_job() is True
    result = client.post("/retrieve", json={
        "board": "CBSE", "class_level": 7, "subject": "Science", "medium": "English",
        "query": "soil sowing seeds manure", "limit": 3,
    })
    assert result.status_code == 200
    assert result.json()["matches"]
    assert result.json()["matches"][0]["source"]["title"] == "Crop Production sample"
    wrong_profile = client.post("/retrieve", json={
        "board": "Tamil Nadu State Board", "class_level": 7, "subject": "Science",
        "medium": "English", "query": "soil sowing seeds manure",
    })
    assert wrong_profile.status_code == 200
    assert wrong_profile.json()["matches"] == []


def test_admin_ingestion_requires_token():
    client = TestClient(curriculum.app)
    response = client.post("/admin/ingest-text", json={
        "board": "CBSE", "academic_year": "2026-27", "class_level": 7,
        "subject": "Science", "medium": "English", "edition": "2026",
        "title": "x", "license_note": "approved", "text": "long enough text for indexing in a basic test"
    })
    assert response.status_code == 401
