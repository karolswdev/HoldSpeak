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
    R4  the decisions that wait for the owner's review (a Desk decision
        that is ``proposed``, a meeting's decision that is ``recorded``).
        Each is an attention row with a Review verb that opens it.
    R5  the coding agents (Claude Code, Codex) that wait for the owner's
        answer: a session in ``awaiting_response`` with a captured question,
        updated in the last 30 minutes (``agent_context``'s recent default),
        plus Secure helper requests awaiting one owner Allow press. Each is
        an attention row of kind ``coder`` that ranks with the due-today rows
        (a blocked agent costs time now).

Owner ruling 2026-10-04: a row the owner is WAITING ON someone else for (it
names an owner, and its reason is ``WAITING ON <owner>``) is listed and is
marked ``waiting``; it is not a member and is not counted. ``count`` is
``len(members)``: what needs the owner. ``waitingCount`` is the number of
unmuted rows that wait on others. Nothing else is a count of ``needs you``.

The pure function is :func:`compute_needs_you`; :func:`compose` reads the
three hub sources (the Door, the assignment roster, the summary-attention
meetings) through their services and applies it to a Room aggregate.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from holdspeak.timestamps import local_wall, parse_stamp, utc_now, utc_now_iso
from typing import Any, Callable, Iterable

from .attention_ranking import dedup_items, normalize_title, rank_items

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


_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def door_due_word(due: Any, today: date) -> str:
    """The wire reason of a Door card in the ``now`` window, by its due day.

    ``DUE TODAY``, ``DUE TOMORROW``, ``DUE Thu`` (the weekday, in its own
    case so the face keeps the capital), ``OVERDUE`` when the day is past.
    The face says it in sentence case (``NeedsRow`` ``stateWords``).
    """
    day = _due_day(due)
    if day is None:
        return "DUE TODAY"
    delta = (day - today).days
    if delta < 0:
        return "OVERDUE"
    if delta == 0:
        return "DUE TODAY"
    if delta == 1:
        return "DUE TOMORROW"
    if delta < 7:
        return f"DUE {_WEEKDAYS[day.weekday()]}"
    return f"DUE {day.isoformat()}"


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
            has_owner = bool(str(owner or "").strip())
            severity = "info"
            if column == "overdue":
                due_ms = _due_epoch_ms(due_at)
                days = max(1, int((now_ms - due_ms) // 86_400_000)) if due_ms is not None else 0
                why = f"OVERDUE · {days}D" if days > 0 else "OVERDUE"
                severity = "danger"
            elif column == "now":
                # The "now" column is a two-day window
                # (``FollowThroughService._lane``): the word says the day.
                # ``compute_needs_you`` makes another person's item a wait on
                # that person (``_dueWord`` keeps the word).
                why = door_due_word(due_at, now.date())
                severity = "warning"
            elif column == "waiting":
                why = f"WAITING ON {str(owner).upper()}" if owner else "WAITING"
            elif has_owner:
                # The ``unassigned`` column also holds an item that HAS an
                # owner and is not reviewed yet. It reads "To review"; only
                # an item with no owner reads "Unassigned".
                why = "TO REVIEW"
                severity = "warning"
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
                "_isUnassigned": column == "unassigned" and not has_owner,
                "_toReview": column == "unassigned" and has_owner,
                # ``compute_needs_you`` makes another person's item in the
                # two-day window or the overdue column a wait on that person.
                **({"_dueWord": door_due_word(due_at, now.date())} if column == "now" else {}),
                **({"_dueWord": "OVERDUE"} if column == "overdue" else {}),
            })
    return merge_unassigned_twins(rows)


def merge_unassigned_twins(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Two unassigned Door rows with the same text and Project are one row.

    Two meetings can make the same action item (``Write the rollback
    runbook``) with no owner; the owner sees it one time. The row with the
    earlier ``created_at`` stays (no stamp sorts last); the other is dropped.
    The twin of ``mergeUnassignedTwins`` (web/src/desk/needsYou.ts).
    """
    def stamp(item: dict[str, Any]) -> str:
        return str((item.get("_doorCard") or {}).get("created_at") or "") or "\uffff"

    kept: dict[tuple[str, str], int] = {}
    out: list[dict[str, Any]] = []
    for row in rows:
        title = normalize_title(row.get("title"))
        if not row.get("_isUnassigned") or not title:
            out.append(row)
            continue
        key = (title, str(row.get("projectId") or ""))
        if key not in kept:
            kept[key] = len(out)
            out.append(row)
            continue
        if stamp(row) < stamp(out[kept[key]]):
            out[kept[key]] = row
    return out


def helper_request_items(
    flights: Iterable[Any], now: datetime | None = None,
) -> list[dict[str, Any]]:
    """R5: Secure helper requests waiting for the owner's Allow press.

    A helper request has no agent session yet, so it cannot be represented by
    :func:`coder_items`. The parent flight remains the durable owner-facing
    projection until the owner consumes the request through the helper route.
    """
    clock = now or local_wall()
    now_s = (clock if clock.tzinfo else clock.astimezone()).timestamp()
    rows: list[dict[str, Any]] = []
    for flight in flights:
        record = flight if isinstance(flight, dict) else dict(flight or {})
        request = record.get("helper_request")
        launch_id = str(record.get("launch_id") or "")
        if not launch_id or not isinstance(request, dict) or request.get("status") != "awaiting_owner":
            continue
        request_id = str(request.get("request_id") or "")
        requested = str(request.get("requested_at") or record.get("launched_at") or "")
        requested_s = _epoch_seconds(requested)
        age = max(0, int(now_s - requested_s)) if requested_s is not None else 0
        instruction = str(request.get("instruction") or "Allow the helper to start").strip()
        ref = f"{CODER_SOURCE}:launch:{launch_id}:helper"
        rows.append({
            "id": ref,
            "ref": ref,
            "notifyKey": f"{ref}#{request_id}" if request_id else ref,
            "projectId": str(record.get("project_id") or ""),
            "projectName": str(record.get("project_name") or ""),
            "title": _excerpt(instruction),
            "why": TO_APPROVE,
            "ageToken": requested,
            "since": requested,
            "dueAt": None,
            "kind": CODER_SOURCE,
            "source": CODER_SOURCE,
            "verbHref": None,
            "openRef": f"launch:{launch_id}",
            "severity": "warning",
            # The helper has no session until Allow starts it. Reusing the
            # parent's key would make fold_asks hide this owner action inside
            # the parent's ordinary question.
            "sessionKey": "",
            "launchId": launch_id,
            "agent": str(record.get("agent") or ""),
            "question": instruction,
            "waitKind": "approve",
            "waitStartedAt": requested,
            "ageSeconds": age,
            "helperRequest": {
                "requestId": request_id,
                "status": "awaiting_owner",
                "instruction": instruction,
                "profile": request.get("profile"),
            },
        })
    return rows


# ── R4: the decisions that wait for the owner's review ───────────────


DECISION_SOURCE = "decision"


def decision_items(decisions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Decisions awaiting review, as attention rows.

    ``decisions`` holds ``{id, title, projectId, since}``. The ref is the
    Desk route token ``decision:<id>``; Review opens it.
    """
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        decision_id = str(decision.get("id") or "")
        if not decision_id:
            continue
        ref = f"{DECISION_SOURCE}:{decision_id}"
        since = str(decision.get("since") or "")
        rows.append({
            "id": ref,
            "ref": ref,
            "projectId": str(decision.get("projectId") or ""),
            "projectName": "",
            "title": str(decision.get("title") or "Untitled"),
            "why": "TO REVIEW",
            "ageToken": since,
            "since": since,
            "dueAt": None,
            "kind": DECISION_SOURCE,
            "source": DECISION_SOURCE,
            "verbHref": None,
            "openRef": ref,
            "status": str(decision.get("status") or ""),
            "severity": "warning",
        })
    return rows


# ── Programs (2026-10-28): what only the owner can do on a Program ──


PROGRAM_SOURCE = "program"

#: The reason token of each Program your-turn kind.
PROGRAM_WHY = {
    "merge": "TO MERGE", "finding": "TO DECIDE", "parked": "TO RESUME", "ask_review": "TO ASK",
    "core": "TO DECIDE", "race": "TO PICK", "add_step": "TO DECIDE", "close": "TO CLOSE",
    # PG19: the step's agent is at its usage limit: continue in the next, or wait.
    "limited": "TO DECIDE",
}


def program_items(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """The Programs' your-turn items as attention rows: merge asks, findings
    left after two rounds, steps the engine parked, a person to ask for a
    review. An agent's question is NOT here: the coder row carries it
    (``coder_items``). The group is the Program's title; each verb is a
    REST decide call (``POST /api/programs/{id}/steps/{sid}/decide``)."""
    rows: list[dict[str, Any]] = []
    for item in items:
        kind = str(item.get("kind") or "")
        if kind not in PROGRAM_WHY or not item.get("program_id") or not (item.get("step_id") or kind == "close"):
            continue
        ref = f"{PROGRAM_SOURCE}:{item['program_id']}:{item['id']}"
        since = str(item.get("since") or "")
        rows.append({
            "id": ref,
            "ref": ref,
            "projectId": str(item.get("project_id") or ""),
            "projectName": "",
            "title": str(item.get("title") or "Program"),
            "why": PROGRAM_WHY[kind],
            "ageToken": since,
            "since": since,
            "dueAt": None,
            "dueWord": "now",
            "kind": PROGRAM_SOURCE,
            "source": PROGRAM_SOURCE,
            "verbHref": None,
            "openRef": f"program:{item['program_id']}",
            "severity": "warning",
            "group": str(item.get("program_title") or ""),
            "program": {
                "programId": str(item["program_id"]), "stepId": str(item["step_id"]),
                "ordinal": item.get("ordinal"), "kind": kind, "choices": list(item.get("choices") or []),
                "findingId": item.get("finding_id"), "pr": item.get("pr"),
                "decide": (f"/api/programs/{item['program_id']}/close" if kind == "close"
                           else f"/api/programs/{item['program_id']}/steps/{item['step_id']}/decide"),
            },
            "personId": item.get("for_person_id") or None,
        })
    return rows


# ── R5: the coding agents that wait for the owner's answer ──────────


CODER_SOURCE = "coder"

#: The reason token of a coder row that asks a question.
TO_ANSWER = "TO ANSWER"

#: The reason token of a coder row blocked on a permission prompt (its latest
#: hook event is a ``Notification`` that carries the ask).
TO_APPROVE = "TO APPROVE"


#: The longest question excerpt a row carries (the full question stays in
#: the session registry; the Agents window shows it).
CODER_EXCERPT_CHARS = 200


def _epoch_seconds(stamp: Any) -> float | None:
    if not stamp or not isinstance(stamp, str):
        return None
    try:
        parsed = datetime.fromisoformat(stamp.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


#: Phase 16: the most of an agent's question a Needs row carries.
CODER_QUESTION_CHARS = 4000


def _excerpt(text: str) -> str:
    flat = " ".join(text.split())
    if len(flat) <= CODER_EXCERPT_CHARS:
        return flat
    return flat[: CODER_EXCERPT_CHARS - 1].rstrip() + "…"


def coder_items(
    sessions: Iterable[Any],
    now: datetime | None = None,
    *,
    max_age_seconds: int | None = None,
) -> list[dict[str, Any]]:
    """R5: the coder sessions that wait for the owner, as attention rows.

    ``sessions`` holds ``agent_context.AgentSession`` objects or their
    ``to_dict()`` mappings. A session is a member when it is blocked
    (``agent_context.is_blocked``: the ONE predicate the hub's coder watcher
    reads too) and was updated within ``max_age_seconds`` (default:
    ``DEFAULT_RECENT_MAX_AGE_SECONDS``, 30 min). Pinned sessions get no
    exemption. The reason is ``TO APPROVE`` for a permission prompt and
    ``TO ANSWER`` for a question or an input prompt.

    ``since`` is the wait's start (``wait_started_at``), so a repeated report
    does not move the row in the oldest-first order; freshness reads
    ``updated_at``. ``notifyKey`` names the wait EPISODE (the stable row ref
    plus ``wait_id``): the Heartbeat dedupes notifications on it, so a new
    wait after an answer notifies again while one wait notifies once.
    """
    from holdspeak.agent_context.models import (
        DEFAULT_RECENT_MAX_AGE_SECONDS,
        TURN_ASKS,
        is_blocked,
        turn_end,
        wait_kind,
    )

    if max_age_seconds is None:
        max_age_seconds = DEFAULT_RECENT_MAX_AGE_SECONDS
    clock = now or local_wall()
    now_s = (clock if clock.tzinfo else clock.astimezone()).timestamp()
    rows: list[dict[str, Any]] = []
    for raw in sessions:
        session = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw or {})
        if not is_blocked(session):
            continue
        # Conductor K5: a wait HoldSpeak is answering (YOLO, deciding) or
        # answered (routine, sent) is not the owner's
        # (``agent_responder.annotate_sessions``).
        answer = session.get("answer") if isinstance(session.get("answer"), dict) else {}
        if answer.get("hidden"):
            continue
        question = str(session.get("question") or "").strip()
        updated = str(session.get("updated_at") or "")
        updated_s = _epoch_seconds(updated)
        if updated_s is None:
            continue
        if max(0, int(now_s - updated_s)) > max_age_seconds:
            continue
        agent = str(session.get("agent") or "")
        session_id = str(session.get("session_id") or "")
        if not agent or not session_id:
            continue
        key = f"{agent}:{session_id}"
        ref = f"{CODER_SOURCE}:{key}"
        started = str(session.get("wait_started_at") or "") or updated
        started_s = _epoch_seconds(started)
        age = max(0, int(now_s - (started_s if started_s is not None else updated_s)))
        wait_id = str(session.get("wait_id") or "")
        approve = wait_kind(session) == "approve"
        if turn_end(session) != TURN_ASKS:
            # PHILO-15 B48 (the A5 law: Needs you is what needs HIM): a turn
            # that ended with no question is IDLE, a lane station and a
            # Conductor lamp, never a Needs you row.
            continue
        rows.append({
            "id": ref,
            "ref": ref,
            "notifyKey": f"{ref}#{wait_id}" if wait_id else ref,
            "projectId": "",
            "projectName": str(session.get("project_name") or ""),
            "title": _excerpt(question),
            "why": TO_APPROVE if approve else TO_ANSWER,
            "ageToken": started,
            "since": started,
            "dueAt": None,
            "kind": CODER_SOURCE,
            "source": CODER_SOURCE,
            "verbHref": None,
            "openRef": ref,
            "severity": "warning",
            "sessionKey": key,
            "agent": agent,
            "cwd": str(session.get("cwd") or ""),
            "repoRoot": str(session.get("repo_root") or ""),
            # Phase 16: the agent's words as it wrote them (newlines and
            # marks kept); the face draws them (AgentWords). The title stays
            # the flat excerpt.
            "question": question[:CODER_QUESTION_CHARS],
            "waitKind": "approve" if approve else "answer",
            "waitStartedAt": started,
            "ageSeconds": age,
        })
        if answer.get("state") in ("escalated", "drafted") and (answer.get("draft") or answer.get("reason")):
            # The drafted answer and why it waits for the owner (K5).
            rows[-1]["draft"] = {
                "verdict": str(answer.get("verdict") or ""),
                "reason": str(answer.get("reason") or ""),
                "text": str(answer.get("draft") or ""),
            }
    return rows


#: The source of a held tool call of a HoldSpeak launch (Conductor R1).
GATE_SOURCE = "gate"


def gate_items(holds: Iterable[dict[str, Any]], now: datetime | None = None) -> list[dict[str, Any]]:
    """R5, held tool calls: each Bash call the tool gate holds for a
    HoldSpeak-launched agent is one ``TO APPROVE`` row (Conductor R1: the
    agent waited up to 240 s and nothing on the Desk said so).

    ``holds`` are :func:`_read_gate_holds` records. The row's ref and its
    Open name the gate proposal (``gate:<proposal_id>``); ``notifyKey`` is
    the same ref, so one hold notifies once."""
    clock = now or local_wall()
    now_s = (clock if clock.tzinfo else clock.astimezone()).timestamp()
    rows: list[dict[str, Any]] = []
    for hold in holds:
        proposal_id = str(hold.get("proposal_id") or "")
        if not proposal_id or not hold.get("held", True):
            continue
        created = float(hold.get("created_at") or now_s)
        since = datetime.fromtimestamp(created, timezone.utc).isoformat().replace("+00:00", "Z")
        ref = f"{GATE_SOURCE}:{proposal_id}"
        title = _excerpt(f"Approve: {hold.get('command') or hold.get('tool') or 'a tool call'}")
        rows.append({
            "id": ref,
            "ref": ref,
            "notifyKey": ref,
            "projectId": "",
            "projectName": "",
            "title": title,
            "why": TO_APPROVE,
            "ageToken": since,
            "since": since,
            "dueAt": None,
            "kind": GATE_SOURCE,
            "source": GATE_SOURCE,
            "verbHref": None,
            "openRef": ref,
            "severity": "warning",
            "sessionKey": str(hold.get("session_key") or ""),
            "launchId": str(hold.get("launch_id") or ""),
            "question": title,
            "waitKind": "approve",
            "waitStartedAt": since,
            "ageSeconds": max(0, int(now_s - created)),
            # PHILO-14 A5: the head is not the whole call; the desk offers
            # Deny and Open, never Approve, on a command it cannot show whole.
            "argsCut": bool(hold.get("args_cut")),
            "argsHidden": int(hold.get("args_hidden") or 0),
            # PHILO-15 15 (B44): the whole shown command (the title is an
            # excerpt), so a long but complete command is approved as seen;
            # and why it waits (B43: ``OUTSIDE THE WORKTREE · /tmp/x``).
            "command": str(hold.get("command") or ""),
            "holdReason": str(hold.get("hold_reason") or ""),
        })
    return rows


def _gate_view(args_head: str, args_len: Any) -> dict[str, Any]:
    """The command, cut flag and hidden count every approval surface shows
    (``db.gate.command_view``: one place, on the text the owner sees)."""
    from holdspeak.db.gate import command_view

    view = command_view(args_head, args_len)
    return {"command": view["command"], "args_cut": view["args_cut"], "args_hidden": view["args_hidden"]}


def _args_cut(args_head: str, args_len: Any) -> dict[str, Any]:
    """The cut flag and hidden count alone (``_gate_view``)."""
    view = _gate_view(args_head, args_len)
    return {"args_cut": view["args_cut"], "args_hidden": view["args_hidden"]}


def _gate_command(args_head: str) -> str:
    """The command of a held call from its (redacted, maybe cut) head."""
    import json

    try:
        parsed = json.loads(args_head)
    except ValueError:
        # A cut head is a JSON fragment: show the command's own text, never
        # the JSON around it (PHILO-14 A5).
        prefix = '{"command":"'
        if args_head.startswith(prefix):
            return args_head[len(prefix):].replace('\\"', '"').replace("\\\\", "\\")
        return args_head
    if isinstance(parsed, dict) and parsed.get("command"):
        return str(parsed["command"])
    return args_head


#: How far back a decided or expired hold still names its session's
#: permission wait (one notification identity through decision or expiry).
GATE_RECENT_SECONDS = 30 * 60
#: Clock slack between the gate hold and the hook's permission Notification.
GATE_WAIT_SLACK_SECONDS = 2.0


def _read_gate_holds(db: Any, *, ledger: Any = None, now: float | None = None) -> list[dict[str, Any]]:
    """The gate proposals of live HoldSpeak launches: each held, unexpired
    one (``held: True``, a row of its own) and each decided or expired in
    the last :data:`GATE_RECENT_SECONDS` (``held: False``, read only to
    correlate a permission wait, :func:`correlate_gate_waits`)."""
    import time

    from holdspeak.db.gate import ALL_STATES, HELD
    from holdspeak.services.gate_service import _LIVE_LAUNCH_STATES, _is_launch_caller

    if ledger is None:
        from holdspeak.delivery.factory_launch import LaunchLedger

        ledger = LaunchLedger()
    moment = time.time() if now is None else now
    launches = [r for r in ledger.list() if str(r.get("state") or "") in _LIVE_LAUNCH_STATES]
    if not launches:
        return []
    holds: list[dict[str, Any]] = []
    for state in sorted(ALL_STATES):
        for proposal in db.gate.list_state(state, limit=200):
            expired = bool(proposal.expires_at and proposal.expires_at <= moment)
            held = state == HELD and not expired
            ended = proposal.decided_at or proposal.expires_at or moment
            if not held and moment - float(ended) > GATE_RECENT_SECONDS:
                continue
            launch = next((r for r in launches if _is_launch_caller(r, proposal.session_key)), None)
            if launch is None:
                continue
            holds.append({
                "proposal_id": proposal.id,
                "launch_id": str(launch.get("launch_id") or ""),
                "session_key": str(launch.get("session_key") or ""),
                "tool": proposal.tool,
                **_gate_view(proposal.args_head, (proposal.operation or {}).get("args_len")),
                "hold_reason": proposal.shown().get("hold_reason", ""),
                "created_at": proposal.created_at,
                "held": held,
                "ended_at": None if held else float(ended),
            })
    return holds


def correlate_gate_waits(
    coder_rows: list[dict[str, Any]], gate_rows: list[dict[str, Any]],
    holds: Iterable[dict[str, Any]], now: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """One ask, one row, one notification (Astra on #916): a held tool call
    and a permission wait of the SAME session that began while that call
    was held are one ask. The gate row stays (it names the command and opens
    the proposal); the coder row goes; the row's notification identity is
    the one of whichever began first. After the hold is decided or expired,
    a permission wait that began during it keeps the hold's identity, so the
    ask never notifies twice. Questions (TO ANSWER) are never joined."""
    clock = now or local_wall()
    now_s = (clock if clock.tzinfo else clock.astimezone()).timestamp()
    by_ref = {row["id"]: row for row in gate_rows}
    records = [h for h in holds if h.get("proposal_id") and h.get("session_key")]
    kept: list[dict[str, Any]] = []
    for row in coder_rows:
        start = _epoch_seconds(row.get("waitStartedAt"))
        if row.get("waitKind") != "approve" or start is None:
            kept.append(row)
            continue
        overlapping = []
        for hold in records:
            if hold["session_key"] != row.get("sessionKey"):
                continue
            begun = float(hold.get("created_at") or 0.0)
            end = now_s if hold.get("held", True) else float(hold.get("ended_at") or now_s)
            if begun - GATE_WAIT_SLACK_SECONDS <= start <= end + GATE_WAIT_SLACK_SECONDS:
                overlapping.append(hold)
        # A live hold first (Astra round 2 on #916: a call approved a moment
        # before a new hold took the new hold's wait); a decided or expired
        # one only when no held one overlaps. Among them, the newest.
        held_ones = [h for h in overlapping if h.get("held", True)]
        pool = held_ones or overlapping
        match = max(pool, key=lambda h: float(h.get("created_at") or 0.0)) if pool else None
        if match is None:
            kept.append(row)
            continue
        ref = f"{GATE_SOURCE}:{match['proposal_id']}"
        first = row["notifyKey"] if start < float(match.get("created_at") or 0.0) else ref
        gate_row = by_ref.get(ref)
        if gate_row is not None:
            gate_row["notifyKey"] = first
            gate_row["joined"] = row["id"]
            continue  # one row: the gate's
        row["notifyKey"] = first
        kept.append(row)
    return kept, gate_rows


#: The names that mean the owner himself. The People store reserves ``me``
#: and ``you`` (no person can take them, ``people_service._RESERVED_OWNER_ALIASES``)
#: and its follow-through projection names the owner ``you`` / ``manager``.
#: :func:`compose` adds the configured meeting speaker label (``Me``) and the
#: owner's own name and aliases (``config.owner``, set on first run).
SELF_OWNER_NAMES: frozenset[str] = frozenset({"me", "you", "manager"})

#: The reason token of a row the owner himself holds with no nearer due date.
YOURS = "YOURS"


def _is_self(owner: Any, self_names: Iterable[str]) -> bool:
    name = str(owner or "").strip().casefold()
    return bool(name) and name in {str(n).strip().casefold() for n in self_names}


def _waiting_on(row: dict[str, Any]) -> bool:
    owner = str(row.get("owner") or "").strip()
    # The head part decides: ``WAITING ON BEA · DUE TOMORROW`` (a Door card
    # in the two-day window) waits on Bea as ``WAITING ON BEA`` does.
    head = str(row.get("why") or "").split(" · ", 1)[0].strip().upper()
    return bool(owner) and head == f"WAITING ON {owner.upper()}"


def _person_identity(row: dict[str, Any]) -> str:
    """The People relationship a row names explicitly, or ``""``.

    A Door card linked to a person carries ``person_relationship_id``
    (door_service.py, HS-149-03/04); the attention row keeps the card.
    """
    card = row.get("_doorCard") if isinstance(row.get("_doorCard"), dict) else {}
    return str(row.get("person_relationship_id") or card.get("person_relationship_id") or "")


def _names_another(row: dict[str, Any], personal_names: Iterable[str]) -> bool:
    """The row names a Person explicitly, and that Person is not the owner.

    Betterment D0: a unique first name now links to its Person, so the
    owner's own "Karol" links to a Person "Karol Nowak" when he keeps
    himself in People. A linked Person whose name is his own is him.
    """
    if not _person_identity(row):
        return False
    card = row.get("_doorCard") if isinstance(row.get("_doorCard"), dict) else {}
    label = " ".join(str(row.get("person_label") or card.get("person_label") or "").split()).casefold()
    return not label or label not in {" ".join(str(n or "").split()).casefold() for n in personal_names}


def _is_me(
    row: dict[str, Any],
    self_names: Iterable[str],
    personal_names: Iterable[str] = (),
    identified: Iterable[str] = (),
    known_people: Iterable[str] | None = None,
) -> bool:
    """The owner himself holds this row.

    ``self_names`` (the reserved names and the speaker label) always match.
    ``personal_names`` (his own name and aliases, ``config.owner``) match a
    BARE owner string only: a row that names a person explicitly
    (``person_relationship_id``) is that person's, even when the person has
    the same first name as the owner. ``identified`` holds the ids of such
    rows, so a merged row's sources (which carry no card) keep the rule.
    """
    owner = row.get("owner")
    if _is_self(owner, self_names):
        return True
    if _names_another(row, personal_names) or str(row.get("id") or "") in set(identified):
        return False
    if _is_self(owner, personal_names):
        return True
    # PHILO-15 B57 (Astra r2 P1): his own FIRST name, exactly, is him: it
    # never depends on the People store or on the one-edit guard below.
    if _is_own_first_name(owner, personal_names):
        return True
    # PHILO-15 B57 (Astra r1 P1): a one-edit mishearing counts as him ONLY
    # when no Person on the desk has that exact name. ``known_people`` is
    # None when the People store could not be read: then nobody can prove
    # there is no Carol, and the tolerance is off.
    if known_people is None:
        return False
    said = " ".join(str(owner or "").split()).casefold()
    if said in set(known_people):
        return False
    return sounds_like_owner(owner, personal_names)


def _is_own_first_name(owner: Any, personal_names: Iterable[str]) -> bool:
    """A bare one-word owner that IS the first word of his name or an alias."""
    said = " ".join(str(owner or "").split()).casefold()
    if not said or " " in said:
        return False
    for raw in personal_names:
        name = " ".join(str(raw or "").split()).casefold()
        if name and name.split(" ")[0] == said:
            return True
    return False


#: The shortest name a one-letter mishearing may match (PHILO-15 B57): a
#: three-letter name is one edit from too many other names.
_SOUNDS_LIKE_MIN = 4


def _within_one_edit(a: str, b: str) -> bool:
    """True when ``a`` and ``b`` differ by at most one insert, delete or change."""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = j = edits = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
            continue
        edits += 1
        if edits > 1:
            return False
        if len(a) == len(b):
            i += 1
        j += 1
    return edits + (len(b) - j) + (len(a) - i) <= 1


def sounds_like_owner(owner: Any, personal_names: Iterable[str]) -> bool:
    """PHILO-15 B57: a bare owner string one letter from his own name is his.

    Speech recognition heard "Karol" as "Carol", so his own action read
    "OWNER CAROL" and waited on a person who does not exist. The match is
    case-insensitive and needs at most one edit: the whole name ("Carol
    Sane" for "Karol Sane"), or a bare first name against the first word of
    his name or an alias ("Carol" for "Karol"). Names shorter than four
    letters match exactly only.
    """
    said = " ".join(str(owner or "").split()).casefold()
    if len(said) < _SOUNDS_LIKE_MIN:
        return False
    said_words = said.split(" ")
    for raw in personal_names:
        name = " ".join(str(raw or "").split()).casefold()
        if len(name) < _SOUNDS_LIKE_MIN:
            continue
        if _within_one_edit(said, name):
            return True
        first = name.split(" ")[0]
        if len(said_words) == 1 and len(first) >= _SOUNDS_LIKE_MIN and _within_one_edit(said, first):
            return True
    return False


def waits_on_other(
    row: dict[str, Any],
    self_names: Iterable[str] = SELF_OWNER_NAMES,
    personal_names: Iterable[str] = (),
    identified: Iterable[str] = (),
    known_people: Iterable[str] | None = None,
) -> bool:
    """True when the owner waits on SOMEONE ELSE for this row.

    The row names an owner who is not the owner himself, and its reason is
    ``WAITING ON <that owner>``: a Door card in the ``waiting`` column, or a
    Room commitment with an owner and a later due date. ``WAITING ON YOUR
    REVIEW`` names no owner and is the owner's own work.
    """
    return _waiting_on(row) and not _is_me(row, self_names, personal_names, identified, known_people)


def configured_owner_names() -> tuple[list[str], list[str]]:
    """``(names, personal)``: the reserved names with his speaker label, and
    the name and aliases he gave on first run (``config.owner``)."""
    speaker: list[Any] = []
    personal: list[str] = []
    try:
        from holdspeak.config import Config

        config = Config.load()
        speaker = [config.meeting.mic_label]
        personal = [name.strip().casefold() for name in config.owner.names()]
    except Exception as exc:
        log.warning("needs-you: the owner names read failed: %s", exc)
    return owner_names(speaker), personal


def self_check(known_people: Iterable[str] | None = None) -> Callable[[Any], bool]:
    """A test of one owner string: is it the owner himself (``_is_me``)?"""
    names, personal = configured_owner_names()
    persons = None if known_people is None else {str(n).strip().casefold() for n in known_people}
    return lambda owner: _is_me({"owner": owner}, names, personal, (), persons)


def owner_names(extra: Iterable[Any] = ()) -> list[str]:
    """The names that mean the owner: the reserved ones and the given ones."""
    names = set(SELF_OWNER_NAMES)
    names.update(str(name).strip().casefold() for name in extra if str(name or "").strip())
    return sorted(names)


# ── R2: the meeting-path blockers ─────────────────────────────────────


def meeting_path_blockers(
    summary: dict[str, Any] | None, read: str = "ok", *, summary_waits: bool = True,
) -> list[dict[str, str]]:
    """Every meeting-path blocker the assignment roster states, in path order.

    ``read`` is ``ok``, ``failed`` or ``pending``. A failed read is one
    ``unknown`` row; a pending read is no row.

    Betterment daily D8: ``summary_waits`` is False when no meeting waits for
    a summary; then "No engine for summaries" does not ask (a fresh desk has
    nothing for it to summarize).
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
    # PHILO-15 01: the row asks the queue's route policy, which the roster
    # states as ``queue`` (meeting-intel-queue@2 also reads the group and
    # global heads).  A roster without it falls back to the owner chain.
    # ``off`` is the owner's own choice: no summary runs, and no row asks.
    queue = analysis.get("queue") if analysis is not None else None
    summary_missing = summary_waits and analysis is not None and (
        (queue.get("status") if isinstance(queue, dict) else status(analysis))
        not in ("assigned", "off")
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


def _a_meeting_waits_for_summary(db: Any) -> bool:
    """Betterment daily D8: True when a kept meeting waits for a summary: its
    summary is queued, running or failed, or it has words and no summary yet
    (and its summary is not skipped). On a read that fails, True: the row
    asks rather than hides."""
    try:
        with db._connection() as conn:
            row = conn.execute(
                """SELECT 1 FROM meetings m
                   WHERE m.parked = 0
                     AND (
                       LOWER(TRIM(COALESCE(m.intel_status, ''))) IN
                         ('pending', 'queued', 'running', 'error', 'failed', 'import_failed')
                       OR (
                         LOWER(TRIM(COALESCE(m.intel_status, ''))) NOT IN ('skipped', 'complete', 'ready')
                         AND EXISTS (SELECT 1 FROM segments s WHERE s.meeting_id = m.id AND TRIM(s.text) != '')
                         AND NOT EXISTS (
                             SELECT 1 FROM intel_snapshots i
                             WHERE i.meeting_id = m.id AND TRIM(COALESCE(i.summary, '')) != '')
                       )
                     )
                   LIMIT 1""",
            ).fetchone()
        return row is not None
    except Exception as exc:
        log.warning("needs-you: the waiting-meeting read failed: %s", exc)
        return True


# ── the rule ──────────────────────────────────────────────────────────


PEOPLE_SOURCE = "people_commitment"


def is_people_row(row: dict[str, Any]) -> bool:
    """True for a row that carries People content (a 1:1 commitment)."""
    return row.get("source") == PEOPLE_SOURCE


def _item_ref(item: dict[str, Any]) -> str:
    ref = item.get("ref")
    return str(ref if ref is not None else item.get("id") or "")


def item_origin_refs(item: dict[str, Any]) -> set[str]:
    """The launch ``origin_ref`` grammar an item row is known by (the twin of
    ``itemOriginRefs`` in ``web/src/desk/agentFlights.ts``)."""
    refs: set[str] = set()
    if item.get("actionItemId"):
        refs.add(f"action:{item['actionItemId']}")
    if item.get("kind") == "issue" and item.get("watchId") and item.get("entityId"):
        refs.add(f"issue:{item['watchId']}.{item['entityId']}")
    card = item.get("_doorCard") if isinstance(item.get("_doorCard"), dict) else {}
    for raw in (card.get("target_ref"), card.get("open_ref"), item.get("ref"), item.get("openRef"), item.get("id")):
        ref = str(raw or "").strip()
        if ":" not in ref:
            continue
        kind, _, rest = ref.partition(":")
        if not rest:
            continue
        if kind in ("action_item", "action"):
            refs.add(f"action:{rest}")
        elif kind == "decision":
            refs.add(f"decision:{rest}")
        elif kind in ("desk_decision", "decision_record"):
            refs.add(f"decision_record:{rest}")
        elif kind in ("note", "project_item"):
            refs.add(f"{kind}:{rest}")
    return refs


_LIVE_FLIGHT_STATES = ("starting", "working", "waiting", "pr_open")


def fold_asks(items: list[dict[str, Any]], flights: Iterable[dict[str, Any]]) -> None:
    """Mark each agent ask (``coder`` / ``gate`` row) whose session works an
    item in ``items`` with ``foldedInto``: that item's ref. In place."""
    by_session: dict[str, str] = {}
    for flight in flights or ():
        key = str(flight.get("session_key") or "")
        live = flight.get("state") in _LIVE_FLIGHT_STATES or (
            flight.get("state") == "merged" and flight.get("close") == "awaiting_confirm"
        )
        if key and live and flight.get("origin_ref"):
            by_session.setdefault(key, str(flight["origin_ref"]))
    if not by_session:
        return
    owners: dict[str, str] = {}
    for item in items:
        if item.get("source") in (CODER_SOURCE, GATE_SOURCE):
            continue
        for ref in item_origin_refs(item):
            owners.setdefault(ref, _item_ref(item))
    for item in items:
        if item.get("source") not in (CODER_SOURCE, GATE_SOURCE):
            continue
        origin = by_session.get(str(item.get("sessionKey") or ""))
        target = owners.get(origin or "")
        # Every ask on the item is the item's (owner ruling 2026-10-07: one
        # object, one row, always); the desk shows the most urgent one.
        if target:
            item["foldedInto"] = target


#: Betterment D0: the four directions of a row. ``mine``: the owner's own
#: work. ``theirs``: a person owes it to him. ``decide``: a decision, an
#: approval, or an agent's question waits for his answer. ``setup``: an
#: engine or a connection is missing (the blockers, a failed summary).
DIRECTIONS: tuple[str, ...] = ("mine", "theirs", "decide", "setup")

_DECIDE_SOURCES = frozenset({DECISION_SOURCE, CODER_SOURCE, GATE_SOURCE, PROGRAM_SOURCE})


def row_direction(row: dict[str, Any], is_me: Callable[[dict[str, Any]], bool]) -> str:
    """Whose move a ranked attention row is (``DIRECTIONS``)."""
    if (
        row.get("source") in _DECIDE_SOURCES
        or row.get("kind") in _DECIDE_SOURCES
        or row.get("proposalKind") == "decision"
    ):
        return "decide"
    if row.get("waiting"):
        return "theirs"
    if "_his" in row:  # a merged row: his when one of its projections is
        return "mine" if row["_his"] else "theirs"
    owner = str(row.get("owner") or "").strip()
    if owner and row.get("why") != YOURS and not is_me(row):
        return "theirs"
    return "mine"


def _due_day(due: Any) -> date | None:
    """A row's due as a local day (a bare ISO day is that day)."""
    text = str(due or "").strip()
    if not text:
        return None
    if len(text) <= 10:
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None
    stamp = parse_stamp(text)
    return stamp.date() if stamp is not None else None


def counts_in_number(item: dict[str, Any], today: date) -> bool:
    """Betterment D1, the one count rule: *mine* due today or late, *decide*
    (decisions, approvals, an agent's question), and *setup* (counted apart:
    the blockers and failed summaries). *Theirs* never counts. A promise not
    kept yet (a proposed action, a To review card) does not count until kept.

    A *mine* row with no due date (a review asked of him, a red build, an
    item nobody owns yet) has no later day to wait for: it counts. Only a
    *mine* row due on a later day waits for that day.
    """
    if item.get("askOverrides"):
        return True  # an agent asks about this item: his answer is due now
    direction = item.get("direction")
    if direction == "decide":
        return True
    if direction != "mine" or item.get("waiting"):
        return False
    if item.get("_toReview") or (item.get("proposalId") and item.get("proposalKind") != "decision"):
        return False
    dues = item.get("_hisDues") if item.get("_hisDues") else [item.get("dueAt")]
    days = [_due_day(due) for due in dues]
    return any(day is None or day <= today for day in days)


def compute_needs_you(
    *,
    door: dict[str, Any] | None = None,
    room_items: Iterable[dict[str, Any]] = (),
    muted_project_ids: Iterable[str] = (),
    assignments: dict[str, Any] | None = None,
    assignment_read: str = "pending",
    meetings: Iterable[dict[str, Any]] = (),
    decisions: Iterable[dict[str, Any]] = (),
    coders: Iterable[Any] = (),
    gate_holds: Iterable[dict[str, Any]] = (),
    flights: Iterable[dict[str, Any]] = (),
    send_items: Iterable[dict[str, Any]] = (),
    programs: Iterable[dict[str, Any]] = (),
    self_names: Iterable[str] = SELF_OWNER_NAMES,
    personal_names: Iterable[str] = (),
    known_people: Iterable[str] | None = None,
    now: datetime | None = None,
    dedup: Callable[[list[dict[str, Any]], datetime], list[dict[str, Any]]] = dedup_items,
    summary_waits: bool = True,
) -> dict[str, Any]:
    """The pure R1-R5 rule. Mirrors ``computeNeedsYou`` line for line.

    ``door`` is the Door response or its board. Returns ``members`` (stable
    refs, in face order), ``count``, ``waitingCount``, the ranked rows split
    by mute (each unmuted row marked ``waiting``), the blockers and the
    failed meetings.
    """
    clock = now or local_wall()
    room = [dict(item) for item in room_items]
    # Send rows are a membership source, but they are not Room rows.  The
    # caller keeps them out of ``roomItems`` so the cached Room projection
    # remains small and every fresh compose sees the current channel rows.
    room.extend(dict(item) for item in send_items)
    covered = {
        str(item["actionItemId"])
        for item in room
        if item.get("source") == "commitment" and item.get("actionItemId")
    }
    # PHILO-15 08: a summary action still to confirm is its proposal row;
    # its To review card is the same obligation, not a second row.
    covered |= {
        str(item["proposalActionItemId"])
        for item in room
        if item.get("proposalId") and item.get("proposalActionItemId")
    }
    board = (door or {}).get("board") if isinstance((door or {}).get("board"), dict) else (door or {})
    combined = door_items(board, covered, clock) + room
    # An item the owner himself holds is his: it reads ``YOURS``, never
    # ``WAITING ON ME``, and it is counted.
    names = list(self_names)
    personal = [str(n) for n in personal_names]
    # Rows that name a person explicitly: the owner's own name never claims them.
    identified = {str(row.get("id") or "") for row in combined if _names_another(row, personal)}
    persons = None if known_people is None else {str(n).strip().casefold() for n in known_people}

    def other(row: dict[str, Any]) -> bool:
        return waits_on_other(row, names, personal, identified, persons)

    for row in combined:
        # The Door's two-day window and its overdue column: another person's
        # item there is a wait on that person, with its due word beside it
        # (``WAITING ON ADA · OVERDUE``); his own keeps the word.
        if (row.get("_dueWord") and str(row.get("owner") or "").strip()
                and not _is_me(row, names, personal, identified, persons)):
            row["why"] = f"WAITING ON {str(row['owner']).strip().upper()} · {row['_dueWord']}"
        if _waiting_on(row) and _is_me(row, names, personal, identified, persons):
            row["why"] = YOURS
    # A People commitment never merges with another row. A merge would put
    # its text and its record ref inside another row's ``sources``, past the
    # custody boundary; it stays one row of its own.
    people = [row for row in combined if is_people_row(row)]
    others = [row for row in combined if not is_people_row(row)]
    # A decision keeps its own row and its own ref (``decision:<id>``): the
    # Brief names the same ref, so the two count it once.
    # A merged row waits on someone else only when EVERY merged projection
    # does. When one projection is the owner's own (YOURS, due, overdue), the
    # row is his: it leads with his reason and it is counted.
    # Each projection keeps its own reason and owner through every merge
    # (the Room aggregate's and this one), so the test reads the projections.
    merged = dedup(others, clock)
    for row in merged:
        sources = [source for source in row.get("sources") or [] if isinstance(source, dict)]
        if len(sources) < 2:
            row["waiting"] = other(row)
            continue
        marks = [other(source) for source in sources]
        row["waiting"] = all(marks)
        # Betterment D1: a projection that names no owner, or names him, is
        # his; their due days decide the count, and one makes the row his.
        his = [
            source for source in sources
            if not str(source.get("owner") or "").strip()
            or _is_me(source, names, personal, identified, persons)
        ]
        row["_his"] = bool(his)
        row["_hisDues"] = [source.get("dueAt") for source in his]
        if not row["waiting"] and other(row):
            his = next(source for source, mark in zip(sources, marks) if not mark)
            row["why"] = YOURS if _waiting_on(his) else (his.get("why") or row.get("why"))
            row["severity"] = his.get("severity") or row.get("severity")
    # A coder row (R5) keeps its own row and its own ref (``coder:<key>``).
    # Conductor R1: held calls of launches; a held call and the same
    # session's permission wait are one row with one notification identity.
    holds = list(gate_holds)
    coder_rows, gate_rows = correlate_gate_waits(
        coder_items(coders, clock), gate_items(holds, clock), holds, clock,
    )
    helper_rows = helper_request_items(flights, clock)
    singles = people + decision_items(decisions) + coder_rows + gate_rows + helper_rows + program_items(programs)
    for row in singles:
        row["waiting"] = other(row)
    ranked = rank_items(merged + singles, clock)
    # PHILO-14 A5, one object, one row, one count (owner ruling 2026-10-07):
    # EVERY agent ask on an item it was handed is that item's (``foldedInto``),
    # whatever the item's mute or wait. An item with an ask is shown and
    # counted once: the ask overrides its mute and its wait.
    fold_asks(ranked, flights)
    asked = {str(item["foldedInto"]) for item in ranked if item.get("foldedInto")}
    for item in ranked:
        if item.get("source") not in (CODER_SOURCE, GATE_SOURCE) and _item_ref(item) in asked:
            item["askOverrides"] = True
            item["waiting"] = False
    # Betterment D0: each row says whose move it is.
    for item in ranked:
        item["direction"] = row_direction(item, lambda row: _is_me(row, names, personal, identified, persons))
    muted_projects = {str(pid) for pid in muted_project_ids}
    unmuted_items: list[dict[str, Any]] = []
    muted_items: list[dict[str, Any]] = []
    for item in ranked:
        project_id = item.get("projectId")
        if item.get("askOverrides"):
            item["muted"] = False
            unmuted_items.append(item)
        elif bool(item.get("muted")) or (project_id and str(project_id) in muted_projects):
            item["muted"] = True
            muted_items.append(item)
        else:
            item["muted"] = False
            unmuted_items.append(item)
    # What the owner waits on someone else for is listed and is not counted.
    waiting_items = [item for item in unmuted_items if item["waiting"]]
    # Betterment D1: the one count rule (``counts_in_number``) marks each row.
    # The asks folded above are listed (the desk draws each on its item's
    # row) and are not members of their own.
    for item in muted_items:
        item["counted"] = False
    for item in unmuted_items:
        item["counted"] = not item.get("foldedInto") and counts_in_number(item, clock.date())
    counted_items = [item for item in unmuted_items if item["counted"]]

    blockers = [
        {**blocker, "direction": "setup"}
        for blocker in meeting_path_blockers(
            None if assignment_read == "failed" else assignments, assignment_read,
            summary_waits=summary_waits,
        )
    ]
    failed_meetings = [
        {**meeting, "direction": "setup"} for meeting in meetings if meeting_needs_you(meeting)
    ]
    members = (
        [{"ref": _item_ref(item), "kind": "attention"} for item in counted_items]
        + [{"ref": f"blocker:{blocker['key']}", "kind": "blocker"} for blocker in blockers]
        + [{"ref": str(meeting.get("id") or ""), "kind": "meeting"} for meeting in failed_meetings]
    )
    return {
        "members": members,
        "count": len(members),
        "waitingCount": len(waiting_items),
        "unmutedItems": unmuted_items,
        "waitingItems": waiting_items,
        "mutedItems": muted_items,
        "blockers": blockers,
        "failedMeetings": failed_meetings,
    }


# ── the hub reads ─────────────────────────────────────────────────────


def _hub_service(name: str, build: Callable[[], Any]) -> Any:
    """The hub's live service, or a bare one where no hub runs (a CLI, a rig)."""
    from holdspeak.runtime import composition

    return build() if composition.installed() is None else composition.service(name, build)


def _read_people_names(principal: Any) -> set[str] | None:
    """Every Person's name on the desk (casefolded), for the B57 tolerance.

    An empty set when this desk has no People store (nobody to protect);
    ``None`` when the store exists but cannot be read now (locked, key
    missing, a failed read): then the one-edit tolerance stays off.
    """
    try:
        people = _hub_service("people_service", lambda: None)
    except Exception:
        return None
    if people is None:
        return set()
    try:
        return people.person_names(principal)
    except Exception as exc:
        log.warning("needs-you: the People names read failed: %s", exc)
        return None


def _row_action_id(row: dict[str, Any]) -> str:
    """The action item a row stands for, or ``""``."""
    if row.get("_isDoor") and row.get("source") == "action_item":
        return str(row.get("ref") or "")
    return str(row.get("actionItemId") or row.get("proposalActionItemId") or "")


def attach_person_ids(
    items: list[dict[str, Any]], db: Any, principal: Any, is_self: Callable[[Any], bool],
) -> None:
    """Betterment D0: ``person_id`` on every row: the Person it is about.

    *theirs*: the owner, when it names exactly one Person. *mine*: the Person
    it is for (``PeopleService.my_action_people``). A People commitment: its
    relationship. Else ``""``. A store that cannot be read leaves ``""``.
    """
    for item in items:
        item["person_id"] = _person_identity(item)
        card = item.get("_doorCard") if isinstance(item.get("_doorCard"), dict) else {}
        target = str(card.get("target_ref") or "")
        if not item["person_id"] and target.startswith("people:") and is_people_row(item):
            item["person_id"] = target.removeprefix("people:")
    try:
        from holdspeak.people.key_free import people_reads_allowed

        people = _hub_service("people_service", lambda: None)
        if people is None or not people_reads_allowed():
            return
        if people.readiness_state() != "ready":
            return
        mine = people.my_action_people(db, is_self) if any(
            item.get("direction") == "mine" and _row_action_id(item) for item in items
        ) else {}
        owners: dict[str, str] = {}
        for item in items:
            if item["person_id"]:
                continue
            if item.get("direction") == "mine":
                item["person_id"] = mine.get(_row_action_id(item), "")
            elif item.get("direction") == "theirs":
                owner = str(item.get("owner") or "").strip()
                if owner and owner not in owners:
                    found = people.resolve_owner_candidates(owner)
                    rel = found.get("relationship") if found.get("link") == "linked" else None
                    owners[owner] = str((rel or {}).get("id") or "")
                item["person_id"] = owners.get(owner, "")
        # Betterment D2: the Person's name rides with its id, so the person
        # picker and an agent's ``person="Theo"`` need no second read.
        names = people.display_names() if any(item["person_id"] for item in items) else {}
        for item in items:
            if item["person_id"] and names.get(item["person_id"]):
                item["person_name"] = names[item["person_id"]]
    except Exception as exc:
        log.warning("needs-you: the People read for row people failed: %s", exc)


#: Betterment D3: at most this many of a meeting's speakers are offered as
#: "Whose?" choices.
WHOSE_CHOICES = 8


def attach_arrivals(items: list[dict[str, Any]], db: Any) -> None:
    """Betterment D3: the promises a finished summary kept on arrival.

    A row whose action item was kept on arrival and not seen yet carries
    ``arrival`` (``meetingId``, ``meetingTitle``, ``startedAt``): the face
    draws it NEW under its meeting at the top until he has seen it. The
    meeting's proposals (decisions to Decide, promises with no owner) join
    that group. A promise with no owner carries ``whose``: the meeting's
    speakers, each one press. A read that fails leaves the rows as they are.
    """
    action_ids = {_row_action_id(item) for item in items} - {""}
    proposal_ids = {str(item.get("proposalId")) for item in items if item.get("proposalId")}
    if not action_ids and not proposal_ids:
        return
    try:
        with db._connection() as conn:
            arrived: dict[str, dict[str, Any]] = {}
            if action_ids:
                for row in conn.execute(
                    """SELECT ai.id, ai.meeting_id, m.title, m.started_at
                          FROM action_items ai JOIN meetings m ON m.id = ai.meeting_id
                         WHERE ai.id IN (SELECT value FROM json_each(?)) AND ai.arrived_at IS NOT NULL
                           AND ai.arrival_seen_at IS NULL""",
                    (json.dumps(sorted(action_ids)),),
                ).fetchall():
                    arrived[str(row[0])] = {
                        "meetingId": str(row[1]), "meetingTitle": str(row[2] or ""),
                        "startedAt": str(row[3] or ""),
                    }
            proposals: dict[str, tuple[str, str, str]] = {}
            if proposal_ids:
                for row in conn.execute(
                    """SELECT id, meeting_id, kind, COALESCE(owner_supplied, owner_hint, '')
                          FROM follow_through_proposals WHERE id IN (SELECT value FROM json_each(?))""",
                    (json.dumps(sorted(proposal_ids)),),
                ).fetchall():
                    proposals[str(row[0])] = (str(row[1] or ""), str(row[2] or ""), str(row[3] or "").strip())
            unowned = {mid for mid, kind, owner in proposals.values() if kind == "action" and not owner}
            speakers: dict[str, list[str]] = {}
            for meeting_id in unowned:
                rows = conn.execute(
                    """SELECT speaker FROM segments WHERE meeting_id = ?
                        GROUP BY speaker ORDER BY MIN(start_time)""",
                    (meeting_id,),
                ).fetchall()
                names = [str(r[0]).strip() for r in rows if str(r[0] or "").strip()]
                speakers[meeting_id] = [n for n in names if n.casefold() not in {"unknown", "speaker"}][:WHOSE_CHOICES]
    except Exception as exc:
        log.warning("needs-you: the arrival read failed: %s", exc)
        return
    groups = {group["meetingId"]: group for group in arrived.values()}
    for item in items:
        group = arrived.get(_row_action_id(item))
        proposal = proposals.get(str(item.get("proposalId") or ""))
        if group is None and proposal is not None:
            group = groups.get(proposal[0])
        if group is not None:
            item["arrival"] = dict(group)
        if proposal is not None and proposal[1] == "action" and not proposal[2]:
            item["whose"] = list(speakers.get(proposal[0], []))


def mark_arrivals_seen(db: Any, meeting_ids: Iterable[str]) -> int:
    """Betterment D3: he has seen these meetings' kept promises; they leave
    the NEW group (they stay in the list). Returns the rows marked."""
    ids = sorted({str(mid) for mid in meeting_ids if str(mid or "").strip()})
    if not ids:
        return 0
    with db._connection() as conn:
        changed = conn.execute(
            """UPDATE action_items SET arrival_seen_at = ?
                 WHERE meeting_id IN (SELECT value FROM json_each(?))
                   AND arrived_at IS NOT NULL AND arrival_seen_at IS NULL""",
            (utc_now_iso(), json.dumps(ids)),
        ).rowcount
    return int(changed or 0)


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

    # The four asking columns only: the rule does not read the active
    # thoughts, the calendar or the week.
    door = _hub_service("door_service", bare)
    return {"board": door.asking_board(principal), "people_store_state": door.people_store_state(principal)}


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


def _read_decisions(db: Any, principal: Any) -> list[dict[str, Any]]:
    """The decisions that wait for the owner's review, through their service.

    A Desk decision that is ``proposed``; a meeting's decision that is
    ``recorded`` (the owner has not accepted or rejected it).
    """
    # The hub composes no shared instance of this service (its route builds
    # one for each request), so a fresh one over the same database is equal.
    from .decision_lifecycle_service import DecisionLifecycleService

    service = DecisionLifecycleService(db)
    out: list[dict[str, Any]] = []
    for desk in service.list_decisions(principal, limit=500).get("decisions") or []:
        if str(desk.get("status") or "") != "proposed":
            continue
        out.append({
            "id": desk.get("id"),
            "title": desk.get("title") or desk.get("decision_markdown") or desk.get("id"),
            "projectId": "",
            "since": desk.get("created_at") or "",
            "status": desk.get("status") or "proposed",
        })
    proposals: dict[str, list[Any]] = {}

    def has_proposal(record: dict[str, Any]) -> bool:
        return meeting_decision_asks_elsewhere(
            db, meeting_id=record.get("source_meeting_id"),
            artifact_id=record.get("source_artifact_id"), text=record.get("text"), cache=proposals,
        )

    offset = 0
    while True:
        rows = list(service.list_decisions(
            principal, lifecycle="recorded", limit=500, offset=offset,
        ).get("decisions") or [])
        for record in rows:
            if has_proposal(record):
                continue
            out.append({
                "id": record.get("id"),
                "title": record.get("text") or record.get("id"),
                "projectId": record.get("project_key") or "",
                "since": record.get("created_at") or "",
            })
        offset += len(rows)
        if len(rows) < 500:
            break
    return out


def _read_arming(db: Any, now: datetime | None = None) -> list[dict[str, Any]]:
    """Read active arming rows and a recent failed fire for Needs you.

    A failed or missed fire remains actionable for that meeting's duration.
    The service owns the receipt wording; this read only applies the same
    relevance window as Meetings ▸ Record.
    """
    from .scheduled_recording_service import ScheduledRecordingService

    service = ScheduledRecordingService(db)

    def successful_record_for_event(
        calendar_event_id: str, failed_at: datetime | None,
    ) -> bool:
        if not calendar_event_id or failed_at is None:
            return False
        with db._connection() as conn:
            meeting_rows = conn.execute(
                """SELECT started_at FROM meetings
                   WHERE calendar_event_id = ?
                     AND capture_status IN ('recording', 'finalized', 'recovered')
                """,
                (calendar_event_id,),
            ).fetchall()
        # Compare parsed instants because old rows can use SQLite UTC stamps
        # or local wall-clock ISO values. An earlier successful occurrence
        # must not clear a later failed occurrence for the same event ID.
        failed_instant = failed_at.timestamp()
        return any(
            (started := parse_stamp(row["started_at"])) is not None
            and started.timestamp() >= failed_instant
            for row in meeting_rows
        )

    now_epoch = (now or utc_now()).timestamp()
    rows = []
    for rec in db.scheduled_recordings.list_all():
        if str(getattr(rec, "state", "")) == "arming":
            rows.append({"scheduleId": str(rec.id), "title": str(rec.title or ""),
                         "armedAt": getattr(rec, "armed_at", None)})
            continue
        failed = service._did_not_record(rec)
        if not failed:
            continue
        at = parse_stamp(failed.get("at"))
        if at is None:
            continue
        # Record now starts the named calendar meeting. Keep the failed
        # occurrence and its receipt in scheduled_recordings, but resolve its
        # live Needs-you row once that meeting has a successful capture state.
        if successful_record_for_event(
            str(getattr(rec, "calendar_event_id", "") or ""), at,
        ):
            continue
        age = now_epoch - at.timestamp()
        if 0 <= age <= max(60, int(getattr(rec, "duration_minutes", 0)) * 60):
            rows.append({
                "scheduleId": str(rec.id),
                "title": str(rec.title or ""),
                "armedAt": None,
                "didNotRecord": failed,
                "calendarEventId": str(getattr(rec, "calendar_event_id", "") or ""),
            })
    return rows


def unread_sources(coverage: Iterable[Any]) -> list[dict[str, Any]]:
    """PHILO-15-09 (B11): the coverage records the desk draws as rows."""
    # PHILO-15 B60: a source held by HoldSpeak's own quiet hours is listed
    # with its quiet end and is never counted.
    return [
        row for row in coverage or ()
        if isinstance(row, dict) and row.get("state") not in ("available", "quiet")
    ]


def _first_line(text: Any) -> str:
    return " ".join(str(text or "").strip().split("\n")[0].split()).casefold()


def source_group_key(row: dict[str, Any]) -> tuple[str, ...]:
    """PHILO-17 (needsyou): the cause of an unread source and where its
    repair goes. Sources with the same cause AND the same repair (verb,
    destination, egress host) are ONE Needs-you row (``GitHub · 30 sources``
    with one Reconnect), so the one number counts the cause once. A source
    with no plain cause groups only with the same first error line, so two
    different failures are never one row. The twin is ``gapGroupKey`` in
    ``web/src/desk/coverage.ts``."""
    repair = row.get("repair") if isinstance(row.get("repair"), dict) else {}
    cause = str(row.get("cause") or "").strip() or _first_line(row.get("reason"))
    return (
        str(row.get("provider") or row.get("kind") or ""),
        str(row.get("state") or ""),
        str(repair.get("token") or ""),
        cause,
        str(repair.get("verb") or ""),
        str(repair.get("href") or ""),
        str(row.get("host") or ""),
    )


def unread_source_groups(coverage: Iterable[Any]) -> list[list[dict[str, Any]]]:
    """The unread sources, grouped by cause, in first-seen order."""
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in unread_sources(coverage):
        groups.setdefault(source_group_key(row), []).append(row)
    return list(groups.values())


def _read_coders() -> list[Any]:
    """The coder sessions the agent hooks recorded (``agent_context``).

    Strict: an absent registry (first run) is no sessions; an unreadable or
    invalid one raises, so the answer names it and is never a false
    all-clear."""
    from holdspeak import agent_context
    from holdspeak.services.agent_responder import annotate_sessions

    sessions = list(agent_context.read_agent_sessions_strict())
    try:
        # Conductor K5: each wait carries HoldSpeak's answer record.
        return annotate_sessions(sessions)
    except Exception as exc:  # the record is a garnish, never a reason to drop a wait
        log.warning("needs-you: the answer records were not read: %s", exc)
        return sessions


def _decision_text(text: Any) -> str:
    return " ".join(str(text or "").split()).lower()


def meeting_decision_asks_elsewhere(
    db: Any, *, meeting_id: Any, artifact_id: Any, text: Any,
    cache: dict[str, list[Any]] | None = None,
) -> bool:
    """True when a recorded meeting decision does not ask for review itself.

    One meeting decision is ONE member. The proposal bridge makes a proposal
    from the same artifact and text. When that proposal is in a Room (its row
    is the one that asks), or the owner has confirmed or dismissed it (he has
    decided), the recorded decision does not ask a second time. The one
    ``needs you`` rule and the Brief's DECISIONS section both use this.
    """
    meeting = str(meeting_id or "")
    if not meeting:
        return False
    cache = cache if cache is not None else {}
    if meeting not in cache:
        cache[meeting] = [
            proposal for proposal in db.proposals.list_proposals(meeting_id=meeting)
            if proposal.kind == "decision"
        ]
    wanted = _decision_text(text)
    artifact = str(artifact_id or "")
    for proposal in cache[meeting]:
        if str(proposal.source_artifact_id or "") != artifact:
            continue
        if wanted not in (_decision_text(proposal.text), _decision_text(proposal.original_text)):
            continue
        if proposal.state != "proposed" or proposal.project_id:
            return True
    return False


def _is_owner(principal: Any) -> bool:
    from holdspeak.principals import PrincipalKind

    return getattr(principal, "kind", None) is PrincipalKind.OWNER


def heartbeat_muted_projects(db: Any) -> set[str]:
    """The heartbeat's muted projects (empty when the setting is unreadable)."""
    try:
        from .heartbeat_service import HeartbeatService

        return {str(pid) for pid in HeartbeatService(db).get_settings().get("muted_projects", [])}
    except Exception:
        return set()


def _reason(exc: Exception) -> str:
    return str(exc).split("\n")[0][:200] or type(exc).__name__


def _send_actor_label(send: dict[str, Any]) -> str:
    """The short human name on a Ready-to-send row.

    A completed automation prepares as the owner principal. Its source-owned
    provenance is frozen in the existing document_json, so an ordinary owner
    prepared send still reads ``you`` when that marker is absent.
    """
    prepared_by = send.get("prepared_by")
    prepared = prepared_by if isinstance(prepared_by, dict) else {}
    kind = str(prepared.get("kind") or "").strip().lower()
    identity = str(prepared.get("identity") or kind or "agent").strip()
    if kind == "owner":
        document_json = send.get("document_json")
        origin = document_json.get("automation_origin") if isinstance(document_json, dict) else None
        document_ref = str(send.get("document_ref") or "")
        artifact_id = document_ref.removeprefix("artifact:").strip()
        if (
            document_ref.startswith("artifact:")
            and isinstance(origin, dict)
            and str(origin.get("kind") or "") == "automation"
            and str(origin.get("artifact_id") or "") == artifact_id
        ):
            name = str(origin.get("workbench_name") or "").strip()
            if name:
                return name
        return "you"
    if "claude" in identity.casefold():
        return "Claude Code"
    if "codex" in identity.casefold():
        return "Codex"
    # Scheduler and agent identities are durable producer labels. Make the
    # value readable without exposing a raw operation id on the face.
    words = " ".join(identity.replace("_", "-").split("-"))
    return words[:1].upper() + words[1:] if words else "Agent"


def _send_attention_rows(db: Any, principal: Any) -> tuple[list[dict[str, Any]], dict[str, Any], str | None]:
    """Read channel sends into the existing Needs-you membership source.

    The global Needs-you answer is owner-visible. A non-owner principal gets
    the source coverage record but no document title, destination, or frozen
    preview. Failed and unknown rows are replaced by a newer attempt for the
    same document and destination; that is the existing channel history's
    durable acted-on marker and needs no second attention table.
    """
    from holdspeak.principals import PrincipalKind
    from .channel_service import ChannelService

    observed_at = utc_now_iso()
    coverage = {
        "source_id": "sends", "kind": "send", "state": "available",
        "observed_at": observed_at, "label": "Sends", "project_id": "",
        "reason": None, "repair": None,
    }
    principal_kind = getattr(getattr(principal, "kind", None), "value", getattr(principal, "kind", None))
    if principal_kind != PrincipalKind.OWNER.value:
        return [], coverage, None
    try:
        service = _hub_service("channel_service", lambda: ChannelService(db))
        sends = service.sends(principal).get("sends") or []
    except Exception as exc:
        reason = _reason(exc)
        coverage.update({
            "state": "failed", "observed_at": None, "reason": reason,
            "repair": {"token": "READ FAILED", "verb": "Retry", "href": "/"},
        })
        return [], coverage, reason

    candidates = [row for row in sends if str(row.get("state") or "") in {"prepared", "failed", "unknown"}]
    # ``created_at`` is deliberately second-granular. SQLite's rowid is the
    # durable insertion order for a prepared retry, which has no dispatch_seq
    # until the owner presses it.
    try:
        with db._connection() as conn:
            durable_order = {
                str(row["id"]): int(row["rowid"])
                for row in conn.execute("SELECT id, rowid FROM channel_sends")
            }
    except Exception:
        durable_order = {}
    rows: list[dict[str, Any]] = []
    for send in candidates:
        state = str(send.get("state") or "")
        if state in {"failed", "unknown"}:
            def later(other: dict[str, Any]) -> bool:
                created = str(send.get("created_at") or "")
                other_created = str(other.get("created_at") or "")
                if other_created > created:
                    return True
                # SQLite's channel timestamps are second-granular. The
                # durable row order handles a prepared retry, which has no
                # dispatch sequence until the owner presses it.
                if other_created == created:
                    current_order = durable_order.get(str(send.get("id") or ""))
                    other_order = durable_order.get(str(other.get("id") or ""))
                    if current_order is not None and other_order is not None and other_order != current_order:
                        return other_order > current_order
                    try:
                        return int(other.get("dispatch_seq") or 0) > int(send.get("dispatch_seq") or 0)
                    except (TypeError, ValueError):
                        return False
                return False

            newer = any(
                other is not send
                and str(other.get("document_ref") or "") == str(send.get("document_ref") or "")
                and str(other.get("destination_id") or "") == str(send.get("destination_id") or "")
                and later(other)
                and str(other.get("state") or "") != "discarded"
                for other in sends
            )
            if newer:
                continue
        provenance = send.get("document_json") if isinstance(send.get("document_json"), dict) else {}
        title = str(provenance.get("title") or send.get("document_ref") or "Document")
        label = str(provenance.get("label") or "DOCUMENT")
        destination = str(send.get("destination_name") or "Destination")
        why = {"prepared": "READY TO SEND", "failed": "NOT SENT", "unknown": "NO ANSWER"}[state]
        severity = {"prepared": "info", "failed": "danger", "unknown": "warning"}[state]
        rows.append({
            "id": f"send:{send.get('id')}", "ref": f"send:{send.get('id')}",
            "kind": "send", "source": "send", "title": title,
            "documentLabel": label, "documentTitle": title,
            "documentRef": send.get("document_ref"), "sendId": send.get("id"),
            "destinationId": send.get("destination_id"), "destinationName": destination,
            "why": why, "severity": severity, "ageToken": send.get("created_at"),
            "since": send.get("created_at"), "dueAt": None, "owner": "you",
            "preparedBy": _send_actor_label(send), "counted": True,
            # The frozen send is available to the owner's Desk face. The
            # non-owner return above prevents it from entering global MCP.
            "send": send,
        })
    return rows, coverage, None


def compose(
    db: Any,
    principal: Any,
    aggregate: dict[str, Any],
    *,
    muted_project_ids: Iterable[str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """The full ``desk.needs_you`` answer over a Room aggregate.

    ``muted_project_ids`` defaults to the heartbeat's muted projects.

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
    if muted_project_ids is None:
        muted_project_ids = heartbeat_muted_projects(db)
    muted = {str(pid) for pid in muted_project_ids}
    room_complete = bool(aggregate.get("roomComplete", aggregate.get("complete", True)))
    errors: dict[str, str] = {}

    send_items, send_coverage, send_error = _send_attention_rows(db, principal)
    if send_error:
        errors["sends"] = send_error

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

    decisions: list[dict[str, Any]] = []
    try:
        decisions = _read_decisions(db, principal)
    except Exception as exc:
        log.warning("needs-you: the decision read failed: %s", exc)
        errors["decisions"] = _reason(exc)

    # R5: the coder session registry (the hooks write it; one file read).
    coders: list[Any] = []
    coder_coverage = {
        "source_id": "coders", "kind": "coder", "state": "available",
        "observed_at": utc_now_iso(), "label": "Agents", "project_id": "",
        "reason": None, "repair": None,
    }
    try:
        coders = _read_coders()
    except Exception as exc:
        log.warning("needs-you: the coder read failed: %s", exc)
        errors["coders"] = _reason(exc)
        coder_coverage.update({
            "state": "failed", "observed_at": None, "reason": _reason(exc),
            "repair": {"token": "READ FAILED", "verb": "Retry", "href": "/"},
        })

    # Conductor R1: the tool calls the gate holds for HoldSpeak launches.
    gate_holds: list[dict[str, Any]] = []
    try:
        gate_holds = _read_gate_holds(db)
    except Exception as exc:
        log.warning("needs-you: the gate read failed: %s", exc)
        errors["gate"] = _reason(exc)

    names, personal = configured_owner_names()
    # PHILO-15 B57 (Astra r1 P1): the People on the desk, so a one-edit
    # mishearing never takes a real colleague's work.
    known_people = _read_people_names(principal)

    # PHILO-14 A5: the items agents were handed, so an ask on one is that item.
    flights: list[dict[str, Any]] = []
    try:
        from .agent_flights import agent_flights

        flights = agent_flights(db, coders)
    except Exception as exc:
        log.warning("needs-you: the flight read failed: %s", exc)

    # Programs (2026-10-28): merge asks, findings left, parked steps.
    programs: list[dict[str, Any]] = []
    try:
        from .program_service import default_program_service

        programs = default_program_service(db).needs_you_items()
    except Exception as exc:
        log.warning("needs-you: the program read failed: %s", exc)
        errors["programs"] = _reason(exc)

    result = compute_needs_you(
        door=door,
        room_items=room_items,
        muted_project_ids=muted,
        assignments=assignments,
        assignment_read=assignment_read,
        meetings=meetings,
        decisions=decisions,
        coders=coders,
        summary_waits=_a_meeting_waits_for_summary(db),
        gate_holds=gate_holds,
        flights=flights,
        send_items=send_items,
        programs=programs,
        self_names=names,
        personal_names=personal,
        known_people=known_people,
        now=now,
    )
    attach_person_ids(
        result["unmutedItems"] + result["mutedItems"], db, principal,
        lambda owner: _is_me({"owner": owner}, names, personal, (), known_people),
    )
    # Betterment D3: the promises kept on arrival, NEW under their meeting.
    attach_arrivals(result["unmutedItems"], db)
    answer = dict(aggregate)
    # One coder coverage record: a recomposed cached answer carries the last
    # one, so it is replaced, never added twice.
    coverage = [
        row for row in (aggregate.get("coverage") or [])
        if not (isinstance(row, dict) and row.get("kind") in {"coder", "send"})
    ]
    answer["coverage"] = coverage + [coder_coverage, send_coverage]
    # PHILO-15-09 (B11, the A5 ruling: headline = Dock badge = notch =
    # counted rows): the one number counts every row the desk draws under
    # the head: the members, each source that could not be read, and a
    # recording that arms. An agent's ask is folded into its item above.
    arming: list[dict[str, Any]] = []
    try:
        arming = _read_arming(db, now)
    except Exception as exc:
        log.warning("needs-you: the arming read failed: %s", exc)
    # PHILO-17 (needsyou): sources of one cause are one row, counted once.
    unread = unread_source_groups(answer["coverage"])
    answer.update({
        "count": result["count"] + len(unread) + len(arming),
        "arming": arming,
        # What the owner waits on someone else for: listed, marked
        # ``waiting`` on its row, not counted.
        "waitingCount": result["waitingCount"],
        # The names that mean the owner (the browser twin's input).
        "ownerNames": sorted({*names, *personal}),
        "members": result["members"],
        # Every attention row, ranked: the unmuted rows, then the muted ones.
        "items": result["unmutedItems"] + result["mutedItems"],
        "mutedCount": len(result["mutedItems"]),
        "blockers": result["blockers"],
        "failedMeetings": result["failedMeetings"],
        "projects": sorted({
            str(item["projectId"]) for item in result["unmutedItems"]
            if item.get("projectId") and item.get("counted")
        }),
        # The members by Project: the per-Project number every face shows
        # (the shade's Projects list, the palette's project badge). It is
        # the one rule's count split by Project, so a Project never shows a
        # row the head does not count (a muted or a waiting row).
        "projectCounts": project_counts(result["unmutedItems"]),
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


_MEMBERSHIP_KEYS = (
    "members", "blockers", "failedMeetings", "sourceErrors", "peopleStoreState", "peopleWithheld",
    "waitingCount", "ownerNames", "projectCounts", "arming",
)


def project_counts(unmuted_items: Iterable[dict[str, Any]]) -> dict[str, int]:
    """The counted attention rows by Project: ``{projectId: n}``.

    A row counts when it is a member (unmuted, not ``waiting``, and marked
    ``counted`` by the one count rule). The sum is the attention part of
    ``count``; a member with no Project (a Door card, a blocker, a failed
    meeting) is in ``count`` and in no Project.
    """
    counts: dict[str, int] = {}
    for item in unmuted_items:
        project_id = item.get("projectId")
        if not project_id or item.get("muted") or item.get("waiting") or item.get("foldedInto"):
            continue
        if item.get("counted") is False:
            continue
        counts[str(project_id)] = counts.get(str(project_id), 0) + 1
    return counts


#: Betterment D2: the filters of the one list (the face's chips, the route's
#: query, ``desk.needs_you``'s arguments).
FILTER_KEYS: tuple[str, ...] = ("direction", "person", "project", "week")


def _folded(text: Any) -> str:
    return " ".join(str(text or "").split()).casefold()


def _row_due_day(row: dict[str, Any]) -> date | None:
    return _due_day(row.get("dueAt") or row.get("proposalDue"))


def row_passes(
    row: dict[str, Any],
    *,
    direction: str | None = None,
    person: str | None = None,
    project: str | None = None,
    week: bool = False,
    today: date | None = None,
) -> bool:
    """True when ``row`` passes every given filter (they combine).

    ``direction``: the row's ``direction``. ``person``: a Person id, or a
    name (the whole name or its first word) of the row's Person or of its
    owner. ``project``: a Project id or its name. ``week``: the row is due
    on or before this week's Sunday (a late row is due this week too).
    """
    if direction and row.get("direction") != direction:
        return False
    if person:
        wanted = _folded(person)
        names = [_folded(row.get("person_name")), _folded(row.get("owner")) if not row.get("person_id") else ""]
        ids = {_folded(row.get("person_id"))} - {""}
        if wanted not in ids and not any(
            name and (wanted == name or wanted == name.split(" ")[0]) for name in names
        ):
            return False
    if project:
        wanted = _folded(project)
        if wanted not in {_folded(row.get("projectId")), _folded(row.get("projectName"))} - {""}:
            return False
    if week:
        day = _row_due_day(row)
        clock = today or local_wall().date()
        if day is None or day > clock + timedelta(days=6 - clock.weekday()):
            return False
    return True


def filter_answer(
    answer: dict[str, Any],
    *,
    direction: str | None = None,
    person: str | None = None,
    project: str | None = None,
    week: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Betterment D2: the one answer narrowed to the rows that pass the filters.

    ``items``, ``blockers`` and ``failedMeetings`` keep the rows that pass
    (a blocker or a failed summary is a *setup* row with no person, Project
    or date). ``count`` and ``members`` stay the desk's one number: a filter
    narrows the list, never the number. ``filter`` says what was applied and
    ``shown`` how many rows passed. No filter given: the answer unchanged.
    """
    given = {
        "direction": direction or None, "person": person or None,
        "project": project or None, "week": bool(week),
    }
    if not any(given.values()):
        return answer
    today = (now or local_wall()).date()

    def passes(row: dict[str, Any]) -> bool:
        return row_passes(row, direction=given["direction"], person=given["person"],
                          project=given["project"], week=given["week"], today=today)

    out = dict(answer)
    out["items"] = [row for row in answer.get("items") or [] if isinstance(row, dict) and passes(row)]
    for key in ("blockers", "failedMeetings"):
        out[key] = [row for row in answer.get(key) or [] if isinstance(row, dict) and passes(row)]
    out["filter"] = {key: value for key, value in given.items() if value}
    out["shown"] = len(out["items"]) + len(out["blockers"]) + len(out["failedMeetings"])
    return out


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


def _opaque_people_ref(ref: Any) -> str:
    """A stable ref for one commitment that names neither its record nor its text."""
    import hashlib

    return f"{PEOPLE_SOURCE}:{hashlib.sha256(str(ref).encode('utf-8')).hexdigest()[:12]}"


def _carries_people(row: dict[str, Any]) -> bool:
    if is_people_row(row):
        return True
    card = row.get("_doorCard")
    if isinstance(card, dict) and card.get("source") == PEOPLE_SOURCE:
        return True
    return any(
        isinstance(source, dict) and source.get("source") == PEOPLE_SOURCE
        for source in row.get("sources") or []
    )


def withhold_people_content(answer: dict[str, Any]) -> dict[str, Any]:
    """The same answer and the same number, with People content withheld.

    For every reader outside the People custody boundary: the observed
    service call (its result is written to ``pipeline_events``), an MCP agent,
    a stored Brief, a notification. The commitment is still a member and is
    still counted; its text, its Door card and its record ref are not
    disclosed. A row is withheld whole when ANY part of it carries People
    content: its own source, its Door card, or a merged ``sources`` entry.
    """
    out = dict(answer)
    refs: dict[str, str] = {}
    items: list[dict[str, Any]] = []
    for row in answer.get("items") or []:
        if not _carries_people(row):
            items.append(row)
            continue
        own = str(row.get("ref") or row.get("id") or "")
        ref = _opaque_people_ref(own)
        refs[own] = ref
        items.append({
            "id": ref, "ref": ref, "source": PEOPLE_SOURCE, "kind": row.get("kind"),
            "title": PEOPLE_ROW_TITLE, "why": row.get("why"), "severity": row.get("severity"),
            "rankClass": row.get("rankClass"), "rank": row.get("rank"),
            "projectId": "", "muted": bool(row.get("muted")),
            "waiting": bool(row.get("waiting")),
            # Betterment D2: whose move it is and whether it counts are not
            # People content; a ``direction`` filter still finds the row.
            "direction": row.get("direction"), "counted": row.get("counted"),
        })
    out["items"] = items
    out["members"] = [
        {**member, "ref": refs.get(str(member.get("ref")), member.get("ref"))}
        for member in answer.get("members") or []
    ]
    out["peopleWithheld"] = True
    return out


__all__ = [
    "CODER_SOURCE",
    "coder_items",
    "helper_request_items",
    "PEOPLE_ROW_TITLE",
    "PEOPLE_SOURCE",
    "is_people_row",
    "room_part",
    "withhold_people_content",
    "DOOR_COLUMNS",
    "compose",
    "attach_arrivals",
    "compute_needs_you",
    "filter_answer",
    "mark_arrivals_seen",
    "row_passes",
    "decision_items",
    "meeting_decision_asks_elsewhere",
    "owner_names",
    "sounds_like_owner",
    "SELF_OWNER_NAMES",
    "waits_on_other",
    "door_items",
    "meeting_needs_you",
    "meeting_path_blockers",
    "source_group_key",
    "unread_source_groups",
    "meeting_summary_badge",
]
