"""Weather MCP server 单测（直接调 tool 函数，不起进程）。"""

from __future__ import annotations

from cozy_mcp_tools.weather.__main__ import weather


def test_known_city() -> None:
    r = weather("上海")
    assert r["temperature"] == 22


def test_unknown_city_returns_mock() -> None:
    r = weather("火星")
    assert r.get("mock") is True
