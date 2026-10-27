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



def test_class_six_cbse_mathematics_outline_includes_patterns_first_and_accepts_maths_alias():
    client = TestClient(curriculum.app)
    for subject in ("Mathematics", "Maths"):
        response = client.get("/curriculum/outline", params={
            "board": "CBSE", "class_level": 6, "subject": subject, "medium": "English",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["chapter_count"] == 10, subject
        assert data["chapters"][0]["title"] == "Patterns in Mathematics", subject
        assert len(data["chapters"][0]["topics"]) >= 5, subject
        assert data["chapters"][0]["topics"][0]["title"].strip(), subject

def test_lines_and_angles_blueprints_are_specific_and_interactive():
    client = TestClient(curriculum.app)
    response = client.get("/interactive-lessons", params={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "chapter": "Lines and Angles",
    })
    assert response.status_code == 200
    lessons = {item["id"]: item for item in response.json()["lessons"]}
    assert "mathematics-lines-and-angles-line-segment" in lessons
    segment = lessons["mathematics-lines-and-angles-line-segment"]
    assert segment["scene_type"] == "line_segment"
    assert len(segment["steps"]) == 3
    assert "two endpoints" in segment["steps"][0]["text"]
    comparison = lessons["mathematics-lines-and-angles-comparing-angles"]
    assert "arm longer" in comparison["steps"][1]["text"]
    classifier = lessons["mathematics-lines-and-angles-types-of-angles"]
    assert classifier["scene_type"] == "angle_classifier"
    assert "90 degrees" in classifier["steps"][1]["text"]




def test_patterns_in_mathematics_has_concept_first_chapter_one_lessons():
    client = TestClient(curriculum.app)
    response = client.get("/interactive-lessons", params={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "chapter": "Patterns in Mathematics",
    })
    assert response.status_code == 200
    lessons = response.json()["lessons"]
    assert len(lessons) >= 12
    topics = {lesson["topic"] for lesson in lessons}
    assert {
        "What is Mathematics?", "Patterns in Numbers",
        "Visualising Number Sequences", "Relations among Number Sequences",
        "Patterns in Shapes", "Relation to Number Sequences",
    }.issubset(topics)
    ids = [lesson["id"] for lesson in lessons]
    assert len(ids) == len(set(ids))
    for lesson in lessons:
        assert lesson["steps"] and len(lesson["steps"]) >= 3
        assert lesson["challenge"]["question"].strip()
        assert lesson["challenge"]["answer"] in lesson["challenge"]["options"]
        assert lesson["challenge"]["hint"].strip()
        assert lesson["scene_type"] in {
            "pattern_builder", "number_pattern", "shape_pattern", "number_machine",
        }


def test_patterns_in_mathematics_contains_key_number_sequences():
    client = TestClient(curriculum.app)
    response = client.get("/interactive-lessons", params={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "chapter": "Patterns in Mathematics",
    })
    lessons = response.json()["lessons"]
    combined = " ".join(
        [lesson["topic"] + " " + lesson["title"] + " " + lesson["caption"] for lesson in lessons]
        + [step["text"] for lesson in lessons for step in lesson["steps"]]
    ).lower()
    for concept in ("counting numbers", "odd numbers", "even numbers", "triangular", "square", "cube", "virahanka", "powers of 2", "powers of 3", "hexagonal numbers", "regular polygon", "complete graph", "stacked squares", "stacked triangles", "koch snowflake", "192"):
        assert concept in combined, f"Chapter 1 missing concept: {concept}"

def test_patterns_in_mathematics_covers_shape_and_sequence_topics():
    client = TestClient(curriculum.app)
    response = client.get("/interactive-lessons", params={
        "board": "CBSE", "class_level": 6, "subject": "Mathematics",
        "chapter": "Patterns in Mathematics",
    })
    assert response.status_code == 200
    lessons = response.json()["lessons"]
    topics = {lesson["topic"] for lesson in lessons}
    assert {
        "What is Mathematics?", "Patterns in Numbers",
        "Visualising Number Sequences", "Relations among Number Sequences",
        "Patterns in Shapes", "Relation to Number Sequences", "All 1s",
    }.issubset(topics)
    combined = " ".join(
        [lesson["topic"] + " " + lesson["title"] + " " + lesson["caption"] for lesson in lessons]
        + [step["text"] for lesson in lessons for step in lesson["steps"]]
    ).lower()
    for concept in (
        "counting numbers", "even numbers", "triangular", "square", "cube",
        "virahanka", "powers of 2", "powers of 3", "regular polygon",
        "complete graph", "stacked", "koch snowflake", "192",
    ):
        assert concept in combined, f"Chapter 1 missing concept: {concept}"
    ids = [lesson["id"] for lesson in lessons]
    assert len(ids) == len(set(ids))
    for lesson in lessons:
        assert len(lesson["steps"]) >= 3, lesson["id"]
        assert lesson["challenge"]["question"].strip(), lesson["id"]
        assert lesson["challenge"]["answer"] in lesson["challenge"]["options"], lesson["id"]
        assert lesson["challenge"]["hint"].strip(), lesson["id"]
        refs = lesson.get("source_refs", [])
        assert refs, f"{lesson['id']} has no stored textbook reference"
        assert all(ref["source_id"] == "6cd135e7-63e4-4350-9b7c-02fe1f566ec3" for ref in refs)
        assert all(ref["page_start"] <= ref["page_end"] for ref in refs)



def test_tutor_speech_rejects_internal_voice_instructions_and_strips_say_tags():
    assert curriculum._contains_tutor_meta_instructions(
        "VOICE DIRECTION: do not say these directions aloud."
    )
    assert curriculum._contains_tutor_meta_instructions(
        "Speak ONLY the exact words between the SAY tags below."
    )
    assert not curriculum._contains_tutor_meta_instructions(
        "Let us learn how plants make their food."
    )
    assert curriculum._clean_tutor_speech_text("<SAY>Let us learn plants.</SAY>") == "Let us learn plants."
    try:
        curriculum._clean_tutor_speech_text("Voice direction: speak gently.")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 422
    else:
        raise AssertionError("internal voice directions must not reach speech playback")


def test_pcm_tail_fade_reduces_final_samples_without_changing_audio_length():
    sample_rate = 1000
    raw = b"".join((12000).to_bytes(2, "little", signed=True) for _ in range(100))
    faded = curriculum._fade_pcm_tail(raw, sample_rate, fade_ms=80)
    assert len(faded) == len(raw)
    original_samples = [int.from_bytes(raw[i:i + 2], "little", signed=True) for i in range(0, len(raw), 2)]
    faded_samples = [int.from_bytes(faded[i:i + 2], "little", signed=True) for i in range(0, len(faded), 2)]
    assert faded_samples[0] == original_samples[0]
    assert abs(faded_samples[-1]) <= 1
    assert abs(faded_samples[-2]) < abs(original_samples[-2])
