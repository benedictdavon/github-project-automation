from __future__ import annotations

from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

from .utils import ConfigError


@dataclass(frozen=True)
class Config:
    token: str
    owner: str
    repo: str
    project_id: str
    api_base: str = "https://api.github.com"


def load_config(*, dotenv_path: str | None = None) -> Config:
    """Load config from environment variables (optionally reading .env)."""
    load_dotenv(dotenv_path=dotenv_path)

    token = getenv("GITHUB_TOKEN", "").strip()
    owner = getenv("GITHUB_OWNER", "").strip()
    repo = getenv("GITHUB_REPO", "").strip()
    project_id = getenv("GITHUB_PROJECT_ID", "").strip()
    api_base = getenv("GITHUB_API_BASE", "https://api.github.com").strip()

    missing = [k for k, v in {
        "GITHUB_TOKEN": token,
        "GITHUB_OWNER": owner,
        "GITHUB_REPO": repo,
        "GITHUB_PROJECT_ID": project_id,
    }.items() if not v]

    if missing:
        raise ConfigError(f"Missing required config: {', '.join(missing)}")

    return Config(token=token, owner=owner, repo=repo, project_id=project_id, api_base=api_base)
