"""Deterministic work-entity extraction from browser history metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import unquote, urlsplit

JIRA_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b")
NOTION_PAGE_ID_RE = re.compile(r"([0-9a-fA-F]{32}|[0-9a-fA-F-]{36})$")


@dataclass(frozen=True)
class ActivityEntity:
    """Stable work-object identity extracted from a URL/title pair."""

    entity_type: str
    entity_id: str
    label: str
    domain: str


def extract_activity_entity(url: str, title: Optional[str] = None) -> ActivityEntity:
    """Extract a deterministic work entity, falling back to the URL domain."""
    parsed = urlsplit(str(url or "").strip())
    domain = (parsed.hostname or "").lower()
    path_parts = [unquote(part) for part in parsed.path.split("/") if part]

    extractor_result = (
        _extract_github(domain, path_parts)
        or _extract_miro(domain, path_parts)
        or _extract_jira(domain, path_parts, title)
        or _extract_linear(domain, path_parts)
        or _extract_confluence(domain, path_parts)
        or _extract_google(domain, path_parts)
        or _extract_notion(domain, path_parts)
    )
    if extractor_result is not None:
        return extractor_result
    return ActivityEntity(
        entity_type="domain",
        entity_id=domain or "unknown",
        label=domain or str(url or "").strip(),
        domain=domain,
    )


def _extract_github(domain: str, parts: list[str]) -> Optional[ActivityEntity]:
    if domain != "github.com" or len(parts) < 4:
        return None
    owner, repo, kind, number = parts[0], parts[1], parts[2], parts[3]
    if not number.isdigit():
        return None
    repo_ref = f"{owner}/{repo}#{number}"
    if kind == "pull":
        return ActivityEntity("github_pull_request", repo_ref, f"{owner}/{repo} PR #{number}", domain)
    if kind == "issues":
        return ActivityEntity("github_issue", repo_ref, f"{owner}/{repo} issue #{number}", domain)
    return None


def _extract_miro(domain: str, parts: list[str]) -> Optional[ActivityEntity]:
    if not domain.endswith("miro.com") or len(parts) < 3:
        return None
    if parts[0] == "app" and parts[1] == "board" and parts[2]:
        board_id = parts[2].strip("/")
        return ActivityEntity("miro_board", board_id, f"Miro board {board_id}", domain)
    return None


def _extract_jira(domain: str, parts: list[str], title: Optional[str]) -> Optional[ActivityEntity]:
    if not ("atlassian.net" in domain or "jira" in domain):
        return None
    path_text = " ".join(parts)
    match = JIRA_KEY_RE.search(path_text)
    if match is None and title:
        match = JIRA_KEY_RE.search(title.upper())
    if match is None:
        return None
    key = match.group(1).upper()
    return ActivityEntity("jira_ticket", key, key, domain)


def _extract_linear(domain: str, parts: list[str]) -> Optional[ActivityEntity]:
    if domain != "linear.app" or len(parts) < 3:
        return None
    workspace = parts[0]
    if parts[1] != "issue":
        return None
    key_match = JIRA_KEY_RE.search(parts[2].upper())
    if key_match is None:
        return None
    key = key_match.group(1).upper()
    return ActivityEntity("linear_issue", f"{workspace}/{key}", key, domain)


def _extract_confluence(domain: str, parts: list[str]) -> Optional[ActivityEntity]:
    if "atlassian.net" not in domain and "confluence" not in domain:
        return None
    try:
        spaces_index = parts.index("spaces")
        pages_index = parts.index("pages")
    except ValueError:
        return None
    if pages_index <= spaces_index or pages_index + 1 >= len(parts):
        return None
    space = parts[spaces_index + 1]
    page_id = parts[pages_index + 1]
    if not space or not page_id:
        return None
    return ActivityEntity("confluence_page", f"{domain}/{space}/{page_id}", f"{space} page {page_id}", domain)


def _extract_google(domain: str, parts: list[str]) -> Optional[ActivityEntity]:
    if domain == "docs.google.com" and len(parts) >= 3 and parts[2]:
        google_types = {
            "document": ("google_doc", "Google doc"),
            "spreadsheets": ("google_sheet", "Google sheet"),
            "presentation": ("google_slide", "Google slide"),
        }
        mapped = google_types.get(parts[0])
        if mapped and parts[1] == "d":
            entity_type, label_prefix = mapped
            return ActivityEntity(entity_type, parts[2], f"{label_prefix} {parts[2]}", domain)
    if domain == "drive.google.com" and len(parts) >= 3 and parts[0] == "file" and parts[1] == "d":
        return ActivityEntity("google_drive_file", parts[2], f"Drive file {parts[2]}", domain)
    return None


def _extract_notion(domain: str, parts: list[str]) -> Optional[ActivityEntity]:
    if not domain.endswith("notion.so") or not parts:
        return None
    last_part = parts[-1].split("?")[0]
    match = NOTION_PAGE_ID_RE.search(last_part)
    if match is None:
        return None
    page_id = match.group(1).replace("-", "").lower()
    return ActivityEntity("notion_page", page_id, f"Notion page {page_id}", domain)
