"""The owner's project delegation grant: grant, revoke, and its projection (PHILO-9-07, the Q2 ruling).

Phase 7's desk grant (``services/desk_delegation.py``), scoped to ONE project:
``project.delegation.grant`` and ``project.delegation.revoke`` are Room kernel
operations, each ADMITTED with its own receipt, owner-only (XI.4: an agent's
attempt is refused ``owner_principal_required`` with a receipt), HTTP only.
The grant-table write, the terminal state and the receipt commit in ONE
transaction (``KernelHandle.terminal(effect=...)``, ``transition_and_receipt``).

The grant is keyed by the agent's IDENTITY and the project, so it survives a
credential reissue and a hub restart. The owner's credential revoke ends every
LIVE project grant of that identity durably FIRST (handover XXIX law 4).
"""
from __future__ import annotations

import uuid
from typing import Any, Mapping

from ..kernel import project as rooms
from . import project_kernel
from .errors import ServiceError


def _database() -> Any:
    from ..db import get_database

    return get_database()


def _now(database: Any) -> float:
    """The kernel's clock (one clock for the grant rows and every check of them)."""
    return float(project_kernel._broker(database)._clock())


def _refuse(name: str, principal: Any, code: str, args: Mapping[str, Any], database: Any, status: int) -> None:
    kernel = project_kernel.refuse(database, principal, name, code, dict(args))
    raise project_kernel.ProjectKernelRefused(code, name, operation_id=(kernel or {}).get("operation_id") or "",
                                              receipt=(kernel or {}).get("receipt"), status=status)


def _project_exists(database: Any, project_id: str) -> bool:
    with database._connection() as conn:
        row = conn.execute("SELECT lifecycle FROM projects WHERE id=?", (project_id,)).fetchone()
    return row is not None and str(row["lifecycle"]) != "archived"


def grant(principal: Any, agent_identity: str, project_id: str, body: Any, *, database: Any = None) -> dict[str, Any]:
    """``project.delegation.grant``: one LIVE grant for (agent, project); a re-grant replaces the old one.

    *body* is ``{expires_at?}`` (epoch seconds, optional, no default). Any
    other field, or a non-object, is ``invalid_arguments`` with a receipt.
    """
    database = database or _database()
    name = "project.delegation.grant"
    args = {"agent_identity": agent_identity, "project_id": project_id}
    # An agent's attempt goes on to the kernel, which refuses it
    # (owner_principal_required) with its receipt.
    if principal.kind.value != "owner":
        pass
    elif not isinstance(body, Mapping) or set(body) - {"expires_at"} or not str(agent_identity).strip() or (
        body.get("expires_at") is not None
        and (isinstance(body.get("expires_at"), bool) or not isinstance(body.get("expires_at"), (int, float)))
    ):
        _refuse(name, principal, "invalid_arguments", args, database, 400)
    elif not _project_exists(database, project_id):
        _refuse(name, principal, "not_found", args, database, 404)
    payload: dict[str, Any] = {
        **args, "grant_id": "projdeleg_" + uuid.uuid4().hex,
        "expires_at": body.get("expires_at") if isinstance(body, Mapping) else None,
    }

    def call(minted: dict[str, Any]) -> dict[str, Any]:
        handle = project_kernel.current()
        assert handle is not None
        effect = rooms.grant_effect(
            grant_id=str(minted["grant_id"]), agent_identity=str(minted["agent_identity"]).strip(),
            project_id=str(minted["project_id"]), delegator_kind=principal.name,
            delegator_identity=principal.identity, expires_at=minted.get("expires_at"),
            operation_id=handle.operation_id, now=_now(database),
        )
        handle.terminal("succeeded", "succeeded", f"{rooms.PROJECT_BASIS_KIND}:{minted['grant_id']}", effect=effect)
        return {"grant_id": minted["grant_id"]}

    result, kernel = project_kernel.run(database, principal, name, payload, call)
    return {**kernel, **result, "agent_identity": agent_identity, "project_id": project_id}


def revoke(principal: Any, agent_identity: str, project_id: str, reason: str = "owner_revoked", *,
           database: Any = None, body: Any = None) -> dict[str, Any]:
    """``project.delegation.revoke``: the LIVE grant REVOKED; none LIVE -> ``project_delegation_required`` with a receipt."""
    database = database or _database()
    name = "project.delegation.revoke"
    args = {"agent_identity": agent_identity, "project_id": project_id}
    if principal.kind.value == "owner" and (
        (body is not None and (not isinstance(body, Mapping) or body)) or reason not in {"owner_revoked", "credential_revoked"}
    ):
        # DELETE declares no body: a non-object or any field is refused.
        _refuse(name, principal, "invalid_arguments", args, database, 400)
    payload = {**args, "reason": reason}

    def call(minted: dict[str, Any]) -> dict[str, Any]:
        handle = project_kernel.current()
        assert handle is not None
        inner = rooms.revoke_effect(agent_identity=str(minted["agent_identity"]).strip(),
                                    project_id=str(minted["project_id"]), reason=str(minted["reason"]),
                                    now=_now(database))

        def effect(conn: Any) -> None:
            try:
                inner(conn)
            except rooms.ProjectGrantRefused as exc:
                # Rolled back with the transaction; the path closes it refused with its receipt.
                raise ServiceError(exc.code, "No LIVE project grant to stop", context={"status": 409}) from exc

        handle.terminal("succeeded", "succeeded", f"project:{minted['project_id']}", effect=effect)
        return {"reason": minted["reason"]}

    result, kernel = project_kernel.run(database, principal, name, payload, call)
    return {**kernel, **result, "agent_identity": agent_identity, "project_id": project_id}


def live_projects(agent_identity: str, *, database: Any = None) -> list[str]:
    """The projects with a LIVE-in-storage grant for *agent_identity* (the credential routes' step 1)."""
    database = database or _database()
    with database._connection() as conn:
        return [str(r[0]) for r in conn.execute(
            "SELECT project_id FROM kernel_project_delegations WHERE agent_identity=? AND state='LIVE' "
            "ORDER BY created_at, id", (agent_identity,)).fetchall()]


def revoke_for_credential(principal: Any, agent_identity: str, *, database: Any = None) -> list[dict[str, Any]]:
    """Durable first: the owner's credential revoke ends EVERY LIVE project grant BEFORE the credential goes.

    One ``project.delegation.revoke`` (reason ``credential_revoked``) per
    project, each with its receipt. A kernel refusal propagates: the route
    leaves the credential in place.
    """
    database = database or _database()
    names = _project_names(database)
    return [
        {**revoke(principal, agent_identity, project_id, "credential_revoked", database=database),
         "project_name": names.get(project_id, project_id)}
        for project_id in live_projects(agent_identity, database=database)
    ]


def _project_names(database: Any) -> dict[str, str]:
    with database._connection() as conn:
        return {str(r["id"]): str(r["name"]) for r in conn.execute("SELECT id, name FROM projects").fetchall()}


def views(identities: list[str], *, database: Any = None, now: float | None = None) -> dict[str, Any]:
    """The Remote Access ledger's project-grant fields for ``GET /api/settings/remote``.

    ``by_identity``: each credential identity -> one entry per project with
    any stored grant row, the latest row projected to its EFFECTIVE state
    (the kernel's own time-aware rule). ``orphans``: every (identity, project)
    whose latest row is LIVE in storage and whose identity has NO credential
    row, with the same projection (the ratified canvas's wire contract).
    """
    database = database or _database()
    now = _now(database) if now is None else now
    names = _project_names(database)
    wanted = set(identities)
    by_identity: dict[str, list[dict[str, Any]]] = {identity: [] for identity in identities}
    orphans: list[dict[str, Any]] = []
    with database._connection() as conn:
        pairs = conn.execute(
            "SELECT agent_identity, project_id, MIN(created_at) AS first FROM kernel_project_delegations "
            "GROUP BY agent_identity, project_id ORDER BY first, agent_identity, project_id").fetchall()
        for row in pairs:
            identity, project_id = str(row["agent_identity"]), str(row["project_id"])
            view = rooms.grant_view(conn, identity, project_id, now)
            if view is None:
                continue
            entry = {"project_id": project_id, "project_name": names.get(project_id, project_id), **view}
            if identity in wanted:
                by_identity[identity].append(entry)
                continue
            live_in_storage = conn.execute(
                "SELECT 1 FROM kernel_project_delegations WHERE agent_identity=? AND project_id=? AND state='LIVE'",
                (identity, project_id)).fetchone() is not None
            if live_in_storage:
                orphans.append({"identity": identity, **entry})
    return {"by_identity": by_identity, "orphans": orphans}
