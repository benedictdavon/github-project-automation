from __future__ import annotations

from typing import Any

from gh_project_automation.project_item_manager import ProjectItemManager


class FakeGraphQL:
    def __init__(self, *, existing_item_id: str | None) -> None:
        self.existing_item_id = existing_item_id
        self.calls: list[dict[str, Any]] = []

    def query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        variables = variables or {}
        self.calls.append({"query": query, "variables": variables})

        if "IssueProjectItems" in query:
            nodes = []
            if self.existing_item_id:
                nodes.append({"id": self.existing_item_id, "project": {"id": "PROJECT_ID"}})
            return {"node": {"projectItems": {"nodes": nodes}}}

        if "AddProjectV2Item" in query:
            return {"addProjectV2ItemById": {"item": {"id": "NEW_ITEM_ID"}}}

        raise AssertionError(f"Unexpected query: {query}")


def test_ensure_issue_in_project_reuses_existing_item() -> None:
    gql = FakeGraphQL(existing_item_id="EXISTING_ITEM_ID")

    item = ProjectItemManager(gql, project_id="PROJECT_ID").ensure_issue_in_project(
        issue_node_id="ISSUE_NODE",
        execute=True,
    )

    assert item.item_id == "EXISTING_ITEM_ID"
    assert len(gql.calls) == 1


def test_ensure_issue_in_project_adds_missing_item() -> None:
    gql = FakeGraphQL(existing_item_id=None)

    item = ProjectItemManager(gql, project_id="PROJECT_ID").ensure_issue_in_project(
        issue_node_id="ISSUE_NODE",
        execute=True,
    )

    assert item.item_id == "NEW_ITEM_ID"
    assert len(gql.calls) == 2
