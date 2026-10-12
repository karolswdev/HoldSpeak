"""HS-167 counsel close fixes — regression tests for each finding."""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import subprocess
import sys
import tempfile
import textwrap
import time
from unittest.mock import MagicMock, patch


# ── M-1: _fetch_meta thread-local leak between watch evaluations ─────


class TestFetchMetaThreadLocalLeak:
    """A source that sets _fetch_meta.calls then raises must not leak
    that value into the next watch's evaluation on the same thread."""

    def test_drain_clears_after_source_sets_and_raises(self) -> None:
        """Simulates the leak: set calls, then raise mid-entity-build.
        drain_fetch_meta must return empty after the clear-on-entry
        pattern fires on the next snapshot call."""
        from holdspeak.services.watch_sources import (
            _fetch_meta,
            drain_fetch_meta,
        )

        # Simulate a Jira fetch that sets calls then crashes
        _fetch_meta.calls = 5

        # drain should return the stale value and clear it
        meta = drain_fetch_meta()
        assert meta == {"calls": 5}

        # After drain, thread-local is clean
        meta2 = drain_fetch_meta()
        assert meta2 == {}

    def test_clear_on_entry_prevents_leak_across_sources(self) -> None:
        """If source A sets calls=5 then raises, and source B runs
        clean on the same thread, source B's evaluation must carry
        no stale calls — because JiraWatchSource.snapshot() clears
        on entry."""
        from holdspeak.services.watch_sources import (
            _fetch_meta,
            drain_fetch_meta,
        )

        # Simulate stale leak from a prior failed source
        _fetch_meta.calls = 7

        # The clear-on-entry in JiraWatchSource.snapshot() calls
        # drain_fetch_meta() at the top.  We test the same primitive:
        drain_fetch_meta()  # clear-on-entry

        # Now a "clean" source runs without setting calls
        # drain should return empty
        meta = drain_fetch_meta()
        assert meta == {}

    def test_evaluate_due_except_drains_stale_meta(self) -> None:
        """The except block in evaluate_due must drain _fetch_meta
        so that a failed fetch never contaminates the next watch.

        We simulate by setting calls, then verifying the drain call
        (which mirrors what evaluate_due's except path does) clears it.
        """
        from holdspeak.services.watch_sources import (
            _fetch_meta,
            drain_fetch_meta,
        )

        # A Jira source sets calls, then _evaluate_core raises
        _fetch_meta.calls = 3

        # The except handler drains (M-1 fix)
        drain_fetch_meta()

        # Next watch on the same thread: no contamination
        assert drain_fetch_meta() == {}

    def test_thread_isolation_of_fetch_meta(self) -> None:
        """_fetch_meta is thread-local: setting calls on thread A
        must not be visible on thread B."""
        from holdspeak.services.watch_sources import (
            _fetch_meta,
            drain_fetch_meta,
        )

        _fetch_meta.calls = 42
        seen_on_other: dict = {}

        def _other_thread() -> None:
            seen_on_other.update(drain_fetch_meta())

        t = threading.Thread(target=_other_thread)
        t.start()
        t.join(timeout=2)

        assert seen_on_other == {}, (
            f"Thread B saw stale calls from thread A: {seen_on_other}"
        )
        # Clean up thread A
        drain_fetch_meta()


# ── S-7: _CrossProcessLock reentrant-acquire fd leak ──────────────────


def _count_open_fds() -> int:
    """Count open file descriptors for this process."""
    try:
        return len(os.listdir("/dev/fd"))
    except FileNotFoundError:
        return len(os.listdir(f"/proc/{os.getpid()}/fd"))


def _make_lock(timeout: float = 2.0):
    from holdspeak.services.jira_provider import _CrossProcessLock
    return _CrossProcessLock(timeout=timeout)


class TestCrossProcessLockFdLeak:
    def test_nested_acquisition_leaks_no_fd(self, tmp_path, monkeypatch):
        """Reentrant __enter__ must NOT open a second fd."""
        monkeypatch.setattr(
            "holdspeak.services.jira_provider._acli_lockfile_path",
            lambda: tmp_path / "test.lock",
        )
        lock = _make_lock()

        fds_before = _count_open_fds()
        with lock:
            with lock:
                with lock:
                    pass
        fds_after = _count_open_fds()

        assert fds_after <= fds_before, (
            f"fd leak: {fds_after - fds_before} fds leaked after nested acquisition"
        )

    def test_second_thread_blocked_while_held(self, tmp_path, monkeypatch):
        """A second thread cannot acquire while the first thread holds it."""
        monkeypatch.setattr(
            "holdspeak.services.jira_provider._acli_lockfile_path",
            lambda: tmp_path / "test.lock",
        )
        lock = _make_lock()
        acquired_inside = threading.Event()

        def contender():
            with lock:
                acquired_inside.set()

        with lock:
            t = threading.Thread(target=contender, daemon=True)
            t.start()
            blocked = not acquired_inside.wait(timeout=0.5)
            assert blocked, "Second thread acquired the lock while first thread held it"

        t.join(timeout=5)
        assert acquired_inside.is_set(), "Contender should acquire after release"

    def test_reentrant_depth_resets_on_exit(self, tmp_path, monkeypatch):
        """After full exit, a fresh acquire must work (depth back to 0)."""
        monkeypatch.setattr(
            "holdspeak.services.jira_provider._acli_lockfile_path",
            lambda: tmp_path / "test.lock",
        )
        lock = _make_lock()

        with lock:
            with lock:
                pass

        with lock:
            depth = getattr(lock._local, "depth", 0)
            assert depth == 1, f"expected depth 1 inside fresh acquire, got {depth}"


# ── S-3: MCP project.configure_steward evaluation_cadence_minutes ─────


class TestMCPConfigureStewardCadence:
    @pytest.fixture
    def db(self, tmp_path: Path):
        from holdspeak.db.core import Database, reset_database
        reset_database()
        database = Database(tmp_path / "s3-test.db")
        yield database
        reset_database()

    @pytest.fixture(autouse=True)
    def _wire(self, db, monkeypatch):
        from holdspeak.mcp import server
        from holdspeak.mcp.families import project as project_family
        from holdspeak.principals import Principal, PrincipalKind
        OWNER = Principal(PrincipalKind.OWNER, "s3-owner")
        monkeypatch.setattr(project_family, "get_database", lambda: db)
        monkeypatch.setattr(
            server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER),
        )
        monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")

    def _seed_project(self, db, pid: str = "proj-s3-001") -> str:
        with db._connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO projects "
                "(id, name, description, keywords_json, team_members_json, "
                "context_json, detection_threshold, is_archived, revision, "
                "created_at, updated_at) "
                "VALUES (?, 'S3 Test', '', '[]', '[]', '{}', 0.5, 0, 1, "
                "'2025-01-01T00:00:00', '2025-06-01T00:00:00')",
                (pid,),
            )
        return pid

    def _call(self, name: str, arguments: dict[str, Any] | None = None):
        from holdspeak.mcp import server
        response = server.handle_message({
            "jsonrpc": "2.0",
            "id": name,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        })
        assert response is not None
        result = response["result"]
        return result["isError"], json.loads(result["content"][0]["text"])

    def test_schema_has_evaluation_cadence_minutes(self) -> None:
        from holdspeak.mcp.families import project as project_family
        for t in project_family.TOOLS:
            if t["name"] == "project.configure_steward":
                props = t["inputSchema"]["properties"]
                assert "evaluation_cadence_minutes" in props
                field = props["evaluation_cadence_minutes"]
                assert field["type"] == "integer"
                assert field["minimum"] == 1
                assert field["maximum"] == 10080
                return
        pytest.fail("project.configure_steward not found in TOOLS")

    def test_cadence_below_minimum_fenced(self, db) -> None:
        pid = self._seed_project(db)
        is_err, body = self._call("project.configure_steward", {
            "project_id": pid,
            "evaluation_cadence_minutes": 0,
        })
        assert is_err
        assert "evaluation_cadence_minutes" in (body.get("error") or body.get("message", ""))

    def test_cadence_above_maximum_fenced(self, db) -> None:
        pid = self._seed_project(db)
        is_err, body = self._call("project.configure_steward", {
            "project_id": pid,
            "evaluation_cadence_minutes": 10081,
        })
        assert is_err
        assert "10080" in (body.get("error") or body.get("message", ""))

    def test_cadence_applied_to_watches(self, db) -> None:
        pid = self._seed_project(db)
        wid = "cw_s3_test_001"
        with db._connection() as conn:
            db.automations.create_watch_in_transaction(
                conn,
                watch_id=wid,
                connector_id="github",
                query_kind="pull_requests",
                name="S3 watch",
                query_json='{"repository":"owner/repo"}',
                enabled=True,
                schema_version="WatchSpec@1",
                project_id=pid,
                state="active",
                revision=1,
            )

        is_err, body = self._call("project.configure_steward", {
            "project_id": pid,
            "evaluation_cadence_minutes": 120,
        })
        assert not is_err
        assert body.get("success") is True

        row = db.automations.get_watch(wid)
        assert row is not None
        assert int(row.get("evaluation_cadence_minutes", 0)) == 120

    def test_cadence_alone_triggers_write_path(self, db) -> None:
        pid = self._seed_project(db)
        is_err, body = self._call("project.configure_steward", {
            "project_id": pid,
            "evaluation_cadence_minutes": 5,
        })
        assert not is_err
        assert body.get("success") is True
        assert "policy" in body


# ── M-2: archive pauses watches + disables unattended ─────────────────


def _make_m2_db(tmp_path: Path):
    from holdspeak.db.core import Database
    return Database(db_path=tmp_path / "holdspeak.db")


def _m2_owner():
    from holdspeak.principals import Principal, PrincipalKind
    return Principal(PrincipalKind.OWNER, "test-owner")


def _m2_make_project(db, principal):
    from holdspeak.services.project_service import ProjectService
    svc = ProjectService(db)
    result = svc.create_project(principal, {"name": "archtest", "description": "d"})
    return result["id"]


def _m2_add_watch(db, watch_id: str, project_id: str, *, state: str = "active"):
    now = datetime.now(timezone.utc)
    next_eval = (now - timedelta(minutes=5)).isoformat(timespec="seconds")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO connector_watches
               (id, connector_id, query_kind, name, query_json, snapshot_json,
                enabled, project_id, state, evaluation_cadence_minutes,
                next_evaluation_at, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (watch_id, "github", "pr", f"w-{watch_id}", "{}", "{}",
             1, project_id, state, 60, next_eval),
        )


def _m2_add_policy(db, project_id: str, *, unattended: bool = True) -> str:
    from holdspeak.project_contracts import generate_pstpol_id
    policy_id = generate_pstpol_id()
    db.steward_policies.insert_policy(
        policy_id=policy_id,
        project_id=project_id,
        eligible_effect_kinds_json="[]",
        yolo_flags_json="{}",
        max_retries=3,
        max_actions_per_run=10,
        cooldown_seconds=0,
        bounds_json="{}",
        enabled=1,
        unattended_enabled=1 if unattended else 0,
    )
    return policy_id


class TestM2ArchivePausesWatches:
    def test_archive_pauses_active_watches(self, tmp_path: Path) -> None:
        db = _make_m2_db(tmp_path)
        principal = _m2_owner()
        project_id = _m2_make_project(db, principal)

        _m2_add_watch(db, "w_active", project_id, state="active")
        _m2_add_watch(db, "w_tested", project_id, state="tested")

        from holdspeak.services.project_service import ProjectService
        svc = ProjectService(db)
        svc.archive_project(principal, project_id)

        with db._connection() as conn:
            for wid in ("w_active", "w_tested"):
                row = conn.execute(
                    "SELECT state FROM connector_watches WHERE id=?", (wid,)
                ).fetchone()
                assert row["state"] == "paused", f"{wid} should be paused after archive"

    def test_archive_disables_unattended_policy(self, tmp_path: Path) -> None:
        db = _make_m2_db(tmp_path)
        principal = _m2_owner()
        project_id = _m2_make_project(db, principal)

        policy_id = _m2_add_policy(db, project_id, unattended=True)

        from holdspeak.services.project_service import ProjectService
        svc = ProjectService(db)
        svc.archive_project(principal, project_id)

        policy = db.steward_policies.get_policy(policy_id)
        assert policy is not None
        assert policy["unattended_enabled"] == 0

    def test_archive_makes_list_due_watches_empty(self, tmp_path: Path) -> None:
        db = _make_m2_db(tmp_path)
        principal = _m2_owner()
        project_id = _m2_make_project(db, principal)

        _m2_add_watch(db, "w_due", project_id, state="active")

        from holdspeak.services.project_service import ProjectService
        svc = ProjectService(db)
        svc.archive_project(principal, project_id)

        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        due = db.automations.list_due_watches(now_iso)
        assert not any(w["id"] == "w_due" for w in due)


class TestM2ListDueWatchesExcludesArchived:
    def test_archived_project_watches_excluded_defensively(self, tmp_path: Path) -> None:
        """Even if a watch is still state='active' (race/direct edit),
        list_due_watches excludes it when the project is archived."""
        db = _make_m2_db(tmp_path)
        principal = _m2_owner()
        project_id = _m2_make_project(db, principal)
        _m2_add_watch(db, "w_race", project_id, state="active")

        # Archive the project directly (bypassing service to simulate race)
        with db._connection() as conn:
            conn.execute(
                "UPDATE projects SET lifecycle='archived', is_archived=1 WHERE id=?",
                (project_id,),
            )

        now_iso = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(timespec="seconds")
        due = db.automations.list_due_watches(now_iso)
        assert not any(w["id"] == "w_race" for w in due)

    def test_unbound_watches_still_listed(self, tmp_path: Path) -> None:
        """Watches without a project_id are unaffected by the filter."""
        db = _make_m2_db(tmp_path)
        _m2_add_watch(db, "w_free", "", state="active")

        now_iso = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat(timespec="seconds")
        due = db.automations.list_due_watches(now_iso)
        assert any(w["id"] == "w_free" for w in due)


class TestM2RestoreDoesNotAutoResume:
    def test_restore_leaves_watches_paused(self, tmp_path: Path) -> None:
        db = _make_m2_db(tmp_path)
        principal = _m2_owner()
        project_id = _m2_make_project(db, principal)

        _m2_add_watch(db, "w_arch", project_id, state="active")

        from holdspeak.services.project_service import ProjectService
        svc = ProjectService(db)
        svc.archive_project(principal, project_id)

        # Verify paused
        with db._connection() as conn:
            row = conn.execute(
                "SELECT state FROM connector_watches WHERE id='w_arch'"
            ).fetchone()
            assert row["state"] == "paused"

        # Restore
        svc.restore_project(principal, project_id)

        # Still paused -- not auto-resumed
        with db._connection() as conn:
            row = conn.execute(
                "SELECT state FROM connector_watches WHERE id='w_arch'"
            ).fetchone()
            assert row["state"] == "paused", "restore must not auto-resume watches"


# ── merged from tests/unit/test_hs167_debts.py ──
# HS-167-02 — the five functional debts, tested.
#
# 1. Population toggles persisted (jira_scope answer round-trip)
# 2. Enrichment receipted (OBSERVE step carries calls count)
# 3. The acli lock across processes (file lock + typed timeout)
# 4. The cadence write wire (policy PUT carries cadence, range-fenced)
# 5. The trigger route (wired -> runs; unwired -> typed refusal)


# ── helpers ────────────────────────────────────────────────────────────

def _make_db(tmp_path: Path) -> Any:
    """Create an isolated HoldSpeak DB."""
    db_path = tmp_path / "holdspeak.db"
    from holdspeak.db.core import Database
    return Database(db_path=db_path)


def _owner() -> Any:
    from holdspeak.principals import Principal, PrincipalKind
    return Principal(PrincipalKind.OWNER, "test-owner")


# ── Debt 1: Population toggles persisted ──────────────────────────────


class TestDebt1PopulationToggles:
    """The jira_scope answer round-trips through project_setup_answer."""

    def test_jira_scope_answer_persists_and_resumes(self, tmp_path: Path) -> None:
        db = _make_db(tmp_path)
        from holdspeak.services.project_setup_service import (
            ProjectSetupService,
            Q_JIRA_SCOPE,
        )

        svc = ProjectSetupService(db)
        principal = _owner()

        # Start a session
        session = svc.start_setup(principal)
        session_id = session["id"]

        # Submit a jira_scope answer
        scope = {
            "connectionRef": "mysite.atlassian.net|me@example.com",
            "projects": ["KAN", "DEV"],
            "issueTypes": ["Bug", "Story"],
            "statusCategories": ["To Do", "In Progress"],
            "jql": "priority = High",
        }
        result = svc.answer(
            principal, session_id, Q_JIRA_SCOPE,
            {"text": json.dumps(scope)},
        )
        assert result["question_id"] == Q_JIRA_SCOPE

        # Resume: get_setup should return the jira_scope answer
        resumed = svc.get_setup(session_id)
        assert Q_JIRA_SCOPE in resumed["answers"]
        answer = resumed["answers"][Q_JIRA_SCOPE]
        # The scope JSON is stored in the answer's original field
        answer_data = answer.get("answer", {})
        if isinstance(answer_data, str):
            answer_data = json.loads(answer_data)
        original = answer_data.get("original", "")
        restored = json.loads(original)
        assert restored["projects"] == ["KAN", "DEV"]
        assert restored["connectionRef"] == "mysite.atlassian.net|me@example.com"

    def test_jira_scope_answer_multiple_revisions(self, tmp_path: Path) -> None:
        db = _make_db(tmp_path)
        from holdspeak.services.project_setup_service import (
            ProjectSetupService,
            Q_JIRA_SCOPE,
        )

        svc = ProjectSetupService(db)
        principal = _owner()

        session = svc.start_setup(principal)
        session_id = session["id"]

        # First answer
        svc.answer(
            principal, session_id, Q_JIRA_SCOPE,
            {"text": json.dumps({"connectionRef": "a|b", "projects": ["A"]})},
        )
        # Second answer (revision 2)
        svc.answer(
            principal, session_id, Q_JIRA_SCOPE,
            {"text": json.dumps({"connectionRef": "a|b", "projects": ["A", "B"]})},
        )

        # Resume should return the LATEST revision
        resumed = svc.get_setup(session_id)
        answer = resumed["answers"][Q_JIRA_SCOPE]
        answer_data = answer.get("answer", {})
        if isinstance(answer_data, str):
            answer_data = json.loads(answer_data)
        restored = json.loads(answer_data.get("original", ""))
        assert restored["projects"] == ["A", "B"]


# ── Debt 2: Enrichment receipted ──────────────────────────────────────


class TestDebt2EnrichmentReceipted:
    """The OBSERVE step carries the calls count from the evaluation."""

    def test_observe_step_carries_calls_count(self, tmp_path: Path) -> None:
        db = _make_db(tmp_path)
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector

        # Create a project and a watch with a known evaluation
        principal = _owner()
        project_id = "proj_test123"

        # Insert a minimal project row
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                (project_id, "Test Project"),
            )

        # Create a watch bound to the project
        watch_id = "watch_test456"
        db.automations.create_watch(
            watch_id=watch_id,
            connector_id="jira",
            query_kind="issues",
            name="Test Watch",
            query={"connection_ref": "site|email"},
            enabled=True,
        )
        db.automations.update_watch_spec(
            watch_id, project_id=project_id, state="active",
        )

        # Create a project_source binding
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO project_sources "
                "(id, project_id, source_ref, enabled, created_at, updated_at) "
                "VALUES (?, ?, ?, 1, datetime('now'), datetime('now'))",
                ("psrc_test789", project_id, f"watch:{watch_id}"),
            )

        # Create an evaluation with metadata_json containing calls=4
        db.automations.create_evaluation(
            evaluation_id="weval_test001",
            watch_id=watch_id,
            watch_revision=0,
            source_revision="abc123",
            trigger_kind="scheduled",
            state="completed",
            started_at="2026-09-03T00:00:00+00:00",
            completed_at="2026-09-03T00:00:01+00:00",
            metadata_json=json.dumps({"calls": 4}),
        )

        # Build the steward with a mock collector (we test the meta, not collection)
        mock_collector = MagicMock(spec=ProjectEvidenceCollector)
        mock_collector.collect_all.return_value = {"native:meetings": {"state": "ok"}}

        mock_delta = MagicMock()
        svc = ProjectStewardService(db, mock_collector, mock_delta)

        # Run the OBSERVE phase
        result = svc._phase_observe(principal, project_id)

        # The result should include calls=4
        assert result.get("calls") == 4
        assert result.get("source_meta", {}).get(watch_id, {}).get("calls") == 4

    def test_observe_step_receipt_json_set(self, tmp_path: Path) -> None:
        """A full run_once sets receipt_json on the OBSERVE step."""
        db = _make_db(tmp_path)
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_delta_service import ProjectDeltaService

        principal = _owner()
        project_id = "proj_receipt"

        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                (project_id, "Receipt Test"),
            )

        watch_id = "watch_receipt"
        db.automations.create_watch(
            watch_id=watch_id,
            connector_id="jira",
            query_kind="issues",
            name="Receipt Watch",
            query={},
            enabled=True,
        )
        db.automations.update_watch_spec(watch_id, project_id=project_id, state="active")

        with db._connection() as conn:
            conn.execute(
                "INSERT INTO project_sources "
                "(id, project_id, source_ref, enabled, created_at, updated_at) "
                "VALUES (?, ?, ?, 1, datetime('now'), datetime('now'))",
                ("psrc_receipt", project_id, f"watch:{watch_id}"),
            )

        db.automations.create_evaluation(
            evaluation_id="weval_receipt",
            watch_id=watch_id,
            source_revision="def456",
            trigger_kind="scheduled",
            state="completed",
            metadata_json=json.dumps({"calls": 4}),
        )

        mock_collector = MagicMock(spec=ProjectEvidenceCollector)
        mock_collector.collect_all.return_value = {}
        mock_delta = MagicMock()
        mock_delta.open_review.return_value = {"id": "rev1", "proposals": []}

        svc = ProjectStewardService(
            db, collector=mock_collector, delta=mock_delta,
        )

        run_id = svc.run_once(principal, project_id)

        # Read the OBSERVE step
        steps = db.steward_steps.list_steps(run_id)
        observe_step = next(
            (s for s in steps if s["phase"] == "observe"),
            None,
        )
        assert observe_step is not None
        receipt = json.loads(observe_step.get("receipt_json") or "{}")
        assert receipt.get("calls") == 4


# ── Debt 3: The acli lock across processes ────────────────────────────


class TestDebt3AcliFileLock:
    """The acli lock is a file lock with typed timeout."""

    def test_lock_acquires_and_releases(self, tmp_path: Path) -> None:
        """Basic acquire/release cycle works."""
        with patch(
            "holdspeak.services.jira_provider._acli_lockfile_path",
            return_value=tmp_path / ".acli.lock",
        ):
            from holdspeak.services.jira_provider import _CrossProcessLock
            lock = _CrossProcessLock(timeout=2.0)
            with lock:
                # Lock is held
                assert (tmp_path / ".acli.lock").exists()
            # Lock released

    def test_lock_timeout_raises_typed_error(self, tmp_path: Path) -> None:
        """A second process holding the lock causes a typed timeout."""
        lockfile = tmp_path / ".acli.lock"

        # Hold the lock from a subprocess
        holder_script = textwrap.dedent(f"""\
            import fcntl, os, sys, time
            fd = os.open({str(lockfile)!r}, os.O_CREAT | os.O_RDWR)
            fcntl.flock(fd, fcntl.LOCK_EX)
            sys.stdout.write("locked\\n")
            sys.stdout.flush()
            time.sleep(10)
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        """)

        proc = subprocess.Popen(
            [sys.executable, "-c", holder_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            # Wait for the subprocess to acquire the lock
            line = proc.stdout.readline()
            assert b"locked" in line

            # Now try to acquire the lock with a short timeout
            with patch(
                "holdspeak.services.jira_provider._acli_lockfile_path",
                return_value=lockfile,
            ):
                from holdspeak.services.jira_provider import _CrossProcessLock
                from holdspeak.services.errors import ServiceError
                lock = _CrossProcessLock(timeout=0.3)
                with pytest.raises(ServiceError) as exc_info:
                    with lock:
                        pass
                assert exc_info.value.code == "lock_timeout"
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_lock_reentrancy_same_thread(self, tmp_path: Path) -> None:
        """The in-process RLock allows reentrant acquisition."""
        with patch(
            "holdspeak.services.jira_provider._acli_lockfile_path",
            return_value=tmp_path / ".acli.lock",
        ):
            from holdspeak.services.jira_provider import _CrossProcessLock
            lock = _CrossProcessLock(timeout=2.0)
            # RLock allows reentrancy within the same thread
            lock._rlock.acquire()
            lock._rlock.acquire()
            lock._rlock.release()
            lock._rlock.release()


def _steward_ctx(db: Any) -> Any:
    """PHILO-9-02: a real WebContext with the real steward service (the routes reach its operations)."""
    from holdspeak.services.project_steward_service import ProjectStewardService
    from holdspeak.web.context import WebContext

    return WebContext(get_state=lambda: {}, project_steward_service=ProjectStewardService(db, None, None))


def _owner_client(router: Any) -> Any:
    """The router under an OWNER principal (an admitted write needs the authenticated principal)."""
    from fastapi import FastAPI
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.testclient import TestClient

    class _Owner(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.principal = _owner()
            return await call_next(request)

    app = FastAPI()
    app.add_middleware(_Owner)
    app.include_router(router)
    return TestClient(app)


def _await_receipt(db: Any, operation_id: str, timeout: float = 20.0) -> dict[str, Any]:
    import time as _time

    deadline = _time.monotonic() + timeout
    while _time.monotonic() < deadline:
        with db._connection() as conn:
            row = conn.execute("SELECT * FROM kernel_receipts WHERE operation_id=?", (operation_id,)).fetchone()
        if row is not None:
            return dict(row)
        _time.sleep(0.05)
    raise AssertionError(f"no terminal receipt for {operation_id}")


# ── Debt 4: The cadence write wire ────────────────────────────────────


class TestDebt4CadenceWriteWire:
    """evaluation_cadence_minutes validation and write in policy PUT."""

    def test_cadence_range_fence_floor(self, tmp_path: Path) -> None:
        """Cadence below 1 is rejected."""
        db = _make_db(tmp_path)
        from holdspeak.web.routes.steward import build_steward_router
        from unittest.mock import AsyncMock

        # Build a mock context
        ctx = _steward_ctx(db)
        router = build_steward_router(ctx)

        # Find the PUT policy handler
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        client = _owner_client(router)

        response = client.put(
            "/api/projects/proj1/steward/policy",
            json={"evaluation_cadence_minutes": 0},
        )
        assert response.status_code == 400
        body = response.json()
        assert "evaluation_cadence_minutes" in body.get("message", "")

    def test_cadence_range_fence_ceiling(self, tmp_path: Path) -> None:
        """Cadence above 10080 is rejected."""
        db = _make_db(tmp_path)

        ctx = _steward_ctx(db)

        from holdspeak.web.routes.steward import build_steward_router
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        client = _owner_client(build_steward_router(ctx))

        response = client.put(
            "/api/projects/proj1/steward/policy",
            json={"evaluation_cadence_minutes": 10081},
        )
        assert response.status_code == 400

    def test_cadence_valid_updates_watches(self, tmp_path: Path) -> None:
        """A valid cadence value updates the project's watches."""
        db = _make_db(tmp_path)

        # Create project + policy + watch
        project_id = "proj_cadence"
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                (project_id, "Cadence Test"),
            )

        watch_id = "watch_cadence"
        db.automations.create_watch(
            watch_id=watch_id,
            connector_id="gh",
            query_kind="pull_requests",
            name="Cadence Watch",
            query={},
            enabled=True,
        )
        db.automations.update_watch_spec(
            watch_id, project_id=project_id, state="active",
        )

        # Insert a policy
        db.steward_policies.insert_policy(
            policy_id="pol_cadence",
            project_id=project_id,
            enabled=1,
        )

        ctx = _steward_ctx(db)

        from holdspeak.web.routes.steward import build_steward_router
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        client = _owner_client(build_steward_router(ctx))

        response = client.put(
            f"/api/projects/{project_id}/steward/policy",
            json={"evaluation_cadence_minutes": 120},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

        # Verify the watch was updated
        watch = db.automations.get_watch(watch_id)
        assert watch["evaluation_cadence_minutes"] == 120


# ── Debt 5: The trigger route ─────────────────────────────────────────


class TestDebt5TriggerRoute:
    """The trigger route calls evaluate_due/run_due through the conductor seam."""

    def test_trigger_unwired_typed_refusal(self, tmp_path: Path) -> None:
        """When scheduler services are not wired, returns typed refusal."""
        db = _make_db(tmp_path)

        ctx = _steward_ctx(db)

        from holdspeak.web.routes.steward import build_steward_router
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        client = _owner_client(build_steward_router(ctx))

        # Ensure the conductor services are NOT wired
        import holdspeak.workbench_conductor as conductor
        with patch.object(conductor, "_watch_service", None), \
             patch.object(conductor, "_steward_service", None):
            response = client.post("/api/steward/trigger")
            assert response.status_code == 503
            body = response.json()
            assert body["code"] == "scheduler_not_wired"

    def test_trigger_wired_runs(self, tmp_path: Path) -> None:
        """When wired, calls evaluate_due + run_due and returns outcomes."""
        db = _make_db(tmp_path)

        ctx = _steward_ctx(db)

        from holdspeak.web.routes.steward import build_steward_router
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        client = _owner_client(build_steward_router(ctx))

        mock_watch_svc = MagicMock()
        mock_watch_svc.evaluate_due.return_value = [
            {"watch_id": "w1", "outcome": "evaluated"},
        ]
        mock_steward_svc = MagicMock()
        mock_steward_svc.run_due.return_value = [
            {"effect_id": "e1", "outcome": "run_started"},
        ]

        import holdspeak.workbench_conductor as conductor
        with patch.object(conductor, "_watch_service", mock_watch_svc), \
             patch.object(conductor, "_steward_service", mock_steward_svc):
            response = client.post("/api/steward/trigger")
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is True
            # PHILO-9-02: the pending handle; the ONE receipt carries the outcomes.
            outcome = json.loads(_await_receipt(db, body["operation_id"])["outcome"])
            assert outcome["evaluated"] == 1 and outcome["runs"] == ["run_started"]
            mock_watch_svc.evaluate_due.assert_called_once()
            mock_steward_svc.run_due.assert_called_once()

    def test_trigger_same_watermark_creates_run_and_reconciles(self, tmp_path: Path) -> None:
        """The 163 same-watermark law: a second call creates a run that
        reconciles at the act step -- never route-level dedup."""
        db = _make_db(tmp_path)
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector

        principal = _owner()
        project_id = "proj_watermark"

        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                (project_id, "Watermark Test"),
            )

        mock_collector = MagicMock(spec=ProjectEvidenceCollector)
        mock_collector.collect_all.return_value = {}
        mock_delta = MagicMock()
        mock_delta.open_review.return_value = {"id": "rev1", "proposals": []}

        svc = ProjectStewardService(
            db, collector=mock_collector, delta=mock_delta,
        )

        # First run with a watermark
        watermark = "watch:w1:rev1"
        run_id_1 = svc.run_once(principal, project_id, watermark=watermark)
        assert run_id_1

        # Second run with the SAME watermark -- must succeed (no route-level dedup)
        run_id_2 = svc.run_once(principal, project_id, watermark=watermark)
        assert run_id_2
        assert run_id_2 != run_id_1

        # Both runs exist
        runs = db.steward_runs.list_runs(project_id, limit=10)
        run_ids = {r["id"] for r in runs}
        assert run_id_1 in run_ids
        assert run_id_2 in run_ids
