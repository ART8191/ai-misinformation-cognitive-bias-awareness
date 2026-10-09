from backend.evidence_comparison import compare_claim, extract_claim_candidates


def test_claim_candidates_classify_question_and_factual_statement():
    claims = extract_claim_candidates("The council approved the measure yesterday. Will it take effect soon?")

    assert claims[0]["type"] == "factual claim"
    assert claims[1]["type"] == "question"


def test_compare_claim_returns_aligned_evidence_with_provenance():
    result = compare_claim(
        "The council approved the measure yesterday.",
        [{"source": "Example News", "url": "https://example.com", "excerpt": "The council approved the measure yesterday after a public vote."}],
    )

    assert result["status"] == "aligned with available evidence"
    assert result["evidence"][0]["source"] == "Example News"


def test_compare_claim_is_explicit_when_corpus_has_no_relevant_evidence():
    result = compare_claim("A new satellite launched from India.", [{"excerpt": "The city opened a new public library."}])

    assert result["status"] == "insufficient evidence"


def test_compare_claim_detects_a_direct_negated_statement():
    result = compare_claim(
        "The council approved the measure yesterday.",
        [{"excerpt": "The council did not approve the measure yesterday."}],
    )

    assert result["status"] == "contradicted by available evidence"


def test_compare_claim_rejects_generic_topic_overlap_as_evidence():
    result = compare_claim(
        "The regional government announced a new security policy.",
        [{"excerpt": "The government released a new report about regional security issues."}],
    )

    assert result["status"] == "insufficient evidence"
