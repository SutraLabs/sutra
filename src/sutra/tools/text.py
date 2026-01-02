"""Text utilities for Sutra tools."""
from __future__ import annotations

import time
from typing import List, Optional, Sequence, TypedDict

TOOL_NAME = "text.chunk"
TOOL_VERSION = "1.0.0"


class ChunkDict(TypedDict):
    chunk_id: int
    text: str
    start: int
    end: int


class ChunkData(TypedDict):
    chunks: List[ChunkDict]
    num_chunks: int


class ToolMeta(TypedDict):
    tool: str
    version: str
    elapsed_ms: int


class ToolError(TypedDict, total=False):
    type: str
    message: str
    details: dict | None
    raw: str | None


class ToolEnvelope(TypedDict):
    ok: bool
    data: ChunkData | None
    error: ToolError | None
    meta: ToolMeta


def _meta(start: float) -> ToolMeta:
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "elapsed_ms": int((time.perf_counter() - start) * 1000),
    }


def _error(start: float, err_type: str, message: str, *, details: dict | None = None) -> ToolEnvelope:
    return {
        "ok": False,
        "data": None,
        "error": {
            "type": err_type,
            "message": message,
            "details": details,
            "raw": None,
        },
        "meta": _meta(start),
    }


def chunk_text(
    *,
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    separators: Optional[Sequence[str]] = None,
) -> ToolEnvelope:
    start_time = time.perf_counter()

    if not isinstance(text, str):
        return _error(start_time, "invalid_args", "text must be a string")
    if chunk_size <= 0:
        return _error(start_time, "invalid_args", "chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        return _error(start_time, "invalid_args", "chunk_overlap must be >=0 and < chunk_size")

    if separators is None:
        separators = ["\n\n", "\n", ". ", " "]

    chunks: List[ChunkDict] = []
    if not text:
        return {
            "ok": True,
            "data": {"chunks": [], "num_chunks": 0},
            "error": None,
            "meta": _meta(start_time),
        }

    pos = 0
    chunk_id = 0
    length = len(text)
    while pos < length:
        end = min(length, pos + chunk_size)
        chunk_text = text[pos:end]

        # try to break at separator
        if end < length:
            for sep in separators:
                idx = chunk_text.rfind(sep)
                if idx != -1 and idx > len(sep):
                    end = pos + idx + len(sep)
                    chunk_text = text[pos:end]
                    break

        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": chunk_text,
                "start": pos,
                "end": end,
            }
        )
        chunk_id += 1
        if end == length:
            break
        pos = max(0, end - chunk_overlap)

    return {
        "ok": True,
        "data": {"chunks": chunks, "num_chunks": len(chunks)},
        "error": None,
        "meta": _meta(start_time),
    }
