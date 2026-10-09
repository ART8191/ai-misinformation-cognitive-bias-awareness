from backend.document_ingestion import _extract_article_html


def test_html_extraction_removes_subscription_and_comment_boilerplate():
    html = """
    <html><head><title>Test story</title></head><body>
      <nav>Navigation</nav>
      <article><p>The report says the policy changed.</p><p>Officials gave no timeline.</p></article>
      <div class="subscription"><p>You are logged in. Active subscription.</p></div>
      <footer><p>Terms &amp; conditions</p></footer>
    </body></html>
    """

    text = _extract_article_html(html)

    assert "policy changed" in text
    assert "Active subscription" not in text
    assert "Terms & conditions" not in text
