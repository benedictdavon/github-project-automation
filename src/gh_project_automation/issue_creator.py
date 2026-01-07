from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .github_rest import GitHubREST
from .utils import console


@dataclass(frozen=True)
class CreatedIssue:
    number: int
    node_id: str
    html_url: str


class IssueCreator:
    def __init__(self, rest: GitHubREST, *, owner: str, repo: str) -> None:
        self.rest = rest
        self.owner = owner
        self.repo = repo

    def create(self, *, title: str, body: str, execute: bool) -> CreatedIssue:
        if not execute:
            console.print(f"[yellow]DRY-RUN[/yellow] would create issue: {title}")
            # Placeholder values
            return CreatedIssue(number=-1, node_id="DRY_RUN_NODE_ID", html_url="DRY_RUN_URL")

        console.print(f"[cyan]Creating issue[/cyan]: {title}")
        data = self.rest.create_issue(owner=self.owner, repo=self.repo, title=title, body=body)
        return CreatedIssue(
            number=int(data["number"]),
            node_id=str(data["node_id"]),
            html_url=str(data["html_url"]),
        )
