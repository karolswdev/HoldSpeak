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


#: One meeting page, and the most pages one read follows (100,000 meetings).
MEETING_PAGE = 500
MAX_MEETING_PAGES = 200


class PartialRead(Exception):
    """A kind read stopped part way: the rows read so far, and why it stopped."""

    def __init__(self, rows: list[dict[str, Any]], cause: str) -> None:
        super().__init__(cause)
        self.rows = rows


def _meeting_row(m: Any) -> dict[str, Any]:
    row = m if isinstance(m, dict) else m.to_dict()
    return {
        "ref": f"meeting:{row['id']}",
        "kind": "meeting",
        "id": str(row["id"]),
        "name": str(row.get("title") or "Meeting"),
        "when": _iso(row.get("started_at")),
        "home": {},
    }


def _meetings(meeting_service: Any, principal: Any) -> list[dict[str, Any]]:
    """Every parked meeting: each page, by ``next_cursor``, up to the bound."""
    out: list[dict[str, Any]] = []
    cursor: Any = None
    for _page in range(MAX_MEETING_PAGES):
        try:
            answer = meeting_service.list_meetings(principal, parked=True, limit=MEETING_PAGE, cursor=cursor)
        except Exception as exc:
            if out:
                raise PartialRead(out, f"page read failed: {exc}") from exc
            raise
        rows = answer.get("meetings", []) if isinstance(answer, dict) else answer
        out.extend(_meeting_row(m) for m in rows)
        cursor = answer.get("next_cursor") if isinstance(answer, dict) else None
        if not cursor:
            return out
    raise PartialRead(out, "more pages than the bound")


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
    """``{items: [{ref, kind, id, name, when, home}], not_read: [kind], partial: [kind]}``, newest first.

    A kind in ``partial`` is also in ``not_read``: some of its rows are here,
    the rest could not be read (never a silently short list)."""
    reads: dict[str, Callable[[], list[dict[str, Any]]]] = {
        "meeting": lambda: _meetings(meeting_service, principal),
        "workbench_item": lambda: _workbench_items(workbench_service, principal),
        "project": lambda: _projects(project_service, principal),
    }
    items: list[dict[str, Any]] = []
    not_read: list[str] = []
    partial: list[str] = []
    for kind in PARKED_KINDS:
        try:
            items.extend(reads[kind]())
        except PartialRead as exc:
            log.warning("Parked read for %s is partial: %s", kind, exc)
            items.extend(exc.rows)
            not_read.append(kind)
            partial.append(kind)
        except Exception as exc:  # one kind's failure never hides the others
            log.warning("Parked read failed for %s: %s", kind, exc)
            not_read.append(kind)
    items.sort(key=lambda row: row["when"], reverse=True)
    return {"items": items, "not_read": not_read, "partial": partial}
