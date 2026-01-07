from __future__ import annotations

import pytest

from gh_project_automation.project_fields import FieldMeta
from gh_project_automation.validator import validate_issues
from gh_project_automation.utils import ValidationError


def _fields_meta() -> dict[str, FieldMeta]:
    return {
        "Release": FieldMeta(id="F1", options={"MVP": "O1"}),
        "Phase": FieldMeta(id="F2", options={"P1 — Scaffolding & DX": "O2"}),
        "Area": FieldMeta(id="F3", options={"API (FastAPI)": "O3"}),
        "Priority": FieldMeta(id="F4", options={"P0 — Must Ship": "O4"}),
        "Risk": FieldMeta(id="F5", options={"Low": "O5"}),
        "Type": FieldMeta(id="F6", options={"Feature": "O6"}),
        "Effort": FieldMeta(id="F7", options={"M — 2–3 days": "O7"}),
        "Status": FieldMeta(id="F8", options={"Backlog": "O8"}),
    }


def test_validate_ok():
    issues = [{
        "title": "Hello",
        "description": "Body",
        "status": "Backlog",
        "release": "MVP",
        "phase": "P1 — Scaffolding & DX",
        "area": "API (FastAPI)",
        "priority": "P0 — Must Ship",
        "risk": "Low",
        "type": "Feature",
        "effort": "M — 2–3 days",
    }]
    out = validate_issues(issues, fields_meta=_fields_meta())
    assert len(out) == 1
    assert out[0].title == "Hello"


def test_missing_key_fails():
    issues = [{
        "title": "Hello",
        "description": "Body",
        # missing required keys
        "status": "Backlog",
    }]
    with pytest.raises(ValidationError):
        validate_issues(issues, fields_meta=_fields_meta())


def test_invalid_option_fails():
    issues = [{
        "title": "Hello",
        "description": "Body",
        "status": "NotARealStatus",
        "release": "MVP",
        "phase": "P1 — Scaffolding & DX",
        "area": "API (FastAPI)",
        "priority": "P0 — Must Ship",
        "risk": "Low",
        "type": "Feature",
        "effort": "M — 2–3 days",
    }]
    with pytest.raises(ValidationError):
        validate_issues(issues, fields_meta=_fields_meta())
