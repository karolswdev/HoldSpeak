"""Batteries-included Reaction presets; the UI never starts from a blank rule."""
from __future__ import annotations

from typing import Any


AUTOMATION_PRESETS: tuple[dict[str, Any], ...] = (
    {
        "id": "github-review-requested",
        "label": "PR review requested",
        "description": "Prepare one Workbench item when a pull request enters the configured review queue.",
        "connector_id": "gh", "query_kind": "pull_requests",
        "query": {"state": "open", "search": "review-requested:@me",
                  "discovery_event": "github.pr.review_requested", "limit": 50},
        "event_pattern": "github.pr.review_requested",
        "title_template": "Review requested: {entity_title}",
        "default_auto_run": False, "adapter_ready": True,
    },
    {
        "id": "github-checks-failed",
        "label": "PR checks failed",
        "description": "Send newly failing pull requests to an engineering triage Workbench.",
        "connector_id": "gh", "query_kind": "pull_requests",
        "query": {"state": "open", "search": "status:failure",
                  "discovery_event": "github.pr.checks_changed", "limit": 50},
        "event_pattern": "github.pr.checks_changed",
        "title_template": "Checks failed: {entity_title}",
        "default_auto_run": False, "adapter_ready": True,
    },
    {
        "id": "github-pr-merged",
        "label": "PR merged",
        "description": "Prepare release follow-through when a merged PR appears.",
        "connector_id": "gh", "query_kind": "pull_requests",
        "query": {"state": "merged", "discovery_event": "github.pr.merged", "limit": 50},
        "event_pattern": "github.pr.merged",
        "title_template": "Merged: {entity_title}",
        "default_auto_run": False, "adapter_ready": True,
    },
    {
        "id": "jira-assigned-to-me",
        "label": "Jira assigned to me",
        "description": "Prepare assigned issues once a Jira snapshot adapter is configured.",
        "connector_id": "jira", "query_kind": "issues",
        "query": {"jql": "assignee = currentUser() AND resolution = Unresolved",
                  "discovery_event": "jira.issue.assigned", "limit": 50},
        "event_pattern": "jira.issue.assigned",
        "title_template": "Assigned: {entity_title}",
        "default_auto_run": False, "adapter_ready": False,
    },
)


def list_automation_presets() -> list[dict[str, Any]]:
    return [{**preset, "query": dict(preset["query"])} for preset in AUTOMATION_PRESETS]


def get_automation_preset(preset_id: str) -> dict[str, Any] | None:
    return next((preset for preset in list_automation_presets() if preset["id"] == preset_id), None)
