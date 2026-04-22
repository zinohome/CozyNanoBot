---
name: unit_convert
description: Convert between units of temperature (C/F/K), length (m/km/mi/ft/in), or weight (g/kg/lb/oz). Use for precise unit conversions the user can't do in their head.
always: true
---

# Unit Convert

Call `mcp_info_tools_unit_convert(value, from_unit, to_unit)` for unit conversion.

## When to Call

- 温度: "23 摄氏度换华氏度", "100°F 是多少摄氏度", "body temperature 37C in F"
- 长度: "5 英里是多少公里", "6 英尺等于多少厘米", "一米等于几英寸"
- 重量: "200 磅是多少公斤", "1 kg 几磅"

## Do NOT Call

- **同单位**: "5 米等于多少米" — 显然不用调
- **跨类别**: "5 米等于多少公斤" — 工具返回错误，先告诉用户不能换
- **名词常识**: "一打等于几" = 12（直接答）, "一公顷是多少平方米" = 10000（直接答）
- **数学表达式**: 用 calculator 算公式

## Supported Units

| 类别 | 支持 |
|---|---|
| 温度 | C/Celsius/摄氏度/℃, F/Fahrenheit/华氏度/℉, K/Kelvin/开尔文 |
| 长度 | m/km/cm/mm (公制) + mi/ft/in/yd (英制) + 中文"米/千米/公里/厘米/毫米/英里/英尺/英寸" |
| 重量 | g/kg/mg/ton + lb/oz + 中文"克/千克/公斤/毫克/吨/磅/盎司" |

## Tool Output Schema

```
{value, from_unit, to_unit, result (number), category}
```
失败: `{error}` — 解释并让用户换表达。

## Response Style

> 23°C ≈ 73.4°F
> 5 英里 ≈ 8.05 公里
