from __future__ import annotations

import argparse

from .config import load_config
from .duplicates import DuplicatePolicy, find_duplicate_titles, normalize_issue_title
from .github_rest import GitHubREST
from .graphql_client import GraphQLClient
from .issue_creator import IssueCreator
from .project_fields import CANONICAL_FIELDS, get_canonical_field_name, load_fields_json
from .project_item_manager import ProjectItemManager
from .utils import GhAutomationError, ValidationError, console
from .validator import ValidatedIssue, load_issues, print_dry_run_preview, validate_issues

FIELD_ORDER = list(CANONICAL_FIELDS.keys())
DUPLICATE_POLICIES = ("fail", "skip", "allow", "upsert")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be greater than or equal to 1")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gh_project_automation",
        description="Create GitHub issues and set GitHub Project v2 fields from JSON.",
    )
    p.add_argument("--issues", required=True, help="Path to issues JSON file")
    p.add_argument("--fields", required=True, help="Path to fields metadata JSON")
    p.add_argument("--limit", type=positive_int, default=None, help="Process only N issues")
    p.add_argument(
        "--duplicate-policy",
        choices=DUPLICATE_POLICIES,
        default="fail",
        help=(
            "How to handle duplicate issue titles: fail (default), "
            "skip repeated/existing issues, allow duplicates, or upsert existing issues."
        ),
    )

    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate and preview only (default)")
    mode.add_argument("--execute", action="store_true", help="Perform real API mutations")
    return p


def apply_local_duplicate_policy(
    issues: list[ValidatedIssue],
    *,
    policy: DuplicatePolicy,
) -> list[ValidatedIssue]:
    if policy == "allow":
        return issues

    duplicates = find_duplicate_titles(issue.title for issue in issues)
    if not duplicates:
        return issues

    if policy in {"fail", "upsert"}:
        details = "; ".join(
            f"#{dup.duplicate_index} duplicates #{dup.first_index}: {dup.title}"
            for dup in duplicates
        )
        raise ValidationError(f"Duplicate issue titles in input: {details}")

    seen: set[str] = set()
    deduped: list[ValidatedIssue] = []
    for issue in issues:
        normalized = normalize_issue_title(issue.title)
        if normalized in seen:
            console.print(f"[yellow]Skipping duplicate input issue:[/yellow] {issue.title}")
            continue
        seen.add(normalized)
        deduped.append(issue)

    return deduped


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    duplicate_policy: DuplicatePolicy = args.duplicate_policy

    execute = bool(args.execute)
    if not execute:
        console.print(
            "[yellow]Running in DRY-RUN mode (no mutations). "
            "Use --execute to apply changes.[/yellow]"
        )

    fields_meta = load_fields_json(args.fields)
    issues_raw = load_issues(args.issues)
    if args.limit is not None:
        issues_raw = issues_raw[: args.limit]

    validated = validate_issues(issues_raw, fields_meta=fields_meta)
    validated = apply_local_duplicate_policy(validated, policy=duplicate_policy)
    print_dry_run_preview(validated, limit=args.limit)

    if not execute:
        console.print(
            f"[green]Validated {len(validated)} issue(s). "
            "No GitHub API calls were made.[/green]"
        )
        return 0

    cfg = load_config()

    rest = GitHubREST(token=cfg.token, api_base=cfg.api_base)
    gql = GraphQLClient(token=cfg.token, api_base=cfg.api_base)

    creator = IssueCreator(rest, owner=cfg.owner, repo=cfg.repo)
    pim = ProjectItemManager(gql, project_id=cfg.project_id)

    # execution loop
    for idx, issue in enumerate(validated, start=1):
        console.rule(f"Issue {idx}/{len(validated)}")

        existing = None
        if duplicate_policy != "allow":
            existing = creator.find_existing(title=issue.title)

        if existing is not None:
            message = (
                f"Duplicate issue already exists: #{existing.number} "
                f"{existing.title or issue.title} ({existing.html_url})"
            )
            if duplicate_policy == "fail":
                raise ValidationError(message)

            if duplicate_policy == "skip":
                console.print(f"[yellow]Skipping remote duplicate.[/yellow] {message}")
                continue

            created = creator.update(issue=existing, title=issue.title, body=issue.description)
            added = pim.ensure_issue_in_project(issue_node_id=created.node_id, execute=execute)
        else:
            created = creator.create(title=issue.title, body=issue.description, execute=execute)
            added = pim.add_issue_to_project(issue_node_id=created.node_id, execute=execute)

        # set each field in a stable order
        for issue_key in FIELD_ORDER:
            canonical = get_canonical_field_name(issue_key)
            meta = fields_meta[canonical]
            human_value = issue.fields[issue_key]
            option_id = meta.options[human_value]

            console.print(f"Setting [bold]{canonical}[/bold] = {human_value}")
            pim.set_single_select(
                item_id=added.item_id,
                field=meta,
                option_id=option_id,
                execute=execute,
            )

        if execute:
            console.print(f"[green]Done[/green] {created.html_url}")
        else:
            console.print("[yellow]DRY-RUN complete for this issue[/yellow]")

    console.print("[green]All done.[/green]")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except GhAutomationError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
