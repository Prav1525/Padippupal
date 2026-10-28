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

    def test_empty_or_missing_sequence_produces_no_unrelated_visual(self):
        self.assertEqual(build_visual_records("lesson-2", {}), [])
        self.assertEqual(build_visual_records("lesson-2", {"teaching_sequence": []}), [])

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


if __name__ == "__main__":
    unittest.main()


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
