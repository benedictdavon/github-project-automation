from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .utils import ApiError, retry


@dataclass(frozen=True)
class GitHubREST:
    token: str
    api_base: str = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }

    def create_issue(self, *, owner: str, repo: str, title: str, body: str) -> dict[str, Any]:
        url = f"{self.api_base}/repos/{owner}/{repo}/issues"

        def _do() -> dict[str, Any]:
            resp = requests.post(url, json={"title": title, "body": body}, headers=self._headers(), timeout=30)
            if resp.status_code >= 400:
                raise ApiError(f"REST HTTP {resp.status_code}: {resp.text}")
            return resp.json()

        return retry(_do, retry_on=(requests.RequestException, ApiError))
