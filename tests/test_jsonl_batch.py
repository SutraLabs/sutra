from __future__ import annotations

from pathlib import Path

from sutra.input import load_work_items


def test_load_jsonl_batch(tmp_path: Path):
    path = tmp_path / "records.jsonl"
    path.write_text(
        '{"text": "first ticket", "fields": {"channel": "web"}}\n'
        '"Second ticket raw line"\n',
        encoding="utf-8",
    )

    items = load_work_items(str(path), None, default_payload=None)
    assert len(items) == 2
    assert items[0]["fields"]["channel"] == "web"
    assert items[1]["text"] == "Second ticket raw line"
    assert items[1]["meta"]["raw"] == "Second ticket raw line"
