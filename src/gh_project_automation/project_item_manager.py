from __future__ import annotations

from dataclasses import dataclass

from .graphql_client import GraphQLClient
from .project_fields import FieldMeta
from .utils import ApiError, console

ADD_ITEM_MUTATION = """
mutation AddProjectV2Item($projectId:ID!, $contentId:ID!) {
  addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
    item { id }
  }
}
"""

ISSUE_PROJECT_ITEMS_QUERY = """
query IssueProjectItems($issueId: ID!) {
  node(id: $issueId) {
    ... on Issue {
      projectItems(first: 100) {
        nodes {
          id
          project {
            id
          }
        }
      }
    }
  }
}
"""

UPDATE_SINGLE_SELECT_MUTATION = """
mutation UpdateProjectV2ItemFieldValue(
  $projectId: ID!
  $itemId: ID!
  $fieldId: ID!
  $optionId: String!
) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $projectId
      itemId: $itemId
      fieldId: $fieldId
      value: { singleSelectOptionId: $optionId }
    }
  ) {
    projectV2Item { id }
  }
}
"""


@dataclass(frozen=True)
class AddedProjectItem:
    item_id: str


class ProjectItemManager:
    def __init__(self, gql: GraphQLClient, *, project_id: str) -> None:
        self.gql = gql
        self.project_id = project_id

    def find_item_for_issue(self, *, issue_node_id: str) -> AddedProjectItem | None:
        data = self.gql.query(ISSUE_PROJECT_ITEMS_QUERY, {"issueId": issue_node_id})
        node = data.get("node") or {}
        project_items = node.get("projectItems") or {}

        for item in project_items.get("nodes") or []:
            project = item.get("project") or {}
            if project.get("id") == self.project_id:
                return AddedProjectItem(item_id=str(item["id"]))

        return None

    def ensure_issue_in_project(self, *, issue_node_id: str, execute: bool) -> AddedProjectItem:
        if not execute:
            return self.add_issue_to_project(issue_node_id=issue_node_id, execute=False)

        existing = self.find_item_for_issue(issue_node_id=issue_node_id)
        if existing is not None:
            console.print("[cyan]Reusing existing project item[/cyan]")
            return existing

        return self.add_issue_to_project(issue_node_id=issue_node_id, execute=True)

    def add_issue_to_project(self, *, issue_node_id: str, execute: bool) -> AddedProjectItem:
        if not execute:
            console.print(
                f"[yellow]DRY-RUN[/yellow] would add issue node {issue_node_id} to project"
            )
            return AddedProjectItem(item_id="DRY_RUN_ITEM_ID")

        console.print("[cyan]Adding issue to project[/cyan]")
        data = self.gql.query(
            ADD_ITEM_MUTATION,
            {"projectId": self.project_id, "contentId": issue_node_id},
        )
        item_id = data["addProjectV2ItemById"]["item"]["id"]
        return AddedProjectItem(item_id=str(item_id))

    def set_single_select(
        self,
        *,
        item_id: str,
        field: FieldMeta,
        option_id: str,
        execute: bool,
    ) -> None:
        if not execute:
            console.print(
                f"[yellow]DRY-RUN[/yellow] would set field {field.id} to option {option_id}"
            )
            return

        data = self.gql.query(
            UPDATE_SINGLE_SELECT_MUTATION,
            {
                "projectId": self.project_id,
                "itemId": item_id,
                "fieldId": field.id,
                "optionId": option_id,
            },
        )
        if not data.get("updateProjectV2ItemFieldValue"):
            raise ApiError("Failed to update field value (no data returned)")
