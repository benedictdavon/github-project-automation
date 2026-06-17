from __future__ import annotations

import json

from gh_project_automation.cli import main


def _sample_issue(title: str = "Create setup docs") -> dict[str, str]:
    return {
        "title": title,
        "description": "Explain install, dry-run, and execute modes.",
        "status": "Backlog",
        "release": "MVP",
        "phase": "P1 - Scaffolding & DX",
        "area": "Docs",
        "priority": "P0 - Must Ship",
        "risk": "Low",
        "type": "Chore",
        "effort": "S - <= 1 day",
    }


def _write_sample_files(tmp_path, issues: list[dict[str, str]] | None = None):
    fields_path = tmp_path / "fields.json"
    issues_path = tmp_path / "issues.json"

    fields_path.write_text(
        json.dumps(
            {
                "Release": {"id": "F1", "options": {"MVP": "O1"}},
                "Phase": {"id": "F2", "options": {"P1 - Scaffolding & DX": "O2"}},
                "Area": {"id": "F3", "options": {"Docs": "O3"}},
                "Priority": {"id": "F4", "options": {"P0 - Must Ship": "O4"}},
                "Risk": {"id": "F5", "options": {"Low": "O5"}},
                "Type": {"id": "F6", "options": {"Chore": "O6"}},
                "Effort": {"id": "F7", "options": {"S - <= 1 day": "O7"}},
                "Status": {"id": "F8", "options": {"Backlog": "O8"}},
            }
        ),
        encoding="utf-8",
    )
    issues_path.write_text(
        json.dumps(issues or [_sample_issue()]),
        encoding="utf-8",
    )
    return issues_path, fields_path


def test_dry_run_does_not_require_github_env(tmp_path, monkeypatch) -> None:
    for key in ["GITHUB_TOKEN", "GITHUB_OWNER", "GITHUB_REPO", "GITHUB_PROJECT_ID"]:
        monkeypatch.delenv(key, raising=False)

    issues_path, fields_path = _write_sample_files(tmp_path)

    assert main(["--issues", str(issues_path), "--fields", str(fields_path)]) == 0


def test_execute_requires_github_env(tmp_path, monkeypatch) -> None:
    for key in ["GITHUB_TOKEN", "GITHUB_OWNER", "GITHUB_REPO", "GITHUB_PROJECT_ID"]:
        monkeypatch.delenv(key, raising=False)

    issues_path, fields_path = _write_sample_files(tmp_path)

    assert main(["--issues", str(issues_path), "--fields", str(fields_path), "--execute"]) == 1


def test_duplicate_input_fails_by_default(tmp_path) -> None:
    issues_path, fields_path = _write_sample_files(
        tmp_path,
        issues=[_sample_issue("Create setup docs"), _sample_issue(" create   setup DOCS ")],
    )

    assert main(["--issues", str(issues_path), "--fields", str(fields_path)]) == 1


def test_duplicate_input_can_be_skipped(tmp_path) -> None:
    issues_path, fields_path = _write_sample_files(
        tmp_path,
        issues=[_sample_issue("Create setup docs"), _sample_issue(" create   setup DOCS ")],
    )

    assert (
        main(
            [
                "--issues",
                str(issues_path),
                "--fields",
                str(fields_path),
                "--duplicate-policy",
                "skip",
            ]
        )
        == 0
    )


def test_duplicate_input_still_fails_in_upsert_mode(tmp_path) -> None:
    issues_path, fields_path = _write_sample_files(
        tmp_path,
        issues=[_sample_issue("Create setup docs"), _sample_issue(" create   setup DOCS ")],
    )

    assert (
        main(
            [
                "--issues",
                str(issues_path),
                "--fields",
                str(fields_path),
                "--duplicate-policy",
                "upsert",
            ]
        )
        == 1
    )


def test_upsert_updates_existing_issue_and_reuses_project_item(tmp_path, monkeypatch) -> None:
    events: list[tuple[str, object]] = []

    class FakeREST:
        def __init__(self, *, token: str, api_base: str) -> None:
            self.token = token
            self.api_base = api_base

        def find_issue_by_title(self, *, owner: str, repo: str, title: str):
            events.append(("find_issue", title))
            return {
                "number": 42,
                "title": "Create setup docs",
                "node_id": "ISSUE_NODE",
                "html_url": "https://github.example/issues/42",
            }

        def update_issue(
            self,
            *,
            owner: str,
            repo: str,
            number: int,
            title: str,
            body: str,
        ):
            events.append(("update_issue", {"number": number, "title": title, "body": body}))
            return {
                "number": number,
                "title": title,
                "node_id": "ISSUE_NODE",
                "html_url": "https://github.example/issues/42",
            }

        def create_issue(self, *, owner: str, repo: str, title: str, body: str):
            events.append(("create_issue", title))
            raise AssertionError("upsert should not create when an existing issue is found")

    class FakeGraphQL:
        def __init__(self, *, token: str, api_base: str) -> None:
            self.token = token
            self.api_base = api_base

        def query(self, query: str, variables: dict | None = None):
            variables = variables or {}
            if "IssueProjectItems" in query:
                events.append(("find_project_item", variables["issueId"]))
                return {
                    "node": {
                        "projectItems": {
                            "nodes": [{"id": "PROJECT_ITEM", "project": {"id": "PROJECT_ID"}}]
                        }
                    }
                }
            if "UpdateProjectV2ItemFieldValue" in query:
                events.append(("set_field", variables["fieldId"]))
                return {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PROJECT_ITEM"}}}
            if "AddProjectV2Item" in query:
                events.append(("add_project_item", variables["contentId"]))
                raise AssertionError("existing project item should be reused")
            raise AssertionError(f"Unexpected query: {query}")

    for key, value in {
        "GITHUB_TOKEN": "token",
        "GITHUB_OWNER": "owner",
        "GITHUB_REPO": "repo",
        "GITHUB_PROJECT_ID": "PROJECT_ID",
    }.items():
        monkeypatch.setenv(key, value)

    monkeypatch.setattr("gh_project_automation.cli.GitHubREST", FakeREST)
    monkeypatch.setattr("gh_project_automation.cli.GraphQLClient", FakeGraphQL)

    issues_path, fields_path = _write_sample_files(tmp_path)

    assert (
        main(
            [
                "--issues",
                str(issues_path),
                "--fields",
                str(fields_path),
                "--duplicate-policy",
                "upsert",
                "--execute",
            ]
        )
        == 0
    )

    event_names = [name for name, _ in events]
    assert "find_issue" in event_names
    assert "update_issue" in event_names
    assert "find_project_item" in event_names
    assert "create_issue" not in event_names
    assert "add_project_item" not in event_names
    assert event_names.count("set_field") == 8
