"""HS-164-02: evaluate_due — watches evaluate themselves, safely.

Tests:
- Due selection truth table: cadence honored, not-due skipped, bookkeeping
  advances transactionally (last_evaluated_at + next_evaluation_at ride the
  same transaction as the evaluation row).
- Per-watch isolation: one broken watch isolates, others still evaluate,
  failure is a recorded outcome, nothing raises out of evaluate_due.
- Circuit lifecycle: opens after CIRCUIT_FAILURE_THRESHOLD consecutive
  failures, refuses evaluation with skipped_circuit_open while the
  cooldown window is active, half-opens after the window, and closes
  on success.
- Manual-override: evaluate_once on a circuit-open watch ALWAYS runs
  (the owner's hand overrides); only the scheduler respects the circuit.
- Transactional bookkeeping: last_evaluated_at and next_evaluation_at
  are written inside the same transaction as the evaluation row.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.reaction_service import ReactionService
from holdspeak.services.watch_service import (
    CIRCUIT_COOLDOWN_SECONDS,
    CIRCUIT_FAILURE_THRESHOLD,
    WatchService,
)

OWNER = Principal(PrincipalKind.OWNER, "test-evaluate-due-owner")


# ── Helpers ──────────────────────────────────────────────────────────


def _make_watch(
    db: Database,
    watch_id: str = "watch-due-01",
    **kwargs: Any,
) -> dict[str, Any]:
    """Create a watch via ReactionService (the legacy creator)."""
    svc = ReactionService(db)
    return svc.create_watch(
        OWNER,
        connector_id=kwargs.get("connector_id", "gh"),
        query_kind=kwargs.get("query_kind", "pull_requests"),
        name=kwargs.get("name", "Due watch"),
        query=kwargs.get("query", {"repository": "acme/app"}),
        watch_id=watch_id,
    )


def _graduate_watch(
    db: Database,
    watch_id: str,
    *,
    state: str = "active",
    cadence_minutes: int = 60,
    next_evaluation_at: str | None = None,
) -> None:
    """Graduate a watch to a WatchSpec@1 evaluable state."""
    db.automations.update_watch_spec(
        watch_id,
        state=state,
        schema_version="WatchSpec@1",
        evaluation_cadence_minutes=cadence_minutes,
        next_evaluation_at=next_evaluation_at,
    )


def _watch_svc(
    db: Database,
    fetcher: Any = None,
) -> WatchService:
    return WatchService(db, snapshot_fetcher=fetcher)


def _baseline_fetcher(entities: list[dict[str, Any]]):
    """Return a fetcher that always returns the given entities."""
    def fetcher(principal, **kwargs):
        return list(entities)
    return fetcher


def _counting_fetcher(phases: list[list[dict[str, Any]]]):
    """Return a fetcher that returns successive snapshot phases."""
    call_count = [0]
    def fetcher(principal, **kwargs):
        idx = min(call_count[0], len(phases) - 1)
        call_count[0] += 1
        return list(phases[idx])
    return fetcher


def _failing_fetcher(error_msg: str = "provider unavailable"):
    """Return a fetcher that always raises."""
    def fetcher(principal, **kwargs):
        raise RuntimeError(error_msg)
    return fetcher


def _selective_fetcher(
    fail_watches: set[str],
    entities: list[dict[str, Any]],
):
    """Return a fetcher that fails for specific watches, succeeds for others."""
    def fetcher(principal, *, connector_id="", query_kind="", query=None):
        repo = (query or {}).get("repository", "")
        # Use repository name to identify which watch this is for.
        if repo in fail_watches:
            raise RuntimeError(f"provider unavailable for {repo}")
        return list(entities)
    return fetcher


def _past_iso(minutes_ago: int) -> str:
    """ISO timestamp ``minutes_ago`` minutes in the past."""
    dt = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return dt.isoformat(timespec="seconds")


def _future_iso(minutes_ahead: int) -> str:
    """ISO timestamp ``minutes_ahead`` minutes in the future."""
    dt = datetime.now(timezone.utc) + timedelta(minutes=minutes_ahead)
    return dt.isoformat(timespec="seconds")


# ── Due selection truth table ────────────────────────────────────────


class TestDueSelection:
    """Cadence honored, not-due skipped, boundary filters correct."""

    def test_due_watch_evaluates(self, tmp_path) -> None:
        """A watch with next_evaluation_at in the past is due."""
        db = Database(tmp_path / "due.db")
        _make_watch(db, "w-due")
        _graduate_watch(db, "w-due", cadence_minutes=60,
                        next_evaluation_at=_past_iso(5))
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        # Baseline first so diff is clean.
        svc.baseline_watch(OWNER, "w-due")
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 1
        assert outcomes[0]["watch_id"] == "w-due"
        assert outcomes[0]["outcome"] == "evaluated"

    def test_not_due_watch_skipped(self, tmp_path) -> None:
        """A watch with next_evaluation_at in the future is NOT due."""
        db = Database(tmp_path / "notdue.db")
        _make_watch(db, "w-future")
        _graduate_watch(db, "w-future", cadence_minutes=60,
                        next_evaluation_at=_future_iso(30))
        svc = _watch_svc(db, fetcher=_baseline_fetcher([]))
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 0

    def test_legacy_watch_not_selected(self, tmp_path) -> None:
        """A legacy watch (state='') is never selected by evaluate_due."""
        db = Database(tmp_path / "legacy.db")
        _make_watch(db, "w-legacy")
        # Set next_evaluation_at but leave state empty (legacy).
        db.automations.update_watch_spec(
            "w-legacy",
            next_evaluation_at=_past_iso(5),
        )
        svc = _watch_svc(db, fetcher=_baseline_fetcher([]))
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 0

    def test_paused_watch_not_selected(self, tmp_path) -> None:
        """A paused graduated watch is not evaluable."""
        db = Database(tmp_path / "paused.db")
        _make_watch(db, "w-paused")
        _graduate_watch(db, "w-paused", state="paused",
                        next_evaluation_at=_past_iso(5))
        svc = _watch_svc(db, fetcher=_baseline_fetcher([]))
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 0

    def test_retired_watch_not_selected(self, tmp_path) -> None:
        """A retired watch is not evaluable."""
        db = Database(tmp_path / "retired.db")
        _make_watch(db, "w-retired")
        _graduate_watch(db, "w-retired", state="retired",
                        next_evaluation_at=_past_iso(5))
        svc = _watch_svc(db, fetcher=_baseline_fetcher([]))
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 0

    def test_disabled_watch_not_selected(self, tmp_path) -> None:
        """An enabled=0 watch is not due regardless of state/timestamps."""
        db = Database(tmp_path / "disabled.db")
        _make_watch(db, "w-disabled")
        _graduate_watch(db, "w-disabled",
                        next_evaluation_at=_past_iso(5))
        db.automations.set_watch_enabled("w-disabled", False)
        svc = _watch_svc(db, fetcher=_baseline_fetcher([]))
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 0

    def test_null_next_evaluation_not_selected(self, tmp_path) -> None:
        """A watch with NULL next_evaluation_at is never due."""
        db = Database(tmp_path / "null-next.db")
        _make_watch(db, "w-null")
        _graduate_watch(db, "w-null", next_evaluation_at=None)
        svc = _watch_svc(db, fetcher=_baseline_fetcher([]))
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 0

    def test_tested_state_is_evaluable(self, tmp_path) -> None:
        """A watch in 'tested' state is eligible for scheduled evaluation."""
        db = Database(tmp_path / "tested.db")
        _make_watch(db, "w-tested")
        _graduate_watch(db, "w-tested", state="tested",
                        next_evaluation_at=_past_iso(5))
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc.baseline_watch(OWNER, "w-tested")
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "evaluated"


# ── Transactional bookkeeping ────────────────────────────────────────


class TestTransactionalBookkeeping:
    """last_evaluated_at + next_evaluation_at ride the evaluation txn."""

    def test_bookkeeping_advances_on_success(self, tmp_path) -> None:
        """After evaluate_due, last_evaluated_at and next_evaluation_at
        are updated to now and now+cadence."""
        db = Database(tmp_path / "bk-advance.db")
        _make_watch(db, "w-bk")
        _graduate_watch(db, "w-bk", cadence_minutes=30,
                        next_evaluation_at=_past_iso(5))
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc.baseline_watch(OWNER, "w-bk")

        before = datetime.now(timezone.utc).replace(microsecond=0)
        svc.evaluate_due(OWNER)
        after = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=1)

        watch = db.automations.get_watch("w-bk")
        assert watch is not None
        last_eval = datetime.fromisoformat(watch["last_evaluated_at"])
        next_eval = datetime.fromisoformat(watch["next_evaluation_at"])
        if last_eval.tzinfo is None:
            last_eval = last_eval.replace(tzinfo=timezone.utc)
        if next_eval.tzinfo is None:
            next_eval = next_eval.replace(tzinfo=timezone.utc)

        # last_evaluated_at should be between before and after
        # (truncated to seconds to match stored ISO precision).
        assert before <= last_eval <= after
        # next_evaluation_at should be ~30 minutes after last_evaluated_at.
        expected_next = last_eval + timedelta(minutes=30)
        delta = abs((next_eval - expected_next).total_seconds())
        assert delta < 2, f"next_evaluation_at off by {delta}s"

    def test_bookkeeping_advances_on_failure(self, tmp_path) -> None:
        """Even on failure, bookkeeping advances so the watch is not
        retried immediately."""
        db = Database(tmp_path / "bk-fail.db")
        _make_watch(db, "w-fail")
        _graduate_watch(db, "w-fail", cadence_minutes=45,
                        next_evaluation_at=_past_iso(5))
        svc = _watch_svc(db, fetcher=_failing_fetcher())

        before = datetime.now(timezone.utc).replace(microsecond=0)
        outcomes = svc.evaluate_due(OWNER)
        after = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=1)

        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "failed"

        watch = db.automations.get_watch("w-fail")
        assert watch is not None
        last_eval = datetime.fromisoformat(watch["last_evaluated_at"])
        next_eval = datetime.fromisoformat(watch["next_evaluation_at"])
        if last_eval.tzinfo is None:
            last_eval = last_eval.replace(tzinfo=timezone.utc)
        if next_eval.tzinfo is None:
            next_eval = next_eval.replace(tzinfo=timezone.utc)

        assert before <= last_eval <= after
        expected_next = last_eval + timedelta(minutes=45)
        delta = abs((next_eval - expected_next).total_seconds())
        assert delta < 2

    def test_circuit_resets_on_success(self, tmp_path) -> None:
        """A successful evaluation resets the circuit to closed, streak=0."""
        db = Database(tmp_path / "circuit-reset.db")
        _make_watch(db, "w-reset")
        _graduate_watch(db, "w-reset", cadence_minutes=60,
                        next_evaluation_at=_past_iso(5))
        # Pre-set some failure streak (below threshold).
        db.automations.update_watch_circuit(
            "w-reset",
            circuit_state="closed",
            circuit_failure_streak=2,
        )
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc.baseline_watch(OWNER, "w-reset")
        svc.evaluate_due(OWNER)

        circuit = db.automations.get_watch_circuit("w-reset")
        assert circuit is not None
        assert circuit["circuit_state"] == "closed"
        assert circuit["circuit_failure_streak"] == 0
        assert circuit["circuit_opened_at"] is None


# ── Per-watch isolation ──────────────────────────────────────────────


class TestIsolation:
    """One broken watch isolates; others still evaluate; never raises."""

    def test_one_failure_does_not_block_others(self, tmp_path) -> None:
        """If watch A fails and watch B succeeds, both get outcomes."""
        db = Database(tmp_path / "isolation.db")
        _make_watch(db, "w-good", query={"repository": "acme/good"})
        _make_watch(db, "w-bad", query={"repository": "acme/bad"})
        _graduate_watch(db, "w-good",
                        next_evaluation_at=_past_iso(5))
        _graduate_watch(db, "w-bad",
                        next_evaluation_at=_past_iso(5))

        good_entities = [{"number": 1, "state": "open", "title": "PR",
                          "url": "http://gh/1", "checks": "success",
                          "headRefOid": "aaa"}]

        fetcher = _selective_fetcher({"acme/bad"}, good_entities)
        svc = _watch_svc(db, fetcher=fetcher)
        # Baseline the good watch.
        svc.baseline_watch(OWNER, "w-good")

        outcomes = svc.evaluate_due(OWNER)

        by_id = {o["watch_id"]: o for o in outcomes}
        assert len(outcomes) == 2
        assert by_id["w-good"]["outcome"] == "evaluated"
        assert by_id["w-bad"]["outcome"] == "failed"
        assert "error" in by_id["w-bad"]

    def test_evaluate_due_never_raises(self, tmp_path) -> None:
        """Even if every watch fails, evaluate_due returns outcomes,
        never raises."""
        db = Database(tmp_path / "all-fail.db")
        _make_watch(db, "w-f1", query={"repository": "acme/f1"})
        _make_watch(db, "w-f2", query={"repository": "acme/f2"})
        _graduate_watch(db, "w-f1",
                        next_evaluation_at=_past_iso(5))
        _graduate_watch(db, "w-f2",
                        next_evaluation_at=_past_iso(5))

        svc = _watch_svc(db, fetcher=_failing_fetcher())
        # Must not raise.
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 2
        assert all(o["outcome"] == "failed" for o in outcomes)

    def test_failure_records_error_string(self, tmp_path) -> None:
        """The failure outcome includes the error message."""
        db = Database(tmp_path / "error-str.db")
        _make_watch(db, "w-err")
        _graduate_watch(db, "w-err",
                        next_evaluation_at=_past_iso(5))
        svc = _watch_svc(db, fetcher=_failing_fetcher("specific error"))
        outcomes = svc.evaluate_due(OWNER)
        assert outcomes[0]["outcome"] == "failed"
        assert "specific error" in outcomes[0]["error"]


# ── Circuit lifecycle ────────────────────────────────────────────────


class TestCircuitLifecycle:
    """Open after threshold, refuse while open, half-open after window,
    close on success."""

    def test_circuit_opens_after_threshold(self, tmp_path) -> None:
        """After CIRCUIT_FAILURE_THRESHOLD consecutive failures the
        circuit opens."""
        db = Database(tmp_path / "circuit-open.db")
        _make_watch(db, "w-circuit")
        _graduate_watch(db, "w-circuit", cadence_minutes=1,
                        next_evaluation_at=_past_iso(5))
        svc = _watch_svc(db, fetcher=_failing_fetcher())

        for i in range(CIRCUIT_FAILURE_THRESHOLD):
            # Re-set next_evaluation_at to keep the watch due.
            db.automations.update_watch_spec(
                "w-circuit",
                next_evaluation_at=_past_iso(5),
            )
            outcomes = svc.evaluate_due(OWNER)
            assert len(outcomes) == 1
            assert outcomes[0]["outcome"] == "failed"

        circuit = db.automations.get_watch_circuit("w-circuit")
        assert circuit is not None
        assert circuit["circuit_state"] == "open"
        assert circuit["circuit_failure_streak"] == CIRCUIT_FAILURE_THRESHOLD
        assert circuit["circuit_opened_at"] is not None

    def test_circuit_open_skips_evaluation(self, tmp_path) -> None:
        """While the circuit is open and cooldown has not elapsed,
        evaluation is skipped with an honest outcome."""
        db = Database(tmp_path / "circuit-skip.db")
        _make_watch(db, "w-skip")
        _graduate_watch(db, "w-skip", cadence_minutes=1,
                        next_evaluation_at=_past_iso(5))
        # Pre-open the circuit with a recent opened_at.
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.automations.update_watch_circuit(
            "w-skip",
            circuit_state="open",
            circuit_failure_streak=CIRCUIT_FAILURE_THRESHOLD,
            circuit_opened_at=now_iso,
        )
        svc = _watch_svc(db, fetcher=_baseline_fetcher([]))
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "skipped_circuit_open"
        assert outcomes[0]["circuit_state"] == "open"

    def test_half_open_probe_on_cooldown_elapsed(self, tmp_path) -> None:
        """After cooldown elapses, ONE probe is allowed and reported
        as probe_half_open."""
        db = Database(tmp_path / "half-open.db")
        _make_watch(db, "w-probe")
        _graduate_watch(db, "w-probe", cadence_minutes=60,
                        next_evaluation_at=_past_iso(5))
        # Set circuit open with opened_at far enough in the past.
        old_opened = (
            datetime.now(timezone.utc)
            - timedelta(seconds=CIRCUIT_COOLDOWN_SECONDS + 60)
        ).isoformat(timespec="seconds")
        db.automations.update_watch_circuit(
            "w-probe",
            circuit_state="open",
            circuit_failure_streak=CIRCUIT_FAILURE_THRESHOLD,
            circuit_opened_at=old_opened,
        )
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc.baseline_watch(OWNER, "w-probe")
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "probe_half_open"
        # After successful probe, circuit is closed.
        circuit = db.automations.get_watch_circuit("w-probe")
        assert circuit is not None
        assert circuit["circuit_state"] == "closed"
        assert circuit["circuit_failure_streak"] == 0

    def test_half_open_probe_failure_reopens(self, tmp_path) -> None:
        """A failed half-open probe re-opens the circuit with a fresh
        opened_at and incremented streak."""
        db = Database(tmp_path / "probe-fail.db")
        _make_watch(db, "w-pfail")
        _graduate_watch(db, "w-pfail", cadence_minutes=60,
                        next_evaluation_at=_past_iso(5))
        old_opened = (
            datetime.now(timezone.utc)
            - timedelta(seconds=CIRCUIT_COOLDOWN_SECONDS + 60)
        ).isoformat(timespec="seconds")
        db.automations.update_watch_circuit(
            "w-pfail",
            circuit_state="open",
            circuit_failure_streak=CIRCUIT_FAILURE_THRESHOLD,
            circuit_opened_at=old_opened,
        )
        svc = _watch_svc(db, fetcher=_failing_fetcher())
        outcomes = svc.evaluate_due(OWNER)
        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "failed"
        # Circuit re-opened with fresh opened_at.
        circuit = db.automations.get_watch_circuit("w-pfail")
        assert circuit is not None
        assert circuit["circuit_state"] == "open"
        assert circuit["circuit_failure_streak"] == CIRCUIT_FAILURE_THRESHOLD + 1
        # opened_at should be recent (not the old one).
        opened = datetime.fromisoformat(circuit["circuit_opened_at"])
        if opened.tzinfo is None:
            opened = opened.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - opened).total_seconds()
        assert age < 10, f"opened_at should be fresh, but is {age}s old"

    def test_success_after_failures_closes_circuit(self, tmp_path) -> None:
        """Success after consecutive failures (below threshold) resets
        the streak to 0 and keeps the circuit closed."""
        db = Database(tmp_path / "reset.db")
        _make_watch(db, "w-rst")
        _graduate_watch(db, "w-rst", cadence_minutes=1,
                        next_evaluation_at=_past_iso(5))
        svc_fail = _watch_svc(db, fetcher=_failing_fetcher())

        # Accumulate failures below threshold.
        for _ in range(CIRCUIT_FAILURE_THRESHOLD - 1):
            db.automations.update_watch_spec(
                "w-rst", next_evaluation_at=_past_iso(5),
            )
            svc_fail.evaluate_due(OWNER)

        circuit = db.automations.get_watch_circuit("w-rst")
        assert circuit["circuit_state"] == "closed"
        assert circuit["circuit_failure_streak"] == CIRCUIT_FAILURE_THRESHOLD - 1

        # Now succeed.
        db.automations.update_watch_spec(
            "w-rst", next_evaluation_at=_past_iso(5),
        )
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc_ok = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc_ok.baseline_watch(OWNER, "w-rst")
        outcomes = svc_ok.evaluate_due(OWNER)
        assert outcomes[0]["outcome"] == "evaluated"
        circuit = db.automations.get_watch_circuit("w-rst")
        assert circuit["circuit_state"] == "closed"
        assert circuit["circuit_failure_streak"] == 0


# ── Manual override ──────────────────────────────────────────────────


class TestManualOverride:
    """evaluate_once IGNORES circuit state; only the scheduler respects it."""

    def test_evaluate_once_runs_on_circuit_open(self, tmp_path) -> None:
        """Manual evaluate_once succeeds even when the circuit is open."""
        db = Database(tmp_path / "manual-override.db")
        _make_watch(db, "w-manual")
        _graduate_watch(db, "w-manual", cadence_minutes=60,
                        next_evaluation_at=_past_iso(5))
        # Open the circuit.
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.automations.update_watch_circuit(
            "w-manual",
            circuit_state="open",
            circuit_failure_streak=CIRCUIT_FAILURE_THRESHOLD,
            circuit_opened_at=now_iso,
        )
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc.baseline_watch(OWNER, "w-manual")

        # Manual evaluation: MUST succeed (owner's hand overrides).
        result = svc.evaluate_once(OWNER, "w-manual")
        assert result["state"] == "completed"

    def test_scheduler_skips_but_manual_runs(self, tmp_path) -> None:
        """The scheduler skips a circuit-open watch, but manual runs it
        in the same session."""
        db = Database(tmp_path / "dual.db")
        _make_watch(db, "w-dual")
        _graduate_watch(db, "w-dual", cadence_minutes=60,
                        next_evaluation_at=_past_iso(5))
        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        db.automations.update_watch_circuit(
            "w-dual",
            circuit_state="open",
            circuit_failure_streak=CIRCUIT_FAILURE_THRESHOLD,
            circuit_opened_at=now_iso,
        )
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc.baseline_watch(OWNER, "w-dual")

        # Scheduler: skips.
        due_outcomes = svc.evaluate_due(OWNER)
        assert len(due_outcomes) == 1
        assert due_outcomes[0]["outcome"] == "skipped_circuit_open"

        # Manual: runs.
        result = svc.evaluate_once(OWNER, "w-dual")
        assert result["state"] == "completed"


# ── Trigger kind traceability ────────────────────────────────────────


class TestTriggerKind:
    """evaluate_due writes trigger_kind='scheduled' on the evaluation row;
    evaluate_once writes 'manual'."""

    def test_scheduled_trigger_kind(self, tmp_path) -> None:
        db = Database(tmp_path / "trigger-sched.db")
        _make_watch(db, "w-tk")
        _graduate_watch(db, "w-tk", cadence_minutes=60,
                        next_evaluation_at=_past_iso(5))
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc.baseline_watch(OWNER, "w-tk")
        outcomes = svc.evaluate_due(OWNER)
        eval_id = outcomes[0]["evaluation_id"]
        # Read the evaluation row.
        with db._connection() as conn:
            row = conn.execute(
                "SELECT trigger_kind FROM watch_evaluations WHERE id=?",
                (eval_id,),
            ).fetchone()
        assert row is not None
        assert row[0] == "scheduled"

    def test_manual_trigger_kind(self, tmp_path) -> None:
        db = Database(tmp_path / "trigger-manual.db")
        _make_watch(db, "w-tm")
        _graduate_watch(db, "w-tm", cadence_minutes=60)
        entities = [{"number": 1, "state": "open", "title": "PR",
                     "url": "http://gh/1", "checks": "success",
                     "headRefOid": "aaa"}]
        svc = _watch_svc(db, fetcher=_baseline_fetcher(entities))
        svc.baseline_watch(OWNER, "w-tm")
        result = svc.evaluate_once(OWNER, "w-tm")
        eval_id = result["evaluation_id"]
        with db._connection() as conn:
            row = conn.execute(
                "SELECT trigger_kind FROM watch_evaluations WHERE id=?",
                (eval_id,),
            ).fetchone()
        assert row is not None
        assert row[0] == "manual"
