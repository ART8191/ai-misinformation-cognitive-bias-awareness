"""Claim extraction with a safe fallback when the summarization model is unavailable."""

from __future__ import annotations

import os
from typing import Any, Optional

from transformers import pipeline


SUMMARY_MODEL = "sshleifer/distilbart-cnn-12-6"
MIN_WORDS_FOR_SUMMARY = 30
MAX_SUMMARY_INPUT_WORDS = 2_800
ALLOW_MODEL_DOWNLOAD = os.getenv("ALLOW_MODEL_DOWNLOAD", "false").lower() == "true"
ENABLE_SUMMARIZATION_MODEL = os.getenv("ENABLE_SUMMARIZATION_MODEL", "false").lower() == "true"

summarizer: Optional[Any] = None
_model_load_attempted = False


def _get_summarizer() -> Optional[Any]:
    global summarizer, _model_load_attempted
    if summarizer is not None:
        return summarizer
    if _model_load_attempted:
        return None

    _model_load_attempted = True
    # A missing Hugging Face model can otherwise make a request retry for many
    # seconds. The application is useful without a summary model, so keep the
    # network/model path explicitly opt-in.
    if not ENABLE_SUMMARIZATION_MODEL:
        return None
    try:
        summarizer = pipeline(
            "summarization",
            model=SUMMARY_MODEL,
            model_kwargs={"local_files_only": not ALLOW_MODEL_DOWNLOAD},
        )
    except Exception:
        summarizer = None
    return summarizer


def extract_claims(text: str) -> str:
    """Return a concise claim, falling back to normalized source text offline."""
    normalized_text = " ".join(text.split())
    words = normalized_text.split()
    if len(words) < MIN_WORDS_FOR_SUMMARY:
        return normalized_text

    active_summarizer = _get_summarizer()
    if active_summarizer is None:
        return normalized_text

    # The model has a finite context window. This does not apply to the
    # model-free fallback above, which preserves the full submitted article.
    if len(words) > MAX_SUMMARY_INPUT_WORDS:
        normalized_text = " ".join(words[:MAX_SUMMARY_INPUT_WORDS])
        words = normalized_text.split()

    max_length = min(80, max(20, len(words) // 2))
    min_length = min(max_length - 1, max(8, len(words) // 5))
    result = active_summarizer(
        normalized_text,
        max_length=max_length,
        min_length=min_length,
        do_sample=False,
        truncation=True,
    )
    return result[0]["summary_text"]
