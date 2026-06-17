from __future__ import annotations

import json

import pytest

from gh_project_automation.project_fields import FieldMeta, load_fields_json
from gh_project_automation.utils import ValidationError
from gh_project_automation.validator import load_issues, validate_issues


def _fields_meta() -> dict[str, FieldMeta]:
    return {
        "Release": FieldMeta(id="F1", options={"MVP": "O1"}),
        "Phase": FieldMeta(id="F2", options={"P1 - Scaffolding & DX": "O2"}),
        "Area": FieldMeta(id="F3", options={"API (FastAPI)": "O3"}),
        "Priority": FieldMeta(id="F4", options={"P0 - Must Ship": "O4"}),
        "Risk": FieldMeta(id="F5", options={"Low": "O5"}),
        "Type": FieldMeta(id="F6", options={"Feature": "O6"}),
        "Effort": FieldMeta(id="F7", options={"M - 2-3 days": "O7"}),
        "Status": FieldMeta(id="F8", options={"Backlog": "O8"}),
    }


def _valid_issue() -> dict[str, str]:
    return {
        "title": "Create setup docs",
        "description": "Explain install, dry-run, and execute modes.",
        "status": "Backlog",
        "release": "MVP",
        "phase": "P1 - Scaffolding & DX",
        "area": "API (FastAPI)",
        "priority": "P0 - Must Ship",
        "risk": "Low",
        "type": "Feature",
        "effort": "M - 2-3 days",
    }


def test_validate_ok() -> None:
    out = validate_issues([_valid_issue()], fields_meta=_fields_meta())

    assert len(out) == 1
    assert out[0].title == "Create setup docs"
    assert out[0].fields["status"] == "Backlog"


def test_missing_key_fails() -> None:
    issue = _valid_issue()
    del issue["priority"]

    with pytest.raises(ValidationError, match="missing required keys: priority"):
        validate_issues([issue], fields_meta=_fields_meta())


def test_empty_description_fails() -> None:
    issue = _valid_issue()
    issue["description"] = "   "

    with pytest.raises(ValidationError, match="description cannot be empty"):
        validate_issues([issue], fields_meta=_fields_meta())


def test_invalid_option_fails() -> None:
    issue = _valid_issue()
    issue["status"] = "NotARealStatus"

    with pytest.raises(ValidationError, match="Invalid value 'NotARealStatus'"):
        validate_issues([issue], fields_meta=_fields_meta())


def test_load_issues_rejects_non_list(tmp_path) -> None:
    issues_path = tmp_path / "issues.json"
    issues_path.write_text(json.dumps({"title": "not a list"}), encoding="utf-8")

    with pytest.raises(ValidationError, match="issues JSON must be a list"):
        load_issues(issues_path)


def test_load_fields_rejects_missing_options(tmp_path) -> None:
    fields_path = tmp_path / "fields.json"
    fields_path.write_text(json.dumps({"Status": {"id": "F8"}}), encoding="utf-8")

    with pytest.raises(ValidationError, match="Invalid metadata"):
        load_fields_json(fields_path)
