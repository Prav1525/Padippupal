import socket
import unittest
from unittest.mock import patch

from curated_web_image_ingest import (
    sniff_image_type,
    validate_source_url,
)


class CuratedWebImageUrlTests(unittest.TestCase):
    @patch("curated_web_image_ingest.socket.getaddrinfo")
    def test_accepts_https_url_on_approved_public_nasa_host(self, resolve):
        resolve.return_value = [(None, None, None, None, ("8.8.8.8", 443))]
        url = "https://images-assets.nasa.gov/image/example.jpg"
        self.assertEqual(validate_source_url(url), url)
        resolve.assert_called_once_with("images-assets.nasa.gov", 443, type=socket.SOCK_STREAM)

    def test_rejects_non_https_and_unapproved_hosts_before_dns(self):
        for url in (
            "http://images-assets.nasa.gov/example.jpg",
            "https://example.com/example.jpg",
            "https://127.0.0.1/private",
            "https://user:pass@images-assets.nasa.gov/image.jpg",
            "https://images-assets.nasa.gov:8443/image.jpg",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_source_url(url)

    @patch("curated_web_image_ingest.socket.getaddrinfo")
    def test_rejects_private_or_loopback_dns_answers(self, resolve):
        resolve.return_value = [(None, None, None, None, ("127.0.0.1", 443))]
        with self.assertRaisesRegex(ValueError, "non-public"):
            validate_source_url("https://images-assets.nasa.gov/image/example.jpg")

    def test_sniffs_supported_image_signatures(self):
        self.assertEqual(sniff_image_type(b"\xff\xd8\xff" + b"data"), "image/jpeg")
        self.assertEqual(sniff_image_type(b"\x89PNG\r\n\x1a\n" + b"data"), "image/png")
        self.assertEqual(sniff_image_type(b"RIFFxxxxWEBP" + b"data"), "image/webp")
        self.assertIsNone(sniff_image_type(b"<html>not an image</html>"))


if __name__ == "__main__":
    unittest.main()
