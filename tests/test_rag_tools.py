from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("sentence_transformers")
pytest.importorskip("reportlab")

from sutra.tools.executor import execute_tool

from .fixtures.sample_docs import create_ticket_pdf


@pytest.fixture(scope="module")
def docs_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("docs")
    create_ticket_pdf(folder / "ticket.pdf")
    (folder / "notes.txt").write_text("Ticket #42 text file detailing login failure and MFA errors.")
    return folder


@pytest.fixture
def index_dir(tmp_path: Path) -> Path:
    return tmp_path / "index"


def test_index_and_query(docs_dir: Path, index_dir: Path):
    idx = execute_tool(
        "rag.index_folder",
        {
            "folder": str(docs_dir),
            "index_dir": str(index_dir),
            "extensions": [".pdf", ".txt"],
            "rebuild": True,
            "max_pages_per_pdf": 5,
        },
    )
    assert idx["ok"], idx["error"]
    assert idx["data"]["num_docs_indexed"] >= 1

    res = execute_tool(
        "rag.query",
        {
            "index_dir": str(index_dir),
            "query": "login failure",
            "top_k": 2,
            "generate": False,
        },
    )
    assert res["ok"], res["error"]
    results = res["data"]["results"]
    assert results
    assert "login failure" in results[0]["text"].lower()


def test_missing_index_error():
    res = execute_tool(
        "rag.query",
        {
            "index_dir": "/tmp/does-not-exist",
            "query": "hello",
        },
    )
    assert not res["ok"]
    assert res["error"]["type"] == "missing_index"
