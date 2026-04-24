"""Unit-level assertion that patch 0002 wires allowed_tools through the runner.

Skips if patches are not yet applied (e.g. fresh clone before
`scripts/apply_patches.sh` ran).
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
UPSTREAM = ROOT / "upstream" / "nanobot"

# Ensure upstream nanobot is importable; the integration harness already runs
# `apply_patches.sh`, but unit tests should not depend on that — we just skip
# if the patched field does not exist.
if str(UPSTREAM) not in sys.path:
    sys.path.insert(0, str(UPSTREAM))


def _patches_applied() -> bool:
    try:
        from nanobot.agent.runner import AgentRunSpec  # type: ignore
    except Exception:
        return False
    return "allowed_tools" in getattr(AgentRunSpec, "__dataclass_fields__", {})


@pytest.mark.skipif(not _patches_applied(), reason="patch 0002 not applied")
def test_run_tool_short_circuits_non_whitelisted() -> None:
    """_run_tool must return a permission_denied string without invoking tools."""
    from nanobot.agent.runner import AgentRunner, AgentRunSpec  # type: ignore
    from nanobot.providers.base import ToolCallRequest  # type: ignore

    class _BoomRegistry:
        """If the runner actually dispatches, this blows up — proving the guard fired."""

        async def execute(self, *_a, **_kw):
            raise AssertionError("tool registry must not be reached for denied tools")

        def prepare_call(self, *_a, **_kw):
            return None, {}, None

    spec = AgentRunSpec(
        initial_messages=[],
        tools=_BoomRegistry(),  # type: ignore[arg-type]
        model="noop",
        max_iterations=1,
        max_tool_result_chars=1000,
        allowed_tools=["calculator"],
    )
    runner = AgentRunner(provider=object())  # type: ignore[arg-type]
    tool_call = ToolCallRequest(id="tc1", name="web_search", arguments={"q": "x"})

    result, event, err = asyncio.run(runner._run_tool(spec, tool_call, {}))

    assert err is None
    assert event["status"] == "denied"
    assert event["name"] == "web_search"
    assert isinstance(result, str)
    assert "permission_denied" in result
    assert "calculator" in result  # the allowed set is echoed back


@pytest.mark.skipif(not _patches_applied(), reason="patch 0002 not applied")
def test_run_tool_allows_whitelisted() -> None:
    """When tool_call.name IS in allowed_tools, the guard must not fire."""
    from nanobot.agent.runner import AgentRunner, AgentRunSpec  # type: ignore
    from nanobot.providers.base import ToolCallRequest  # type: ignore

    class _OkRegistry:
        async def execute(self, name, params):
            return f"ran:{name}"

        def prepare_call(self, *_a, **_kw):
            return None, {}, None

    spec = AgentRunSpec(
        initial_messages=[],
        tools=_OkRegistry(),  # type: ignore[arg-type]
        model="noop",
        max_iterations=1,
        max_tool_result_chars=1000,
        allowed_tools=["calculator"],
    )
    runner = AgentRunner(provider=object())  # type: ignore[arg-type]
    tool_call = ToolCallRequest(id="tc2", name="calculator", arguments={})

    result, event, err = asyncio.run(runner._run_tool(spec, tool_call, {}))

    assert err is None
    assert event["status"] == "ok"
    assert result == "ran:calculator"


@pytest.mark.skipif(not _patches_applied(), reason="patch 0002 not applied")
def test_run_tool_none_allowlist_is_unrestricted() -> None:
    """allowed_tools=None must preserve legacy (unrestricted) behaviour."""
    from nanobot.agent.runner import AgentRunner, AgentRunSpec  # type: ignore
    from nanobot.providers.base import ToolCallRequest  # type: ignore

    class _OkRegistry:
        async def execute(self, name, params):
            return f"ran:{name}"

        def prepare_call(self, *_a, **_kw):
            return None, {}, None

    spec = AgentRunSpec(
        initial_messages=[],
        tools=_OkRegistry(),  # type: ignore[arg-type]
        model="noop",
        max_iterations=1,
        max_tool_result_chars=1000,
        allowed_tools=None,
    )
    runner = AgentRunner(provider=object())  # type: ignore[arg-type]
    tool_call = ToolCallRequest(id="tc3", name="web_search", arguments={})

    result, event, err = asyncio.run(runner._run_tool(spec, tool_call, {}))
    assert err is None
    assert event["status"] == "ok"
    assert result == "ran:web_search"
