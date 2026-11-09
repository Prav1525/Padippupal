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


def test_manifest_has_unique_module_mappings_and_supported_diagrams():
    manifest = json.loads((ROOT / "assets/lesson-images/authoring-manifest.json").read_text())
    keys = [(item["lesson_id"], item["module_key"], tuple(item["step_ids"])) for item in manifest["images"]]
    assert len(keys) == len(set(keys))
    assert len(manifest["images"]) >= 60
    supported = {
        "fractions", "rectangle_properties", "decantation", "scientific_method", "angle", "four_point_lines",
        "area_perimeter", "symmetry", "bar_graph", "water_states", "seedling", "plant",
        "magnet", "separation", "thermometer", "ruler_measurement", "sun_energy",
        "number_line", "orbit", "solar_system", "constellation", "leaf_venation",
        "solubility", "food_variety", "factor_tree", "triangle_pattern",
        "number_ray", "perimeter_rectangle", "nutrient_sources", "tea_filter", "seed_germination",
        "fraction_number_line", "equivalent_fractions", "fraction_addition", "fraction_compare",
        "protractor", "clock_angles", "number_patterns", "odd_numbers_square", "square_growth",
        "polygon_perimeter", "tangram", "grid_area", "factor_arrays", "even_numbers",
        "building_floors", "integer_movement", "zero_pairs", "integer_addition", "condensation",
        "evaporation", "earthen_pot", "pole_star", "day_night", "compass", "magnet_poles",
        "handpicking", "winnowing", "salt_evaporation", "magnetic_separation", "windmill",
        "fresh_water", "soil_formation", "vehicle_fuels", "digital_thermometer", "lab_thermometer",
        "thermometer_setup", "melting_plateau", "temperature_scales", "forest_products",
        "perimeter_shapes", "same_area_perimeters", "shared_prime_factors",
        "threefold_rotation", "building_symmetry", "paper_hole_symmetry",
        "double_line_symmetry", "reflection_only_symmetry", "earth_moon_orbit",
        "constellation_pattern", "water_cycle_condensation",
        "condensation_examples", "condensation_process",
    }
    used = {panel["diagram"] for item in manifest["images"] for panel in item["panels"] if "diagram" in panel}
    assert used <= supported
