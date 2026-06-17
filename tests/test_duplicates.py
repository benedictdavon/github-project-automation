from __future__ import annotations

from gh_project_automation.duplicates import find_duplicate_titles, normalize_issue_title


def test_normalize_issue_title_collapses_case_and_whitespace() -> None:
    assert normalize_issue_title(" Create   Setup DOCS ") == "create setup docs"


def test_find_duplicate_titles_reports_original_indices() -> None:
    duplicates = find_duplicate_titles(["Alpha", "Beta", " alpha "])

    assert len(duplicates) == 1
    assert duplicates[0].title == "Alpha"
    assert duplicates[0].first_index == 1
    assert duplicates[0].duplicate_index == 3
