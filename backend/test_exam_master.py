from fastapi.testclient import TestClient
import base64
import io
from pypdf import PdfReader
import app as curriculum


def test_exam_master_catalog_and_two_printable_pdfs():
    client = TestClient(curriculum.app)
    catalog = client.get("/exam-master/catalog")
    assert catalog.status_code == 200
    data = catalog.json()
    assert data["class_level"] == 6
    assert data["subject"] == "Science"
    assert len(data["chapters"]) == 12
    assert data["question_bank_count"] == 60
    assert "textbook exercise ids" in data["question_policy"].lower()

    generated = client.post("/exam-master/generate", json={
        "board": "CBSE",
        "class_level": 6,
        "subject": "Science",
        "medium": "English",
        "selected_chapters": ["Exploring Magnets", "A Journey through States of Water"],
        "question_count": 10,
        "student_name": "Test Student",
        "exam_title": "Unit Practice",
        "seed": 5,
    })
    assert generated.status_code == 200, generated.text
    result = generated.json()
    assert result["question_count"] == 10
    assert result["maximum_marks"] > 0
    assert result["source_mix"]["syllabus_aligned_practice_variants"] == 8
    assert result["source_mix"]["chapter_context_practice_variants"] == 2
    student_pdf = base64.b64decode(result["student_pdf_base64"])
    parent_pdf = base64.b64decode(result["parent_key_pdf_base64"])
    assert student_pdf.startswith(b"%PDF-")
    assert parent_pdf.startswith(b"%PDF-")
    assert student_pdf != parent_pdf
    student_text = "\\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(student_pdf)).pages)
    parent_text = "\\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(parent_pdf)).pages)
    assert "PARENT ANSWER KEY" not in student_text
    assert "PARENT ANSWER KEY" in parent_text
    assert "mark-wise rubric" in parent_text


def test_exam_master_rejects_unsupported_profile_and_chapter():
    client = TestClient(curriculum.app)
    wrong_profile = client.post("/exam-master/generate", json={
        "board": "Tamil Nadu State Board", "class_level": 6, "subject": "Science",
        "selected_chapters": ["Exploring Magnets"], "question_count": 5,
    })
    assert wrong_profile.status_code == 422
    wrong_chapter = client.post("/exam-master/generate", json={
        "board": "CBSE", "class_level": 6, "subject": "Science",
        "selected_chapters": ["Invented chapter"], "question_count": 5,
    })
    assert wrong_chapter.status_code == 422



def test_question_bank_has_complete_answers_and_honest_source_labels():
    from exam_master import BANK, CHAPTERS
    assert set(BANK) == set(CHAPTERS)
    for chapter, questions in BANK.items():
        assert len(questions) == 5, chapter
        assert sum(q[2] == "syllabus_practice_variant" for q in questions) == 4, chapter
        assert sum(q[2] == "chapter_context_variant" for q in questions) == 1, chapter
        for prompt, marks, category, answer in questions:
            assert prompt.strip(), chapter
            assert marks > 0, (chapter, prompt)
            assert category in {"syllabus_practice_variant", "chapter_context_variant"}, (chapter, category)
            assert answer.strip(), (chapter, prompt)


def test_exam_master_answers_use_precise_ncert_concepts():
    from exam_master import BANK
    materials_answer = next(q[3] for q in BANK["Materials Around Us"] if q[0].startswith("A shopkeeper uses transparent jars"))
    constellation_answer = BANK["Beyond Earth"][0][3]
    assert "see the contents clearly" in materials_answer
    assert "defined region of the sky" in constellation_answer
    assert not any("floats on water" in q[0] for q in BANK["Materials Around Us"])
