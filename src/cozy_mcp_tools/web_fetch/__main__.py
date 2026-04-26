"""Web fetch MCP server — 抓取 URL 并提取正文。

用 httpx 抓 HTML，BeautifulSoup 剥 <script>/<style>/<nav>/<footer>，
抽出 <article> 或 <main> 或 body 正文，长度截断防爆 context。
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import emit_log, setup_logging

logger = setup_logging("web_fetch")
mcp = FastMCP("cozy-web-fetch")

_TIMEOUT = 10.0
_MAX_CHARS = 4000  # 防爆 context
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; cozy-nanobot/1.0; +https://github.com/zinohome)"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

_NOISE_TAGS = ("script", "style", "nav", "footer", "aside", "iframe", "noscript", "header")


def _extract_text(html: str) -> tuple[str, str | None]:
    """返回 (正文, 页面标题)。"""
    soup = BeautifulSoup(html, "html.parser")
    for tag_name in _NOISE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    title_el = soup.find("title")
    title = title_el.get_text(strip=True) if title_el else None
    container = soup.find("article") or soup.find("main") or soup.body or soup
    text = container.get_text(separator="\n", strip=True)
    # 折叠多余空行
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines), title


@mcp.tool()
def web_fetch(url: str, max_chars: int = _MAX_CHARS) -> dict[str, Any]:
    """抓取指定 URL 并提取正文文本（去广告/脚本/导航）。

    Args:
        url: 完整 URL，必须是 http:// 或 https://
        max_chars: 正文最大字符数（默认 4000，最大 10000）

    Returns:
        成功: {url, title, content, truncated, bytes}
        失败: {url, error}
    """
    max_chars = max(500, min(max_chars, 10000))
    logger.info("web_fetch: %s (max_chars=%d)", url, max_chars)
    emit_log(tool="web_fetch", action="start", url=url)
    _start = time.monotonic()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return {"url": url, "error": "只接受 http:// 或 https:// 开头的 URL"}
    if not parsed.netloc:
        return {"url": url, "error": "URL 格式错误（缺 host）"}
    try:
        resp = httpx.get(
            url,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        if "html" not in ctype.lower() and "text" not in ctype.lower():
            return {"url": url, "error": f"非文本/HTML 内容 (content-type={ctype})"}
        content, title = _extract_text(resp.text)
        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars] + "…（已截断）"
        emit_log(
            tool="web_fetch", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="ok", url=url,
        )
        return {
            "url": str(resp.url),
            "title": title,
            "content": content,
            "truncated": truncated,
            "bytes": len(resp.content),
        }
    except httpx.TimeoutException:
        emit_log(
            tool="web_fetch", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error="timeout", url=url,
        )
        return {"url": url, "error": "抓取超时（10s）"}
    except httpx.HTTPStatusError as e:
        emit_log(
            tool="web_fetch", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error=f"http_{e.response.status_code}", url=url,
        )
        return {"url": url, "error": f"HTTP {e.response.status_code}"}
    except Exception as e:
        logger.exception("web_fetch error")
        emit_log(
            tool="web_fetch", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="error", error=f"{type(e).__name__}", url=url,
        )
        return {"url": url, "error": f"抓取失败: {type(e).__name__}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
