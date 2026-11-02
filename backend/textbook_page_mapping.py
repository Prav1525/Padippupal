"""Explicit mapping from Beyond Earth lesson topics to original PDF page numbers.

PDF page numbers are 1-based positions in fecu112.pdf, not the printed page
numbers shown in the textbook footer. Keep the mapping conservative: include
only pages whose extracted text confirms the named topic.
"""
from __future__ import annotations

import re
from typing import Any

BEYOND_EARTH_SOURCE_TITLE = "NCERT Curiosity Class 6 Science — Chapter PDF (fecu112.pdf)"
BEYOND_EARTH_PDF_SHA256 = "514963bedfef5679733b4d2b6b7274629ebc9031dcded7777bf0324bf7404928"

# (canonical topic labels, inclusive PDF page range, inclusive printed page range)
BEYOND_EARTH_PAGE_MAP: tuple[dict[str, Any], ...] = (
    {"topic": "Stars and constellations", "keywords": ("star", "constellation", "pole star", "big dipper", "little dipper"), "pdf_pages": (3, 5), "printed_pages": (233, 235)},
    {"topic": "Night sky watching", "keywords": ("night sky", "night-sky watching", "orion", "dark open area", "light pollution"), "pdf_pages": (6, 8), "printed_pages": (236, 238)},
    {"topic": "Sun and Earth's motion", "keywords": ("rising sun", "revolving around the sun", "rotation", "revolution of the earth"), "pdf_pages": (9, 10), "printed_pages": (239, 240)},
    {"topic": "Solar System and planets", "keywords": ("solar system", "planets", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"), "pdf_pages": (11, 13), "printed_pages": (241, 243)},
    {"topic": "Natural satellites and Moon missions", "keywords": ("natural satellites", "chandrayaan", "moon mission", "lunar"), "pdf_pages": (14, 15), "printed_pages": (244, 245)},
    {"topic": "Comets", "keywords": ("comet", "tail of the comet"), "pdf_pages": (16, 16), "printed_pages": (246, 246)},
    {"topic": "Milky Way galaxy", "keywords": ("milky way", "galaxy"), "pdf_pages": (17, 17), "printed_pages": (247, 247)},
    {"topic": "Chapter summary", "keywords": ("summary", "keywords", "eight planets"), "pdf_pages": (18, 19), "printed_pages": (248, 249)},
)


def match_beyond_earth_pages(chapter: str | None, topic: str | None, message: str | None = None) -> dict[str, Any] | None:
    """Return a conservative mapping for Beyond Earth only; never guess for other chapters."""
    chapter_text = re.sub(r"\s+", " ", chapter or "").strip().casefold()
    if chapter_text != "beyond earth":
        return None
    query = " ".join((topic or "", message or "")).casefold()
    if not query.strip():
        return None

    # A named topic should win over broad terms; map the most specific matching entry.
    ordered = sorted(BEYOND_EARTH_PAGE_MAP, key=lambda item: max(map(len, item["keywords"])), reverse=True)
    for item in ordered:
        if any(keyword in query for keyword in item["keywords"]):
            return {
                "source_title": BEYOND_EARTH_SOURCE_TITLE,
                "source_sha256": BEYOND_EARTH_PDF_SHA256,
                "topic": item["topic"],
                "pdf_page_start": item["pdf_pages"][0],
                "pdf_page_end": item["pdf_pages"][1],
                "printed_page_start": item["printed_pages"][0],
                "printed_page_end": item["printed_pages"][1],
            }
    return None
