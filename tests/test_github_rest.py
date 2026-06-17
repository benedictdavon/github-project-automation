from __future__ import annotations

from typing import Any

from gh_project_automation.github_rest import GitHubREST


class FakeResponse:
    status_code = 200
    text = "OK"

    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self._payload = payload

    def json(self) -> list[dict[str, Any]]:
        return self._payload


def test_find_issue_by_title_ignores_pull_requests(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_get(url, *, params, headers, timeout):  # noqa: ANN001
        calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        return FakeResponse(
            [
                {
                    "number": 7,
                    "title": "Create setup docs",
                    "node_id": "PR_NODE",
                    "html_url": "https://github.example/pull/7",
                    "pull_request": {},
                },
                {
                    "number": 8,
                    "title": " Create   Setup Docs ",
                    "node_id": "ISSUE_NODE",
                    "html_url": "https://github.example/issues/8",
                },
            ]
        )

    monkeypatch.setattr("gh_project_automation.github_rest.requests.get", fake_get)

    found = GitHubREST(token="token").find_issue_by_title(
        owner="owner",
        repo="repo",
        title="create setup docs",
    )

    assert found is not None
    assert found["number"] == 8
    assert calls[0]["params"]["state"] == "open"


def test_update_issue_uses_patch(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    class PatchResponse:
        status_code = 200
        text = "OK"

        def json(self) -> dict[str, Any]:
            return {
                "number": 8,
                "title": "Updated title",
                "body": "Updated body",
                "node_id": "ISSUE_NODE",
                "html_url": "https://github.example/issues/8",
            }

    def fake_patch(url, *, json, headers, timeout):  # noqa: ANN001
        calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return PatchResponse()

    monkeypatch.setattr("gh_project_automation.github_rest.requests.patch", fake_patch)

    updated = GitHubREST(token="token").update_issue(
        owner="owner",
        repo="repo",
        number=8,
        title="Updated title",
        body="Updated body",
    )

    assert updated["number"] == 8
    assert calls[0]["url"].endswith("/repos/owner/repo/issues/8")
    assert calls[0]["json"] == {"title": "Updated title", "body": "Updated body"}
