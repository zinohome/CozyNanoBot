---
name: current_time
description: Timezone input conventions + response formatting for current_time.
always: true
---

# Current Time Response Formatting

This file covers **时区输入 + 响应风格**。

## Timezone Input

首选 IANA 标准名：`Asia/Shanghai`, `America/New_York`, `Europe/London`, `UTC`

支持别名（工具内部映射）：
`beijing`, `shanghai`, `tokyo`, `nyc`, `la`, `london`, `paris`, `utc`
中文 "北京" / "上海" 也支持。

**用户没指定时默认 `Asia/Shanghai`**（USER.md 已写明）。

## Tool Output Schema

```
{timezone, datetime (ISO 8601 含时区偏移),
 weekday (中文 "周三"), unix (timestamp)}
```

## Response Style

> 现在是 2026 年 4 月 22 日 14:30（周三，Asia/Shanghai）。

对 "今天星期几" 类简短问题，可更精简：

> 今天是周三。
