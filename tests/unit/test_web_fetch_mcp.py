"""Unit tests for the web_fetch MCP tool."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from cozy_mcp_tools.web_fetch.__main__ import _extract_text, web_fetch


# ---------------------------------------------------------------------------
# _extract_text tests
# ---------------------------------------------------------------------------


def test_extract_text_uses_article_tag() -> None:
    html = """<html><body>
        <header>Nav stuff</header>
        <article>Main article content here.</article>
        <footer>Footer</footer>
    </body></html>"""
    text, title = _extract_text(html)
    assert "Main article content here." in text
    # header and footer should be stripped
    assert "Nav stuff" not in text
    assert "Footer" not in text


def test_extract_text_uses_main_tag() -> None:
    html = """<html><body>
        <nav>Navigation</nav>
        <main>Primary content in main.</main>
    </body></html>"""
    text, title = _extract_text(html)
    assert "Primary content in main." in text
    assert "Navigation" not in text


def test_extract_text_strips_script_and_style() -> None:
    html = """<html><body>
        <script>var x = 1;</script>
        <style>.foo { color: red; }</style>
        <p>Clean paragraph text.</p>
    </body></html>"""
    text, title = _extract_text(html)
    assert "Clean paragraph text." in text
    assert "var x = 1" not in text
    assert ".foo" not in text


def test_extract_text_falls_back_to_body() -> None:
    html = """<html><body>
        <p>Body fallback content.</p>
    </body></html>"""
    text, title = _extract_text(html)
    assert "Body fallback content." in text


def test_extract_text_returns_title() -> None:
    html = """<html><head><title>Test Page Title</title></head>
        <body><p>Some content.</p></body></html>"""
    text, title = _extract_text(html)
    assert title == "Test Page Title"


def test_extract_text_title_none_when_missing() -> None:
    html = "<html><body><p>No title here.</p></body></html>"
    text, title = _extract_text(html)
    assert title is None


# ---------------------------------------------------------------------------
# web_fetch tests
# ---------------------------------------------------------------------------


def _make_mock_response(
    text: str,
    content_type: str = "text/html; charset=utf-8",
    url: str = "https://example.com/page",
    status_code: int = 200,
) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    resp.content = text.encode()
    resp.headers = {"content-type": content_type}
    resp.url = url
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    return resp


def test_web_fetch_normal_html_page() -> None:
    html = "<html><head><title>Hello</title></head><body><p>World content.</p></body></html>"
    mock_resp = _make_mock_response(html)

    with patch("cozy_mcp_tools.web_fetch.__main__.httpx.get", return_value=mock_resp):
        result = web_fetch("https://example.com/page")

    assert result["title"] == "Hello"
    assert "World content." in result["content"]
    assert result["truncated"] is False
    assert "error" not in result


def test_web_fetch_truncation_at_max_chars() -> None:
    # Generate content definitely longer than 500 chars
    long_text = "A" * 600
    html = f"<html><body><p>{long_text}</p></body></html>"
    mock_resp = _make_mock_response(html)

    with patch("cozy_mcp_tools.web_fetch.__main__.httpx.get", return_value=mock_resp):
        result = web_fetch("https://example.com/page", max_chars=500)

    assert result["truncated"] is True
    assert result["content"].endswith("…（已截断）")
    # Content before suffix should be exactly 500 chars
    suffix = "…（已截断）"
    content_without_suffix = result["content"][: -len(suffix)]
    assert len(content_without_suffix) == 500


def test_web_fetch_invalid_scheme_ftp() -> None:
    result = web_fetch("ftp://example.com/file")
    assert "error" in result
    assert result["url"] == "ftp://example.com/file"


def test_web_fetch_no_netloc() -> None:
    result = web_fetch("http:///path/only")
    assert "error" in result
    assert "URL" in result["error"] or "host" in result["error"]


def test_web_fetch_non_html_content_type() -> None:
    mock_resp = _make_mock_response(
        text=b"\x89PNG\r\n".decode("latin-1"),
        content_type="image/png",
    )

    with patch("cozy_mcp_tools.web_fetch.__main__.httpx.get", return_value=mock_resp):
        result = web_fetch("https://example.com/image.png")

    assert "error" in result
    assert "image/png" in result["error"]


def test_web_fetch_timeout_error() -> None:
    with patch(
        "cozy_mcp_tools.web_fetch.__main__.httpx.get",
        side_effect=httpx.TimeoutException("timed out"),
    ):
        result = web_fetch("https://example.com/slow")

    assert "error" in result
    assert "超时" in result["error"]


def test_web_fetch_http_status_error() -> None:
    error_response = MagicMock()
    error_response.status_code = 404
    exc = httpx.HTTPStatusError(
        "404 Not Found", request=MagicMock(), response=error_response
    )

    with patch("cozy_mcp_tools.web_fetch.__main__.httpx.get", side_effect=exc):
        result = web_fetch("https://example.com/missing")

    assert "error" in result
    assert "404" in result["error"]


def test_web_fetch_generic_exception() -> None:
    with patch(
        "cozy_mcp_tools.web_fetch.__main__.httpx.get",
        side_effect=ConnectionError("network down"),
    ):
        result = web_fetch("https://example.com/page")

    assert "error" in result
    assert "ConnectionError" in result["error"] or "抓取失败" in result["error"]
