"""weather 和 search 工具被调用时产生 start + end 两条 JSON 日志。"""
from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stderr
from unittest.mock import MagicMock, patch


def _extract_json_events(stderr_text: str) -> list[dict]:
    events = []
    for line in stderr_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def test_weather_tool_logs_start_and_end() -> None:
    """调用 weather 工具时，stderr 应产出 tool='weather' 的 start+end 两条 JSON。"""
    from cozy_mcp_tools.weather import __main__ as weather_main

    fake_resp = MagicMock()
    fake_resp.raise_for_status = MagicMock()
    fake_resp.json.return_value = {
        "current_condition": [
            {
                "temp_C": "22",
                "weatherDesc": [{"value": "Clear"}],
                "humidity": "55",
                "windspeedKmph": "10",
                "winddir16Point": "N",
                "FeelsLikeC": "21",
            }
        ]
    }

    buf = io.StringIO()
    with redirect_stderr(buf):
        with patch.object(weather_main.httpx, "get", return_value=fake_resp):
            result = weather_main.weather("上海")

    assert result["temperature"] == 22
    events = _extract_json_events(buf.getvalue())
    weather_events = [e for e in events if e.get("tool") == "weather"]
    actions = [e.get("action") for e in weather_events]
    assert "start" in actions, f"no start event; got: {actions}"
    assert "end" in actions, f"no end event; got: {actions}"
    end_event = next(e for e in weather_events if e["action"] == "end")
    assert end_event.get("duration_ms") is not None
    assert end_event.get("status") == "ok"


def test_weather_tool_logs_error_status_on_exception() -> None:
    """weather 内部异常被捕获成结构化 error dict；end 日志仍应写出。"""
    from cozy_mcp_tools.weather import __main__ as weather_main

    buf = io.StringIO()
    with redirect_stderr(buf):
        with patch.object(weather_main.httpx, "get", side_effect=RuntimeError("boom")):
            result = weather_main.weather("Nowhere")

    assert "error" in result
    events = _extract_json_events(buf.getvalue())
    weather_events = [e for e in events if e.get("tool") == "weather"]
    actions = [e.get("action") for e in weather_events]
    assert "start" in actions
    assert "end" in actions
    end_event = next(e for e in weather_events if e["action"] == "end")
    assert end_event.get("status") == "error"


def test_search_tool_logs_start_and_end() -> None:
    from cozy_mcp_tools.search import __main__ as search_main

    fake_resp = MagicMock()
    fake_resp.raise_for_status = MagicMock()
    fake_resp.text = (
        '<html><body>'
        '<div class="result">'
        '<a class="result__a" href="https://example.com/python">Python tutorial</a>'
        '<a class="result__snippet">Learn python basics</a>'
        '</div>'
        '</body></html>'
    )

    buf = io.StringIO()
    with redirect_stderr(buf):
        with patch.object(search_main.httpx, "post", return_value=fake_resp):
            result = search_main.search("python")

    assert "results" in result
    events = _extract_json_events(buf.getvalue())
    search_events = [e for e in events if e.get("tool") == "search"]
    actions = [e.get("action") for e in search_events]
    assert "start" in actions, f"no start event; got: {actions}"
    assert "end" in actions, f"no end event; got: {actions}"
    end_event = next(e for e in search_events if e["action"] == "end")
    assert end_event.get("duration_ms") is not None
    assert end_event.get("status") == "ok"
