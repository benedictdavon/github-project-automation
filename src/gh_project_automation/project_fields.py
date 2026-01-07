from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils import ValidationError


@dataclass(frozen=True)
class FieldMeta:
    id: str
    options: dict[str, str]  # human label -> option id


def load_fields_json(path: str | Path) -> dict[str, FieldMeta]:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    out: dict[str, FieldMeta] = {}

    if not isinstance(raw, dict):
        raise ValidationError("fields.json must be an object mapping field name -> metadata")

    for field_name, meta in raw.items():
        if not isinstance(meta, dict) or "id" not in meta or "options" not in meta:
            raise ValidationError(f"Invalid metadata for field '{field_name}'. Expected keys: id, options")
        options = meta["options"]
        if not isinstance(options, dict):
            raise ValidationError(f"Invalid options for field '{field_name}': must be an object")
        out[field_name] = FieldMeta(id=str(meta["id"]), options={str(k): str(v) for k, v in options.items()})
    return out


# Canonical field names (as they appear in fields.json)
CANONICAL_FIELDS: dict[str, str] = {
    "release": "Release",
    "phase": "Phase",
    "area": "Area",
    "priority": "Priority",
    "risk": "Risk",
    "type": "Type",
    "effort": "Effort",
    "status": "Status",
}


def get_canonical_field_name(issue_key: str) -> str:
    if issue_key not in CANONICAL_FIELDS:
        raise ValidationError(f"Unknown issue field key: {issue_key}")
    return CANONICAL_FIELDS[issue_key]
