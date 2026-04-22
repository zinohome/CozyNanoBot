---
name: news
description: Response formatting for the news tool (RSS aggregation).
always: true
---

# News Response Formatting

Fire-rate rules are in `TOOLS.md` and the tool's own description — this file only covers **response formatting**.

## Trigger Examples (冗余提醒)

- "有什么新闻" / "最新头条" / "最近热点" → **必调**
- "最近发生了什么大事" → **必调**
- "科技圈最近有啥" → 调 `news(category="tech")`
- "AI 最新消息" → 调 `news(query="AI")`
- 不调：历史事件 / 某条具体新闻的评论（那是闲聊）

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
