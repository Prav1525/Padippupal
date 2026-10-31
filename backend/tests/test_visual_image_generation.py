import io
import struct

import pytest
from fastapi import HTTPException
from PIL import Image

import visual_image_generation as generator


def png_bytes(width: int = 1024, height: int = 1024) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(output, format="PNG")
    return output.getvalue()


def test_allowlist_contains_only_three_beyond_earth_assets():
    assert set(generator.ASSETS) == {
        "beyond-earth-solar-system-v1",
        "beyond-earth-day-night-v1",
        "beyond-earth-moon-phases-v1",
    }


def test_png_normalization_returns_valid_png_and_dimensions():
    data, width, height = generator._png_bytes(png_bytes(1024, 768))
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    assert (width, height) == (1024, 768)
    assert struct.unpack(">II", data[16:24]) == (1024, 768)


def test_png_rejects_too_small_dimensions():
    with pytest.raises(HTTPException) as exc:
        generator._png_bytes(png_bytes(256, 256))
    assert exc.value.status_code == 502


def test_png_rejects_non_image_bytes():
    with pytest.raises(HTTPException) as exc:
        generator._png_bytes(b"not an image")
    assert exc.value.status_code == 502


def test_generation_disabled_without_explicit_development_flag(monkeypatch):
    monkeypatch.setenv("PADIPPUPAL_VISUALS_ENV", "production")
    with pytest.raises(HTTPException) as exc:
        generator._development_config()
    assert exc.value.status_code == 503


def test_generation_rejects_production_database_url(monkeypatch):
    monkeypatch.setenv("PADIPPUPAL_VISUALS_ENV", "development")
    monkeypatch.setenv("DATABASE_URL", "postgresql://example/production_db")
    monkeypatch.setenv("AWS_ENDPOINT_URL_S3", "https://storage.example")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "dev-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "dev-secret")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "account")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "token")
    with pytest.raises(HTTPException) as exc:
        generator._development_config()
    assert exc.value.status_code == 403
