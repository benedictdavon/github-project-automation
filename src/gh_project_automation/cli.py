from __future__ import annotations

import argparse
import sys

from .config import load_config
from .github_rest import GitHubREST
from .graphql_client import GraphQLClient
from .issue_creator import IssueCreator
from .project_fields import load_fields_json, get_canonical_field_name
from .project_item_manager import ProjectItemManager
from .utils import ApiError, ValidationError, console
from .validator import load_issues, validate_issues, print_dry_run_preview


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gh_project_automation",
        description="Create GitHub issues and set GitHub Project v2 fields from JSON.",
    )
    p.add_argument("--issues", required=True, help="Path to issues JSON file")
    p.add_argument("--fields", required=True, help="Path to fields metadata JSON")
    p.add_argument("--limit", type=int, default=None, help="Process only N issues")
    p.add_argument("--dry-run", action="store_true", help="Do not mutate (default)")
    p.add_argument("--execute", action="store_true", help="Perform real API mutations")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Safety: default to dry-run unless --execute
    execute = bool(args.execute) and not bool(args.dry_run)
    if not execute:
        console.print("[yellow]Running in DRY-RUN mode (no mutations). Use --execute to apply changes.[/yellow]")

    cfg = load_config()

    fields_meta = load_fields_json(args.fields)
    issues_raw = load_issues(args.issues)
    if args.limit:
        issues_raw = issues_raw[: args.limit]

    validated = validate_issues(issues_raw, fields_meta=fields_meta)
    print_dry_run_preview(validated, limit=args.limit)

    rest = GitHubREST(token=cfg.token, api_base=cfg.api_base)
    gql = GraphQLClient(token=cfg.token, api_base=cfg.api_base)

    creator = IssueCreator(rest, owner=cfg.owner, repo=cfg.repo)
    pim = ProjectItemManager(gql, project_id=cfg.project_id)

    # execution loop
    for idx, issue in enumerate(validated, start=1):
        console.rule(f"Issue {idx}/{len(validated)}")
        created = creator.create(title=issue.title, body=issue.description, execute=execute)

        added = pim.add_issue_to_project(issue_node_id=created.node_id, execute=execute)

        # set each field in a stable order
        for issue_key in ["release", "phase", "area", "priority", "risk", "type", "effort", "status"]:
            canonical = get_canonical_field_name(issue_key)
            meta = fields_meta[canonical]
            human_value = issue.fields[issue_key]
            option_id = meta.options[human_value]

            console.print(f"Setting [bold]{canonical}[/bold] = {human_value}")
            pim.set_single_select(item_id=added.item_id, field=meta, option_id=option_id, execute=execute)

        if execute:
            console.print(f"[green]Done[/green] {created.html_url}")
        else:
            console.print("[yellow]DRY-RUN complete for this issue[/yellow]")

    console.print("[green]All done.[/green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
