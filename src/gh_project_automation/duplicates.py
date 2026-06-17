from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

DuplicatePolicy = Literal["fail", "skip", "allow", "upsert"]


@dataclass(frozen=True)
class DuplicateTitle:
    title: str
    first_index: int
    duplicate_index: int


def normalize_issue_title(title: str) -> str:
    """Normalize titles for exact duplicate detection."""
    return " ".join(title.casefold().split())


def find_duplicate_titles(titles: Iterable[str]) -> list[DuplicateTitle]:
    seen: dict[str, tuple[int, str]] = {}
    duplicates: list[DuplicateTitle] = []

    for index, title in enumerate(titles, start=1):
        normalized = normalize_issue_title(title)
        if normalized in seen:
            first_index, first_title = seen[normalized]
            duplicates.append(
                DuplicateTitle(
                    title=first_title,
                    first_index=first_index,
                    duplicate_index=index,
                )
            )
            continue

        seen[normalized] = (index, title)

    return duplicates
