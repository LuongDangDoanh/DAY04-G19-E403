from __future__ import annotations

import ast
import operator
from typing import Any

from tools._shared import err

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.BinOp):
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        op = _ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(left, right)
    if isinstance(node, ast.UnaryOp):
        op = _ALLOWED_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op(_evaluate(node.operand))
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    raise ValueError(f"Unsupported expression: {type(node).__name__}")


def calculate(expression: str = "") -> dict[str, Any]:
    try:
        if not expression:
            raise ValueError("Missing expression")
        parsed = ast.parse(expression, mode="eval")
        result = _evaluate(parsed.body)
        return {"tool": "calculator", "expression": expression, "result": result}
    except Exception as exc:
        return err("calculator", exc)
