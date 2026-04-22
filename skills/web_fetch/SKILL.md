---
name: web_fetch
description: max_chars 选择 + 响应风格 for web_fetch.
always: true
---

# Web Fetch Response Formatting

Fire-rate rules are in `TOOLS.md` — this file covers **参数选择 + 响应风格**。

## Parameter: max_chars

- 默认 4000，够日常摘要
- 长文章（技术 blog / paper）用 `max_chars=8000`
- 上限 10000（工具内部 clamp）

## Tool Output Schema

```
{url (最终 URL after redirect), title (页面 <title>),
 content (正文), truncated (bool), bytes (原始字节数)}
```
失败: `{url, error}` —— 常见为 404 / 超时 / 非 HTML。

## Response Style

**抓到后总结 + 引用**（不要原样复述 4000 字正文）：

> **页面**: [GitHub - tiangolo/fastapi](https://github.com/tiangolo/fastapi)
>
> **摘要**: FastAPI 是一个现代化、快速的 Python Web 框架。
> 本次 release 主要修复了 ...

## 与 search 配合

- `search(query)` → 拿 3-5 条摘要
- 用户觉得某条有用 → `web_fetch(url)` 读全文
- 若仅需链接点击，直接给 URL 即可，不必每次都抓
