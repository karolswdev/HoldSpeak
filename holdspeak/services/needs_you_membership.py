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
        updated in the last 30 minutes (``agent_context``'s recent default).
        Each is an attention row of kind ``coder`` that ranks with the
        due-today rows (a blocked agent costs time now).

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

import logging
from datetime import datetime, timezone
from holdspeak.timestamps import local_wall, utc_now_iso
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
            has_owner = bool(str(owner or "").strip())
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
            "severity": "warning",
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
        is_blocked,
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
            "question": _excerpt(question),
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
        })
    return rows


def _args_cut(args_head: str, args_len: Any) -> dict[str, Any]:
    """PHILO-14 A5: is the stored head the whole call? The hub keeps only the
    first ``ARGS_HEAD_CHARS`` of the redacted call (a design limit: the hook
    never sends it whole). ``args_cut`` when the call is longer than its head;
    an older hook sends no length, and a head at the limit reads as cut."""
    from holdspeak.db.gate import ARGS_HEAD_CHARS

    head = str(args_head or "")
    try:
        total = max(0, int(args_len or 0))
    except (TypeError, ValueError):
        total = 0
    cut = total > len(head) if total else len(head) >= ARGS_HEAD_CHARS
    return {"args_cut": cut, "args_hidden": max(0, total - len(head)) if cut else 0}


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
                "command": _gate_command(proposal.args_head),
                **_args_cut(proposal.args_head, (proposal.operation or {}).get("args_len")),
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
    return bool(owner) and str(row.get("why") or "").strip().upper() == f"WAITING ON {owner.upper()}"


def _person_identity(row: dict[str, Any]) -> str:
    """The People relationship a row names explicitly, or ``""``.

    A Door card linked to a person carries ``person_relationship_id``
    (door_service.py, HS-149-03/04); the attention row keeps the card.
    """
    card = row.get("_doorCard") if isinstance(row.get("_doorCard"), dict) else {}
    return str(row.get("person_relationship_id") or card.get("person_relationship_id") or "")


def _is_me(
    row: dict[str, Any],
    self_names: Iterable[str],
    personal_names: Iterable[str] = (),
    identified: Iterable[str] = (),
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
    if _person_identity(row) or str(row.get("id") or "") in set(identified):
        return False
    return _is_self(owner, personal_names)


def waits_on_other(
    row: dict[str, Any],
    self_names: Iterable[str] = SELF_OWNER_NAMES,
    personal_names: Iterable[str] = (),
    identified: Iterable[str] = (),
) -> bool:
    """True when the owner waits on SOMEONE ELSE for this row.

    The row names an owner who is not the owner himself, and its reason is
    ``WAITING ON <that owner>``: a Door card in the ``waiting`` column, or a
    Room commitment with an owner and a later due date. ``WAITING ON YOUR
    REVIEW`` names no owner and is the owner's own work.
    """
    return _waiting_on(row) and not _is_me(row, self_names, personal_names, identified)


def owner_names(extra: Iterable[Any] = ()) -> list[str]:
    """The names that mean the owner: the reserved ones and the given ones."""
    names = set(SELF_OWNER_NAMES)
    names.update(str(name).strip().casefold() for name in extra if str(name or "").strip())
    return sorted(names)


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
    self_names: Iterable[str] = SELF_OWNER_NAMES,
    personal_names: Iterable[str] = (),
    now: datetime | None = None,
    dedup: Callable[[list[dict[str, Any]], datetime], list[dict[str, Any]]] = dedup_items,
) -> dict[str, Any]:
    """The pure R1-R5 rule. Mirrors ``computeNeedsYou`` line for line.

    ``door`` is the Door response or its board. Returns ``members`` (stable
    refs, in face order), ``count``, ``waitingCount``, the ranked rows split
    by mute (each unmuted row marked ``waiting``), the blockers and the
    failed meetings.
    """
    clock = now or local_wall()
    room = [dict(item) for item in room_items]
    covered = {
        str(item["actionItemId"])
        for item in room
        if item.get("source") == "commitment" and item.get("actionItemId")
    }
    board = (door or {}).get("board") if isinstance((door or {}).get("board"), dict) else (door or {})
    combined = door_items(board, covered, clock) + room
    # An item the owner himself holds is his: it reads ``YOURS``, never
    # ``WAITING ON ME``, and it is counted.
    names = list(self_names)
    personal = [str(n) for n in personal_names]
    # Rows that name a person explicitly: the owner's own name never claims them.
    identified = {str(row.get("id") or "") for row in combined if _person_identity(row)}

    def other(row: dict[str, Any]) -> bool:
        return waits_on_other(row, names, personal, identified)

    for row in combined:
        if _waiting_on(row) and _is_me(row, names, personal, identified):
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
    singles = people + decision_items(decisions) + coder_rows + gate_rows
    for row in singles:
        row["waiting"] = other(row)
    ranked = rank_items(merged + singles, clock)
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
    # What the owner waits on someone else for is listed and is not counted.
    waiting_items = [item for item in unmuted_items if item["waiting"]]
    counted_items = [item for item in unmuted_items if not item["waiting"]]
    # PHILO-14 A5, one object, one count (UX-CANON D): an agent's ask (a
    # question, a held call) on an item it was handed is part of that item.
    # The ask stays listed (``foldedInto`` names the item; the desk draws it
    # on the item's row) and is not a member of its own.
    fold_asks(counted_items, flights)
    counted_items = [item for item in counted_items if not item.get("foldedInto")]

    blockers = meeting_path_blockers(
        None if assignment_read == "failed" else assignments, assignment_read,
    )
    failed_meetings = [meeting for meeting in meetings if meeting_needs_you(meeting)]
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

    # The names that mean the owner: the reserved ones, his speaker label,
    # and the name and aliases he gave on first run (``config.owner``).
    speaker: list[Any] = []
    personal: list[str] = []
    try:
        from holdspeak.config import Config

        config = Config.load()
        speaker = [config.meeting.mic_label]
        personal = [name.strip().casefold() for name in config.owner.names()]
    except Exception as exc:
        log.warning("needs-you: the owner names read failed: %s", exc)
    names = owner_names(speaker)

    # PHILO-14 A5: the items agents were handed, so an ask on one is that item.
    flights: list[dict[str, Any]] = []
    try:
        from .agent_flights import agent_flights

        flights = agent_flights(db, coders)
    except Exception as exc:
        log.warning("needs-you: the flight read failed: %s", exc)

    result = compute_needs_you(
        door=door,
        room_items=room_items,
        muted_project_ids=muted,
        assignments=assignments,
        assignment_read=assignment_read,
        meetings=meetings,
        decisions=decisions,
        coders=coders,
        gate_holds=gate_holds,
        flights=flights,
        self_names=names,
        personal_names=personal,
        now=now,
    )
    answer = dict(aggregate)
    # One coder coverage record: a recomposed cached answer carries the last
    # one, so it is replaced, never added twice.
    coverage = [
        row for row in (aggregate.get("coverage") or [])
        if not (isinstance(row, dict) and row.get("kind") == "coder")
    ]
    answer["coverage"] = coverage + [coder_coverage]
    answer.update({
        "count": result["count"],
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
            if item.get("projectId") and not item.get("waiting")
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
    "waitingCount", "ownerNames", "projectCounts",
)


def project_counts(unmuted_items: Iterable[dict[str, Any]]) -> dict[str, int]:
    """The counted attention rows by Project: ``{projectId: n}``.

    A row counts when it is a member (unmuted and not ``waiting``). The sum is
    the attention part of ``count``; a member with no Project (a Door card,
    a blocker, a failed meeting) is in ``count`` and in no Project.
    """
    counts: dict[str, int] = {}
    for item in unmuted_items:
        project_id = item.get("projectId")
        if not project_id or item.get("muted") or item.get("waiting") or item.get("foldedInto"):
            continue
        counts[str(project_id)] = counts.get(str(project_id), 0) + 1
    return counts


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
    "PEOPLE_ROW_TITLE",
    "PEOPLE_SOURCE",
    "is_people_row",
    "room_part",
    "withhold_people_content",
    "DOOR_COLUMNS",
    "compose",
    "compute_needs_you",
    "decision_items",
    "meeting_decision_asks_elsewhere",
    "owner_names",
    "SELF_OWNER_NAMES",
    "waits_on_other",
    "door_items",
    "meeting_needs_you",
    "meeting_path_blockers",
    "meeting_summary_badge",
]
