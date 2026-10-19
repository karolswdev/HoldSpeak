"""Today's page-shaped read over the existing desk producers."""
from __future__ import annotations
import datetime
from dataclasses import asdict
from typing import Any
from holdspeak import operations
from holdspeak.principals import Principal
from holdspeak.services.monday_brief_service import brief_period_label, brief_title
from holdspeak.services.workbench_service import WorkbenchService


class TodayService:
    def __init__(self, db: Any) -> None:
        self._db = db

    def get(self, principal: Principal, *, ops: operations.OperationRegistry,
            door_service: Any, workbenches: WorkbenchService) -> dict[str, Any]:
        return _today_read(ops=ops, workbenches=workbenches, db=self._db,
                           principal=principal, door_service=door_service)


def _today_brief(ops: operations.OperationRegistry, db: Any, principal: Principal) -> dict[str, Any] | None:
    """Read the same ensured brief that the Today face places in Since yesterday."""
    service = ops.target("brief.latest")
    brief = ops.invoke(principal, "brief.latest", {})
    try:
        stale = bool(service.is_stale(brief)) if brief is not None else True
    except Exception:
        stale = False
    if brief is None or stale:
        brief = ops.invoke(principal, "brief.generate", {})
    if brief is None:
        return None
    try:
        stale = bool(service.is_stale(brief))
    except Exception:
        stale = False
    result = asdict(brief)
    result["period_label"] = brief_period_label(result.get("period_start"), result.get("period_end"))
    generated_at = result.get("generated_at")
    result["generated_label"] = None
    if generated_at:
        try:
            stamp = datetime.datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
            months = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
            result["generated_label"] = f"GENERATED {months[stamp.month - 1]} {stamp.day:02d} {stamp.hour:02d}:{stamp.minute:02d}"
        except (TypeError, ValueError):
            pass
    result["title"] = brief_title(result.get("period_end"))
    result["stale"] = stale
    return result


def _today_read(
    *,
    ops: operations.OperationRegistry,
    workbenches: WorkbenchService,
    db: Any,
    principal: Principal,
    door_service: Any,
) -> dict[str, Any]:
    """Compose Today from the same production reads as the web face."""
    door = door_service.get(principal)
    meeting_read = ops.invoke(principal, "meeting.list", {"limit": 40})
    needs = ops.invoke(
        principal,
        "desk.needs_you",
        {},
        held={
            "door_upcoming": getattr(door_service, "_upcoming", None),
        },
    )
    top = dict(needs)
    today = datetime.datetime.now(datetime.timezone.utc).astimezone().date().isoformat()
    top_items = []
    for item in list(needs.get("items") or []):
        # Today hides a future-due ``theirs`` row while the full Needs-you
        # read keeps it available to the drawer.  Keep this as a small
        # presentation projection over the service's ranked answer.
        if item.get("direction") == "theirs":
            due = str(item.get("dueAt") or item.get("due") or "")[:10]
            if len(due) != 10 or due > today:
                continue
        top_items.append(item)
        if len(top_items) == 5:
            break
    top["items"] = top_items
    # ``top`` names the projection explicitly for clients while ``items``
    # remains the familiar Needs-you wire field used by the face.
    top["top"] = list(top["items"])
    day = dict(door or {})
    day["meetings"] = list((meeting_read or {}).get("meetings") or [])
    if isinstance(meeting_read, dict) and "total" in meeting_read:
        day["meeting_total"] = meeting_read["total"]
    return {
        "needs_you": top,
        "day": day,
        "since_yesterday": _today_brief(ops, db, principal),
        "prepared": workbenches.prepared_for_today(principal),
    }


