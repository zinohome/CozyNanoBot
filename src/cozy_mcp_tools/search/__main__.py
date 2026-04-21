"""Search MCP server（M1 mock）。"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import setup_logging

logger = setup_logging("search")
mcp = FastMCP("cozy-search")


@mcp.tool()
def search(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """网页搜索，返回摘要列表（M1 mock 数据）。

    Args:
        query: 搜索关键词
        top_k: 返回条数，默认 3

    Returns:
        [{title, url, snippet}, ...]
    """
    logger.info("search: query=%s top_k=%d", query, top_k)
    return [
        {
            "title": f"示例结果 {i + 1}：{query}",
            "url": f"https://example.com/{i}",
            "snippet": "这是一条 mock 的搜索摘要",
        }
        for i in range(top_k)
    ]


if __name__ == "__main__":
    mcp.run(transport="stdio")
