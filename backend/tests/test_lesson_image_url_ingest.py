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
    ("content_type", "payload"),
    [
        ("image/jpeg", b"\\xff\\xd8\\xff"),
        ("image/png", b"\\x89PNG\\r\\n\\x1a\\n"),
        ("image/webp", b"RIFFxxxxNOPE"),
        ("image/gif", b"GIF00a"),
    ],
)
def test_image_signature_rejects_literal_escape_text_and_wrong_magic(content_type, payload):
    assert not ingest._image_signature_matches(payload, content_type)


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
