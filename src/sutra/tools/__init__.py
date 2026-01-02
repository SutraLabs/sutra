"""Tool registry for Sutra."""
from __future__ import annotations

from typing import Callable, Dict

from .pdf import extract_text
from .rag import index_folder, query
from .text import chunk_text

TOOL_REGISTRY: Dict[str, Callable[..., dict]] = {
    "pdf.extract_text": extract_text,
    "text.chunk": chunk_text,
    "rag.index_folder": index_folder,
    "rag.query": query,
}

__all__ = ["TOOL_REGISTRY", "extract_text", "chunk_text", "index_folder", "query"]
