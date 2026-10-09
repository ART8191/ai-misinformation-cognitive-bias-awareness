# AI-Based Misinformation Exposure and Cognitive Bias Awareness

An explainable news-literacy prototype for examining a news article before it is shared. It supports critical reading by exposing claim candidates, local-corpus retrieval results, wording signals, provenance, and limitations. It is not an automated fact-checking authority.

## What the prototype does

- Accepts pasted text, public article URLs, and PDF, DOCX, or TXT files.
- Applies size, URL-safety, and boilerplate-removal safeguards before analysis.
- Extracts a central claim and up to five sentence-level claim candidates.
- Highlights configured emotional, certainty, authority, causal, and political-framing signals.
- Retrieves related passages from a local article corpus using lexical retrieval by default; optional FAISS and sentence-embedding retrieval can be enabled locally.
- Reports an evidence relationship as aligned, contradicted, mixed, or insufficient evidence.
- Preserves available source provenance and cross-source coverage.
- Allows a reader to explicitly add a reviewed URL article to the local corpus. Articles are never added automatically.

These outputs describe the relationship between a claim and material available in the local corpus. They do **not** establish factual truth, rate source quality, assign political ideology, or infer an author's intent.

## Repository layout

```text
backend/       FastAPI service and analysis modules
frontend/      Streamlit interface
tests/         Automated functional tests
data/          Local corpus location and optional FAISS cache (not for public raw data)
tools/         Research-paper asset generation utilities
```

## Requirements

- Python 3.9 or later
- pip

## Local installation

```bash
git clone <YOUR-REPOSITORY-URL>
cd ai-misinfo-system
python3 -m venv .venv
source .venv/bin/activate           # macOS/Linux
# .venv\Scripts\Activate.ps1         # Windows PowerShell
pip install --upgrade pip
pip install -r requirements.txt
```

## Run the application

Start the API in one terminal:

```bash
uvicorn backend.main:app --reload
```

Start the interface in a second terminal:

```bash
streamlit run frontend/app.py
```

The frontend uses `http://127.0.0.1:8000` by default. To use a different API endpoint, set `API_URL` before starting Streamlit.

```bash
API_URL=http://127.0.0.1:8000 streamlit run frontend/app.py
```

By default, the system uses deterministic lexical retrieval and does not download a transformer model. To permit a local embedding-model download and FAISS-based semantic retrieval, set the following before starting the API:

```bash
ALLOW_MODEL_DOWNLOAD=true uvicorn backend.main:app --reload
```

## Tests

Run the automated functional suite from the repository root:

```bash
pytest -q
```

The tests cover supported document ingestion, URL safety, claim extraction, lexical retrieval fallback, provenance retention, claim-comparison safeguards, and language/framing output. Passing tests validate expected software behavior; they are not a benchmark measurement of misinformation-detection accuracy.

## Data and privacy

Do not commit API keys, private URLs, user uploads, raw scraped articles, `data/articles/`, or `data/faiss_cache.pkl`. The repository should contain only code, documentation, tests, and lawfully shareable metadata or reproduction scripts. If a corpus is used, document its licence, provenance, and the method used to obtain it before public release.

## Limitations

The local corpus is incomplete and text-only. Retrieval overlap is not fact verification, and language patterns are prompts for further inspection rather than proof that an article is false or misleading. Predictive claims require a separately annotated evaluation with precision, recall, F1, and ideally a reader study.

## Citation

If you use this prototype in academic work, cite the accompanying manuscript:

> Taware, A.R., Mohite, V.D., Sarvade, A.A., Sus, P.J., Mohite, A.A. *AI-Based Misinformation Exposure and Cognitive Bias Awareness in News Articles*. Manuscript under preparation.
