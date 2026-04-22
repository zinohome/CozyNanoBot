"""Weather MCP server — 真 API (wttr.in)。

wttr.in 是公开服务（无需 API key）。支持 JSON 输出 format=j1。
全球城市 + 中文名查询。超时 6s，失败降级为结构化错误（由 LLM 解释）。
"""

from __future__ import annotations

from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import setup_logging

logger = setup_logging("weather")
mcp = FastMCP("cozy-weather")

_WTTR_BASE = "https://wttr.in"
_TIMEOUT = 6.0

_CONDITION_CN = {
    "Clear": "晴", "Sunny": "晴",
    "Partly cloudy": "多云", "Cloudy": "多云", "Overcast": "阴",
    "Mist": "薄雾", "Fog": "雾",
    "Patchy rain possible": "可能有阵雨", "Light rain": "小雨",
    "Moderate rain": "中雨", "Heavy rain": "大雨",
    "Light snow": "小雪", "Moderate snow": "中雪", "Heavy snow": "大雪",
    "Thunderstorm": "雷暴", "Patchy rain nearby": "附近有阵雨",
}


def _translate_condition(en: str) -> str:
    return _CONDITION_CN.get(en.strip(), en)


@mcp.tool()
def weather(city: str) -> dict[str, Any]:
    """查询任何城市的当前天气。**只要用户提到城市 + 冷/热/下雨/温度/湿度/穿什么，就调这个工具**，
    不要从训练知识或闲聊式回答代替。中文俗语请先映射到正式城市名：
    魔都→上海、帝都→北京、羊城/花城→广州、山城→重庆、蓉城→成都。

    触发示例：
    - "查上海天气" / "北京温度多少度"
    - "上海冷吗" / "魔都冷吗" / "广州适合穿什么" ← 间接询问也要调
    - "Tokyo weather" / "weather in Shanghai"
    - 繁体 "查上海天氣" 照调（city 繁简一致）

    不触发的仅：过去天气 / 天气预报 / 假设 / 比喻（"心情的天气"）/ 无城市线索。

    Args:
        city: 城市名（已映射俗语后），例如 上海 / Tokyo / New York

    Returns:
        成功: {city, temperature, condition, humidity, wind, feels_like, source}
        失败: {city, error}
    """
    logger.info("weather query: %s", city)
    try:
        resp = httpx.get(
            f"{_WTTR_BASE}/{city}",
            params={"format": "j1"},
            timeout=_TIMEOUT,
            headers={"User-Agent": "cozy-nanobot/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        current = data["current_condition"][0]
        return {
            "city": city,
            "temperature": int(current["temp_C"]),
            "condition": _translate_condition(current["weatherDesc"][0]["value"]),
            "humidity": int(current["humidity"]),
            "wind": f"{current['windspeedKmph']} km/h {current['winddir16Point']}",
            "feels_like": int(current["FeelsLikeC"]),
            "source": "wttr.in",
        }
    except httpx.TimeoutException:
        logger.warning("weather timeout for %s", city)
        return {"city": city, "error": "查询超时（6s），请稍后再试"}
    except httpx.HTTPStatusError as e:
        logger.warning("weather http error %s for %s", e.response.status_code, city)
        return {"city": city, "error": f"未找到城市「{city}」或服务异常 (HTTP {e.response.status_code})"}
    except Exception as e:
        logger.exception("weather unexpected error")
        return {"city": city, "error": f"查询失败: {type(e).__name__}"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
