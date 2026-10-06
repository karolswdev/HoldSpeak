"""The project delegation grant (PHILO-9-07), carved from ``kernel/project.py``.

The owner's Q2 ruling: an agent may do the bound (``PROJECT_GRANT_OPERATIONS``)
in ONE project under a grant he gives. Phase 7's desk grant, scoped to a
project (``kernel/desk.py``): the same one check (``desk.check_row``), the
same codes in the same order, the same imported terms hash with the expiry
inside it, the same atomic terminal writes. The grant rows are the sibling
table ``kernel_project_delegations`` (one LIVE per agent and project).
``kernel/project.py`` re-exports every name here.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

#: The owner's ruled bound for the project grant ("Run, stop, publish"):
#: without a LIVE grant naming it for that project, every agent call is refused.
PROJECT_GRANT_OPERATIONS: frozenset[str] = frozenset({
    "project.run_steward", "project.stop_steward", "project.publish_update",
})

#: Conductor K6 (ruling on #903, round 4): what a LAUNCH may do in its own
#: Project under the grant the owner's press on Hand to agent makes: add a
#: link or a resource, and remove a resource (the MCP gate allows that only
#: for a resource the agent added). Only a launch identity is granted these.
LAUNCH_GRANT_OPERATIONS: frozenset[str] = frozenset({
    "project.link", "project.resource.add", "project.resource.remove",
})
LAUNCH_IDENTITY_PREFIX = "agent:launch:"


def launch_grantable(name: str, identity: Any) -> bool:
    """A launch identity's operation that its launch grant may admit."""
    return str(name) in LAUNCH_GRANT_OPERATIONS and str(identity or "").startswith(LAUNCH_IDENTITY_PREFIX)


def granted_operation(name: str, identity: Any) -> bool:
    """An agent operation a LIVE project grant decides."""
    return str(name) in PROJECT_GRANT_OPERATIONS or launch_grantable(name, identity)


REQUIRED = "project_delegation_required"
EXPIRED = "project_delegation_expired"
REVOKED = "project_delegation_revoked"

PROJECT_BASIS_KIND = "project-delegation"
GRANT_CODES: frozenset[str] = frozenset({REQUIRED, EXPIRED, REVOKED})
_TABLE = "kernel_project_delegations"


def terms_for(agent_identity: str, project_id: str, operations: Any = None) -> dict[str, Any]:
    """The grant's terms, stored in the row: a later code change never widens an old grant.

    ``operations`` (K6, a launch's grant) chooses from the grantable sets."""
    chosen = PROJECT_GRANT_OPERATIONS if operations is None else (
        frozenset(operations) & (PROJECT_GRANT_OPERATIONS | LAUNCH_GRANT_OPERATIONS))
    return {"agent_identity": agent_identity, "project_id": project_id,
            "operations": sorted(chosen)}


def terms_sha256(terms: Mapping[str, Any], expires_at: float | None) -> str:
    from . import desk

    return desk.terms_sha256(terms, expires_at)


def basis(grant_id: str, sha: str) -> str:
    return f"{PROJECT_BASIS_KIND}:{grant_id}:{sha}"


def parse_basis(value: str) -> tuple[str, str] | None:
    parts = str(value or "").split(":", 2)
    if len(parts) != 3 or parts[0] != PROJECT_BASIS_KIND or not parts[1] or not parts[2]:
        return None
    return parts[1], parts[2]


def check_row(row: Any, *, agent_identity: str, project_id: str, operation_name: str | None, now: float,
              frozen_sha256: str | None = None, conn: Any = None, authoritative: bool = False) -> str:
    """Phase 7's one check, plus the project: a grant on project A is nothing on project B."""
    from . import desk

    if row is None or str(row["project_id"]) != str(project_id):
        return REQUIRED
    code = desk.check_row(row, agent_identity=agent_identity, operation_name=operation_name, now=now,
                          frozen_sha256=frozen_sha256, conn=conn, authoritative=authoritative, table=_TABLE)
    # The same order, the project siblings of Phase 7's codes.
    return {desk.REQUIRED: REQUIRED, desk.EXPIRED: EXPIRED, desk.REVOKED: REVOKED}.get(code, code)


def by_identity(conn: Any, agent_identity: str, project_id: str, operation_name: str | None, now: float, *,
                authoritative: bool = False) -> tuple[str, Any]:
    """Admission and the chip: the LIVE row; else the latest historical row, for the CODE only."""
    row = conn.execute(
        f"SELECT * FROM {_TABLE} WHERE agent_identity=? AND project_id=? AND state='LIVE'",
        (agent_identity, project_id),
    ).fetchone()
    if row is None:
        row = conn.execute(
            f"SELECT * FROM {_TABLE} WHERE agent_identity=? AND project_id=? ORDER BY updated_at DESC, id DESC LIMIT 1",
            (agent_identity, project_id),
        ).fetchone()
    return check_row(row, agent_identity=agent_identity, project_id=project_id, operation_name=operation_name,
                     now=now, conn=conn, authoritative=authoritative), row


def by_grant(conn: Any, grant_id: str, sha: str, *, agent_identity: str, project_id: str | None,
             operation_name: str | None, now: float, authoritative: bool = False) -> str:
    """Approval, the claim and a steward child: ONLY the row the frozen basis names (never a newer G2).

    ``project_id=None``: the row's own project (the admission already bound
    it to the stored run or update, whose project never changes).
    """
    row = conn.execute(f"SELECT * FROM {_TABLE} WHERE id=?", (grant_id,)).fetchone()
    if project_id is None:
        project_id = str(row["project_id"]) if row is not None else ""
    return check_row(row, agent_identity=agent_identity, project_id=project_id, operation_name=operation_name,
                     now=now, frozen_sha256=sha, conn=conn, authoritative=authoritative)


def by_basis(conn: Any, operation: Mapping[str, Any], project_id: str | None, now: float, *,
             authoritative: bool = True) -> str:
    parsed = parse_basis(str(operation.get("authority_basis") or ""))
    if parsed is None:
        return REQUIRED
    return by_grant(conn, parsed[0], parsed[1], agent_identity=str(operation.get("principal_identity") or ""),
                    project_id=project_id, operation_name=str(operation.get("name") or ""), now=now,
                    authoritative=authoritative)


def provenance(row: Any, target_ref: str) -> dict[str, str]:
    values = {"target_ref": target_ref}
    if row is not None:
        values.update({
            "delegator_kind": str(row["delegator_kind"]),
            "delegator_identity": str(row["delegator_identity"]),
            "authority_basis": basis(str(row["id"]), str(row["terms_sha256"])),
        })
    return values


def grant_code(conn: Any, principal: Any, name: str, project_id: str,
               now: float | None = None) -> tuple[str, Mapping[str, str]]:
    """THE check point: ``("", basis)`` when a LIVE grant for this agent AND this project names the operation.

    Else the refusal code in Phase 7's order (required -> expired -> revoked)
    and, for a historical row, its provenance for the refusal receipt.
    """
    import time as _time

    now = _time.time() if now is None else now
    identity = str(getattr(principal, "identity", "") or "")
    code, row = by_identity(conn, identity, str(project_id or ""), name, now)
    if code:
        return code, (provenance(row, "") if code in {EXPIRED, REVOKED} else {})
    return "", {"authority_basis": basis(str(row["id"]), str(row["terms_sha256"])),
                "delegator_kind": str(row["delegator_kind"]),
                "delegator_identity": str(row["delegator_identity"])}


def frozen_grant_code(conn: Any, frozen: Mapping[str, Any] | None, *, agent_identity: str, project_id: str,
                      now: float, authoritative: bool = False) -> str:
    """A steward run's frozen grant (``{id, terms_sha256}``) re-checked now; "" for a run with none."""
    if not frozen:
        return ""
    return by_grant(conn, str(frozen.get("id") or ""), str(frozen.get("terms_sha256") or ""),
                    agent_identity=agent_identity, project_id=project_id, operation_name="project.run_steward",
                    now=now, authoritative=authoritative)


def grant_view(conn: Any, agent_identity: str, project_id: str, now: float) -> dict[str, Any] | None:
    """The chip's projection for one (agent, project): ``{state, grant_id, expires_at}``; ``None`` = never granted."""
    code, row = by_identity(conn, agent_identity, project_id, None, now)
    if row is None or code == REQUIRED:
        return None
    state = {"": "LIVE", EXPIRED: "EXPIRED", REVOKED: "REVOKED"}[code]
    return {"state": state, "grant_id": str(row["id"]), "expires_at": row["expires_at"]}


class ProjectGrantRefused(Exception):
    """A domain refusal inside a grant-table effect: the transaction rolls back."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def grant_effect(*, grant_id: str, agent_identity: str, project_id: str, delegator_kind: str,
                 delegator_identity: str, expires_at: float | None, operation_id: str, now: float,
                 operations: Any = None) -> Any:
    terms = terms_for(agent_identity, project_id, operations)
    sha = terms_sha256(terms, expires_at)

    def effect(conn: Any) -> None:
        # Local SQL on the supplied connection ONLY (the callback contract).
        conn.execute(
            f"UPDATE {_TABLE} SET state='REVOKED',revoked_at=?,revocation_reason='reapproved',updated_at=? "
            "WHERE agent_identity=? AND project_id=? AND state='LIVE'",
            (now, now, agent_identity, project_id),
        )
        conn.execute(
            f"INSERT INTO {_TABLE}(id,agent_identity,project_id,delegator_kind,delegator_identity,operations_json,"
            "terms_sha256,expires_at,state,revoked_at,revocation_reason,grant_operation_id,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,'LIVE',NULL,'',?,?,?)",
            (grant_id, agent_identity, project_id, delegator_kind, delegator_identity,
             json.dumps(terms["operations"]), sha, expires_at, operation_id, now, now),
        )

    return effect


def revoke_effect(*, agent_identity: str, project_id: str, reason: str, now: float) -> Any:
    def effect(conn: Any) -> None:
        changed = conn.execute(
            f"UPDATE {_TABLE} SET state='REVOKED',revoked_at=?,revocation_reason=?,updated_at=? "
            "WHERE agent_identity=? AND project_id=? AND state='LIVE'",
            (now, reason, now, agent_identity, project_id),
        ).rowcount
        if changed != 1:
            raise ProjectGrantRefused(REQUIRED)

    return effect
