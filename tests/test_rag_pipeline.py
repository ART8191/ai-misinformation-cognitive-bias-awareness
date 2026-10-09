import backend.rag_pipeline as rag_pipeline


def test_retrieve_falls_back_to_keyword_search_without_embeddings(monkeypatch):
    monkeypatch.setattr(rag_pipeline, "model", None)
    monkeypatch.setattr(rag_pipeline, "index", None)
    monkeypatch.setattr(rag_pipeline, "chunked_docs", ["Alpha beta", "Gamma delta"])

    results = rag_pipeline.retrieve("alpha")

    assert results == ["Alpha beta"]


def test_add_document_persists_reviewed_article_and_updates_keyword_corpus(monkeypatch, tmp_path):
    monkeypatch.setattr(rag_pipeline, "ARTICLES_DIR", tmp_path / "articles")
    monkeypatch.setattr(rag_pipeline, "chunked_docs", [])
    monkeypatch.setattr(rag_pipeline, "chunk_metadata", [])
    monkeypatch.setattr(rag_pipeline, "index", None)

    result = rag_pipeline.add_document(
        "A reviewed article discusses an energy policy.",
        "Example News",
        "https://example.com/article",
    )

    assert result["added"] is True
    assert list((tmp_path / "articles").glob("live_*.txt"))
    assert rag_pipeline.retrieve("energy policy")
    record = rag_pipeline.retrieve_records("energy policy")[0]
    assert record["source"] == "Example News"
    assert record["url"] == "https://example.com/article"

    duplicate = rag_pipeline.add_document(
        "A reviewed article discusses an energy policy.",
        "Example News",
    )
    assert duplicate["added"] is False
