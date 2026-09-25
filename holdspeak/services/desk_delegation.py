"""The owner's desk delegation grant: grant, revoke, and its projection (PHILO-7-02, R1).

``delegation.grant`` and ``delegation.revoke`` are kernel operations, each
ADMITTED with its own receipt (XI.1: they change authority), owner-only
(XI.4: an agent's attempt is refused ``owner_principal_required`` with a
receipt; an agent can never grant itself). The grant-table write, the terminal
state and the receipt commit in ONE transaction (the lifecycle beat, T9).

The grant is keyed by the agent's principal IDENTITY and survives a credential
reissue and a hub restart (invariant 5). Only the two OWNER revocation routes
revoke it, durably first, before the credential is removed.
"""
from __future__ import annotations

import uuid
from typing import Any, Mapping

from ..kernel import desk
from . import desk_kernel


def _database() -> Any:
    from ..db import get_database

    return get_database()


def _now(database: Any) -> float:
    """The kernel's clock (one clock for the grant rows and every check of them)."""
    return float(desk_kernel._broker(database)._clock())


def grant(principal: Any, agent_identity: str, body: Any, *, database: Any = None) -> dict[str, Any]:
    """``delegation.grant``: one LIVE grant for *agent_identity* (a re-grant replaces the old one).

    *body* is the request body (``{expires_at?}``). A non-object body is an
    identifiable consequential attempt: a refusal receipt ``invalid_arguments``.
    """
    database = database or _database()
    if not isinstance(body, Mapping):
        kernel = desk_kernel.refuse(database, principal, "delegation.grant", "invalid_arguments",
                                    {"agent_identity": agent_identity})
        raise desk_kernel.DeskKernelRefused("invalid_arguments", "delegation.grant",
                                            operation_id=(kernel or {}).get("operation_id") or "",
                                            receipt=(kernel or {}).get("receipt"))
    payload: dict[str, Any] = {
        "agent_identity": agent_identity, "grant_id": "deskdeleg_" + uuid.uuid4().hex,
        **{key: value for key, value in body.items() if key != "grant_id"},
    }
    payload.setdefault("expires_at", None)

    def effect_for(operation_id: str, minted: dict[str, Any]) -> Any:
        effect = desk.grant_effect(
            grant_id=str(minted["grant_id"]), agent_identity=str(minted["agent_identity"]).strip(),
            delegator_kind=principal.name, delegator_identity=principal.identity,
            expires_at=minted.get("expires_at"), operation_id=operation_id, now=_now(database),
        )
        effect.result_ref = desk_kernel.target_ref(desk.BASIS_KIND, minted["grant_id"])  # type: ignore[attr-defined]
        return effect

    _result, kernel = desk_kernel.run(database, principal, "delegation.grant", payload, None, effect_for=effect_for)
    return {**kernel, "grant_id": payload["grant_id"]}


def revoke(principal: Any, agent_identity: str, reason: str = "owner_revoked", *,
           database: Any = None, body: Any = None) -> dict[str, Any]:
    """``delegation.revoke``: the LIVE grant REVOKED; none LIVE -> ``desk_delegation_required`` with a receipt."""
    database = database or _database()
    if body is not None and not isinstance(body, Mapping):
        kernel = desk_kernel.refuse(database, principal, "delegation.revoke", "invalid_arguments",
                                    {"agent_identity": agent_identity})
        raise desk_kernel.DeskKernelRefused("invalid_arguments", "delegation.revoke",
                                            operation_id=(kernel or {}).get("operation_id") or "",
                                            receipt=(kernel or {}).get("receipt"))
    payload = {"agent_identity": agent_identity, "reason": reason}

    def effect_for(operation_id: str, minted: dict[str, Any]) -> Any:
        return desk.revoke_effect(agent_identity=str(minted["agent_identity"]).strip(),
                                  reason=str(minted["reason"]), now=_now(database))

    _result, kernel = desk_kernel.run(database, principal, "delegation.revoke", payload, None, effect_for=effect_for)
    return kernel


def live_grant(agent_identity: str, *, database: Any = None) -> bool:
    """Whether a LIVE-in-storage grant exists for *agent_identity* (the credential routes' step 1)."""
    database = database or _database()
    with database._connection() as conn:
        return conn.execute(
            "SELECT 1 FROM kernel_desk_delegations WHERE agent_identity=? AND state='LIVE'", (agent_identity,)
        ).fetchone() is not None


def revoke_for_credential(principal: Any, agent_identity: str, *, database: Any = None) -> dict[str, Any] | None:
    """Durable first (invariant 5): the owner's credential revoke ends a LIVE grant BEFORE the credential goes.

    ``None`` when there is no LIVE grant (no operation is made). A kernel
    refusal propagates: the route leaves the credential in place.
    """
    if not live_grant(agent_identity, database=database):
        return None
    return revoke(principal, agent_identity, "credential_revoked", database=database)


def views(identities: list[str], *, database: Any = None, now: float | None = None) -> dict[str, Any]:
    """The Remote Access ledger's grant fields for ``GET /api/settings/remote``.

    ``by_identity`` maps each credential identity to its EFFECTIVE projection
    ``{state, grant_id, expires_at}`` (``None``: never granted), computed with
    the kernel's own time-aware rule; ``orphans`` lists, with the same
    projection, every identity that has a grant row (LIVE or historical) and
    NO credential row.
    """
    database = database or _database()
    now = _now(database) if now is None else now
    with database._connection() as conn:
        by_identity = {identity: desk.grant_view(conn, identity, now) for identity in identities}
        granted = [str(row[0]) for row in conn.execute(
            "SELECT DISTINCT agent_identity FROM kernel_desk_delegations ORDER BY agent_identity"
        ).fetchall()]
        orphans = []
        for identity in granted:
            if identity in by_identity:
                continue
            view = desk.grant_view(conn, identity, now)
            if view is not None:
                orphans.append({"identity": identity, **view})
    return {"by_identity": by_identity, "orphans": orphans}
