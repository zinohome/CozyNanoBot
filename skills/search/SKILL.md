---
name: search
description: Response formatting + query construction for DuckDuckGo search.
always: true
---

# Search Response Formatting & Query Tips

Fire-rate rules are in `TOOLS.md` — this file covers **query 构造 + 结果呈现**。

## Query Construction

- 用关键词，不要自然语句
  - ❌ "请帮我搜一下关于 Python 3.13 的新特性"
  - ✅ "Python 3.13 new features"
- 中英文皆可；英文结果更丰富
- 时间敏感问题加年份：`"2026 AI news"` > `"AI news"`

## Tool Output Schema

```
{query, results: [{title, url, snippet}, ...]}
```
失败: `{query, error}` — 告诉用户并建议重试。

## Response Style

**引用时带源**，避免用户以为是你编的：

> 根据搜索结果，FastAPI 最新版本是 **0.110.0**（2024-03 发布）：
> - 主要变化：...
> - 参考：https://github.com/tiangolo/fastapi/releases

## 与 web_fetch 配合

`search` 只给摘要。用户想看"全文"时，用 search 找 URL → 再 `web_fetch(url)` 抓正文。
