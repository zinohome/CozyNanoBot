---
name: current_time
description: Get current datetime in a specific timezone. Use when user asks for the current time, date, day of week, or "is it morning/night" in a location.
always: true
---

# Current Time

Call `mcp_info_tools_current_time(timezone)` to get wall-clock time.

## When to Call

- "现在几点" / "今天几号" / "今天星期几"
- "Tokyo 现在几点" / "纽约现在是白天还是晚上"
- 时区换算前置：算"北京 10 点对应洛杉矶几点"先取两地 current_time

## Do NOT Call

- **过去 / 未来**: "昨天几号" / "下周一是几号" — 从用户上下文推算或用 calculator
- **持续时间**: "我等了多久" — 不是当前时间
- **相对时间**: "几分钟前" — 根据上下文推理

## Timezone Input

首选 IANA 标准名：`Asia/Shanghai`, `America/New_York`, `Europe/London`, `UTC`

支持别名（工具内部映射）：
`beijing`, `shanghai`, `tokyo`, `nyc`, `la`, `london`, `paris`, `utc` 等。
中文 "北京" / "上海" 也支持。

**不确定时默认 `Asia/Shanghai`**（用户主要在中国）。

## Tool Output Schema

```
{timezone, datetime (ISO 8601 含时区偏移),
 weekday (中文 "周三"), unix (timestamp)}
```

## Response Style

> 现在是 2026 年 4 月 22 日 14:30（周三，Asia/Shanghai）。
