"""Streamlit interface for AI-based news misinformation and bias analysis."""



from __future__ import annotations



import os

from html import escape



import httpx

import streamlit as st





API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

PROJECT_TITLE = "AI-Based Misinformation & Cognitive Bias Detection in News Articles"



# ---------------- VISUALIZATION LAYER ----------------

def render_evidence_visualization(comparisons):
    """Visualize the existing claim/evidence relationships only."""

    if not comparisons:
        return

    buckets = {
        "Aligns": {"icon": "🟢", "count": 0, "sources": []},
        "Contradicts": {"icon": "🔴", "count": 0, "sources": []},
        "Mixed Evidence": {"icon": "🟠", "count": 0, "sources": []},
        "Insufficient Evidence": {"icon": "⚪", "count": 0, "sources": []},
    }

    def bucket_for(value):
        value = str(value or "").strip().lower()

        if value in {
            "aligned with available evidence",
            "aligned",
            "aligns",
            "supported",
            "support",
        }:
            return "Aligns"

        if value in {
            "contradicted by available evidence",
            "contradicted",
            "contradicts",
            "contradiction",
        }:
            return "Contradicts"

        if value in {"mixed evidence", "mixed"}:
            return "Mixed Evidence"

        if value in {"insufficient evidence", "insufficient"}:
            return "Insufficient Evidence"

        return None

    for comparison in comparisons:
        status_bucket = bucket_for(comparison.get("status"))
        evidence_items = comparison.get("evidence") or []

        # Count each claim once by its existing overall status.
        if status_bucket:
            buckets[status_bucket]["count"] += 1

        # Attribute individual sources using the relationship already returned by the backend.
        for item in evidence_items:
            source = item.get("source") or "Local article corpus"
            relationship_bucket = bucket_for(item.get("relationship"))

            if relationship_bucket:
                buckets[relationship_bucket]["sources"].append(str(source))

    st.markdown(
        "<div class='section-title'>Coverage &amp; Evidence Landscape</div>",
        unsafe_allow_html=True,
    )

    st.caption(
        "A visual summary of the relationships already produced by the analysis engine. "
        "No new classification is performed here."
    )

    # Summary metrics — uses the same existing bucket counts.
    cols = st.columns(4)

    for col, label in zip(cols, buckets):
        with col:
            data = buckets[label]

            st.metric(
                label=f"{data['icon']} {label}",
                value=data["count"],
                help=f"Claims classified as {label.lower()} by the existing analysis.",
            )

    # Preserve the same relationship distribution while making the chart
    # easier to read with an explicit category and value field.
    chart_data = {
        "Relationship": list(buckets.keys()),
        "Claims": [data["count"] for data in buckets.values()],
    }

    if any(chart_data["Claims"]):
        st.markdown("#### Evidence relationship distribution")

        st.bar_chart(
            chart_data,
            x="Relationship",
            y="Claims",
            height=300,
            use_container_width=True,
        )

    else:
        st.info(
            "No classified claim relationships are available to visualize yet."
        )

    st.markdown("#### Source / agency alignment")

    rows = []

    for label, data in buckets.items():
        unique_sources = list(dict.fromkeys(data["sources"]))

        rows.append(
            {
                "Relationship": f"{data['icon']} {label}",
                "Sources / agencies": len(unique_sources),
                "Sources": (
                    ", ".join(unique_sources)
                    if unique_sources
                    else "—"
                ),
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("View agencies/sources by relationship"):
        for label, data in buckets.items():
            unique_sources = list(dict.fromkeys(data["sources"]))

            st.markdown(
                f"**{data['icon']} {label}**"
            )

            if unique_sources:
                for source in unique_sources:
                    st.write(f"• {source}")
            else:
                st.caption(
                    "No source-level relationship was returned for this category."
                )


# ---------------- END VISUALIZATION LAYER ----------------







st.set_page_config(
    page_title=PROJECT_TITLE,
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)





def apply_styles() -> None:

    st.markdown(

        """

        <style>

        :root { --ink: #12233f; --muted: #61728d; --navy: #102a43; --blue: #1769e0; --sky: #eaf3ff; --line: #dbe5f1; --paper: #ffffff; }

        .stApp { background: #f5f8fc; color: var(--ink); }

        [data-testid="stHeader"] { background: rgba(245, 248, 252, .88); }

        [data-testid="stMainBlockContainer"] { max-width: 1160px; padding: 2.25rem 2rem 4.5rem; margin: 0 auto; }

        .hero { background: radial-gradient(circle at 90% 15%, #2d7be6 0, #1557ad 26%, #102a43 69%); border-radius: 24px; color: white; padding: 3.2rem 3.5rem; box-shadow: 0 18px 48px rgba(16, 42, 67, .18); margin-bottom: 1.25rem; }

        .eyebrow { color: #a9d3ff; font-size: .78rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; margin-bottom: .8rem; }

        .hero h1 { color: white !important; font-size: clamp(2rem, 4vw, 3.25rem) !important; line-height: 1.08; letter-spacing: -.04em; max-width: 820px; margin: 0 0 1rem; }

        .hero p { color: #dcecff; font-size: 1.05rem; line-height: 1.65; max-width: 690px; margin: 0; }

        .section-title { font-size: 1.35rem; font-weight: 750; color: var(--ink); margin: 2.2rem 0 .35rem; }

        .section-copy { color: var(--muted); margin: 0 0 1rem; }

        .feature-card { background: var(--paper); border: 1px solid var(--line); border-radius: 16px; padding: 1.15rem 1.2rem; min-height: 128px; box-shadow: 0 5px 16px rgba(16, 42, 67, .04); }

        .feature-card .number { display: inline-flex; width: 30px; height: 30px; align-items: center; justify-content: center; border-radius: 50%; background: var(--sky); color: var(--blue); font-size: .82rem; font-weight: 800; margin-bottom: .7rem; }

        .feature-card strong { display: block; font-size: .98rem; margin-bottom: .3rem; color: var(--ink); }

        .feature-card span { color: var(--muted); font-size: .88rem; line-height: 1.4; }

        .notice { background: #eef6ff; color: #284c75; border: 1px solid #cbe0f9; border-radius: 12px; padding: .85rem 1rem; font-size: .9rem; margin: 1.25rem 0 .5rem; }

        .report-hero { background: white; border: 1px solid var(--line); border-radius: 18px; padding: 1.5rem 1.7rem; margin: 1.8rem 0 1rem; }

        .report-label { color: var(--blue); font-size: .76rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; }

        .claim { font-size: 1.2rem; line-height: 1.55; color: var(--ink); margin-top: .55rem; }

        .finding { background: #fff; border: 1px solid var(--line); border-left: 5px solid #ea8f23; border-radius: 12px; padding: 1rem 1.2rem; margin: .65rem 0; }

        .finding-type { color: #9b5b10; font-size: .78rem; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; }

        .finding-quote { color: #273b58; font-style: italic; line-height: 1.55; margin: .45rem 0; }

        .finding-copy { color: var(--muted); font-size: .92rem; line-height: 1.5; }

        [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: .45rem; border-bottom: 1px solid var(--line); padding-bottom: .35rem; }

        [data-testid="stTabs"] button { background: #eaf1fa !important; border: 1px solid #cfdbeb !important; border-radius: 9px 9px 0 0; color: #193b63 !important; font-weight: 750; opacity: 1 !important; padding: .65rem 1rem; }

        [data-testid="stTabs"] button p { color: #193b63 !important; font-weight: 750 !important; opacity: 1 !important; }

        [data-testid="stTabs"] button[aria-selected="true"] { background: #1769e0 !important; border-color: #1769e0 !important; }

        [data-testid="stTabs"] button[aria-selected="true"] p { color: #ffffff !important; }

        [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: #1769e0 !important; height: 3px !important; }

        [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input { background: #ffffff !important; border-radius: 10px; color: #12233f !important; -webkit-text-fill-color: #12233f !important; caret-color: #1769e0 !important; }

        [data-testid="stTextArea"] textarea::placeholder, [data-testid="stTextInput"] input::placeholder { color: #6d7f99 !important; -webkit-text-fill-color: #6d7f99 !important; opacity: 1 !important; }

        [data-testid="stFileUploader"] { background: white; border: 1px dashed #aabed7; border-radius: 12px; padding: .8rem; }

        .stButton > button { border-radius: 10px; font-weight: 700; padding: .6rem 1rem; }

        @media (max-width: 720px) { [data-testid="stMainBlockContainer"] { padding: 1.2rem 1rem 3rem; } .hero { padding: 2rem 1.4rem; border-radius: 18px; } }

        </style>

        """,

        unsafe_allow_html=True,

    )





def request_analysis(path: str, **kwargs):

    try:

        response = httpx.post(
            f"{API_URL}{path}",
            timeout=60.0,
            **kwargs,
        )

        response.raise_for_status()

        return response.json(), None

    except httpx.HTTPStatusError as exc:

        try:

            detail = exc.response.json().get(
                "detail",
                exc.response.text,
            )

        except ValueError:

            detail = exc.response.text

        return None, str(detail)

    except httpx.HTTPError:

        return (
            None,
            f"Could not reach the analysis API at {API_URL}. "
            "Start the FastAPI server and try again.",
        )





def feature_card(
    column,
    number: str,
    title: str,
    copy: str,
) -> None:

    with column:

        st.markdown(

            f'<div class="feature-card"><div class="number">{number}</div><strong>{title}</strong><span>{copy}</span></div>',

            unsafe_allow_html=True,

        )





def render_report(report: dict) -> None:

    explanation = report["explanation"]

    central_claim = escape(explanation["central_claim"])

    st.markdown(

        f"""

        <div class="report-hero">

          <div class="report-label">Analysis report</div>

          <div class="claim">{central_claim}</div>

        </div>

        """,

        unsafe_allow_html=True,

    )

    st.markdown(
        "<div class='section-title'>What the analyzer found</div>",
        unsafe_allow_html=True,
    )

    st.write(explanation["summary"])



    findings = report["findings"]

    if not findings:

        st.success(
            "No configured language signals were found. "
            "This does not verify that the article is accurate."
        )

    for finding in findings:

        finding_type = escape(finding["type"])

        trigger = escape(finding["trigger"])

        passage = escape(finding["passage"])

        finding_explanation = escape(finding["explanation"])

        st.markdown(

            f"""

            <div class="finding">

              <div class="finding-type">{finding_type} · Trigger: {trigger}</div>

              <div class="finding-quote">“{passage}”</div>

              <div class="finding-copy">{finding_explanation}</div>

            </div>

            """,

            unsafe_allow_html=True,

        )



    comparisons = report.get("claim_comparisons", [])

    if comparisons:

        st.markdown(
            "<div class='section-title'>Claim-to-evidence comparison</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "Results compare wording with the local dataset; "
            "they are not fact-check verdicts."
        )

        status_colors = {

            "aligned with available evidence": "🟢",

            "contradicted by available evidence": "🔴",

            "mixed evidence": "🟠",

            "insufficient evidence": "⚪",

        }

        for comparison in comparisons:

            marker = status_colors.get(
                comparison["status"],
                "•",
            )

            with st.expander(
                f"{marker} {comparison['status'].title()} — "
                f"{comparison['type']}"
            ):

                st.write(
                    f"**Claim:** {comparison['claim']}"
                )

                st.write(comparison["summary"])

                if not comparison["evidence"]:

                    st.caption(
                        "No relevant evidence was found in "
                        "the current local dataset."
                    )

                for item in comparison["evidence"]:

                    source = escape(
                        item.get("source")
                        or "Local article corpus"
                    )

                    st.markdown(
                        f"**{source}** · {item['relationship']}"
                    )

                    st.write(item["excerpt"])

                    if item.get("url"):

                        st.link_button(
                            "Open original source",
                            item["url"],
                        )



    render_evidence_visualization(comparisons)



    source_coverage = report.get(
        "source_coverage",
        [],
    )

    if len(source_coverage) > 1:

        st.markdown(
            "<div class='section-title'>Cross-source coverage</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "This compares what available sources emphasize; "
            "it does not assign political labels or source-quality ratings."
        )

        for item in source_coverage:

            with st.expander(item["source"]):

                if item["distinct_emphasis"]:

                    st.write(
                        "Distinct terms in retrieved coverage: "
                        + ", ".join(
                            item["distinct_emphasis"]
                        )
                    )

                for excerpt in item["excerpts"]:

                    st.write(excerpt)

                if item.get("url"):

                    st.link_button(
                        "Open source",
                        item["url"],
                    )



    political_framing = report.get(
        "political_framing",
        {},
    ).get(
        "findings",
        [],
    )

    if political_framing:

        st.markdown(
            "<div class='section-title'>Political framing signals</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "These signals describe wording, not the writer's ideology "
            "or the truth of the article."
        )

        for finding in political_framing:

            finding_type = escape(
                finding["type"]
            )

            trigger = escape(
                finding["trigger"]
            )

            passage = escape(
                finding["passage"]
            )

            finding_explanation = escape(
                finding["explanation"]
            )

            st.markdown(

                f"""

                <div class="finding">

                  <div class="finding-type">{finding_type} · Trigger: {trigger}</div>

                  <div class="finding-quote">“{passage}”</div>

                  <div class="finding-copy">{finding_explanation}</div>

                </div>

                """,

                unsafe_allow_html=True,

            )



    left, right = st.columns(
        [1.15, 1],
        gap="large",
    )

    with left:

        st.markdown(
            "<div class='section-title'>Related evidence</div>",
            unsafe_allow_html=True,
        )

        st.write(
            report["evidence_assessment"]["summary"]
        )

        if not report["evidence"]:

            st.caption(
                "No sufficiently relevant evidence was found "
                "in the local corpus."
            )

        for evidence in report["evidence"]:

            with st.expander(
                evidence["source"]
            ):

                st.write(
                    evidence["excerpt"]
                )

                if evidence.get("url"):

                    st.link_button(
                        "Open original source",
                        evidence["url"],
                    )

    with right:

        st.markdown(
            "<div class='section-title'>How to use this</div>",
            unsafe_allow_html=True,
        )

        st.info(
            explanation["how_to_read_this"]
        )

        with st.expander(
            "Important limitations"
        ):

            for limitation in explanation["limitations"]:

                st.write(
                    f"- {limitation}"
                )

            st.write(
                f"- {report.get('comparison_limitation', '')}"
            )





apply_styles()

st.markdown(

    f"""

    <section class="hero">

      <div class="eyebrow">News literacy, made practical</div>

      <h1>{PROJECT_TITLE}</h1>

      <p>Examine a news story before you share it. We point out wording that deserves a closer look and explain it in clear, everyday language.</p>

    </section>

    """,

    unsafe_allow_html=True,

)



feature_columns = st.columns(
    3,
    gap="medium",
)

feature_card(
    feature_columns[0],
    "01",
    "Add an article",
    "Paste text, upload a document, or bring in a public article link.",
)

feature_card(
    feature_columns[1],
    "02",
    "Review the signals",
    "See the exact sentences that contain persuasive or biased wording.",
)

feature_card(
    feature_columns[2],
    "03",
    "Read critically",
    "Use the related evidence and limitations to make up your own mind.",
)



st.markdown(
    "<div class='section-title'>Start an analysis</div>",
    unsafe_allow_html=True,
)

st.markdown(
    "<p class='section-copy'>Choose the way you want to provide the news article.</p>",
    unsafe_allow_html=True,
)



tab_text, tab_file, tab_url = st.tabs(
    [
        "Paste article text",
        "Upload a document",
        "Use an article link",
    ]
)



with tab_text:

    text = st.text_area(
        "Article text",
        height=240,
        placeholder="Paste the news article here…",
        label_visibility="collapsed",
    )

    if st.button(
        "Analyze article",
        type="primary",
        key="analyze_text",
    ):

        report, error = request_analysis(
            "/analyze",
            json={"text": text},
        )

        if error:

            st.error(error)

        else:

            st.session_state["report"] = report



with tab_file:

    st.caption(
        "Supported formats: PDF, Word (.docx), and text files. "
        "Maximum size: 10 MB."
    )

    uploaded = st.file_uploader(
        "Choose a document",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed",
    )

    if st.button(
        "Analyze document",
        type="primary",
        key="analyze_file",
        disabled=uploaded is None,
    ):

        report, error = request_analysis(

            "/analyze-file",

            files={
                "file": (
                    uploaded.name,
                    uploaded.getvalue(),
                    uploaded.type,
                )
            },

        )

        if error:

            st.error(error)

        else:

            st.session_state["report"] = report



with tab_url:

    st.caption(
        "Use a publicly accessible link, then review the extracted article before analyzing it."
    )

    url = st.text_input(
        "Article URL",
        placeholder="https://example.com/news-story",
        label_visibility="collapsed",
    )

    if st.button(
        "Extract article",
        type="primary",
        key="extract_url",
        disabled=not url,
    ):

        extraction, error = request_analysis(
            "/extract-url",
            json={"url": url},
        )

        if error:

            st.error(error)

        else:

            st.session_state["extracted_url"] = extraction



    if extraction := st.session_state.get(
        "extracted_url"
    ):

        st.caption(
            f"Review the extracted text from: "
            f"{extraction['source']['name']}"
        )

        reviewed_text = st.text_area(

            "Extracted article text",

            value=extraction["text"],

            height=300,

            key="reviewed_url_text",

        )

        if st.button(
            "Analyze reviewed article",
            type="primary",
            key="analyze_reviewed_url",
        ):

            report, error = request_analysis(
                "/analyze",
                json={"text": reviewed_text},
            )

            if error:

                st.error(error)

            else:

                st.session_state["report"] = report

        if st.button(
            "Add reviewed article to local knowledge base",
            key="add_to_knowledge_base",
        ):

            result, error = request_analysis(

                "/knowledge-base/add",

                json={

                    "text": reviewed_text,

                    "source_name": extraction["source"]["name"],

                    "source_url": extraction["source"].get("url"),

                },

            )

            if error:

                st.error(error)

            elif result["added"]:

                st.success(
                    f"Saved. The local knowledge base now has "
                    f"{result['total_chunks']} searchable chunks."
                )

            else:

                st.info(
                    result["message"]
                )





st.markdown(

    "<div class='notice'>This is an educational tool, not a fact-checking authority. A language signal is a prompt to verify a claim, not proof that an article is false.</div>",

    unsafe_allow_html=True,

)



if report := st.session_state.get(
    "report"
):

    render_report(report)