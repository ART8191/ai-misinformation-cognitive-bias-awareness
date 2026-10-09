"""Explain observable persuasive-language patterns without claiming intent."""

from __future__ import annotations

import re


BIAS_PATTERNS = {
    "emotional language": {
        "terms": ("fear", "panic", "crisis", "threat", "danger", "alarming", "shocking", "devastating", "outrage", "disaster", "catastrophe", "collapse", "terrifying", "chaos"),
        "explanation": "This wording can make the reader feel alarmed. Strong emotion is not, by itself, evidence that a claim is wrong.",
    },
    "absolute certainty": {
        "terms": ("clearly", "obviously", "undeniable", "no doubt", "everyone knows", "proven", "without question", "definitely", "absolutely", "cannot deny", "undoubtedly"),
        "explanation": "The passage presents a conclusion as settled. Look for the underlying evidence and credible sources before accepting it.",
    },
    "appeal to authority": {
        "terms": ("experts say", "scientists say", "according to", "studies show", "research shows", "officials say", "sources say", "data indicates"),
        "explanation": "It relies on an authority or source. Check who that source is, what it actually found, and whether other credible sources agree.",
    },
    "strong causal framing": {
        "terms": ("leads to", "results in", "causes", "responsible for", "drives", "forces", "proves", "demonstrates"),
        "explanation": "The passage connects one event to another as cause and effect. A connection needs evidence that rules out coincidence and other explanations.",
    },
}


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]


def detect_bias(text: str) -> dict:
    """Return passage-level language signals, not a diagnosis of author intent."""
    findings = []
    seen = set()
    for sentence in _sentences(text):
        lowered = sentence.casefold()
        for pattern_name, pattern in BIAS_PATTERNS.items():
            trigger = next((term for term in pattern["terms"] if term in lowered), None)
            key = (sentence, pattern_name)
            if trigger and key not in seen:
                seen.add(key)
                findings.append(
                    {
                        "type": pattern_name,
                        "passage": sentence,
                        "trigger": trigger,
                        "explanation": pattern["explanation"],
                        "confidence": "language signal",
                    }
                )

    detected = sorted({finding["type"] for finding in findings})
    return {
        "detected_biases": detected,
        "bias_score": round(len(detected) / len(BIAS_PATTERNS), 2),
        "findings": findings,
        "limitation": "These are language signals, not proof that the author intended to mislead or that the article is false.",
    }
