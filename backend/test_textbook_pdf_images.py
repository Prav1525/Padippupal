import hashlib
import io
import json
import pathlib
import tempfile

import fitz
from fastapi.testclient import TestClient

import app as curriculum


def setup_module():
    curriculum.DB_PATH = pathlib.Path(tempfile.mkstemp(suffix=".sqlite3")[1])
    curriculum.ADMIN_TOKEN = "test-token"
    curriculum.init_db()


def test_pdf_ingestion_persists_original_and_each_page_image():
    document = fitz.open()
    for label in ("Textbook page one has enough text for extraction.", "Textbook page two has enough text for extraction."):
        page = document.new_page(width=300, height=400)
        page.insert_text((30, 50), label)
    raw_pdf = document.tobytes()
    document.close()

    metadata = {
        "board": "CBSE", "academic_year": "2026-27", "class_level": 6,
        "subject": "Science", "medium": "English", "term": "Term 1",
        "edition": "2026", "title": "PDF persistence fixture",
        "source_url": "", "license_note": "Private test fixture",
    }
    response = TestClient(curriculum.app).post(
        "/admin/ingest-pdf",
        data={"metadata_json": json.dumps(metadata)},
        files={"file": ("fixture.pdf", raw_pdf, "application/pdf")},
        headers={"X-Admin-Token": "test-token"},
    )
    assert response.status_code == 202, response.text
    source_id = response.json()["source_id"]

    with curriculum.db() as conn:
        pdf = conn.execute(
            "SELECT pdf_bytes, pdf_sha256, byte_length FROM source_pdf_assets WHERE source_id=?",
            (source_id,),
        ).fetchone()
        pages = conn.execute(
            "SELECT page_number, mime_type, image_bytes, image_sha256, width, height "
            "FROM source_page_images WHERE source_id=? ORDER BY page_number",
            (source_id,),
        ).fetchall()
    assert pdf is not None
    assert bytes(pdf["pdf_bytes"]) == raw_pdf
    assert pdf["pdf_sha256"] == hashlib.sha256(raw_pdf).hexdigest()
    assert pdf["byte_length"] == len(raw_pdf)
    assert len(pages) == 2
    assert [row["page_number"] for row in pages] == [1, 2]
    for row in pages:
        image = bytes(row["image_bytes"])
        assert row["mime_type"] == "image/png"
        assert image.startswith(b"\x89PNG\r\n\x1a\n")
        assert row["image_sha256"] == hashlib.sha256(image).hexdigest()
        assert row["width"] > 0 and row["height"] > 0


def test_pdf_asset_checksum_mismatch_is_rejected():
    document = fitz.open()
    page = document.new_page()
    page.insert_text((30, 50), "A valid test page with enough text.")
    pdf_bytes = document.tobytes()
    document.close()

    metadata = curriculum.SourceMetadata(
        board="CBSE", academic_year="2026-27", class_level=6, subject="Science",
        medium="English", edition="2026", title="Mismatch fixture",
        license_note="Private test fixture",
    )
    queued = curriculum.enqueue_source(metadata, "enough extracted text for a test", hashlib.sha256(b"other pdf").hexdigest(), 1)
    try:
        curriculum._persist_pdf_and_page_images(queued["source_id"], pdf_bytes)
        assert False, "checksum mismatch should fail closed"
    except ValueError as exc:
        assert "checksum" in str(exc).lower()
