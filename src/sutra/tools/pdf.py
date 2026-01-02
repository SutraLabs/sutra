"""PDF tool connector for Sutra."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict, Union

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - handled at runtime
    PdfReader = None  # type: ignore

TOOL_NAME = "pdf.extract_text"
TOOL_VERSION = "1.0.0"
DEFAULT_MAX_CHARS = 200_000


class ToolMeta(TypedDict):
    tool: str
    version: str
    elapsed_ms: int


class ToolError(TypedDict, total=False):
    type: str
    message: str
    details: Any
    raw: Optional[str]


class PdfMetadata(TypedDict, total=False):
    title: Optional[str]
    author: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    subject: Optional[str]
    keywords: Optional[str]


class PageChunk(TypedDict):
    page: int
    text: str
    text_len: int


class PdfData(TypedDict, total=False):
    path: str
    num_pages: int
    is_encrypted: bool
    metadata: PdfMetadata
    text: str
    text_len: int
    truncated: bool
    pages: Optional[List[PageChunk]]


class ToolEnvelope(TypedDict, total=False):
    ok: bool
    data: Optional[PdfData]
    error: Optional[ToolError]
    meta: ToolMeta


def _meta(start: float) -> ToolMeta:
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "elapsed_ms": int((time.perf_counter() - start) * 1000),
    }


def _error(start: float, err_type: str, message: str, *, details: Any = None, raw: Optional[str] = None) -> ToolEnvelope:
    return {
        "ok": False,
        "data": None,
        "error": {
            "type": err_type,
            "message": message,
            "details": details,
            "raw": raw,
        },
        "meta": _meta(start),
    }


def extract_text(
    *,
    path: Union[str, Path],
    max_pages: Optional[int] = None,
    per_page: bool = False,
    max_chars: Optional[int] = DEFAULT_MAX_CHARS,
    password: Optional[str] = None,
) -> ToolEnvelope:
    """Extract text and metadata from a PDF."""
    start = time.perf_counter()

    if PdfReader is None:
        return _error(start, "missing_dependency", "pypdf is required for pdf.extract_text", details="pip install 'sutra-ai[pdf]'")

    pdf_path = Path(path)
    if not pdf_path.exists() or not pdf_path.is_file():
        return _error(start, "file_not_found", f"File not found: {pdf_path}")

    if max_pages is not None and max_pages <= 0:
        return _error(start, "invalid_argument", "max_pages must be positive when provided", details={"max_pages": max_pages})
    if max_chars is not None and max_chars <= 0:
        return _error(start, "invalid_argument", "max_chars must be positive when provided", details={"max_chars": max_chars})

    try:
        reader = PdfReader(str(pdf_path))
    except Exception as exc:
        return _error(start, "pdf_read_error", "Unable to read PDF", raw=str(exc))

    if reader.is_encrypted:

        if not password:
            return _error(start, "encrypted_pdf", "PDF is encrypted and password was not provided")
        try:
            decrypt_result = reader.decrypt(password)
        except Exception as exc:
            return _error(start, "bad_password", "Unable to decrypt PDF with provided password", raw=str(exc))
        if decrypt_result == 0:
            return _error(start, "bad_password", "Incorrect password for encrypted PDF")

    total_pages = len(reader.pages)
    limit_pages = max_pages if max_pages is not None else total_pages

    collected: List[PageChunk] = []
    for idx, page in enumerate(reader.pages):
        if idx >= limit_pages:
            break
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            return _error(start, "page_extract_error", f"Failed to extract page {idx+1}", raw=str(exc))
        collected.append(
            {
                "page": idx + 1,
                "text": text,
                "text_len": len(text),
            }
        )

    if not collected or all(chunk["text"].strip() == "" for chunk in collected):
        return _error(start, "no_text_extracted", "No extractable text found in PDF", details={"pages_checked": len(collected)})

    full_text = "\n\n".join(chunk["text"] for chunk in collected)
    truncated = False
    if max_chars is not None and len(full_text) > max_chars:
        truncated = True
        full_text = full_text[:max_chars]

    metadata = reader.metadata or {}
    meta_payload: PdfMetadata = {
        "title": metadata.get("/Title"),
        "author": metadata.get("/Author"),
        "creator": metadata.get("/Creator"),
        "producer": metadata.get("/Producer"),
        "subject": metadata.get("/Subject"),
        "keywords": metadata.get("/Keywords"),
    }

    data: PdfData = {
        "path": str(pdf_path),
        "num_pages": total_pages,
        "is_encrypted": bool(reader.is_encrypted),
        "metadata": meta_payload,
        "text": full_text,
        "text_len": len(full_text),
        "truncated": truncated,
        "pages": collected if per_page else None,
    }

    return {
        "ok": True,
        "data": data,
        "error": None,
        "meta": _meta(start),
    }
