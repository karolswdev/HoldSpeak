"""HS-200-02 — runtime identity over the real HTTP surfaces, and the restore rehearsal.

Contract C1: diagnostics identify the loaded parts; the Desk shows a compact
repair state; upgrade creates a recoverable backup through the existing
mechanism; restore is first rehearsed against a copy.

Every database here is a throwaway under ``tmp_path``. The owner's database is
never opened, copied, or named.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak import runtime_identity as ri
from holdspeak import runtime_lock as rl
from holdspeak.db import Database, reset_database
from holdspeak.db.core import backup_database, restore_database, read_schema_version
from holdspeak.db.reconcile import reconcile_schema
from holdspeak.db.schema import SCHEMA_VERSION
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """An isolated HOME, config and database for every test."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".config" / "holdspeak" / "config.json")
    import holdspeak.db.core as db_core

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    ri.reset_runtime_identity()
    rl.release_database()
    yield
    reset_database()
    ri.reset_runtime_identity()
    rl.release_database()


def _stamp(directory: Path, build_id: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ri.BUILD_STAMP_NAME).write_text(
        json.dumps({"build_id": build_id}), encoding="utf-8"
    )


def _client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    return TestClient(server.app)


# ── The served identity ──────────────────────────────────────────────


def test_identity_route_serves_every_c1_field(tmp_path, monkeypatch):
    bundle = tmp_path / "_built"
    _stamp(bundle, "served-build")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = tmp_path / "holdspeak.db"
    Database(db)
    ri.capture_runtime_identity(db_path=db, force=True)

    body = _client().get("/api/system/identity").json()

    identity = body["identity"]
    for field in (
        "backend_version", "backend_revision", "process_start", "pid",
        "frontend_build", "database_id", "schema_version_expected",
        "schema_version_loaded", "config_revision",
    ):
        assert identity.get(field) is not None, field
    assert identity["pid"] == os.getpid()
    assert identity["frontend_build"] == "served-build"
    assert identity["schema_version_loaded"] == SCHEMA_VERSION
    # The diagnostics surface, and only it, carries the filesystem path.
    assert identity["database_path"] == str(db)
    assert "ownership" in body and "diagnoses" in body


def test_setup_status_carries_the_compact_block_without_the_path(tmp_path, monkeypatch):
    """The ordinary Desk surface: repair tokens, no path, no pid."""
    bundle = tmp_path / "_built"
    _stamp(bundle, "loaded")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = tmp_path / "holdspeak.db"
    Database(db)
    ri.capture_runtime_identity(db_path=db, force=True)
    _stamp(bundle, "rebuilt")  # the checkout moves under the running process

    body = _client().get("/api/setup/status").json()

    block = body["runtime_identity"]
    assert block["repair"] == [ri.STALE_BUNDLE]
    assert "database_path" not in block["identity"]
    assert "pid" not in block["identity"]
    assert str(tmp_path) not in json.dumps(block)
    assert block["identity"]["frontend_build"] == "loaded"


def test_a_later_checkout_does_not_move_the_served_identity(tmp_path, monkeypatch):
    """The C1 law, over HTTP: the running process keeps reporting what it loaded."""
    bundle = tmp_path / "_built"
    _stamp(bundle, "at-start")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = tmp_path / "holdspeak.db"
    Database(db)
    ri.capture_runtime_identity(db_path=db, force=True)
    client = _client()

    before = client.get("/api/system/identity").json()["identity"]
    _stamp(bundle, "after-checkout")
    after = client.get("/api/system/identity").json()

    assert after["identity"] == before
    assert after["bundle_on_disk"] == "after-checkout"
    assert ri.STALE_BUNDLE in after["repair"]


def test_schema_mismatch_is_served_as_its_own_token(tmp_path, monkeypatch):
    bundle = tmp_path / "_built"
    _stamp(bundle, "same")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = tmp_path / "holdspeak.db"
    Database(db)
    ri.capture_runtime_identity(db_path=db, force=True)
    reset_database()
    conn = sqlite3.connect(str(db))
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION + 3,))
    conn.commit()
    conn.close()

    body = _client().get("/api/system/identity").json()
    assert body["repair"] == [ri.SCHEMA_AHEAD]
    assert body["diagnoses"][0]["expected"] == SCHEMA_VERSION


# ── Two runtimes on one database ─────────────────────────────────────


_HOLDER = """
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, {repo!r})
from holdspeak import runtime_lock as rl
lock = rl.DatabaseOwnerLock(Path(sys.argv[1]))
held = lock.acquire(port=49353, host="127.0.0.1")
print(json.dumps({{"pid": os.getpid(), "held": held}}), flush=True)
time.sleep(120)
"""


@pytest.fixture
def owning_process(tmp_path):
    """A real second process holding the database owner lock."""
    repo = str(Path(__file__).resolve().parents[2])
    db = tmp_path / "holdspeak.db"
    Database(db)
    reset_database()
    proc = subprocess.Popen(
        [sys.executable, "-c", _HOLDER.format(repo=repo), str(db)],
        stdout=subprocess.PIPE, text=True,
    )
    assert proc.stdout is not None
    first = json.loads(proc.stdout.readline())
    assert first["held"] is True
    try:
        yield SimpleNamespace(pid=first["pid"], db=db)
    finally:
        proc.terminate()
        proc.wait(timeout=20)


def _claim_probe():
    from datetime import datetime

    return SimpleNamespace(runtime_started_at=datetime.now(), owns_database=False)


def test_a_second_hub_refuses_to_start(owning_process, capsys, monkeypatch):
    """The chosen behaviour: refuse. C10 forbids a multi-writer SQLite arrangement."""
    from holdspeak.web_runtime import WebRuntime

    monkeypatch.delenv(rl.ALLOW_UNOWNED_ENV, raising=False)
    probe = _claim_probe()

    with pytest.raises(SystemExit) as exit_info:
        WebRuntime._claim_database(probe)

    assert exit_info.value.code == 1
    err = capsys.readouterr().err
    assert ri.TWO_RUNTIMES in err
    assert str(owning_process.pid) in err
    assert "49353" in err
    assert probe.owns_database is False


def test_the_hatch_starts_without_ownership_and_flies_the_token(
    owning_process, monkeypatch, tmp_path
):
    """HOLDSPEAK_ALLOW_UNOWNED_DB: start, sweeps OFF, TWO RUNTIMES on the surface."""
    from holdspeak.web_runtime import WebRuntime

    monkeypatch.setenv(rl.ALLOW_UNOWNED_ENV, "1")
    bundle = tmp_path / "_built"
    _stamp(bundle, "same")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)

    probe = _claim_probe()
    WebRuntime._claim_database(probe)  # does not raise
    assert probe.owns_database is False

    ri.capture_runtime_identity(db_path=owning_process.db, force=True)
    body = _client().get("/api/system/identity").json()

    assert ri.TWO_RUNTIMES in body["repair"]
    assert body["owns_database"] is False
    assert body["ownership"]["owner"]["pid"] == owning_process.pid
    assert body["diagnoses"][0]["owner_port"] == 49353


def test_the_owner_keeps_the_claim_and_reports_no_finding(tmp_path, monkeypatch):
    from holdspeak.web_runtime import WebRuntime

    bundle = tmp_path / "_built"
    _stamp(bundle, "same")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = tmp_path / "holdspeak.db"
    Database(db)
    reset_database()

    probe = _claim_probe()
    WebRuntime._claim_database(probe)
    assert probe.owns_database is True

    ri.capture_runtime_identity(db_path=db, force=True)
    body = _client().get("/api/system/identity").json()
    assert body["owns_database"] is True
    assert ri.TWO_RUNTIMES not in body["repair"]


# ── Backup → upgrade → restore → reopen, on a copy ───────────────────


def _seed(path: Path) -> None:
    """A meeting and its permitted attachment (an artifact), through raw SQL."""
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            "INSERT OR REPLACE INTO meetings (id, title, started_at) "
            "VALUES ('m-restore', 'The rehearsal meeting', datetime('now'))"
        )
        conn.execute(
            "INSERT OR REPLACE INTO artifacts "
            "(id, meeting_id, origin, artifact_type, title, body_markdown) "
            "VALUES ('a-restore', 'm-restore', 'meeting', 'summary', "
            "'The rehearsal attachment', '# kept')"
        )
        conn.commit()
    finally:
        conn.close()


def _read_back(path: Path) -> tuple[str | None, str | None]:
    conn = sqlite3.connect(str(path))
    try:
        meeting = conn.execute("SELECT title FROM meetings WHERE id='m-restore'").fetchone()
        artifact = conn.execute(
            "SELECT body_markdown FROM artifacts WHERE id='a-restore'"
        ).fetchone()
        return (meeting[0] if meeting else None, artifact[0] if artifact else None)
    finally:
        conn.close()


def _make_an_older_copy(path: Path) -> None:
    """Shape the copy the way schema 75 held it (before HS-176-02).

    75 → 76 added ``dictation_journal.corrections_applied``. Removing the column
    and re-stamping 75 is exactly the database an upgrade has to carry forward.
    """
    conn = sqlite3.connect(str(path))
    try:
        conn.execute("ALTER TABLE dictation_journal DROP COLUMN corrections_applied")
        conn.execute("DELETE FROM schema_version")
        conn.execute("INSERT INTO schema_version (version) VALUES (75)")
        conn.commit()
    finally:
        conn.close()


def _columns(path: Path, table: str) -> set[str]:
    conn = sqlite3.connect(str(path))
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def test_backup_upgrade_restore_reopen_on_a_copy(tmp_path):
    """P200-A02, rehearsed on a copy — never on the selected database itself."""
    original = tmp_path / "holdspeak.db"
    Database(original)
    _seed(original)
    reset_database()

    # The rehearsal runs on a COPY. The original is the control.
    copy = tmp_path / "rehearsal" / "holdspeak.db"
    copy.parent.mkdir(parents=True)
    copy.write_bytes(original.read_bytes())
    _make_an_older_copy(copy)
    assert read_schema_version(copy) == 75
    assert "corrections_applied" not in _columns(copy, "dictation_journal")

    # 1. Back up through the existing mechanism, before the upgrade.
    backup = backup_database(copy)
    assert backup.exists() and backup.parent == copy.parent
    assert read_schema_version(backup) == 75

    # 2. The supported upgrade: the declarative reconcile, 75 → 76.
    conn = sqlite3.connect(str(copy))
    try:
        reconcile_schema(conn)
        conn.commit()
    finally:
        conn.close()
    assert read_schema_version(copy) == SCHEMA_VERSION == 76
    assert "corrections_applied" in _columns(copy, "dictation_journal")
    assert _read_back(copy) == ("The rehearsal meeting", "# kept")

    # 3. Restore the pre-upgrade backup. The current database is snapshotted first.
    safety = restore_database(backup, copy)
    assert safety is not None and safety.exists()
    assert read_schema_version(safety) == SCHEMA_VERSION
    assert read_schema_version(copy) == 75

    # 4. Reopen the restored copy through the product. It upgrades on open, and
    #    the meeting and its attachment both come back.
    Database(copy)
    reset_database()
    assert read_schema_version(copy) == SCHEMA_VERSION
    assert _read_back(copy) == ("The rehearsal meeting", "# kept")

    # The control never moved.
    assert read_schema_version(original) == SCHEMA_VERSION


def test_the_backup_covers_the_main_database_only(tmp_path):
    """The protected-store boundary, stated as a test.

    ``backup_database`` snapshots ONE SQLite file. The encrypted People store
    (``people.v1.sqlite3``, the sole authority for confidential People payloads)
    is a separate file with separate keys, and the Keychain is not a file at
    all. Neither is inside the backup, and neither is touched by a restore.
    """
    db = tmp_path / "holdspeak.db"
    Database(db)
    _seed(db)
    reset_database()

    from holdspeak.people.store import DEFAULT_PEOPLE_DB_PATH

    assert DEFAULT_PEOPLE_DB_PATH.name == "people.v1.sqlite3"
    people = db.parent / DEFAULT_PEOPLE_DB_PATH.name
    people.write_bytes(b"encrypted-people-store-stand-in")
    before = hashlib.sha256(people.read_bytes()).hexdigest()

    backup = backup_database(db)
    assert backup != people
    assert backup.name.startswith(db.name)
    # The People store is not inside the snapshot: it is a separate database.
    with sqlite3.connect(str(backup)) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "meetings" in tables
    assert not any("people_secret" in name for name in tables)

    restore_database(backup, db)
    assert hashlib.sha256(people.read_bytes()).hexdigest() == before


def test_an_interrupted_restore_leaves_the_original_intact(tmp_path):
    """A restore that cannot complete never becomes the step that loses data."""
    db = tmp_path / "holdspeak.db"
    Database(db)
    _seed(db)
    reset_database()
    before = hashlib.sha256(db.read_bytes()).hexdigest()

    # (a) The backup file is gone mid-restore.
    with pytest.raises(ValueError, match="not found"):
        restore_database(tmp_path / "vanished.bak", db)
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before

    # (b) The backup is not a HoldSpeak database (a truncated copy).
    truncated = tmp_path / "truncated.bak"
    truncated.write_bytes(db.read_bytes()[:512])
    with pytest.raises(ValueError):
        restore_database(truncated, db)
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before

    # (c) A readable SQLite file that is somebody else's database.
    foreign = tmp_path / "foreign.bak"
    conn = sqlite3.connect(str(foreign))
    conn.execute("CREATE TABLE notes (id TEXT)")
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="meetings"):
        restore_database(foreign, db)
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before

    # Nothing above wrote a safety snapshot, and the records still open.
    assert list(db.parent.glob(f"{db.name}.*.bak")) == []
    assert _read_back(db) == ("The rehearsal meeting", "# kept")
