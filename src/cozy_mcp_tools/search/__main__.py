"""Search MCP server — DuckDuckGo HTML 真搜索（无需 API key）。

使用 https://html.duckduckgo.com/html/?q=... 端点，BeautifulSoup 解析结果。
超时 8s，失败返回结构化错误。
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import emit_log, setup_logging

logger = setup_logging("search")
mcp = FastMCP("cozy-search")

_DDG_URL = "https://html.duckduckgo.com/html/"
_TIMEOUT = 8.0
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
}


@mcp.tool()
def search(query: str, top_k: int = 5) -> dict[str, Any]:
    """搜索网页（DuckDuckGo HTML 端点，无 API key，全球可用）。

    Args:
        query: 搜索关键词
        top_k: 返回条数上限，默认 5，最大 10

    Returns:
        成功: {query, results: [{title, url, snippet}, ...]}
        失败: {query, error}
    """
    top_k = max(1, min(top_k, 10))
    logger.info("search: query=%s top_k=%d", query, top_k)
    emit_log(tool="search", action="start", query=query, top_k=top_k)
    _start = time.monotonic()
    try:
        resp = httpx.post(
            _DDG_URL,
            data={"q": query},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[dict[str, str]] = []
        for result in soup.select("div.result")[: top_k * 2]:
            link = result.select_one("a.result__a")
            snippet_el = result.select_one("a.result__snippet") or result.select_one(".result__snippet")
            if not link:
                continue
            title = link.get_text(strip=True)
            url = link.get("href", "")
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            if not title or not url:
                continue
            results.append({"title": title, "url": url, "snippet": snippet})
            if len(results) >= top_k:
                break
        duration_ms = round((time.monotonic() - _start) * 1000, 2)
        if not results:
            emit_log(
                tool="search", action="end", duration_ms=duration_ms,
                status="ok", query=query, result_count=0,
            )
            return {"query": query, "results": [], "note": "未找到结果"}
        emit_log(
            tool="search", action="end", duration_ms=duration_ms,
            status="ok", query=query, result_count=len(results),
        )
        return {"query": query, "results": results}
    except httpx.TimeoutException:
        logger.warning("search timeout: %s", query)
        emit_log(
            tool="search", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error="timeout", query=query,
        )
        return {"query": query, "error": "搜索超时（8s），请稍后再试"}
    except Exception as e:
        logger.exception("search error")
        emit_log(
            tool="search", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error=f"{type(e).__name__}: {str(e)[:200]}", query=query,
        )
        return {"query": query, "error": f"搜索失败: {type(e).__name__}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
