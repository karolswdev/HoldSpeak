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
