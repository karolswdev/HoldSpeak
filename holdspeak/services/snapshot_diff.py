"""Connector snapshots: normalize one, and diff two into semantic transitions.

One home for the comparison every watch uses (2026-11-08): the Room's
WatchService, project setup, the evidence collector and the Automations
event trigger. It reads and writes nothing.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from holdspeak.services.errors import ValidationError


def _clean_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted({str(item).strip() for item in value if str(item).strip()})


def _normalize_entity(connector_id: str, entity: Any) -> dict[str, Any]:
    if not isinstance(entity, dict):
        raise ValidationError("Every snapshot entity must be an object")
    entity_id = str(entity.get("id") or entity.get("number") or entity.get("key") or "").strip()
    if not entity_id:
        raise ValidationError("Every snapshot entity requires id, number, or key")
    common = {
        "id": entity_id,
        "title": str(entity.get("title") or entity.get("summary") or "").strip(),
        "url": str(entity.get("url") or "").strip(),
        "updated_at": str(entity.get("updated_at") or entity.get("updatedAt") or "").strip(),
    }
    if connector_id == "gh":
        common.update({
            "state": str(entity.get("state") or "").lower(),
            "is_draft": bool(entity.get("is_draft", entity.get("isDraft", False))),
            "review_requests": _clean_strings(
                entity.get("review_requests", entity.get("reviewRequests", []))
            ),
            "review_decision": str(
                entity.get("review_decision", entity.get("reviewDecision", "")) or ""
            ).lower(),
            "checks": str(entity.get("checks") or entity.get("ci") or "").lower(),
            "head_sha": str(entity.get("head_sha") or entity.get("headRefOid") or ""),
            # Conductor K4: the branch, so a merge observation names the
            # branch an agent launch worked on.
            "head_ref": str(entity.get("head_ref") or entity.get("headRefName") or ""),
        })
        if isinstance(entity.get("labels"), list):
            # Conductor R4: a GitHub issue's labels and age (issue Watches only;
            # a PR entity carries no labels key, so its shape is unchanged).
            common["labels"] = sorted(str(label) for label in entity["labels"])
            common["created_at"] = str(entity.get("created_at") or entity.get("createdAt") or "")
    elif connector_id == "jira":
        common.update({
            "status": str(entity.get("status") or "").lower(),
            "status_category": str(entity.get("status_category") or "").lower(),
            "assignee": str(entity.get("assignee") or "").strip(),
            "priority": str(entity.get("priority") or "").lower(),
            "resolution": str(entity.get("resolution") or "").lower(),
            "due_at": str(entity.get("due_at") or entity.get("dueDate") or ""),
            "issue_type": str(entity.get("issue_type") or "").strip(),
            "labels": entity.get("labels", []) if isinstance(entity.get("labels"), list) else [],
            "project_key": str(entity.get("project_key") or "").strip(),
            "status_changed_at": str(entity.get("status_changed_at") or "").strip(),
        })
    elif connector_id == "meeting":
        # HS-175-04: meeting-specific fields for token computation.
        common.update({
            "entity_type": "meeting",
            "date": str(entity.get("date") or ""),
            "participants": entity.get("participants", 0),
            "decisions_count": entity.get("decisions_count", 0),
            "commitments_count": entity.get("commitments_count", 0),
            "intel_status": str(entity.get("intel_status") or "off"),
        })
    return common


def normalize_snapshot(connector_id: str, entities: Any) -> dict[str, Any]:
    if not isinstance(entities, list):
        raise ValidationError("entities must be an array")
    normalized = [_normalize_entity(connector_id, entity) for entity in entities]
    by_id = {entity["id"]: entity for entity in normalized}
    if len(by_id) != len(normalized):
        raise ValidationError("snapshot entity ids must be unique")
    return {"schema": 1, "entities": {key: by_id[key] for key in sorted(by_id)}}


def _revision(entity: dict[str, Any]) -> str:
    material = json.dumps(entity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode()).hexdigest()


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _event(event_type: str, before: dict[str, Any],
           after: dict[str, Any], changed: Any) -> dict[str, Any]:
    entity = after or before
    revision = _revision(after or before)
    return {
        "event_type": event_type,
        "entity_ref": entity["id"],
        "source_revision": revision,
        "facts": {"entity_title": entity.get("title", ""), "url": entity.get("url", ""),
                  "changed": changed,
                  # HS-166-03: carry the current entity so snapshot-level
                  # comparisons (due_within_days, overdue, inactive_for,
                  # older_than, newer_than) can read field values.
                  "current": dict(entity)},
    }


def diff_snapshots(connector_id: str, before: dict[str, Any],
                   after: dict[str, Any], *, discovery_event: str = "",
                   query_kind: str = "") -> list[dict[str, Any]]:
    """Produce semantic transitions. Missing rows are not treated as deletion."""
    old = before.get("entities", {}) if isinstance(before, dict) else {}
    new = after.get("entities", {})
    events: list[dict[str, Any]] = []
    if connector_id == "gh" and query_kind == "issues":
        # Conductor R4: a GitHub issues Watch speaks of issues, never PRs.
        for entity_id, current in new.items():
            previous = old.get(entity_id)
            if previous is None:
                events.append(_event(discovery_event or "github.issue.opened", {}, current, {"entity": "new"}))
            elif previous.get("state") != current.get("state"):
                state = current.get("state")
                kind = "github.issue.closed" if state == "closed" else "github.issue.reopened"
                events.append(_event(kind, previous, current, {"state": [previous.get("state"), state]}))
        return events
    for entity_id, current in new.items():
        previous = old.get(entity_id)
        if previous is None:
            kind = discovery_event or (
                "github.pr.opened" if connector_id == "gh" else "jira.issue.discovered"
            )
            events.append(_event(kind, {}, current, {"entity": "new"}))
            continue
        if connector_id == "gh":
            if previous.get("state") != current.get("state"):
                state = current.get("state")
                kind = "github.pr.merged" if state == "merged" else "github.pr.state_changed"
                events.append(_event(kind, previous, current,
                                     {"state": [previous.get("state"), state]}))
            added = sorted(set(current.get("review_requests", [])) - set(previous.get("review_requests", [])))
            if added:
                events.append(_event("github.pr.review_requested", previous, current,
                                     {"reviewers": added}))
            for field, kind in (
                ("review_decision", "github.pr.review_decision_changed"),
                ("checks", "github.pr.checks_changed"),
                ("head_sha", "github.pr.head_changed"),
            ):
                if previous.get(field) != current.get(field):
                    events.append(_event(kind, previous, current,
                                         {field: [previous.get(field), current.get(field)]}))
        elif connector_id == "meeting":
            # HS-175-04: meeting-specific transitions.
            for field, kind in (
                ("decisions_count", "meeting.decisions_changed"),
                ("commitments_count", "meeting.commitments_changed"),
                ("intel_status", "meeting.intel_status_changed"),
            ):
                if previous.get(field) != current.get(field):
                    events.append(_event(kind, previous, current,
                                         {field: [previous.get(field), current.get(field)]}))
        else:
            for field, kind in (
                ("assignee", "jira.issue.assigned"),
                ("status", "jira.issue.status_changed"),
                ("status_category", "jira.issue.category_changed"),
                ("priority", "jira.issue.priority_changed"),
                ("due_at", "jira.issue.due_changed"),
            ):
                if previous.get(field) != current.get(field):
                    events.append(_event(kind, previous, current,
                                         {field: [previous.get(field), current.get(field)]}))
            if not previous.get("resolution") and current.get("resolution"):
                events.append(_event("jira.issue.resolved", previous, current,
                                     {"resolution": current.get("resolution")}))
    return events
