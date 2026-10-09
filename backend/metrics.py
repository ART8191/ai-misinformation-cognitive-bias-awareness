"""Evidence-support assessment. Similarity is never a truth verdict."""

from __future__ import annotations

import re


def _terms(text: str) -> set[str]:
    return {term for term in re.findall(r"\w+", text.casefold()) if len(term) > 2}


def assess_evidence_support(claim: str, evidence_list: list[str]) -> dict:
    claim_terms = _terms(claim)
    scores = []
    for evidence in evidence_list:
        evidence_terms = _terms(evidence)
        union = claim_terms | evidence_terms
        scores.append(round(len(claim_terms & evidence_terms) / len(union), 3) if union else 0.0)

    score = max(scores, default=0.0)
    if score >= 0.12:
        summary = "The retrieved material discusses some of the same terms as the claim. It still needs source-level verification."
    elif evidence_list:
        summary = "The retrieved material has limited overlap with the claim. This is not proof that the claim is false."
    else:
        summary = "No relevant local evidence was retrieved. This is not proof that the claim is false."

    return {
        "support_score": score,
        "overlap_scores": scores,
        "summary": summary,
        "limitation": "This measures overlap with this app's local corpus, not factual truth, source quality, or consensus.",
    }


# Compatibility alias for callers that have not yet moved to the new name.
misinformation_score = assess_evidence_support
