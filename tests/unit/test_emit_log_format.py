"""emit_log 产生的 JSON 可 parse，字段齐全。"""
from __future__ import annotations

import io
import json
from contextlib import redirect_stderr

from cozy_mcp_tools._common import emit_log


def test_emit_log_produces_parseable_json():
    buf = io.StringIO()
    with redirect_stderr(buf):
        emit_log(tool="weather", action="start", session_id="s1", request_id="r1")
    line = buf.getvalue().strip()
    assert line, "emit_log produced no output"
    data = json.loads(line)
    assert data["tool"] == "weather"
    assert data["action"] == "start"
    assert data["session_id"] == "s1"
    assert data["request_id"] == "r1"
    assert "ts" in data
    # default status is "ok"
    assert data.get("status") == "ok"


def test_emit_log_with_duration_and_status():
    buf = io.StringIO()
    with redirect_stderr(buf):
        emit_log(tool="search", action="end", duration_ms=120.5, status="ok")
    data = json.loads(buf.getvalue().strip())
    assert data["duration_ms"] == 120.5
    assert data["status"] == "ok"
    assert data["tool"] == "search"


def test_emit_log_with_error():
    buf = io.StringIO()
    with redirect_stderr(buf):
        emit_log(tool="web_fetch", action="end", status="error", error="timeout")
    data = json.loads(buf.getvalue().strip())
    assert data["status"] == "error"
    assert data["error"] == "timeout"


def test_emit_log_extra_fields():
    """额外的 kwargs 应该被透传到 JSON。"""
    buf = io.StringIO()
    with redirect_stderr(buf):
        emit_log(tool="calculator", action="end", expression="1+2", result=3)
    data = json.loads(buf.getvalue().strip())
    assert data["expression"] == "1+2"
    assert data["result"] == 3


def test_emit_log_chinese_preserved():
    """中文内容不应被 ASCII escape。"""
    buf = io.StringIO()
    with redirect_stderr(buf):
        emit_log(tool="translate", action="end", text="你好")
    line = buf.getvalue().strip()
    # 直接 bytes 里应该含 '你好'
    assert "你好" in line
