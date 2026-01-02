"""Minimal example showing PDF indexing + query via Sutra tools."""
from __future__ import annotations

from pathlib import Path

from sutra.tools.executor import execute_tool


def main():
    docs = "path/to/folder"  # replace with folder containing PDFs/text files
    index = ".sutra/rag_index"

    idx_env = execute_tool(
        "rag.index_folder",
        {
            "folder": docs,
            "index_dir": index,
            "extensions": [".pdf", ".txt"],
            "embed_model": "all-MiniLM-L6-v2",
            "rebuild": True,
        },
    )
    if not idx_env["ok"]:
        raise SystemExit(f"Indexing failed: {idx_env['error']}")

    query_env = execute_tool(
        "rag.query",
        {
            "index_dir": index,
            "query": "What were the key issues mentioned?",
            "top_k": 3,
            "generate": False,
        },
    )
    if not query_env["ok"]:
        raise SystemExit(f"Query failed: {query_env['error']}")

    for res in query_env["data"]["results"]:
        print(f"{res['rank']}: {res['path']} (score={res['score']:.3f})")
        print(res["text"])
        print("-" * 40)


if __name__ == "__main__":
    main()
