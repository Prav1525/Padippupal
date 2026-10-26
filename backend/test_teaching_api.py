from fastapi.testclient import TestClient

import app as curriculum


def test_teaching_method_returns_class6_maths_scaffold_and_contract():
    response = TestClient(curriculum.app).get(
        "/tutor/teaching-method",
        params={"class_level": 6, "subject": "maths"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["dataset_id"] == "cbse-class-6-teaching-pilot"
    assert body["lesson_contract"]["checkpoint_question_count"] == {"min": 2, "max": 3}
    assert body["chapters"]
    assert all(item["subject"] == "Mathematics" for item in body["chapters"])
    assert body["completeness"]["status"] == "starter_scaffolds_only"


def test_teaching_method_returns_science_scaffold():
    response = TestClient(curriculum.app).get(
        "/tutor/teaching-method",
        params={"class_level": 6, "subject": "Science"},
    )
    assert response.status_code == 200
    assert response.json()["chapters"]
    assert all(item["subject"] == "Science" for item in response.json()["chapters"])


def test_teaching_method_fails_closed_for_unsupported_grade():
    response = TestClient(curriculum.app).get(
        "/tutor/teaching-method",
        params={"class_level": 7, "subject": "Science"},
    )
    assert response.status_code == 404


def test_mastery_gate_blocks_progression_without_explanation():
    client = TestClient(curriculum.app)
    response = client.post("/tutor/mastery-decision", json={
        "class_level": 6, "subject": "Science",
        "correct_answers": 3, "total_answers": 3,
        "demonstrated_explanation_or_application": False,
    })
    assert response.status_code == 200
    assert response.json()["mastered"] is False
    assert response.json()["can_advance"] is False
    assert response.json()["next_action"] == "reteach_and_retest"


def test_mastery_gate_allows_progression_only_with_answer_and_reasoning_evidence():
    response = TestClient(curriculum.app).post("/tutor/mastery-decision", json={
        "class_level": 6, "subject": "Mathematics",
        "correct_answers": 2, "total_answers": 3,
        "demonstrated_explanation_or_application": True,
    })
    assert response.status_code == 200
    assert response.json()["mastered"] is True
    assert response.json()["can_advance"] is True


def test_mastery_gate_rejects_more_correct_than_total():
    response = TestClient(curriculum.app).post("/tutor/mastery-decision", json={
        "class_level": 6, "subject": "Science",
        "correct_answers": 4, "total_answers": 3,
        "demonstrated_explanation_or_application": True,
    })
    assert response.status_code == 422
