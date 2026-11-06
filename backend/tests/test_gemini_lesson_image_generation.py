import struct

import pytest
from fastapi import HTTPException

import gemini_lesson_image_generation as generator


def png_header(width=1024, height=1365):
    return (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\x0dIHDR"
        + struct.pack(">II", width, height)
        + b"\x08\x02\x00\x00\x00"
    )


def test_png_dimensions_accepts_valid_portrait_header():
    assert generator._png_dimensions(png_header()) == (1024, 1365)


@pytest.mark.parametrize("payload", [b"not png", png_header(200, 200), png_header(5000, 1000)])
def test_png_dimensions_rejects_invalid_or_oversized_dimensions(payload):
    with pytest.raises(HTTPException):
        generator._png_dimensions(payload)


def test_step_prompt_uses_only_lesson_grounded_content_and_padippupal_style():
    lesson = {
        "board": "CBSE",
        "class_level": 6,
        "medium": "English",
        "chapter": "Beyond Earth",
        "topic": "Day and night",
    }
    step = {
        "id": "step_1",
        "title": "Why do we have day and night?",
        "caption": "Earth rotates on its axis.",
        "visual": {"labels": ["Sun", "Earth"], "arrow": "rotation"},
    }
    prompt = generator._step_prompt(lesson, step)
    assert "Excalidraw-inspired" in prompt
    assert "hand-drawn pencil" in prompt
    assert "Earth rotates on its axis" in prompt
    assert "Only include short labels directly supported" in prompt
    assert "Day and night" in prompt


def test_tamil_medium_requests_tamil_labels():
    prompt = generator._step_prompt(
        {"medium": "Tamil", "chapter": "விண்வெளிக்கு அப்பால்", "topic": "பகலும் இரவும்"},
        {"id": "step_1", "title": "பூமியின் சுழற்சி", "caption": "பூமி தன் அச்சில் சுழல்கிறது."},
    )
    assert "short, correctly spelled Tamil labels" in prompt


def test_missing_gemini_key_fails_closed(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        generator._generate_with_gemini("test")
    assert exc.value.status_code == 503
