from __future__ import annotations

import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "samples" / "science_beyond_earth_inline.py"
spec = importlib.util.spec_from_file_location("science_beyond_earth_inline", SCRIPT)
assert spec and spec.loader
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


def test_chapter_pilot_has_three_module_owned_visuals():
    assert [module["id"] for module in pilot.MODULES] == [
        "earth-moon-sun", "day-and-night", "phases-of-the-moon"
    ]
    assert all(module["narration"] and module["caption"] and module["prompt"] for module in pilot.MODULES)


def test_svg_outputs_are_original_and_topic_specific():
    for module, expected in zip(pilot.MODULES, ("Sun", "DAY", "Moon")):
        svg = pilot.render_svg(module)
        assert svg.startswith("<svg ")
        assert f"<title id=\"title\">{module['topic']}</title>" in svg
        assert expected in svg
        assert "role=\"img\"" in svg


def test_excalidraw_exports_contain_drawable_elements():
    for module in pilot.MODULES:
        board = pilot.render_excalidraw(module)
        assert board["type"] == "excalidraw"
        assert len(board["elements"]) >= 8
        assert any(element["type"] in {"ellipse", "rectangle"} for element in board["elements"])
        assert any(element["type"] == "text" for element in board["elements"])


def test_every_asset_stays_draft_and_inline_without_database_writes():
    manifest = {
        "assets": [
            {
                "approval_status": "draft",
                "active": False,
                "database_written": False,
                "render_mode": "inline_below_module",
                "overlay": False,
            }
            for _ in pilot.MODULES
        ],
        "database_writes": 0,
        "learner_activation": False,
    }
    assert len(manifest["assets"]) == 3
    assert all(asset["approval_status"] == "draft" for asset in manifest["assets"])
    assert all(asset["active"] is False and asset["database_written"] is False for asset in manifest["assets"])
    assert all(asset["render_mode"] == "inline_below_module" and asset["overlay"] is False for asset in manifest["assets"])
    assert manifest["database_writes"] == 0
    assert manifest["learner_activation"] is False


def test_excalidraw_payload_is_json_serializable():
    for module in pilot.MODULES:
        encoded = json.dumps(pilot.render_excalidraw(module))
        assert json.loads(encoded)["type"] == "excalidraw"
