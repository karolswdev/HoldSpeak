"""HS-200-13 -- the carry mark: `Carry into brief`, by reference (C3).

A recall on the Desk memory face finds the CURRENT decision; `Carry into
brief` queues that record for the Project's NEXT preparation.  The mark is a
row in ``preparation_carries`` naming the record by ref -- never a copy -- so
a record superseded between the recall and the preparation resolves to the
current one at read time (``pending_carries`` follows the successor chain).

The seam HS-200-11 binds to (the preparation brief's manifest builder):

    from holdspeak.services.brief_carry import pending_carries, consume_carries

    carried = pending_carries(db, project_id)
        # -> [{"carry_id", "ref", "record_id", "current_ref",
        #      "current_record_id", "resolved_through", "carried_at",
        #      "carried_by", "superseded"}], oldest carry first
    ...freeze the manifest with `carried` under "carried"...
    consume_carries(db, project_id, brief_id)
        # stamps consumed_at / consumed_by on every pending mark

``ref`` is the record the owner pressed the verb on; ``current_ref`` is what
the brief cites (the same ref unless a supersession happened in between, in
which case ``superseded`` is True and ``resolved_through`` lists the chain).
A record that was DISPUTED since the carry is still handed over, with
``lifecycle`` saying so -- the brief decides how to draw it, the carry does not
hide it (AC2).

**One mark per CURRENT record** (counsel-on-built P1-2).  Identity is the
RESOLVED record, never the pressed ref: a press on a record whose resolved
current record already has a pending mark is a replay (``replayed: True``,
no new row, no second receipt); ``pending_carries`` hands each current record
over ONCE (the oldest mark wins, its ``resolved_through`` names the chain);
``pending_carry_refs`` returns the CURRENT refs, so a successor drawn on the
face reads ``CARRIED`` when its predecessor was carried.  The unique index on
the pressed ref is only the belt against a double press on one ref.

Only a CURRENT record can be carried (``not_current`` otherwise -- a
superseded or disputed record is discoverable, never carried, AC2), and only
a principal with the DECIDE right may carry (the same right that accepts a
decision; an UNAUTHENTICATED caller is refused by name).

Every carry writes a kernel receipt (``decision.carried``, Article XI).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from holdspeak.principals import PrincipalRight, refusal
from holdspeak.services.observer import current_correlation_id
from holdspeak.services.service_event_ledger import ServiceEventLedger


class RightRequired(PermissionError):
    """The caller lacks the right the act needs; ``response`` is the refusal
    the transport returns (`principal_right_required`, the principal named)."""

    def __init__(self, principal: Any, right: PrincipalRight) -> None:
        self.response = refusal(principal, right)
        super().__init__(f"principal_right_required: {right.value} ({getattr(principal, 'name', principal)})")


def require_right(principal: Any, right: PrincipalRight) -> None:
    if not getattr(principal, "permits", lambda _r: False)(right):
        raise RightRequired(principal, right)

RECORD_REF_PREFIX = "decision_record:"

#: The lifecycles a decision record can carry.  ``active`` and ``published``
#: are CURRENT; ``superseded`` names a successor; ``disputed`` (HS-200-13,
#: defined minimally here) is a record someone contests -- discoverable,
#: never presented as current, never accented.
CURRENT_LIFECYCLES = frozenset({"active", "published"})


def record_ref(record_id: str) -> str:
    rid = str(record_id or "").strip()
    return rid if rid.startswith(RECORD_REF_PREFIX) else f"{RECORD_REF_PREFIX}{rid}"


def record_id_of(ref: str) -> str:
    text = str(ref or "").strip()
    return text[len(RECORD_REF_PREFIX):] if text.startswith(RECORD_REF_PREFIX) else text


def _principal_name(principal: Any) -> str:
    for attr in ("name", "identity", "id", "label"):
        value = getattr(principal, attr, None)
        if value:
            return str(value)
    return ""


def successor_of(conn: Any, record_id: str) -> str | None:
    """The successor a superseded record names (``decision_record_sources``
    row of type ``successor``; the same fact ``DecisionRecordService.supersede``
    writes)."""
    row = conn.execute(
        """SELECT source_ref FROM decision_record_sources
           WHERE record_id = ? AND source_type = 'successor'
           ORDER BY created_at DESC, id DESC LIMIT 1""",
        (record_id,),
    ).fetchone()
    return str(row["source_ref"]) if row and row["source_ref"] else None


def resolve_current(conn: Any, record_id: str) -> dict[str, Any]:
    """Follow the successor chain from ``record_id`` to the record that is
    current NOW.  Returns the resolved id, its lifecycle, and the chain walked
    (``resolved_through`` excludes the start, includes the end)."""
    seen: list[str] = []
    current = str(record_id)
    lifecycle = None
    for _ in range(64):  # a chain longer than this is a data defect, not a loop to follow
        row = conn.execute(
            "SELECT id, lifecycle, deleted FROM decision_records WHERE id = ?", (current,)
        ).fetchone()
        if row is None:
            return {"record_id": current, "lifecycle": None, "resolved_through": seen, "found": False}
        lifecycle = str(row["lifecycle"] or "active")
        if lifecycle != "superseded":
            break
        nxt = successor_of(conn, current)
        if not nxt or nxt in seen or nxt == record_id:
            break
        seen.append(nxt)
        current = nxt
    return {"record_id": current, "lifecycle": lifecycle, "resolved_through": seen, "found": True}


def project_for_record(conn: Any, record_id: str) -> str | None:
    """The Project a record belongs to: an explicit ``project_resources`` row
    first, else the Room its source meeting is linked to."""
    row = conn.execute(
        """SELECT project_id FROM project_resources
           WHERE resource_ref = ? AND deleted = 0 ORDER BY project_id LIMIT 1""",
        (record_ref(record_id),),
    ).fetchone()
    if row and row["project_id"]:
        return str(row["project_id"])
    row = conn.execute(
        """SELECT mp.project_id FROM decision_record_sources drs
           JOIN meeting_projects mp
             ON mp.meeting_id IN (drs.source_ref, replace(drs.source_ref, 'meeting:', ''))
           WHERE drs.record_id = ? AND drs.source_type IN ('meeting', 'transcript')
           ORDER BY mp.project_id LIMIT 1""",
        (record_id,),
    ).fetchone()
    return str(row["project_id"]) if row and row["project_id"] else None


def carry_into_brief(
    db: Any, principal: Any, record_id: str, *, project_id: str | None = None,
) -> dict[str, Any]:
    """Queue a decision record for its Project's next preparation.

    Idempotent per (Project, CURRENT record): a press whose resolved record
    already has a pending mark returns that row with ``replayed: True``.  A
    consumed mark (a brief already read it) can be carried again -- that is a
    new mark.  Refuses a non-current record (``not_current``) and a caller
    without the DECIDE right.
    """
    require_right(principal, PrincipalRight.DECIDE)
    rid = record_id_of(record_id)
    if not rid:
        raise ValueError("record_id is required")
    now = datetime.now().isoformat()
    with db._connection() as conn:
        record = conn.execute(
            "SELECT id, lifecycle, decision_text FROM decision_records WHERE id = ? AND deleted = 0",
            (rid,),
        ).fetchone()
        if record is None:
            raise KeyError(rid)
        lifecycle = str(record["lifecycle"] or "active")
        if lifecycle not in CURRENT_LIFECYCLES:
            raise ValueError(f"not_current: the record is {lifecycle}; only the current decision can be carried")
        pid = str(project_id or "").strip() or project_for_record(conn, rid)
        if not pid:
            raise ValueError("no_project: the record belongs to no Project, so there is no brief to carry it into")
        for row in conn.execute(
            """SELECT * FROM preparation_carries
               WHERE project_id = ? AND consumed_at IS NULL
               ORDER BY carried_at ASC, id ASC""",
            (pid,),
        ).fetchall():
            resolved = resolve_current(conn, record_id_of(str(row["record_ref"])))
            if resolved["record_id"] == rid:
                return {**dict(row), "replayed": True}
        carry_id = f"carry-{uuid4().hex[:16]}"
        by = _principal_name(principal)
        conn.execute(
            """INSERT INTO preparation_carries
               (id, project_id, record_ref, carried_at, carried_by, consumed_at, consumed_by)
               VALUES (?, ?, ?, ?, ?, NULL, NULL)""",
            (carry_id, pid, record_ref(rid), now, by),
        )
        ServiceEventLedger(db).append_in_transaction(
            conn, principal,
            event_type="decision.carried",
            producer="brief_carry",
            subject_ref=record_ref(rid),
            source_revision=carry_id,
            facts={
                "carry_id": carry_id,
                "project_id": pid,
                "record_id": rid,
                "lifecycle": str(record["lifecycle"] or "active"),
                "entity_title": str(record["decision_text"] or ""),
            },
            refs=[record_ref(rid), f"project:{pid}", f"carry:{carry_id}"],
            correlation_id=current_correlation_id(),
            causation_id=record_ref(rid),
        )
        row = conn.execute("SELECT * FROM preparation_carries WHERE id = ?", (carry_id,)).fetchone()
    return {**dict(row), "replayed": False}


def pending_carries(db: Any, project_id: str) -> list[dict[str, Any]]:
    """Every pending carry mark of a Project, oldest first, each resolved to
    the record that is CURRENT at read time, ONE row per current record (the
    oldest mark).  This is the read HS-200-11's manifest builder makes."""
    pid = str(project_id or "").strip()
    if not pid:
        return []
    out: list[dict[str, Any]] = []
    seen_current: set[str] = set()
    with db._connection() as conn:
        rows = conn.execute(
            """SELECT * FROM preparation_carries
               WHERE project_id = ? AND consumed_at IS NULL
               ORDER BY carried_at ASC, id ASC""",
            (pid,),
        ).fetchall()
        for row in rows:
            rid = record_id_of(str(row["record_ref"]))
            resolved = resolve_current(conn, rid)
            current_id = str(resolved["record_id"])
            if current_id in seen_current:
                continue
            seen_current.add(current_id)
            text_row = conn.execute(
                "SELECT decision_text, rationale, lifecycle FROM decision_records WHERE id = ? AND deleted = 0",
                (current_id,),
            ).fetchone()
            out.append({
                "carry_id": str(row["id"]),
                "ref": str(row["record_ref"]),
                "record_id": rid,
                "current_ref": record_ref(current_id),
                "current_record_id": current_id,
                "resolved_through": [record_ref(r) for r in resolved["resolved_through"]],
                "superseded": bool(resolved["resolved_through"]),
                "lifecycle": (str(text_row["lifecycle"]) if text_row else resolved["lifecycle"]),
                "text": str(text_row["decision_text"]) if text_row else "",
                "rationale": (text_row["rationale"] if text_row else None) or "",
                "carried_at": str(row["carried_at"]),
                "carried_by": str(row["carried_by"] or ""),
                "found": bool(text_row is not None),
            })
    return out


def pending_carry_refs(db: Any, project_id: str) -> set[str]:
    """The CURRENT refs carried for a Project (the face's `CARRIED` state):
    a successor whose predecessor was carried reads as carried."""
    return {row["current_ref"] for row in pending_carries(db, project_id)}


def consume_carries(db: Any, project_id: str, brief_id: str) -> int:
    """Stamp every pending mark of a Project as read by ``brief_id``.
    Returns how many were consumed.  Called by the preparation that froze
    them into its manifest (HS-200-11)."""
    pid = str(project_id or "").strip()
    bid = str(brief_id or "").strip()
    if not pid or not bid:
        raise ValueError("project_id and brief_id are required")
    now = datetime.now().isoformat()
    with db._connection() as conn:
        cur = conn.execute(
            """UPDATE preparation_carries SET consumed_at = ?, consumed_by = ?
               WHERE project_id = ? AND consumed_at IS NULL""",
            (now, bid, pid),
        )
        return int(cur.rowcount or 0)


__all__ = [
    "CURRENT_LIFECYCLES",
    "RightRequired",
    "require_right",
    "carry_into_brief",
    "consume_carries",
    "pending_carries",
    "pending_carry_refs",
    "project_for_record",
    "record_id_of",
    "record_ref",
    "resolve_current",
    "successor_of",
]
