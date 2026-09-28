"""The steward on the contract: its lifecycle and its children's authority (PHILO-9-02).

The RATIFIED design is the steward beat
(``docs/internal/philo/phase-9/steward-beat/README.md``); this module builds
it on the existing loop, kernel states, warrant and atomic receipt seam:

* **The pending handle (section 2).** ``project.run_steward`` is admitted,
  claimed, and left non-terminal while the run works: the call returns
  ``{run_id, operation_id, state, receipt: null}`` at once. The run row is
  persisted, linked to its operation (``steward_runs.operation_id``) and to
  its frozen authority (``authority_json``), BEFORE the handle is returned.
* **One terminal winner (section 3).** Every end of the run -- completed,
  failed, stopped, refused on lost authority -- writes the run row and the
  run operation's ONE receipt in ONE transaction (``transition_and_receipt``,
  strict). The completion re-reads the stop flag and the policy under that
  transaction; a stop that committed first wins.
* **Stop (section 3).** ``project.stop_steward`` is its own admitted
  operation: the stop flag and the stop's receipt in one transaction; the
  run ends later with its own ``cancelled`` receipt.
* **Children (sections 4 and 5).** Each executed policy slot is one
  ``project.steward.effect`` child of the run operation; each proposal the
  run accepts is one ``project.decide_proposal`` child. The child acts as
  the run's actor and names the run and its frozen authority
  (``project-steward:<run_id>:<authority_sha256>``); the claim re-checks the
  durable stop and the policy digest (the cutoff).
* **The scheduler (section 4).** Unattended runs act as SCHEDULER
  ``local-steward-conductor`` under the owner's RECORDED policy
  (``steward_policies.configure_operation_id``), never as a manufactured
  OWNER.
* **Recovery (section 3).** After a hub restart, every steward operation left
  non-terminal ends ``indeterminate / hub_restart_during_steward`` with its
  receipt, children first, and its run row ``interrupted`` in the same
  transaction; a legacy run with no operation is interrupted as before.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from holdspeak.kernel import project as rooms
from holdspeak.principals import Principal, PrincipalKind

from ..logging_config import get_logger
from .errors import NotFound, ServiceError, ValidationError

log = get_logger("steward_contract")

_TERMINAL_RUN_STATES = frozenset({"completed", "failed", "interrupted"})
_RUN_NAMESPACE = uuid.UUID("0e5bd8a1-2f0c-4d8e-9b0b-7d1d6c4f1e22")
SCHEDULER = Principal(PrincipalKind.SCHEDULER, rooms.STEWARD_SCHEDULER)


class StewardStopWon(Exception):
    """A stop committed before the completion's transaction: the completion rolls back."""


class StewardRunAlreadyTerminal(Exception):
    """The run already ended (another winner): nothing is written."""


class StewardAuthorityLost(Exception):
    """The frozen policy changed or was disabled: the run ends refused with the code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _refusal(code: str, message: str, status: int = 409) -> ServiceError:
    return ServiceError(code, message, context={"status": status})


def policy_terms(policy: Optional[dict[str, Any]]) -> dict[str, Any]:
    """The policy's semantic terms (the beat, section 4): provenance ids stay outside."""
    if not policy:
        return {}

    def _json(value: Any, default: Any) -> Any:
        try:
            return json.loads(value) if isinstance(value, str) else (value if value is not None else default)
        except (TypeError, ValueError):
            return default

    return {
        "project_id": str(policy.get("project_id") or ""),
        "enabled": bool(policy.get("enabled", 1)),
        "unattended_enabled": bool(policy.get("unattended_enabled", 0)),
        "eligible_effect_kinds": sorted(_json(policy.get("eligible_effect_kinds_json"), [])),
        "bounds": _json(policy.get("bounds_json"), {}),
        "yolo_flags": _json(policy.get("yolo_flags_json"), {}),
        "max_retries": int(policy.get("max_retries") or 0),
        "max_actions_per_run": int(policy.get("max_actions_per_run") or 0),
        "cooldown_seconds": int(policy.get("cooldown_seconds") or 0),
        "nudge_template": str(policy.get("nudge_template") or ""),
    }


def _hash(terms: dict[str, Any]) -> str:
    """The Phase 7 helper, imported (``services/schedule_delegation.py``), never copied."""
    from holdspeak.services.schedule_delegation import _hash as schedule_hash

    return schedule_hash(dict(terms), None)


def policy_sha256(policy: Optional[dict[str, Any]]) -> str:
    return _hash(policy_terms(policy)) if policy else ""


class StewardContract:
    """The steward's operations on the one contract (a mixin of ProjectStewardService)."""

    _db: Any
    _delta: Any

    # ── the policy (project.configure_steward) ────────────────────────

    def configure_policy(
        self, principal: Principal, project_id: str, *, enabled: Optional[bool] = None,
        unattended_enabled: Optional[bool] = None, eligible_effect_kinds: Optional[list[str]] = None,
        max_retries: Optional[int] = None, max_actions_per_run: Optional[int] = None,
        cooldown_seconds: Optional[int] = None, bounds: Optional[dict[str, Any]] = None,
        evaluation_cadence_minutes: Optional[int] = None, command_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Read the policy (only ``project_id``), or write it as the owner's admitted operation.

        The write, its ``configure_operation_id`` (the beat, section 4: the
        operation that wrote these terms) and the operation's receipt commit
        in ONE transaction. The HTTP route's validation, for both transports.
        """
        from holdspeak.project_contracts import generate_pstpol_id
        from holdspeak.services import project_kernel
        from holdspeak.services.project_steward_service import EFFECT_KINDS
        from holdspeak.web.routes.steward import _serialize_policy

        fields = {"enabled": enabled, "unattended_enabled": unattended_enabled,
                  "eligible_effect_kinds": eligible_effect_kinds, "max_retries": max_retries,
                  "max_actions_per_run": max_actions_per_run, "cooldown_seconds": cooldown_seconds,
                  "bounds": bounds, "evaluation_cadence_minutes": evaluation_cadence_minutes}
        if all(value is None for value in fields.values()):
            self._require_project(project_id)
            return {"policy": _serialize_policy(self._db.steward_policies.get_policy_for_project(project_id))}
        _validate_policy_fields(fields, EFFECT_KINDS)
        self._require_project(project_id)
        handle = project_kernel.current()
        if handle is None:
            raise RuntimeError("a steward policy write runs only as an admitted operation")
        if handle.replay:
            return {"success": True, "policy": _serialize_policy(
                self._db.steward_policies.get_policy_for_project(project_id))}
        written: dict[str, str] = {}

        def effect(conn: Any) -> None:
            existing = self._db.steward_policies.get_policy_for_project_in_transaction(conn, project_id)
            if existing is None:
                policy_id = generate_pstpol_id()
                self._db.steward_policies.insert_policy_in_transaction(
                    conn, policy_id=policy_id, project_id=project_id,
                    eligible_effect_kinds_json=json.dumps(eligible_effect_kinds or []),
                    max_retries=3 if max_retries is None else max_retries,
                    max_actions_per_run=10 if max_actions_per_run is None else max_actions_per_run,
                    cooldown_seconds=0 if cooldown_seconds is None else cooldown_seconds,
                    bounds_json=json.dumps(bounds or {}),
                    enabled=0 if enabled is False else 1,
                    unattended_enabled=1 if unattended_enabled else 0,
                )
            else:
                policy_id = str(existing["id"])
                self._db.steward_policies.update_policy_in_transaction(
                    conn, policy_id,
                    eligible_effect_kinds_json=None if eligible_effect_kinds is None else json.dumps(eligible_effect_kinds),
                    max_retries=max_retries, max_actions_per_run=max_actions_per_run,
                    cooldown_seconds=cooldown_seconds,
                    bounds_json=None if bounds is None else json.dumps(bounds),
                    enabled=None if enabled is None else int(enabled),
                    unattended_enabled=None if unattended_enabled is None else int(unattended_enabled),
                )
            conn.execute("UPDATE steward_policies SET configure_operation_id=? WHERE id=?",
                         (handle.operation_id, policy_id))
            if evaluation_cadence_minutes is not None:
                from holdspeak.db.automations import AutomationRepository

                AutomationRepository.set_project_cadence_in_txn(conn, project_id, evaluation_cadence_minutes)
            policy = self._db.steward_policies.get_policy_in_transaction(conn, policy_id) or {}
            self._ledger.append_in_transaction(
                conn, principal, event_type="steward.configured", producer="ProjectStewardService",
                subject_ref=f"steward_policy:{policy_id}", source_revision="",
                facts={"policy_id": policy_id, "project_id": project_id,
                       "enabled": bool(policy.get("enabled")),
                       "unattended_enabled": bool(policy.get("unattended_enabled"))},
                refs=[f"project:{project_id}", f"steward_policy:{policy_id}"],
            )
            # Ruling A/B (round three): the whole answer is recorded with the
            # write and the receipt, so a replay of this key answers THESE
            # terms, never the policy as it is now.
            written["answer"] = {"success": True, "policy": _serialize_policy(policy)}
            project_kernel.answered(
                conn, command_id=command_id, project_id=project_id, command_kind="configure_steward",
                request_hash=project_kernel.request_hash(fields), answer=written["answer"], close=False,
            )

        handle.terminal("succeeded", "succeeded", f"project:{project_id}", effect=effect)
        return written["answer"]

    # ── the run (project.run_steward) ─────────────────────────────────

    def start_run(self, principal: Principal, project_id: str, watermark: Optional[str] = None,
                  command_id: Optional[str] = None) -> dict[str, Any]:
        """Start a run: admitted, persisted and linked, then worked on a daemon (the pending handle)."""
        return self._start_admitted(principal, project_id, str(watermark or ""), background=True)

    def _start_admitted(self, principal: Principal, project_id: str, watermark: str, *,
                        background: bool, parent_operation_id: str = "") -> dict[str, Any]:
        from holdspeak.db.steward import ActiveRunExistsError
        from holdspeak.services import project_kernel

        handle = project_kernel.current()
        if handle is None:
            raise RuntimeError("project.run_steward runs only as an admitted operation")
        if handle.replay:
            run = self._run_for_operation(handle.operation_id)
            return self._pending(run, handle.operation_id)
        self._require_project(project_id)
        policy = self._db.steward_policies.get_policy_for_project(project_id)
        if principal.kind is not PrincipalKind.OWNER and (policy is None or not policy.get("configure_operation_id")):
            raise _refusal("steward_policy_required",
                           "No recorded owner policy lets this principal run the steward. The owner saves the "
                           "steward policy first.")
        if policy is not None and not policy.get("enabled", 1):
            raise _refusal("steward_disabled", "The steward policy is disabled for this project")
        remaining = self._cooldown_remaining(project_id, policy)
        if remaining:
            raise _refusal("cooldown_active", f"Cooling down: {remaining}s remaining")
        authority = self._freeze(principal, project_id, policy, parent_operation_id)
        run_id = "pstrun_" + uuid.uuid5(_RUN_NAMESPACE, handle.operation_id).hex
        try:
            with self._db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                self._db.steward_runs.insert_run_in_transaction(
                    conn, run_id=run_id, project_id=project_id,
                    policy_id=(policy or {}).get("id"), state="queued", phase="observe",
                    requested_by=f"principal:{principal.identity}", watermark=watermark,
                )
                conn.execute("UPDATE steward_runs SET operation_id=?, authority_json=? WHERE id=?",
                             (handle.operation_id, json.dumps(authority, sort_keys=True), run_id))
        except ActiveRunExistsError as exc:
            raise _refusal("active_run_exists",
                           f"Project {project_id} already has an active steward run (STW-002)") from exc
        handle.detach()
        if background:
            threading.Thread(target=self._work, args=(principal, run_id, project_id, handle, authority),
                             daemon=True, name=f"steward-{run_id}").start()
        else:
            self._work(principal, run_id, project_id, handle, authority)
        return self._pending(self._db.steward_runs.get_run(run_id), handle.operation_id)

    def _pending(self, run: Optional[dict[str, Any]], operation_id: str) -> dict[str, Any]:
        from holdspeak.kernel.runtime import _configure

        store = _configure(self._db).store
        operation = store.operation(operation_id) or {}
        receipt = store.receipt(operation_id)
        return {"success": True, "run_id": (run or {}).get("id"), "operation_id": operation_id,
                "state": operation.get("state"), "receipt": dict(receipt) if receipt is not None else None}

    def _run_for_operation(self, operation_id: str) -> Optional[dict[str, Any]]:
        with self._db._connection() as conn:
            row = conn.execute("SELECT * FROM steward_runs WHERE operation_id=?", (operation_id,)).fetchone()
        return dict(row) if row is not None else None

    def _require_project(self, project_id: str) -> None:
        with self._db._connection() as conn:
            if conn.execute("SELECT 1 FROM projects WHERE id=?", (str(project_id),)).fetchone() is None:
                raise NotFound("project", project_id)

    def _cooldown_remaining(self, project_id: str, policy: Optional[dict[str, Any]]) -> int:
        cooldown = int((policy or {}).get("cooldown_seconds", 0) or 0)
        if cooldown <= 0:
            return 0
        for prior in self._db.steward_runs.list_runs(project_id, limit=20):
            if prior.get("state") not in ("completed", "failed"):
                continue
            completed_at = prior.get("completed_at")
            if not completed_at:
                return 0
            try:
                done = datetime.fromisoformat(str(completed_at).replace("Z", "+00:00"))
            except ValueError:
                return 0
            if done.tzinfo is None:
                done = done.replace(tzinfo=timezone.utc)
            elapsed = (self._now_utc() - done).total_seconds()
            return int(cooldown - elapsed) if elapsed < cooldown else 0
        return 0

    def _freeze(self, principal: Principal, project_id: str, policy: Optional[dict[str, Any]],
                parent_operation_id: str) -> dict[str, Any]:
        """The run's immutable authority (the beat, section 4)."""
        sha = policy_sha256(policy)
        delegator = ""
        if policy and policy.get("configure_operation_id"):
            from holdspeak.kernel.runtime import _configure

            owner_op = _configure(self._db).store.operation(str(policy["configure_operation_id"])) or {}
            delegator = str(owner_op.get("principal_identity") or "")
        terms = {"project_id": project_id, "actor_kind": principal.kind.value,
                 "actor_identity": principal.identity, "policy_sha256": sha,
                 "grant_id": "", "grant_sha256": ""}
        return {
            "policy_id": (policy or {}).get("id"),
            "configure_operation_id": (policy or {}).get("configure_operation_id"),
            "policy_sha256": sha,
            "policy_terms": policy_terms(policy),
            "authority_terms": terms,
            "authority_sha256": _hash(terms),
            "delegator_kind": "owner" if principal.kind is PrincipalKind.OWNER or delegator else "",
            "delegator_identity": principal.identity if principal.kind is PrincipalKind.OWNER else delegator,
            "parent_operation_id": parent_operation_id,
            "grant": None,
        }

    def _work(self, principal: Principal, run_id: str, project_id: str, handle: Any,
              authority: dict[str, Any]) -> None:
        """The run, under the trusted steward context (issued here, after the real claim)."""
        context = {
            "run_id": run_id, "operation_id": handle.operation_id, "project_id": project_id,
            "actor_kind": principal.kind.value, "actor_identity": principal.identity,
            "authority_sha256": authority["authority_sha256"],
            "delegator_kind": authority.get("delegator_kind") or "",
            "delegator_identity": authority.get("delegator_identity") or "",
            "cutoff": lambda: self._cutoff(run_id),
        }
        try:
            with rooms.steward_context(context):
                self.execute_phases(principal, run_id, project_id, handle=handle)
        except Exception:  # pragma: no cover - execute_phases closes every path itself
            log.error("steward run %s raised outside its phases", run_id, exc_info=True)

    # ── the boundary checks (the beat, section 3) ─────────────────────

    def _cutoff(self, run_id: str) -> str:
        """"" while the run may act; else the code that stops it (a durable stop, a changed policy)."""
        run = self._db.steward_runs.get_run(run_id)
        if run is None or run.get("state") in _TERMINAL_RUN_STATES:
            return "steward_run_already_terminal"
        if run.get("state") == "stopping" or run.get("stop_requested_at"):
            return "stop_requested"
        return self._authority_code(run)

    def _authority_code(self, run: dict[str, Any], conn: Any = None) -> str:
        try:
            authority = json.loads(run.get("authority_json") or "{}")
        except (TypeError, ValueError):
            authority = {}
        policy_id = authority.get("policy_id")
        if not policy_id:
            return ""  # a no-policy owner run: nothing to cut it off (Muad'Dib r1 C2)
        policy = (self._db.steward_policies.get_policy_in_transaction(conn, policy_id) if conn is not None
                  else self._db.steward_policies.get_policy(policy_id))
        if policy is None or not policy.get("enabled", 1):
            return "steward_disabled"
        if policy_sha256(policy) != authority.get("policy_sha256"):
            return "steward_policy_changed"
        return ""

    def _frozen_terms(self, run_id: str) -> Optional[dict[str, Any]]:
        """The run's frozen policy terms (``{}`` for a no-policy owner run); ``None`` off the contract."""
        if rooms.current_steward_context() is None:
            return None
        run = self._db.steward_runs.get_run(run_id) or {}
        try:
            authority = json.loads(run.get("authority_json") or "{}")
        except (TypeError, ValueError):
            return None
        terms = authority.get("policy_terms")
        return dict(terms) if isinstance(terms, dict) else None

    def _boundary(self, run_id: str) -> None:
        """Before each phase and each child: a stop stops, a lost authority refuses."""
        from holdspeak.services.project_steward_service import StopRequested

        code = self._cutoff(run_id)
        if code == "stop_requested":
            raise StopRequested(f"Run {run_id} stop requested")
        if code:
            raise StewardAuthorityLost(code)

    # ── the children (the beat, section 5) ────────────────────────────

    def _child(self, principal: Principal, name: str, payload: dict[str, Any],
               call: Callable[[], Any]) -> Any:
        """One child operation of the run: admitted, claimed (the cutoff), executed once, receipted."""
        from holdspeak.services import project_kernel
        from holdspeak.services.project_steward_service import StopRequested

        context = rooms.current_steward_context()
        if context is None:
            return call()  # a run outside the contract (the engine's own test seam, run_once)
        self._boundary(str(context["run_id"]))
        try:
            result, _kernel = project_kernel.run(
                self._db, principal, name, payload, lambda _payload: call(),
                parent_operation_id=str(context["operation_id"]),
            )
        except project_kernel.ProjectKernelRefused as exc:
            if exc.code == "stop_requested":
                raise StopRequested(str(context["run_id"])) from exc
            if exc.code in {"steward_policy_changed", "steward_disabled"}:
                raise StewardAuthorityLost(exc.code) from exc
            raise
        return result

    def _effect_child(self, principal: Principal, run_id: str, project_id: str, effect_kind: str,
                      call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        """One ``project.steward.effect`` child for one executed policy slot."""
        from holdspeak.services import project_kernel

        def run_slot() -> dict[str, Any]:
            receipt = call()
            handle = project_kernel.current()
            outcome = str((receipt or {}).get("outcome") or "applied")
            if handle is not None and not handle.closed:
                handle.terminal("failed" if outcome == "failed" else "succeeded", outcome, f"steward_run:{run_id}")
            return receipt

        return self._child(principal, rooms.STEWARD_EFFECT,
                           {"run_id": run_id, "project_id": project_id, "effect_kind": effect_kind}, run_slot)

    # ── the terminal writes (the beat, section 3) ─────────────────────

    def _close_run(self, handle: Any, run_id: str, run_state: str, kernel_state: str, outcome: str,
                   summary: dict[str, Any]) -> None:
        """The run row, the run operation's state and its ONE receipt: one transaction."""
        from holdspeak.kernel.model import KernelRefused
        from holdspeak.services.project_steward_service import PHASES

        def effect(conn: Any) -> None:
            run = self._db.steward_runs.get_run_in_transaction(conn, run_id)
            if run is None or run.get("state") in _TERMINAL_RUN_STATES:
                raise StewardRunAlreadyTerminal(run_id)
            if kernel_state == "succeeded":
                if run.get("stop_requested_at") or run.get("state") == "stopping":
                    raise StewardStopWon(run_id)
                code = self._authority_code(run, conn)
                if code:
                    raise StewardAuthorityLost(code)
            self._db.steward_steps.interrupt_pending_steps_in_transaction(conn, run_id)
            self._db.steward_runs.update_run_state_in_transaction(
                conn, run_id, state=run_state, summary_json=json.dumps(summary, default=str))

        try:
            handle.terminal(kernel_state, outcome, f"steward_run:{run_id}", effect=effect)
        except StewardStopWon:
            done = [p for p in PHASES if p in (summary.get("phases_completed") or [])]
            self._close_run(handle, run_id, "interrupted", "cancelled", "stop_requested",
                            {"outcome": "interrupted", "reason": "stop_requested", "phases_completed": done})
        except StewardAuthorityLost as exc:
            self._close_run(handle, run_id, "interrupted", "refused", exc.code,
                            {"outcome": "interrupted", "reason": exc.code,
                             "phases_completed": summary.get("phases_completed") or []})
        except StewardRunAlreadyTerminal:
            return
        except KernelRefused:
            return  # a lost CAS: the winner's receipt stands, nothing is written

    # ── stop (project.stop_steward) ───────────────────────────────────

    def stop_run(self, principal: Principal, run_id: str, command_id: Optional[str] = None) -> dict[str, Any]:
        """A durable stop request, committed WITH the stop's receipt (its result: requested, not stopped)."""
        from holdspeak.services import project_kernel

        handle = project_kernel.current()
        if handle is None:
            raise RuntimeError("project.stop_steward runs only as an admitted operation")
        run = self._db.steward_runs.get_run(run_id)
        if run is None:
            raise NotFound("steward_run", run_id)
        if handle.replay:
            return {"success": True, "run_id": run_id}

        def effect(conn: Any) -> None:
            current = self._db.steward_runs.get_run_in_transaction(conn, run_id)
            if current is None or current.get("state") in _TERMINAL_RUN_STATES:
                raise _refusal("steward_run_already_terminal", f"Steward run {run_id} already ended")
            self._db.steward_runs.request_stop_in_transaction(conn, run_id)

        handle.terminal("succeeded", "stop_requested", f"steward_run:{run_id}", effect=effect)
        return {"success": True, "run_id": run_id}

    # ── the read (project.get_steward_run) ────────────────────────────

    def read_run(self, principal: Principal, run_id: str) -> dict[str, Any]:
        """The run, its steps, its operation and its terminal receipt (null while it works)."""
        from holdspeak.kernel.runtime import _configure
        from holdspeak.web.routes.steward import _serialize_run, _serialize_steps

        run = self._db.steward_runs.get_run(run_id)
        if run is None:
            raise NotFound("steward_run", run_id)
        operation_id = run.get("operation_id") or None
        receipt = _configure(self._db).store.receipt(operation_id) if operation_id else None
        return {"run": _serialize_run(run), "steps": _serialize_steps(self._db.steward_steps.list_steps(run_id)),
                "operation_id": operation_id, "receipt": dict(receipt) if receipt is not None else None}

    # ── the trigger (project.steward.trigger) ─────────────────────────

    def trigger(self, principal: Principal, command_id: Optional[str] = None) -> dict[str, Any]:
        """Evaluate the due watches and run the due steward work, as the owner's admitted operation.

        Returns the pending handle at once; the trigger's operation stays
        live until its child runs settle, then ends with its one receipt.
        """
        from holdspeak.services import project_kernel
        from holdspeak.workbench_conductor import get_scheduler_services

        handle = project_kernel.current()
        if handle is None:
            raise RuntimeError("project.steward.trigger runs only as an admitted operation")
        if handle.replay:
            return self._trigger_handle(handle.operation_id)
        wired_watch, wired_steward = get_scheduler_services()
        if wired_watch is None and wired_steward is None:
            raise _refusal(
                "scheduler_not_wired",
                "project.steward.trigger needs the conductor's scheduler services, which only the running hub "
                "wires. Nothing was evaluated and no steward run started. Start the hub and retry.", 503)
        handle.detach()

        def drain() -> None:
            outcomes: dict[str, Any] = {"evaluate": [], "runs": []}
            try:
                if wired_watch is not None:
                    # Each due watch's evaluation (a provider read) is its own
                    # admitted child of the trigger, with its leaf receipt.
                    def admit(watch_id: str, evaluate: Callable[[], Any]) -> Any:
                        result, _kernel = project_kernel.run(
                            self._db, principal, "project.watch.evaluate", {"watch_id": watch_id},
                            lambda _payload: evaluate(), parent_operation_id=handle.operation_id,
                        )
                        return result

                    outcomes["evaluate"] = wired_watch.evaluate_due(principal, limit=None, admit=admit)
                if wired_steward is not None:
                    outcomes["runs"] = wired_steward.run_due(principal, parent_operation_id=handle.operation_id)
                # The terminal result carries the watch and run outcomes (the
                # beat, section 4); each run is also a child operation.
                summary = json.dumps({
                    "evaluated": len(outcomes["evaluate"]),
                    "deferred": int(getattr(wired_watch, "last_sweep_deferred", 0) or 0),
                    "runs": [str(o.get("outcome") or "") for o in outcomes["runs"]],
                }, separators=(",", ":"))
                handle.terminal("succeeded", summary, "")
            except Exception as exc:  # pragma: no cover - a real fault is recorded, never dressed as success
                log.error("steward trigger failed: %s", exc, exc_info=True)
                try:
                    handle.terminal("failed", type(exc).__name__[:60] or "failed")
                except Exception:
                    pass

        threading.Thread(target=drain, daemon=True, name=f"steward-trigger-{handle.operation_id}").start()
        return self._trigger_handle(handle.operation_id)

    def _trigger_handle(self, operation_id: str) -> dict[str, Any]:
        from holdspeak.kernel.runtime import _configure

        store = _configure(self._db).store
        operation = store.operation(operation_id) or {}
        receipt = store.receipt(operation_id)
        return {"success": True, "operation_id": operation_id, "state": operation.get("state"),
                "receipt": dict(receipt) if receipt is not None else None}

    # ── the scheduler (the beat, section 4; A6) ───────────────────────

    def start_scheduled(self, principal: Principal, project_id: str, watermark: str, *,
                        parent_operation_id: str = "") -> dict[str, Any]:
        """One due run, admitted and worked synchronously on the caller's thread.

        The conductor passes SCHEDULER ``local-steward-conductor``: its root
        is admitted under the owner's RECORDED policy (``configure_operation_id``).
        A manual trigger passes the owner and its own operation: the run is
        the trigger's child.
        """
        from holdspeak.services import project_kernel

        policy = self._db.steward_policies.get_policy_for_project(project_id) or {}
        call = lambda payload: self._start_admitted(  # noqa: E731
            principal, payload["project_id"], payload.get("watermark") or "", background=False,
            parent_operation_id=parent_operation_id)
        args = {"project_id": project_id, "watermark": watermark}
        if principal.kind is PrincipalKind.SCHEDULER:
            root = {
                "authority_basis": (f"project-steward-policy:{policy.get('id')}:{policy_sha256(policy)}"
                                    if policy.get("configure_operation_id") else "project-steward-policy:unrecorded"),
                "delegator_kind": "owner" if policy.get("configure_operation_id") else "",
                "delegator_identity": self._configurer(policy),
            }
            with rooms.scheduler_root(root):
                result, _kernel = project_kernel.run(self._db, principal, "project.run_steward", args, call)
            return result
        result, _kernel = project_kernel.run(self._db, principal, "project.run_steward", args, call,
                                             parent_operation_id=parent_operation_id)
        return result

    def _configurer(self, policy: dict[str, Any]) -> str:
        if not policy.get("configure_operation_id"):
            return ""
        from holdspeak.kernel.runtime import _configure

        return str((_configure(self._db).store.operation(str(policy["configure_operation_id"])) or {})
                   .get("principal_identity") or "")

    # ── the nudges (F9: the hub's service, its real collaborators) ────

    def nudges(self, principal: Principal, project_id: str, state: Optional[str] = None) -> list[dict[str, Any]]:
        return self.list_nudges(project_id, state=state)

    def send_nudge_command(self, principal: Principal, step_id: str, text: str) -> dict[str, Any]:
        """Send a reviewed nudge; a refusal is a named ServiceError (its operation ends refused)."""
        if not (text or "").strip():
            raise _refusal("empty_text", "The nudge text must not be empty", 400)
        result = self.send_nudge(principal, step_id, text)
        if "error" in result:
            code = str(result["error"])
            raise ServiceError(code, code.replace("_", " "),
                               context={"status": 404 if code == "nudge_not_found" else 409,
                                        **{k: v for k, v in result.items() if k != "error"}})
        # Codex Astra r3: the comment's own evidence (URL, reviewer, time) and the
        # kernel receipt the transports add are two things, under two keys.
        return {"success": True, "comment_receipt": result.get("receipt")}

    # ── recovery (the beat, section 3; L6) ────────────────────────────

    def recover_admitted_on_startup(self) -> dict[str, int]:
        """Settle abandoned steward work BEFORE starts are accepted: descendants first, then parents.

        Every steward operation left non-terminal ends ``indeterminate /
        hub_restart_during_steward`` with its receipt, and its run row ends
        ``interrupted`` in the SAME transaction. An operation with no run and a
        queued run whose worker never started are both covered. Existing
        winners are kept; a repeat is a no-op; nothing is replayed.
        """
        from holdspeak.kernel.desk_broker import journal_receipt
        from holdspeak.kernel.model import KernelRefused
        from holdspeak.kernel.runtime import _configure

        store = _configure(self._db).store
        pending: list[dict[str, Any]] = []
        for state in ("admitting", "awaiting_decision", "awaiting_execution", "claimed"):
            pending.extend(op for op in store.operations_in_state(state) if rooms.is_project(op["name"]))
        # descendants first: an operation whose id is some other's parent closes after it
        parents = {str(op.get("parent_operation_id") or "") for op in pending}
        pending.sort(key=lambda op: (op["operation_id"] in parents, float(op.get("created_at") or 0)))
        closed = 0
        for operation in pending:
            reason = ("hub_restart_during_steward" if operation["name"] in rooms.STEWARD_OPERATIONS
                      else "hub_restart_during_decision")
            run = self._run_for_operation(str(operation["operation_id"]))

            def effect(conn: Any, run: Optional[dict[str, Any]] = run) -> None:
                if run is None:
                    return
                current = self._db.steward_runs.get_run_in_transaction(conn, run["id"])
                if current is None or current.get("state") in _TERMINAL_RUN_STATES:
                    return
                self._db.steward_steps.interrupt_pending_steps_in_transaction(conn, run["id"])
                self._db.steward_runs.update_run_state_in_transaction(
                    conn, run["id"], state="interrupted",
                    summary_json=json.dumps({"outcome": "interrupted", "reason": reason,
                                             "interrupted_phase": current.get("phase")}))

            try:
                ended, _receipt = store.transition_and_receipt(
                    operation["operation_id"], int(operation["revision"]), "indeterminate", reason,
                    f"steward_run:{run['id']}" if run else "", strict=True, warrant_revoked=1, effect=effect)
            except KernelRefused:
                continue
            journal_receipt(store, ended, reason)
            closed += 1
        legacy = self.recover_on_startup()  # an old unlinked run: interrupted as legacy work
        return {"operations": closed, "legacy_runs": len(legacy)}


def _validate_policy_fields(fields: dict[str, Any], effect_kinds: tuple[str, ...]) -> None:
    """The HTTP route's policy validation, for both transports."""
    def refuse(message: str) -> None:
        raise ValidationError(message, code="validation_error")

    eligible = fields.get("eligible_effect_kinds")
    if eligible is not None:
        if not isinstance(eligible, list):
            refuse("eligible_effect_kinds must be a list")
        invalid = [k for k in eligible if k not in effect_kinds]
        if invalid:
            refuse(f"Invalid effect kinds: {invalid}. Valid: {list(effect_kinds)}")
    for field, ceiling in (("max_retries", 100), ("max_actions_per_run", 1000), ("cooldown_seconds", 86400)):
        value = fields.get(field)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                refuse(f"{field} must be a non-negative integer")
            if value > ceiling:
                refuse(f"{field} cannot exceed {ceiling}")
    for field in ("enabled", "unattended_enabled"):
        value = fields.get(field)
        if value is not None and not isinstance(value, bool):
            refuse(f"{field} must be a boolean")
    cadence = fields.get("evaluation_cadence_minutes")
    if cadence is not None:
        if isinstance(cadence, bool) or not isinstance(cadence, int) or cadence < 1:
            refuse("evaluation_cadence_minutes must be an integer >= 1")
        if cadence > 10080:
            refuse("evaluation_cadence_minutes cannot exceed 10080 (7 days)")
