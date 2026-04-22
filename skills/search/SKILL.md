---
name: search
description: Web search via DuckDuckGo. Use for recent facts, news, version numbers, release dates, or anything that changed after the model's knowledge cutoff.
always: true
---

# Web Search

Call `mcp_search_search(query, top_k=5)` for web search.

## When to Call

- **Recency-sensitive** queries: "FastAPI 最新版本", "Python 3.13 新特性", "昨天发生了什么"
- **Facts likely after knowledge cutoff**: "X 公司最近动态", "某产品新功能"
- **Specific version / date lookups**: 发布日期、更新日志、新特性

## Do NOT Call

- **Stable encyclopedic knowledge**: "什么是素数", "黄金分割比例", "孔子哪年出生" — 从训练知识答
- **Personal opinions or interpretation**: "你觉得 X 怎么样", "推荐一本书" — 根据对话回答
- **Math / calculation**: 用 calculator
- **Weather / time**: 用对应工具
- **URL fetching** (用户给了具体 URL): 用 web_fetch 而非 search

## Query Construction Tips

- 用关键词，不用自然语句: ❌ "请帮我搜一下关于 Python 3.13 的新特性"  ✅ "Python 3.13 new features"
- 中英文皆可；英文结果更丰富
- 必要时加时间限定词: "2026 AI news" > "AI news"

## Tool Output Schema

```
{query, results: [{title, url, snippet}, ...]}
```

失败: `{query, error}` — 告诉用户并建议稍后重试。

## Response Style

引用时带源（URL），避免用户觉得是你编的：

> 根据搜索结果：
> - FastAPI 最新版本是 0.110.0（2024-03 发布）— https://github.com/tiangolo/fastapi/releases
> - 主要变化：...

## 与 web_fetch 的配合

`search` 只给摘要。用户想看"全文"时，用 search 找 URL → 再 `web_fetch(url)` 抓正文。
