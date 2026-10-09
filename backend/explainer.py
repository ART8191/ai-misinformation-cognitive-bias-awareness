def generate_explanation(claim, evidence, metrics, bias):
    """Create a plain-language report without asserting a truth verdict."""
    if bias["findings"]:
        opening = "The article contains language patterns worth checking before sharing."
    else:
        opening = "No configured language patterns were found; this is not a fact-check."

    return {
        "summary": opening,
        "central_claim": claim,
        "evidence_assessment": metrics["summary"],
        "how_to_read_this": "A finding highlights wording to question. Open the evidence, check the original source, and look for independent reporting.",
        "limitations": [bias["limitation"], metrics["limitation"]],
        "evidence_used": evidence,
    }
