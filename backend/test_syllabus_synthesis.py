import unittest

from syllabus_synthesis import (
    EvidenceChunk,
    build_evidence_packet,
    evidence_fingerprint,
    group_chapter_evidence,
    make_run_id,
    validate_synthesis_payload,
    validate_chapter_lesson_payload,
)


class SyllabusSynthesisTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            EvidenceChunk("chunk-b", "book-1", "Chapter A", 1, 2, 2, "Second page evidence"),
            EvidenceChunk("chunk-a", "book-1", "Chapter A", 0, 1, 1, "First page evidence"),
        ]

    def test_fingerprint_is_stable_for_input_order(self):
        self.assertEqual(evidence_fingerprint(self.chunks), evidence_fingerprint(list(reversed(self.chunks))))

    def test_fingerprint_changes_when_evidence_changes(self):
        changed = self.chunks + [EvidenceChunk("chunk-c", "book-1", "Chapter A", 2, 3, 3, "New evidence")]
        self.assertNotEqual(evidence_fingerprint(self.chunks), evidence_fingerprint(changed))

    def test_packet_requires_one_source_and_chapter(self):
        packet = build_evidence_packet(self.chunks)
        self.assertEqual(packet["chapter"], "Chapter A")
        self.assertEqual(packet["page_start"], 1)
        self.assertEqual(packet["page_end"], 2)
        with self.assertRaises(ValueError):
            build_evidence_packet(self.chunks + [
                EvidenceChunk("other", "book-2", "Chapter A", 3, 3, 3, "Other source")
            ])

    def test_grouping_skips_missing_chapter_or_text(self):
        rows = [
            {"id": "1", "source_id": "s", "chapter": "A", "chunk_no": 1, "text": "hello"},
            {"id": "2", "source_id": "s", "chapter": "", "chunk_no": 2, "text": "skip"},
            {"id": "3", "source_id": "s", "chapter": "A", "chunk_no": 3, "text": ""},
        ]
        grouped = group_chapter_evidence(rows)
        self.assertEqual(list(grouped), ["A"])
        self.assertEqual(len(grouped["A"]), 1)

    def test_payload_rejects_unknown_citations(self):
        result = validate_synthesis_payload({
            "topics": [{
                "topic": "Observation",
                "learning_objectives": ["Explain observation"],
                "explanation": "Observe carefully.",
                "citation_refs": ["missing-chunk"],
            }]
        }, {"real-chunk"})
        self.assertFalse(result["valid"])
        self.assertTrue(any("unknown chunks" in error for error in result["errors"]))

    def test_valid_payload_and_deterministic_run_id(self):
        payload = {"topics": [{
            "topic": "Observation",
            "learning_objectives": ["Explain observation"],
            "explanation": "Observe carefully.",
            "citation_refs": ["real-chunk"],
        }]}
        result = validate_synthesis_payload(payload, {"real-chunk"})
        self.assertTrue(result["valid"])
        self.assertEqual(
            make_run_id("book", "Chapter A", "v1", "fingerprint"),
            make_run_id("book", "Chapter A", "v1", "fingerprint"),
        )


    def test_chapter_lesson_validator_requires_complete_teaching_contract(self):
        lesson = {
            "chapter_title": "Chapter A",
            "overview": "A source-grounded overview.",
            "learning_objectives": ["Explain the central idea."],
            "concept_map": [{"concept": "Central idea", "source_chunk_ids": ["chunk-a"]}],
            "teaching_sequence": [{
                "title": "First step",
                "teacher_says": "Let us explore the idea.",
                "caption": "The key point is shown here.",
                "checkpoint": "What is the key point?",
                "source_chunk_ids": ["chunk-a"],
                "visual": {"type": "none"},
            }],
        }
        valid = validate_chapter_lesson_payload(lesson, {"chunk-a"})
        self.assertTrue(valid["valid"], valid["errors"])
        self.assertEqual(valid["topic_count"], 1)

        incomplete = dict(lesson)
        incomplete["teaching_sequence"] = [dict(lesson["teaching_sequence"][0])]
        incomplete["teaching_sequence"][0]["checkpoint"] = ""
        invalid = validate_chapter_lesson_payload(incomplete, {"chunk-a"})
        self.assertFalse(invalid["valid"])
        self.assertTrue(any("checkpoint" in error for error in invalid["errors"]))

    def test_chapter_lesson_validator_rejects_unknown_citations_and_empty_concepts(self):
        lesson = {
            "chapter_title": "Chapter A",
            "overview": "An overview.",
            "learning_objectives": ["Explain the idea."],
            "concept_map": [{"concept": "Central idea", "source_chunk_ids": ["outside-chunk"]}],
            "teaching_sequence": [{
                "title": "First step",
                "teacher_says": "Textbook-grounded explanation.",
                "caption": "Key point.",
                "checkpoint": "What did you learn?",
                "source_chunk_ids": ["chunk-a"],
                "visual": {"type": "none"},
            }],
        }
        invalid = validate_chapter_lesson_payload(lesson, {"chunk-a"})
        self.assertFalse(invalid["valid"])
        self.assertTrue(any("unknown source chunk" in error for error in invalid["errors"]))
        lesson["concept_map"] = []
        invalid_empty = validate_chapter_lesson_payload(lesson, {"chunk-a"})
        self.assertFalse(invalid_empty["valid"])
        self.assertTrue(any("concept_map must be a non-empty list" in error for error in invalid_empty["errors"]))


if __name__ == "__main__":
    unittest.main()
