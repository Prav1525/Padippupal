import json
import unittest
from argparse import Namespace
import visual_engine as engine


def args(**overrides):
    data = dict(subject="Mathematics", chapter="Patterns in Mathematics", topic="Repeating patterns",
        medium="English", source_id="test-source", source_page=12, evidence_status="source_verified",
        format="svg", out="/tmp/pattern.svg")
    data.update(overrides)
    return Namespace(**data)


class VisualEngineTests(unittest.TestCase):
    def test_pattern_renderer_has_sequence_and_source_metadata(self):
        a=args(); family=engine.classify(a.subject,a.topic,a.chapter); out=engine.svg(a,family)
        self.assertEqual(family,"math_patterns")
        self.assertIn("Find what repeats",out)
        self.assertIn("test-source",out)
        self.assertIn("source_verified",out)

    def test_water_states_shows_all_three_states(self):
        a=args(subject="Science",chapter="A Journey through States of Water",topic="States of water")
        out=engine.svg(a,engine.classify(a.subject,a.topic,a.chapter))
        for label in (">Solid<",">Liquid<",">Gas<"): self.assertIn(label,out)

    def test_unsupported_topic_fails_closed(self):
        with self.assertRaises(engine.VisualError):
            engine.classify("Science","Unmapped topic","Unknown chapter")

    def test_unreviewed_evidence_is_rejected(self):
        with self.assertRaises(engine.VisualError): engine.validate(args(evidence_status="needs_review"))

    def test_invalid_page_is_rejected(self):
        with self.assertRaises(engine.VisualError): engine.validate(args(source_page=0))

    def test_excalidraw_export_is_valid_json(self):
        data=json.loads(engine.excalidraw(args(),"math_patterns"))
        self.assertEqual(data["type"],"excalidraw")
        self.assertEqual(len(data["elements"]),4)

    def test_manim_export_is_source_not_a_rendered_video(self):
        source=engine.manim_source(args(),"math_patterns")
        self.assertIn("class PadippuPalTopicVisual(Scene)",source)
        self.assertIn("Source-checked animation steps required",source)


if __name__=="__main__": unittest.main()
