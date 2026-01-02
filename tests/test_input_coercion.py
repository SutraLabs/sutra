from __future__ import annotations

from sutra.input import coerce_work_item, load_work_items, validate_work_item


def test_coerce_string_payload():
    wi = coerce_work_item("KYC for Jane Doe")
    assert wi["text"] == "KYC for Jane Doe"
    assert wi["id"] is None and wi["type"] is None
    assert wi["meta"]["raw"] == "KYC for Jane Doe"
    ok, errors = validate_work_item(wi)
    assert ok, errors


def test_coerce_dict_with_unknown_fields():
    payload = {
        "id": 42,
        "type": "ticket",
        "text": "Ticket id 42",
        "fields": {"channel": "email"},
        "attachments": "image.png",
        "priority": "high",
    }
    wi = coerce_work_item(payload)
    assert wi["id"] == "42"
    assert wi["type"] == "ticket"
    assert wi["attachments"] == ["image.png"]
    # Unknown keys mirrored into fields and captured under meta.extra
    assert wi["fields"]["priority"] == "high"
    assert wi["fields"]["channel"] == "email"
    assert wi["meta"]["extra"]["priority"] == "high"


def test_load_work_items_prefers_text_argument():
    items = load_work_items(None, "Inline text payload", default_payload=None)
    assert len(items) == 1
    assert items[0]["text"] == "Inline text payload"
