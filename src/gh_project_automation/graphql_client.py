from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .utils import ApiError, retry


@dataclass(frozen=True)
class GraphQLClient:
    token: str
    api_base: str = "https://api.github.com"

    @property
    def endpoint(self) -> str:
        return f"{self.api_base}/graphql"

    def query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        def _do() -> dict[str, Any]:
            resp = requests.post(
                self.endpoint,
                json={"query": query, "variables": variables or {}},
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=30,
            )
            if resp.status_code >= 400:
                raise ApiError(f"GraphQL HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            if "errors" in data and data["errors"]:
                raise ApiError(f"GraphQL errors: {data['errors']}")
            return data["data"]

        return retry(_do, retry_on=(requests.RequestException, ApiError))
