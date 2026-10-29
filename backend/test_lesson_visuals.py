import json
import unittest

from lesson_visuals import build_visual_records


class SynthesizedLessonVisualTests(unittest.TestCase):
    def setUp(self):
        self.lesson = {
            "chapter_title": "Fractions",
            "teaching_sequence": [
                {
                    "id": "fraction-whole",
                    "title": "Split a whole",
                    "caption": "A fraction shows equal parts of one whole.",
                    "teacher_says": "Look at these four equal parts.",
                    "source_chunk_ids": ["chunk-12"],
                    "visual": {
                        "type": "fraction",
                        "objects": ["one whole", "four equal parts", "one shaded part"],
                        "actions": ["shade one part"],
                        "narration_sync": ["four equal parts"],
                        "spatial_relationships": ["four equal-sized parts make one whole"],
                        "teaching_order": ["show the whole", "divide into four equal parts", "shade one part"],
                        "reference_page_numbers": [12],
                    },
                },
                {
                    "id": "fraction-recap",
                    "title": "Remember the rule",
                    "caption": "The bottom number tells how many equal parts make the whole.",
                    "source_chunk_ids": ["chunk-12", "chunk-13"],
                    "visual": {"type": "diagram", "objects": ["denominator", "equal parts"]},
                },
            ],
        }

    def test_visual_records_map_one_to_one_to_synthesis_steps(self):
        records = build_visual_records("lesson-1", self.lesson)
        self.assertEqual([r["step_id"] for r in records], ["fraction-whole", "fraction-recap"])
        self.assertEqual(records[0]["summary_text"], self.lesson["teaching_sequence"][0]["caption"])
        self.assertEqual(records[0]["source_chunk_ids_json"], '["chunk-12"]')
        self.assertEqual(records[0]["blueprint"]["nodes"], ["one whole", "four equal parts", "one shaded part"])
        self.assertEqual(records[0]["blueprint"]["reference_page_numbers"], [12])
        self.assertEqual(records[0]["blueprint"]["spatial_relationships"], ["four equal-sized parts make one whole"])
        self.assertEqual(records[0]["blueprint"]["animation_plan"]["stages"], ["show the whole", "divide into four equal parts", "shade one part"])

    def test_visuals_are_small_static_2d_blueprints(self):
        records = build_visual_records("lesson-1", self.lesson)
        for record in records:
            blueprint = record["blueprint"]
            self.assertEqual(blueprint["layout"], "compact_2d")
            self.assertEqual(blueprint["motion"], "narration_synced_staggered_reveal")
            self.assertEqual(blueprint["animation_plan"]["mode"], "staggered_reveal")
            self.assertFalse(blueprint["animation_plan"]["loop"])
            self.assertLessEqual(blueprint["animation_plan"]["duration_ms"], 1000)
            self.assertNotIn("3d", json.dumps(blueprint).lower())
            self.assertLessEqual(len(blueprint["nodes"]), 6)

    def test_fingerprint_is_stable_and_changes_with_synthesis(self):
        first = build_visual_records("lesson-1", self.lesson)
        second = build_visual_records("lesson-1", self.lesson)
        self.assertEqual([r["content_fingerprint"] for r in first],
                         [r["content_fingerprint"] for r in second])
        self.lesson["teaching_sequence"][0]["caption"] = "A fraction names equal parts of a whole."
        changed = build_visual_records("lesson-1", self.lesson)
        self.assertNotEqual(first[0]["content_fingerprint"], changed[0]["content_fingerprint"])

    def test_sequence_alias_uses_sequence_renderer_not_generic_concept_card(self):
        lesson = {"teaching_sequence": [{
            "id": "all-ones",
            "title": "All 1s",
            "caption": "Each term stays 1.",
            "source_chunk_ids": ["chunk-pattern-1"],
            "visual": {"type": "sequence", "objects": ["1", "1", "1", "1", "1"]},
        }]}
        record = build_visual_records("lesson-pattern", lesson)[0]
        self.assertEqual(record["visual_kind"], "sequence")
        self.assertEqual(record["blueprint"]["kind"], "sequence")
        self.assertIn('<rect x="', record["blueprint"]["svg_markup"])
        self.assertEqual(record["source_chunk_ids_json"], '["chunk-pattern-1"]')

    def test_empty_or_missing_sequence_produces_no_unrelated_visual(self):
        self.assertEqual(build_visual_records("lesson-2", {}), [])
        self.assertEqual(build_visual_records("lesson-2", {"teaching_sequence": []}), [])

    def test_sparse_textbook_table_infers_the_explicit_all_ones_sequence(self):
        lesson = {"teaching_sequence": [{
            "id": "all-ones-table-row",
            "title": "Patterns in Mathematics — Part 1",
            "caption": ("Mathematics is, in large part, the search for patterns and explanations. "
                        + ("Introductory textbook passage. " * 12)
                        + "Table of number sequences: Squares 1 4 9 16 25. All 1’s 1 1 1 1 1. Counting numbers 1 2 3 4 5."),
            "source_chunk_ids": ["chunk-patterns-page-1"],
            "visual": {"type": "table", "objects": []},
        }]}
        record = build_visual_records("lesson-patterns", lesson)[0]
        self.assertEqual(record["visual_kind"], "sequence")
        self.assertEqual(record["blueprint"]["nodes"], ["1", "1", "1", "1", "1"])
        self.assertLessEqual(len(record["summary_text"]), 160)
        self.assertIn("narration_synced_staggered_reveal", record["blueprint"]["motion"])

    def test_sparse_table_without_grounded_visual_evidence_is_skipped(self):
        lesson = {"teaching_sequence": [{
            "id": "generic",
            "title": "A chapter introduction",
            "caption": "Let us read this introduction carefully and discuss what it says.",
            "source_chunk_ids": ["chunk-generic"],
            "visual": {"type": "table", "objects": []},
        }]}
        self.assertEqual(build_visual_records("lesson-generic", lesson), [])

    def test_svg_is_stored_with_blueprint_and_escapes_lesson_labels(self):
        lesson = {"teaching_sequence": [{
            "id": "safe-label",
            "title": 'A < B',
            "caption": "Compare the two values.",
            "source_chunk_ids": ["chunk-1"],
            "visual": {"type": "compare", "objects": ['A < B', 'C & D']},
        }]}
        record = build_visual_records("lesson-safe", lesson)[0]
        svg = record["blueprint"]["svg_markup"]
        self.assertIn("<svg", svg)
        self.assertIn("compact_2d", record["blueprint"]["layout"])
        self.assertIn("A &lt; B", svg)
        self.assertIn("C &amp; D", svg)
        self.assertNotIn("< B", svg)
        self.assertEqual(json.loads(record["blueprint_json"])["svg_markup"], svg)


    def test_chapter_one_science_uses_source_specific_visuals_not_ocr_fraction_or_magnet_fallback(self):
        lesson = {"chapter_title": "The Wonderful World of Science", "teaching_sequence": [
            {"id": "step_1", "title": "The Wonderful World of Science — Part 1",
             "caption": "We have always been curious. Have you watched a flower bloom and wondered how it knows when to open?",
             "source_chunk_ids": ["ncert-page-1"], "visual": {"type": "table", "objects": []}},
            {"id": "step_2", "title": "Science as a jigsaw puzzle",
             "caption": "Science is like a giant and unending jigsaw puzzle. Every new discovery adds another piece.",
             "source_chunk_ids": ["ncert-page-2"], "visual": {"type": "table", "objects": []}},
            {"id": "step_3", "title": "Things around us",
             "caption": "Paper, metal key, plastic ruler and rubber eraser are things around us. Are they made of different materials?",
             "source_chunk_ids": ["ncert-page-4"], "visual": {"type": "table", "objects": []}},
            {"id": "step_4", "title": "Test a guess",
             "caption": "Your pen stops writing. You ask why, guess the ink is finished, and test this guess.",
             "source_chunk_ids": ["ncert-page-5"], "visual": {"type": "table", "objects": []}},
            {"id": "step_5", "title": "Scientific method",
             "caption": "The scientific method starts with observation and a question, then we test the guess and analyse the results. Reprint 2026-27.",
             "source_chunk_ids": ["ncert-page-6"], "visual": {"type": "table", "objects": []}},
            {"id": "step_6", "title": "Learning together",
             "caption": "Scientists work together in teams and learn from friends. We may not find every answer right away.",
             "source_chunk_ids": ["ncert-page-7"], "visual": {"type": "table", "objects": []}},
            {"id": "step_7", "title": "Keep wondering",
             "caption": "Enjoy your scientific journey, keep exploring and never stop wondering about mysteries of the universe.",
             "source_chunk_ids": ["ncert-page-8"], "visual": {"type": "table", "objects": []}},
        ]}
        records = build_visual_records("chapter-1", lesson)
        by_step = {row["step_id"]: row for row in records}
        self.assertEqual(by_step["step_1"]["visual_kind"], "curiosity")
        self.assertEqual(by_step["step_1"]["blueprint"]["nodes"], ["Notice", "Wonder", "Ask why"])
        self.assertEqual(by_step["step_2"]["visual_kind"], "jigsaw")
        self.assertEqual(by_step["step_3"]["visual_kind"], "material_examples")
        self.assertEqual(by_step["step_3"]["blueprint"]["nodes"], ["Paper", "Metal key", "Plastic ruler", "Rubber eraser"])
        self.assertEqual(by_step["step_4"]["visual_kind"], "scientific_method")
        self.assertEqual(by_step["step_5"]["visual_kind"], "scientific_method")
        self.assertEqual(by_step["step_6"]["visual_kind"], "collaborative_exploration")
        self.assertEqual(by_step["step_7"]["visual_kind"], "curiosity")
        self.assertNotEqual(by_step["step_5"]["visual_kind"], "fraction")
        for row in records:
            self.assertIn("<svg", row["blueprint"]["svg_markup"])
            self.assertTrue(row["source_chunk_ids_json"].startswith('["ncert-page-'))


if __name__ == "__main__":
    unittest.main()


def test_dynamic_tutor_visuals_are_saved_under_the_exact_selected_topic(tmp_path, monkeypatch):
    import app as curriculum

    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "topic-visual-assets.sqlite3")
    curriculum.init_db()
    payload = curriculum.LessonPlanRequest(
        board="CBSE", class_level=6, subject="Mathematics", medium="English",
        message="Explain the All 1s pattern", chapter="Patterns in Mathematics",
        topic="All 1s",
    )
    segments = [{
        "id": "segment-1",
        "spoken_text": "In the All 1s pattern, every term stays 1.",
        "caption_text": "In the All 1s pattern, every term stays 1.",
        "source_chunk_ids": ["chunk-pattern-page-1"],
        "visual_action": {"type": "highlight", "target": "1", "value": "repeat each time"},
    }]
    sources = [{"chunk_id": "chunk-pattern-page-1", "page_start": 1, "page_end": 1}]
    result = curriculum.attach_topic_visuals(payload, segments, sources)
    inline = result[0]["interactive_lesson"]
    assert inline["topic"] == "All 1s"
    assert inline["visual_kind"] == "sequence"
    assert inline["steps"][0]["nodes"] == ["1", "1", "1", "1", "1"]
    assert inline["reference_page_numbers"] == [1]

    with curriculum.db() as conn:
        rows = conn.execute(
            "SELECT board, class_level, subject, chapter, topic, source_chunk_ids_json, active "
            "FROM tutor_topic_visual_assets"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0]["topic"] == "All 1s"
    assert rows[0]["chapter"] == "Patterns in Mathematics"
    assert rows[0]["source_chunk_ids_json"] == '["chunk-pattern-page-1"]'
    assert rows[0]["active"] == 1


def test_visual_blueprints_are_persisted_and_updated_with_the_synthesis(tmp_path, monkeypatch):
    import app as curriculum

    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "visual-assets.sqlite3")
    curriculum.init_db()
    lesson_id = "visual-persistence-test"
    lesson = {
        "chapter_title": "Fractions",
        "overview": "A fraction names equal parts of a whole.",
        "teaching_sequence": [{
            "id": "fraction-step-1",
            "title": "Equal parts",
            "caption": "A fraction names equal parts of one whole.",
            "source_chunk_ids": ["chunk-fraction-1"],
            "visual": {"type": "fraction", "objects": ["whole", "four equal parts"]},
        }],
    }
    now = 1.0
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO chapter_lessons
               (id, board, class_level, subject, medium, chapter, topic, status,
                lesson_json, source_refs_json, model, review_feedback, created_at, updated_at)
               VALUES (?, 'CBSE', 5, 'Mathematics', 'English', 'Fractions', 'Equal parts',
                       'approved', ?, '[]', '', '', ?, ?)""",
            (lesson_id, json.dumps(lesson), now, now),
        )

    first = curriculum.get_or_create_lesson_visuals(lesson_id, lesson)
    assert len(first) == 1
    assert first[0]["step_id"] == "fraction-step-1"
    assert first[0]["source_chunk_ids"] == ["chunk-fraction-1"]
    assert first[0]["layout"] == "compact_2d"
    assert first[0]["animation"] == "narration_synced_2d"

    revised = json.loads(json.dumps(lesson))
    revised["teaching_sequence"][0]["caption"] = "One whole can be split into equal parts."
    second = curriculum.get_or_create_lesson_visuals(lesson_id, revised)
    assert second[0]["summary_text"] == "One whole can be split into equal parts."
    assert second[0]["content_fingerprint"] != first[0]["content_fingerprint"]
    inline = curriculum.build_inline_synthesized_visual(lesson_id, revised, second, topic="Equal parts")
    assert inline["topic"] == "Equal parts"
    assert inline["title"] == "Equal parts"
    assert inline["scene_type"] == "synthesis_static"
    assert inline["animation"] == "narration_synced_2d"

    with curriculum.db() as conn:
        rows = conn.execute(
            "SELECT COUNT(*) AS count FROM lesson_visual_assets WHERE lesson_id=? AND active=1",
            (lesson_id,),
        ).fetchone()
    assert rows["count"] == 1


def test_approved_topic_synthesis_visual_backfill_persists_only_source_cited_topics(tmp_path, monkeypatch):
    import app as curriculum

    monkeypatch.setattr(curriculum, "DATABASE_URL", "")
    monkeypatch.setattr(curriculum, "DB_PATH", tmp_path / "approved-topic-visuals.sqlite3")
    curriculum.init_db()
    now = 1.0
    with curriculum.db() as conn:
        conn.execute(
            """INSERT INTO sources
               (id, board, academic_year, class_level, subject, medium, term, edition,
                title, source_url, license_note, sha256, status, page_count, created_at)
               VALUES ('source-water', 'CBSE', '2026', 5, 'Science', 'English', '', '1',
                       'Class 5 Science', '', 'approved textbook', 'sha-water', 'ready', 1, ?)""",
            (now,),
        )
        conn.execute(
            """INSERT INTO chunks (id, source_id, chunk_no, chapter, page_start, page_end, text)
               VALUES ('water-chunk-1', 'source-water', 0, 'Water Cycle', 12, 12,
                       'Water evaporates, condenses into clouds and returns as precipitation.')"""
        )
        conn.execute(
            """INSERT INTO syllabus_synthesis_rounds
               (id, source_id, board, class_level, subject, chapter, curriculum_version, status,
                model, prompt_version, source_chunk_ids_json, evidence_fingerprint, validation_json,
                error_message, created_at, updated_at)
               VALUES ('round-water', 'source-water', 'CBSE', 5, 'Science', 'Water Cycle', 'v1',
                       'approved', 'test-model', 'v1', '["water-chunk-1"]', 'fingerprint',
                       '{}', '', ?, ?)""",
            (now, now),
        )
        conn.execute(
            """INSERT INTO syllabus_topic_syntheses
               (id, round_id, source_id, topic, page_start, page_end, learning_objectives_json,
                explanation_json, examples_json, practice_questions_json, citation_refs_json,
                validation_status, validation_notes_json, approval_status, created_at, updated_at)
               VALUES ('topic-water', 'round-water', 'source-water', 'Water Cycle', 12, 12,
                       '["Explain evaporation and condensation"]',
                       '{"simple_explanation":"In the water cycle, water evaporates, condenses into clouds, and returns as precipitation."}',
                       '["Sunlight warms water and starts evaporation."]', '[]',
                       '["water-chunk-1"]', 'approved', '[]', 'approved', ?, ?)""",
            (now, now),
        )

    curriculum._backfill_approved_topic_synthesis_visuals()

    with curriculum.db() as conn:
        rows = conn.execute(
            """SELECT topic, chapter, source_chunk_ids_json, active, blueprint_json
               FROM tutor_topic_visual_assets WHERE topic='Water Cycle'"""
        ).fetchall()
    assert rows
    assert all(row["topic"] == "Water Cycle" and row["chapter"] == "Water Cycle" for row in rows)
    assert all(row["source_chunk_ids_json"] == '["water-chunk-1"]' for row in rows)
    assert all(row["active"] == 1 for row in rows)
    assert all("svg_markup" in json.loads(row["blueprint_json"]) for row in rows)
