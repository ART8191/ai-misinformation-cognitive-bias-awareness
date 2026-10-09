import backend.claim_extractor as claim_extractor


def test_extract_claims_returns_short_input_without_loading_model(monkeypatch):
    monkeypatch.setattr(claim_extractor, "summarizer", None)
    monkeypatch.setattr(claim_extractor, "_model_load_attempted", False)

    assert claim_extractor.extract_claims("  A   short claim. ") == "A short claim."
    assert claim_extractor._model_load_attempted is False


def test_extract_claims_uses_configured_summarizer(monkeypatch):
    def fake_summarizer(text, **kwargs):
        assert kwargs["min_length"] < kwargs["max_length"]
        return [{"summary_text": "Extracted claim"}]

    monkeypatch.setattr(claim_extractor, "summarizer", fake_summarizer)
    text = " ".join(["word"] * claim_extractor.MIN_WORDS_FOR_SUMMARY)

    assert claim_extractor.extract_claims(text) == "Extracted claim"
