"""Local retrieval over the converted article corpus.

Model loading is deliberately lazy: importing the API must not require a
network connection or download several hundred megabytes of model files.
"""

from __future__ import annotations

import os
import pickle
import re
from hashlib import sha256
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTICLES_DIR = PROJECT_ROOT / "data" / "articles"
CACHE_PATH = PROJECT_ROOT / "data" / "faiss_cache.pkl"
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 3
ALLOW_MODEL_DOWNLOAD = os.getenv("ALLOW_MODEL_DOWNLOAD", "false").lower() == "true"

model: Optional[SentenceTransformer] = None
index: Optional[faiss.Index] = None
_model_load_attempted = False


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Split text into fixed-size word chunks, omitting empty chunks."""
    words = text.split()
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]


def _load_chunks() -> list[str]:
    chunks: list[str] = []
    if not ARTICLES_DIR.exists():
        return chunks

    for path in sorted(ARTICLES_DIR.glob("*.txt")):
        _, body = _metadata_for_document(path, path.read_text(encoding="utf-8"))
        chunks.extend(chunk_text(body))
    return chunks


def _metadata_for_document(path: Path, text: str) -> tuple[dict, str]:
    """Read optional provenance headers stored with user-reviewed documents."""
    source = "Local article corpus"
    source_url = None
    body = text
    if text.startswith("SOURCE:"):
        header, separator, body = text.partition("\n\n")
        for line in header.splitlines():
            if line.startswith("SOURCE:"):
                source = line.removeprefix("SOURCE:").strip() or source
            elif line.startswith("URL:"):
                source_url = line.removeprefix("URL:").strip() or None
        if not separator:
            body = text
    return {"source": source, "url": source_url, "document": path.name}, body


chunked_docs = _load_chunks()


def _load_chunk_metadata() -> list[dict]:
    metadata: list[dict] = []
    if not ARTICLES_DIR.exists():
        return metadata
    for path in sorted(ARTICLES_DIR.glob("*.txt")):
        document = path.read_text(encoding="utf-8")
        record, body = _metadata_for_document(path, document)
        metadata.extend([record.copy() for _ in chunk_text(body)])
    return metadata


chunk_metadata = _load_chunk_metadata()


def _load_cached_index() -> Optional[faiss.Index]:
    """Use the legacy cache only when it exactly matches today's corpus."""
    if not CACHE_PATH.exists():
        return None

    try:
        with CACHE_PATH.open("rb") as cache_file:
            cached_index, cached_chunks = pickle.load(cache_file)
        if cached_chunks != chunked_docs or cached_index.ntotal != len(chunked_docs):
            return None
        return cached_index
    except (OSError, pickle.UnpicklingError, AttributeError, EOFError, TypeError):
        return None


index = _load_cached_index()


def _get_model() -> Optional[SentenceTransformer]:
    """Load the embedding model once; callers can fall back when unavailable."""
    global model, _model_load_attempted
    if model is not None:
        return model
    if _model_load_attempted:
        return None

    _model_load_attempted = True
    try:
        model = SentenceTransformer(
            MODEL_NAME, local_files_only=not ALLOW_MODEL_DOWNLOAD
        )
    except Exception:
        # Retrieval remains available through lexical matching in offline mode.
        model = None
    return model


def _build_index(embedding_model: SentenceTransformer) -> Optional[faiss.Index]:
    global index
    if not chunked_docs:
        return None

    embeddings = np.asarray(embedding_model.encode(chunked_docs), dtype="float32")
    new_index = faiss.IndexFlatL2(embeddings.shape[1])
    new_index.add(embeddings)

    try:
        with CACHE_PATH.open("wb") as cache_file:
            pickle.dump((new_index, chunked_docs), cache_file)
    except OSError:
        pass

    index = new_index
    return index


def add_document(text: str, source_name: str, source_url: Optional[str] = None) -> dict:
    """Persist a reviewed article and make it searchable during this process.

    New documents use lexical retrieval immediately. A semantic index is rebuilt
    only when an embedding model is explicitly enabled.
    """
    global index
    normalized_text = " ".join(text.split())
    if not normalized_text:
        raise ValueError("Cannot add an empty article to the knowledge base.")

    source = " ".join(source_name.split()) or "User-reviewed article"
    document_id = sha256(normalized_text.encode("utf-8")).hexdigest()[:16]
    path = ARTICLES_DIR / f"live_{document_id}.txt"
    stored_document = f"SOURCE: {source}\n"
    if source_url:
        stored_document += f"URL: {source_url}\n"
    stored_document += f"\n{normalized_text}"

    if path.exists():
        return {
            "added": False,
            "message": "This article is already in the local knowledge base.",
            "document_id": document_id,
            "total_chunks": len(chunked_docs),
        }

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(stored_document, encoding="utf-8")
    new_chunks = chunk_text(normalized_text)
    chunked_docs.extend(new_chunks)
    chunk_metadata.extend(
        [{"source": source, "url": source_url, "document": path.name} for _ in new_chunks]
    )
    # Any existing index was built before this addition and must not be used.
    index = None
    return {
        "added": True,
        "message": "Article added to the local knowledge base.",
        "document_id": document_id,
        "total_chunks": len(chunked_docs),
    }


def _keyword_indices(query: str, limit: int = TOP_K) -> list[int]:
    query_terms = set(re.findall(r"\w+", query.casefold()))
    if not query_terms:
        return []

    matches: list[tuple[int, int]] = []
    for position, document in enumerate(chunked_docs):
        score = len(query_terms.intersection(re.findall(r"\w+", document.casefold())))
        if score:
            matches.append((score, position))
    matches.sort(key=lambda item: item[0], reverse=True)
    return [position for _, position in matches[:limit]]


def _retrieve_indices(query: str, limit: int = TOP_K) -> list[int]:
    """Return matching corpus positions while preserving retrieval's offline fallback."""
    if index is None and not ALLOW_MODEL_DOWNLOAD:
        return _keyword_indices(query, limit)

    embedding_model = _get_model()
    active_index = index or (_build_index(embedding_model) if embedding_model else None)
    if embedding_model is None or active_index is None:
        return _keyword_indices(query, limit)

    query_embedding = np.asarray(embedding_model.encode([query]), dtype="float32")
    _, indices = active_index.search(query_embedding, k=min(limit, active_index.ntotal))
    return [int(position) for position in indices[0] if position >= 0]


def retrieve(query: str, limit: int = TOP_K) -> list[str]:
    """Return relevant chunks, with a deterministic offline lexical fallback."""
    query = query.strip()
    if not query or not chunked_docs:
        return []

    return [chunked_docs[position] for position in _retrieve_indices(query, limit)]


def retrieve_records(query: str, limit: int = TOP_K) -> list[dict]:
    """Retrieve excerpts with their stored source provenance for user review."""
    if not query.strip() or not chunked_docs:
        return []
    records = []
    for position in _retrieve_indices(query, limit):
        metadata = chunk_metadata[position] if position < len(chunk_metadata) else {}
        records.append({"excerpt": chunked_docs[position], **metadata})
    return records
