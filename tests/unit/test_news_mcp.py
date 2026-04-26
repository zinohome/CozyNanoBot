"""Unit tests for the news MCP tool."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cozy_mcp_tools.news.__main__ import _entry_to_item, _fetch_feed, news


# ---------------------------------------------------------------------------
# _entry_to_item tests
# ---------------------------------------------------------------------------


def _make_entry(
    title: str = "Test Title",
    link: str = "https://example.com/article",
    published: str = "Mon, 01 Jan 2026 00:00:00 GMT",
    summary: str = "Plain summary text.",
) -> SimpleNamespace:
    return SimpleNamespace(
        title=title,
        link=link,
        published=published,
        summary=summary,
    )


def test_entry_to_item_strips_html_tags() -> None:
    entry = _make_entry(summary="<p>Hello <b>world</b>!</p>")
    item = _entry_to_item(entry, "Test Source")
    assert "<p>" not in item["summary"]
    assert "<b>" not in item["summary"]
    assert "Hello" in item["summary"]
    assert "world" in item["summary"]


def test_entry_to_item_truncates_long_summary() -> None:
    long_summary = "X" * 400
    entry = _make_entry(summary=long_summary)
    item = _entry_to_item(entry, "Test Source")
    assert len(item["summary"]) <= 283  # 280 + "..."
    assert item["summary"].endswith("...")


def test_entry_to_item_handles_missing_fields_gracefully() -> None:
    # Entry with no title, no link, no published, no summary
    entry = SimpleNamespace()
    item = _entry_to_item(entry, "Sparse Source")
    assert item["title"] == ""
    assert item["url"] == ""
    assert item["published"] == ""
    assert item["summary"] == ""
    assert item["source"] == "Sparse Source"


def test_entry_to_item_uses_description_fallback() -> None:
    entry = SimpleNamespace(
        title="Title",
        link="https://example.com",
        published="",
        description="Fallback description text.",
    )
    item = _entry_to_item(entry, "Source")
    assert "Fallback description text." in item["summary"]


def test_entry_to_item_uses_updated_as_published_fallback() -> None:
    entry = SimpleNamespace(
        title="Title",
        link="https://example.com",
        published="",
        updated="Tue, 02 Jan 2026 00:00:00 GMT",
        summary="",
    )
    item = _entry_to_item(entry, "Source")
    assert item["published"] == "Tue, 02 Jan 2026 00:00:00 GMT"


# ---------------------------------------------------------------------------
# news() tests
# ---------------------------------------------------------------------------


def _make_parsed_feed(entries: list) -> MagicMock:
    """Return a feedparser-like object with .entries."""
    feed = MagicMock()
    feed.entries = entries
    return feed


def _make_feed_entry(title: str, summary: str = "", link: str = "https://example.com") -> SimpleNamespace:
    return SimpleNamespace(
        title=title,
        link=link,
        published="Mon, 01 Jan 2026 00:00:00 GMT",
        summary=summary,
    )


def test_news_keyword_match() -> None:
    entries = [
        _make_feed_entry("Python AI News Today", "Big advances in machine learning"),
        _make_feed_entry("Sports Results", "Football match results"),
    ]
    parsed = _make_parsed_feed(entries)

    with patch("cozy_mcp_tools.news.__main__._fetch_feed", return_value=parsed):
        result = news(query="python")

    assert "results" in result
    titles = [r["title"] for r in result["results"]]
    assert any("Python" in t for t in titles)
    assert all("Sports" not in t for t in titles)


def test_news_category_filter_tech() -> None:
    """Only tech feeds should be queried when category='tech'."""
    parsed = _make_parsed_feed([_make_feed_entry("Tech article")])

    call_urls: list[str] = []

    def mock_fetch(url: str):
        call_urls.append(url)
        return parsed

    with patch("cozy_mcp_tools.news.__main__._fetch_feed", side_effect=mock_fetch):
        result = news(category="tech")

    # All queried feeds must be tech category
    from cozy_mcp_tools.news.__main__ import _FEEDS
    tech_urls = {f["url"] for f in _FEEDS if f["category"] == "tech"}
    non_tech_urls = {f["url"] for f in _FEEDS if f["category"] != "tech"}

    for url in call_urls:
        assert url in tech_urls, f"Unexpected non-tech feed called: {url}"
    # No non-tech feed should have been called
    for url in non_tech_urls:
        assert url not in call_urls


def test_news_top_k_limits_results() -> None:
    entries = [_make_feed_entry(f"Article {i}") for i in range(10)]
    parsed = _make_parsed_feed(entries)

    with patch("cozy_mcp_tools.news.__main__._fetch_feed", return_value=parsed):
        result = news(top_k=3)

    assert len(result["results"]) <= 3


def test_news_no_matches_returns_empty() -> None:
    entries = [_make_feed_entry("Completely unrelated content")]
    parsed = _make_parsed_feed(entries)

    with patch("cozy_mcp_tools.news.__main__._fetch_feed", return_value=parsed):
        result = news(query="xyzzy_nonexistent_keyword_12345")

    assert result["results"] == []
    assert "note" in result


def test_news_feed_fetch_failure_is_skipped_gracefully() -> None:
    """If _fetch_feed returns None (simulating a failed fetch), it is skipped."""
    # Two feeds: first fails, second succeeds
    good_entries = [_make_feed_entry("Good article from second feed")]
    good_feed = _make_parsed_feed(good_entries)

    call_count = 0

    def mock_fetch(url: str):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return None  # first feed fails
        return good_feed

    with patch("cozy_mcp_tools.news.__main__._fetch_feed", side_effect=mock_fetch):
        result = news()

    # Should not raise, and results from non-failed feeds should be present
    assert "results" in result or "note" in result


def test_news_default_category_queries_all_feeds() -> None:
    """With no category filter, all feeds should be queried."""
    parsed = _make_parsed_feed([_make_feed_entry("Generic news")])

    call_urls: list[str] = []

    def mock_fetch(url: str):
        call_urls.append(url)
        return parsed

    with patch("cozy_mcp_tools.news.__main__._fetch_feed", side_effect=mock_fetch):
        news(category="")

    from cozy_mcp_tools.news.__main__ import _FEEDS
    all_feed_urls = {f["url"] for f in _FEEDS}

    assert set(call_urls) == all_feed_urls


def test_news_invalid_category_returns_error() -> None:
    result = news(category="invalidcat")
    assert "error" in result
