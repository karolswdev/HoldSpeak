"""HS-172-07 — Room People resolver.

Collects distinct owner identities from a Room's Watch snapshot entities,
resolves each through people_service.resolve_relationship_by_watch_identity,
and returns resolved people with per-Room counts. No writes. No raw logins
in the payload (Article III).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .project_service import ProjectService


def _extract_identities(project_service: ProjectService, project_id: str) -> dict[str, dict[str, int]]:
    """Extract distinct identities from Watch entities with per-identity counts.

    Returns {identity: {"prs_waiting": N, "assignments_open": N, "assignments_overdue": N}}.
    GitHub PR entities: reviewRequests (list of logins waiting on review).
    Jira issue entities: assignee field.
    """
    watches = project_service._db.automations.list_project_watches(project_id)
    identities: dict[str, dict[str, int]] = {}
    now = datetime.now(timezone.utc)

    for watch in watches:
        connector_id = watch.get("connector_id", "")
        query_kind = watch.get("query_kind", "")
        snapshot = watch.get("snapshot")
        if not snapshot:
            continue
        entities = ProjectService._entities(snapshot)

        if connector_id == "gh" and query_kind == "pull_requests":
            for entity in entities:
                state = str(entity.get("state", "")).lower()
                if state != "open":
                    continue
                review_requests = (
                    entity.get("review_requests")
                    or entity.get("reviewRequests")
                    or []
                )
                for login in review_requests:
                    login_str = str(login).strip()
                    if not login_str:
                        continue
                    key = login_str.lower()
                    if key not in identities:
                        identities[key] = {
                            "prs_waiting": 0,
                            "assignments_open": 0,
                            "assignments_overdue": 0,
                            "_raw": login_str,
                        }
                    identities[key]["prs_waiting"] += 1

        elif connector_id == "jira" and query_kind == "issues":
            for entity in entities:
                assignee = str(entity.get("assignee") or "").strip()
                if not assignee:
                    continue
                key = assignee.lower()
                if key not in identities:
                    identities[key] = {
                        "prs_waiting": 0,
                        "assignments_open": 0,
                        "assignments_overdue": 0,
                        "_raw": assignee,
                    }
                identities[key]["assignments_open"] += 1

                # Check overdue
                due_at = entity.get("due_at") or entity.get("dueDate")
                if due_at:
                    try:
                        due_str = str(due_at).replace("Z", "+00:00")
                        if "T" in due_str:
                            due_str = due_str.split("T")[0]
                        due_dt = datetime.fromisoformat(due_str)
                        if due_dt.replace(tzinfo=None) < now.replace(tzinfo=None):
                            identities[key]["assignments_overdue"] += 1
                    except (ValueError, TypeError):
                        pass

    return identities


def room_people(
    project_service: ProjectService,
    people_service: Any,
    project_id: str,
) -> list[dict[str, Any]]:
    """Return resolved people for a Room's Watch entities.

    Only RESOLVED identities with at least one non-zero count appear.
    display_name is read from the People store, never the raw login.
    """
    # Ensure project exists (raises NotFound)
    project_service._require_project(project_id)

    identities = _extract_identities(project_service, project_id)
    if not identities or people_service is None:
        return []

    result: list[dict[str, Any]] = []
    for _key, counts in identities.items():
        raw = counts.pop("_raw", _key)
        # Skip if all counts are zero
        if not any(v > 0 for v in counts.values()):
            continue

        resolved = people_service.resolve_relationship_by_watch_identity(raw)
        if not resolved or resolved.get("state") != "ready":
            continue
        relationship = resolved.get("relationship")
        if not relationship:
            continue

        rel_id = relationship.get("id")
        display_name = relationship.get("display_name") or ""
        if not rel_id or not display_name:
            continue

        entry: dict[str, Any] = {
            "relationship_id": rel_id,
            "display_name": display_name,
        }
        if counts.get("prs_waiting", 0) > 0:
            entry["prs_waiting"] = counts["prs_waiting"]
        if counts.get("assignments_open", 0) > 0:
            entry["assignments_open"] = counts["assignments_open"]
        if counts.get("assignments_overdue", 0) > 0:
            entry["assignments_overdue"] = counts["assignments_overdue"]

        # Only include if at least one token is non-zero
        if any(k in entry for k in ("prs_waiting", "assignments_open", "assignments_overdue")):
            result.append(entry)

    # Sort by display_name for stable ordering
    result.sort(key=lambda r: r.get("display_name", "").lower())
    return result
