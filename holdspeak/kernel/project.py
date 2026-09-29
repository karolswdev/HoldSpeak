"""The Room's kernel operations: names, codes and the trusted paths (PHILO-9-02).

Article XI as the owner ruled it for the Room (Q1, admission BY EFFECT; Q2,
bounded delegation): every ADMITTED Room operation is one kernel operation
with one terminal receipt. An OWNER call is the owner's gesture (approved
inline, XI.4). An AGENT call is refused ``project_delegation_required`` with a
receipt unless a LIVE project grant for that agent and that project names the
operation (PHILO-9-07): this module holds that one check (:func:`grant_code`)
and the grant table's writes. Nothing here
decides WHAT is admitted: the descriptors (``holdspeak/operations.py``) do.

The design is the RATIFIED steward beat
(``docs/internal/philo/phase-9/steward-beat/README.md``): the steward's run is
one operation that stays non-terminal while its daemon works; each executed
effect is a child operation; the scheduler's runs act as SCHEDULER under the
owner's recorded policy, never as a manufactured OWNER.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import json
from typing import Any, Iterator, Mapping

#: story 01's admitted rows, enforced here.
ROOM_ADMITTED: frozenset[str] = frozenset({
    "project.archive", "project.link", "project.unlink", "project.decide_proposal",
    "project.accept_review", "project.publish_update", "project.resource.add",
    "project.resource.remove", "project.door.create",
})
#: this story's admitted rows (the charter's admission table).
STEWARD_AND_CONNECTORS_ADMITTED: frozenset[str] = frozenset({
    "project.door.count", "project.configure_steward", "project.run_steward",
    "project.stop_steward", "project.steward.trigger", "nudge.send",
    "project.watch.test", "project.watch.evaluate", "project.watch.set_rules",
    "project.watch.pause", "project.watch.resume", "project.watch.retire",
    "project.watch.update", "project.watch.baseline", "project.add_suggested_source",
    "connection.recheck", "project.mark_update_delivered",
})
#: PHILO-10-01: the Send's rows live beside their settle (``kernel/channel_send.py``).
from .channel_send import AGENT_PREPARE_OPERATIONS, CHANNEL_ADMITTED, SETTLED_ROW_REPLAY  # noqa: E402,F401
#: The beat's section 5: one child per executed policy slot that has no
#: admitted operation of its own. Internal: no transport, never grantable.
STEWARD_EFFECT = "project.steward.effect"
#: Its closed effect-kind enum (``apply_proposal_effects`` is not here: each
#: acceptance is its own ``project.decide_proposal`` child).
STEWARD_EFFECT_KINDS: frozenset[str] = frozenset({
    "observe_ci", "refresh_sources", "create_proposals", "draft_update",
    "create_door_item", "github_comment",
})
#: PHILO-9-07: the two owner-only operations that change a project grant (HTTP only, in no palette).
PROJECT_DELEGATION_OPERATIONS: frozenset[str] = frozenset({
    "project.delegation.grant", "project.delegation.revoke",
})
#: Scopes the atomic terminal writes, the claim and the recovery ONLY; never an authority set.
PROJECT_KERNEL_OPERATIONS: frozenset[str] = (ROOM_ADMITTED | STEWARD_AND_CONNECTORS_ADMITTED | {STEWARD_EFFECT}
                                             | PROJECT_DELEGATION_OPERATIONS | CHANNEL_ADMITTED)
#: The owner's ruled bound for the project grant ("Run, stop, publish"):
#: without a LIVE grant naming it for that project, every agent call is refused.
PROJECT_GRANT_OPERATIONS: frozenset[str] = frozenset({
    "project.run_steward", "project.stop_steward", "project.publish_update",
})
#: The operations whose terminal receipt a daemon writes later (the beat, section 2).
ASYNC_OPERATIONS: frozenset[str] = frozenset({"project.run_steward", "project.steward.trigger"})
#: The steward's operations the startup recovery closes as ``hub_restart_during_steward``.
STEWARD_OPERATIONS: frozenset[str] = frozenset({
    "project.run_steward", "project.steward.trigger", STEWARD_EFFECT,
})

REQUIRED = "project_delegation_required"
EXPIRED = "project_delegation_expired"
REVOKED = "project_delegation_revoked"
RUN_OWNER_REQUIRED = "steward_run_owner_required"

#: The node identity that claims and executes the Room's operations inside the hub.
PROJECT_EXECUTOR = "hub-project-writer"
PROJECT_PLACEMENT = f"node:{PROJECT_EXECUTOR}"
#: The scheduler's identity for the steward's unattended runs (the beat, section 4).
STEWARD_SCHEDULER = "local-steward-conductor"

#: Set only while the Room's kernel path (``services/project_kernel.py``) runs
#: an operation: a raw ``/api/kernel/submit`` of a Room name has no effect to
#: run, so it is refused with a receipt (the desk precedent).
_PROJECT_PATH: ContextVar[bool] = ContextVar("project_path", default=False)
#: The steward's trusted context, issued ONLY by the hub's steward service after
#: a real run claim (the beat, section 4): ``{run_id, operation_id, actor_kind,
#: actor_identity, project_id, authority_sha256}``. Never a public argument.
_STEWARD_CONTEXT: ContextVar[Mapping[str, Any] | None] = ContextVar("steward_context", default=None)
#: The scheduler's root admission: set by the steward service only while it
#: admits one unattended run under the recorded policy.
_SCHEDULER_ROOT: ContextVar[Mapping[str, Any] | None] = ContextVar("steward_scheduler_root", default=None)


@contextmanager
def project_path() -> Iterator[None]:
    token = _PROJECT_PATH.set(True)
    try:
        yield
    finally:
        _PROJECT_PATH.reset(token)


def in_project_path() -> bool:
    return _PROJECT_PATH.get()


@contextmanager
def steward_context(context: Mapping[str, Any]) -> Iterator[None]:
    token = _STEWARD_CONTEXT.set(dict(context))
    try:
        yield
    finally:
        _STEWARD_CONTEXT.reset(token)


def current_steward_context() -> Mapping[str, Any] | None:
    return _STEWARD_CONTEXT.get()


@contextmanager
def scheduler_root(context: Mapping[str, Any]) -> Iterator[None]:
    token = _SCHEDULER_ROOT.set(dict(context))
    try:
        yield
    finally:
        _SCHEDULER_ROOT.reset(token)


def scheduler_may_submit(name: str, principal: Any) -> bool:
    """The broker's declared-capability layer for a SCHEDULER (the beat, section 4).

    Only inside the hub's steward service: the root run it admits under the
    recorded policy, or a child of the run it claimed. Never a public path.
    """
    identity = str(getattr(principal, "identity", "") or "")
    if identity != STEWARD_SCHEDULER or not _PROJECT_PATH.get():
        return False
    root = _SCHEDULER_ROOT.get()
    if root is not None and name == "project.run_steward":
        return True
    context = _STEWARD_CONTEXT.get()
    return bool(context and context.get("actor_kind") == "scheduler"
                and name in {STEWARD_EFFECT, "project.decide_proposal", "inference.invoke"})


def scheduler_approves(operation: Mapping[str, Any], principal: Any) -> bool:
    """Approval of the scheduler's OWN steward operation, inside the trusted path only."""
    from ..principals import PrincipalKind

    if principal.kind is not PrincipalKind.SCHEDULER or not _PROJECT_PATH.get():
        return False
    if str(operation.get("principal_kind")) != "scheduler" or str(operation.get("principal_identity")) != principal.identity:
        return False
    name = str(operation.get("name") or "")
    if name == "project.run_steward":
        return _SCHEDULER_ROOT.get() is not None
    context = _STEWARD_CONTEXT.get()
    parent = str(operation.get("parent_operation_id") or "")
    # A model draft under the scheduler run's draft effect (the beat, section
    # 5): the broker's causality already bound it to a claimed parent of this
    # same actor.
    return bool(context and (
        (name in {STEWARD_EFFECT, "project.decide_proposal"} and parent == str(context.get("operation_id") or ""))
        or (name in _SCHEDULER_MODEL_CHILDREN and context.get("actor_kind") == "scheduler" and parent)))


_SCHEDULER_MODEL_CHILDREN = frozenset({"inference.invoke"})


# ── the project delegation grant (PHILO-9-07) ────────────────────────────
#
# The owner's Q2 ruling: an agent may do the bound (``PROJECT_GRANT_OPERATIONS``)
# in ONE project under a grant he gives. Phase 7's desk grant, scoped to a
# project (``kernel/desk.py``): the same one check (``desk.check_row``), the
# same codes in the same order, the same imported terms hash with the expiry
# inside it, the same atomic terminal writes. The grant rows are the sibling
# table ``kernel_project_delegations`` (one LIVE per agent and project).

PROJECT_BASIS_KIND = "project-delegation"
GRANT_CODES: frozenset[str] = frozenset({REQUIRED, EXPIRED, REVOKED})
OWNER_REQUIRED = "owner_principal_required"
#: The children a steward run makes under the run's actor (the beat, section 5).
STEWARD_CHILDREN: frozenset[str] = frozenset({STEWARD_EFFECT, "project.decide_proposal"})
_TABLE = "kernel_project_delegations"


def terms_for(agent_identity: str, project_id: str) -> dict[str, Any]:
    """The grant's terms, stored in the row: a later code change never widens an old grant."""
    return {"agent_identity": agent_identity, "project_id": project_id,
            "operations": sorted(PROJECT_GRANT_OPERATIONS)}


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
                 delegator_identity: str, expires_at: float | None, operation_id: str, now: float) -> Any:
    terms = terms_for(agent_identity, project_id)
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


def agent_steward_child(name: str, principal: Any, parent_operation_id: str) -> bool:
    """The steward's trusted path for an AGENT run's child (the beat, section 4).

    True only inside the hub's steward service, for a child the run's own
    agent makes under the run's operation. Generic agent children keep the
    kernel's refusal.
    """
    from ..principals import PrincipalKind

    context = _STEWARD_CONTEXT.get()
    return bool(
        getattr(principal, "kind", None) is PrincipalKind.AGENT and _PROJECT_PATH.get() and context
        and context.get("actor_kind") == "agent" and context.get("actor_identity") == principal.identity
        and name in STEWARD_CHILDREN and parent_operation_id
        and parent_operation_id == str(context.get("operation_id") or "")
    )


def project_approval_code(broker: Any, operation: Mapping[str, Any], principal: Any) -> str | None:
    """T3 for the Room (PHILO-9-07): ``None`` when this is not the agent's granted Room operation.

    Else "" (the kernel approves) or the refusal code: the agent's own
    ``PROJECT_GRANT_OPERATIONS`` operation by the grant its frozen basis
    names; a child of its own steward run by the run's frozen grant.
    """
    name = str(operation.get("name") or "")
    if not _PROJECT_PATH.get():
        return None
    if name in AGENT_PREPARE_OPERATIONS:
        # PHILO-10-01 (Q5): the agent's own prepare, under its own identity.
        return ""
    if agent_steward_child(name, principal, str(operation.get("parent_operation_id") or "")):
        with broker.store._connection() as conn:
            return agent_child_code(conn, principal, broker._clock())
    if name in PROJECT_GRANT_OPERATIONS and parse_basis(str(operation.get("authority_basis") or "")):
        with broker.store._connection() as conn:
            return by_basis(conn, operation, None, broker._clock(), authoritative=True)
    return None


def agent_child_code(conn: Any, principal: Any, now: float) -> str:
    """The frozen grant of the run whose child this is, re-checked (G1, never a newer G2)."""
    context = _STEWARD_CONTEXT.get() or {}
    return frozen_grant_code(conn, context.get("grant"), agent_identity=str(principal.identity),
                             project_id=str(context.get("project_id") or ""), now=now, authoritative=True)


def is_project(name: Any) -> bool:
    return str(name) in PROJECT_KERNEL_OPERATIONS


def steward_run_ended_effect(operation: Mapping[str, Any], reason: str) -> Any:
    """The liveness reaper's run-row write for a steward run operation (the beat, section 3).

    Local SQL on the seam's ONE connection: the linked run (if still active)
    ends ``interrupted`` in the same transaction as the operation's receipt.
    ``None`` for every other operation.
    """
    if str(operation.get("name") or "") not in STEWARD_OPERATIONS:
        return None
    operation_id = str(operation.get("operation_id") or "")

    def effect(conn: Any) -> None:
        conn.execute(
            "UPDATE steward_steps SET state='interrupted' WHERE run_id IN "
            "(SELECT id FROM steward_runs WHERE operation_id=? AND state IN ('queued','running','stopping')) "
            "AND state IN ('pending','running')",
            (operation_id,),
        )
        conn.execute(
            "UPDATE steward_runs SET state='interrupted', summary_json=?, completed_at=datetime('now'), "
            "updated_at=datetime('now') WHERE operation_id=? AND state IN ('queued','running','stopping')",
            ('{"outcome":"interrupted","reason":"%s"}' % reason, operation_id),
        )

    return effect

