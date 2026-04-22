"""Info tools MCP server — time + unit_convert（轻量工具合并进程）。

按架构决策：无外部 IO、无 key、稳定不变的轻工具合并到一个 MCP server。
- current_time: 返回指定时区的当前时间
- unit_convert: 常用单位换算（温度 / 长度 / 重量）
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import setup_logging

logger = setup_logging("info")
mcp = FastMCP("cozy-info-tools")


_TZ_ALIASES = {
    "beijing": "Asia/Shanghai", "shanghai": "Asia/Shanghai", "china": "Asia/Shanghai",
    "cn": "Asia/Shanghai", "北京": "Asia/Shanghai", "上海": "Asia/Shanghai",
    "tokyo": "Asia/Tokyo", "japan": "Asia/Tokyo", "jp": "Asia/Tokyo",
    "new york": "America/New_York", "nyc": "America/New_York", "ny": "America/New_York",
    "los angeles": "America/Los_Angeles", "la": "America/Los_Angeles",
    "london": "Europe/London", "uk": "Europe/London",
    "paris": "Europe/Paris", "france": "Europe/Paris",
    "utc": "UTC", "gmt": "UTC",
}


@mcp.tool()
def current_time(timezone: str = "Asia/Shanghai") -> dict[str, Any]:
    """获取当前时间。**你对"现在几点/几号/星期几"永远不知道，必须调这个工具，不要猜**。

    触发场景（全部必须调）：
    - "现在几点" / "今天几号" / "今天是星期几" / "几号了"
    - "东京现在几点" / "纽约是白天还是晚上"
    - 任何隐含"当前时间"的问题

    绝不从对话上下文猜日期 —— 即使 system prompt 里有某个日期，也可能过时。

    Args:
        timezone: 时区名（IANA 如 Asia/Shanghai / America/New_York），
                  或别名（beijing / tokyo / nyc / london ...）。默认 Asia/Shanghai。

    Returns:
        {timezone, datetime (ISO 8601), weekday, unix}
    """
    tz_input = timezone.strip()
    tz_key = _TZ_ALIASES.get(tz_input.lower(), tz_input)
    try:
        tz = ZoneInfo(tz_key)
    except ZoneInfoNotFoundError:
        return {"error": f"未知时区: {timezone}（请用 IANA 格式如 Asia/Shanghai）"}
    now = datetime.now(tz)
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
    return {
        "timezone": str(tz),
        "datetime": now.isoformat(timespec="seconds"),
        "weekday": weekday_cn,
        "unix": int(now.timestamp()),
    }


# === 单位换算（内置表，无外部依赖） ===
# 温度单独处理（非线性），其他类走"都先转基准单位"

_LENGTH_TO_METER = {
    "m": 1.0, "meter": 1.0, "米": 1.0,
    "km": 1000.0, "kilometer": 1000.0, "千米": 1000.0, "公里": 1000.0,
    "cm": 0.01, "centimeter": 0.01, "厘米": 0.01,
    "mm": 0.001, "millimeter": 0.001, "毫米": 0.001,
    "mi": 1609.344, "mile": 1609.344, "英里": 1609.344,
    "ft": 0.3048, "feet": 0.3048, "英尺": 0.3048,
    "in": 0.0254, "inch": 0.0254, "英寸": 0.0254,
    "yd": 0.9144, "yard": 0.9144, "码": 0.9144,
}

_WEIGHT_TO_GRAM = {
    "g": 1.0, "gram": 1.0, "克": 1.0,
    "kg": 1000.0, "kilogram": 1000.0, "千克": 1000.0, "公斤": 1000.0,
    "mg": 0.001, "毫克": 0.001,
    "lb": 453.592, "pound": 453.592, "磅": 453.592,
    "oz": 28.3495, "ounce": 28.3495, "盎司": 28.3495,
    "ton": 1_000_000.0, "吨": 1_000_000.0,
}


def _convert_temp(value: float, src: str, dst: str) -> float:
    src, dst = src.lower(), dst.lower()
    # 先转摄氏
    if src in ("c", "celsius", "摄氏度", "℃"):
        celsius = value
    elif src in ("f", "fahrenheit", "华氏度", "℉"):
        celsius = (value - 32) * 5 / 9
    elif src in ("k", "kelvin", "开尔文"):
        celsius = value - 273.15
    else:
        raise ValueError(f"unknown temperature unit: {src}")
    # 再从摄氏转目标
    if dst in ("c", "celsius", "摄氏度", "℃"):
        return celsius
    if dst in ("f", "fahrenheit", "华氏度", "℉"):
        return celsius * 9 / 5 + 32
    if dst in ("k", "kelvin", "开尔文"):
        return celsius + 273.15
    raise ValueError(f"unknown temperature unit: {dst}")


@mcp.tool()
def unit_convert(value: float, from_unit: str, to_unit: str) -> dict[str, Any]:
    """单位换算：温度 (C/F/K) / 长度 (m/km/mi/ft/in/cm/mm/yd) / 重量 (g/kg/lb/oz/ton)。

    Args:
        value: 数值
        from_unit: 源单位，支持中英文和符号（℃ / 摄氏度 / celsius / c）
        to_unit: 目标单位

    Returns:
        {value, from_unit, to_unit, result, category} 或 {error}
    """
    logger.info("unit_convert: %s %s → %s", value, from_unit, to_unit)
    fu, tu = from_unit.strip().lower(), to_unit.strip().lower()
    try:
        # 温度
        temp_units = {"c", "celsius", "摄氏度", "℃", "f", "fahrenheit", "华氏度", "℉", "k", "kelvin", "开尔文"}
        if fu in temp_units and tu in temp_units:
            result = _convert_temp(value, fu, tu)
            return {"value": value, "from_unit": from_unit, "to_unit": to_unit,
                    "result": round(result, 4), "category": "temperature"}
        # 长度
        if fu in _LENGTH_TO_METER and tu in _LENGTH_TO_METER:
            meters = value * _LENGTH_TO_METER[fu]
            result = meters / _LENGTH_TO_METER[tu]
            return {"value": value, "from_unit": from_unit, "to_unit": to_unit,
                    "result": round(result, 6), "category": "length"}
        # 重量
        if fu in _WEIGHT_TO_GRAM and tu in _WEIGHT_TO_GRAM:
            grams = value * _WEIGHT_TO_GRAM[fu]
            result = grams / _WEIGHT_TO_GRAM[tu]
            return {"value": value, "from_unit": from_unit, "to_unit": to_unit,
                    "result": round(result, 6), "category": "weight"}
        return {"error": f"不支持的单位组合: {from_unit} → {to_unit}（或跨类别换算）"}
    except ValueError as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
