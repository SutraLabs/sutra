"""Utilities to create sample PDFs for tests."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def _add_text(writer: PdfWriter, page, text: str) -> None:
    stream = DecodedStreamObject()
    stream.set_data(f"BT /F1 14 Tf 72 720 Td ({text}) Tj ET".encode("utf-8"))
    stream_ref = writer._add_object(stream)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})})
    page[NameObject("/Contents")] = stream_ref


def create_sample_pdf(path: Path) -> Path:
    writer = PdfWriter()
    page1 = writer.add_blank_page(width=612, height=792)
    _add_text(writer, page1, "Ticket 123 sample page one.")

    page2 = writer.add_blank_page(width=612, height=792)
    _add_text(writer, page2, "Ticket 123 sample page two with more info.")

    writer.add_metadata({"/Title": "Fixture PDF", "/Author": "Sutra"})
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        writer.write(fh)
    return path
