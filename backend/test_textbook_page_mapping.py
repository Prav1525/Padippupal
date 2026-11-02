import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from textbook_page_mapping import match_beyond_earth_pages


def test_maps_topic_to_pdf_and_printed_page_numbers_separately():
    result = match_beyond_earth_pages("Beyond Earth", "Solar System and planets")
    assert result is not None
    assert (result["pdf_page_start"], result["pdf_page_end"]) == (11, 13)
    assert (result["printed_page_start"], result["printed_page_end"]) == (241, 243)


def test_maps_moon_missions_to_original_textbook_pages():
    result = match_beyond_earth_pages("Beyond Earth", "Chandrayaan Moon missions")
    assert result is not None
    assert result["topic"] == "Natural satellites and Moon missions"
    assert (result["pdf_page_start"], result["pdf_page_end"]) == (14, 15)


def test_does_not_guess_for_other_chapters_or_ambiguous_topics():
    assert match_beyond_earth_pages("Nature's Treasures", "stars and constellations") is None
    assert match_beyond_earth_pages("Beyond Earth", "please explain this") is None
    assert match_beyond_earth_pages("Beyond Earth", "") is None
