"""Weather MCP server。启动：`python -m cozy_mcp_tools.weather`。

M1 使用固定 mock 数据。nanobot 作为 MCP client 连接 stdio transport，
通过 tools/list 获取 `weather` 工具，通过 tools/call 调用。
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import setup_logging

logger = setup_logging("weather")

mcp = FastMCP("cozy-weather")


_MOCK = {
    "上海": {"temperature": 22, "condition": "晴", "humidity": 65},
    "北京": {"temperature": 18, "condition": "多云", "humidity": 50},
    "广州": {"temperature": 28, "condition": "小雨", "humidity": 85},
}


@mcp.tool()
def weather(city: str) -> dict[str, Any]:
    """查询指定城市的天气（M1 mock 数据）。

    Args:
        city: 城市名，例如 上海 / 北京 / 广州

    Returns:
        天气字典，含 temperature / condition / humidity
    """
    logger.info("weather query: %s", city)
    return _MOCK.get(
        city,
        {"temperature": 20, "condition": "未知", "humidity": 60, "mock": True},
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
