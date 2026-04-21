"""MCP server 共用工具函数。"""

from __future__ import annotations

import logging
import sys


def setup_logging(server_name: str) -> logging.Logger:
    """MCP server 日志必须写 stderr，stdout 是 MCP 协议通道。"""
    logger = logging.getLogger(f"cozy_mcp.{server_name}")
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(f"[{server_name}] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
