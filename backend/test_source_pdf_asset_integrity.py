import hashlib

from app import source_pdf_asset_is_valid


def test_valid_pdf_asset_matches_source_checksum_and_page_count():
    pdf = b"%PDF-1.7\nexample"
    digest = hashlib.sha256(pdf).hexdigest()
    assert source_pdf_asset_is_valid(pdf, digest, 24, digest, 24)


def test_pdf_asset_rejects_corrupt_bytes_even_when_row_exists():
    pdf = b"%PDF-1.7\noriginal"
    corrupt = b"%PDF-1.7\ncorrupt"
    source_digest = hashlib.sha256(pdf).hexdigest()
    asset_digest = hashlib.sha256(corrupt).hexdigest()
    assert not source_pdf_asset_is_valid(corrupt, asset_digest, 24, source_digest, 24)


def test_pdf_asset_rejects_source_checksum_mismatch():
    pdf = b"%PDF-1.7\nexample"
    digest = hashlib.sha256(pdf).hexdigest()
    assert not source_pdf_asset_is_valid(pdf, digest, 24, "0" * 64, 24)


def test_pdf_asset_rejects_page_count_mismatch():
    pdf = b"%PDF-1.7\nexample"
    digest = hashlib.sha256(pdf).hexdigest()
    assert not source_pdf_asset_is_valid(pdf, digest, 23, digest, 24)


def test_pdf_asset_rejects_non_pdf_bytes():
    content = b"not a pdf"
    digest = hashlib.sha256(content).hexdigest()
    assert not source_pdf_asset_is_valid(content, digest, 24, digest, 24)
