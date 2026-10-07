"""PHILO-15 04 (gap 14): the Parked drawer's one read.

Parked is a drawer of objects (the Phase 14 charter). Each kind keeps its own
park and its own restore; this module only composes the existing per-kind
reads into one collection, so the drawer needs one hub read:

* meetings: ``MeetingService.list_meetings(parked=True)``;
* Workbench items: ``WorkbenchService.get_workbench(parked=True)`` per bench;
* Projects: ``ProjectService.list_projects(include_archived=True)``, archived only.

No new table and no write. A kind whose read fails is named in ``not_read``,
never shown as an empty kind (UX-CANON A.10).
"""
from __future__ import annotations

from typing import Any, Callable

from ..logging_config import get_logger

log = get_logger("services.parked")

#: The kinds, in the order the drawer reads them.
PARKED_KINDS = ("meeting", "workbench_item", "project")


def _iso(value: Any) -> str:
    if value is None:
        return ""
    iso = getattr(value, "isoformat", None)
    return str(iso() if callable(iso) else value)


def _meetings(meeting_service: Any, principal: Any) -> list[dict[str, Any]]:
    answer = meeting_service.list_meetings(principal, parked=True, limit=500)
    rows = answer.get("meetings", []) if isinstance(answer, dict) else answer
    out = []
    for m in rows:
        row = m if isinstance(m, dict) else m.to_dict()
        out.append({
            "ref": f"meeting:{row['id']}",
            "kind": "meeting",
            "id": str(row["id"]),
            "name": str(row.get("title") or "Meeting"),
            "when": _iso(row.get("started_at")),
            "home": {},
        })
    return out


def _workbench_items(workbench_service: Any, principal: Any) -> list[dict[str, Any]]:
    out = []
    for bench in workbench_service.list_workbenches(principal):
        full = workbench_service.get_workbench(principal, bench["id"], parked=True)
        for item in full.get("items", []):
            out.append({
                "ref": f"workbench_item:{item['id']}",
                "kind": "workbench_item",
                "id": str(item["id"]),
                "name": str(item.get("title") or "Item"),
                "when": _iso(item.get("last_modified") or item.get("created_at")),
                "home": {"workbench_id": str(bench["id"]), "workbench_name": str(bench.get("name") or "")},
            })
    return out


def _projects(project_service: Any, principal: Any) -> list[dict[str, Any]]:
    out = []
    for project in project_service.list_projects(principal, include_archived=True):
        if not project.get("is_archived"):
            continue
        out.append({
            "ref": f"project:{project['id']}",
            "kind": "project",
            "id": str(project["id"]),
            "name": str(project.get("name") or "Project"),
            "when": _iso(project.get("updated_at")),
            "home": {},
        })
    return out


def parked_collection(
    principal: Any,
    *,
    meeting_service: Any,
    workbench_service: Any,
    project_service: Any,
) -> dict[str, Any]:
    """``{items: [{ref, kind, id, name, when, home}], not_read: [kind]}``, newest first."""
    reads: dict[str, Callable[[], list[dict[str, Any]]]] = {
        "meeting": lambda: _meetings(meeting_service, principal),
        "workbench_item": lambda: _workbench_items(workbench_service, principal),
        "project": lambda: _projects(project_service, principal),
    }
    items: list[dict[str, Any]] = []
    not_read: list[str] = []
    for kind in PARKED_KINDS:
        try:
            items.extend(reads[kind]())
        except Exception as exc:  # one kind's failure never hides the others
            log.warning("Parked read failed for %s: %s", kind, exc)
            not_read.append(kind)
    items.sort(key=lambda row: row["when"], reverse=True)
    return {"items": items, "not_read": not_read}
