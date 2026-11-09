from __future__ import annotations
import json
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import render_lesson_visuals as renderer


def test_every_curated_visual_renders_as_phone_first_png(tmp_path):
    manifest = json.loads((ROOT / "assets/lesson-images/authoring-manifest.json").read_text())
    assert len(manifest["images"]) >= 20
    rendered = 0
    for item in manifest["images"]:
        assert item["layout"] in {"single", "pair"}
        assert len(item["panels"]) == (1 if item["layout"] == "single" else 2)
        for index, panel in enumerate(item["panels"], 1):
            out = tmp_path / f"{rendered}-{index}.png"
            renderer.render_panel(panel, out, index, len(item["panels"]))
            with Image.open(out) as image:
                assert image.format == "PNG"
                assert image.size == (1080, 720)
            rendered += 1
    assert rendered >= 20


def test_pair_layout_is_two_full_width_panels(tmp_path):
    first = renderer.render_panel({"heading": "First idea", "diagram": "fractions", "parts": 4, "shaded": 1},
                                  tmp_path / "first.png", 1, 2)
    second = renderer.render_panel({"heading": "Second idea", "diagram": "number_line"},
                                   tmp_path / "second.png", 2, 2)
    assert Image.open(first).size == (1080, 720)
    assert Image.open(second).size == (1080, 720)
