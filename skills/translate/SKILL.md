---
name: translate
description: Response formatting for the translate tool (Tencent TMT).
always: true
---

# Translate Response Formatting

Fire-rate rules are in `TOOLS.md` and the tool's own description — this file only covers **response formatting**.

## Trigger Examples (冗余提醒)

- "翻译 'hello world' 到中文" → **必调**
- "把这句话翻译成日文" / "译成法语" → **必调**
- "translate 你好 to English" → **必调**
- 用户只是在句子里掺英文而没说"翻译"，**不调**

## Tool Output Schema

```
success: {source_lang, target_lang, source_text, translated_text, source: "tencent_tmt"}
failure: {error}  ← 直接转述给用户
```

## Response Style

**简短直出结果**，不要加"希望对你有帮助"这类套话。

> "Hello world" 的中文翻译：**你好世界**。

> 日文：**愛してる**。

批量翻译时逐行对照：

> - "good morning" → "早安"
> - "thank you" → "谢谢"

如果 error 是 `TENCENT_SECRET_ID/KEY not configured`，告诉用户"翻译服务未配置密钥"。
