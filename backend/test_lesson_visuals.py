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

    def test_unsupported_synthesis_topic_is_not_replaced_with_generic_title_card(self):
        lesson = {"teaching_sequence": [{
            "id": "unknown-topic",
            "title": "A newly synthesized unfamiliar concept",
            "caption": "The textbook describes a topic that has no reviewed renderer yet.",
            "source_chunk_ids": ["source-chunk-9"],
            "visual": {"type": "none", "objects": [], "narration_sync": ["A newly synthesized unfamiliar concept"]},
        }]}
        # The renderer must fail closed. The orchestration layer converts this
        # empty drawable result into an inactive needs_review asset.
        self.assertEqual(build_visual_records("lesson-unknown", lesson), [])

    def test_science_chapter_one_scenes_are_topic_specific(self):
        cases = [
            ("A pen stops writing", "When a pen stops writing, check the ink refill and test the explanation.", "process"),
            ("Science as a jigsaw", "Knowledge grows like a jigsaw as new discoveries create new questions.", "diagram"),
            ("Objects and materials", "Compare paper, a metal key, a plastic ruler and a rubber eraser by their materials.", "compare"),
            ("Scientific inquiry", "Observe the problem, ask a question, test a possible explanation and review evidence.", "process"),
        ]
        for title, caption, expected_kind in cases:
            with self.subTest(title=title):
                records = build_visual_records("profile", {"teaching_sequence": [{
                    "id": "topic-step", "title": title, "caption": caption,
                    "source_chunk_ids": ["source-1"],
                    "source_evidence": caption,
                    "visual": {"type": "none", "objects": [], "narration_sync": [title]},
                }]})
                self.assertEqual(len(records), 1)
                self.assertEqual(records[0]["visual_kind"], expected_kind)
                self.assertEqual(records[0]["blueprint"]["source_chunk_ids"], ["source-1"])
                self.assertIn("<svg", records[0]["blueprint"]["svg_markup"])


    def test_jigsaw_visual_is_a_connected_concept_map(self):
        record = build_visual_records("profile", {"teaching_sequence": [{
            "id": "jigsaw-step",
            "title": "Science as a jigsaw",
            "caption": "Knowledge grows like a jigsaw as discoveries create new questions.",
            "source_chunk_ids": ["source-jigsaw"],
            "source_evidence": "Science is like a giant jigsaw puzzle; discoveries lead to new questions.",
            "visual": {"type": "none", "objects": []},
        }]})[0]
        svg = record["blueprint"]["svg_markup"]
        self.assertEqual(record["visual_kind"], "diagram")
        self.assertIn("What we know", svg)
        self.assertIn("New discovery", svg)
        self.assertIn("New question", svg)

    def test_pen_inquiry_visual_shows_testable_hypothesis_steps(self):
        record = build_visual_records("profile", {"teaching_sequence": [{
            "id": "pen-step",
            "title": "A pen stops writing",
            "caption": "A pen stops writing; a possible cause is the ink refill, so check it.",
            "source_chunk_ids": ["source-pen"],
            "source_evidence": "When a pen stops writing, check the ink refill and test the explanation.",
            "visual": {"type": "none", "objects": []},
        }]})[0]
        svg = record["blueprint"]["svg_markup"]
        self.assertEqual(record["visual_kind"], "process")
        self.assertIn("Pen stops writing", svg)
        self.assertIn("Possible explanation", svg)
        self.assertIn("Check the refill", svg)

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


    def test_new_synthesis_step_is_renderable_with_exact_source_mapping(self):
        # Contract exercised by the synthesis-to-visual pipeline: one generated
        # topic produces one stable visual tied only to its cited source chunks.
        lesson = {
            "chapter_title": "The Wonderful World of Science",
            "topic": "Testing a possible explanation",
            "overview": "A guess should be tested with evidence.",
            "teaching_sequence": [{
                "id": "syn-abc123def456-1",
                "title": "Testing a possible explanation",
                "caption": "When a pen stops writing, check whether the ink refill is empty.",
                "teacher_says": "When a pen stops writing, check whether the ink refill is empty.",
                "source_chunk_ids": ["chunk-pen-1", "chunk-pen-2"],
                "visual": {
                    "type": "process",
                    "objects": ["Pen stops writing", "Possible guess", "Check refill"],
                    "narration_sync": ["Possible guess"],
                    "reference_page_numbers": [4, 5],
                },
            }],
        }
        records = build_visual_records("profile-key", lesson)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["step_id"], "syn-abc123def456-1")
        self.assertEqual(json.loads(record["source_chunk_ids_json"]), ["chunk-pen-1", "chunk-pen-2"])
        self.assertEqual(record["blueprint"]["reference_page_numbers"], [4, 5])
        self.assertIn("svg_markup", record["blueprint"])
        self.assertIn("Pen stops writing", record["blueprint"]["svg_markup"])
        self.assertTrue(record["content_fingerprint"])


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


def test_topic_specific_visual_engine_uses_cited_evidence_not_generic_cards():
    from lesson_visuals import build_visual_records

    cases = [
        ("The Wonderful World of Science — Part 2", "Knowledge is like a jigsaw puzzle; each discovery adds a piece.",
         "Our knowledge is like a giant and unending jigsaw puzzle.", "process",
         ["What we know", "New discovery", "New questions"]),
        ("Pen investigation", "If a pen stops writing, guess that the ink is empty and check the refill.",
         "A pen may stop writing; test whether the refill has ink.", "process",
         ["Pen stops writing", "Possible explanation", "Check the refill"]),
        ("Scientific inquiry", "Observe, ask, guess, test and analyse the results.",
         "Scientific inquiry: observe, ask a question, test the guess and review evidence.", "process",
         ["Observe", "Ask", "Guess", "Test", "Review results"]),
        ("Everyday objects", "Compare paper, a metal key, a plastic ruler and a rubber eraser.",
         "These objects are made of different materials: paper, a metal key, a plastic ruler and a rubber eraser.", "compare",
         ["Paper", "Metal key", "Plastic ruler", "Rubber eraser"]),
    ]
    for topic, caption, evidence, expected_kind, expected_nodes in cases:
        records = build_visual_records("profile-test", {
            "teaching_sequence": [{
                "id": "source-step-1", "title": topic, "caption": caption,
                "source_chunk_ids": ["chunk-source-1"], "source_evidence": evidence,
                "visual": {"type": "none", "objects": [], "evidence_status": "source_cited_draft"},
            }]
        })
        assert len(records) == 1
        blueprint = records[0]["blueprint"]
        assert blueprint["kind"] == expected_kind
        assert blueprint["nodes"] == expected_nodes
        assert blueprint["source_chunk_ids"] == ["chunk-source-1"]
        assert blueprint["evidence_status"] == "source_cited_draft"
        assert "svg_markup" in blueprint["svg_markup"] or blueprint["svg_markup"].startswith("<svg")


def test_visual_engine_preserves_quality_flags_and_never_activates_candidates():
    from lesson_visuals import build_visual_records

    records = build_visual_records("profile-test", {
        "teaching_sequence": [{
            "id": "ocr-step-1", "title": "Curiosity", "caption": "Notice something and ask why.",
            "source_chunk_ids": ["chunk-ocr-1"], "source_evidence": "Or watched a flower bloom. Chapter 1.indd 1",
            "visual": {"type": "none", "objects": [], "evidence_status": "needs_review",
                       "quality_flags": ["running_header_or_timestamp", "malformed_ocr_sentence"]},
        }]
    })
    assert len(records) == 1
    blueprint = records[0]["blueprint"]
    assert blueprint["evidence_status"] == "needs_review"
    assert "running_header_or_timestamp" in blueprint["quality_flags"]
    assert "malformed_ocr_sentence" in blueprint["quality_flags"]


def test_science_chapter1_pen_inquiry_gets_topic_specific_scene():
    lesson = {"chapter_title": "The Wonderful World of Science", "teaching_sequence": [{
        "id": "pen-inquiry", "title": "A pen stops writing",
        "caption": "When a pen stops writing, one possible explanation is that the ink refill is empty. Check the refill to test the guess.",
        "source_chunk_ids": ["source-pen-page-4"],
        "visual": {"type": "process", "objects": ["A pen stops writing", "Ink refill"]},
    }]}
    record = build_visual_records("science-ch1", lesson)[0]
    assert record["visual_kind"] == "process"
    assert record["blueprint"]["nodes"] == ["Pen stops writing", "Possible explanation", "Check the refill"]
    assert "Check the refill" in record["blueprint"]["svg_markup"]
    assert json.loads(record["source_chunk_ids_json"]) == ["source-pen-page-4"]


def test_science_chapter1_jigsaw_gets_connected_concept_map():
    lesson = {"chapter_title": "The Wonderful World of Science", "teaching_sequence": [{
        "id": "knowledge-jigsaw", "title": "Science is a growing jigsaw",
        "caption": "Knowledge is like a jigsaw puzzle: each new discovery adds a piece and leads to new questions.",
        "source_chunk_ids": ["source-science-page-2"],
        "visual": {"type": "diagram", "objects": ["Knowledge", "Discovery"]},
    }]}
    record = build_visual_records("science-ch1", lesson)[0]
    assert record["visual_kind"] == "process"
    svg = record["blueprint"]["svg_markup"]
    assert "What we know" in svg
    assert "New discovery" in svg
    assert "New questions" in svg


def test_science_chapter1_inquiry_process_gets_ordered_steps():
    lesson = {"chapter_title": "The Wonderful World of Science", "teaching_sequence": [{
        "id": "scientific-inquiry", "title": "Scientific inquiry",
        "caption": "Observe a problem, ask a question, suggest a possible explanation, test it, and review the evidence.",
        "source_chunk_ids": ["source-science-page-5"],
        "visual": {"type": "process", "objects": ["Observe", "Test"]},
    }]}
    record = build_visual_records("science-ch1", lesson)[0]
    assert record["visual_kind"] == "process"
    assert record["blueprint"]["nodes"] == ["Observe", "Ask", "Guess", "Test", "Review results"]
    assert json.loads(record["source_chunk_ids_json"]) == ["source-science-page-5"]
