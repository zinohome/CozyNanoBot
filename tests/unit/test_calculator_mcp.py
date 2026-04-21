from __future__ import annotations

import pytest

from cozy_mcp_tools.calculator.__main__ import _compute_expr, calculator


def test_compute_basic() -> None:
    assert _compute_expr("1+2") == 3
    assert _compute_expr("(1+2)*3") == 9
    assert _compute_expr("10/4") == 2.5
    assert _compute_expr("2**8") == 256
    assert _compute_expr("-5+3") == -2


def test_rejects_name() -> None:
    with pytest.raises(ValueError):
        _compute_expr("x+1")


def test_rejects_call() -> None:
    with pytest.raises(ValueError):
        _compute_expr("print(1)")


def test_tool_happy() -> None:
    r = calculator("(2+3)*4")
    assert r["result"] == 20


def test_tool_bad() -> None:
    assert "error" in calculator("foo()")
