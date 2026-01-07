# GitHub Project Automation (Issues + Project v2 fields)

A small, reusable Python tool to:
- create GitHub issues from structured JSON (REST API)
- add created issues to a GitHub Project (v2) (GraphQL API)
- set Project custom fields (single-select) using cached field metadata (`fields.json`)
- validate inputs and support safe dry-run by default

## Why GraphQL is required for Project v2
GitHub Project v2 (Projects Next) operations (add item, update field values, query field options) are only
available via the GitHub **GraphQL** API. Issue creation is simplest via the **REST** API.

## Repo structure
This project follows a strict, modular layout under `src/gh_project_automation` and provides scripts to fetch
metadata needed for field updates.

## Setup

### 1) Install
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
```

### 2) Configure environment
Copy `.env.example` → `.env` and fill:
- `GITHUB_TOKEN`
- `GITHUB_OWNER`
- `GITHUB_REPO`
- `GITHUB_PROJECT_ID` (Project v2 node ID)

### 3) Fetch Project + Field IDs
Project item field updates require:
- Project node ID (`GITHUB_PROJECT_ID`)
- Field node IDs
- Option IDs for each single-select value

Use the scripts:
```bash
python scripts/fetch_project_metadata.py --out data/fields.json
# or, if you want a minimal cached file template:
python scripts/bootstrap_fields_cache.py --out data/fields_example.json
```

> Note: `fields.json` maps human-readable values to option IDs.

## Usage (Dry-run is default)
```bash
python -m gh_project_automation.cli   --issues data/issues_example.json   --fields data/fields_example.json   --dry-run
```

To actually mutate GitHub, you must pass `--execute`:
```bash
python -m gh_project_automation.cli   --issues data/issues_example.json   --fields data/fields.json   --execute
```

### Optional flags
- `--limit N` process only the first N issues
- `--dry-run` (default) never calls mutations
- `--execute` performs real API calls

## Input format
See `data/issues_example.json`. Each issue includes:
- `title`
- `description` (markdown body)
- project fields: `release`, `phase`, `area`, `priority`, `risk`, `type`, `effort`, `status`

## Common errors & fixes

### "Missing required config"
Your `.env` is missing one of: `GITHUB_TOKEN`, `GITHUB_OWNER`, `GITHUB_REPO`, `GITHUB_PROJECT_ID`.

### "Invalid option value"
Your issue JSON value doesn't exist in `fields.json` options. Re-run metadata script or fix the value.

### "Field not found in metadata"
Your `fields.json` doesn't include the field name (e.g., `Status`). Ensure the Project field exists and your
metadata file includes it.

## Notes
- This scaffolding includes clean TODOs for real-world extensions (labels, assignees, bulk mode, etc.).
- All IDs are loaded from config or JSON metadata; nothing is hard-coded in business logic.
