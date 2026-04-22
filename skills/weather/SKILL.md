---
name: weather
description: Query real-time weather for a city via wttr.in. Use when user asks about temperature, conditions, humidity, wind, or whether it's hot/cold/raining in a specific location.
always: true
---

# Weather Query

Call `mcp_weather_weather(city)` for current weather.

## When to Call

- Direct: "查上海天气", "北京温度多少", "Tokyo weather"
- Condition questions with a location: "上海冷吗", "广州下雨吗", "东京适合穿什么"
- Indirect: "出门要带伞吗" — if user has context about location, call; else ask for city

## City Name Aliases（必须先映射再调用）

| 俗称 | 传入 tool 的 city |
|---|---|
| 魔都 | 上海 |
| 帝都 / 京城 | 北京 |
| 羊城 / 花城 | 广州 |
| 山城 | 重庆 |
| 蓉城 | 成都 |
| 泉城 | 济南 |
| 鹭岛 | 厦门 |

传统中文（"天氣"）直接用，city 名繁简结果一致。

## Do NOT Call

- **Past weather**: "上周上海多少度" / "去年冬天冷不冷" — tool 只返回当前
- **Forecast**: "明天会下雨吗" / "未来一周天气" — tool 不支持预报
- **Hypothetical**: "如果明天下雨怎么办" — 不是事实查询
- **Metaphorical**: "心情的天气" / "爱情的温度"
- **No location**: "冷吗", "下雨吗" — 反问用户 "哪个城市？" 而不是猜

## Tool Output Schema

```
{city, temperature (°C int), condition (中文), humidity (% int),
 wind (如 "10 km/h NW"), feels_like (°C int), source: "wttr.in"}
```

失败时 `{city, error}`，直接把 error 字段复述给用户。

## Response Style

> 上海现在 22°C，天气晴，湿度 65%，西北风 10 km/h，体感 20°C。
