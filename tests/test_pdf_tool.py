from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pypdf")

from sutra.tools.executor import execute_tool

from .fixtures.make_sample_pdf import create_sample_pdf


@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("pdfs") / "sample.pdf"
    return create_sample_pdf(path)


def test_extract_text_success(sample_pdf: Path):
    res = execute_tool("pdf.extract_text", {"path": str(sample_pdf)})
    assert res["ok"] is True
    assert res["data"]["num_pages"] == 2
    assert "Ticket 123 sample page one" in res["data"]["text"]


def test_max_pages_limit(sample_pdf: Path):
    res = execute_tool("pdf.extract_text", {"path": str(sample_pdf), "max_pages": 1})
    assert res["ok"]
    assert "page two" not in res["data"]["text"]


def test_per_page_results(sample_pdf: Path):
    res = execute_tool("pdf.extract_text", {"path": str(sample_pdf), "per_page": True})
    assert res["ok"]
    pages = res["data"]["pages"]
    assert pages is not None
    assert len(pages) == 2
    assert pages[0]["page"] == 1


def test_unknown_tool_error():
    res = execute_tool("does.not.exist", {})
    assert res["ok"] is False
    assert res["error"]["type"] == "unknown_tool"
