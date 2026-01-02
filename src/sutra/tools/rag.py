"""Local RAG tools for Sutra."""
from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict
try:
    import numpy as np
except Exception:  # pragma: no cover - optional extra
        np = None  # type: ignore

from ..version import __version__ as SUTRA_VERSION
from ..core import Ollama
from .pdf import extract_text as pdf_extract
from .text import chunk_text

TOOL_INDEX = "rag.index_folder"
TOOL_QUERY = "rag.query"
INDEX_VERSION = "1.0"


class ToolMeta(TypedDict):
    tool: str
    version: str
    elapsed_ms: int


class ToolError(TypedDict, total=False):
    type: str
    message: str
    details: Any
    raw: Optional[str]


class ToolEnvelope(TypedDict):
    ok: bool
    data: Optional[dict]
    error: Optional[ToolError]
    meta: ToolMeta


def _meta(tool: str, start: float) -> ToolMeta:
    return {"tool": tool, "version": INDEX_VERSION, "elapsed_ms": int((time.perf_counter() - start) * 1000)}


def _error(tool: str, start: float, err_type: str, message: str, *, details: Any = None, raw: Optional[str] = None) -> ToolEnvelope:
    return {
        "ok": False,
        "data": None,
        "error": {"type": err_type, "message": message, "details": details, "raw": raw},
        "meta": _meta(tool, start),
    }


def _load_sentence_model(name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover - optional dep
        raise RuntimeError("sentence-transformers is required for rag tools") from exc
    try:
        return SentenceTransformer(name, device="cpu")
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Unable to load embedding model '{name}'") from exc


def _normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def _read_text_file(path: Path, max_chars: Optional[int]) -> str:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if max_chars is not None:
        return data[:max_chars]
    return data


def _pdf_to_text(path: Path, max_pages: Optional[int], max_chars: Optional[int]) -> Tuple[str, Dict[str, Any]]:
    envelope = pdf_extract(path=str(path), max_pages=max_pages, per_page=True, max_chars=max_chars)
    if not envelope["ok"] or not envelope["data"]:
        raise ValueError(envelope["error"]["message"] if envelope["error"] else "PDF extraction failed")
    return envelope["data"]["text"], envelope["data"]


def _assign_page_offsets(pages: List[dict]) -> List[Tuple[int, int]]:
    offsets = []
    cursor = 0
    for page_info in pages or []:
        text = page_info.get("text") or ""
        start = cursor
        cursor += len(text) + 2  # compensate for join newline
        offsets.append((start, cursor, page_info.get("page")))
    return offsets


def _page_for_chunk(start: int, offsets: List[Tuple[int, int]]) -> Optional[int]:
    for s, e, page in offsets:
        if start >= s and start < e:
            return page
    return None


def _prepare_index_dir(index_dir: Path, rebuild: bool) -> None:
    if rebuild and index_dir.exists():
        shutil.rmtree(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)


def index_folder(
    *,
    folder: str,
    index_dir: str,
    extensions: Optional[List[str]] = None,
    embed_model: str = "all-MiniLM-L6-v2",
    chunk_size: int = 800,
    chunk_overlap: int = 120,
    max_files: Optional[int] = None,
    max_pages_per_pdf: Optional[int] = 25,
    max_chars_per_doc: Optional[int] = 200000,
    rebuild: bool = False,
) -> ToolEnvelope:
    start = time.perf_counter()
    if np is None:
        return _error(TOOL_INDEX, start, "missing_dependency", "numpy is required. Install 'sutra-ai[rag]'.")
    folder_path = Path(folder)
    idx_path = Path(index_dir)
    if not folder_path.exists():
        return _error(TOOL_INDEX, start, "invalid_args", f"Folder not found: {folder}")

    exts = set((extensions or [".pdf", ".txt", ".md"]))
    files = [p for p in folder_path.rglob("*") if p.suffix.lower() in exts and p.is_file()]
    if max_files:
        files = files[:max_files]
    if not files:
        return _error(TOOL_INDEX, start, "no_files_found", "No documents found for indexing")

    try:
        model = _load_sentence_model(embed_model)
    except RuntimeError as exc:
        return _error(TOOL_INDEX, start, "embed_model_load_failed", str(exc))

    _prepare_index_dir(idx_path, rebuild)
    embeddings: List[np.ndarray] = []
    chunk_records: List[dict] = []
    skipped: List[dict] = []
    doc_id = 0

    for path in files:
        try:
            if path.suffix.lower() == ".pdf":
                text, pdf_meta = _pdf_to_text(path, max_pages_per_pdf, max_chars_per_doc)
                pages = pdf_meta.get("pages") if pdf_meta else None
            else:
                text = _read_text_file(path, max_chars_per_doc)
                pages = None
        except Exception as exc:
            skipped.append({"path": str(path), "reason": str(exc)})
            continue

        if not text.strip():
            skipped.append({"path": str(path), "reason": "empty_text"})
            continue

        chunk_env = chunk_text(text=text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunk_env["ok"] or not chunk_env["data"]:
            reason = chunk_env["error"]["message"] if chunk_env.get("error") else "chunking_failed"
            skipped.append({"path": str(path), "reason": reason})
            continue

        offsets = _assign_page_offsets(pages or [])
        for chunk in chunk_env["data"]["chunks"]:
            chunk_text_val = chunk["text"].strip()
            if not chunk_text_val:
                continue
            chunk_records.append(
                {
                    "doc_id": doc_id,
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk_text_val,
                    "path": str(path),
                    "page": _page_for_chunk(chunk["start"], offsets),
                    "start": chunk["start"],
                    "end": chunk["end"],
                }
            )
        doc_id += 1

    if not chunk_records:
        return _error(TOOL_INDEX, start, "no_chunks", "No valid chunks extracted", details={"skipped": skipped})

    texts = [record["text"] for record in chunk_records]
    try:
        vecs = model.encode(texts, convert_to_numpy=True, batch_size=32)
    except Exception as exc:
        return _error(TOOL_INDEX, start, "embedding_failed", "Failed to embed chunks", raw=str(exc))
    vecs = _normalize(vecs.astype(np.float32))
    embeddings.append(vecs)

    full_embeddings = np.vstack(embeddings)
    np.save(idx_path / "embeddings.npy", full_embeddings)
    with open(idx_path / "chunks.jsonl", "w", encoding="utf-8") as fh:
        for record in chunk_records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    manifest = {
        "version": INDEX_VERSION,
        "sutra_version": SUTRA_VERSION,
        "embed_model": embed_model,
        "dims": full_embeddings.shape[1],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "num_docs": doc_id,
        "num_chunks": len(chunk_records),
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }
    with open(idx_path / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    return {
        "ok": True,
        "data": {
            "folder": str(folder_path),
            "index_dir": str(idx_path),
            "embed_model": embed_model,
            "num_docs_indexed": doc_id,
            "num_chunks_indexed": len(chunk_records),
            "skipped": skipped,
            "manifest": manifest,
        },
        "error": None,
        "meta": _meta(TOOL_INDEX, start),
    }


def _load_index(index_dir: Path) -> Tuple[dict, List[dict], np.ndarray]:
    manifest_path = index_dir / "manifest.json"
    embeddings_path = index_dir / "embeddings.npy"
    chunks_path = index_dir / "chunks.jsonl"
    if not manifest_path.exists() or not embeddings_path.exists() or not chunks_path.exists():
        raise FileNotFoundError("Index files missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    embeddings = np.load(embeddings_path)
    chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(chunks) != embeddings.shape[0]:
        raise ValueError("Embeddings/chunks count mismatch")
    return manifest, chunks, embeddings


def query(
    *,
    index_dir: str,
    query: str,
    top_k: int = 5,
    min_score: Optional[float] = None,
    generate: bool = False,
    ollama_model: Optional[str] = None,
    max_context_chars: int = 12000,
) -> ToolEnvelope:
    start = time.perf_counter()
    if np is None:
        return _error(TOOL_QUERY, start, "missing_dependency", "numpy is required. Install 'sutra-ai[rag]'.")
    idx_path = Path(index_dir)
    if not idx_path.exists():
        return _error(TOOL_QUERY, start, "missing_index", f"Index directory not found: {index_dir}")

    try:
        manifest, chunks, embeddings = _load_index(idx_path)
    except FileNotFoundError:
        return _error(TOOL_QUERY, start, "missing_index", "Index files missing")
    except Exception as exc:
        return _error(TOOL_QUERY, start, "index_load_failed", "Unable to load index", raw=str(exc))

    if embeddings.size == 0:
        return _error(TOOL_QUERY, start, "empty_index", "Index contains no embeddings")

    embed_model = manifest.get("embed_model", "all-MiniLM-L6-v2")
    try:
        model = _load_sentence_model(embed_model)
    except RuntimeError as exc:
        return _error(TOOL_QUERY, start, "embed_model_load_failed", str(exc))

    try:
        q_vec = model.encode([query], convert_to_numpy=True)[0]
    except Exception as exc:
        return _error(TOOL_QUERY, start, "query_embed_failed", "Failed to embed query", raw=str(exc))
    q_vec = q_vec.astype(np.float32)
    q_vec /= np.linalg.norm(q_vec) or 1.0

    scores = embeddings @ q_vec
    idxs = np.argsort(-scores)[: top_k * 2]

    results = []
    for rank, idx_val in enumerate(idxs[:top_k], start=1):
        score = float(scores[idx_val])
        if min_score is not None and score < min_score:
            continue
        chunk = chunks[idx_val]
        results.append(
            {
                "rank": rank,
                "score": score,
                "text": chunk["text"],
                "path": chunk["path"],
                "page": chunk.get("page"),
            }
        )
    if not results:
        return {
            "ok": True,
            "data": {"query": query, "top_k": top_k, "results": []},
            "error": None,
            "meta": _meta(TOOL_QUERY, start),
        }

    output = {"query": query, "top_k": top_k, "results": results}

    if generate:
        context = ""
        used = []
        for r in results:
            snippet = f"[{r['path']}:{r.get('page')}] {r['text']}\n\n"
            if len(context) + len(snippet) > max_context_chars:
                break
            context += snippet
            used.append({"rank": r["rank"], "score": r["score"], "path": r["path"], "page": r.get("page")})
        if not context:
            output["answer"] = ""
        else:
            model_name = ollama_model or "llama3.1:latest"
            prompt = (
                "You are a precise assistant. Use the provided context to answer the question.\n"
                "Return JSON only with keys 'answer' and 'citations'.\n"
                f"Context:\n{context}\nQuestion: {query}\nJSON:"
            )
            try:
                llm = Ollama(model=model_name)
                raw = llm.generate(prompt, json_mode=True)
                payload = json.loads(raw)
                answer = payload.get("answer", raw)
            except Exception as exc:
                answer = f"Generation failed: {exc}"
                used = []
            output["answer"] = answer
            output["used_context"] = used

    return {"ok": True, "data": output, "error": None, "meta": _meta(TOOL_QUERY, start)}
