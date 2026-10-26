from fastapi import FastAPI
from fastapi.testclient import TestClient

import syllabus_prototype


def _db(path):
    import sqlite3

    conn = sqlite3.connect(path)
    conn.executescript("""
    CREATE TABLE sources (
        id TEXT PRIMARY KEY, board TEXT, academic_year TEXT, class_level INTEGER,
        subject TEXT, medium TEXT, term TEXT, edition TEXT, title TEXT, source_url TEXT,
        license_note TEXT, sha256 TEXT, status TEXT, page_count INTEGER, created_at REAL
    );
    CREATE TABLE source_content (source_id TEXT PRIMARY KEY, content TEXT);
    CREATE TABLE chunks (
        id TEXT PRIMARY KEY, source_id TEXT, chunk_no INTEGER, chapter TEXT,
        page_start INTEGER, page_end INTEGER, text TEXT
    );
    """)
    conn.execute(
        """INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        ("book-science-1", "CBSE", "2026-27", 6, "Science", "English", "",
         "Reprint 2026-27", "NCERT Curiosity Class 6 Science — Test Chapter", "",
         "Private testing; rights not reviewed", "abc123", "ready", 1, 0.0),
    )
    conn.execute(
        "INSERT INTO source_content VALUES (?, ?)",
        ("book-science-1", "[Page 1] Plants have roots, stems and leaves.\n\n[Page 2] Leaves use sunlight to make food."),
    )
    conn.execute(
        "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("chunk-1", "book-science-1", 0, "Plants", 1, 2,
         "Plants have roots, stems and leaves. Leaves use sunlight to make food."),
    )
    conn.commit()
    conn.close()


def _client(monkeypatch, tmp_path):
    db_path = tmp_path / "curriculum.sqlite3"
    _db(db_path)
    output = tmp_path / "syllabus-library"
    monkeypatch.setenv("PADIPPUPAL_DB", str(db_path))
    monkeypatch.setenv("PADIPPUPAL_ADMIN_TOKEN", "test-secret")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(syllabus_prototype, "DEFAULT_OUTPUT_ROOT", output)
    app = FastAPI()
    app.include_router(syllabus_prototype.router)
    return TestClient(app)


def test_prototype_page_is_available_and_explains_review_gate(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.get("/admin/syllabus-prototype")
    assert response.status_code == 200
    assert "Syllabus synthesis lab" in response.text
    assert "will not approve" in response.text


def test_prototype_lists_actual_ready_class6_books_and_requires_admin(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    assert client.get("/admin/syllabus-prototype/api/sources").status_code == 401
    response = client.get(
        "/admin/syllabus-prototype/api/sources",
        headers={"x-admin-token": "test-secret"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["sources"]) == 1
    assert data["sources"][0]["id"] == "book-science-1"
    assert data["sources"][0]["stored_characters"] > 0
    assert data["sources"][0]["chunk_count"] == 1


def test_prototype_builds_page_evidence_from_existing_database_text(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.post(
        "/admin/syllabus-prototype/api/sources/book-science-1/package",
        headers={"x-admin-token": "test-secret"},
        json={
            "topic_title": "Plant Food Making",
            "keywords": ["leaves", "sunlight", "make food"],
            "chapter": "Plants",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["existing_curriculum_source_id"] == "book-science-1"
    assert data["page_count"] == 2
    assert data["topic"]["coverage_status"] == "evidence_found"
    assert data["topic"]["matched_page_count"] == 1
    assert data["approved"] is False
    assert data["rights_reviewed"] is False
    package = client.get(
        f"/admin/syllabus-prototype/api/packages/{data['source_id']}",
        headers={"x-admin-token": "test-secret"},
    )
    assert package.status_code == 200
    assert package.json()["topics"][0]["topic_title"] == "Plant Food Making"


def test_prototype_previews_page_marked_text(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.get('/admin/syllabus-prototype/api/sources/book-science-1/preview', headers={'x-admin-token': 'test-secret'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['pages_with_text'] == 2
    assert data['preview_pages'][0]['page'] == 1
    assert 'Plants have roots' in data['preview_pages'][0]['text_preview']
    assert data['preview_pages'][1]['page'] == 2
    assert 'sunlight to make food' in data['preview_pages'][1]['text_preview']
    assert data['approved'] is False
    assert data['rights_reviewed'] is False


def test_whole_chapter_package_includes_every_extracted_page(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    response = client.post(
        "/admin/syllabus-prototype/api/sources/book-science-1/chapter-package",
        headers={"x-admin-token": "test-secret"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["page_count"] == 2
    assert data["pages_with_text"] == 2
    assert data["topic"]["matched_page_count"] == 2
    assert [item["page"] for item in data["topic"]["page_matches"]] == [1, 2]
    assert data["approved"] is False
    assert data["rights_reviewed"] is False
    package = client.get(
        f"/admin/syllabus-prototype/api/packages/{data['source_id']}",
        headers={"x-admin-token": "test-secret"},
    )
    assert package.status_code == 200
    assert package.json()["topics"][0]["matched_page_count"] == 2
