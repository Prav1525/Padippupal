from tools.validate_web_image_manifest import validate

def test_web_candidates_have_provenance_and_no_original_mapping_collision():
    web = {"images": [{
        "title": "Example",
        "lesson_id": "lesson-12345678",
        "module_key": "module-1",
        "step_ids": ["step_1"],
        "image_url": "https://upload.wikimedia.org/example.jpg",
        "source_page_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
        "license_name": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "creator": "Example creator",
        "attribution": "Example image — Example creator, CC BY 4.0.",
        "alt_text": "A sufficiently detailed alternative text description for children."
    }]}
    assert validate(web, {"images": []}) == []

def test_web_candidates_cannot_duplicate_original_mapping():
    web = {"images": [{
        "title": "Example",
        "lesson_id": "lesson-12345678",
        "module_key": "module-1",
        "step_ids": ["step_1"],
        "image_url": "https://upload.wikimedia.org/example.jpg",
        "source_page_url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
        "license_name": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "creator": "Example creator",
        "attribution": "Example image — Example creator, CC BY 4.0.",
        "alt_text": "A sufficiently detailed alternative text description for children."
    }]}
    assert any("duplicates an original PNG mapping" in e for e in validate(web, {"images": [{"lesson_id": "lesson-12345678", "module_key": "module-1"}]}))


def test_empty_web_candidate_manifest_is_valid_when_modules_use_original_diagrams():
    assert validate({"images": []}, {"images": [{"lesson_id": "lesson-12345678", "module_key": "module-1"}]}) == []
