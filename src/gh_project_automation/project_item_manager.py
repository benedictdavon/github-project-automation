from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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

UPDATE_SINGLE_SELECT_MUTATION = """
mutation UpdateProjectV2ItemFieldValue($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
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

    def add_issue_to_project(self, *, issue_node_id: str, execute: bool) -> AddedProjectItem:
        if not execute:
            console.print(f"[yellow]DRY-RUN[/yellow] would add issue node {issue_node_id} to project")
            return AddedProjectItem(item_id="DRY_RUN_ITEM_ID")

        console.print("[cyan]Adding issue to project[/cyan]")
        data = self.gql.query(ADD_ITEM_MUTATION, {"projectId": self.project_id, "contentId": issue_node_id})
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
            console.print(f"[yellow]DRY-RUN[/yellow] would set field {field.id} to option {option_id}")
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
