"""Create sample docs for RAG tests."""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_ticket_pdf(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(72, 720, "Ticket #42 - Sample PDF content about login failures.")
    c.drawString(72, 700, "User cannot sign in due to two-factor issues.")
    c.showPage()
    c.save()
    return path
