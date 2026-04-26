"""Search MCP tool unit tests — fully mocked, no real HTTP calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from cozy_mcp_tools.search.__main__ import search


def _make_html_response(results: list[dict]) -> str:
    """Build minimal DuckDuckGo-style HTML with div.result elements."""
    items = []
    for r in results:
        snippet_html = (
            f'<a class="result__snippet">{r.get("snippet", "")}</a>'
            if r.get("snippet")
            else ""
        )
        items.append(
            f'<div class="result">'
            f'<a class="result__a" href="{r["url"]}">{r["title"]}</a>'
            f'{snippet_html}'
            f'</div>'
        )
    return "<html><body>" + "".join(items) + "</body></html>"


def _mock_response(html: str, status_code: int = 200) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.text = html
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# Test 1: normal search returns parsed results
# ---------------------------------------------------------------------------

def test_normal_search_returns_parsed_results() -> None:
    html = _make_html_response([
        {"title": "Python Official", "url": "https://python.org", "snippet": "The Python language home."},
        {"title": "Python Tutorial", "url": "https://docs.python.org/tutorial", "snippet": "Official tutorial."},
        {"title": "Python Wiki",    "url": "https://wiki.python.org", "snippet": "Community wiki."},
    ])
    with patch("cozy_mcp_tools.search.__main__.httpx.post", return_value=_mock_response(html)) as mock_post:
        result = search("Python")

    mock_post.assert_called_once()
    assert result["query"] == "Python"
    assert isinstance(result["results"], list)
    assert len(result["results"]) == 3
    first = result["results"][0]
    assert first["title"] == "Python Official"
    assert first["url"] == "https://python.org"
    assert first["snippet"] == "The Python language home."


# ---------------------------------------------------------------------------
# Test 2: empty results (no div.result in HTML)
# ---------------------------------------------------------------------------

def test_empty_results_when_no_divs() -> None:
    html = "<html><body><p>No results found.</p></body></html>"
    with patch("cozy_mcp_tools.search.__main__.httpx.post", return_value=_mock_response(html)):
        result = search("xyznonexistentquery12345")

    assert result["query"] == "xyznonexistentquery12345"
    assert result["results"] == []


# ---------------------------------------------------------------------------
# Test 3: top_k limits the number of returned results
# ---------------------------------------------------------------------------

def test_top_k_limits_results() -> None:
    # Provide 8 results in HTML; top_k=3 should cap at 3
    items = [
        {"title": f"Result {i}", "url": f"https://example.com/{i}", "snippet": f"Snippet {i}"}
        for i in range(8)
    ]
    html = _make_html_response(items)
    with patch("cozy_mcp_tools.search.__main__.httpx.post", return_value=_mock_response(html)):
        result = search("test", top_k=3)

    assert len(result["results"]) == 3


# ---------------------------------------------------------------------------
# Test 4: TimeoutException returns error dict
# ---------------------------------------------------------------------------

def test_timeout_returns_error_dict() -> None:
    with patch(
        "cozy_mcp_tools.search.__main__.httpx.post",
        side_effect=httpx.TimeoutException("timed out"),
    ):
        result = search("Python")

    assert result["query"] == "Python"
    assert "error" in result
    assert "超时" in result["error"]
    assert "results" not in result


# ---------------------------------------------------------------------------
# Test 5: generic exception returns error dict
# ---------------------------------------------------------------------------

def test_generic_exception_returns_error_dict() -> None:
    with patch(
        "cozy_mcp_tools.search.__main__.httpx.post",
        side_effect=RuntimeError("connection refused"),
    ):
        result = search("Python")

    assert result["query"] == "Python"
    assert "error" in result
    assert "RuntimeError" in result["error"]
    assert "results" not in result
