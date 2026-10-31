"""Tests for source-page image persistence and synthesis-facing image URLs."""
import hashlib

from fastapi.testclient import TestClient

import app as curriculum


def test_extract_and_serve_figure_bearing_textbook_page(tmp_path, monkeypatch):
    import fitz

    db_path = tmp_path / "textbook-images.sqlite3"
    monkeypatch.setattr(curriculum, "DB_PATH", db_path)
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    curriculum.init_db()

    pdf = fitz.open()
    page = pdf.new_page(width=420, height=595)
    page.draw_rect(fitz.Rect(80, 100, 340, 300), color=(0, 0, 1), width=2)
    page.insert_text((100, 330), "Solar System figure")
    raw = pdf.tobytes()
    pdf.close()

    images = curriculum.extract_pdf_visual_pages(raw)
    assert 1 in images
    assert images[1].startswith(b"\x89PNG\r\n\x1a\n")

    source_id = "source-test-beyond-earth"
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO sources(id,board,academic_year,class_level,subject,medium,term,
               edition,title,source_url,license_note,sha256,status,page_count,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (source_id, "CBSE", "2026-27", 6, "Science", "English", "", "2026",
             "Beyond Earth", "https://ncert.nic.in/textbook/pdf/fecu112.pdf",
             "approved test fixture", hashlib.sha256(raw).hexdigest(), "ready", 1, 1.0),
        )
    assert curriculum.persist_source_page_images(source_id, images) == 1

    response = TestClient(curriculum.app).get(f"/textbook-images/{source_id}/1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == images[1]
    assert response.headers["etag"] == '"' + hashlib.sha256(images[1]).hexdigest() + '"'


def test_nonexistent_textbook_page_returns_404(tmp_path, monkeypatch):
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "empty.sqlite3")
    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    curriculum.init_db()
    response = TestClient(curriculum.app).get("/textbook-images/missing/99")
    assert response.status_code == 404



def test_topic_figure_mapping_prefers_specific_observation_topics():
    assert curriculum.textbook_figure_pages_for_topic("Planets and observing the sky") == [13]
    assert curriculum.textbook_figure_pages_for_topic("The Sun and our Solar System") == [8, 10]
    assert curriculum.textbook_figure_pages_for_topic("Natural satellites and the Moon") == [14]
    assert curriculum.textbook_figure_pages_for_topic("Stars and constellations") == [1, 2, 3, 5]
