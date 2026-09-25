"""The desk writes' kernel operations and the owner's desk delegation grant (PHILO-7-02).

Article XI as the owner ruled it (D3, R1, R4, R5): every desk write that FILES
or DECIDES is one kernel operation with one terminal receipt. An OWNER write is
the owner's gesture (approved inline, XI.4). An AGENT write is approved by the
kernel only under a LIVE desk delegation the owner granted to THAT agent
identity for THAT operation; without one it is refused at admission with a
receipt. Nothing is held.

The design is the checked lifecycle beat
(``pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md``):

* ONE check, :func:`check_row`, with two entry points: :func:`by_identity`
  (admission and the chip: the LIVE row, else the latest historical row for
  the CODE only) and :func:`by_basis` (approval and the claim: the row the
  operation's own frozen ``authority_basis`` names, never another);
* the codes, in order: ``desk_delegation_required`` -> ``_expired`` ->
  ``_revoked``;
* the grant's terms hash is the schedule precedent's ``_hash(terms,
  expires_at)``, so the expiry is inside the hashed terms;
* the grant row table is ``kernel_desk_delegations`` (one LIVE per identity).
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Iterator, Mapping


#: R1 + R5: exactly the ADMITTED desk writes. Never ``delegation.*``.
DESK_GRANT_OPERATIONS: frozenset[str] = frozenset({
    "zone.file", "zone.unfile",
    "decision.create", "decision.update", "decision.status", "decision.supersede", "decision.delete",
    "kb.member.add", "kb.member.remove", "kb.create", "kb.update",
    "zone.create", "zone.update", "zone.delete",
    "note.delete",
})
#: The two owner-only operations that change the grant.
DELEGATION_OPERATIONS: frozenset[str] = frozenset({"delegation.grant", "delegation.revoke"})
#: Scopes the atomic terminal writes and the startup recovery ONLY; never an authority set.
DESK_KERNEL_OPERATIONS: frozenset[str] = DESK_GRANT_OPERATIONS | DELEGATION_OPERATIONS

REQUIRED = "desk_delegation_required"
EXPIRED = "desk_delegation_expired"
REVOKED = "desk_delegation_revoked"
OWNER_REQUIRED = "owner_principal_required"

#: The node identity that claims and executes desk operations inside the hub.
DESK_EXECUTOR = "hub-desk-writer"
DESK_PLACEMENT = f"node:{DESK_EXECUTOR}"
BASIS_KIND = "desk-delegation"
REVOCATION_REASONS = frozenset({"owner_revoked", "credential_revoked"})


#: Set only while the desk path (``holdspeak/services/desk_kernel.py``) runs an
#: operation: a raw ``/api/kernel/submit`` of a desk name has no effect to run
#: and would only leave an operation waiting, so it is refused with a receipt
#: (the scheduler precedent: a public submission stays refused).
_DESK_PATH: ContextVar[bool] = ContextVar("desk_path", default=False)


@contextmanager
def desk_path() -> Iterator[None]:
    token = _DESK_PATH.set(True)
    try:
        yield
    finally:
        _DESK_PATH.reset(token)


def terms_for(agent_identity: str) -> dict[str, Any]:
    """The grant's terms: the agent and the SORTED operation set, stored in the row."""
    return {"agent_identity": agent_identity, "operations": sorted(DESK_GRANT_OPERATIONS)}


def terms_sha256(terms: Mapping[str, Any], expires_at: float | None) -> str:
    """The schedule precedent's hash, imported, not copied (the expiry is inside it)."""
    from ..services.schedule_delegation import _hash

    return _hash(dict(terms), expires_at)


def basis(grant_id: str, sha: str) -> str:
    return f"{BASIS_KIND}:{grant_id}:{sha}"


def parse_basis(value: str) -> tuple[str, str] | None:
    """``desk-delegation:<id>:<sha256:...>`` -> (id, sha); at most two splits (the sha keeps its prefix)."""
    parts = str(value or "").split(":", 2)
    if len(parts) != 3 or parts[0] != BASIS_KIND or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


# ── the one check ────────────────────────────────────────────────────────


def check_row(
    row: Any, *, agent_identity: str, operation_name: str | None, now: float,
    frozen_sha256: str | None = None, conn: Any = None, authoritative: bool = False,
) -> str:
    """"" when *row* authorises this agent's operation now, else the refusal code.

    ``operation_name=None`` skips the operation-set test (the chip). With
    ``authoritative`` a LIVE row past its expiry is persisted EXPIRED on *conn*
    (as ``schedule_delegated.py:24-27``); the same code comes back either way.
    """
    if row is None or str(row["agent_identity"]) != str(agent_identity):
        return REQUIRED
    if operation_name is not None and operation_name not in json.loads(str(row["operations_json"] or "[]")):
        return REQUIRED
    state = str(row["state"])
    expires_at = row["expires_at"]
    if state == "EXPIRED" or (state == "LIVE" and expires_at is not None and float(expires_at) <= now):
        if authoritative and state == "LIVE" and conn is not None:
            conn.execute(
                "UPDATE kernel_desk_delegations SET state='EXPIRED',updated_at=? WHERE id=? AND state='LIVE'",
                (now, str(row["id"])),
            )
        return EXPIRED
    if state == "REVOKED" or (frozen_sha256 is not None and str(row["terms_sha256"]) != frozen_sha256):
        return REVOKED
    return ""


def by_identity(
    conn: Any, agent_identity: str, operation_name: str | None, now: float, *, authoritative: bool = False,
) -> tuple[str, Any]:
    """Admission and the chip: the LIVE row; else the latest historical row, for the CODE only."""
    row = conn.execute(
        "SELECT * FROM kernel_desk_delegations WHERE agent_identity=? AND state='LIVE'", (agent_identity,)
    ).fetchone()
    if row is None:
        row = conn.execute(
            "SELECT * FROM kernel_desk_delegations WHERE agent_identity=? ORDER BY updated_at DESC, id DESC LIMIT 1",
            (agent_identity,),
        ).fetchone()
    code = check_row(row, agent_identity=agent_identity, operation_name=operation_name, now=now,
                     conn=conn, authoritative=authoritative)
    return code, row


def by_basis(conn: Any, operation: Mapping[str, Any], now: float, *, authoritative: bool = True) -> str:
    """Approval and the claim: ONLY the row the operation's frozen basis names."""
    parsed = parse_basis(str(operation.get("authority_basis") or ""))
    if parsed is None:
        return REQUIRED
    grant_id, sha = parsed
    row = conn.execute("SELECT * FROM kernel_desk_delegations WHERE id=?", (grant_id,)).fetchone()
    return check_row(row, agent_identity=str(operation.get("principal_identity") or ""),
                     operation_name=str(operation.get("name") or ""), now=now,
                     frozen_sha256=sha, conn=conn, authoritative=authoritative)


def provenance(row: Any, target_ref: str) -> dict[str, str]:
    """The receipt join's authority fields for a refusal that a historical row explains."""
    values = {"target_ref": target_ref}
    if row is not None:
        values.update({
            "delegator_kind": str(row["delegator_kind"]),
            "delegator_identity": str(row["delegator_identity"]),
            "authority_basis": basis(str(row["id"]), str(row["terms_sha256"])),
        })
    return values


def grant_view(conn: Any, agent_identity: str, now: float) -> dict[str, Any] | None:
    """The chip's projection: ``{state, grant_id, expires_at}``, or ``None`` when never granted.

    The SAME time-aware rule as the kernel (``by_identity`` with *now*,
    non-authoritative): a stored LIVE row past its expiry projects EXPIRED.
    """
    code, row = by_identity(conn, agent_identity, None, now)
    if row is None or code == REQUIRED:
        return None
    state = {"": "LIVE", EXPIRED: "EXPIRED", REVOKED: "REVOKED"}[code]
    return {"state": state, "grant_id": str(row["id"]), "expires_at": row["expires_at"]}


# ── the grant table writes (T9: run on the seam's ONE connection) ────────


class DeskEffectRefused(Exception):
    """A domain refusal inside a delegation effect: the transaction rolls back."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def grant_effect(*, grant_id: str, agent_identity: str, delegator_kind: str, delegator_identity: str,
                 expires_at: float | None, operation_id: str, now: float) -> Callable[[Any], None]:
    terms = terms_for(agent_identity)
    sha = terms_sha256(terms, expires_at)

    def effect(conn: Any) -> None:
        # Local SQL on the supplied connection ONLY (the callback contract).
        conn.execute(
            "UPDATE kernel_desk_delegations SET state='REVOKED',revoked_at=?,revocation_reason='reapproved',"
            "updated_at=? WHERE agent_identity=? AND state='LIVE'",
            (now, now, agent_identity),
        )
        conn.execute(
            "INSERT INTO kernel_desk_delegations(id,agent_identity,delegator_kind,delegator_identity,"
            "operations_json,terms_sha256,expires_at,state,revoked_at,revocation_reason,grant_operation_id,"
            "created_at,updated_at) VALUES(?,?,?,?,?,?,?,'LIVE',NULL,'',?,?,?)",
            (grant_id, agent_identity, delegator_kind, delegator_identity,
             json.dumps(terms["operations"]), sha, expires_at, operation_id, now, now),
        )

    return effect


def revoke_effect(*, agent_identity: str, reason: str, now: float) -> Callable[[Any], None]:
    def effect(conn: Any) -> None:
        changed = conn.execute(
            "UPDATE kernel_desk_delegations SET state='REVOKED',revoked_at=?,revocation_reason=?,updated_at=? "
            "WHERE agent_identity=? AND state='LIVE'",
            (now, reason, now, agent_identity),
        ).rowcount
        if changed != 1:
            raise DeskEffectRefused(REQUIRED)

    return effect
