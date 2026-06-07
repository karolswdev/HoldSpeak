"""Meeting aftercare aggregation (Phase 49, HS-49-01).

A read-only rollup over data that already exists — meetings, action items, and
the `decisions` artifact — answering the three questions a person actually has
after a meeting:

- **What's still open for me?** the pending action items, grouped by owner.
- **What did we decide?** the decisions captured for this meeting.
- **What changed since last meeting?** a real diff of decisions and action
  items against the chronologically previous meeting.

Nothing here writes, and nothing is fabricated. When there is no prior meeting,
or nothing changed, the diff stays empty rather than inventing a delta. The
caller decides whether to render at all via the `is_empty` flag.
"""
from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # avoid an import cycle; the DB container imports models, not this
    from .db import Database


def _norm(value: object) -> str:
    """Normalize text for set-membership comparisons (case/space folded)."""
    return " ".join(str(value or "").strip().lower().split())


def _clean_owner(owner: object) -> Optional[str]:
    """A blank/whitespace owner is treated as unassigned (None)."""
    text = str(owner or "").strip()
    return text or None


def _coerce_timestamp(value: object) -> Optional[float]:
    """Return a float meeting-offset only when one really exists."""
    if isinstance(value, bool):  # bool is an int subclass; never a timestamp
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def resolve_provenance_segment(
    segments: list[Any], source_timestamp: object
) -> Optional[dict[str, Any]]:
    """Map a real provenance timestamp to the transcript segment that justifies it.

    The seek target for the "show me the moment" jump (HS-49-02). Returns None —
    no affordance, honest — when the timestamp is missing/non-numeric or there are
    no segments. Otherwise picks the segment with the greatest `start_time` at or
    before the timestamp (clamped to the first segment), so a real `0.0` resolves
    to the opening segment rather than a fake jump.

    `segments` are `TranscriptSegment`s in `start_time` order (as
    `MeetingState.segments` is loaded).
    """
    ts = _coerce_timestamp(source_timestamp)
    if ts is None or not segments:
        return None
    chosen_index = 0
    chosen = segments[0]
    for idx, seg in enumerate(segments):
        if seg.start_time <= ts:
            chosen_index = idx
            chosen = seg
        else:
            break
    text = str(getattr(chosen, "text", "") or "")
    return {
        "source_timestamp": ts,
        "segment_index": chosen_index,
        "segment_start": chosen.start_time,
        "speaker": getattr(chosen, "speaker", None),
        "text_preview": text[:120],
    }


def _decisions_for_meeting(
    db: "Database", meeting_id: str, segments: Optional[list[Any]] = None
) -> list[dict[str, Any]]:
    """Pull the decisions captured for one meeting from its `decisions` artifact.

    Decisions live in the `decisions` artifact's `structured_json` (see
    `plugins/synthesis.py`). Deduped by normalized decision text, first wins.
    When `segments` is given, a decision carrying a real `source_timestamp` gets
    a resolved `provenance` jump target; decisions without one stay unlinked.
    """
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for artifact in db.plugins.list_artifacts(meeting_id, limit=200):
        if artifact.artifact_type != "decisions":
            continue
        raw = artifact.structured_json.get("decisions")
        if not isinstance(raw, list):
            continue
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            decision = str(entry.get("decision") or "").strip()
            if not decision:
                continue
            key = _norm(decision)
            if key in seen:
                continue
            seen.add(key)
            rationale = str(entry.get("rationale") or "").strip() or None
            source_timestamp = _coerce_timestamp(entry.get("source_timestamp"))
            out.append(
                {
                    "decision": decision,
                    "rationale": rationale,
                    "source_timestamp": source_timestamp,
                    "provenance": (
                        resolve_provenance_segment(segments, source_timestamp)
                        if segments is not None
                        else None
                    ),
                }
            )
    return out


def _open_item_payload(item: Any, segments: Optional[list[Any]] = None) -> dict[str, Any]:
    """Serialize one open action item (with a resolved provenance jump target)."""
    return {
        "id": item.id,
        "task": item.task,
        "owner": _clean_owner(item.owner),
        "due": item.due,
        "review_state": item.review_state,
        "source_timestamp": _coerce_timestamp(item.source_timestamp),
        "provenance": resolve_provenance_segment(segments or [], item.source_timestamp),
        "meeting_id": item.meeting_id,
    }


def _group_open_by_owner(
    items: list[Any], segments: Optional[list[Any]] = None
) -> list[dict[str, Any]]:
    """Group pending items by owner; named owners A→Z, unassigned last."""
    groups: dict[Optional[str], list[dict[str, Any]]] = {}
    for item in items:
        owner = _clean_owner(item.owner)
        groups.setdefault(owner, []).append(_open_item_payload(item, segments))

    def sort_key(owner: Optional[str]) -> tuple[int, str]:
        # Unassigned sinks to the bottom; named owners sort case-insensitively.
        return (1, "") if owner is None else (0, owner.lower())

    return [
        {"owner": owner, "count": len(groups[owner]), "items": groups[owner]}
        for owner in sorted(groups, key=sort_key)
    ]


def _previous_meeting(db: "Database", meeting: Any) -> Optional[Any]:
    """Find the chronologically previous meeting by `started_at`.

    The prior meeting is the one with the greatest `started_at` strictly before
    this meeting's. `id` is the tie-break so the choice is deterministic when two
    meetings share a timestamp.
    """
    current_started = meeting.started_at
    current_id = meeting.id
    best = None
    for summary in db.meetings.list_meetings(limit=10000):
        if summary.id == current_id:
            continue
        if summary.started_at > current_started:
            continue
        if summary.started_at == current_started and summary.id >= current_id:
            # Same instant: only count ids that order before us, to avoid a
            # meeting picking itself or its same-instant successor.
            continue
        if best is None:
            best = summary
            continue
        if (summary.started_at, summary.id) > (best.started_at, best.id):
            best = summary
    return best


def _since_last_meeting(
    db: "Database",
    *,
    previous: Any,
    current_decisions: list[dict[str, Any]],
    current_open_items: list[Any],
    current_segments: list[Any],
) -> dict[str, Any]:
    """Compute the real diff of decisions + action items vs the prior meeting."""
    # Prior decisions/items are needed only for text comparison, so skip
    # resolving their (other meeting's) provenance.
    prior_decisions = _decisions_for_meeting(db, previous.id)
    prior_decision_keys = {_norm(d["decision"]) for d in prior_decisions}

    # Every prior action item (any status) — used both to detect what's new now
    # and to surface loops from last time that have since closed.
    prior_items = db.meetings.list_action_items(
        include_completed=True, meeting_id=previous.id
    )
    prior_task_keys = {_norm(item.task) for item in prior_items}

    new_decisions = [
        d for d in current_decisions if _norm(d["decision"]) not in prior_decision_keys
    ]
    new_actions = [
        _open_item_payload(item, current_segments)
        for item in current_open_items
        if _norm(item.task) not in prior_task_keys
    ]
    closed_actions = [
        {
            "id": item.id,
            "task": item.task,
            "owner": _clean_owner(item.owner),
            "status": item.status,
            "meeting_id": item.meeting_id,
        }
        for item in prior_items
        if item.status in ("done", "dismissed")
    ]

    return {
        "previous_meeting": {
            "id": previous.id,
            "title": previous.title,
            "date": previous.started_at.isoformat(),
        },
        "new_decisions": new_decisions,
        "new_actions": new_actions,
        "closed_actions": closed_actions,
        "changed": bool(new_decisions or new_actions or closed_actions),
    }


def compute_meeting_aftercare(
    db: "Database", meeting_id: str
) -> Optional[dict[str, Any]]:
    """Build the read-only aftercare digest for one meeting.

    Returns None when the meeting does not exist. The returned dict carries
    `is_empty=True` when there is nothing open, nothing decided, and nothing
    changed — the caller's cue to stay quiet.
    """
    meeting = db.meetings.get_meeting(meeting_id)
    if meeting is None:
        return None

    segments = meeting.segments or []
    open_items = db.meetings.list_action_items(
        include_completed=False, meeting_id=meeting_id
    )
    decisions = _decisions_for_meeting(db, meeting_id, segments)

    previous = _previous_meeting(db, meeting)
    since_last_meeting = (
        _since_last_meeting(
            db,
            previous=previous,
            current_decisions=decisions,
            current_open_items=open_items,
            current_segments=segments,
        )
        if previous is not None
        else None
    )

    is_empty = (
        not open_items
        and not decisions
        and (since_last_meeting is None or not since_last_meeting["changed"])
    )

    return {
        "meeting_id": meeting.id,
        "meeting_title": meeting.title,
        "meeting_date": meeting.started_at.isoformat(),
        "open_items": {
            "total": len(open_items),
            "by_owner": _group_open_by_owner(open_items, segments),
        },
        "decisions": decisions,
        "since_last_meeting": since_last_meeting,
        "is_empty": is_empty,
    }
