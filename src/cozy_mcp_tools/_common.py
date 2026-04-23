"""MCP server 共用工具函数。"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


def setup_logging(server_name: str) -> logging.Logger:
    """MCP server 日志必须写 stderr，stdout 是 MCP 协议通道。"""
    logger = logging.getLogger(f"cozy_mcp.{server_name}")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(f"[{server_name}] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def emit_log(
    tool: str,
    action: str,
    duration_ms: float | None = None,
    status: str = "ok",
    error: str | None = None,
    session_id: str | None = None,
    request_id: str | None = None,
    **extra,
) -> None:
    """Emit one JSON log line to stderr (for container log collectors).

    Fields:
        tool: MCP tool name (e.g. "weather")
        action: "start" / "end" / "error" etc.
        duration_ms: optional float, only set for action="end"
        status: "ok" / "error"
        error: optional error message string
        session_id / request_id: optional trace IDs (for cross-service correlation)
        **extra: any additional key-value pairs merged into the output
    """
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "action": action,
        "duration_ms": duration_ms,
        "status": status,
        "error": error,
        "session_id": session_id,
        "request_id": request_id,
    }
    payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr, flush=True)
