"""Tool executor for Sutra tool registry."""
from __future__ import annotations

import time
from typing import Any, Dict

from . import TOOL_REGISTRY


def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a registered tool by name."""
    start = time.perf_counter()

    if name not in TOOL_REGISTRY:
        return {
            "ok": False,
            "data": None,
            "error": {
                "type": "unknown_tool",
                "message": f"Tool '{name}' is not registered",
                "details": None,
                "raw": None,
            },
            "meta": {
                "tool": name,
                "version": "unknown",
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
            },
        }

    if not isinstance(args, dict):
        return {
            "ok": False,
            "data": None,
            "error": {
                "type": "invalid_arguments",
                "message": "Tool arguments must be provided as a dict",
                "details": {"received_type": type(args).__name__},
                "raw": None,
            },
            "meta": {
                "tool": name,
                "version": "unknown",
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
            },
        }

    func = TOOL_REGISTRY[name]
    try:
        return func(**args)
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "ok": False,
            "data": None,
            "error": {
                "type": "tool_execution_error",
                "message": f"Tool '{name}' raised an exception",
                "details": None,
                "raw": str(exc),
            },
            "meta": {
                "tool": name,
                "version": "unknown",
                "elapsed_ms": int((time.perf_counter() - start) * 1000),
            },
        }
