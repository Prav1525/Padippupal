#!/usr/bin/env python3
"""Regression guard for the Beyond Earth inline textbook-image renderer.

This is deliberately separate from the generic Mathematics emulator smoke test:
it verifies the production Android renderer contract and complements the JVM
mapping tests. It does not claim to prove live production image delivery.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SCREEN = ROOT / "app/src/main/java/com/padippupal/app/TutorScreen.kt"
MAPPING = ROOT / "app/src/main/java/com/padippupal/app/BeyondEarthImageMapping.kt"
TEST = ROOT / "app/src/test/java/com/padippupal/app/BeyondEarthImageMappingTest.kt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("FAIL: " + message)
    print("PASS: " + message)


def main() -> None:
    screen = SCREEN.read_text(encoding="utf-8")
    mapping = MAPPING.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")

    start = screen.find("private fun BeyondEarthTextbookPageImage(")
    end = screen.find("\n@Composable\nprivate fun DatabaseInteractiveLessonLab(", start)
    require(start >= 0 and end > start, "Beyond Earth inline image composable exists")
    renderer = screen[start:end]

    require('chapter.contains("beyond earth"' in renderer.lower(),
            "image renderer is restricted to the Beyond Earth chapter")
    require('"$base/chapter-lessons/$encodedLessonId/images"' in renderer,
            "renderer fetches the lesson-specific image manifest")
    for field in ('"id"', '"url"', '"title"', '"alt_text"', '"module_key"', '"step_ids"'):
        require(field in renderer, f"manifest parser reads {field}")
    require("matchingBeyondEarthImageAssets(candidates, stepId, moduleKey)" in renderer,
            "manifest entries are matched against the active step and module")
    require("matchedAssets.mapNotNull { asset ->" in renderer,
            "renderer iterates the complete matched image collection")
    require("BitmapFactory.decodeStream(it)" in renderer,
            "each image response is decoded as a bitmap")
    require("loadedImages.forEachIndexed" in renderer,
            "every successfully decoded image is rendered inline")
    require("loadedImages.size} original textbook image" in renderer,
            "UI exposes the number of rendered original images")
    require("firstOrNull" not in renderer,
            "single-first-match regression is absent")
    require("startsWith(\"/chapter-lessons/\")" in renderer,
            "image URLs are constrained to the chapter-lessons image endpoint")

    require("distinctBy { it.id.ifBlank { it.url } }" in mapping,
            "mapping helper deduplicates assets by ID with URL fallback")
    for test_name in (
        "returnsEveryImageMappedToTheSameModule",
        "includesStepMappedImagesAndModuleImagesWithoutDuplicates",
        "returnsNoImagesForAnUnmappedModuleOrStep",
        "deduplicatesRepeatedAssetIds",
    ):
        require(test_name in tests, f"JVM mapping regression test exists: {test_name}")

    print("PASS: Beyond Earth renderer contract checks completed")
    print("NOTE: This source/JVM contract gate is not a live production-image emulator screenshot.")


if __name__ == "__main__":
    main()
