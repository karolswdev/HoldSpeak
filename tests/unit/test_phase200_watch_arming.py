"""HS-200-43 (suite `phase200_watch_arming`): a watch becomes schedulable.

The audit's §3.2/§3.3. `list_due_watches` refuses a NULL
`next_evaluation_at`, and before this story the ONLY writer of that column
sat inside `evaluate_due` -- so a watch the scheduler had never evaluated
could never be selected by the scheduler (the owner's desk: 32 watches, 30
enabled, 2 armed). And `_match_and_record_effects` had exactly one caller,
inside `evaluate_due`, so a manual evaluation minted zero effects and could
never reach the steward (`watch_effects` on his desk: 0).

Every rule here is proven against the REAL producer and the REAL validator:
watches are created through `ProjectDoorService.create` and
`ProjectSetupService.finalize`, selection is asserted through the real
`db.automations.list_due_watches`, the backfill is driven through the real
`reconcile_schema` entry point (never the helper), and the steward reads
through the real `ProjectStewardService.run_due`.

R1 single scheduler   -> TestSingleScheduler
R2 quiet hours        -> TestQuietHoursHoldEvaluation
R3 arm on create/enable -> TestArmOnCreate, TestArmOnEnable
R4 backfill, ungated  -> TestBackfill
R5 manual effects     -> TestManualEvaluationRecordsEffects
"""
from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.watch_validation import ACTION_SCHEMA, CONDITION_SCHEMA

OWNER = Principal(PrincipalKind.OWNER, "test-200-43")


@pytest.fixture()
def db(tmp_path: Path) -> Any:
    return Database(tmp_path / "arming.db")


# ── Helpers ─────────────────────────────────────────────────────────


def _now_iso(offset_minutes: int = 0) -> str:
    return (
        datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)
    ).isoformat(timespec="seconds")


def _due_ids(db: Any, *, at_minutes: int = 0) -> list[str]:
    """The ids the REAL scheduler query would select."""
    return [w["id"] for w in db.automations.list_due_watches(_now_iso(at_minutes))]


def _pr(number: int = 1, checks: str = "pending") -> dict[str, Any]:
    return {
        "number": number, "state": "open", "title": f"PR {number}",
        "url": f"http://gh/{number}", "checks": checks, "headRefOid": "aaa",
    }


def _fetcher(*phases: list[dict[str, Any]]):
    """A snapshot fetcher walking successive phases (last one repeats)."""
    calls = [0]

    def fetch(principal, **kwargs):
        idx = min(calls[0], len(phases) - 1)
        calls[0] += 1
        return list(phases[idx])

    return fetch


class _FakeGitHubAdapter:
    """The adapter seam the Interview reads for candidate proposals."""

    def connection_status(self, principal):
        return {"state": "connected", "display": {"account": "test"}}

    def snapshot(self, principal, spec):
        return [_pr(1)]


def _watch_service(db: Any, fetcher: Any = None):
    from holdspeak.services.watch_service import WatchService
    return WatchService(db, snapshot_fetcher=fetcher)


def _seed_watch(
    db: Any,
    watch_id: str,
    *,
    state: str = "active",
    enabled: int = 1,
    snapshot_json: str | None = None,
    connector_id: str = "gh",
    project_id: str = "",
    next_evaluation_at: str | None = None,
) -> str:
    """Insert a raw connector_watches row (the shape already on disk)."""
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO connector_watches
               (id, connector_id, query_kind, name, state, enabled,
                snapshot_json, project_id, next_evaluation_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (watch_id, connector_id, "pull_requests", watch_id, state,
             enabled, snapshot_json, project_id, next_evaluation_at),
        )
    return watch_id


def _next_eval(db: Any, watch_id: str) -> str | None:
    with db._connection() as conn:
        row = conn.execute(
            "SELECT next_evaluation_at FROM connector_watches WHERE id=?",
            (watch_id,),
        ).fetchone()
    return row["next_evaluation_at"] if row else None


def _seed_project(db: Any, project_id: str | None = None) -> str:
    pid = project_id or f"proj-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO projects (id, name, created_at, updated_at) "
            "VALUES (?,?,datetime('now'),datetime('now'))",
            (pid, "Test Room"),
        )
    return pid


def _checks_changed_rule(db: Any, watch_id: str) -> str:
    """Set a real rule (through WatchService.set_rules) on the watch."""
    svc = _watch_service(db)
    result = svc.set_rules(OWNER, watch_id, [{
        "condition": {
            "schema": CONDITION_SCHEMA,
            "operator": "any",
            "clauses": [{"field": "checks", "comparison": "changed"}],
        },
        "actions": [
            {"schema": ACTION_SCHEMA, "kind": "project.steward.run_once"},
        ],
    }])
    return result["rules"][0]["id"]


def _effect_rows(db: Any) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM watch_effects ORDER BY id"
        )]


# ── R3: arm on create ───────────────────────────────────────────────


class TestArmOnCreate:
    """Every creation path leaves a row the scheduler can select."""

    def _door(self, db: Any):
        from holdspeak.services.project_door_service import ProjectDoorService
        from holdspeak.services.project_service import ProjectService

        ws = _watch_service(db, _fetcher([_pr(1)]))
        return ProjectDoorService(
            project_service=ProjectService(db),
            watch_service=ws,
        ), ws

    def test_door_created_watch_is_selectable_with_no_prior_run(
        self, db: Any,
    ) -> None:
        """AC-1a: through the REAL Door -> REAL list_due_watches."""
        door, _ws = self._door(db)

        door.create(
            OWNER,
            "Ship the release",
            [{"provider": "github", "scope": "acme/app",
              "watches": ["open_prs"]}],
        )

        watches = db.automations.list_watches()
        assert watches, "the Door created no watch"
        watch_id = watches[0]["id"]

        assert _next_eval(db, watch_id) is not None, (
            "the Door left the watch UNARMED -- list_due_watches refuses a NULL"
        )
        # The Door baselines right after create_from_setup commits, so the
        # watch is due NOW: its first evaluation diffs against a real
        # snapshot and can only report real change.
        assert watch_id in _due_ids(db), (
            "a Door-created watch must be selectable by the real scheduler "
            "query with no prior manual run"
        )

    def test_interview_created_watch_is_selectable_with_no_prior_run(
        self, db: Any,
    ) -> None:
        """AC-1b: through the REAL Interview (ProjectSetupService.finalize)."""
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_setup_service import ProjectSetupService

        ws = _watch_service(db, _fetcher([_pr(1)]))
        setup = ProjectSetupService(
            db,
            project_service=ProjectService(db),
            watch_service=ws,
            github_adapter=_FakeGitHubAdapter(),
        )

        session = setup.start_setup(OWNER)
        sid = session["id"]
        setup.answer(OWNER, sid, "outcome", {"text": "Ship the release"})
        setup.answer(OWNER, sid, "signals", {"text": "PRs and CI"})
        proposals = setup.suggest(OWNER, sid)
        assert proposals, "the Interview proposed nothing to activate"
        pid = proposals[0]["id"]
        setup.select_proposal(OWNER, sid, pid)
        setup.test_proposal(OWNER, sid, pid)
        result = setup.finalize(OWNER, sid)

        activated = result.get("activated_watches", [])
        assert activated, "finalize activated no watch"
        watch_id = activated[0]["watch_id"]

        assert _next_eval(db, watch_id) is not None, (
            "the Interview left the watch UNARMED"
        )
        assert watch_id in _due_ids(db)

    def test_ensure_meeting_watch_arms(self, db: Any) -> None:
        """The meeting Watch is born armed (no snapshot -> one cadence out)."""
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = f"mtg-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO meetings (id, title, started_at, capture_status) "
                "VALUES (?,?,?,'finalized')",
                (mid, "Standup", "2026-09-03T10:00:00"),
            )
            conn.execute(
                "INSERT INTO meeting_projects "
                "(meeting_id, project_id, source, confidence) "
                "VALUES (?,?,'auto',0.9)",
                (mid, project_id),
            )

        created = ensure_meeting_watch(db, project_id)
        assert created is not None
        watch_id = created["id"]

        assert _next_eval(db, watch_id) is not None, (
            "ensure_meeting_watch left the meeting Watch UNARMED"
        )
        # Due NOW. Safe because no caller ever baselines a meeting watch,
        # so its first evaluation is the silent one (F1) -- see
        # TestSilentFirstEvaluation.test_meeting_watch_first_run_is_silent.
        assert watch_id in _due_ids(db)

    def test_first_scheduled_run_on_an_armed_baselined_watch_is_silent(
        self, db: Any,
    ) -> None:
        """An armed watch WITH a real baseline sees ZERO transitions.

        The arming rule exists to keep this true: arming a snapshot-less
        watch to `now` would make its first scheduled run "discover" the
        whole source.
        """
        door, ws = self._door(db)
        door.create(
            OWNER,
            "Ship the release",
            [{"provider": "github", "scope": "acme/app",
              "watches": ["open_prs"]}],
        )
        watch_id = db.automations.list_watches()[0]["id"]
        assert db.automations.get_watch(watch_id).get("snapshot"), (
            "precondition: the Door must have established a real baseline"
        )

        outcomes = ws.evaluate_due(OWNER)

        assert [o["watch_id"] for o in outcomes] == [watch_id]
        assert sum(o.get("transitions", 0) for o in outcomes) == 0
        assert _effect_rows(db) == []


# ── R3: arm on enable, and never on pause/retire/disable ────────────


class TestArmOnEnable:

    def test_resume_arms_a_watch_paused_before_it_ever_ran(
        self, db: Any,
    ) -> None:
        """AC-2: resuming makes it schedulable again."""
        watch_id = _seed_watch(db, "w-resume", state="paused")
        svc = _watch_service(db)

        assert _next_eval(db, watch_id) is None
        svc.resume_watch(OWNER, watch_id)

        assert _next_eval(db, watch_id) is not None, (
            "resume left the watch unarmed -- it can never be selected"
        )

    def test_disabled_watch_is_never_selected(self, db: Any) -> None:
        """AC-2: disabling leaves no row the scheduler picks up.

        `list_due_watches` filters on `enabled = 1`, so the column is left
        as it is on disable -- this test is the proof the filter is real,
        not an assumption.
        """
        from holdspeak.services.reaction_service import ReactionService

        watch_id = _seed_watch(
            db, "w-toggle", state="active",
            next_evaluation_at=_now_iso(-5),
        )
        assert watch_id in _due_ids(db)

        ReactionService(db).set_watch_enabled(OWNER, watch_id, False)
        assert watch_id not in _due_ids(db), (
            "a disabled watch is still selectable by the scheduler"
        )

        # Re-enabling ARMS it (the legacy enable path, graduated row).
        # The column is cleared first so the assertion cannot pass on a
        # value the seed left behind.
        db.automations.update_watch_spec(watch_id, state="active")
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET next_evaluation_at=NULL "
                "WHERE id=?", (watch_id,),
            )
        ReactionService(db).set_watch_enabled(OWNER, watch_id, True)
        assert _next_eval(db, watch_id) is not None, (
            "enabling left the watch unarmed -- it can never be selected"
        )

    def test_enable_does_not_arm_a_legacy_row(self, db: Any) -> None:
        """A legacy (state='') watch stays owned by refresh_due_watches."""
        from holdspeak.services.reaction_service import ReactionService

        watch_id = _seed_watch(db, "w-legacy", state="", enabled=0)
        ReactionService(db).set_watch_enabled(OWNER, watch_id, True)

        assert _next_eval(db, watch_id) is None, (
            "enabling a legacy row armed it -- two schedulers on one row"
        )

    def test_paused_and_retired_are_never_selected(self, db: Any) -> None:
        """AC-5: arming respects the paused and retired states."""
        svc = _watch_service(db)
        paused = _seed_watch(
            db, "w-pause", state="active", next_evaluation_at=_now_iso(-5),
        )
        retired = _seed_watch(
            db, "w-retire", state="active", next_evaluation_at=_now_iso(-5),
        )
        assert set(_due_ids(db)) == {paused, retired}

        svc.pause_watch(OWNER, paused)
        svc.retire_watch(OWNER, retired)

        assert _due_ids(db) == []


# ── R4: the ungated backfill ────────────────────────────────────────


class TestBackfill:
    """Driven through the REAL reconcile entry point, never the helper.

    HS-200-10's B3 lesson: a helper shipped built, tested and uncalled.
    """

    def _reconcile(self, db: Any) -> None:
        from holdspeak.db.reconcile import reconcile_schema
        with db._connection() as conn:
            reconcile_schema(conn)

    def test_reconcile_schema_arms_unarmed_rows(self, db: Any) -> None:
        """AC-3: the wiring proof -- reconcile_schema(conn), not the helper."""
        bare = _seed_watch(db, "w-bare", state="active")
        based = _seed_watch(
            db, "w-based", state="active",
            snapshot_json='{"entities":{"1":{"number":1}}}',
        )
        assert _next_eval(db, bare) is None
        assert _next_eval(db, based) is None

        self._reconcile(db)

        assert _next_eval(db, bare) is not None
        assert _next_eval(db, based) is not None
        # HS-200-43 F1: BOTH are due now. Arming the snapshot-less row a
        # cadence out only postponed the discovery flood; the real fix is
        # that its first evaluation is silent.
        assert based in _due_ids(db)
        assert bare in _due_ids(db)

    def test_backfill_leaves_paused_retired_legacy_and_disabled_alone(
        self, db: Any,
    ) -> None:
        """AC-5: only enabled, graduated rows are armed."""
        paused = _seed_watch(db, "w-p", state="paused")
        retired = _seed_watch(db, "w-r", state="retired")
        legacy = _seed_watch(db, "w-l", state="")
        disabled = _seed_watch(db, "w-d", state="active", enabled=0)
        active = _seed_watch(db, "w-a", state="active")

        self._reconcile(db)

        for wid in (paused, retired, legacy, disabled):
            assert _next_eval(db, wid) is None, f"{wid} was armed and must not be"
        assert _next_eval(db, active) is not None

    def test_backfill_does_not_resurrect_a_meeting_watch_tombstone(
        self, db: Any,
    ) -> None:
        """AC-5: a retired meeting Watch is the owner's 'no' for that Room."""
        project_id = _seed_project(db)
        tomb = _seed_watch(
            db, "w-tomb", state="retired", connector_id="meeting",
            project_id=project_id,
        )

        self._reconcile(db)

        assert _next_eval(db, tomb) is None
        assert tomb not in _due_ids(db, at_minutes=10_000)

    def test_backfill_is_idempotent(self, db: Any) -> None:
        """A second reconcile matches nothing and moves no armed row."""
        from holdspeak.db.reconcile import _arm_unarmed_watches

        watch_id = _seed_watch(db, "w-idem", state="active")
        self._reconcile(db)
        first = _next_eval(db, watch_id)
        assert first is not None

        with db._connection() as conn:
            second_pass = _arm_unarmed_watches(conn)

        assert second_pass == 0, "the backfill re-armed an already-armed row"
        assert _next_eval(db, watch_id) == first


# ── R5: a manual evaluation records its effects ─────────────────────


class TestManualEvaluationRecordsEffects:

    def _armed_watch_with_rule(self, db: Any):
        """A real project-bound watch, baselined, with a real rule."""
        from holdspeak.services.project_door_service import ProjectDoorService
        from holdspeak.services.project_service import ProjectService

        ws = _watch_service(
            db, _fetcher([_pr(1, "pending")], [_pr(1, "success")]),
        )
        ProjectDoorService(
            project_service=ProjectService(db), watch_service=ws,
        ).create(
            OWNER, "Ship the release",
            [{"provider": "github", "scope": "acme/app",
              "watches": ["open_prs"]}],
        )
        watch_id = db.automations.list_watches()[0]["id"]
        rule_id = _checks_changed_rule(db, watch_id)
        return ws, watch_id, rule_id

    def test_manual_evaluation_mints_the_scheduled_idempotency_key(
        self, db: Any,
    ) -> None:
        """AC-4: evaluate_once records effects, keyed as a scheduled run is."""
        ws, watch_id, rule_id = self._armed_watch_with_rule(db)

        result = ws.evaluate_once(OWNER, watch_id)

        assert result["state"] == "completed"
        assert result["transitions"] == 1
        assert "_transitions" not in result, (
            "evaluate_once leaked the internal _transitions key its own "
            "docstring says is never serialised"
        )
        assert len(result.get("effects", [])) == 1

        rows = _effect_rows(db)
        assert len(rows) == 1, "a manual evaluation minted no watch_effects row"
        assert rows[0]["action_kind"] == "project.steward.run_once"
        assert rows[0]["state"] == "pending"
        # The key is derived from the EVALUATION, never from the trigger
        # kind -- which is what lets a scheduled pass dedupe against it.
        expected = hashlib.sha256(
            f"{result['evaluation_id']}:{rule_id}:project.steward.run_once"
            .encode("utf-8"),
        ).hexdigest()[:32]
        assert rows[0]["idempotency_key"] == expected

    def test_manual_then_scheduled_mint_exactly_one_effect(
        self, db: Any,
    ) -> None:
        """The same evaluation cannot mint twice."""
        ws, watch_id, _rule_id = self._armed_watch_with_rule(db)

        manual = ws.evaluate_once(OWNER, watch_id)
        assert len(_effect_rows(db)) == 1

        # Make it due again; the fetcher's last phase repeats, so the
        # scheduler sees the IDENTICAL source revision (a no_op).
        db.automations.update_watch_spec(
            watch_id, next_evaluation_at=_now_iso(-5),
        )
        outcomes = ws.evaluate_due(OWNER)

        assert outcomes and outcomes[0]["outcome"] == "evaluated"
        rows = _effect_rows(db)
        assert len(rows) == 1, (
            f"manual + scheduled minted {len(rows)} effects, expected exactly 1"
        )
        assert rows[0]["evaluation_id"] == manual["evaluation_id"]

    def test_steward_run_due_picks_up_a_manually_minted_effect(
        self, db: Any,
    ) -> None:
        """AC-4: the steward can act on it.

        `skipped_no_opt_in` IS the green: the owner's policies stay OFF,
        so reaching the opt-in gate is proof the effect was visible to
        `run_due` at all -- before this story `run_due` had nothing to read.
        """
        from holdspeak.services.project_delta_service import ProjectDeltaService
        from holdspeak.services.project_evidence_collector import (
            ProjectEvidenceCollector,
        )
        from holdspeak.services.project_steward_service import (
            ProjectStewardService,
        )

        ws, watch_id, _rule_id = self._armed_watch_with_rule(db)
        ws.evaluate_once(OWNER, watch_id)
        assert len(_effect_rows(db)) == 1

        collector = ProjectEvidenceCollector(db)
        steward = ProjectStewardService(
            db, collector, ProjectDeltaService(db, collector),
        )
        outcomes = steward.run_due(OWNER)

        assert len(outcomes) == 1, (
            "run_due saw no pending effect from the owner's own hand"
        )
        assert outcomes[0]["outcome"] == "skipped_no_opt_in", outcomes[0]


# ── R1: one scheduler ───────────────────────────────────────────────


class TestSingleScheduler:

    def test_workbench_conductor_does_not_call_evaluate_due(self) -> None:
        """AC-6: the conductor's watch block is gone at the SOURCE level.

        A source fence rather than a behavioural one because the fact
        being guarded is an absence: the heartbeat is the single
        scheduler, and a re-added conductor call would silently restore
        the double-scheduler race that made the quiet-hours promise false.
        """
        import holdspeak.workbench_conductor as wc

        source = Path(wc.__file__).read_text()
        calls = re.findall(r"evaluate_due\s*\(", source)
        assert calls == [], (
            f"workbench_conductor.py calls evaluate_due {len(calls)} time(s); "
            "the heartbeat is the single scheduler (HS-200-43 R1)"
        )
        # The seam itself stays -- steward.py and the MCP trigger read it.
        assert hasattr(wc, "set_scheduler_services")
        assert hasattr(wc, "get_scheduler_services")

    def test_heartbeat_prefers_the_app_wired_watch_service(self) -> None:
        """The single scheduler must run the fully-wired instance."""
        import holdspeak.workbench_conductor as wc
        from holdspeak.runtime.heartbeat import _sweep_watch_service

        sentinel = object()
        wc.set_scheduler_services(sentinel, None)
        try:
            assert _sweep_watch_service(None, None) is sentinel
        finally:
            wc.set_scheduler_services(None, None)


# ── R2: quiet hours hold the whole sweep ────────────────────────────


class TestQuietHoursHoldEvaluation:
    """Quiet hours hold EVALUATION, not only notification.

    Asserted against the real `WatchService` and the real
    `watch_evaluations` table -- a mock `evaluate_due` would prove only
    that a method was not called, not that no watch was evaluated.
    """

    def _rig(self, db: Any):
        from holdspeak.services.heartbeat_service import HeartbeatService

        watch_id = _seed_watch(
            db, "w-quiet", state="active", next_evaluation_at=_now_iso(-5),
        )
        ws = _watch_service(db, _fetcher([_pr(1)]))
        ws.baseline_watch(OWNER, watch_id)
        db.automations.update_watch_spec(
            watch_id, next_evaluation_at=_now_iso(-5),
        )
        assert watch_id in _due_ids(db)
        return HeartbeatService(db, watch_service=ws), watch_id

    def _evaluation_count(self, db: Any) -> int:
        with db._connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) AS c FROM watch_evaluations"
            ).fetchone()["c"]

    def test_due_watch_is_not_evaluated_during_quiet_hours(
        self, db: Any,
    ) -> None:
        hb, watch_id = self._rig(db)
        hour = datetime.now().hour
        hb.update_settings(
            {"quiet_hours": {"start": hour, "end": (hour + 2) % 24}},
        )
        assert hb.in_quiet_hours() is True

        receipt = hb.run_sweep(OWNER)

        assert receipt["held"] is True
        assert receipt["watches"] == 0
        assert self._evaluation_count(db) == 0, (
            "a watch was evaluated during quiet hours"
        )
        # Held, not consumed: the row is still due for the first sweep
        # after the window closes.
        assert watch_id in _due_ids(db)

    def test_due_watch_is_evaluated_outside_quiet_hours(
        self, db: Any,
    ) -> None:
        hb, watch_id = self._rig(db)
        hour = datetime.now().hour
        hb.update_settings(
            {"quiet_hours": {"start": (hour + 3) % 24,
                             "end": (hour + 5) % 24}},
        )
        assert hb.in_quiet_hours() is False

        receipt = hb.run_sweep(OWNER)

        assert receipt["held"] is False
        assert receipt["watches"] == 1
        assert self._evaluation_count(db) == 1


# ── F1: the first evaluation of an empty baseline is silent ─────────


class TestSilentFirstEvaluation:
    """Counsel's flood repro, ported.

    `diff_snapshots` emits a discovered event for every entity absent
    from the baseline, and evaluation reads `watch["snapshot"]` --
    never `baseline_state`. So an armed row with an empty baseline used
    to report its whole source as new. Counsel measured 30 entities ->
    30 transitions, 30 observations, 1 effect.
    """

    def _thirty_prs(self) -> list[dict[str, Any]]:
        old = (datetime.now(timezone.utc) - timedelta(days=400)).isoformat()
        return [
            {"number": i, "state": "open", "title": f"PR {i}",
             "url": f"http://gh/{i}", "checks": "success",
             "headRefOid": "aaa", "updated_at": old}
            for i in range(1, 31)
        ]

    def _older_than_rule(self, db: Any, watch_id: str) -> None:
        """A snapshot-level rule of the kind the Interview templates emit."""
        _watch_service(db).set_rules(OWNER, watch_id, [{
            "condition": {
                "schema": CONDITION_SCHEMA,
                "operator": "any",
                "clauses": [{"field": "updated_at",
                             "comparison": "older_than", "value": 1}],
            },
            "actions": [
                {"schema": ACTION_SCHEMA, "kind": "project.steward.run_once"},
            ],
        }])

    def _observation_count(self, db: Any) -> int:
        with db._connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) AS c FROM project_observations"
            ).fetchone()["c"]

    def test_thirty_entities_empty_baseline_evaluates_to_silence(
        self, db: Any,
    ) -> None:
        """The flood fence: 30 entities, no baseline -> `baselined`, 0 of everything."""
        project_id = _seed_project(db)
        # The shape the Door leaves behind when `baseline_watch` raises:
        # baseline_state='pending', snapshot NULL.
        watch_id = _seed_watch(
            db, "w-flood", state="active", project_id=project_id,
            next_evaluation_at=_now_iso(-5),
        )
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET baseline_state='pending' "
                "WHERE id=?", (watch_id,),
            )
        self._older_than_rule(db, watch_id)

        prs = self._thirty_prs()
        ws = _watch_service(db, _fetcher(prs))
        outcomes = ws.evaluate_due(OWNER)

        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "baselined", outcomes[0]
        assert outcomes[0]["transitions"] == 0
        assert outcomes[0]["observation_ids"] == []
        assert "effects" not in outcomes[0]
        assert self._observation_count(db) == 0, (
            "the first evaluation of an empty baseline discovered the "
            "whole source as new"
        )
        assert _effect_rows(db) == []

        # The baseline is now real, and bookkeeping advanced.
        watch = db.automations.get_watch(watch_id)
        assert watch["baseline_state"] == "established"
        assert len(watch["snapshot"].get("entities", {})) == 30
        assert watch_id not in _due_ids(db), (
            "the watch stayed due and would re-baseline every sweep"
        )

    def test_second_run_sees_exactly_the_one_new_entity(
        self, db: Any,
    ) -> None:
        """Silence is not blindness: the next run is a real diff."""
        project_id = _seed_project(db)
        watch_id = _seed_watch(
            db, "w-flood2", state="active", project_id=project_id,
            next_evaluation_at=_now_iso(-5),
        )
        self._older_than_rule(db, watch_id)

        prs = self._thirty_prs()
        newcomer = dict(prs[0])
        newcomer["number"] = 31
        newcomer["url"] = "http://gh/31"
        ws = _watch_service(db, _fetcher(prs, prs + [newcomer]))

        first = ws.evaluate_due(OWNER)
        assert first[0]["outcome"] == "baselined"

        db.automations.update_watch_spec(
            watch_id, next_evaluation_at=_now_iso(-5),
        )
        second = ws.evaluate_due(OWNER)

        assert second[0]["outcome"] == "evaluated"
        assert second[0]["transitions"] == 1, (
            f"expected exactly the one new PR, got {second[0]['transitions']}"
        )
        assert self._observation_count(db) == 1

    def _room_with_meetings(self, db: Any, count: int = 5) -> str:
        project_id = _seed_project(db)
        for i in range(count):
            mid = f"mtg-{uuid.uuid4().hex[:8]}"
            with db._connection() as conn:
                conn.execute(
                    "INSERT INTO meetings (id, title, started_at, "
                    "capture_status) VALUES (?,?,?,'finalized')",
                    (mid, f"Standup {i}", "2026-09-03T10:00:00"),
                )
                conn.execute(
                    "INSERT INTO meeting_projects (meeting_id, project_id, "
                    "source, confidence) VALUES (?,?,'auto',0.9)",
                    (mid, project_id),
                )
        return project_id

    def _meeting_fetcher(self, db: Any):
        """The REAL meeting source, bound to this test's Database.

        `evaluate_due`'s default path calls `fetch_watch_snapshot` with
        `meeting_db=None`, which resolves the process-global handle --
        a different file under an isolated HOME. Binding it here is a
        rig detail; the adapter and the query are the real ones.
        """
        from holdspeak.services.watch_sources import fetch_watch_snapshot

        def fetch(principal, *, connector_id, query_kind, query):
            return fetch_watch_snapshot(
                principal, connector_id=connector_id,
                query_kind=query_kind, query=query, meeting_db=db,
            )

        return fetch

    def test_meeting_watch_armed_now_does_not_flood(self, db: Any) -> None:
        """A Room must not discover the meetings it already has as new.

        `ensure_meeting_watch` baselines itself inline (`record_refresh`
        on the freshly built `MeetingWatchSource` snapshot), so on the
        happy path the row is armed AND baselined and its first
        scheduled run is an ordinary silent diff. This is the fence on
        arming it to `now`: through the real `ensure_meeting_watch` and
        the real meeting source, no stub fetcher.
        """
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = self._room_with_meetings(db)
        created = ensure_meeting_watch(db, project_id)
        assert created is not None
        watch_id = created["id"]
        assert watch_id in _due_ids(db), "precondition: armed and due now"
        assert len(
            db.automations.get_watch(watch_id)["snapshot"].get("entities", {})
        ) == 5, "precondition: ensure_meeting_watch baselined inline"

        outcomes = _watch_service(
            db, self._meeting_fetcher(db),
        ).evaluate_due(OWNER)

        assert len(outcomes) == 1
        assert outcomes[0]["transitions"] == 0, (
            "the Room discovered its already-linked meetings as new"
        )
        assert self._observation_count(db) == 0

    def test_meeting_watch_whose_inline_baseline_failed_is_silent(
        self, db: Any, monkeypatch,
    ) -> None:
        """The inline baseline is wrapped in a swallowing try/except.

        When the snapshot raises at creation, the row is left armed with
        an EMPTY baseline and `baseline_state` never reaches
        'established' -- the exact flood shape. The first evaluation
        must establish the baseline silently.
        """
        from holdspeak.services import watch_sources
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = self._room_with_meetings(db)

        def _boom(self, principal, **kwargs):
            raise RuntimeError("meeting source unavailable at creation")

        monkeypatch.setattr(
            watch_sources.MeetingWatchSource, "snapshot", _boom,
        )
        created = ensure_meeting_watch(db, project_id)
        monkeypatch.undo()

        assert created is not None
        watch_id = created["id"]
        assert not db.automations.get_watch(watch_id).get("snapshot"), (
            "precondition: the inline baseline was swallowed"
        )
        assert watch_id in _due_ids(db)

        outcomes = _watch_service(
            db, self._meeting_fetcher(db),
        ).evaluate_due(OWNER)

        assert outcomes[0]["outcome"] == "baselined", outcomes[0]
        assert outcomes[0]["transitions"] == 0
        assert self._observation_count(db) == 0
        assert len(
            db.automations.get_watch(watch_id)["snapshot"].get("entities", {})
        ) == 5

    def test_manual_evaluation_of_an_empty_baseline_is_also_silent(
        self, db: Any,
    ) -> None:
        """The branch lives in `_evaluate_core`, so both callers share it."""
        project_id = _seed_project(db)
        watch_id = _seed_watch(
            db, "w-flood3", state="active", project_id=project_id,
        )
        self._older_than_rule(db, watch_id)
        ws = _watch_service(db, _fetcher(self._thirty_prs()))

        result = ws.evaluate_once(OWNER, watch_id)

        assert result["state"] == "baselined"
        assert result["transitions"] == 0
        assert "_transitions" not in result
        assert self._observation_count(db) == 0
        assert _effect_rows(db) == []


# ── F2: the sweep is bounded ────────────────────────────────────────


class TestSweepIsBounded:

    def _seed_due(self, db: Any, count: int) -> list[str]:
        """`count` armed, baselined watches, oldest-due first by index."""
        ids = []
        for i in range(count):
            wid = _seed_watch(
                db, f"w-b{i:02d}", state="active",
                snapshot_json='{"entities":{},"fetched_at":"x"}',
                next_evaluation_at=_now_iso(-(count - i) - 1),
            )
            ids.append(wid)
        return ids

    def test_one_sweep_evaluates_the_bound_oldest_first(
        self, db: Any,
    ) -> None:
        from holdspeak.services.watch_service import WATCH_SWEEP_MAX

        ids = self._seed_due(db, 25)
        ws = _watch_service(db, _fetcher([]))

        first = ws.evaluate_due(OWNER)

        assert len(first) == WATCH_SWEEP_MAX == 10
        assert [o["watch_id"] for o in first] == ids[:10], (
            "the bound did not take the oldest-due first"
        )
        assert ws.last_sweep_deferred == 15

    def test_the_next_sweep_takes_the_next_ten(self, db: Any) -> None:
        """Nothing starves: the deferred rows are still the oldest."""
        ids = self._seed_due(db, 25)
        ws = _watch_service(db, _fetcher([]))

        ws.evaluate_due(OWNER)
        second = ws.evaluate_due(OWNER)

        assert [o["watch_id"] for o in second] == ids[10:20]
        assert ws.last_sweep_deferred == 5

    def test_limit_none_evaluates_everything(self, db: Any) -> None:
        """The manual trigger paths may want the lot."""
        self._seed_due(db, 25)
        ws = _watch_service(db, _fetcher([]))

        outcomes = ws.evaluate_due(OWNER, limit=None)

        assert len(outcomes) == 25
        assert ws.last_sweep_deferred == 0

    def test_sweep_receipt_reports_what_it_deferred(self, db: Any) -> None:
        """A desk with more watches than the bound must not look finished."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        self._seed_due(db, 25)
        ws = _watch_service(db, _fetcher([]))
        hb = HeartbeatService(db, watch_service=ws)
        hour = datetime.now().hour
        hb.update_settings(
            {"quiet_hours": {"start": (hour + 3) % 24,
                             "end": (hour + 5) % 24}},
        )

        receipt = hb.run_sweep(OWNER)

        assert receipt["watches"] == 10
        assert receipt["watches_deferred"] == 15


# ── F3: a remote runner holds the whole sweep ───────────────────────


class TestRemoteRunnerHoldsTheSweep:
    """Not live (the owner's runner is `local`), but fenced so it is not
    a surprise: since R1 the heartbeat is the ONLY scheduler, so a
    non-local `runs_on` stops local watch evaluation entirely.
    """

    def _rig(self, db: Any, runs_on: str):
        """One real heartbeat loop iteration with a real due watch."""
        import threading

        import holdspeak.db as hsdb
        import holdspeak.workbench_conductor as wc
        from holdspeak.runtime.heartbeat import HeartbeatMixin
        from holdspeak.services.heartbeat_service import HeartbeatService

        watch_id = _seed_watch(
            db, "w-remote", state="active",
            snapshot_json='{"entities":{},"fetched_at":"x"}',
            next_evaluation_at=_now_iso(-5),
        )
        assert watch_id in _due_ids(db)

        hb = HeartbeatService(db)
        hour = datetime.now().hour
        hb.update_settings({
            "runs_on": runs_on,
            "quiet_hours": {"start": (hour + 3) % 24, "end": (hour + 5) % 24},
        })

        class _OneTick(threading.Event):
            """Let the loop run its body exactly once, then stop it."""

            def __init__(self) -> None:
                super().__init__()
                self.checks = 0

            def is_set(self) -> bool:
                self.checks += 1
                return self.checks > 1

            def wait(self, timeout=None) -> bool:  # never actually sleep
                return False

        class _Runtime(HeartbeatMixin):
            def __init__(self, ev) -> None:
                self.runtime_stop_event = ev

        return watch_id, hb, _OneTick, _Runtime, hsdb, wc

    def _run_one_tick(self, db: Any, runs_on: str, monkeypatch) -> int:
        watch_id, _hb, OneTick, Runtime, hsdb, wc = self._rig(db, runs_on)
        monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
        wc.set_scheduler_services(_watch_service(db, _fetcher([])), None)
        try:
            Runtime(OneTick())._heartbeat_loop()
        finally:
            wc.set_scheduler_services(None, None)
        with db._connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) AS c FROM watch_evaluations"
            ).fetchone()["c"]

    def test_remote_runs_on_stops_local_watch_evaluation(
        self, db: Any, monkeypatch,
    ) -> None:
        assert self._run_one_tick(db, "holdspeak-43", monkeypatch) == 0, (
            "a remote runs_on did not hold the sweep"
        )

    def test_local_runs_on_evaluates(self, db: Any, monkeypatch) -> None:
        """The control: the same rig with `local` DOES evaluate."""
        assert self._run_one_tick(db, "local", monkeypatch) == 1


# ── F2 rider: the bound is for the UNATTENDED sweep only ────────────


class TestTheOwnersHandIsUnbounded:
    """`Run now` and the explicit trigger evaluate EVERYTHING.

    The `WATCH_SWEEP_MAX` bound protects the unattended heartbeat
    thread, where nobody is watching and the calendar refresh and the
    receipt are queued behind the fetches. When the owner presses a
    verb he is standing there, so his hand is exempt.
    """

    def _seed_due(self, db: Any, count: int = 25) -> list[str]:
        return [
            _seed_watch(
                db, f"w-h{i:02d}", state="active",
                snapshot_json='{"entities":{},"fetched_at":"x"}',
                next_evaluation_at=_now_iso(-(count - i) - 1),
            )
            for i in range(count)
        ]

    def test_mcp_steward_trigger_evaluates_every_due_watch(
        self, db: Any,
    ) -> None:
        """Through the REAL MCP dispatch for `project.steward.trigger`."""
        import holdspeak.workbench_conductor as wc
        from holdspeak.mcp.families.project import dispatch

        self._seed_due(db, 25)
        ws = _watch_service(db, _fetcher([]))
        wc.set_scheduler_services(ws, None)
        try:
            result = dispatch("project.steward.trigger", {}, OWNER)
        finally:
            wc.set_scheduler_services(None, None)

        assert result["success"] is True
        assert len(result["evaluate_outcomes"]) == 25, (
            "the owner's explicit trigger was bounded like the "
            "unattended sweep"
        )
        assert ws.last_sweep_deferred == 0

    def test_mcp_heartbeat_run_now_evaluates_every_due_watch(
        self, db: Any, monkeypatch,
    ) -> None:
        """Through the REAL MCP dispatch for `heartbeat.run_now`."""
        import holdspeak.mcp.families.heartbeat as hb_family

        self._seed_due(db, 25)
        monkeypatch.setattr(hb_family, "get_database", lambda *a, **k: db)
        monkeypatch.setattr(
            hb_family, "WatchService",
            lambda d, **kw: _watch_service(db, _fetcher([])),
        )
        hour = datetime.now().hour
        from holdspeak.services.heartbeat_service import HeartbeatService
        HeartbeatService(db).update_settings(
            {"quiet_hours": {"start": (hour + 3) % 24,
                             "end": (hour + 5) % 24}},
        )

        receipt = hb_family.dispatch("heartbeat.run_now", {}, OWNER)

        assert receipt["watches"] == 25, (
            "Run now was bounded like the unattended sweep"
        )
        assert receipt["watches_deferred"] == 0
        assert receipt["held"] is False
        assert receipt["quiet_overridden"] is False

    def test_the_scheduled_sweep_is_still_bounded(self, db: Any) -> None:
        """The control: the same 25 watches, the unattended path."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        self._seed_due(db, 25)
        ws = _watch_service(db, _fetcher([]))
        hb = HeartbeatService(db, watch_service=ws)
        hour = datetime.now().hour
        hb.update_settings(
            {"quiet_hours": {"start": (hour + 3) % 24,
                             "end": (hour + 5) % 24}},
        )

        receipt = hb.run_sweep(OWNER)

        assert receipt["watches"] == 10
        assert receipt["watches_deferred"] == 15


# ── P2-b: the owner's hand overrides quiet hours ────────────────────


class TestRunNowOverridesQuietHours:
    """`USER_GUIDE.md` has always promised Run now is "allowed during
    quiet hours" and ARCHITECTURE called it "the owner's override" --
    but `held` was computed unconditionally, so Run now at 23:00 did
    nothing and reported success.
    """

    def _rig(self, db: Any) -> str:
        from holdspeak.services.heartbeat_service import HeartbeatService

        watch_id = _seed_watch(
            db, "w-quiet-override", state="active",
            snapshot_json='{"entities":{},"fetched_at":"x"}',
            next_evaluation_at=_now_iso(-5),
        )
        assert watch_id in _due_ids(db)
        hour = datetime.now().hour
        HeartbeatService(db).update_settings(
            {"quiet_hours": {"start": hour, "end": (hour + 2) % 24}},
        )
        return watch_id

    def _evaluations(self, db: Any) -> int:
        with db._connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) AS c FROM watch_evaluations"
            ).fetchone()["c"]

    def test_mcp_run_now_evaluates_inside_quiet_hours(
        self, db: Any, monkeypatch,
    ) -> None:
        """Through the REAL `heartbeat.run_now` MCP dispatch."""
        import holdspeak.mcp.families.heartbeat as hb_family

        self._rig(db)
        monkeypatch.setattr(hb_family, "get_database", lambda *a, **k: db)
        monkeypatch.setattr(
            hb_family, "WatchService",
            lambda d, **kw: _watch_service(db, _fetcher([])),
        )

        receipt = hb_family.dispatch("heartbeat.run_now", {}, OWNER)

        assert receipt["held"] is False, (
            "Run now was held by quiet hours, contradicting the User Guide"
        )
        assert receipt["quiet_overridden"] is True
        assert receipt["watches"] == 1
        assert self._evaluations(db) == 1

    def test_scheduled_sweep_still_holds_inside_quiet_hours(
        self, db: Any,
    ) -> None:
        """The control: the unattended sweep is still held."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        self._rig(db)
        hb = HeartbeatService(
            db, watch_service=_watch_service(db, _fetcher([])),
        )

        receipt = hb.run_sweep(OWNER)

        assert receipt["held"] is True
        assert receipt["quiet_overridden"] is False
        assert receipt["watches"] == 0
        assert self._evaluations(db) == 0


# ── P2-a: a baselined watch is not a diffed evaluation ──────────────


class TestReceiptCountsBaselinedSeparately:

    def test_receipt_splits_baselined_from_evaluated(self, db: Any) -> None:
        """`watches` counts diffed evaluations only."""
        from holdspeak.services.heartbeat_service import HeartbeatService

        # Two with a real baseline, three with none.
        for i in range(2):
            _seed_watch(
                db, f"w-based{i}", state="active",
                snapshot_json='{"entities":{},"fetched_at":"x"}',
                next_evaluation_at=_now_iso(-9),
            )
        for i in range(3):
            _seed_watch(
                db, f"w-bare{i}", state="active",
                next_evaluation_at=_now_iso(-8),
            )

        hb = HeartbeatService(
            db, watch_service=_watch_service(db, _fetcher([])),
        )
        hour = datetime.now().hour
        hb.update_settings(
            {"quiet_hours": {"start": (hour + 3) % 24,
                             "end": (hour + 5) % 24}},
        )

        receipt = hb.run_sweep(OWNER)

        assert receipt["watches_baselined"] == 3
        assert receipt["watches"] == 2, (
            "a baselined watch diffed nothing and must not be counted as "
            "an evaluated one"
        )


# ── P2-g: a manual baseline still happened ──────────────────────────


class TestManualBaselineRecordsItRan:

    def test_manual_evaluation_that_baselines_sets_last_evaluated_at(
        self, db: Any,
    ) -> None:
        watch_id = _seed_watch(db, "w-manual-base", state="active")
        assert db.automations.get_watch(watch_id)["last_evaluated_at"] is None

        result = _watch_service(db, _fetcher([_pr(1)])).evaluate_once(
            OWNER, watch_id,
        )

        assert result["state"] == "baselined"
        watch = db.automations.get_watch(watch_id)
        assert watch["last_evaluated_at"] is not None, (
            "the face would show a watch the owner just evaluated as "
            "never evaluated"
        )
        assert watch["baseline_state"] == "established"


# ── P2-e: the two HTTP sites, through the real routes ───────────────


class TestOwnersHandOverHttp:
    """The MCP fences above prove the dispatch; these prove THE WIRE.

    Pattern borrowed from `tests/integration/test_provider_routes.py`:
    isolated DB, real FastAPI app, real router, TestClient, owner
    principal injected by middleware.
    """

    def _client(self, db: Any, ws: Any, router_builder: Any):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from starlette.middleware.base import BaseHTTPMiddleware

        from holdspeak.web.context import WebContext

        from holdspeak.services.credential_service import CredentialService

        # The settings router composes its secret routes at build time and
        # refuses without a real CredentialService -- supply one on this
        # test's own DB rather than weakening the composition check.
        ctx = WebContext(
            get_state=lambda: {},
            watch_service=ws,
            credential_service=CredentialService(db),
        )

        class _OwnerMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                request.state.principal = OWNER
                return await call_next(request)

        app = FastAPI()
        app.add_middleware(_OwnerMiddleware)
        app.include_router(router_builder(ctx))
        return TestClient(app)

    def _seed_due(self, db: Any, count: int = 25) -> None:
        for i in range(count):
            _seed_watch(
                db, f"w-http{i:02d}", state="active",
                snapshot_json='{"entities":{},"fetched_at":"x"}',
                next_evaluation_at=_now_iso(-(count - i) - 1),
            )

    def test_steward_trigger_route_evaluates_every_due_watch(
        self, db: Any,
    ) -> None:
        """POST /api/steward/trigger -- 25 due, 25 evaluated ON THE WIRE."""
        import holdspeak.workbench_conductor as wc
        from holdspeak.web.routes import build_steward_router

        self._seed_due(db, 25)
        ws = _watch_service(db, _fetcher([]))
        client = self._client(db, ws, build_steward_router)

        wc.set_scheduler_services(ws, None)
        try:
            resp = client.post("/api/steward/trigger")
        finally:
            wc.set_scheduler_services(None, None)

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert len(body["evaluate_outcomes"]) == 25, (
            "the owner's explicit trigger was bounded on the wire"
        )

    def test_run_now_route_evaluates_every_due_watch(
        self, db: Any, monkeypatch,
    ) -> None:
        """POST /api/settings/heartbeat/run-now -- 25 due, 25 on the wire."""
        import holdspeak.db as hsdb
        from holdspeak.services.heartbeat_service import HeartbeatService
        from holdspeak.web.routes.system.settings import build_settings_router

        self._seed_due(db, 25)
        hour = datetime.now().hour
        HeartbeatService(db).update_settings(
            {"quiet_hours": {"start": (hour + 3) % 24,
                             "end": (hour + 5) % 24}},
        )
        # The route resolves its own handles; point them at this DB and
        # give it the fetcher a bare WatchService would not carry.
        monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
        import holdspeak.services.watch_service as ws_mod
        real_ctor = ws_mod.WatchService
        monkeypatch.setattr(
            ws_mod, "WatchService",
            lambda d, **kw: real_ctor(db, snapshot_fetcher=_fetcher([])),
        )

        ws = _watch_service(db, _fetcher([]))
        client = self._client(db, ws, build_settings_router)
        resp = client.post("/api/settings/heartbeat/run-now")

        assert resp.status_code == 200, resp.text
        receipt = resp.json()
        assert receipt["watches"] == 25, (
            "Run now was bounded on the wire"
        )
        assert receipt["watches_deferred"] == 0
