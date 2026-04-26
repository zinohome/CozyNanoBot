"""News MCP server — 免费 RSS 聚合。

从若干公开 RSS 源抓取最新条目，支持关键词过滤与分类。
无 API key，超时 8s，死链自动跳过。
"""

from __future__ import annotations

import time
from typing import Any

import feedparser
import httpx

from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import emit_log, setup_logging

logger = setup_logging("news")
mcp = FastMCP("cozy-news")

_TIMEOUT = 8.0
_USER_AGENT = "cozy-nanobot/1.0 (+https://github.com/)"

# 经 2026-04-22 curl 验证可访问的 RSS 源
# 死掉：Reuters、BBC http、zhihu rss → 已剔除
_FEEDS: list[dict[str, str]] = [
    # --- 英文 ---
    {
        "name": "BBC World",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "world",
        "lang": "en",
    },
    {
        "name": "BBC Tech",
        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "category": "tech",
        "lang": "en",
    },
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "category": "tech",
        "lang": "en",
    },
    {
        "name": "WSJ World",
        "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "category": "world",
        "lang": "en",
    },
    # --- 中文 ---
    {
        "name": "人民网时政",
        "url": "http://www.people.com.cn/rss/politics.xml",
        "category": "cn",
        "lang": "zh",
    },
    {
        "name": "36Kr",
        "url": "https://36kr.com/feed",
        "category": "tech",
        "lang": "zh",
    },
    {
        "name": "FT中文网",
        "url": "https://www.ftchinese.com/rss/news",
        "category": "cn",
        "lang": "zh",
    },
]


def _fetch_feed(url: str) -> Any:
    """Fetch RSS via httpx (显式 UA 更稳) + feedparser parse。"""
    try:
        resp = httpx.get(
            url,
            timeout=_TIMEOUT,
            headers={"User-Agent": _USER_AGENT},
            follow_redirects=True,
        )
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception as e:
        logger.warning("feed fetch failed %s: %s", url, type(e).__name__)
        return None


def _entry_to_item(entry: Any, source_name: str) -> dict[str, str]:
    summary = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
    # 粗剥 HTML（避免引入额外依赖）
    if summary:
        import re as _re
        summary = _re.sub(r"<[^>]+>", "", summary).strip()
        if len(summary) > 280:
            summary = summary[:280] + "..."
    return {
        "title": getattr(entry, "title", "").strip(),
        "url": getattr(entry, "link", ""),
        "published": getattr(entry, "published", "") or getattr(entry, "updated", ""),
        "source": source_name,
        "summary": summary,
    }


@mcp.tool()
def news(query: str = "", top_k: int = 5, category: str = "") -> dict[str, Any]:
    """获取最新新闻（免费 RSS 聚合）。**用户问"最新新闻/头条/热点/最近发生了什么"就调**。

    触发示例：
    - "有什么新闻" / "最新头条"
    - "最近发生了什么大事"
    - "科技圈最新动态"
    - "AI 相关新闻"（query="AI"）

    Args:
        query: 关键词过滤（不分大小写，在 title/summary 里匹配）；默认空=不过滤
        top_k: 返回条数，默认 5，上限 15
        category: "tech" / "world" / "cn" / "en" 或 "" 不过滤

    Returns:
        成功: {results: [{title, url, published, source, summary}, ...]}
        无结果: {results: [], note: "..."}
        失败: {error}
    """
    top_k = max(1, min(top_k, 15))
    q = query.strip().lower()
    cat = category.strip().lower()

    feeds = _FEEDS
    if cat == "tech":
        feeds = [f for f in _FEEDS if f["category"] == "tech"]
    elif cat == "world":
        feeds = [f for f in _FEEDS if f["category"] == "world"]
    elif cat == "cn":
        feeds = [f for f in _FEEDS if f["lang"] == "zh"]
    elif cat == "en":
        feeds = [f for f in _FEEDS if f["lang"] == "en"]
    elif cat and cat != "":
        return {"error": f"不支持的 category: {category}"}

    logger.info("news: query=%r top_k=%d category=%r feeds=%d",
                query, top_k, category, len(feeds))
    emit_log(tool="news", action="start", query=query, category=category, top_k=top_k)
    _start = time.monotonic()

    items: list[dict[str, str]] = []
    for feed_meta in feeds:
        parsed = _fetch_feed(feed_meta["url"])
        if not parsed or not getattr(parsed, "entries", None):
            continue
        for entry in parsed.entries[:10]:
            item = _entry_to_item(entry, feed_meta["name"])
            if not item["title"]:
                continue
            if q:
                haystack = (item["title"] + " " + item["summary"]).lower()
                if q not in haystack:
                    continue
            items.append(item)

    if not items:
        emit_log(
            tool="news", action="end",
            duration_ms=round((time.monotonic() - _start) * 1000, 2),
            status="ok", result_count=0,
        )
        return {
            "results": [],
            "note": "未找到匹配的新闻条目（可能 RSS 源全失败或关键词无命中）",
        }

    # 简单截断（不排序，各源交替的原始顺序已足够）
    emit_log(
        tool="news", action="end",
        duration_ms=round((time.monotonic() - _start) * 1000, 2),
        status="ok", result_count=len(items[:top_k]),
    )
    return {"results": items[:top_k]}


if __name__ == "__main__":
    mcp.run(transport="stdio")
