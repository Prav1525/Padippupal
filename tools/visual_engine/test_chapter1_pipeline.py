import importlib.util
import json
import unittest
from pathlib import Path

PATH=Path(__file__).with_name("generate_science_chapter1.py")
SPEC=importlib.util.spec_from_file_location("chapter1_pipeline",PATH)
pipeline=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)

FIXTURES=PATH.parent/"fixtures"/"science_chapter1"

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

    def test_fixture_manifest_uses_verified_live_synthesis_ids_and_chunk_ids(self):
        manifest=json.loads((FIXTURES/"manifest.json").read_text(encoding="utf-8"))
        expected=[
          ("98c502390c68f17e1a94e3f8b376db8039c15ffa983b465233a3261d74368083",["85e8fe7b-ba04-45e3-8e88-54770f76a11b","540d5b48-97fc-4a93-8251-1b3e177b4b61"]),
          ("a8d0b8714c2d726dc9d92f11751f74e5bc661f845b3b7cd8fd5ee9f41259af8f",["c87f3be1-35c5-4b1e-b769-2e53850f6de5","51c5eeae-dcb2-4c04-a2ef-90e7fe5f6fc0"]),
          ("bc8c23f4f2ffe8df3b621a2dc8a6689369eb259a7a6409a6e02a1758c90323f2",["f03c46cb-1a45-403b-89b1-7a56640e8b08","4a6a000d-ae81-4737-8121-f52375ed449c"]),
          ("30b3765025c95e342ae45174ff82a6e0247d457582b1cc2449766c28227b48c5",["8caf1fd6-b2f3-436b-a7b9-f37c99e44e99","0988f81b-21f7-4e16-9f5b-8224f72a1767"]),
          ("15f19c0f4077e3a277eab4a9de1b0d13e8a6b373014afdc411b03a0fe298cae5",["35d81817-d498-4c4c-9d46-d826259ece45","d5075a26-dc9d-457b-aab7-de1059240635"]),
          ("a5ab26dbc69d1f5a7b459d9c677def8d76cdc2757f33ab63fd6e82cd85793995",["14256fbc-cb64-43bb-8051-56ad2b0a53fe","23e47207-f97d-475c-8654-93de2a43a73b"]),
          ("99cb9f298d8376e2c5a6bd86e8f85945397f0de6adbed83b8158f9a14bbce6ea",["012dbf53-fad3-4312-96fd-1386c8535ba0"]),
        ]
        self.assertEqual(len(manifest["assets"]),7)
        for asset,(synthesis_id,chunk_ids) in zip(manifest["assets"],expected):
            with self.subTest(part=asset["topic_part"]):
                self.assertEqual(asset["synthesis_id"],synthesis_id)
                self.assertEqual(asset["chunks"],chunk_ids)
                self.assertFalse(asset.get("active",False))
        part2=json.loads((FIXTURES/"part-2.json").read_text(encoding="utf-8"))
        self.assertEqual(part2["synthesis_id"],expected[1][0])
        self.assertEqual(part2["source_chunk_ids"],expected[1][1])
        self.assertFalse(part2["active"])
        self.assertFalse(part2["database_written"])

if __name__=="__main__": unittest.main()
