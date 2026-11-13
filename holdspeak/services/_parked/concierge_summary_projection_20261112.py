# PARKED: the engine door now supplies the summary assignment; no live readers.
from __future__ import annotations

from typing import Any
from ..concierge_service import SUMMARY_CAPABILITY_ID

SUMMARY_ASSIGNMENT_PROJECTION_SCHEMA = "ConciergeSummaryAssignmentProjection@1"

def _summary_entry_projection(entry: dict[str, Any]) -> dict[str, Any]:
    """Project one assignment entry without exposing provider private material."""
    boundary = str(entry.get("boundary") or "unknown")
    # The assignment authority uses its transport boundary vocabulary.  The
    # Concierge keeps the smaller face vocabulary for the egress badge.
    boundary = {"private_network": "lan", "mesh": "lan"}.get(boundary, boundary)
    return {
        "profileId": str(entry.get("profile_id") or ""),
        "profileRevision": int(entry.get("profile_revision") or 0),
        "label": str(entry.get("label") or "Missing model"),
        "boundary": boundary,
        "readiness": str(entry.get("readiness") or "unknown"),
    }


def _summary_assignment_tombstone(db: Any) -> int:
    """The cleared head revision for the summary capability, else 0.

    ``get_assignment`` reads active heads only, so an owner who turned the
    summary OFF and one who never chose an engine look identical to it.
    They are not the same thing on a face: the first must reopen as OFF,
    the second as the proposal.  The head row already records the
    difference (``cleared=1`` with the tombstone's revision); this reads
    that one fact and nothing else.
    """
    if db is None:
        return 0
    try:
        with db._connection() as conn:
            row = conn.execute(
                "SELECT revision,cleared FROM inference_assignment_heads WHERE assignment_key=?",
                (f"capability:{SUMMARY_CAPABILITY_ID}",),
            ).fetchone()
    except Exception:  # pragma: no cover - a head read never blocks the face
        return 0
    if row is None:
        return 0
    try:
        return int(row["revision"] or 0) if int(row["cleared"] or 0) else 0
    except (KeyError, IndexError, TypeError, ValueError):  # pragma: no cover
        return 0


def summary_assignment_projection(
    *, assignment_service: Any, principal: Any, db: Any = None
) -> dict[str, Any]:
    """Read the exact summary assignment that the SERVICE route will consume."""
    from .errors import NotFound

    assignment = None
    try:
        assignment = assignment_service.get_assignment(
            principal,
            _summary_assignment_scope(),
        )
    except NotFound:
        pass

    if not isinstance(assignment, dict):
        cleared_revision = _summary_assignment_tombstone(db)
        queue = _summary_queue_resolution(assignment_service, principal)
        if queue is not None:
            # PHILO-15 01: the meeting-intel queue's own answer decides. The
            # owner's OFF holds before any default; with no exact head the
            # queue also reads the group and global heads
            # (meeting-intel-queue@2), so a Default for AI work runs summaries.
            off = queue.get("status") == "off"
            inherited = None if off else _summary_queue_projection(queue, cleared_revision)
            if inherited is not None:
                return inherited
        else:
            # A service without the queue's answer: the tombstone is the OFF.
            off = bool(cleared_revision)
        return {
            "schema": SUMMARY_ASSIGNMENT_PROJECTION_SCHEMA,
            "capabilityId": SUMMARY_CAPABILITY_ID,
            "status": "off" if off else "unassigned",
            "assignmentRevision": cleared_revision,
            "profileId": None,
            "profileRevision": None,
            "label": None,
            "boundary": None,
            "readiness": None,
        }

    entries = assignment.get("entries") or []
    if not entries:
        return {
            "schema": SUMMARY_ASSIGNMENT_PROJECTION_SCHEMA,
            "capabilityId": SUMMARY_CAPABILITY_ID,
            "status": "unassigned",
            "assignmentRevision": int(assignment.get("revision") or 0),
            "profileId": None,
            "profileRevision": None,
            "label": None,
            "boundary": None,
            "readiness": None,
        }
    entry = entries[0] if entries and isinstance(entries[0], dict) else {}
    projected = _summary_entry_projection(entry)
    issues = [issue for issue in assignment.get("issues") or [] if isinstance(issue, dict)]
    status = "attention" if any(issue.get("severity") == "blocking" for issue in issues) else "assigned"
    return {
        "schema": SUMMARY_ASSIGNMENT_PROJECTION_SCHEMA,
        "capabilityId": SUMMARY_CAPABILITY_ID,
        "status": status,
        "assignmentRevision": int(assignment.get("revision") or 0),
        **projected,
    }


def _summary_queue_resolution(assignment_service: Any, principal: Any) -> dict[str, Any] | None:
    """The meeting-intel queue's own resolution of the summary capability.

    ``None`` when the service cannot answer (a test double without
    ``resolve_for_queue``) or the read fails.
    """
    resolve = getattr(assignment_service, "resolve_for_queue", None)
    if resolve is None:
        return None
    try:
        resolved = resolve(principal, capability_id=SUMMARY_CAPABILITY_ID)
    except Exception as exc:  # pragma: no cover - a read never blocks the face
        log.warning(f"concierge: queue summary resolution unavailable ({exc})")
        return None
    return resolved if isinstance(resolved, dict) else None


def _summary_queue_projection(resolved: dict[str, Any], revision: int) -> dict[str, Any] | None:
    """The inherited head the queue would use, as the summary projection.

    ``assignmentRevision`` is the exact head's revision (its tombstone's, or
    0): that is what a write to the summary scope expects. ``inheritedFrom``
    names the head the queue reads (``group`` or ``global``).
    """
    if resolved.get("inherited_from") in (None, "capability"):
        return None
    assignment = resolved.get("assignment") if isinstance(resolved.get("assignment"), dict) else {}
    entries = [e for e in (assignment.get("entries") or []) if isinstance(e, dict)]
    if not entries:
        return None
    return {
        "schema": SUMMARY_ASSIGNMENT_PROJECTION_SCHEMA,
        "capabilityId": SUMMARY_CAPABILITY_ID,
        "status": "attention" if resolved.get("status") == "no_compatible_assignment" else "assigned",
        "assignmentRevision": int(revision or 0),
        "inheritedFrom": str(resolved.get("inherited_from")),
        **_summary_entry_projection(entries[0]),
    }




def _summary_expected_revision(
    assignment_service: Any, principal: Any, db: Any = None
) -> int:
    """The revision a WRITE to the summary capability must present.

    HS-201-09 (counsel finding 2): OFF then ON was refused. `get_assignment`
    reads ACTIVE heads only, so after a clear it answers 0 — while
    `set_assignment` compares against `_current`
    (`inference_assignment_service.py:402`), which still sees the
    tombstone's revision. The write therefore presents the same number the
    projection publishes: the active head when there is one, the tombstone
    when the owner turned it off. The OFF path keeps the active-only read,
    so re-applying OFF writes no second tombstone.
    """
    active = _summary_assignment_revision(assignment_service, principal)
    return active if active else _summary_assignment_tombstone(db)
