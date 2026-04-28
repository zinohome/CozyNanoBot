---
name: unit_convert
description: Supported units + response formatting for unit_convert.
always: true
---

# Unit Convert Response Formatting

This file covers **支持的单位 + 响应风格**。

## Supported Units

| 类别 | 单位 |
|---|---|
| 温度 | C/Celsius/摄氏度/℃, F/Fahrenheit/华氏度/℉, K/Kelvin/开尔文 |
| 长度 | 公制 m/km/cm/mm + 英制 mi/ft/in/yd + 中文"米/千米/公里/厘米/毫米/英里/英尺/英寸" |
| 重量 | g/kg/mg/ton + lb/oz + 中文"克/千克/公斤/毫克/吨/磅/盎司" |

**跨类别**（如米换公斤）工具会返回 error —— 告诉用户不能换。

## Tool Output Schema

```
{value, from_unit, to_unit, result, category}
```
失败: `{error}`

## Response Style

```
23°C ≈ 73.4°F
5 英里 ≈ 8.05 公里
200 磅 ≈ 90.72 公斤
```

用 ≈ 表示换算结果，保留合理小数位（温度 1 位，长度/重量 2-4 位）。
