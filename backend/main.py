from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field, field_validator

from backend.bias_detector import detect_bias
from backend.claim_extractor import extract_claims
from backend.document_ingestion import extract_file, extract_url
from backend.evidence_comparison import compare_claims, compare_source_coverage, extract_claim_candidates
from backend.explainer import generate_explanation
from backend.metrics import assess_evidence_support
from backend.political_classifier import detect_political_framing
from backend.rag_pipeline import add_document, retrieve_records


MAX_INPUT_CHARACTERS = 50_000
MAX_INPUT_WORDS = 9_000
app = FastAPI(title="News Literacy Analyzer", version="0.1.0")


class InputText(BaseModel):
    text: str = Field(max_length=MAX_INPUT_CHARACTERS)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        normalized_value = " ".join(value.split())
        if not normalized_value:
            raise ValueError("text must not be empty or whitespace only")
        if len(normalized_value.split()) > MAX_INPUT_WORDS:
            raise ValueError(f"text must contain at most {MAX_INPUT_WORDS} words")
        return normalized_value


class InputUrl(BaseModel):
    url: str


class KnowledgeBaseDocument(InputText):
    source_name: str = Field(default="User-reviewed article", max_length=300)
    source_url: Optional[str] = Field(default=None, max_length=2_000)


@app.post("/extract-url")
def extract_article_url(input: InputUrl):
    """Fetch article text for user review before analysis."""
    try:
        text, source = extract_url(input.url)
        return {"text": text, "source": source}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/knowledge-base/add")
def add_to_knowledge_base(input: KnowledgeBaseDocument):
    try:
        return add_document(input.text, input.source_name, input.source_url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def analyze_article(text: str, source: dict) -> dict:
    validated = InputText(text=text).text
    claim = extract_claims(validated)
    bias = detect_bias(validated)
    political_framing = detect_political_framing(validated)
    claims = extract_claim_candidates(validated)
    claim_comparisons = compare_claims(claims, lambda item: retrieve_records(item))
    # Only claim-relevant passages are report evidence. This prevents the top
    # keyword matches for a broad topic from looking like actual support.
    seen_evidence = set()
    evidence = []
    for comparison in claim_comparisons:
        for record in comparison["evidence"]:
            identity = (record.get("document"), record["excerpt"])
            if identity not in seen_evidence:
                seen_evidence.add(identity)
                evidence.append(record)
    evidence_assessment = assess_evidence_support(claim, [record["excerpt"] for record in evidence])
    explanation = generate_explanation(claim, [record["excerpt"] for record in evidence], evidence_assessment, bias)
    coverage_evidence = evidence
    return {
        "source": source,
        "article": validated,
        "findings": bias["findings"],
        "political_framing": political_framing,
        "evidence": evidence,
        "evidence_assessment": evidence_assessment,
        "claim_comparisons": claim_comparisons,
        "source_coverage": compare_source_coverage(coverage_evidence),
        "comparison_limitation": "Alignment and contradiction are conservative text comparisons against the local dataset, not factual verdicts or source-quality ratings.",
        "explanation": explanation,
    }


@app.post("/analyze")
def analyze(input: InputText):
    return analyze_article(input.text, {"kind": "text", "name": "Pasted text"})


@app.post("/analyze-url")
def analyze_url(input: InputUrl):
    try:
        text, source = extract_url(input.url)
        return analyze_article(text, source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/analyze-file")
async def analyze_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text, source = extract_file(content, file.filename or "upload")
        return analyze_article(text, source)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
