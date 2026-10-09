"""Conservative, explainable claim-to-corpus comparison utilities.

These heuristics report what the local corpus appears to say. They are not a
fact checker and intentionally return insufficient evidence when overlap is weak.
"""

from __future__ import annotations

import re
from collections import defaultdict


STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "have", "has", "was", "were",
    "are", "but", "not", "about", "into", "their", "they", "will", "would", "could",
    "should", "than", "then", "been", "also", "when", "where", "which", "who", "what",
}
GENERIC_TOPIC_TERMS = {
    "agreement", "agreements", "government", "governments", "policy", "policies", "official",
    "officials", "report", "reports", "security", "regional", "country", "countries", "public",
    "international", "national", "situation", "issue", "issues", "development", "developments",
    "said", "says", "news", "article", "people", "state", "states", "new", "latest",
}
NEGATIONS = {"not", "no", "never", "false", "denied", "deny", "reject", "rejected", "untrue"}


def _terms(text: str) -> set[str]:
    return {
        word for word in re.findall(r"\w+", text.casefold())
        if len(word) > 2 and word not in STOPWORDS and word not in GENERIC_TOPIC_TERMS
    }


def extract_claim_candidates(text: str, limit: int = 5) -> list[dict]:
    """Produce readable, sentence-level claims without requiring a hosted model."""
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if len(item.split()) >= 4]
    if not sentences:
        sentences = [" ".join(text.split())]
    claims = []
    for sentence in sentences[:limit]:
        lowered = sentence.casefold()
        if sentence.endswith("?"):
            kind = "question"
        elif any(marker in lowered for marker in ("i think", "we believe", "in my opinion", "should ", "must ")):
            kind = "opinion"
        elif any(marker in lowered for marker in (" will ", " may ", " might ", " likely ", " could ")):
            kind = "prediction"
        else:
            kind = "factual claim"
        claims.append({"claim": sentence, "type": kind})
    return claims


def _negates_shared_subject(text: str, shared_terms: set[str]) -> bool:
    """Only treat negation as meaningful when it is close to the shared claim topic."""
    words = re.findall(r"\w+", text.casefold())
    for position, word in enumerate(words):
        if word in NEGATIONS and shared_terms.intersection(words[position + 1 : position + 5]):
            return True
    return False


def relevance_score(claim: str, excerpt: str) -> tuple[float, set[str]]:
    """Score whether a passage is evidence for this claim, not merely its topic."""
    claim_terms = _terms(claim)
    shared_terms = claim_terms & _terms(excerpt)
    if not claim_terms:
        return 0.0, shared_terms
    return len(shared_terms) / len(claim_terms), shared_terms


def is_relevant_evidence(claim: str, excerpt: str) -> tuple[bool, float, set[str]]:
    """Require several distinctive shared terms before exposing a passage as evidence."""
    score, shared_terms = relevance_score(claim, excerpt)
    # A high claim-coverage score helps concise claims; the absolute threshold
    # prevents broad, generic topic overlap from being presented as evidence.
    relevant = len(shared_terms) >= 3 and (score >= 0.30 or len(shared_terms) >= 5)
    return relevant, score, shared_terms


def compare_claim(claim: str, evidence: list[dict]) -> dict:
    claim_terms = _terms(claim)
    relevant = []
    for record in evidence:
        is_relevant, score, overlap = is_relevant_evidence(claim, record["excerpt"])
        if is_relevant:
            contradictory = _negates_shared_subject(claim, overlap) != _negates_shared_subject(record["excerpt"], overlap)
            relationship = "contradicts" if contradictory else "aligns"
            relevant.append({
                **record,
                "relationship": relationship,
                "shared_terms": sorted(overlap)[:8],
                "relevance_score": round(score, 2),
            })

    if not relevant:
        status = "insufficient evidence"
        summary = "No sufficiently relevant passage was found in the local dataset. This does not mean the claim is false."
    else:
        relationships = {record["relationship"] for record in relevant}
        if len(relationships) > 1:
            status = "mixed evidence"
            summary = "Relevant local passages point in different directions; review the cited sources."
        elif "contradicts" in relationships:
            status = "contradicted by available evidence"
            summary = "Relevant local passages use incompatible wording. Review the cited excerpts and original sources."
        else:
            status = "aligned with available evidence"
            summary = "Relevant local passages use compatible wording. This is corpus agreement, not a truth verdict."
    return {"claim": claim, "status": status, "summary": summary, "evidence": relevant}


def compare_claims(claims: list[dict], evidence_for_claim):
    results = []
    for item in claims:
        results.append({"type": item["type"], **compare_claim(item["claim"], evidence_for_claim(item["claim"]))})
    return results


def compare_source_coverage(evidence: list[dict]) -> list[dict]:
    """Summarize source-level emphasis without assigning political labels."""
    groups = defaultdict(list)
    for record in evidence:
        groups[record.get("source") or "Local article corpus"].append(record)
    all_terms = _terms(" ".join(record["excerpt"] for record in evidence))
    comparison = []
    for source, records in groups.items():
        source_terms = _terms(" ".join(record["excerpt"] for record in records))
        other_terms = _terms(" ".join(r["excerpt"] for s, rs in groups.items() if s != source for r in rs))
        emphasis = sorted(source_terms - other_terms - STOPWORDS, key=str.casefold)[:6]
        comparison.append({
            "source": source,
            "url": records[0].get("url"),
            "excerpts": [record["excerpt"] for record in records],
            "distinct_emphasis": emphasis,
            "shared_topic_terms": sorted(source_terms & all_terms)[:6],
        })
    return comparison
