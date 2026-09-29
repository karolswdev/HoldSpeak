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
#: PHILO-9-07: the project delegation grant lives in its own concern module
#: (``kernel/project_grant.py``); its names stay readable here.
from .project_grant import (  # noqa: E402,F401
    PROJECT_GRANT_OPERATIONS, REQUIRED, EXPIRED, REVOKED, PROJECT_BASIS_KIND, GRANT_CODES,
    terms_for, terms_sha256, basis, parse_basis, check_row, by_identity, by_grant, by_basis,
    provenance, grant_code, frozen_grant_code, grant_view, ProjectGrantRefused, grant_effect, revoke_effect,
)
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
#: #694 (Codex Astra counsel r2): the Room operations an AGENT can never be
#: admitted to outside its own steward run -- no grant covers them and they
#: are not the agent's prepare. ``ProjectCodec.authorize`` refuses a non-owner
#: by this set. (What a THREAD acting as the owner may do is the owner's
#: separate ruling: ``holdspeak/mcp/tool_authority.py``.)
OWNER_ONLY_OPERATIONS: frozenset[str] = (PROJECT_KERNEL_OPERATIONS - PROJECT_GRANT_OPERATIONS
                                         - AGENT_PREPARE_OPERATIONS)
#: The operations whose terminal receipt a daemon writes later (the beat, section 2).
ASYNC_OPERATIONS: frozenset[str] = frozenset({"project.run_steward", "project.steward.trigger"})
#: The steward's operations the startup recovery closes as ``hub_restart_during_steward``.
STEWARD_OPERATIONS: frozenset[str] = frozenset({
    "project.run_steward", "project.steward.trigger", STEWARD_EFFECT,
})

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


OWNER_REQUIRED = "owner_principal_required"
#: The children a steward run makes under the run's actor (the beat, section 5).
STEWARD_CHILDREN: frozenset[str] = frozenset({STEWARD_EFFECT, "project.decide_proposal"})


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

