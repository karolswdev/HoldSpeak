"""The one meaning of ``needs you``: the R1-R3 membership rule, on the hub.

Phase 13 story 03 wrote the rule in the browser
(``web/src/desk/needsYou.ts`` ``computeNeedsYou``). The bell, the Chair and
the Dock read it there; notifications, the palette, the system shade, the
Brief and MCP read a Room-only count here, so the numbers disagreed. This
module is the same rule, line for line, and it is the single source: the
declared ``desk.needs_you`` operation returns its answer and every face
reads that answer.

    R1  the Door board's four asking columns (overdue, now, waiting,
        unassigned) plus every Room row. A Room commitment owns its action
        item, so the matching Door card is removed. The merged rows use the
        shared dedup and ranking (``attention_ranking``). A row whose
        Project is muted is kept apart and is not counted.
    R2  the meeting-path blockers (no engine for speech or for summaries).
    R3  the meetings whose summary FAILED or is RETRYING.

``count`` is ``len(members)``. Nothing else is a count of ``needs you``.

The pure function is :func:`compute_needs_you`; :func:`compose` reads the
three hub sources (the Door, the assignment roster, the summary-attention
meetings) through their services and applies it to a Room aggregate.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

from .attention_ranking import dedup_items, rank_items

log = logging.getLogger(__name__)

#: The four Door board columns that ask the owner. ``active`` is absent on
#: purpose: an active thought is a Door item, but it does not need the owner.
DOOR_COLUMNS: tuple[str, ...] = ("overdue", "now", "waiting", "unassigned")

SUMMARY_CAPABILITY = "meeting.deferred_analysis"
SPEECH_CAPABILITY = "speech.transcribe"

_INTEL_BADGE = {
    "complete": "RAN", "ready": "RAN", "running": "RUNNING", "queued": "QUEUED",
    "pending": "QUEUED", "error": "FAILED", "failed": "FAILED",
    "import_failed": "FAILED", "partial": "PARTIAL", "skipped": "SKIPPED",
    "disabled": "OFF",
}


# ── R1: the Door cards as attention rows ──────────────────────────────


def _due_epoch_ms(due: Any) -> float | None:
    """The due stamp as the browser's ``new Date(due).getTime()`` reads it:
    a bare date is UTC midnight."""
    if not due or not isinstance(due, str):
        return None
    try:
        parsed = datetime.fromisoformat(due.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc) if len(due.strip()) <= 10 else parsed.astimezone()
    return parsed.timestamp() * 1000.0


def door_items(
    board: dict[str, Any], covered_action_items: set[str], now: datetime,
) -> list[dict[str, Any]]:
    """Door cards in the four asking columns, as attention rows."""
    now_ms = (now if now.tzinfo else now.astimezone()).timestamp() * 1000.0
    rows: list[dict[str, Any]] = []
    for column in DOOR_COLUMNS:
        for card in board.get(column) or []:
            card_id = str(card.get("id") or "")
            if not card_id or card_id in covered_action_items:
                continue
            due_at = card.get("due")
            owner = card.get("owner")
            severity = "info"
            if column == "overdue":
                due_ms = _due_epoch_ms(due_at)
                days = max(1, int((now_ms - due_ms) // 86_400_000)) if due_ms is not None else 0
                why = f"OVERDUE · {days}D" if days > 0 else "OVERDUE"
                severity = "danger"
            elif column == "now":
                why = "DUE TODAY"
                severity = "warning"
            elif column == "waiting":
                why = f"WAITING ON {str(owner).upper()}" if owner else "WAITING"
            else:
                why = "UNASSIGNED"
                severity = "warning"
            rows.append({
                "id": f"door:{card_id}",
                "ref": card_id,
                "projectId": str(card.get("project_id") or card.get("projectId") or ""),
                "projectName": "",
                "title": str(card.get("title") or card.get("text") or "Untitled"),
                "why": why,
                "ageToken": "",
                "since": "",
                "dueAt": due_at,
                "kind": "action_item",
                "source": str(card.get("source") or "action_item"),
                # ``open_ref`` is a Desk route token, never an external URL.
                "verbHref": None,
                "openRef": card.get("open_ref"),
                "severity": severity,
                "owner": owner,
                "_doorCard": card,
                "_isDoor": True,
                "_isUnassigned": column == "unassigned",
            })
    return rows


# ── R2: the meeting-path blockers ─────────────────────────────────────


def meeting_path_blockers(
    summary: dict[str, Any] | None, read: str = "ok",
) -> list[dict[str, str]]:
    """Every meeting-path blocker the assignment roster states, in path order.

    ``read`` is ``ok``, ``failed`` or ``pending``. A failed read is one
    ``unknown`` row; a pending read is no row.
    """
    if read == "pending":
        return []
    if read == "failed" or not summary:
        return [{"key": "unknown", "label": "Could not read setup", "verb": "Try again"}]
    tasks = summary.get("task_overrides") or []

    def row(capability: str) -> dict[str, Any] | None:
        return next((task for task in tasks if task.get("id") == capability), None)

    def status(task: dict[str, Any]) -> Any:
        return (task.get("effective") or {}).get("status")

    verb = "Choose an engine"
    speech = row(SPEECH_CAPABILITY)
    speech_missing = speech is not None and status(speech) != "assigned"
    analysis = row(SUMMARY_CAPABILITY)
    summary_missing = analysis is not None and not (
        bool(analysis.get("has_override")) and status(analysis) == "assigned"
    )
    if speech_missing and summary_missing:
        return [{"key": "engines", "label": "No engine yet", "verb": verb}]
    blockers: list[dict[str, str]] = []
    if speech_missing:
        blockers.append({"key": "speech", "label": "No engine for speech", "verb": verb})
    if summary_missing:
        blockers.append({"key": "summary", "label": "No engine for summaries", "verb": verb})
    return blockers


# ── R3: the meetings whose summary failed ─────────────────────────────


def _intel_state(meeting: dict[str, Any]) -> str:
    raw = meeting.get("intel_status")
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("state"), str):
        return raw["state"]
    return ""


def meeting_summary_badge(meeting: dict[str, Any]) -> str:
    job = meeting.get("intel_job") if isinstance(meeting.get("intel_job"), dict) else None
    job_status = str((job or {}).get("status") or "").lower() if job and isinstance(job.get("status"), str) else ""
    attempts = (job or {}).get("attempts")
    attempts = attempts if isinstance(attempts, (int, float)) and not isinstance(attempts, bool) else 0
    last_error = (job or {}).get("last_error")
    # A retry stays RETRYING after its scheduled time: the failed lineage is
    # the fact the owner needs.
    if job_status in ("queued", "retrying") and attempts > 0 and isinstance(last_error, str) and last_error:
        return "RETRYING"
    if job_status == "failed":
        return "FAILED"
    state = _intel_state(meeting)
    if not state:
        return "SAVED"
    return _INTEL_BADGE.get(state.lower(), "SAVED")


def meeting_needs_you(meeting: dict[str, Any]) -> bool:
    return meeting_summary_badge(meeting) in ("FAILED", "RETRYING")


# ── the rule ──────────────────────────────────────────────────────────


def _item_ref(item: dict[str, Any]) -> str:
    ref = item.get("ref")
    return str(ref if ref is not None else item.get("id") or "")


def compute_needs_you(
    *,
    door: dict[str, Any] | None = None,
    room_items: Iterable[dict[str, Any]] = (),
    muted_project_ids: Iterable[str] = (),
    assignments: dict[str, Any] | None = None,
    assignment_read: str = "pending",
    meetings: Iterable[dict[str, Any]] = (),
    now: datetime | None = None,
    dedup: Callable[[list[dict[str, Any]], datetime], list[dict[str, Any]]] = dedup_items,
) -> dict[str, Any]:
    """The pure R1-R3 rule. Mirrors ``computeNeedsYou`` line for line.

    ``door`` is the Door response or its board. Returns ``members`` (stable
    refs, in face order), ``count``, the ranked rows split by mute, the
    blockers and the failed meetings.
    """
    clock = now or datetime.now()
    room = [dict(item) for item in room_items]
    covered = {
        str(item["actionItemId"])
        for item in room
        if item.get("source") == "commitment" and item.get("actionItemId")
    }
    board = (door or {}).get("board") if isinstance((door or {}).get("board"), dict) else (door or {})
    combined = door_items(board, covered, clock) + room
    ranked = rank_items(dedup(combined, clock), clock)
    muted_projects = {str(pid) for pid in muted_project_ids}
    unmuted_items: list[dict[str, Any]] = []
    muted_items: list[dict[str, Any]] = []
    for item in ranked:
        project_id = item.get("projectId")
        if bool(item.get("muted")) or (project_id and str(project_id) in muted_projects):
            item["muted"] = True
            muted_items.append(item)
        else:
            item["muted"] = False
            unmuted_items.append(item)

    blockers = meeting_path_blockers(
        None if assignment_read == "failed" else assignments, assignment_read,
    )
    failed_meetings = [meeting for meeting in meetings if meeting_needs_you(meeting)]
    members = (
        [{"ref": _item_ref(item), "kind": "attention"} for item in unmuted_items]
        + [{"ref": f"blocker:{blocker['key']}", "kind": "blocker"} for blocker in blockers]
        + [{"ref": str(meeting.get("id") or ""), "kind": "meeting"} for meeting in failed_meetings]
    )
    return {
        "members": members,
        "count": len(members),
        "unmutedItems": unmuted_items,
        "mutedItems": muted_items,
        "blockers": blockers,
        "failedMeetings": failed_meetings,
    }


# ── the hub reads ─────────────────────────────────────────────────────


def _hub_service(name: str, build: Callable[[], Any]) -> Any:
    """The hub's live service, or a bare one where no hub runs (a CLI, a rig)."""
    from holdspeak.runtime import composition

    return build() if composition.installed() is None else composition.service(name, build)


def _read_door(db: Any, principal: Any) -> dict[str, Any]:
    def bare() -> Any:
        from holdspeak.config import Config
        from .door_service import DoorService
        from .follow_through_service import FollowThroughService
        from .refinement_thought_service import RefinementThoughtService

        return DoorService(
            FollowThroughService(db), RefinementThoughtService(db),
            db.scheduled_recordings, db.calendar_events, db=db, config_loader=Config.load,
        )

    return _hub_service("door_service", bare).get(principal)


def _read_assignments(db: Any, principal: Any) -> dict[str, Any]:
    def bare() -> Any:
        from .inference_assignment_service import InferenceAssignmentService

        return InferenceAssignmentService(db)

    return _hub_service("inference_assignment_service", bare).assignment_summary(principal)


def _read_summary_attention(db: Any, principal: Any) -> list[dict[str, Any]]:
    def bare() -> Any:
        from .meeting_service import MeetingService

        return MeetingService(db)

    meetings = _hub_service("meeting_service", bare)
    out: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = meetings.list_meetings(principal, limit=500, cursor=offset, summary_attention=True)
        rows = list(page.get("meetings") or [])
        out.extend(rows)
        offset += len(rows)
        total = page.get("total")
        if len(rows) < 500 or (isinstance(total, int) and offset >= total):
            break
    return out


def _is_owner(principal: Any) -> bool:
    from holdspeak.principals import PrincipalKind

    return getattr(principal, "kind", None) is PrincipalKind.OWNER


def _reason(exc: Exception) -> str:
    return str(exc).split("\n")[0][:200] or type(exc).__name__


def compose(
    db: Any,
    principal: Any,
    aggregate: dict[str, Any],
    *,
    muted_project_ids: Iterable[str] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    """The full ``desk.needs_you`` answer over a Room aggregate.

    ``aggregate`` is ``needs_you_aggregate.build_aggregate``'s payload (or an
    earlier answer of this function: ``roomItems`` holds the Room rows, so a
    cached Room read is recomposed with a fresh Door on every request).

    A hub source that cannot be read is named in ``sourceErrors`` and makes
    ``complete`` false; it is never a silent zero. A failed assignment read
    is the rule's own ``unknown`` blocker.
    """
    room_items = aggregate.get("roomItems")
    if room_items is None:
        room_items = aggregate.get("items") or []
    # The current mute list decides; a mark left on a cached Room row does not.
    room_items = [{key: value for key, value in row.items() if key != "muted"} for row in room_items]
    muted = {str(pid) for pid in muted_project_ids}
    room_complete = bool(aggregate.get("roomComplete", aggregate.get("complete", True)))
    errors: dict[str, str] = {}

    door: dict[str, Any] | None = None
    try:
        door = _read_door(db, principal)
    except Exception as exc:
        log.warning("needs-you: the Door read failed: %s", exc)
        errors["door"] = _reason(exc)

    assignments: dict[str, Any] | None = None
    assignment_read = "ok"
    try:
        assignments = _read_assignments(db, principal)
    except Exception as exc:
        log.warning("needs-you: the assignment read failed: %s", exc)
        errors["assignments"] = _reason(exc)
        # The owner's failed read is the rule's ``unknown`` row (one verb that
        # reads again). A reader that may not read the roster at all learns
        # nothing about it: no row, the source named in ``sourceErrors``.
        assignment_read = "failed" if _is_owner(principal) else "pending"

    meetings: list[dict[str, Any]] = []
    try:
        meetings = _read_summary_attention(db, principal)
    except Exception as exc:
        log.warning("needs-you: the meeting read failed: %s", exc)
        errors["meetings"] = _reason(exc)

    result = compute_needs_you(
        door=door,
        room_items=room_items,
        muted_project_ids=muted,
        assignments=assignments,
        assignment_read=assignment_read,
        meetings=meetings,
        now=now,
    )
    answer = dict(aggregate)
    answer.update({
        "count": result["count"],
        "members": result["members"],
        # Every attention row, ranked: the counted rows, then the muted ones.
        "items": result["unmutedItems"] + result["mutedItems"],
        "mutedCount": len(result["mutedItems"]),
        "blockers": result["blockers"],
        "failedMeetings": result["failedMeetings"],
        "projects": sorted({
            str(item["projectId"]) for item in result["unmutedItems"] if item.get("projectId")
        }),
        # The Room rows alone (the input of R1), with the mute marks the
        # Room wire always carried.
        "roomItems": [
            {**row, "muted": row.get("projectId") in muted} if muted else row
            for row in room_items
        ],
        "sourceErrors": errors,
        # The Room read's own completeness is kept apart, so a recomposed
        # answer does not carry an earlier Door failure.
        "roomComplete": room_complete,
        "complete": room_complete and not errors,
    })
    if door is not None and door.get("people_store_state") is not None:
        # The People store state travels with the answer: a locked store means
        # its commitments are absent, and the face says so.
        answer["peopleStoreState"] = door["people_store_state"]
    return answer


_MEMBERSHIP_KEYS = ("members", "blockers", "failedMeetings", "sourceErrors", "peopleStoreState")


def room_part(answer: dict[str, Any]) -> dict[str, Any]:
    """The Room read of an answer, alone: what a cache may hold.

    People commitments reach the rule through the Door. They never enter a
    cache, so the cached value keeps the Room rows and drops every row and
    member the Door, the roster and the meetings gave.
    """
    room = {key: value for key, value in answer.items() if key not in _MEMBERSHIP_KEYS}
    room_items = [
        {key: value for key, value in row.items() if key != "muted"}
        for row in (answer.get("roomItems") or [])
    ]
    room["roomItems"] = room_items
    room["items"] = list(room_items)
    room["count"] = len(room_items)
    room["complete"] = bool(answer.get("roomComplete", answer.get("complete", True)))
    return room


#: What an outside reader sees in place of a People commitment's text.
PEOPLE_ROW_TITLE = "1:1 commitment"


def withhold_people_content(answer: dict[str, Any]) -> dict[str, Any]:
    """The same answer and the same number, with People content withheld.

    For a reader outside the People custody boundary (an MCP agent, a stored
    Brief). The commitment is still a member and still counted; its text, its
    Door card and its record ref are not disclosed.
    """
    out = dict(answer)
    refs: dict[str, str] = {}
    items: list[dict[str, Any]] = []
    for index, row in enumerate(answer.get("items") or []):
        if row.get("source") != "people_commitment":
            items.append(row)
            continue
        ref = f"people_commitment:{index}"
        refs[str(row.get("ref") or row.get("id") or "")] = ref
        items.append({
            "id": ref, "ref": ref, "source": "people_commitment", "kind": row.get("kind"),
            "title": PEOPLE_ROW_TITLE, "why": row.get("why"), "severity": row.get("severity"),
            "rankClass": row.get("rankClass"), "rank": row.get("rank"),
            "projectId": "", "muted": bool(row.get("muted")),
        })
    out["items"] = items
    out["members"] = [
        {**member, "ref": refs.get(str(member.get("ref")), member.get("ref"))}
        for member in answer.get("members") or []
    ]
    return out


__all__ = [
    "PEOPLE_ROW_TITLE",
    "room_part",
    "withhold_people_content",
    "DOOR_COLUMNS",
    "compose",
    "compute_needs_you",
    "door_items",
    "meeting_needs_you",
    "meeting_path_blockers",
    "meeting_summary_badge",
]
