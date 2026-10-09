from backend.bias_detector import detect_bias
from backend.document_ingestion import extract_file
from backend.metrics import assess_evidence_support


def test_bias_detector_returns_the_triggering_passage():
    result = detect_bias("Experts say this crisis will clearly cause chaos.")

    assert result["findings"]
    assert all(finding["passage"] for finding in result["findings"])
    assert all(finding["explanation"] for finding in result["findings"])


def test_evidence_assessment_does_not_return_a_truth_verdict():
    result = assess_evidence_support("A city changed a policy", ["The city changed its policy yesterday."])

    assert result["support_score"] > 0
    assert "truth" in result["limitation"]


def test_extract_txt_file():
    text, metadata = extract_file(b"A short news article.", "article.txt")

    assert text == "A short news article."
    assert metadata == {"kind": "file", "name": "article.txt"}
