# Tool Usage Notes

Tool signatures are provided automatically via function calling.
This file documents non-obvious constraints and usage patterns.

---

## External Cozy Tools（外部工具，通过 MCP 注册，function calling schema 会自动注入）

### Fire-rate Bias（关键）

**默认倾向：遇到能用工具就用，不要从训练知识里瞎答。**

尤其这几类查询**永远要 fire 对应工具**：

| 用户说 | 必须调用 | 不要 |
|---|---|---|
| "几点 / 几号 / 星期几" | `current_time` | 从对话上下文猜日期 |
| "X 城市 冷/热/下雨/温度/穿什么" | `weather` | 闲聊或假设 |
| "X 换算成 Y 单位" | `unit_convert` | 心算 |
| "搜 / 最新 / 新特性 / 新闻" | `search` | 用可能过时的训练知识 |
| 用户给了 `http(s)://` 链接 | `web_fetch` | 凭链接名猜内容 |

### 各工具触发细则

#### `weather` — 即使间接询问也要 fire

- 直接：`"查上海天气"`, `"北京温度"`
- 间接：`"上海冷吗"`, `"魔都冷吗"`, `"广州适合穿什么"`, `"东京现在下雨吗"`
- 中文俗语映射（先映射再调用）：
  - 魔都→上海、帝都/京城→北京、羊城/花城→广州
  - 山城→重庆、蓉城→成都、泉城→济南、鹭岛→厦门
- 繁体（Whisper 常产繁体）：直接用（city 繁简一致）

不调用的场景仅：过去天气、预报、假设、比喻（"心情的天气"）、无城市线索。

#### `current_time` — 你对日期时间永远是不知道的

即使 USER.md 写了 timezone，你也**不知道现在几号几点**。不要猜。
"几点/几号/星期几/今天是/现在时间" 全部 fire。

#### `unit_convert` — 精确换算

用户问"23°C 几华氏度" / "5 英里几公里" / "200 磅几公斤" 一律 fire。
显然同类同单位（"5 米等于多少米"）不调。

#### `search` — 时效性查询或超出训练知识

"最新/新特性/新闻/某产品更新" 一律 fire。稳定百科知识（素数、历史）不调。

#### `web_fetch` — 用户给了 URL

用户提供 `http://` 或 `https://` → 基本就是让你读，fire。

---

## Built-in Nanobot Tools

### exec — Safety Limits

- Commands have a configurable timeout (default 60s)
- Dangerous commands are blocked (rm -rf, format, dd, shutdown, etc.)
- Output is truncated at 10,000 characters
- `restrictToWorkspace` config can limit file access to the workspace

### glob — File Discovery

- Use `glob` to find files by pattern before falling back to shell commands
- Simple patterns like `*.py` match recursively by filename
- Prefer this over `exec` when you only need file paths

### grep — Content Search

- Use `grep` to search file contents inside the workspace
- Default behavior returns only matching file paths

### cron — Scheduled Reminders

- Please refer to cron skill for usage.
