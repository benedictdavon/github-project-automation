from __future__ import annotations

import argparse
import json
from pathlib import Path

# Minimal bootstrap file you can edit by hand if you don't want to fetch yet.

DEFAULT = {
  "Release": {"id": "FIELD_ID", "options": {"MVP": "OPTION_ID"}},
  "Phase": {"id": "FIELD_ID", "options": {"P1 — Scaffolding & DX": "OPTION_ID"}},
  "Area": {"id": "FIELD_ID", "options": {"API (FastAPI)": "OPTION_ID"}},
  "Priority": {"id": "FIELD_ID", "options": {"P0 — Must Ship": "OPTION_ID"}},
  "Risk": {"id": "FIELD_ID", "options": {"Low": "OPTION_ID"}},
  "Type": {"id": "FIELD_ID", "options": {"Feature": "OPTION_ID"}},
  "Effort": {"id": "FIELD_ID", "options": {"M — 2–3 days": "OPTION_ID"}},
  "Status": {"id": "FIELD_ID", "options": {"Backlog": "OPTION_ID"}},
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Create a starter fields.json template")
    p.add_argument("--out", default="data/fields_example.json", help="Output path")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(DEFAULT, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
