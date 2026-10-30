"""Today's page-shaped read over the existing desk producers."""
from __future__ import annotations
import datetime
from dataclasses import asdict
import json
from typing import Any
from holdspeak import operations
from holdspeak.principals import Principal
from holdspeak.timestamps import local_now as wall_clock_now
from holdspeak.services.monday_brief_service import brief_period_label, brief_title
from holdspeak.services.workbench_service import WorkbenchService


class TodayService:
    def __init__(self, db: Any) -> None:
        self._db = db

    def get(self, principal: Principal, *, ops: operations.OperationRegistry,
            door_service: Any, workbenches: WorkbenchService) -> dict[str, Any]:
        return _today_read(ops=ops, workbenches=workbenches, db=self._db,
                           principal=principal, door_service=door_service)

    def since_morning(self, principal: Principal, *, now: datetime.datetime | None = None) -> dict[str, Any]:
        """DELIGHT slice 5: Today's Since this morning (``GET /api/today/since-morning``),
        with the Programs block (PG18: ``ProgramService.since_morning``; ``None``
        when the Programs could not be read, never a count of zero that lies)."""
        read = since_morning_read(self._db, now)
        try:
            from holdspeak.services.program_service import ProgramService

            read["programs"] = ProgramService(self._db).since_morning(principal, now=now)
        except Exception as exc:
            from holdspeak.logging_config import get_logger

            get_logger("today_service").warning(f"programs not read for Since this morning: {exc}")
            read["programs"] = None
        return read


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


# ── DELIGHT slice 5 (2026-10-28): Since this morning ─────────────────────────
# Today in the evening lists what got done today: tasks ticked, decisions
# recorded, notes filed, sends sent, meetings held. Each row names its
# object (a ref the desk opens), a title, one word and the time; newest
# first. Every fact is a row the hub already keeps; this read only gathers
# them for the local day.

#: A note at birth sits in the Inbox; "filed" means it moved out of it.
_INBOX_DIRECTORY_ID = "hs-seed-inbox"
SINCE_MORNING_LIMIT = 30


def _stamp(value: Any) -> datetime.datetime | None:
    """One aware UTC time from the three stamp shapes the tables hold
    (``ProjectionRepository._normalize_timestamp``: a SQLite stamp is UTC, an
    ISO string with an offset is exact, a bare ISO string is local time)."""
    clean = str(value or "").strip()
    if not clean:
        return None
    sqlite_utc = "T" not in clean and " " in clean
    if sqlite_utc:
        clean = clean.replace(" ", "T", 1)
    if clean.endswith("Z"):
        clean = clean[:-1] + "+00:00"
    try:
        at = datetime.datetime.fromisoformat(clean)
    except ValueError:
        return None
    if at.tzinfo is None:
        at = at.replace(tzinfo=datetime.timezone.utc) if sqlite_utc else at.astimezone()
    return at.astimezone(datetime.timezone.utc)


def _first_line(text: Any) -> str:
    for line in str(text or "").splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:120]
    return ""


def since_morning_read(db: Any, now: datetime.datetime | None = None,
                       limit: int = SINCE_MORNING_LIMIT) -> dict[str, Any]:
    """What got done since the local midnight of ``now`` (the hub's clock)."""
    local_now = (now or wall_clock_now()).astimezone()
    morning = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = morning.astimezone(datetime.timezone.utc)
    # A coarse SQL bound (a day before the UTC morning, as a date prefix,
    # works for every stamp shape); the exact cut is made on the parsed time.
    floor = (start - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    items: list[dict[str, Any]] = []

    def add(kind: str, ref: str, title: str, word: str, at_value: Any) -> None:
        at = _stamp(at_value)
        if at is None or at < start or at > local_now.astimezone(datetime.timezone.utc) + datetime.timedelta(minutes=5):
            return
        items.append({"kind": kind, "ref": ref, "title": title, "word": word,
                      "at": at.isoformat(timespec="seconds").replace("+00:00", "Z"), "_at": at})

    def rows(conn: Any, sql: str, *args: Any) -> list[Any]:
        try:
            return conn.execute(sql, (*args, floor)).fetchall()
        except Exception:  # a table this hub does not have yet: no rows
            return []

    with db._connection() as conn:
        for row in rows(conn, """SELECT id, task, completed_at FROM action_items
                                 WHERE status = 'done' AND completed_at >= ?"""):
            add("action", f"action_item:{row['id']}", str(row["task"] or "Task"), "Done", row["completed_at"])
        for row in rows(conn, """SELECT id, decision_text, created_at FROM decision_records
                                 WHERE deleted = 0 AND kind = 'decision' AND created_at >= ?"""):
            add("decision", f"decision_record:{row['id']}", _first_line(row["decision_text"]) or "Decision",
                "Recorded", row["created_at"])
        for row in rows(conn, """SELECT n.id, n.title, n.body_markdown, d.name, m.last_modified
                                 FROM directory_memberships m
                                 JOIN notes n ON m.primitive_id = 'note:' || n.id
                                 LEFT JOIN directories d ON d.id = m.directory_id
                                 WHERE m.deleted = 0 AND n.deleted = 0 AND m.directory_id != ''
                                   AND m.directory_id != ? AND m.last_modified >= ?""", _INBOX_DIRECTORY_ID):
            name = str(row["name"] or "").strip()
            add("note", f"note:{row['id']}", str(row["title"] or "").strip() or _first_line(row["body_markdown"]) or "Note",
                f"Filed in {name}" if name else "Filed", row["last_modified"])
        for row in rows(conn, """SELECT id, document_ref, document_json, settled_at FROM channel_sends
                                 WHERE state = 'sent' AND settled_at >= ?"""):
            try:
                title = str((json.loads(row["document_json"] or "{}") or {}).get("title") or "")
            except (TypeError, ValueError):
                title = ""
            add("send", str(row["document_ref"]), title.strip() or "Document", "Sent", row["settled_at"])
        for row in rows(conn, """SELECT id, title, started_at, ended_at, intel_status FROM meetings
                                 WHERE parked = 0 AND ended_at IS NOT NULL AND started_at >= ?"""):
            if (_stamp(row["started_at"]) or start) < start:
                continue
            add("meeting", f"meeting:{row['id']}", str(row["title"] or "").strip() or "Meeting",
                "Summary stored" if row["intel_status"] == "ready" else "Held", row["ended_at"])
    items.sort(key=lambda item: item.pop("_at"), reverse=True)
    return {"since": start.isoformat().replace("+00:00", "Z"), "items": items[:max(1, int(limit))]}

