"""Calculator MCP server — AST 白名单，绝不运行任意代码。"""

from __future__ import annotations

import ast
import operator
from typing import Any

from mcp.server.fastmcp import FastMCP

from cozy_mcp_tools._common import setup_logging

logger = setup_logging("calculator")
mcp = FastMCP("cozy-calculator")


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def _compute_expr(expr: str) -> float | int:
    tree = ast.parse(expr, mode="eval")

    def _visit(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return _visit(node.body)
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError("only numeric constants allowed")
            return node.value
        if isinstance(node, ast.BinOp):
            fn = _BIN_OPS.get(type(node.op))
            if fn is None:
                raise ValueError(f"binary op not allowed: {type(node.op).__name__}")
            return fn(_visit(node.left), _visit(node.right))
        if isinstance(node, ast.UnaryOp):
            fn = _UNARY_OPS.get(type(node.op))
            if fn is None:
                raise ValueError(f"unary op not allowed: {type(node.op).__name__}")
            return fn(_visit(node.operand))
        raise ValueError(f"node not allowed: {type(node).__name__}")

    return _visit(tree)


@mcp.tool()
def calculator(expression: str) -> dict[str, Any]:
    """计算算术表达式（支持 + - * / // % ** 和括号）。绝不执行任意代码。

    Args:
        expression: 纯算术表达式，例如 "(2+3)*4"

    Returns:
        {"expression": ..., "result": ...} 或 {"expression": ..., "error": ...}
    """
    logger.info("calculator: %s", expression)
    try:
        return {"expression": expression, "result": _compute_expr(expression)}
    except (ValueError, SyntaxError, ZeroDivisionError) as e:
        return {"expression": expression, "error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
