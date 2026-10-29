import importlib.util
import unittest
from pathlib import Path

PATH=Path(__file__).with_name("generate_science_chapter1.py")
SPEC=importlib.util.spec_from_file_location("chapter1_pipeline",PATH)
pipeline=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)

class Chapter1PipelineTests(unittest.TestCase):
    def test_seven_chapter_visual_intents_are_topic_specific(self):
        cases=[
          ("The Wonderful World of Science — Part 1","curiosity","flower bloom curiosity"),
          ("The Wonderful World of Science — Part 2","jigsaw","giant and unending jigsaw puzzle"),
          ("The Wonderful World of Science — Part 3","everyday_objects","paper metal key plastic ruler rubber eraser"),
          ("The Wonderful World of Science — Part 4","pen_inquiry","pen stops writing guess ink refill"),
          ("The Wonderful World of Science — Part 5","scientific_method","observe question guess test analyse results"),
          ("The Wonderful World of Science — Part 6","daily_life","daily life examples cooking bicycle tyre bulb switch"),
          ("The Wonderful World of Science — Part 7","curiosity","continuing questions journey ahead"),
        ]
        for topic,expected,evidence in cases:
            with self.subTest(topic=topic):
                self.assertEqual(pipeline.family(topic,"",evidence),expected)
                svg=pipeline.svg_scene(topic,expected,evidence)
                self.assertIn("<svg",svg)
                self.assertIn(topic,svg)

    def test_ocr_and_timestamp_contamination_is_flagged(self):
        flags=pipeline.clean_text("Or watched a flower bloom. Chapter 1.indd 1 10/18/2024 9:49:28 AM fi nd")
        self.assertIn("running_header_or_timestamp",flags)
        self.assertIn("ocr_split_word",flags)
        self.assertIn("malformed_ocr_sentence",flags)

    def test_no_unknown_generic_visual_family(self):
        with self.assertRaises(ValueError):
            pipeline.family("Unmapped topic","unknown","")

if __name__=="__main__": unittest.main()
