"""The one admission rule for memory (MEMORY-DESIGN.md §3.1 step 1, §5).

``memory_admits(kind, row)`` holds every exclusion in one place.  The chunk
sweep and the keyword (FTS) rebuild both call it, so a source that one index
refuses can never be in the other.

There is no People kind here.  A kind this module does not name is refused,
so People store content has no way in.
"""
from __future__ import annotations

from typing import Any, Mapping


def _flag(row: Mapping[str, Any], key: str) -> bool:
    try:
        return bool(int(row.get(key) or 0))
    except (TypeError, ValueError):
        return bool(row.get(key))


def _live(row: Mapping[str, Any]) -> bool:
    return not _flag(row, "deleted")


_RULES = {
    # A decision whose source is gone is not memory (the FTS rule).
    "decision": lambda row: _live(row) and str(row.get("source_state") or "linked") == "linked",
    "decision_record": _live,
    "desk_decision": _live,
    "artifact": lambda row: True,
    "meeting": lambda row: True,
    "note": _live,
    "thread": lambda row: row.get("deleted_at") is None,
    # One part of a thread message: never a sensitive part, never a draft.
    "thread_part": lambda row: (
        row.get("deleted_at") is None
        and row.get("message_deleted_at") is None
        and not _flag(row, "sensitive")
        and not _flag(row, "draft")
        and str(row.get("part_kind") or "text") == "text"
    ),
    "action": lambda row: True,
    "project_item": lambda row: True,
    "workbench_item": lambda row: str(row.get("status") or "") != "dismissed",
    "cadence": lambda row: str(row.get("status") or "") != "killed",
    # A send he pressed: sent, failed or unknown.  A prepared or discarded
    # row left nothing.
    "send": lambda row: str(row.get("state") or "") in ("sent", "failed", "unknown"),
    # Published only: a draft is not yet what he said.
    "project_update": lambda row: str(row.get("lifecycle") or "") == "published",
    "prep_brief": lambda row: str(row.get("lifecycle") or "") != "discarded",
    "calendar_event": lambda row: True,
    # Slice 2 (MEMORY-DESIGN.md §3.1).
    # A Brief item, never its 1:1 rows: the Brief writes them with no People
    # text, and memory leaves them out whole (People custody, §5).
    "brief_item": lambda row: (
        "people_commitment:" not in str(row.get("source_ref") or "")
        and not str(row.get("source_ref") or "").startswith("people:")
    ),
    # A dry run tests the pipeline; it is not something he said.
    "dictation": lambda row: str(row.get("source") or "") != "dry_run",
    # A finished run only: a queued or running run has said nothing yet.
    "steward_run": lambda row: str(row.get("state") or "") in ("completed", "failed", "interrupted"),
    # A Room ask that has its answer, until he discards it.
    "ask_answer": lambda row: str(row.get("state") or "") != "discarded" and _flag(row, "answered"),
}

ADMITTED_KINDS = frozenset(_RULES)


def memory_admits(kind: str, row: Mapping[str, Any]) -> bool:
    """True when this source row may enter memory.

    ``row`` carries the source row's own flags (``deleted``, ``parked``,
    ``sensitive``, ``draft`` …) and ``promoted``: true when the row is the
    target of a context promotion.  A promoted row and a parked row are
    never memory, for any kind.  An unknown kind is refused.
    """
    rule = _RULES.get(str(kind or ""))
    if rule is None:
        return False
    if _flag(row, "promoted"):
        return False
    # Parked is out of memory for EVERY kind: the row's own ``parked`` flag
    # (a meeting, a workbench item) and the flag of the meeting it came from
    # (an action, an artifact, a decision of a parked meeting).
    if _flag(row, "parked"):
        return False
    return bool(rule(row))


__all__ = ["ADMITTED_KINDS", "memory_admits"]
