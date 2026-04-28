---
name: news
description: Response formatting for the news tool (RSS aggregation).
always: true
---

# News Response Formatting

This file covers **response formatting** guidance.

## Tool Output Schema

```
success: {results: [{title, url, published, source, summary}, ...]}
空: {results: [], note: "..."}
failure: {error}
```

## Response Style

列表形式，每条一行，**带源 + 链接**：

> 最新几条新闻：
> 1. **AI 新芯片发布** — BBC Tech · 2026-04-22
>    摘要片段（两三句话概括）
>    https://example.com/xxx
> 2. ...

不要 dump 原始 summary HTML 残留；如果 summary 很长，保留 1-2 句。

没有结果时直接告诉用户："暂时没有抓到相关新闻，换个关键词或稍后再试。"
