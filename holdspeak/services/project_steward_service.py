"""Project Steward service: six-phase run engine (HS-163-02, STW-001..009).

OBSERVE -> COMPARE -> PROPOSE -> ACT -> VERIFY -> RECORD, every phase
checkpointing durable state.  run_once returns a pollable run before any
phase work (SS9.2).  stop() sets a durable request checked between phases
and before every effect slot (STW-003).  recover_on_startup() marks stale
running runs/steps interrupted (STW-009).

Phase bodies in 02 are the NO-EFFECT spine:
  OBSERVE  -> delegates to ProjectEvidenceCollector.collect_all
  COMPARE  -> delegates to ProjectDeltaService.open_review
  PROPOSE  -> thin wrapper (proposals live inside the review window)
  ACT      -> bounded effects (story 03: five effect kinds, verified,
               deduplicated, policy-bounded)
  VERIFY   -> writes run summary with verification receipts
  RECORD   -> writes ledger event in one transaction with final state
"""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from holdspeak.db.steward import ActiveRunExistsError
from holdspeak.principals import Principal
from holdspeak.project_contracts import generate_pstrun_id, generate_pststep_id
from holdspeak.services.service_event_ledger import ServiceEventLedger

from ..logging_config import get_logger

log = get_logger("project_steward")

# The six phases in order (SS9.2).
PHASES: tuple[str, ...] = ("observe", "compare", "propose", "act", "verify", "record")

# The five V0 effect kinds (SS9.3, HS-163-03).
EFFECT_KINDS: tuple[str, ...] = (
    "refresh_sources",
    "create_proposals",
    "apply_proposal_effects",
    "draft_update",
    "create_door_item",
)

# Severity rank for deterministic total order (highest-material first).
_SEVERITY_RANK: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


class StewardDisabledError(Exception):
    """The project's steward policy is disabled (counsel S-3)."""


class CooldownActiveError(Exception):
    """A cooldown from the last terminal run is still active (STW-008)."""

    def __init__(self, seconds_remaining: int) -> None:
        self.seconds_remaining = seconds_remaining
        super().__init__(
            f"Cooldown active: {seconds_remaining}s remaining"
        )


class StopRequested(Exception):
    """Raised internally when the durable stop flag is detected."""


class BoundExceeded(Exception):
    """Raised when STW-008 policy bounds are exceeded."""

    def __init__(self, bound: str, limit: int, current: int) -> None:
        self.bound = bound
        self.limit = limit
        self.current = current
        super().__init__(
            f"STW-008: {bound} exceeded (limit={limit}, current={current})"
        )


class ProjectStewardService:
    """Run coordination for the Project Steward (SS9.1, SS9.2).

    Constructed with a db handle, an evidence collector, and a delta service.
    The conductor's isolation pattern: each public method catches its own
    exceptions so a broken project never poisons the caller.
    """

    def __init__(
        self,
        db: Any,
        collector: Any,
        delta: Any,
        *,
        update_service: Any = None,
        project_service: Any = None,
        door_service: Any = None,
    ) -> None:
        self._db = db
        self._collector = collector
        self._delta = delta
        self._update_service = update_service
        self._project_service = project_service
        self._door_service = door_service
        self._ledger = ServiceEventLedger(db)

    # ── public API ────────────────────────────────────────────────────

    def run_once(
        self,
        principal: Principal,
        project_id: str,
        *,
        policy_id: Optional[str] = None,
        watermark: str = "",
    ) -> str:
        """Persist a queued run and return the run ID immediately (SS9.2).

        The worker executes the six phases synchronously on the calling
        thread (the conductor pattern: the caller is already on a daemon
        thread).  STW-002: ActiveRunExistsError propagates to the caller
        as a typed refusal.
        """
        run_id = self.insert_run(
            principal, project_id,
            policy_id=policy_id, watermark=watermark,
        )

        # Execute the six phases on the calling thread (conductor pattern).
        self.execute_phases(principal, run_id, project_id)

        return run_id

    def insert_run(
        self,
        principal: Principal,
        project_id: str,
        *,
        policy_id: Optional[str] = None,
        watermark: str = "",
    ) -> str:
        """Persist a queued run and return the run ID (SS9.2, STW-001).

        This is the INSERT half of the run_once seam.  The route layer
        calls this on the request thread so STW-002 ActiveRunExistsError
        surfaces synchronously as a typed 409 before the daemon thread
        starts phase execution.

        Existing callers that want synchronous execution still call
        run_once, which calls insert_run + execute_phases.
        """
        project_id = str(project_id).strip()

        # Counsel S-3: a disabled policy refuses the run outright.
        # Counsel S-2 / STW-008: cooldown_seconds gates a new run against
        # the last COMPLETED or FAILED run; interrupted runs are exempt
        # (STW-009: recovery must leave the project re-runnable).
        policy = self._db.steward_policies.get_policy_for_project(project_id)
        if policy is not None:
            if not policy.get("enabled", 1):
                raise StewardDisabledError(
                    f"Steward policy for {project_id} is disabled"
                )
            cooldown = int(policy.get("cooldown_seconds", 0) or 0)
            if cooldown > 0:
                for prior in self._db.steward_runs.list_runs(
                    project_id, limit=20,
                ):
                    if prior.get("state") not in ("completed", "failed"):
                        continue
                    completed_at = prior.get("completed_at")
                    if not completed_at:
                        break
                    try:
                        done = datetime.fromisoformat(
                            str(completed_at).replace("Z", "+00:00")
                        )
                    except ValueError:
                        break
                    if done.tzinfo is None:
                        done = done.replace(tzinfo=timezone.utc)
                    elapsed = (
                        datetime.now(timezone.utc) - done
                    ).total_seconds()
                    if elapsed < cooldown:
                        raise CooldownActiveError(int(cooldown - elapsed))
                    break

        run_id = generate_pstrun_id()

        # STW-001: durable BEFORE asynchronous work.
        # STW-002: the partial unique index raises ActiveRunExistsError
        # if another active run exists for this project.
        self._db.steward_runs.insert_run(
            run_id=run_id,
            project_id=project_id,
            policy_id=policy_id,
            state="queued",
            phase="observe",
            requested_by=f"principal:{principal.identity}",
            watermark=watermark,
        )

        return run_id

    def stop(self, run_id: str) -> None:
        """Set the durable stop request (STW-003).

        The loop checks this between phases AND before every effect slot.
        Never dependent on a model response.
        """
        self._db.steward_runs.request_stop(str(run_id).strip())

    def recover_on_startup(self) -> list[str]:
        """Mark stale running/queued/stopping runs as interrupted (STW-009).

        Leaves the project re-runnable: the partial unique index only
        covers queued/running/stopping, so interrupted frees the slot.

        Returns a list of recovered run IDs.
        """
        recovered: list[str] = []
        with self._db._connection() as conn:
            # Find all runs in active states (queued, running, stopping).
            rows = self._db.steward_runs.list_all_active_runs_in_transaction(conn)

            for row in rows:
                run_id = row["id"]
                phase = row["phase"]

                # Mark any pending/running steps as interrupted.
                self._db.steward_steps.interrupt_pending_steps_in_transaction(
                    conn, run_id
                )

                # Mark the run as interrupted with an honest summary.
                summary = json.dumps({
                    "outcome": "interrupted",
                    "reason": "startup_recovery",
                    "interrupted_phase": phase,
                })
                self._db.steward_runs.update_run_state_in_transaction(
                    conn,
                    run_id,
                    state="interrupted",
                    summary_json=summary,
                )

                recovered.append(run_id)
                log.info(
                    "STW-009 recovery: run %s (phase %s) -> interrupted",
                    run_id, phase,
                )

        return recovered

    # ── phase execution loop ──────────────────────────────────────────

    def execute_phases(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
    ) -> None:
        """Walk OBSERVE -> ... -> RECORD with a checkpoint per transition.

        This is the EXECUTE half of the run_once seam.  The route layer
        calls this from a daemon thread after insert_run returns the ID
        on the request path.  Existing callers (run_once, tests) call
        it synchronously.

        Failure isolation per the conductor's patterns (SS9.1): exceptions
        are caught, the run is marked failed with an honest summary, and
        the caller is not poisoned.
        """
        try:
            # Transition queued -> running.
            self._db.steward_runs.update_run_state(
                run_id, state="running", phase="observe",
            )

            phase_results: dict[str, Any] = {}

            for phase in PHASES:
                # STW-003: check durable stop BETWEEN phases.
                self._check_stop(run_id)

                # Checkpoint: update run phase.
                self._db.steward_runs.update_run_state(
                    run_id, state="running", phase=phase,
                )

                # Create a step record for this phase.  seq allocates
                # from the live step count so phase rows and act-effect
                # rows share ONE strictly increasing chronology (the
                # glass interleave scar).
                step_id = generate_pststep_id()
                seq = len(self._db.steward_steps.list_steps(run_id))
                self._db.steward_steps.insert_step(
                    step_id=step_id,
                    run_id=run_id,
                    phase=phase,
                    seq=seq,
                    state="running",
                    effect_kind=f"phase:{phase}",
                    idempotency_key=f"{run_id}:{phase}",
                )

                try:
                    # STW-003: check stop before every effect slot.
                    self._check_stop(run_id)

                    result = self._run_phase(
                        principal, run_id, project_id, phase,
                        phase_results,
                    )
                    phase_results[phase] = result

                    # Mark step completed.
                    self._db.steward_steps.update_step(
                        step_id,
                        state="completed",
                        observed_state_json=json.dumps(
                            result if isinstance(result, dict) else {"ok": True},
                            default=str,
                        ),
                    )

                except StopRequested:
                    self._db.steward_steps.update_step(
                        step_id,
                        state="interrupted",
                        error_json=json.dumps({"reason": "stop_requested"}),
                    )
                    raise

                except Exception as exc:
                    self._db.steward_steps.update_step(
                        step_id,
                        state="failed",
                        error_json=json.dumps({
                            "code": type(exc).__name__,
                            "message": str(exc),
                        }),
                    )
                    raise

            # All six phases complete: mark the run completed.
            summary = json.dumps({
                "outcome": "completed",
                "phases_completed": list(PHASES),
                "phase_results": {
                    k: (v if isinstance(v, dict) else {"ok": True})
                    for k, v in phase_results.items()
                },
            }, default=str)
            self._db.steward_runs.update_run_state(
                run_id,
                state="completed",
                summary_json=summary,
            )

        except StopRequested:
            # Graceful stop: run transitions stopping -> interrupted.
            current = self._db.steward_runs.get_run(run_id)
            interrupted_phase = current["phase"] if current else "unknown"
            summary = json.dumps({
                "outcome": "interrupted",
                "reason": "stop_requested",
                "interrupted_phase": interrupted_phase,
                "phases_completed": [
                    p for p in PHASES
                    if p in phase_results
                ],
            }, default=str)
            self._db.steward_runs.update_run_state(
                run_id,
                state="interrupted",
                summary_json=summary,
            )
            log.info("Run %s stopped at phase %s", run_id, interrupted_phase)

        except Exception as exc:
            # Failure isolation: mark failed, never poison the caller.
            summary = json.dumps({
                "outcome": "failed",
                "error": {"code": type(exc).__name__, "message": str(exc)},
                "phases_completed": [
                    p for p in PHASES
                    if p in phase_results
                ],
            }, default=str)
            self._db.steward_runs.update_run_state(
                run_id,
                state="failed",
                summary_json=summary,
            )
            log.error("Run %s failed: %s", run_id, exc, exc_info=True)

    # ── per-phase dispatch ────────────────────────────────────────────

    def _run_phase(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
        phase: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Dispatch to the appropriate phase handler."""
        if phase == "observe":
            return self._phase_observe(principal, project_id)
        elif phase == "compare":
            return self._phase_compare(principal, project_id)
        elif phase == "propose":
            return self._phase_propose(principal, project_id, phase_results)
        elif phase == "act":
            return self._phase_act(principal, run_id, project_id, phase_results)
        elif phase == "verify":
            return self._phase_verify(principal, run_id, project_id, phase_results)
        elif phase == "record":
            return self._phase_record(principal, run_id, project_id, phase_results)
        else:
            return {"skipped": True, "reason": f"unknown phase {phase}"}

    # ── OBSERVE ───────────────────────────────────────────────────────

    def _phase_observe(
        self,
        principal: Principal,
        project_id: str,
    ) -> dict[str, Any]:
        """Delegate to the 160 evidence collector (SS5.5)."""
        coverage = self._collector.collect_all(project_id)
        return {"coverage": coverage}

    # ── COMPARE ───────────────────────────────────────────────────────

    def _phase_compare(
        self,
        principal: Principal,
        project_id: str,
    ) -> dict[str, Any]:
        """Delegate to the Delta's deterministic review machinery (SS7.2).

        STW-007: model failure falls back to deterministic with a receipt.
        """
        review = self._delta.open_review(principal, project_id)
        return {
            "review_id": review.get("id", ""),
            "proposal_count": len(review.get("proposals", [])),
            "proposals": review.get("proposals", []),
        }

    # ── PROPOSE ───────────────────────────────────────────────────────

    def _phase_propose(
        self,
        principal: Principal,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Thin wrapper: proposals live inside the review window.

        The Delta's open_review already generated and stored deterministic
        proposals.  This phase is the hook for model augmentation (story 03+).
        """
        compare_result = phase_results.get("compare", {})
        return {
            "review_id": compare_result.get("review_id", ""),
            "proposal_count": compare_result.get("proposal_count", 0),
            "proposals": compare_result.get("proposals", []),
        }

    # ── ACT (HS-163-03: the bounded hand) ─────────────────────────────

    def _phase_act(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute bounded V0 effects, each checkpointed and policy-gated.

        Five effect kinds (SS9.3):
        1. refresh_sources: refresh configured sources, persist observations
        2. create_proposals: deterministic proposals + evidence links
        3. apply_proposal_effects: apply configured Project-owned effects
        4. draft_update: draft or replace unaccepted update (UPD-004)
        5. create_door_item: ONE deduplicated Door item for the
           highest-material overdue/blocking item lacking follow-through

        Every effect:
        - Step row FIRST with idempotency_key (STW-001)
        - Stop checked before acting (STW-003)
        - Policy eligibility checked (STW-010)
        - STW-005: reconcile by idempotency_key before re-acting
        - expected_state_json before apply, observed_state_json after
        - STW-008: bounded by policy (max_actions_per_run, max_retries)
        """
        # Load policy for this project
        policy = self._load_policy(project_id)
        eligible_kinds = set(json.loads(
            policy.get("eligible_effect_kinds_json", "[]")))
        max_actions = policy.get("max_actions_per_run", 10)
        max_retries = policy.get("max_retries", 3)

        # Collect the run's watermark for Door dedup.
        run_row = self._db.steward_runs.get_run(run_id)
        watermark = run_row.get("watermark", "") if run_row else ""

        actions_taken = 0
        effect_receipts: list[dict[str, Any]] = []
        effects_skipped: list[dict[str, Any]] = []

        # Get the current step sequence number.
        existing_steps = self._db.steward_steps.list_steps(run_id)
        seq = len(existing_steps)

        for effect_kind in EFFECT_KINDS:
            # STW-003: check stop before every effect slot.
            self._check_stop(run_id)

            # STW-008: max_actions_per_run check.
            if actions_taken >= max_actions:
                effects_skipped.append({
                    "effect_kind": effect_kind,
                    "reason": "max_actions_per_run_exceeded",
                    "limit": max_actions,
                })
                log.info(
                    "STW-008: skipping %s (max_actions=%d reached)",
                    effect_kind, max_actions,
                )
                continue

            # STW-010: check policy eligibility.
            if effect_kind not in eligible_kinds:
                effects_skipped.append({
                    "effect_kind": effect_kind,
                    "reason": "not_in_eligible_effect_kinds",
                })
                continue

            # Build the idempotency key for this effect.
            idem_key = self._effect_idempotency_key(
                run_id, effect_kind, project_id, watermark,
            )

            # STW-005: reconcile before re-acting.
            existing_step = self._db.steward_steps.get_step_by_idempotency_key(
                idem_key,
            )
            if existing_step and existing_step["state"] == "completed":
                effect_receipts.append({
                    "effect_kind": effect_kind,
                    "outcome": "reconciled",
                    "step_id": existing_step["id"],
                    "idempotency_key": idem_key,
                })
                log.info(
                    "STW-005: reconciled %s (key=%s already completed)",
                    effect_kind, idem_key,
                )
                continue

            # Create a step row FIRST (STW-001).
            step_id = generate_pststep_id()
            expected_state = self._compute_expected_state(
                effect_kind, project_id, phase_results,
            )
            self._db.steward_steps.insert_step(
                step_id=step_id,
                run_id=run_id,
                phase="act",
                seq=seq,
                state="running",
                effect_kind=effect_kind,
                idempotency_key=idem_key,
                expected_state_json=json.dumps(expected_state, default=str),
            )
            seq += 1

            # Apply the effect with retry logic (STW-008).
            receipt = self._apply_effect_with_retry(
                principal, run_id, project_id, step_id,
                effect_kind, phase_results, watermark,
                max_retries=max_retries,
            )

            effect_receipts.append(receipt)
            if receipt.get("outcome") == "applied":
                actions_taken += 1

        return {
            "actions_taken": actions_taken,
            "effect_receipts": effect_receipts,
            "effects_skipped": effects_skipped,
        }

    # ── effect application ───────────────────────────────────────────

    def _apply_effect_with_retry(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
        step_id: str,
        effect_kind: str,
        phase_results: dict[str, Any],
        watermark: str,
        *,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Apply a single effect with bounded retries (STW-008).

        Returns a receipt dict describing what happened.
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            # STW-003 (counsel M-1): a retry IS another effect slot --
            # the durable stop request is honored between attempts.
            self._check_stop(run_id)
            try:
                result = self._apply_effect(
                    principal, run_id, project_id, step_id,
                    effect_kind, phase_results, watermark,
                )

                # Record observed state (STW-004).
                observed = result if isinstance(result, dict) else {"ok": True}

                # Determine the true outcome: the inner effect may
                # return "reconciled" (STW-005 dedup) or "skipped"
                # (STW-007 fallback, missing service).
                inner_outcome = observed.get("outcome", "")
                is_skipped = observed.get("skipped", False)
                if inner_outcome == "reconciled":
                    outcome = "reconciled"
                elif is_skipped:
                    outcome = "skipped"
                else:
                    outcome = "applied"

                self._db.steward_steps.update_step(
                    step_id,
                    state="completed",
                    observed_state_json=json.dumps(observed, default=str),
                    receipt_json=json.dumps({
                        "effect_kind": effect_kind,
                        "outcome": outcome,
                        "attempt": attempt + 1,
                    }, default=str),
                )

                return {
                    "effect_kind": effect_kind,
                    "outcome": outcome,
                    "step_id": step_id,
                    "attempt": attempt + 1,
                    "result": observed,
                }

            except StopRequested:
                self._db.steward_steps.update_step(
                    step_id,
                    state="interrupted",
                    error_json=json.dumps({"reason": "stop_requested"}),
                )
                raise

            except Exception as exc:
                last_error = exc
                log.warning(
                    "Effect %s attempt %d/%d failed: %s",
                    effect_kind, attempt + 1, max_retries + 1, exc,
                )
                if attempt >= max_retries:
                    break

        # All retries exhausted.
        error_info = {
            "code": type(last_error).__name__ if last_error else "Unknown",
            "message": str(last_error) if last_error else "unknown error",
            "attempts": max_retries + 1,
        }
        self._db.steward_steps.update_step(
            step_id,
            state="failed",
            error_json=json.dumps(error_info),
            receipt_json=json.dumps({
                "effect_kind": effect_kind,
                "outcome": "failed",
                "error": error_info,
            }),
        )

        return {
            "effect_kind": effect_kind,
            "outcome": "failed",
            "step_id": step_id,
            "error": error_info,
        }

    def _apply_effect(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
        step_id: str,
        effect_kind: str,
        phase_results: dict[str, Any],
        watermark: str,
    ) -> dict[str, Any]:
        """Dispatch to the appropriate effect handler."""
        if effect_kind == "refresh_sources":
            return self._effect_refresh_sources(principal, project_id)
        elif effect_kind == "create_proposals":
            return self._effect_create_proposals(
                principal, project_id, phase_results,
            )
        elif effect_kind == "apply_proposal_effects":
            return self._effect_apply_proposals(
                principal, project_id, phase_results,
            )
        elif effect_kind == "draft_update":
            return self._effect_draft_update(principal, project_id)
        elif effect_kind == "create_door_item":
            return self._effect_create_door_item(
                principal, project_id, watermark, phase_results,
            )
        else:
            return {"skipped": True, "reason": f"unknown effect {effect_kind}"}

    # ── Effect 1: refresh sources ────────────────────────────────────

    def _effect_refresh_sources(
        self,
        principal: Principal,
        project_id: str,
    ) -> dict[str, Any]:
        """Refresh configured sources and persist observations (SS9.3-1).

        STW-006: source failures isolate to partial coverage.
        """
        try:
            coverage = self._collector.collect_all(project_id)
            return {
                "effect": "refresh_sources",
                "coverage": coverage,
                "partial": False,
            }
        except Exception as exc:
            log.warning(
                "STW-006: refresh_sources partial failure for %s: %s",
                project_id, exc,
            )
            return {
                "effect": "refresh_sources",
                "coverage": {},
                "partial": True,
                "error": str(exc),
            }

    # ── Effect 2: create proposals ───────────────────────────────────

    def _effect_create_proposals(
        self,
        principal: Principal,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Create deterministic proposals + evidence links (SS9.3-2).

        STW-007: model failure falls back to deterministic with a receipt.
        """
        try:
            review = self._delta.open_review(principal, project_id)
            return {
                "effect": "create_proposals",
                "review_id": review.get("id", ""),
                "proposal_count": len(review.get("proposals", [])),
            }
        except Exception as exc:
            # STW-007: deterministic fallback with intelligible receipt.
            log.warning(
                "STW-007: create_proposals failed for %s: %s",
                project_id, exc,
            )
            return {
                "effect": "create_proposals",
                "review_id": "",
                "proposal_count": 0,
                "fallback": "deterministic",
                "receipt": f"Model/delta failure: {exc}",
            }

    # ── Effect 3: apply proposal effects ─────────────────────────────

    def _effect_apply_proposals(
        self,
        principal: Principal,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply configured Project-owned proposal effects (SS9.3-3).

        Uses the 160 decide_proposal verb with the one-transaction
        create_item (the 161 S-2 law).  Every open proposal is accepted
        through the verb; per-proposal failures are receipted and never
        abort the batch.
        """
        compare_result = phase_results.get("compare", {})
        proposals = compare_result.get("proposals", [])

        applied = []
        skipped = []

        for proposal in proposals:
            lifecycle = proposal.get("lifecycle", "")
            if lifecycle != "open":
                skipped.append({
                    "proposal_id": proposal.get("id", ""),
                    "reason": f"lifecycle={lifecycle}",
                })
                continue

            proposal_kind = proposal.get("proposal_kind", "")
            proposal_id = proposal.get("id", "")

            # Accept through the delta's decide_proposal verb.
            try:
                result = self._delta.decide_proposal(
                    principal, project_id, proposal_id, "accept",
                )
                applied.append({
                    "proposal_id": proposal_id,
                    "proposal_kind": proposal_kind,
                    "result": "accepted",
                    "item_id": result.get("item_id"),
                })
            except Exception as exc:
                skipped.append({
                    "proposal_id": proposal_id,
                    "proposal_kind": proposal_kind,
                    "reason": str(exc),
                })

        return {
            "effect": "apply_proposal_effects",
            "applied": applied,
            "skipped": skipped,
        }

    # ── Effect 4: draft update ───────────────────────────────────────

    def _effect_draft_update(
        self,
        principal: Principal,
        project_id: str,
    ) -> dict[str, Any]:
        """Draft or replace an unaccepted update (SS9.3-4, UPD-004).

        STW-007: model failure falls back to deterministic with a receipt.
        Never touches a published update.
        """
        if self._update_service is None:
            return {
                "effect": "draft_update",
                "skipped": True,
                "reason": "update_service_not_configured",
            }

        try:
            update = self._update_service.draft_update(
                principal, project_id,
            )
            return {
                "effect": "draft_update",
                "update_id": update.get("id", ""),
                "lifecycle": update.get("lifecycle", "draft"),
                "generator": update.get("generator", "deterministic"),
            }
        except Exception as exc:
            # STW-007: deterministic fallback with receipt.
            log.warning(
                "STW-007: draft_update failed for %s: %s",
                project_id, exc,
            )
            return {
                "effect": "draft_update",
                "skipped": True,
                "reason": f"draft_failed: {exc}",
                "fallback": "deterministic",
            }

    # ── Effect 5: create Door item ───────────────────────────────────

    def _effect_create_door_item(
        self,
        principal: Principal,
        project_id: str,
        watermark: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Create EXACTLY ONE deduplicated Door item (SS9.3-5).

        Deterministic selection rule (total order):
          1. severity rank (critical=0 > high=1 > medium=2 > low=3 > null=999)
          2. due_at ASC NULLS LAST (soonest first)
          3. id ASC (stable tiebreak)

        Filters: overdue or blocking items (lifecycle in open/at_risk/broken)
        that lack canonical follow-through.

        Idempotency key: sha256(project_id + watermark + selected_item_id)
        A re-run with the same watermark creates ZERO additional items.
        """
        if self._door_service is None:
            return {
                "effect": "create_door_item",
                "skipped": True,
                "reason": "door_service_not_configured",
            }

        # Read the items to find the highest-material overdue/blocking one.
        selected_item = self._select_door_candidate(
            principal, project_id, phase_results,
        )

        if selected_item is None:
            return {
                "effect": "create_door_item",
                "skipped": True,
                "reason": "no_eligible_items",
            }

        item_id = selected_item.get("id", "")

        # Same-watermark dedup lives on the ACT step's idempotency key
        # (watermark-scoped, checked in _phase_act before this runs);
        # cross-watermark dedup is the follow-through read-back above.

        # Create the Door item through the canonical service.
        item_title = selected_item.get("title", "Steward follow-up")
        item_type = selected_item.get("item_type", "risk")
        severity = selected_item.get("severity")

        door_result = self._door_service.add_item(
            principal,
            f"[Steward] {item_title}",
            source_type="steward",
            source_ref=f"project_item:{item_id}",
        )

        return {
            "effect": "create_door_item",
            "door_item_id": door_result.get("id", ""),
            "source_item_id": item_id,
            "source_item_type": item_type,
            "source_severity": severity,
        }

    def _select_door_candidate(
        self,
        principal: Principal,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        """Select the highest-material overdue/blocking item.

        Deterministic total order:
          1. severity rank: critical(0) > high(1) > medium(2) > low(3) > null(999)
          2. due_at ASC NULLS LAST (most urgent first)
          3. id ASC (stable tiebreak)

        Eligible: lifecycle in (open, at_risk, broken, planned, pending)
        AND (overdue by due_at OR blocking lifecycle).
        """
        if self._project_service is None:
            return None

        try:
            items_result = self._project_service.list_items(
                principal,
                project_id,
                limit=200,
            )
            items = items_result.get("items", [])
        except Exception:
            return None

        if not items:
            return None

        # Filter to overdue/blocking items.
        now_date = datetime.now(timezone.utc).date().isoformat()
        candidates = []
        for item in items:
            lifecycle = (item.get("lifecycle") or "").lower()
            due_at = item.get("due_at")

            # "Blocking" lifecycles: at_risk, broken
            is_blocking = lifecycle in ("at_risk", "broken")

            # "Overdue": has a due_at in the past and lifecycle is active
            is_overdue = False
            if due_at and lifecycle in ("open", "planned", "active", "pending"):
                try:
                    if due_at[:10] < now_date:
                        is_overdue = True
                except (TypeError, ValueError):
                    pass

            if not (is_blocking or is_overdue):
                continue

            # The charter's law: only items LACKING canonical
            # follow-through are candidates.  This is the cross-watermark
            # half of the ONE-Door dedup: the idempotency key handles the
            # same-watermark re-run; this read handles every later one.
            item_ref = f"project_item:{item.get('id', '')}"
            if self._door_service is not None and self._door_service.has_item_for_source(item_ref):
                continue

            candidates.append(item)

        if not candidates:
            return None

        # Deterministic total order.
        def sort_key(item: dict[str, Any]) -> tuple:
            sev = (item.get("severity") or "").lower()
            sev_rank = _SEVERITY_RANK.get(sev, 999)
            due = item.get("due_at") or "\xff"  # nulls last
            item_id = item.get("id", "")
            return (sev_rank, due, item_id)

        candidates.sort(key=sort_key)
        return candidates[0]

    # ── VERIFY ────────────────────────────────────────────────────────

    def _phase_verify(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Write the run summary with verification receipts (STW-004, STW-011).

        Collects verification from ACT effect receipts and builds a
        summary that proves at least one real effect was performed.
        """
        observe_coverage = phase_results.get("observe", {}).get("coverage", {})
        compare_result = phase_results.get("compare", {})
        act_result = phase_results.get("act", {})

        actions_taken = act_result.get("actions_taken", 0)
        effect_receipts = act_result.get("effect_receipts", [])
        effects_skipped = act_result.get("effects_skipped", [])

        # STW-011: a run with real effects carries verification/receipt.
        verified_effects = [
            r for r in effect_receipts
            if r.get("outcome") == "applied"
        ]

        summary = {
            "source_count": len(observe_coverage) if isinstance(observe_coverage, dict) else 0,
            "review_id": compare_result.get("review_id", ""),
            "proposal_count": compare_result.get("proposal_count", 0),
            "actions_taken": actions_taken,
            "verified_effects": len(verified_effects),
            "effect_receipts": effect_receipts,
            "effects_skipped": effects_skipped,
            "has_real_effects": actions_taken > 0,
        }
        return summary

    # ── RECORD ────────────────────────────────────────────────────────

    def _phase_record(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Write the ledger event in one transaction with the final state.

        The revision law: state + ledger event in ONE transaction.
        """
        verify_summary = phase_results.get("verify", {})

        facts = {
            "run_id": run_id,
            "project_id": project_id,
            "source_count": verify_summary.get("source_count", 0),
            "review_id": verify_summary.get("review_id", ""),
            "proposal_count": verify_summary.get("proposal_count", 0),
            "actions_taken": verify_summary.get("actions_taken", 0),
            "verified_effects": verify_summary.get("verified_effects", 0),
            "has_real_effects": verify_summary.get("has_real_effects", False),
        }

        with self._db._connection() as conn:
            self._ledger.append_in_transaction(
                conn,
                principal,
                event_type="steward.run_completed",
                producer="ProjectStewardService",
                subject_ref=f"steward_run:{run_id}",
                source_revision="",
                facts=facts,
                refs=[f"project:{project_id}", f"steward_run:{run_id}"],
            )

        return {"event_recorded": True}

    # ── stop check ────────────────────────────────────────────────────

    def _check_stop(self, run_id: str) -> None:
        """Read the durable stop flag from the DB (STW-003).

        Never an in-memory flag alone, never dependent on a model response.
        """
        run = self._db.steward_runs.get_run(run_id)
        if run and run.get("state") == "stopping":
            raise StopRequested(f"Run {run_id} stop requested")

    # ── policy loading ────────────────────────────────────────────────

    def _load_policy(self, project_id: str) -> dict[str, Any]:
        """Load the steward policy for a project, or return defaults."""
        policy = self._db.steward_policies.get_policy_for_project(project_id)
        if policy is not None:
            return policy
        return {
            "eligible_effect_kinds_json": "[]",
            "yolo_flags_json": "{}",
            "max_retries": 3,
            "max_actions_per_run": 10,
            "cooldown_seconds": 0,
        }

    # ── idempotency key computation ──────────────────────────────────

    @staticmethod
    def _effect_idempotency_key(
        run_id: str,
        effect_kind: str,
        project_id: str,
        watermark: str,
    ) -> str:
        """Compute the idempotency key for an effect step.

        For most effects: run_id:effect_kind (unique per run, reconciles
        an in-run crash).  For create_door_item with a watermark: the
        watermark-scoped door key — a same-watermark re-run finds the
        completed step and reconciles to ZERO additional items (the
        charter's ONE-Door law).  Without a watermark there is no
        same-watermark contract, so the run-scoped key applies.
        """
        if effect_kind == "create_door_item" and watermark:
            return _door_idempotency_key(project_id, watermark)
        return f"{run_id}:{effect_kind}"

    @staticmethod
    def _compute_expected_state(
        effect_kind: str,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute expected state JSON before applying an effect (STW-004)."""
        if effect_kind == "refresh_sources":
            return {"effect": "refresh_sources", "project_id": project_id}
        elif effect_kind == "create_proposals":
            return {
                "effect": "create_proposals",
                "project_id": project_id,
                "prior_review_id": phase_results.get(
                    "compare", {},
                ).get("review_id", ""),
            }
        elif effect_kind == "apply_proposal_effects":
            proposals = phase_results.get("compare", {}).get("proposals", [])
            return {
                "effect": "apply_proposal_effects",
                "proposal_count": len(proposals),
            }
        elif effect_kind == "draft_update":
            return {"effect": "draft_update", "project_id": project_id}
        elif effect_kind == "create_door_item":
            return {"effect": "create_door_item", "project_id": project_id}
        return {"effect": effect_kind}


def _door_idempotency_key(project_id: str, watermark: str) -> str:
    """Compute the Door-effect idempotency key: ONE per (project, watermark).

    The key lives ON the act step, so the ordinary step-key reconcile in
    _phase_act catches every same-watermark re-run — ZERO additional Door
    items regardless of which item selection would pick (the glass-proven
    law: run 1's own effects may mint new candidates; the re-run must
    still create nothing).
    """
    material = f"{project_id}:{watermark}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:32]
    return f"door:{digest}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
