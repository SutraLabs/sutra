"""Example pipeline that uses the PDF tool connector."""
from __future__ import annotations

from sutra import Pipeline, Step
from sutra.tools.executor import execute_tool


class PdfLoader:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
    def run(self, inputs):
        envelope = execute_tool("pdf.extract_text", {"path": self.pdf_path, "max_pages": 2})
        return {"pdf_envelope": envelope}


class Summarizer:
    def run(self, inputs):
        envelope = inputs.get("pdf_envelope", {})
        if not envelope or not envelope.get("ok"):
            return {"summary": "PDF extraction failed", "raw": envelope}
        text = envelope["data"]["text"]
        summary = text[:200] + ("..." if len(text) > 200 else "")
        return {"summary": summary}


def build():
    pdf_path = "path/to/document.pdf"  # Update to a real file on disk
    steps = [
        Step(PdfLoader(pdf_path)),
        Step(Summarizer()),
    ]
    return Pipeline(steps)


DEFAULT_INPUT = {}


if __name__ == "__main__":
    pipe = build()
    result = pipe.run(DEFAULT_INPUT)
    print(result["summary"]["summary"])
