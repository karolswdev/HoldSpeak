"""HS-200-02 — the loaded runtime identity, the owner lock, the diagnoses.

Contract C1: diagnostics identify the loaded backend build, frontend build,
process start, opaque database identity, schema and configuration revision;
a later Git checkout cannot change what an already running process reports;
two processes cannot silently own the same scheduled work.

State-level proof lives here. The real-service flows — the HTTP surfaces, two
actual processes on one database, backup → upgrade → restore → reopen — live in
``tests/integration/test_phase200_runtime_identity.py``.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from holdspeak import runtime_identity as ri
from holdspeak import runtime_lock as rl


@pytest.fixture(autouse=True)
def _fresh_capture():
    """Every test captures its own identity; none leaks into the next."""
    ri.reset_runtime_identity()
    rl.release_database()
    yield
    ri.reset_runtime_identity()
    rl.release_database()


def _stamp(directory: Path, build_id: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ri.BUILD_STAMP_NAME
    path.write_text(json.dumps({"build_id": build_id}), encoding="utf-8")
    return path


def _make_db(path: Path, version: int = 76) -> Path:
    import sqlite3

    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("CREATE TABLE schema_version (version INTEGER)")
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (int(version),))
        conn.commit()
    finally:
        conn.close()
    return path


# ── Capture once ─────────────────────────────────────────────────────


def test_identity_carries_every_c1_field(tmp_path, monkeypatch):
    """C1's six identity axes are all present and populated."""
    bundle = tmp_path / "_built"
    _stamp(bundle, "bundle-aaa")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = _make_db(tmp_path / "holdspeak.db")

    identity = ri.capture_runtime_identity(db_path=db, force=True)

    assert identity.backend_version  # the package version
    assert identity.backend_revision  # a sha, or the honest "unknown"
    assert identity.process_start
    assert identity.pid == os.getpid()
    assert identity.frontend_build == "bundle-aaa"
    assert identity.database_id and len(identity.database_id) == 16
    assert identity.schema_version_expected is not None
    assert identity.schema_version_loaded == 76
    assert identity.config_revision


def test_a_later_checkout_cannot_change_a_running_identity(tmp_path, monkeypatch):
    """The C1 law: capture once. Rebuild the bundle — the process does not move."""
    bundle = tmp_path / "_built"
    _stamp(bundle, "build-at-start")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = _make_db(tmp_path / "holdspeak.db")

    first = ri.capture_runtime_identity(db_path=db, force=True)
    assert first.frontend_build == "build-at-start"

    # The checkout moves under the running process.
    _stamp(bundle, "build-after-checkout")
    monkeypatch.setenv("HOLDSPEAK_BACKEND_REVISION", "deadbeefdeadbeef")

    again = ri.current_runtime_identity()
    assert again is first
    assert again.frontend_build == "build-at-start"
    assert again.backend_revision != "deadbeefdeadbeef"


def test_capture_is_idempotent_without_force(tmp_path, monkeypatch):
    bundle = tmp_path / "_built"
    _stamp(bundle, "one")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = _make_db(tmp_path / "holdspeak.db")

    first = ri.capture_runtime_identity(db_path=db, force=True)
    second = ri.capture_runtime_identity(db_path=tmp_path / "other.db")
    assert second is first


# ── The ordinary surface hides the path and the pid ──────────────────


def test_public_dict_drops_path_and_pid(tmp_path, monkeypatch):
    """C1: detailed process and filesystem information stays in diagnostics."""
    bundle = tmp_path / "_built"
    _stamp(bundle, "x")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = _make_db(tmp_path / "holdspeak.db")
    identity = ri.capture_runtime_identity(db_path=db, force=True)

    public = identity.public_dict()
    assert "database_path" not in public
    assert "pid" not in public
    assert public["database_id"] == identity.database_id
    assert str(tmp_path) not in json.dumps(public)


def test_database_identity_is_opaque_and_stable(tmp_path):
    a = _make_db(tmp_path / "a.db")
    b = _make_db(tmp_path / "b.db")

    first = ri.database_identity(a)
    assert first == ri.database_identity(a)
    assert first != ri.database_identity(b)
    assert "a.db" not in first and str(tmp_path) not in first


def test_config_revision_moves_with_the_file(tmp_path):
    cfg = tmp_path / "config.json"
    assert ri.config_revision(cfg) == ri.UNKNOWN
    cfg.write_text('{"a": 1}', encoding="utf-8")
    one = ri.config_revision(cfg)
    cfg.write_text('{"a": 2}', encoding="utf-8")
    assert ri.config_revision(cfg) != one
    # A digest, never the content: no configured value survives in it.
    assert "1" not in one or len(one) == 16


# ── Diagnoses ────────────────────────────────────────────────────────


def test_matching_bundle_and_schema_produce_no_diagnosis(tmp_path, monkeypatch):
    bundle = tmp_path / "_built"
    _stamp(bundle, "same")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    from holdspeak.db.schema import SCHEMA_VERSION

    db = _make_db(tmp_path / "holdspeak.db", SCHEMA_VERSION)
    identity = ri.capture_runtime_identity(db_path=db, force=True)

    assert ri.diagnose(identity, bundle_dir=bundle, db_path=db, ownership={"held": True}) == []


def test_stale_bundle_when_the_disk_moved_under_the_process(tmp_path, monkeypatch):
    bundle = tmp_path / "_built"
    _stamp(bundle, "loaded")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    from holdspeak.db.schema import SCHEMA_VERSION

    db = _make_db(tmp_path / "holdspeak.db", SCHEMA_VERSION)
    identity = ri.capture_runtime_identity(db_path=db, force=True)
    _stamp(bundle, "rebuilt")

    findings = ri.diagnose(identity, bundle_dir=bundle, db_path=db, ownership={"held": True})
    assert [f["token"] for f in findings] == [ri.STALE_BUNDLE]
    assert findings[0]["loaded"] == "loaded"
    assert findings[0]["on_disk"] == "rebuilt"


def test_stale_bundle_when_no_stamp_exists_at_all(tmp_path, monkeypatch):
    bundle = tmp_path / "_built"
    bundle.mkdir(parents=True)
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    from holdspeak.db.schema import SCHEMA_VERSION

    db = _make_db(tmp_path / "holdspeak.db", SCHEMA_VERSION)
    identity = ri.capture_runtime_identity(db_path=db, force=True)

    findings = ri.diagnose(identity, bundle_dir=bundle, db_path=db, ownership={"held": True})
    assert [f["token"] for f in findings] == [ri.STALE_BUNDLE]
    assert findings[0]["on_disk"] == ""


@pytest.mark.parametrize(
    "delta,token",
    [(1, ri.SCHEMA_AHEAD), (-1, ri.SCHEMA_BEHIND)],
)
def test_schema_mismatch_names_its_direction(tmp_path, monkeypatch, delta, token):
    bundle = tmp_path / "_built"
    _stamp(bundle, "same")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    from holdspeak.db.schema import SCHEMA_VERSION

    db = _make_db(tmp_path / "holdspeak.db", SCHEMA_VERSION + delta)
    identity = ri.capture_runtime_identity(db_path=db, force=True)

    findings = ri.diagnose(identity, bundle_dir=bundle, db_path=db, ownership={"held": True})
    assert [f["token"] for f in findings] == [token]
    assert findings[0]["expected"] == SCHEMA_VERSION
    assert findings[0]["loaded"] == SCHEMA_VERSION + delta


def test_two_runtimes_diagnosis_names_the_owner(tmp_path, monkeypatch):
    bundle = tmp_path / "_built"
    _stamp(bundle, "same")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    from holdspeak.db.schema import SCHEMA_VERSION

    db = _make_db(tmp_path / "holdspeak.db", SCHEMA_VERSION)
    identity = ri.capture_runtime_identity(db_path=db, force=True)

    findings = ri.diagnose(
        identity,
        bundle_dir=bundle,
        db_path=db,
        ownership={"held": False, "owner": {"pid": 4242, "port": 49353, "process_start": "T"}},
    )
    assert [f["token"] for f in findings] == [ri.TWO_RUNTIMES]
    assert findings[0]["owner_pid"] == 4242
    assert findings[0]["owner_port"] == 49353


def test_unknown_ownership_is_not_a_two_runtimes_finding(tmp_path, monkeypatch):
    """A process that never claimed is unknown, not refused. No false alarm."""
    bundle = tmp_path / "_built"
    _stamp(bundle, "same")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    from holdspeak.db.schema import SCHEMA_VERSION

    db = _make_db(tmp_path / "holdspeak.db", SCHEMA_VERSION)
    identity = ri.capture_runtime_identity(db_path=db, force=True)

    snapshot = rl.ownership_snapshot()
    assert snapshot["held"] is None
    findings = ri.diagnose(identity, bundle_dir=bundle, db_path=db, ownership=snapshot)
    assert findings == []


def test_identity_report_hides_details_on_the_ordinary_surface(tmp_path, monkeypatch):
    bundle = tmp_path / "_built"
    _stamp(bundle, "loaded")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    from holdspeak.db.schema import SCHEMA_VERSION

    db = _make_db(tmp_path / "holdspeak.db", SCHEMA_VERSION)
    ri.capture_runtime_identity(db_path=db, force=True)
    _stamp(bundle, "rebuilt")

    ordinary = ri.identity_report(detailed=False, bundle_dir=bundle, db_path=db)
    assert ordinary["repair"] == [ri.STALE_BUNDLE]
    assert "database_path" not in ordinary["identity"]
    assert "diagnoses" not in ordinary and "ownership" not in ordinary

    detailed = ri.identity_report(detailed=True, bundle_dir=bundle, db_path=db)
    assert detailed["identity"]["database_path"] == str(db)
    assert detailed["diagnoses"][0]["detail"]
    assert detailed["bundle_on_disk"] == "rebuilt"


# ── The owner lock ───────────────────────────────────────────────────


def test_one_lock_is_exclusive_and_names_its_owner(tmp_path):
    db = _make_db(tmp_path / "holdspeak.db")
    first = rl.DatabaseOwnerLock(db)
    assert first.acquire(port=49353, host="127.0.0.1") is True
    assert first.held

    second = rl.DatabaseOwnerLock(db)
    assert second.acquire(port=54644) is False
    assert not second.held

    owner = second.owner()
    assert owner is not None
    assert owner["pid"] == os.getpid()
    assert owner["port"] == 49353
    assert owner["alive"] is True

    first.release()
    assert second.acquire() is True
    second.release()


def test_a_dead_claim_is_stale_and_reclaimable(tmp_path):
    """flock releases on process death, so a crashed hub leaves no live claim."""
    db = _make_db(tmp_path / "holdspeak.db")
    rl.owner_lock_path(db).write_text(
        json.dumps({"pid": 999_999, "port": 1, "process_start": "old"}), encoding="utf-8"
    )
    stale = rl.read_owner(db)
    assert stale is not None and stale["alive"] is False

    lock = rl.DatabaseOwnerLock(db)
    assert lock.acquire(port=2) is True
    assert (rl.read_owner(db) or {})["pid"] == os.getpid()
    lock.release()


def test_a_process_never_refuses_itself(tmp_path):
    """One process, one claim. flock refuses a second descriptor in the SAME
    process, so a naive re-claim would make a hub report TWO RUNTIMES against
    itself (caught live by tests/unit/test_web_runtime.py)."""
    db = _make_db(tmp_path / "holdspeak.db")

    first = rl.claim_database(db, port=49353)
    assert first.held is True

    again = rl.claim_database(db, port=49353)
    assert again is first
    assert again.held is True
    assert (rl.read_owner(db) or {})["pid"] == os.getpid()

    rl.release_database()
    assert rl.ownership_snapshot()["held"] is None


def test_release_is_safe_when_never_held(tmp_path):
    lock = rl.DatabaseOwnerLock(tmp_path / "holdspeak.db")
    lock.release()
    assert not lock.held
    assert lock.owner() is None


def test_refusal_message_is_a_specific_diagnosis(tmp_path):
    db = tmp_path / "holdspeak.db"
    message = rl.refusal_message(db, {"pid": 63921, "port": 54644, "host": "127.0.0.1", "process_start": "S"})
    assert message.startswith(ri.TWO_RUNTIMES)
    assert "63921" in message and "54644" in message


def test_allow_unowned_reads_the_hatch(monkeypatch):
    monkeypatch.delenv(rl.ALLOW_UNOWNED_ENV, raising=False)
    assert rl.allow_unowned() is False
    monkeypatch.setenv(rl.ALLOW_UNOWNED_ENV, "0")
    assert rl.allow_unowned() is False
    monkeypatch.setenv(rl.ALLOW_UNOWNED_ENV, "1")
    assert rl.allow_unowned() is True


# ── The sweep gate ───────────────────────────────────────────────────


class _SweepProbe:
    """The gate under test, with the sweeps replaced by recorders."""

    def __init__(self, owns: bool) -> None:
        self.owns_database = owns
        self.cadence_thread = None
        self.heartbeat_started = False

    _cadence_enabled = staticmethod(lambda: True)
    _cadence_loop = staticmethod(lambda: None)

    def _start_heartbeat_thread(self) -> None:
        self.heartbeat_started = True


def test_only_the_database_owner_runs_the_sweeps():
    """C1: two processes cannot silently own the same scheduled work."""
    from holdspeak.web_runtime import WebRuntime

    owner = _SweepProbe(owns=True)
    WebRuntime._start_scheduled_work(owner)
    assert owner.heartbeat_started is True
    assert owner.cadence_thread is not None
    owner.cadence_thread.join(timeout=1.0)

    tenant = _SweepProbe(owns=False)
    WebRuntime._start_scheduled_work(tenant)
    assert tenant.heartbeat_started is False
    assert tenant.cadence_thread is None


# ── Two real processes ───────────────────────────────────────────────


_CHILD = """
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, {repo!r})
from holdspeak import runtime_lock as rl
db = Path(sys.argv[1])
lock = rl.DatabaseOwnerLock(db)
held = lock.acquire(port=int(sys.argv[2]))
print(json.dumps({{"pid": os.getpid(), "held": held, "owner": lock.owner()}}), flush=True)
if held:
    time.sleep(float(sys.argv[3]))
"""


def test_two_real_processes_and_exactly_one_owns_the_database(tmp_path):
    """The live 2026-09-06 condition, reproduced: two hubs, one database file."""
    repo = str(Path(__file__).resolve().parents[2])
    db = _make_db(tmp_path / "holdspeak.db")
    script = _CHILD.format(repo=repo)

    first = subprocess.Popen(
        [sys.executable, "-c", script, str(db), "49353", "20"],
        stdout=subprocess.PIPE, text=True,
    )
    try:
        assert first.stdout is not None
        held_first = json.loads(first.stdout.readline())
        assert held_first["held"] is True

        second = subprocess.run(
            [sys.executable, "-c", script, str(db), "54644", "0"],
            capture_output=True, text=True, timeout=60,
        )
        held_second = json.loads(second.stdout.strip().splitlines()[-1])
        assert held_second["held"] is False
        assert held_second["owner"]["pid"] == held_first["pid"]
        assert held_second["owner"]["port"] == 49353
        assert held_second["owner"]["alive"] is True
    finally:
        first.terminate()
        first.wait(timeout=20)

    # The dead owner's claim releases with the process: the next hub takes it.
    after = rl.DatabaseOwnerLock(db)
    assert after.acquire(port=1) is True
    after.release()
