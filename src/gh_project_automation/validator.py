from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from rich.table import Table

from .project_fields import CANONICAL_FIELDS, FieldMeta, get_canonical_field_name
from .utils import ValidationError, console


REQUIRED_ISSUE_KEYS = [
    "title",
    "description",
    "status",
    "release",
    "phase",
    "area",
    "priority",
    "risk",
    "type",
    "effort",
]


@dataclass(frozen=True)
class ValidatedIssue:
    title: str
    description: str
    fields: dict[str, str]  # issue_key -> human option label


def load_issues(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValidationError("issues JSON must be a list of issue objects")
    return raw


def validate_issues(
    issues: Iterable[dict[str, Any]],
    *,
    fields_meta: dict[str, FieldMeta],
) -> list[ValidatedIssue]:
    validated: list[ValidatedIssue] = []
    for idx, issue in enumerate(issues, start=1):
        if not isinstance(issue, dict):
            raise ValidationError(f"Issue #{idx} must be an object")
        missing = [k for k in REQUIRED_ISSUE_KEYS if k not in issue]
        if missing:
            raise ValidationError(f"Issue #{idx} missing required keys: {', '.join(missing)}")

        title = str(issue["title"]).strip()
        desc = str(issue["description"])

        if not title:
            raise ValidationError(f"Issue #{idx} title cannot be empty")

        # validate each project field value exists in fields.json
        issue_fields: dict[str, str] = {}
        for issue_key in CANONICAL_FIELDS.keys():
            val = str(issue[issue_key]).strip()
            canonical = get_canonical_field_name(issue_key)
            if canonical not in fields_meta:
                raise ValidationError(
                    f"Field '{canonical}' not found in fields metadata. "
                    f"(needed by issue key '{issue_key}')"
                )
            meta = fields_meta[canonical]
            if val not in meta.options:
                allowed = ", ".join(sorted(meta.options.keys()))
                raise ValidationError(
                    f"Invalid value '{val}' for field '{canonical}' in issue #{idx}. "
                    f"Allowed: {allowed}"
                )
            issue_fields[issue_key] = val

        validated.append(ValidatedIssue(title=title, description=desc, fields=issue_fields))
    return validated


def print_dry_run_preview(issues: list[ValidatedIssue], *, limit: int | None = None) -> None:
    table = Table(title="Dry-run Preview (Issues)")
    table.add_column("#", style="dim", width=4)
    table.add_column("Title", overflow="fold")
    for k in ["release", "phase", "area", "priority", "risk", "type", "effort", "status"]:
        table.add_column(k)

    slice_ = issues[:limit] if limit else issues
    for i, it in enumerate(slice_, start=1):
        row = [str(i), it.title] + [it.fields[k] for k in ["release","phase","area","priority","risk","type","effort","status"]]
        table.add_row(*row)

    console.print(table)
