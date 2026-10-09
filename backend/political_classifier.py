"""Identify political framing signals without assigning an ideology label."""

from __future__ import annotations

import re


FRAMING_PATTERNS = {
    "loaded political label": {
        "terms": (
            "radical left", "radical right", "far-left", "far-right", "far right",
            "far left", "liberal elite", "woke", "anti-national", "traitor",
        ),
        "explanation": "This label can turn a political position or group into a simplified identity. Check the underlying policy or action being discussed.",
    },
    "institutional distrust framing": {
        "terms": (
            "weaponized", "rigged", "deep state", "sham", "kangaroo court",
            "political persecution", "witch hunt", "corrupt establishment",
        ),
        "explanation": "This wording casts an institution or process as illegitimate. Look for verifiable details about the decision, process, and evidence.",
    },
    "political threat framing": {
        "terms": (
            "enemy of the people", "destroy our country", "attack on democracy",
            "war on", "existential threat", "take back our country",
        ),
        "explanation": "This frames political disagreement as an urgent threat. Consider whether the passage presents evidence and acknowledges other interpretations.",
    },
}


def detect_political_framing(text: str) -> dict:
    """Return observable framing signals; never infer the author's ideology."""
    findings = []
    seen = set()
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    for sentence in sentences:
        lowered = sentence.casefold()
        for framing_type, pattern in FRAMING_PATTERNS.items():
            trigger = next((term for term in pattern["terms"] if term in lowered), None)
            key = (sentence, framing_type)
            if trigger and key not in seen:
                seen.add(key)
                findings.append(
                    {
                        "type": framing_type,
                        "passage": sentence,
                        "trigger": trigger,
                        "explanation": pattern["explanation"],
                        "confidence": "language signal",
                    }
                )
    return {
        "findings": findings,
        "limitation": "These are wording signals, not a judgment about the author's political ideology or the truth of the article.",
    }
