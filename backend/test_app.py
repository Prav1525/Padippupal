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


def test_official_registry_separates_authority_from_ingestion_permission():
    client = TestClient(curriculum.app)
    response = client.get("/sources/registry")
    assert response.status_code == 200
    data = response.json()
    assert data["reviewed_on"] == "2026-10-19"
    by_id = {item["id"]: item for item in data["sources"]}
    assert by_id["ncert-textbooks"]["authority_verified"] is True
    assert by_id["ncert-textbooks"]["ingestion_approved"] is False
    assert by_id["cbse-academic-curriculum-2026-27"]["official_url"].startswith("https://cbseacademic.nic.in/")
    assert by_id["tn-textbook-corporation"]["ingestion_approved"] is False
    assert data["automatic_ingestion_enabled"] is False



def test_visual_lesson_library_is_seeded_and_topic_matched():
    client = TestClient(curriculum.app)
    response = client.get("/visual-lessons/match", params={
        "board": "CBSE", "class_level": 7, "subject": "Science",
        "query": "How does photosynthesis use carbon dioxide?",
    })
    assert response.status_code == 200
    lesson = response.json()["visual_lesson"]
    assert lesson["id"] == "global-photosynthesis"
    assert len(lesson["steps"]) >= 3
    assert "glucose" in lesson["caption"]


def test_visual_lesson_profiles_and_admin_upsert():
    client = TestClient(curriculum.app)
    payload = {
        "id": "cbse-class-7-sample-topic",
        "board": "CBSE",
        "class_level": 7,
        "subject": "Science",
        "topic": "Sample topic",
        "title": "Sample visual",
        "visual_type": "process",
        "keywords": ["sample topic", "sample keyword"],
        "caption": "A short accurate caption.",
        "steps": [
            {"icon": "1", "label": "First step"},
            {"icon": "2", "label": "Second step"},
        ],
    }
    saved = client.post("/admin/visual-lessons", json=payload, headers={"X-Admin-Token": "test-token"})
    assert saved.status_code == 201
    assert saved.json()["saved"] is True
    matching = client.get("/visual-lessons/match", params={
        "board": "CBSE", "class_level": 7, "subject": "Science", "query": "sample keyword",
    }).json()["visual_lesson"]
    assert matching["id"] == payload["id"]
    wrong_profile = client.get("/visual-lessons/match", params={
        "board": "Tamil Nadu State Board", "class_level": 7, "subject": "Science", "query": "sample keyword",
    }).json()["visual_lesson"]
    assert wrong_profile is None



def test_class_six_concept_outline_has_complete_chapter_lists():
    client = TestClient(curriculum.app)
    response = client.get("/curriculum/outline", params={
        "board": "CBSE", "class_level": 6, "subject": "Science", "medium": "English",
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["chapters"]) == 12
    assert data["chapters"][0]["title"] == "The Wonderful World of Science"
    assert data["chapters"][-1]["title"] == "Beyond Earth"
    for chapter in data["chapters"]:
        assert len(chapter["topics"]) >= 5, chapter["title"]
        assert all(item["title"].strip() for item in chapter["topics"])
