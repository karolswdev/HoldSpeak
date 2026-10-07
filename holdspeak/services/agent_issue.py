"""A Room issue as an item a coding agent can take (Conductor R4).

The Room reads issues from its Watches (a Jira ``issues`` Watch; a GitHub
Watch whose ``query_kind`` is ``issues``). An issue is not a desk object,
so its item id names the Watch and the entity: ``<watch_id>.<entity_id>``
(``issue:w_ledger.PAY-418``). The id holds no ``:``, so it is also a valid
story ref and branch slug.

The snapshot holds the title, labels, status and URL. The body
(description) is not in a snapshot: it is read once, at brief time, with
the same read-only CLI the Watch uses (``gh issue view``, ``acli jira
workitem view``). A failed read is named in the brief; it never refuses
the hand-off. Nothing is written to GitHub or Jira.
"""
from __future__ import annotations

import json
import subprocess
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("agent_issue")

ISSUE_KIND = "issue"
#: The Watch kinds whose entities are issues.
ISSUE_WATCHES = frozenset({("jira", "issues"), ("gh", "issues"), ("github", "issues")})
#: The longest body the brief carries (the brief cap still applies).
BODY_MAX_CHARS = 8_000


def issue_item_id(watch_id: str, entity_id: str) -> str:
    return f"{watch_id}.{entity_id}"


def split_issue_id(item_id: str) -> Optional[tuple[str, str]]:
    """``"<watch_id>.<entity_id>"`` -> ``(watch_id, entity_id)``. The entity
    is after the LAST dot (a Jira key and a GitHub number hold none)."""
    watch_id, dot, entity_id = str(item_id or "").rpartition(".")
    if not dot or not watch_id or not entity_id:
        return None
    return watch_id, entity_id


def _entities(snapshot: Any) -> dict[str, dict[str, Any]]:
    if isinstance(snapshot, dict):
        entities = snapshot.get("entities")
        if isinstance(entities, dict):
            return {str(k): v for k, v in entities.items() if isinstance(v, dict)}
        snapshot = entities
    if isinstance(snapshot, list):
        out: dict[str, dict[str, Any]] = {}
        for entity in snapshot:
            if isinstance(entity, dict):
                key = str(entity.get("id") or entity.get("key") or entity.get("number") or "")
                if key:
                    out[key] = entity
        return out
    return {}


def read_issue(db: Any, item_id: str) -> Optional[dict[str, Any]]:
    """The issue an item id names, from its Watch's stored snapshot, or
    ``None`` (no such Watch, not an issue Watch, or no such entity)."""
    parts = split_issue_id(item_id)
    if parts is None:
        return None
    watch_id, entity_id = parts
    with db._connection() as conn:
        row = conn.execute(
            "SELECT id, connector_id, query_kind, name, query_json, snapshot_json, project_id "
            "FROM connector_watches WHERE id = ?",
            (watch_id,),
        ).fetchone()
    if row is None or (str(row["connector_id"]), str(row["query_kind"])) not in ISSUE_WATCHES:
        return None
    try:
        snapshot = json.loads(row["snapshot_json"] or "{}")
        query = json.loads(row["query_json"] or "{}")
    except (TypeError, ValueError):
        return None
    entity = _entities(snapshot).get(entity_id)
    if entity is None:
        return None
    connector = "jira" if row["connector_id"] == "jira" else "gh"
    key = str(entity.get("key") or entity.get("number") or entity.get("id") or entity_id)
    labels = entity.get("labels") if isinstance(entity.get("labels"), list) else []
    return {
        "item_id": item_id,
        "watch_id": watch_id,
        "watch_name": str(row["name"] or ""),
        "connector": connector,
        "key": key,
        "title": " ".join(str(entity.get("title") or entity.get("summary") or "").split()) or "Untitled",
        "url": str(entity.get("url") or ""),
        "labels": [str(label.get("name") if isinstance(label, dict) else label) for label in labels],
        "status": str(entity.get("status") or entity.get("state") or ""),
        "issue_type": str(entity.get("issue_type") or ""),
        "due_at": str(entity.get("due_at") or ""),
        "project_id": str(row["project_id"] or "") or None,
        "repository": str((query or {}).get("repository") or ""),
        "connection_ref": str((query or {}).get("connection_ref") or ""),
    }


def issue_label(issue: Mapping[str, Any]) -> str:
    """``#418 Title`` (GitHub) or ``PAY-418 Title`` (Jira): the Room row's own words."""
    key = str(issue.get("key") or "")
    marker = f"#{key}" if issue.get("connector") == "gh" and key.isdigit() else key
    return f"{marker} {issue.get('title') or ''}".strip()


def tracker_host(issue: Mapping[str, Any]) -> str:
    """The host an issue's body is read from: the Jira site, or github.com."""
    if issue.get("connector") == "jira":
        site = str(issue.get("connection_ref") or "").split("|", 1)[0].strip().lower()
        if site:
            return site
    from urllib.parse import urlsplit

    return (urlsplit(str(issue.get("url") or "")).hostname or "github.com").lower()


# ── the body, read once at brief time ────────────────────────────────

def _adf_text(node: Any) -> str:
    """Plain text of an Atlassian document (``description`` in ADF), or
    the string itself."""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_adf_text(child) for child in node)
    if not isinstance(node, dict):
        return ""
    if node.get("type") == "text":
        return str(node.get("text") or "")
    if node.get("type") == "hardBreak":
        return "\n"
    inner = _adf_text(node.get("content") or [])
    if node.get("type") in {"paragraph", "heading", "listItem", "codeBlock", "blockquote"}:
        return inner.rstrip("\n") + "\n"
    return inner


def _gh_body(principal: Any, issue: Mapping[str, Any], runner: Optional[Callable[..., Any]]) -> tuple[str, str]:
    from ..connector_packs import github_cli
    from ..connector_runtime import PermissionGate

    repository, key = str(issue.get("repository") or ""), str(issue.get("key") or "")
    if "/" not in repository or not key.isdigit():
        return "", "body_not_read"
    command = ["gh", "issue", "view", key, "--repo", repository, "--json", "body,labels,title,url"]
    if not github_cli.is_command_allowed(command):
        return "", "body_not_read"
    try:
        completed = PermissionGate(github_cli.MANIFEST).run_read_subprocess(
            command, principal=principal, runner=runner,
            stdin=subprocess.DEVNULL, capture_output=True, text=True,
            errors="replace", timeout=github_cli.DEFAULT_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # gh missing, denied, timed out
        log.info("issue body not read (%s)", type(exc).__name__)
        return "", "body_not_read"
    if completed.returncode != 0:
        return "", "body_not_read"
    try:
        data = json.loads(completed.stdout or "{}")
    except ValueError:
        return "", "body_not_read"
    return str((data or {}).get("body") or ""), "read"


def _jira_body(principal: Any, issue: Mapping[str, Any], adapter: Any) -> tuple[str, str]:
    connection_ref, key = str(issue.get("connection_ref") or ""), str(issue.get("key") or "")
    if "|" not in connection_ref or not key:
        return "", "body_not_read"
    if adapter is None:
        from ..db import get_database
        from .jira_provider import JiraProviderAdapter

        adapter = JiraProviderAdapter(db=get_database())
    try:
        result = adapter.view_description(principal, connection_ref, key)
    except Exception as exc:
        log.info("issue description not read (%s)", type(exc).__name__)
        return "", "body_not_read"
    if not isinstance(result, Mapping) or result.get("state") != "ready":
        return "", "body_not_read"
    # No People cut here: launched agents may read People information
    # (owner ruling 2026-10-06; lane R7 owns the brief's People handling).
    return _adf_text(result.get("description")).strip(), "read"


def issue_body(
    principal: Any,
    issue: Mapping[str, Any],
    *,
    gh_runner: Optional[Callable[..., Any]] = None,
    jira_adapter: Any = None,
) -> tuple[str, str]:
    """``(body, state)``: state is ``read`` or ``body_not_read``."""
    if issue.get("connector") == "jira":
        body, state = _jira_body(principal, issue, jira_adapter)
    else:
        body, state = _gh_body(principal, issue, gh_runner)
    if len(body) > BODY_MAX_CHARS:
        body = body[:BODY_MAX_CHARS] + f"\n[body cut at {BODY_MAX_CHARS} characters]"
    return body, state


def issue_text(issue: Mapping[str, Any], body: str, body_state: str) -> str:
    """The issue as the brief's item part."""
    lines = [f"Issue: {issue_label(issue)}"]
    if issue.get("url"):
        lines.append(f"URL: {issue['url']}")
    tracker = "Jira" if issue.get("connector") == "jira" else "GitHub"
    lines.append(f"Tracker: {tracker}; Room watch: {issue.get('watch_name') or issue.get('watch_id')}")
    if issue.get("status"):
        lines.append(f"Status: {issue['status']}")
    if issue.get("issue_type"):
        lines.append(f"Type: {issue['issue_type']}")
    if issue.get("due_at"):
        lines.append(f"Due: {issue['due_at']}")
    lines.append("Labels: " + (", ".join(issue.get("labels") or []) or "none"))
    lines.append("")
    if body_state == "read" and body.strip():
        lines += ["Body:", body.strip()]
    elif body_state == "read":
        lines.append("Body: empty")
    else:
        lines.append("Body: not read (the tracker did not answer). Open the URL to read it.")
    return "\n".join(lines)


__all__ = [
    "ISSUE_KIND",
    "issue_body",
    "issue_item_id",
    "issue_label",
    "issue_text",
    "read_issue",
    "split_issue_id",
    "tracker_host",
]
