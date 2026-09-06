"""HS-164-03: run_due — the triggered hand, one run per watermark.

Tests:
- TST-RD-001: Happy path — pending effect triggers a run, effect resolved.
- TST-RD-002: Same-watermark dedup — repeated requests resolve to ONE run.
- TST-RD-003: No opt-in skip — unattended_enabled=0 produces honest skip.
- TST-RD-004: Cooldown gates unattended runs at this layer.
- TST-RD-005: Disabled policy skip (separate from no-opt-in).
- TST-RD-006: STW-002 absorbed as resolution, never error.
- TST-RD-007: Deterministic watermark — same evaluation yields same watermark.
- TST-RD-008: run_due NEVER raises, even with corrupt effects.
- TST-RD-009: Manual insert_run/run_once byte-identical (no unattended gates).
- TST-RD-010: No project binding skip.
- TST-RD-011: Replay idempotency — re-draining same effect is no-op.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import pytest

from holdspeak.db.schema import SCHEMA_SQL
from holdspeak.db.steward import (
    ActiveRunExistsError,
    StewardCommandRepository,
    StewardPolicyRepository,
    StewardRunRepository,
    StewardStepRepository,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import (
    generate_pstpol_id,
    generate_pstrun_id,
    generate_pststep_id,
)
from holdspeak.services.project_steward_service import (
    CooldownActiveError,
    StewardDisabledError,
    ProjectStewardService,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _principal() -> Principal:
    return Principal(PrincipalKind.OWNER, "test-run-due-owner")


def _make_conn(tmp_path: Path, db_name: str = "test.db") -> sqlite3.Connection:
    db_path = tmp_path / db_name
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    _seed_project(conn)
    return conn


def _seed_project(
    conn: sqlite3.Connection,
    project_id: str = "proj-1",
    name: str = "Alpha",
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO projects "
        "(id, name, description, keywords_json, team_members_json, "
        "context_json, detection_threshold, is_archived, revision, "
        "created_at, updated_at) "
        "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, "
        "'2025-01-01T00:00:00', '2025-06-01T00:00:00')",
        (project_id, name),
    )
    conn.commit()


def _make_repos(conn: sqlite3.Connection):
    class _ConnCtx:
        def __enter__(self_):
            return conn
        def __exit__(self_, *a):
            conn.commit()

    factory = lambda: _ConnCtx()
    return (
        StewardPolicyRepository(factory),
        StewardRunRepository(factory),
        StewardStepRepository(factory),
        StewardCommandRepository(factory),
    )


class _FakeAutomations:
    """Automations repo backed by the real connection."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def list_pending_effects(
        self, action_kind: str, *, limit: int = 200,
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """SELECT we.*,
                      wev.watch_id   AS eval_watch_id,
                      wev.source_revision AS eval_source_revision,
                      cw.project_id  AS watch_project_id
               FROM watch_effects we
               JOIN watch_evaluations wev ON we.evaluation_id = wev.id
               JOIN connector_watches cw  ON wev.watch_id = cw.id
               WHERE we.state = 'pending'
                 AND we.action_kind = ?
               ORDER BY we.created_at ASC
               LIMIT ?""",
            (action_kind, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def update_effect(
        self,
        effect_id: str,
        *,
        state: str | None = None,
        target_ref: str | None = None,
        result_ref: str | None = None,
        verification_state: str | None = None,
        error_code: str | None = None,
        error_detail: str | None = None,
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if state is not None:
            updates.append("state = ?")
            params.append(state)
        if target_ref is not None:
            updates.append("target_ref = ?")
            params.append(target_ref)
        if result_ref is not None:
            updates.append("result_ref = ?")
            params.append(result_ref)
        if verification_state is not None:
            updates.append("verification_state = ?")
            params.append(verification_state)
        if error_code is not None:
            updates.append("error_code = ?")
            params.append(error_code)
        if error_detail is not None:
            updates.append("error_detail = ?")
            params.append(error_detail)
        if not updates:
            return
        if state in ("completed", "failed", "skipped"):
            updates.append("completed_at = datetime('now')")
        params.append(effect_id)
        self._conn.execute(
            f"UPDATE watch_effects SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        self._conn.commit()

    def get_effect(self, effect_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM watch_effects WHERE id=?",
            (effect_id,),
        ).fetchone()
        return dict(row) if row else None

    def append_event(self, event: dict) -> bool:
        return True

    def append_event_in_transaction(self, conn: Any, event: dict) -> bool:
        return True

    def get_event(self, event_id: str) -> Optional[dict]:
        return None

    def list_events(self, **kw: Any) -> list:
        return []


class _FakeDB:
    """DB mock with real steward repos + FakeAutomations."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        policies, runs, steps, commands = _make_repos(conn)
        self.steward_policies = policies
        self.steward_runs = runs
        self.steward_steps = steps
        self.steward_commands = commands
        self.automations = _FakeAutomations(conn)

    def _connection(self):
        class _Ctx:
            def __init__(self_, conn):
                self_._conn = conn
            def __enter__(self_):
                return self_._conn
            def __exit__(self_, *a):
                self_._conn.commit()
        return _Ctx(self._conn)


class _FakeCollector:
    def collect_all(self, project_id: str) -> dict[str, Any]:
        return {}


class _FakeDelta:
    def open_review(self, principal: Any, project_id: str) -> dict[str, Any]:
        return {"id": "prev_test", "proposals": []}


def _make_service(
    conn: sqlite3.Connection,
) -> tuple[ProjectStewardService, _FakeDB]:
    db = _FakeDB(conn)
    svc = ProjectStewardService(db, _FakeCollector(), _FakeDelta())
    return svc, db


def _make_policy(
    conn: sqlite3.Connection,
    project_id: str = "proj-1",
    *,
    unattended_enabled: int = 1,
    enabled: int = 1,
    cooldown_seconds: int = 0,
    eligible_kinds: list[str] | None = None,
) -> str:
    policy_id = generate_pstpol_id()
    conn.execute(
        """INSERT INTO steward_policies
           (id, project_id, eligible_effect_kinds_json,
            cooldown_seconds, enabled, unattended_enabled)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (policy_id, project_id,
         json.dumps(eligible_kinds or []),
         cooldown_seconds, enabled, unattended_enabled),
    )
    conn.commit()
    return policy_id


def _seed_watch_and_effect(
    conn: sqlite3.Connection,
    *,
    watch_id: str = "watch-rd-01",
    project_id: str = "proj-1",
    effect_id: str = "weff_rd_001",
    evaluation_id: str = "weval_rd_001",
    source_revision: str = "abc123",
    action_kind: str = "project.steward.run_once",
    rule_id: str = "wrule_rd_001",
) -> dict[str, str]:
    """Insert a watch, evaluation, rule, and pending effect."""
    # Watch
    conn.execute(
        """INSERT OR IGNORE INTO connector_watches
           (id, connector_id, query_kind, name, query_json, enabled, project_id)
           VALUES (?, 'gh', 'pull_requests', 'test', '{}', 1, ?)""",
        (watch_id, project_id),
    )
    # Rule
    conn.execute(
        """INSERT OR IGNORE INTO watch_rules
           (id, watch_id, ordinal, condition_schema, condition_json,
            action_schema, action_json, enabled, revision)
           VALUES (?, ?, 0, 'WatchCondition@1', '{}',
                   'WatchAction@1', '[]', 1, 0)""",
        (rule_id, watch_id),
    )
    # Evaluation
    conn.execute(
        """INSERT OR IGNORE INTO watch_evaluations
           (id, watch_id, watch_revision, source_revision,
            trigger_kind, state)
           VALUES (?, ?, 0, ?, 'scheduled', 'completed')""",
        (evaluation_id, watch_id, source_revision),
    )
    # Effect
    idem_key = f"test_idem_{effect_id}"
    conn.execute(
        """INSERT OR IGNORE INTO watch_effects
           (id, evaluation_id, rule_id, action_kind, idempotency_key, state)
           VALUES (?, ?, ?, ?, ?, 'pending')""",
        (effect_id, evaluation_id, rule_id, action_kind, idem_key),
    )
    conn.commit()
    return {
        "watch_id": watch_id,
        "effect_id": effect_id,
        "evaluation_id": evaluation_id,
        "source_revision": source_revision,
        "rule_id": rule_id,
    }


# ── TST-RD-001: Happy path ──────────────────────────────────────────


class TestRunDueHappyPath:
    """Pending effect triggers a run, effect resolved."""

    def test_run_due_starts_run(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)
        ids = _seed_watch_and_effect(conn)

        outcomes = svc.run_due(_principal())

        assert len(outcomes) == 1
        o = outcomes[0]
        assert o["outcome"] == "run_started"
        assert o["project_id"] == "proj-1"
        assert o["run_id"].startswith("pstrun_")
        assert o["run_state"] == "completed"

        # Effect row should be completed with target_ref = run_id.
        eff = db.automations.get_effect(ids["effect_id"])
        assert eff is not None
        assert eff["state"] == "completed"
        assert eff["target_ref"] == o["run_id"]
        assert eff["verification_state"] == "completed"

    def test_run_due_deterministic_watermark(self, tmp_path: Path) -> None:
        """Watermark = watch:watch_id:source_revision."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)
        ids = _seed_watch_and_effect(conn, source_revision="rev42")

        outcomes = svc.run_due(_principal())
        assert outcomes[0]["watermark"] == f"watch:watch-rd-01:rev42"

        # Verify the run row carries the watermark.
        run = db.steward_runs.get_run(outcomes[0]["run_id"])
        assert run["watermark"] == f"watch:watch-rd-01:rev42"


# ── TST-RD-002: Same-watermark dedup ────────────────────────────────


class TestSameWatermarkDedup:
    """Multiple requests at the same watermark resolve to ONE run."""

    def test_second_effect_same_watermark_resolves(self, tmp_path: Path) -> None:
        """Two effects for the same watermark: first starts a run,
        second resolves to that run (resolved_existing_run)."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)

        # First effect.
        ids1 = _seed_watch_and_effect(
            conn,
            effect_id="weff_rd_001",
            evaluation_id="weval_rd_001",
            source_revision="same_rev",
        )

        outcomes1 = svc.run_due(_principal())
        assert len(outcomes1) == 1
        assert outcomes1[0]["outcome"] == "run_started"
        run_id = outcomes1[0]["run_id"]

        # Second effect: same evaluation (same watch + source_revision
        # = same watermark), different effect_id.
        idem_key_2 = "test_idem_weff_rd_002"
        conn.execute(
            """INSERT INTO watch_effects
               (id, evaluation_id, rule_id, action_kind,
                idempotency_key, state)
               VALUES (?, ?, ?, 'project.steward.run_once', ?, 'pending')""",
            ("weff_rd_002", ids1["evaluation_id"], ids1["rule_id"],
             idem_key_2),
        )
        conn.commit()

        outcomes2 = svc.run_due(_principal())
        assert len(outcomes2) == 1
        assert outcomes2[0]["outcome"] == "resolved_existing_run"
        assert outcomes2[0]["run_id"] == run_id

    def test_different_watermarks_create_separate_runs(self, tmp_path: Path) -> None:
        """Different source_revisions => different watermarks => separate runs."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)

        _seed_watch_and_effect(
            conn,
            effect_id="weff_rd_a",
            evaluation_id="weval_rd_a",
            source_revision="rev_a",
        )

        outcomes_a = svc.run_due(_principal())
        assert outcomes_a[0]["outcome"] == "run_started"
        run_a = outcomes_a[0]["run_id"]

        # Same rule_id (already exists) to avoid FK violation.
        _seed_watch_and_effect(
            conn,
            effect_id="weff_rd_b",
            evaluation_id="weval_rd_b",
            source_revision="rev_b",
        )

        outcomes_b = svc.run_due(_principal())
        assert outcomes_b[0]["outcome"] == "run_started"
        run_b = outcomes_b[0]["run_id"]

        assert run_a != run_b


# ── TST-RD-003: No opt-in skip ──────────────────────────────────────


class TestNoOptInSkip:
    """unattended_enabled=0 => no run, honest skip receipt."""

    def test_no_optin_skips(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=0)
        ids = _seed_watch_and_effect(conn)

        outcomes = svc.run_due(_principal())
        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "skipped_no_opt_in"

        # Effect row should be skipped.
        eff = db.automations.get_effect(ids["effect_id"])
        assert eff["state"] == "skipped"
        assert eff["error_code"] == "no_opt_in"

    def test_no_policy_skips(self, tmp_path: Path) -> None:
        """No policy at all => no opt-in (default OFF)."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        # No policy created.
        ids = _seed_watch_and_effect(conn)

        outcomes = svc.run_due(_principal())
        assert outcomes[0]["outcome"] == "skipped_no_opt_in"


# ── TST-RD-004: Cooldown gates unattended ────────────────────────────


class TestCooldownGate:
    """Scheduling-layer cooldown gates unattended runs."""

    def test_cooldown_active_skips(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1, cooldown_seconds=3600)

        # Complete a run first to set up cooldown.
        run_id = svc.run_once(_principal(), "proj-1")
        assert db.steward_runs.get_run(run_id)["state"] == "completed"

        # Now seed a pending effect.
        ids = _seed_watch_and_effect(conn)

        outcomes = svc.run_due(_principal())
        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "skipped_cooldown"

        eff = db.automations.get_effect(ids["effect_id"])
        assert eff["state"] == "skipped"
        assert eff["error_code"] == "cooldown_active"

    def test_interrupted_exempt_from_cooldown(self, tmp_path: Path) -> None:
        """Interrupted runs are exempt from cooldown (STW-009)."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1, cooldown_seconds=3600)

        # Insert and mark a run as interrupted.
        run_id = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id, project_id="proj-1",
        )
        db.steward_runs.update_run_state(run_id, state="interrupted")

        # Pending effect should not be blocked.
        ids = _seed_watch_and_effect(conn)

        outcomes = svc.run_due(_principal())
        assert outcomes[0]["outcome"] == "run_started"


# ── TST-RD-005: Disabled policy skip ────────────────────────────────


class TestDisabledPolicySkip:
    """Steward policy disabled => honest skip."""

    def test_disabled_skips(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1, enabled=0)
        ids = _seed_watch_and_effect(conn)

        outcomes = svc.run_due(_principal())
        assert outcomes[0]["outcome"] == "skipped_disabled"

        eff = db.automations.get_effect(ids["effect_id"])
        assert eff["state"] == "skipped"
        assert eff["error_code"] == "steward_disabled"


# ── TST-RD-006: STW-002 absorbed as resolution ──────────────────────


class TestSTW002Absorbed:
    """ActiveRunExistsError is resolution, not error."""

    def test_active_run_absorbed(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)

        # Insert an active run (queued, different watermark).
        active_id = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=active_id, project_id="proj-1",
            watermark="other_watermark",
        )

        ids = _seed_watch_and_effect(conn)

        outcomes = svc.run_due(_principal())
        assert outcomes[0]["outcome"] == "resolved_existing_run"
        assert outcomes[0]["run_id"] == active_id


# ── TST-RD-007: Deterministic watermark ──────────────────────────────


class TestDeterministicWatermark:
    """Same evaluation identity => same watermark, always."""

    def test_watermark_formula(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)

        ids = _seed_watch_and_effect(
            conn,
            watch_id="w-det",
            source_revision="sr_42",
        )

        outcomes = svc.run_due(_principal())
        expected_wm = "watch:w-det:sr_42"
        assert outcomes[0]["watermark"] == expected_wm


# ── TST-RD-008: run_due NEVER raises ────────────────────────────────


class TestRunDueNeverRaises:
    """Even with corrupt effects, run_due returns outcomes."""

    def test_corrupt_effect_isolated(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)

        # Create a watch + eval but NO project, so project_id is empty.
        conn.execute(
            """INSERT INTO connector_watches
               (id, connector_id, query_kind, name, query_json, enabled, project_id)
               VALUES ('w-corrupt', 'gh', 'pull_requests', 'bad', '{}', 1, '')""",
        )
        conn.execute(
            """INSERT INTO watch_rules
               (id, watch_id, ordinal, condition_schema, condition_json,
                action_schema, action_json, enabled, revision)
               VALUES ('wrule_corrupt', 'w-corrupt', 0, '', '{}', '', '[]', 1, 0)""",
        )
        conn.execute(
            """INSERT INTO watch_evaluations
               (id, watch_id, watch_revision, source_revision,
                trigger_kind, state)
               VALUES ('weval_corrupt', 'w-corrupt', 0, 'rev_x',
                       'scheduled', 'completed')""",
        )
        conn.execute(
            """INSERT INTO watch_effects
               (id, evaluation_id, rule_id, action_kind,
                idempotency_key, state)
               VALUES ('weff_corrupt', 'weval_corrupt', 'wrule_corrupt',
                       'project.steward.run_once', 'idem_corrupt', 'pending')""",
        )
        conn.commit()

        # Must not raise.
        outcomes = svc.run_due(_principal())
        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "skipped_no_project"

    def test_no_pending_effects_empty(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        outcomes = svc.run_due(_principal())
        assert outcomes == []


# ── TST-RD-009: Manual paths byte-identical ──────────────────────────


class TestManualPathsByteIdentical:
    """Manual insert_run/run_once behavior stays untouched.

    These re-prove the existing gates work identically: manual paths
    do NOT check unattended_enabled.
    """

    def test_manual_run_once_ignores_unattended(self, tmp_path: Path) -> None:
        """Manual run_once works even with unattended_enabled=0."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=0)

        # Manual run_once should succeed (unattended gate is NOT here).
        run_id = svc.run_once(_principal(), "proj-1")
        assert run_id.startswith("pstrun_")
        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"

    def test_manual_insert_run_ignores_unattended(self, tmp_path: Path) -> None:
        """Manual insert_run works even with unattended_enabled=0."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=0)

        run_id = svc.insert_run(_principal(), "proj-1")
        assert run_id.startswith("pstrun_")

    def test_manual_cooldown_still_enforced(self, tmp_path: Path) -> None:
        """Manual insert_run still checks cooldown (the existing gate)."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, cooldown_seconds=3600, unattended_enabled=0)

        first = svc.run_once(_principal(), "proj-1")
        assert db.steward_runs.get_run(first)["state"] == "completed"

        with pytest.raises(CooldownActiveError):
            svc.insert_run(_principal(), "proj-1")

    def test_manual_disabled_still_enforced(self, tmp_path: Path) -> None:
        """Manual insert_run still checks enabled (the existing gate)."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, enabled=0, unattended_enabled=0)

        with pytest.raises(StewardDisabledError):
            svc.insert_run(_principal(), "proj-1")


# ── TST-RD-010: No project binding ──────────────────────────────────


class TestNoProjectBinding:
    """Effect for a watch with no project_id => honest skip."""

    def test_empty_project_skips(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)

        # Watch with empty project_id.
        conn.execute(
            """INSERT INTO connector_watches
               (id, connector_id, query_kind, name, query_json, enabled, project_id)
               VALUES ('w-noproj', 'gh', 'pull_requests', 'no proj', '{}', 1, '')""",
        )
        conn.execute(
            """INSERT INTO watch_rules
               (id, watch_id, ordinal, condition_schema, condition_json,
                action_schema, action_json, enabled, revision)
               VALUES ('wrule_noproj', 'w-noproj', 0, '', '{}', '', '[]', 1, 0)""",
        )
        conn.execute(
            """INSERT INTO watch_evaluations
               (id, watch_id, watch_revision, source_revision,
                trigger_kind, state)
               VALUES ('weval_noproj', 'w-noproj', 0, 'rev_np',
                       'scheduled', 'completed')""",
        )
        conn.execute(
            """INSERT INTO watch_effects
               (id, evaluation_id, rule_id, action_kind,
                idempotency_key, state)
               VALUES ('weff_noproj', 'weval_noproj', 'wrule_noproj',
                       'project.steward.run_once', 'idem_noproj', 'pending')""",
        )
        conn.commit()

        outcomes = svc.run_due(_principal())
        assert outcomes[0]["outcome"] == "skipped_no_project"


# ── TST-RD-011: Replay idempotency ──────────────────────────────────


class TestReplayIdempotency:
    """Re-draining an already-completed effect is a no-op."""

    def test_completed_effect_not_re_drained(self, tmp_path: Path) -> None:
        """Once an effect is completed, run_due does not re-drain it."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        _make_policy(conn, unattended_enabled=1)
        ids = _seed_watch_and_effect(conn)

        # First drain: starts a run.
        outcomes1 = svc.run_due(_principal())
        assert outcomes1[0]["outcome"] == "run_started"

        # Second drain: effect is completed, not pending => empty.
        outcomes2 = svc.run_due(_principal())
        assert outcomes2 == []
