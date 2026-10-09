"""Text extraction for pasted articles, public URLs, PDF, and DOCX files."""

from __future__ import annotations

import ipaddress
import socket
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from docx import Document


MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_REDIRECTS = 3
USER_AGENT = "NewsLiteracyAnalyzer/0.1 (educational prototype)"
BOILERPLATE_MARKERS = (
    "you are logged in",
    "active subscription",
    "terms & conditions",
    "community guidelines",
    "comments have to be",
    "register and login",
)


def _normalise(text: str) -> str:
    return " ".join(text.split())


def _fallback_html_extraction(html: str) -> str:
    """Conservative fallback for pages the readability extractor cannot parse."""
    soup = BeautifulSoup(html, "html.parser")
    for element in soup.select(
        "script, style, nav, footer, header, aside, form, "
        "[class*='comment'], [id*='comment'], [class*='subscription'], "
        "[id*='subscription'], [class*='login'], [id*='login']"
    ):
        element.decompose()
    root = (
        soup.select_one("[itemprop='articleBody']")
        or soup.select_one(".article-body, .articlebodycontent, .article-content")
        or soup.find("article")
        or soup.find("main")
        or soup
    )
    paragraphs = []
    for paragraph in root.find_all("p"):
        value = _normalise(paragraph.get_text(" ", strip=True))
        if value and not any(marker in value.casefold() for marker in BOILERPLATE_MARKERS):
            paragraphs.append(value)
    return _normalise(" ".join(paragraphs))


def _extract_article_html(html: str) -> str:
    return _fallback_html_extraction(html)


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Please provide a complete http or https URL.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise ValueError("The URL host could not be resolved.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Private or local network URLs are not allowed.")


def extract_url(url: str) -> tuple[str, dict]:
    """Download a public article URL while blocking obvious local-network SSRF."""
    current_url = url
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=15.0, follow_redirects=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            _validate_public_url(current_url)
            response = client.get(current_url)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise ValueError("The URL returned an invalid redirect.")
                current_url = str(response.url.join(location))
                continue
            response.raise_for_status()
            if len(response.content) > MAX_FILE_BYTES:
                raise ValueError("The fetched page is larger than 10 MB.")
            if "html" not in response.headers.get("content-type", "").lower():
                raise ValueError("The URL must point to an HTML article page.")
            soup = BeautifulSoup(response.text, "html.parser")
            title = _normalise(soup.title.get_text(" ", strip=True)) if soup.title else "Untitled article"
            text = _extract_article_html(response.text)
            if not text:
                raise ValueError("No readable article text was found at this URL.")
            return text, {"kind": "url", "name": title, "url": str(response.url)}
    raise ValueError("The URL redirected too many times.")


def extract_file(content: bytes, filename: str) -> tuple[str, dict]:
    if not content:
        raise ValueError("The uploaded file is empty.")
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("Files must be 10 MB or smaller.")

    suffix = Path(filename).suffix.casefold()
    try:
        if suffix == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(BytesIO(content))
            text = _normalise(" ".join(page.extract_text() or "" for page in reader.pages))
        elif suffix == ".docx":
            document = Document(BytesIO(content))
            text = _normalise(" ".join(paragraph.text for paragraph in document.paragraphs))
        elif suffix == ".txt":
            text = _normalise(content.decode("utf-8"))
        else:
            raise ValueError("Supported file types are PDF, DOCX, and TXT.")
    except UnicodeDecodeError as exc:
        raise ValueError("TXT files must be UTF-8 encoded.") from exc
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("The file could not be read. It may be encrypted or malformed.") from exc

    if not text:
        raise ValueError("No readable text was found in this file.")
    return text, {"kind": "file", "name": filename}
