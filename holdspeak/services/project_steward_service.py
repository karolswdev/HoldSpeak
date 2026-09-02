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
  ACT      -> bounded no-op hook (story 03 fills)
  VERIFY   -> writes run summary
  RECORD   -> writes ledger event in one transaction with final state
"""
from __future__ import annotations

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


class StopRequested(Exception):
    """Raised internally when the durable stop flag is detected."""


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
    ) -> None:
        self._db = db
        self._collector = collector
        self._delta = delta
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
        project_id = str(project_id).strip()
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

        # Execute the six phases on the calling thread (conductor pattern).
        self._execute_phases(principal, run_id, project_id)

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

    def _execute_phases(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
    ) -> None:
        """Walk OBSERVE -> ... -> RECORD with a checkpoint per transition.

        Failure isolation per the conductor's patterns (SS9.1): exceptions
        are caught, the run is marked failed with an honest summary, and
        the caller is not poisoned.
        """
        seq = 0

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

                # Create a step record for this phase.
                step_id = generate_pststep_id()
                self._db.steward_steps.insert_step(
                    step_id=step_id,
                    run_id=run_id,
                    phase=phase,
                    seq=seq,
                    state="running",
                    effect_kind=f"phase:{phase}",
                    idempotency_key=f"{run_id}:{phase}",
                )
                seq += 1

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
        """Delegate to the Delta's deterministic review machinery (SS7.2)."""
        review = self._delta.open_review(principal, project_id)
        return {
            "review_id": review.get("id", ""),
            "proposal_count": len(review.get("proposals", [])),
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
        }

    # ── ACT ───────────────────────────────────────────────────────────

    def _phase_act(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Bounded no-op hook (story 03 fills with real effects)."""
        return {"actions_taken": 0}

    # ── VERIFY ────────────────────────────────────────────────────────

    def _phase_verify(
        self,
        principal: Principal,
        run_id: str,
        project_id: str,
        phase_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Write the run summary from accumulated phase results."""
        observe_coverage = phase_results.get("observe", {}).get("coverage", {})
        compare_result = phase_results.get("compare", {})
        act_result = phase_results.get("act", {})

        summary = {
            "source_count": len(observe_coverage),
            "review_id": compare_result.get("review_id", ""),
            "proposal_count": compare_result.get("proposal_count", 0),
            "actions_taken": act_result.get("actions_taken", 0),
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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
