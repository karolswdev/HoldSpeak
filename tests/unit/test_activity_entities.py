"""Unit tests for local activity entity extractors."""

from __future__ import annotations

import pytest

from holdspeak.activity_entities import extract_activity_entity


@pytest.mark.parametrize(
    ("url", "title", "entity_type", "entity_id"),
    [
        (
            "https://example.atlassian.net/browse/HS-804",
            "Activity work",
            "jira_ticket",
            "HS-804",
        ),
        (
            "https://example.atlassian.net/jira/software/c/projects/HS/boards/1?selectedIssue=HS-805",
            "HS-805: Extract from title fallback",
            "jira_ticket",
            "HS-805",
        ),
        (
            "https://miro.com/app/board/uXjVTestBoard=/",
            None,
            "miro_board",
            "uXjVTestBoard=",
        ),
        (
            "https://github.com/openai/codex/pull/42/files",
            None,
            "github_pull_request",
            "openai/codex#42",
        ),
        (
            "https://github.com/openai/codex/issues/99",
            None,
            "github_issue",
            "openai/codex#99",
        ),
        (
            "https://linear.app/acme/issue/ENG-123/ship-it",
            None,
            "linear_issue",
            "acme/ENG-123",
        ),
        (
            "https://example.atlassian.net/wiki/spaces/ENG/pages/123456789/Architecture",
            None,
            "confluence_page",
            "example.atlassian.net/ENG/123456789",
        ),
        (
            "https://docs.google.com/document/d/doc-id-123/edit",
            None,
            "google_doc",
            "doc-id-123",
        ),
        (
            "https://docs.google.com/spreadsheets/d/sheet-id-123/edit",
            None,
            "google_sheet",
            "sheet-id-123",
        ),
        (
            "https://drive.google.com/file/d/drive-file-123/view",
            None,
            "google_drive_file",
            "drive-file-123",
        ),
        (
            "https://www.notion.so/acme/Project-Plan-0123456789abcdef0123456789abcdef",
            None,
            "notion_page",
            "0123456789abcdef0123456789abcdef",
        ),
    ],
)
def test_extract_activity_entity_known_work_urls(url, title, entity_type, entity_id):
    entity = extract_activity_entity(url, title=title)

    assert entity.entity_type == entity_type
    assert entity.entity_id == entity_id


def test_jira_title_fallback_requires_jira_or_atlassian_domain():
    entity = extract_activity_entity(
        "https://example.com/release-notes",
        title="Mentions HS-804 but is not a Jira surface",
    )

    assert entity.entity_type == "domain"
    assert entity.entity_id == "example.com"


def test_unknown_url_falls_back_to_generic_domain_entity():
    entity = extract_activity_entity("https://docs.example.com/handbook/page")

    assert entity.entity_type == "domain"
    assert entity.entity_id == "docs.example.com"
    assert entity.label == "docs.example.com"
