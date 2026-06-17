# GitHub Project Automation

CLI tool for turning structured JSON backlog items into GitHub issues and
GitHub Project v2 single-select field updates.

It is designed for safe project bootstrapping: dry-run is the default, so you
can validate issue JSON and field metadata before any GitHub mutation happens.

## What It Does

- Validates a list of issue definitions from JSON.
- Creates GitHub issues through the REST API.
- Adds created issues to a GitHub Project v2 board through GraphQL.
- Sets Project v2 single-select fields such as release, phase, priority, risk,
  type, effort, area, and status.
- Uses cached Project field metadata so field IDs and option IDs are not
  hard-coded in business logic.

## Why This Exists

GitHub Project v2 automation requires both APIs:

- REST API: straightforward issue creation.
- GraphQL API: Project v2 item creation and field-value mutation.

This package hides that split behind a small CLI workflow:

```text
issues.json + fields.json -> validate -> create issue -> add to project -> set fields
```

## Install

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

After installation, use either command style:

```bash
gh-project-automation --help
python -m gh_project_automation.cli --help
```

## Quick Dry-Run

This command works without a GitHub token:

```bash
gh-project-automation --issues data/issues_example.json --fields data/fields_example.json
```

Expected behavior:

- validates every issue object
- detects duplicate titles inside the input file
- verifies each field value exists in `fields_example.json`
- prints a preview table
- exits without calling GitHub APIs

## Execute Against GitHub

Copy the environment template and fill in real values:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Required values:

```text
GITHUB_TOKEN=github_pat_...
GITHUB_OWNER=your-org-or-username
GITHUB_REPO=target-repository
GITHUB_PROJECT_ID=project-v2-node-id
```

Fetch real Project v2 field IDs and option IDs:

```bash
python scripts/fetch_project_metadata.py --out data/fields.json
```

Then execute:

```bash
gh-project-automation --issues data/issues_example.json --fields data/fields.json --execute
```

## Duplicate Detection

Duplicate detection and upsert use normalized exact title matching. Whitespace
and case differences are ignored, so `Create setup docs` and
`create   setup docs` are treated as the same title.

The default policy is conservative:

```bash
gh-project-automation --issues data/issues_example.json --fields data/fields.json --execute
```

With the default `--duplicate-policy fail`, the CLI fails when:

- the input JSON contains repeated issue titles
- execution mode finds an existing open GitHub issue with the same title

For repeated batch runs where existing issues should be ignored:

```bash
gh-project-automation \
  --issues data/issues_example.json \
  --fields data/fields.json \
  --duplicate-policy skip \
  --execute
```

To update/reuse existing open issues instead of creating duplicates:

```bash
gh-project-automation \
  --issues data/issues_example.json \
  --fields data/fields.json \
  --duplicate-policy upsert \
  --execute
```

Upsert behavior:

- If no open issue with the same normalized title exists, create a new issue.
- If an open issue exists, update its title and body from JSON.
- If the issue is already in the target Project, reuse that Project item.
- If the issue is not in the target Project, add it.
- Always set Project field values from the JSON payload.

To restore the old behavior and always create new issues:

```bash
gh-project-automation \
  --issues data/issues_example.json \
  --fields data/fields.json \
  --duplicate-policy allow \
  --execute
```

Dry-run checks duplicates inside the input file only. Remote duplicate and
upsert checks require GitHub API access and therefore run only with `--execute`.

To try local duplicate detection without editing files:

```bash
gh-project-automation --issues data/issues_duplicates_example.json --fields data/fields_example.json
```

Then compare with:

```bash
gh-project-automation \
  --issues data/issues_duplicates_example.json \
  --fields data/fields_example.json \
  --duplicate-policy skip
```

### Local Duplicate Inputs

`--duplicate-policy upsert` still fails when the input JSON itself contains
duplicate titles. Two records with the same title would conflict about which
body and fields are the desired final state.

Current upsert matching only checks open issues by normalized title. A future
external-key field would be safer for long-lived production workflows.

## Input Format

Each issue must include:

```json
{
  "title": "[P1][Docs] Add repository setup guide",
  "description": "Markdown issue body",
  "status": "Backlog",
  "release": "MVP",
  "phase": "P1 - Scaffolding & DX",
  "area": "Docs",
  "priority": "P0 - Must Ship",
  "risk": "Low",
  "type": "Chore",
  "effort": "S - <= 1 day"
}
```

The values must match the option labels in the fields metadata file.

## Field Metadata Format

`fields.json` maps Project field names to GitHub node IDs and option IDs:

```json
{
  "Status": {
    "id": "PROJECT_FIELD_ID",
    "options": {
      "Backlog": "OPTION_ID"
    }
  }
}
```

Generate a starter template:

```bash
python scripts/bootstrap_fields_cache.py --out data/fields_example.json
```

Fetch real metadata from a configured project:

```bash
python scripts/fetch_project_metadata.py --out data/fields.json
```

## Architecture

```text
src/gh_project_automation/
  cli.py                  # CLI orchestration and safe dry-run behavior
  config.py               # Environment config loading
  validator.py            # Issue JSON validation
  project_fields.py       # Field metadata parsing and canonical field names
  github_rest.py          # REST API client for issue creation
  graphql_client.py       # GraphQL client for Project v2 operations
  issue_creator.py        # Issue creation workflow
  project_item_manager.py # Project item and field update workflow
  utils.py                # Shared errors, retry, and console
```

The boundary is intentional: validation and dry-run work without API clients,
while execution mode initializes GitHub clients only after inputs are valid.

## Development

```bash
python -m pytest
ruff check .
python -m compileall src scripts tests
```

The tests cover:

- valid issue payloads
- missing required keys
- invalid field options
- malformed issue/field metadata files
- dry-run without GitHub credentials
- execute mode failing cleanly when required config is missing
- duplicate title detection and upsert primitives

## Safety Notes

- Dry-run is the default.
- `--execute` is required for mutations.
- Secrets belong in `.env`, which is ignored by Git.
- Project field IDs are loaded from metadata, not hard-coded.
- API calls use a small retry wrapper for transient failures.

## Roadmap

- Add labels and assignees.
- Support duplicate matching by stable external key, not only title.
- Support multiple field types beyond single-select.
- Add a `--json` output mode for CI logs.
