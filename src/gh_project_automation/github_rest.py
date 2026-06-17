from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .duplicates import normalize_issue_title
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
            resp = requests.post(
                url,
                json={"title": title, "body": body},
                headers=self._headers(),
                timeout=30,
            )
            if resp.status_code >= 400:
                raise ApiError(f"REST HTTP {resp.status_code}: {resp.text}")
            return resp.json()

        return retry(_do, retry_on=(requests.RequestException, ApiError))

    def update_issue(
        self,
        *,
        owner: str,
        repo: str,
        number: int,
        title: str,
        body: str,
    ) -> dict[str, Any]:
        url = f"{self.api_base}/repos/{owner}/{repo}/issues/{number}"

        def _do() -> dict[str, Any]:
            resp = requests.patch(
                url,
                json={"title": title, "body": body},
                headers=self._headers(),
                timeout=30,
            )
            if resp.status_code >= 400:
                raise ApiError(f"REST HTTP {resp.status_code}: {resp.text}")
            return resp.json()

        return retry(_do, retry_on=(requests.RequestException, ApiError))

    def find_issue_by_title(
        self,
        *,
        owner: str,
        repo: str,
        title: str,
        state: str = "open",
        max_pages: int = 10,
    ) -> dict[str, Any] | None:
        """Find an existing issue by exact normalized title.

        Pull requests are returned by GitHub's issues endpoint, so they are
        explicitly ignored.
        """
        url = f"{self.api_base}/repos/{owner}/{repo}/issues"
        target = normalize_issue_title(title)

        def _fetch_page(page: int) -> list[dict[str, Any]]:
            resp = requests.get(
                url,
                params={"state": state, "per_page": 100, "page": page},
                headers=self._headers(),
                timeout=30,
            )
            if resp.status_code >= 400:
                raise ApiError(f"REST HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            if not isinstance(data, list):
                raise ApiError("REST issues response was not a list")
            return data

        for page in range(1, max_pages + 1):
            issues = retry(
                lambda page=page: _fetch_page(page),
                retry_on=(requests.RequestException, ApiError),
            )
            for issue in issues:
                if "pull_request" in issue:
                    continue
                if normalize_issue_title(str(issue.get("title", ""))) == target:
                    return issue

            if len(issues) < 100:
                break

        return None
