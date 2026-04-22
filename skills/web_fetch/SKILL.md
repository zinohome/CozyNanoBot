---
name: web_fetch
description: Fetch a URL and extract its main text content. Use when the user provides a specific URL and asks you to read/summarize it, or after `search` finds a link worth reading in full.
always: true
---

# Web Fetch

Call `mcp_web_fetch_web_fetch(url, max_chars=4000)` to pull and extract text from a URL.

## When to Call

- **用户给了明确 URL**: "帮我读下 https://...", "总结这个页面"
- **search 找到某条值得详读**: 先 `search(query)` → 挑 URL → `web_fetch(url)`
- **需要页面具体内容**（不止摘要）

## Do NOT Call

- **用户只给了关键词，没 URL**: 用 search，不要自己编 URL
- **URL 明显是文件下载**（.pdf / .zip / .exe）: 工具只吃 HTML/文本
- **用户在问常识**: "什么是素数" 不需要抓网页

## Parameters

- `url`: 必须 `http://` 或 `https://` 开头。工具会自动跟随 3xx 重定向
- `max_chars`: 截断上限，默认 4000，上限 10000
  - 长文章用 `max_chars=8000` 或更多
  - 只要摘要用默认即可

## Tool Output Schema

```
{url (最终 URL), title (页面 <title>), content (正文),
 truncated (bool), bytes (原始字节数)}
```
失败: `{url, error}` — 常见是 404 / 超时 / 非 HTML。

## Response Style

抓到后**总结 + 引用**（不要原样复述 4000 字）：

> **页面**: [GitHub - tiangolo/fastapi](https://github.com/tiangolo/fastapi)
>
> **摘要**: FastAPI 是一个现代化、快速的 Python Web 框架... 本次 release 主要修复了 ...

## 与 search 的配合

- `search(query)` → 拿 3-5 条摘要
- 用户觉得某条有用 → `web_fetch(url)` 读全文
- 直接给用户 URL 让他们自己看也可，不一定每次都抓
