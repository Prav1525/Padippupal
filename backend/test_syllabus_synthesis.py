import unittest

from syllabus_synthesis import (
    EvidenceChunk,
    build_evidence_packet,
    evidence_fingerprint,
    group_chapter_evidence,
    make_run_id,
    validate_synthesis_payload,
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


if __name__ == "__main__":
    unittest.main()
