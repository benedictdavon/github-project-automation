from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from gh_project_automation.config import load_config
from gh_project_automation.graphql_client import GraphQLClient

# NOTE:
# This script fetches field IDs + single-select option IDs from a Project v2.
# It writes a fields.json compatible with the CLI validator.

PROJECT_FIELDS_QUERY = """
query ProjectFields($projectId: ID!) {
  node(id: $projectId) {
    ... on ProjectV2 {
      fields(first: 50) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id
            name
            options {
              id
              name
            }
          }
        }
      }
    }
  }
}
"""


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fetch Project v2 field metadata into fields.json")
    p.add_argument("--out", default="data/fields.json", help="Output path")
    p.add_argument("--dotenv", default=None, help="Optional .env path")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_dotenv(dotenv_path=args.dotenv)
    cfg = load_config(dotenv_path=args.dotenv)

    gql = GraphQLClient(token=cfg.token, api_base=cfg.api_base)
    data = gql.query(PROJECT_FIELDS_QUERY, {"projectId": cfg.project_id})

    node = data["node"]
    fields = node["fields"]["nodes"] if node else []

    out: dict[str, Any] = {}
    for f in fields:
        # only single-select fields are returned by this query fragment
        name = f["name"]
        out[name] = {
            "id": f["id"],
            "options": {opt["name"]: opt["id"] for opt in (f.get("options") or [])},
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path} with {len(out)} fields.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
