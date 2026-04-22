---
name: weather
description: Response formatting guide for weather tool results.
always: true
---

# Weather Response Formatting

Fire-rate rules are in `TOOLS.md` and the tool's own description — this file only covers **response formatting**.

## Trigger Examples (冗余提醒)

- "查上海天气" / "北京温度" / "Tokyo weather" → **必调**
- "上海冷吗" / "魔都冷吗" / "广州适合穿什么" → **必调**（间接询问也要 fire）
- 俗语映射后再调：魔都=上海、帝都=北京、花城=广州、山城=重庆

## Tool Output Schema

```
success: {city, temperature (°C int), condition (中文), humidity (% int),
          wind (如 "10 km/h NW"), feels_like (°C int), source: "wttr.in"}
failure: {city, error}  ← 直接把 error 转述给用户
```

## Response Style

自然、简洁、**不要 dump JSON**：

> 上海现在 22°C，天气晴，湿度 65%，西北风 10 km/h，体感 20°C。

不要：

```
❌ weather 工具返回: {"city": "上海", "temperature": 22, ...}
```

多城对比类问题（"北京和上海哪个更冷"）调两次后直接对比：

> 北京 18°C，上海 22°C —— 上海更暖一些。
