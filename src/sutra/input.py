"""WorkItem coercion and input loading utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, TypedDict


class WorkItem(TypedDict):
    id: str | None
    type: str | None
    text: str
    fields: Dict[str, Any]
    attachments: List[str]
    meta: Dict[str, Any]


KNOWN_KEYS = {"id", "type", "text", "fields", "attachments", "meta"}


def _safe_raw(value: Any) -> Any:
    """Ensure meta.raw is JSON serializable."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        json.dumps(value)
        return value
    except TypeError:
        return repr(value)


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def _coerce_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return str(value)


def _coerce_fields(data: Any) -> Dict[str, Any]:
    if isinstance(data, dict):
        return dict(data)
    return {}


def _coerce_attachments(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [value]
    return [str(value)]


def coerce_work_item(payload: Any) -> WorkItem:
    """
    Coerce arbitrary payloads (string/dict) into a canonical WorkItem.
    Unknown keys are captured under meta["extra"] and mirrored into fields
    for backward compatibility.
    """
    meta = {"raw": _safe_raw(payload)}
    if isinstance(payload, dict):
        base = dict(payload)
        meta_payload = base.get("meta")
        if isinstance(meta_payload, dict):
            meta.update(meta_payload)
        meta["raw"] = _safe_raw(payload)
        raw_fields = _coerce_fields(base.get("fields"))
        extras = {k: v for k, v in base.items() if k not in KNOWN_KEYS}
        if extras:
            meta["extra"] = extras
        # Merge extras into fields so older pipelines still see the keys.
        merged_fields = {**extras, **raw_fields}
        text_value = _coerce_text(base.get("text", ""))
        wi: WorkItem = {
            "id": _coerce_str(base.get("id")),
            "type": _coerce_str(base.get("type")),
            "text": text_value,
            "fields": merged_fields,
            "attachments": _coerce_attachments(base.get("attachments")),
            "meta": meta,
        }
        return wi

    text_value = _coerce_text(payload)
    wi = WorkItem(
        id=None,
        type=None,
        text=text_value,
        fields={},
        attachments=[],
        meta=meta,
    )
    return wi


def validate_work_item(item: WorkItem) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(item.get("text"), str):
        errors.append("text must be a string")
    if not isinstance(item.get("fields"), dict):
        errors.append("fields must be an object")
    if not isinstance(item.get("attachments"), list):
        errors.append("attachments must be a list")
    if not isinstance(item.get("meta"), dict):
        errors.append("meta must be an object")
    attachments = item.get("attachments", [])
    if isinstance(attachments, list):
        for idx, value in enumerate(attachments):
            if not isinstance(value, str):
                errors.append(f"attachments[{idx}] must be string")
    if errors:
        return False, errors
    return True, []


def _items_from_iterable(records: Iterable[Any]) -> List[WorkItem]:
    return [coerce_work_item(record) for record in records]


def load_work_items_from_text(text: str) -> List[WorkItem]:
    return [coerce_work_item({"text": text})]


def load_work_items_from_json(obj: Any) -> List[WorkItem]:
    if isinstance(obj, list):
        return _items_from_iterable(obj)
    return [coerce_work_item(obj)]


def load_work_items_from_jsonl(path: Path) -> List[WorkItem]:
    items: List[WorkItem] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = stripped
        items.append(coerce_work_item(payload))
    return items


def _parse_inline_json(data: str) -> Any:
    return json.loads(data)


def load_work_items(input_arg: str | None, text_arg: str | None, default_payload: Any | None = None) -> List[WorkItem]:
    """
    Resolve CLI inputs into a list of WorkItems.
    Priority:
        1. --text
        2. --input path/json/jsonl
        3. DEFAULT_INPUT fallback
    """
    if text_arg is not None:
        return load_work_items_from_text(text_arg)

    if input_arg:
        candidate = Path(input_arg)
        if candidate.exists():
            if candidate.suffix.lower() in (".jsonl", ".ndjson"):
                return load_work_items_from_jsonl(candidate)
            data = json.loads(candidate.read_text(encoding="utf-8"))
            return load_work_items_from_json(data)
        # fallback: treat argument as inline JSON
        try:
            parsed = _parse_inline_json(input_arg)
            return load_work_items_from_json(parsed)
        except json.JSONDecodeError as exc:
            raise ValueError(f"--input is neither a file nor valid JSON: {exc}") from exc

    if default_payload is None:
        return [coerce_work_item({"text": ""})]
    return load_work_items_from_json(default_payload)
