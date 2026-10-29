from textbook_visual_refs import describe_pdf_visual_references


def test_no_gemini_key_skips_visual_analysis_without_failing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert describe_pdf_visual_references(b"%PDF-test") == {}
