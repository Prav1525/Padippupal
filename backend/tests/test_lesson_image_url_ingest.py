import socket

import pytest
from fastapi import HTTPException

import lesson_image_ingest as ingest


@pytest.mark.parametrize(
    ("content_type", "payload"),
    [
        ("image/jpeg", b"\xff\xd8\xff\xe0jpeg"),
        ("image/png", b"\x89PNG\r\n\x1a\n" + b"rest"),
        ("image/webp", b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"rest"),
        ("image/gif", b"GIF89a" + b"rest"),
    ],
)
def test_image_signature_accepts_real_binary_magic_bytes(content_type, payload):
    assert ingest._image_signature_matches(payload, content_type)


@pytest.mark.parametrize(
    ("content_type", "payload", "expected"),
    [
        ("image/jpeg", b"\\xff\\xd8\\xff", False),
        ("image/png", b"\x89PNG\r\n\x1a\n", True),
        ("image/webp", b"RIFFxxxxNOPE", False),
        ("image/gif", b"GIF00a", False),
    ],
)
def test_image_signature_accepts_valid_and_rejects_invalid_magic(content_type, payload, expected):
    assert ingest._image_signature_matches(payload, content_type) is expected


def test_url_validation_returns_the_public_ip_that_must_be_pinned(monkeypatch):
    def fake_getaddrinfo(host, port, type):
        assert host == "upload.wikimedia.org"
        assert port == 443
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]

    monkeypatch.setattr(ingest.socket, "getaddrinfo", fake_getaddrinfo)
    url, host, ip = ingest._validate_public_image_url(
        "https://upload.wikimedia.org/example.png?size=large"
    )
    assert url.endswith("?size=large")
    assert host == "upload.wikimedia.org"
    assert ip == "93.184.216.34"


def test_url_validation_rejects_non_public_dns_results(monkeypatch):
    monkeypatch.setattr(
        ingest.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ],
    )
    with pytest.raises(HTTPException) as exc:
        ingest._validate_public_image_url("https://upload.wikimedia.org/example.png")
    assert exc.value.status_code == 422


def test_url_validation_rejects_unapproved_host_before_dns(monkeypatch):
    monkeypatch.setattr(
        ingest.socket,
        "getaddrinfo",
        lambda *args, **kwargs: pytest.fail("DNS must not run for an unapproved host"),
    )
    with pytest.raises(HTTPException) as exc:
        ingest._validate_public_image_url("https://example.com/image.png")
    assert exc.value.status_code == 422


def test_pinned_connection_uses_validated_ip_without_resolving_hostname(monkeypatch):
    calls = []

    class FakeContext:
        def wrap_socket(self, raw_socket, server_hostname):
            assert server_hostname == "upload.wikimedia.org"
            return "wrapped-socket"

    monkeypatch.setattr(
        ingest.socket,
        "create_connection",
        lambda address, timeout: calls.append((address, timeout)) or "raw-socket",
    )
    connection = ingest._PinnedHTTPSConnection("upload.wikimedia.org", "93.184.216.34")
    connection._context = FakeContext()
    connection.connect()
    assert calls[0][0] == ("93.184.216.34", 443)
    assert connection.sock == "wrapped-socket"


@pytest.mark.parametrize(
    ("module_key", "step_ids"),
    [
        ("module-2", ["step_2"]),
        ("module-2", ["step_2", "step_2"]),
        ("module-2", ["step_2", "step_3"]),
    ],
)
def test_module_mapping_accepts_only_one_consistent_step(module_key, step_ids):
    if len(set(step_ids)) == 1:
        ingest._validate_module_step_mapping(module_key, step_ids)
    else:
        with pytest.raises(HTTPException):
            ingest._validate_module_step_mapping(module_key, step_ids)


def test_module_mapping_rejects_step_to_wrong_module():
    with pytest.raises(HTTPException) as exc:
        ingest._validate_module_step_mapping("step_2", ["step_2"])
    assert exc.value.status_code == 422


@pytest.mark.parametrize(
    ("lesson_json", "module_key", "steps", "valid"),
    [
        ('{"teaching_sequence":[{"id":"step_1"},{"id":"step_2"}]}', "module-2", ["step_2"], True),
        ('{"teaching_sequence":[{"id":"step_1"},{"id":"step_2"}]}', "module-2", ["step_3"], False),
        ('{"teaching_sequence":[{"id":"step_1"},{"id":"step_2"}]}', "module-1", ["step_2"], False),
        ('{"teaching_sequence":[{"id":"step_12"}]}', "module-12", ["step_12"], True),
    ],
)
def test_lesson_mapping_must_match_existing_step_and_module(lesson_json, module_key, steps, valid):
    if valid:
        ingest._validate_lesson_step_mapping(lesson_json, module_key, steps)
    else:
        with pytest.raises(HTTPException) as exc:
            ingest._validate_lesson_step_mapping(lesson_json, module_key, steps)
        assert exc.value.status_code == 422


@pytest.mark.parametrize(
    ("content_type", "payload", "expected"),
    [
        ("image/png", b"\x89PNG\r\n\x1a\n" + b"png-data", "image/png"),
        ("image/jpeg", b"\xff\xd8\xff" + b"jpeg-data", "image/jpeg"),
        ("image/webp", b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"data", "image/webp"),
        ("image/svg+xml", b"<svg/>", "reject"),
        ("image/png", b"not-a-png", "reject"),
    ],
)
def test_original_raster_upload_validates_type_and_magic_bytes(content_type, payload, expected):
    if expected == "reject":
        with pytest.raises(HTTPException):
            ingest._validate_original_image(payload, content_type)
    else:
        assert ingest._validate_original_image(payload, content_type) == expected


def test_original_raster_upload_rejects_oversized_payload():
    with pytest.raises(HTTPException) as exc:
        ingest._validate_original_image(b"x" * (ingest.MAX_IMAGE_BYTES + 1), "image/png")
    assert exc.value.status_code == 413


def test_original_raster_upload_rejects_gif_for_static_teaching_art():
    with pytest.raises(HTTPException) as exc:
        ingest._validate_original_image(b"GIF89a" + b"data", "image/gif")
    assert exc.value.status_code == 415


def test_original_upload_stores_bytes_as_pending_and_never_publishes(monkeypatch):
    import asyncio
    import json
    from io import BytesIO
    from starlette.datastructures import Headers, UploadFile

    lesson_json = json.dumps({"teaching_sequence": [{"id": "step_1", "title": "A real step"}]})
    lesson = {
        "id": "lesson-12345678", "board": "CBSE", "class_level": 6,
        "subject": "Science", "chapter": "A Journey through States of Water",
        "medium": "English", "status": "approved", "lesson_json": lesson_json,
    }

    class Result:
        def __init__(self, row=None): self.row = row
        def fetchone(self): return self.row

    class FakeConnection:
        def __init__(self): self.calls = []; self.committed = False; self.rolled_back = False
        def execute(self, query, params=None):
            self.calls.append((query, params))
            if "SELECT id, board, class_level, subject, chapter, medium, status, lesson_json" in query:
                return Result(lesson)
            return Result()
        def commit(self): self.committed = True
        def rollback(self): self.rolled_back = True
        def close(self): pass

    conn = FakeConnection()
    monkeypatch.setattr(ingest, "connect", lambda: conn)
    png = b"\x89PNG\r\n\x1a\n" + b"valid-test-png-payload"
    upload = UploadFile(
        file=BytesIO(png),
        filename="water-states.png",
        headers=Headers({"content-type": "image/png"}),
    )
    result = asyncio.run(ingest.ingest_original_lesson_image(
        lesson_id=lesson["id"],
        module_key="module-1",
        step_ids_json='["step_1"]',
        alt_text="Three states of water",
        title="Water states",
        file=upload,
    ))

    assert result["status"] == "pending_review"
    assert result["student_visible"] is False
    assert result["lesson_id"] == lesson["id"]
    assert result["module_key"] == "module-1"
    assert conn.committed is True
    asset_insert = next((q, p) for q, p in conn.calls if "INSERT INTO lesson_image_assets" in q)
    blob_insert = next((q, p) for q, p in conn.calls if "INSERT INTO lesson_image_asset_blobs" in q)
    assert "'pending'" in asset_insert[0]
    assert asset_insert[1][0] == result["asset_id"]
    assert blob_insert[1][0] == result["asset_id"]
    assert blob_insert[1][1] == png
    assert blob_insert[1][2] == result["sha256"]


def test_original_upload_rejects_unapproved_lesson_before_any_insert(monkeypatch):
    import asyncio
    import json
    from io import BytesIO
    from starlette.datastructures import Headers, UploadFile

    class Result:
        def fetchone(self): return {
            "id": "lesson-12345678", "board": "CBSE", "class_level": 6,
            "subject": "Science", "chapter": "Test", "medium": "English",
            "status": "draft", "lesson_json": json.dumps({"teaching_sequence": [{"id": "step_1"}]}),
        }

    class FakeConnection:
        def __init__(self): self.queries = []; self.rolled_back = False
        def execute(self, query, params=None):
            self.queries.append(query)
            return Result()
        def commit(self): raise AssertionError("draft lessons must never be written")
        def rollback(self): self.rolled_back = True
        def close(self): pass

    conn = FakeConnection()
    monkeypatch.setattr(ingest, "connect", lambda: conn)
    upload = UploadFile(file=BytesIO(b"\x89PNG\r\n\x1a\n" + b"payload"),
                        filename="diagram.png", headers=Headers({"content-type": "image/png"}))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(ingest.ingest_original_lesson_image(
            lesson_id="lesson-12345678", module_key="module-1",
            step_ids_json='["step_1"]', alt_text="A labelled diagram", title="",
            file=upload,
        ))
    assert exc.value.status_code == 422
    assert conn.rolled_back is True
    assert not any("INSERT INTO" in query for query in conn.queries)


def test_original_upload_admin_authentication_is_required(monkeypatch):
    monkeypatch.setattr(ingest, "ADMIN_TOKEN", "test-secret")
    ingest.require_image_admin("test-secret")
    with pytest.raises(HTTPException) as exc:
        ingest.require_image_admin("wrong-secret")
    assert exc.value.status_code == 401

def test_lesson_image_manifest_keeps_paired_assets_in_stable_order(monkeypatch):
    rows = [
        {
            "id": "original-first",
            "module_key": "module-4",
            "title": "Sun energy",
            "step_ids_json": '["step_4"]',
            "content_type": "image/png",
            "alt_text": "Sunlight reaches Earth",
            "sha256": "a" * 64,
            "byte_length": 123,
        },
        {
            "id": "original-second",
            "module_key": "module-4",
            "title": "Forest products",
            "step_ids_json": '["step_4"]',
            "content_type": "image/png",
            "alt_text": "Useful forest products",
            "sha256": "b" * 64,
            "byte_length": 456,
        },
    ]

    class Result:
        def fetchall(self):
            return rows

    class FakeConnection:
        def __init__(self):
            self.query = ""

        def execute(self, query, params=None):
            self.query = query
            assert params == ("lesson-12345678",)
            return Result()

        def close(self):
            pass

    connection = FakeConnection()
    monkeypatch.setattr(ingest, "connect", lambda: connection)

    result = ingest.list_lesson_images("lesson-12345678")

    assert [image["id"] for image in result["images"]] == [
        "original-first",
        "original-second",
    ]
    assert result["asset_version_policy"] == "latest_per_module"
    assert "WITH latest_module_assets AS" in connection.query
    assert "MAX(updated_at) AS latest_updated_at" in connection.query
    assert "latest.latest_updated_at=a.updated_at" in connection.query
    assert "ORDER BY a.module_key, a.created_at, a.id" in connection.query
    assert all(image["step_ids"] == ["step_4"] for image in result["images"])


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Mathematics", "Mathematics"),
        ("Beyond Earth", "Beyond-Earth"),
        ("A Journey through States of Water", "A-Journey-through-States-of-Water"),
        ("English / Tamil", "English-Tamil"),
    ],
)
def test_storage_key_segments_are_safe_and_subject_agnostic(raw, expected):
    assert ingest._safe_object_segment(raw) == expected


def test_storage_key_segment_rejects_empty_or_path_only_metadata():
    with pytest.raises(HTTPException):
        ingest._safe_object_segment("...")
    with pytest.raises(HTTPException):
        ingest._safe_object_segment("")
