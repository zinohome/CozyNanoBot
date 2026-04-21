from __future__ import annotations

from cozy_mcp_tools.search.__main__ import search


def test_default_top_k() -> None:
    r = search("Python")
    assert len(r) == 3
    assert all("Python" in item["title"] for item in r)


def test_custom_top_k() -> None:
    assert len(search("x", top_k=7)) == 7
