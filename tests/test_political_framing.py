from backend.political_classifier import detect_political_framing


def test_political_framing_returns_passage_without_ideology_label():
    result = detect_political_framing("The report called the case a weaponized witch hunt by the deep state.")

    assert result["findings"]
    assert result["findings"][0]["passage"]
    assert "ideology" in result["limitation"]
