"""HS-200-45: ONE composition root — MCP is a caller of it, like an HTTP request.

The fences here reproduce the defects the 2026-09-13 operational-surface audit
measured (§9, §10.1), each one written so it FAILS on the pre-fix tree:

* :class:`TestMcpWriteReachesTheDesk` — an MCP write put no frame on the bus,
  because ``tools.dispatch`` rebuilt ``PrimitiveService`` from
  ``get_database()`` with no ``broadcast``. Pre-fix this file's assertion
  ``frames == [...]`` saw ``[]``.
* :class:`TestContendedWrite` — ``journal_mode`` was ``delete`` and no
  ``busy_timeout`` was ever set, so a second writer meeting a held write
  transaction raised ``database is locked`` at once.
* :class:`TestLoopbackOwnerAdmission` — ``POST /api/mcp`` answered 404 to the
  hub's own local transport whenever ``remote.streamable_http_enabled`` was
  off, which left the stdio sidecar no lawful path to the hub at all.

The two process-level fences (a real sidecar with no hub; a real sidecar
against a real hub) live in
``tests/integration/test_phase200_one_composition_root_processes.py``.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.runtime import composition

OWNER = Principal(PrincipalKind.OWNER, "owner")


# ── helpers ─────────────────────────────────────────────────────────────


def _hub_app(db: Database, frames: list[tuple[str, Any]], *, remote_enabled: bool,
             client_host: str = "127.0.0.1", owner_token: str = "owner-tok-123"):
    """A FastAPI app with the real /api/mcp route over a real composition root.

    The composition step is `composition.install_from_web_context`, which is
    the SAME function `MeetingWebServer._create_app` calls — not a hand-kept
    copy of it. So what this fence proves about the route is what holds in the
    hub: the route composes nothing itself, and the dispatch it invokes
    resolves the hub's instances.
    """
    from fastapi import FastAPI

    from holdspeak.principals import AgentCredentialStore, UNAUTHENTICATED, derive_owner
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.mcp_http import build_mcp_http_router
    from holdspeak.web_auth import extract_request_token

    ctx = WebContext(
        get_state=lambda: {},
        broadcast=lambda message_type, data: frames.append((message_type, data)),
    )
    composition.install_from_web_context(ctx, db=db, observer=None)

    app = FastAPI()
    store = AgentCredentialStore()
    app.state.agent_credentials = store
    app.state.owner_token = owner_token
    app.state._remote_settings = {"enabled": remote_enabled}

    @app.middleware("http")
    async def _auth(request, call_next):  # noqa: ANN001
        request.scope["client"] = (client_host, 50000)
        token = extract_request_token(
            authorization=request.headers.get("authorization"),
            header_token=request.headers.get("x-holdspeak-token"),
            query_token=request.query_params.get("token"),
        )
        principal = derive_owner(token, owner_token) or store.derive(token) or UNAUTHENTICATED
        request.state.principal = principal
        return await call_next(request)

    app.include_router(build_mcp_http_router(ctx))
    return app


def _call(client, name: str, arguments: dict[str, Any], *, rpc_id: int = 1):
    return client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0",
            "id": rpc_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        headers={"Authorization": "Bearer owner-tok-123"},
    )


# ── (a) the no-broadcast defect ─────────────────────────────────────────


class TestMcpWriteReachesTheDesk:
    """An MCP write broadcasts exactly as the equivalent HTTP write does."""

    def test_desk_create_over_mcp_emits_one_desk_changed_frame(self, tmp_path: Path) -> None:
        from starlette.testclient import TestClient

        db = Database(tmp_path / "mcp-broadcast.db")
        frames: list[tuple[str, Any]] = []
        app = _hub_app(db, frames, remote_enabled=True)
        client = TestClient(app)

        resp = _call(client, "desk.create", {"kind": "notes", "data": {"title": "From MCP"}})
        assert resp.status_code == 200, resp.text
        assert resp.json()["result"]["isError"] is False, resp.text

        changed = [f for f in frames if f[0] == "desk_changed"]
        assert len(changed) == 1, f"expected ONE desk_changed frame, saw {frames!r}"
        payload = changed[0][1]
        assert payload["kind"] == "note"
        assert payload["op"] == "create"
        assert payload["id"]
        # HS-174-04 tags origin before dispatch; the frame carries who wrote.
        assert payload["origin"]

    def test_desk_update_over_mcp_emits_one_frame(self, tmp_path: Path) -> None:
        from starlette.testclient import TestClient

        db = Database(tmp_path / "mcp-broadcast-update.db")
        frames: list[tuple[str, Any]] = []
        app = _hub_app(db, frames, remote_enabled=True)
        client = TestClient(app)

        created = _call(client, "desk.create", {"kind": "notes", "data": {"title": "a"}})
        import json as _json

        note_id = _json.loads(created.json()["result"]["content"][0]["text"])["id"]
        frames.clear()

        resp = _call(
            client, "desk.update",
            {"kind": "notes", "id": note_id, "data": {"title": "b"}}, rpc_id=2,
        )
        assert resp.status_code == 200, resp.text
        changed = [f for f in frames if f[0] == "desk_changed"]
        assert len(changed) == 1, f"expected ONE frame, saw {frames!r}"
        assert changed[0][1] == {
            # The frame names the SINGULAR primitive kind, not the tool's
            # plural selector — it is about one object.
            "kind": "note", "id": note_id, "op": "update",
            "origin": changed[0][1]["origin"],
        }

    def test_mcp_and_http_write_through_the_same_instance(self, tmp_path: Path) -> None:
        """The point of the story: one root, not two.

        Pre-fix, `tools.dispatch` built its own `PrimitiveService` from
        `get_database()` while the hub held a different one. Here the object
        MCP dispatch resolves and the object the primitive HTTP routes resolve
        are the same object.
        """
        from holdspeak.mcp import tools as mcp_tools
        from holdspeak.web.context import WebContext

        db = Database(tmp_path / "one-root.db")
        frames: list[tuple[str, Any]] = []
        ctx = WebContext(
            get_state=lambda: {},
            broadcast=lambda t, d: frames.append((t, d)),
        )
        root = composition.install_from_web_context(ctx, db=db, observer=None)

        assert ctx.primitive_service is root.primitive_service
        assert composition.service(
            "primitive_service", lambda: pytest.fail("built a second instance")
        ) is root.primitive_service
        # And the accessor MCP modules use hands back the hub's handle, never
        # opening a second one.
        assert composition.db_or(lambda: pytest.fail("opened a second database")) is db
        assert mcp_tools.dispatch("desk.list", {"kind": "notes"}, OWNER) == []


# ── (b) the contended write ─────────────────────────────────────────────


class TestContendedWrite:
    """Two `Database` objects over one file; contention does not kill a peer.

    A note on what actually failed pre-fix, measured rather than assumed. The
    absence of ``busy_timeout`` turned out NOT to be the hazard: Python's
    ``sqlite3.connect`` already applies ``timeout=5.0``, so a peer meeting a
    briefly-held write lock already waited rather than raising. Two probes
    written to fail pre-fix passed pre-fix for that reason (a second writer
    behind a 300 ms write transaction; a reader behind an uncommitted write,
    which rollback-journal mode permits anyway).

    ``journal_mode = delete`` was the real hazard, and
    :meth:`test_a_writer_is_not_blocked_by_a_held_read` is the case that
    reproduces it: in rollback-journal mode a writer needs an EXCLUSIVE lock to
    commit, so a reader holding a SHARED lock stalls it until the busy timeout
    expires and then it raises ``sqlite3.OperationalError: database is locked``.
    Under WAL a reader never blocks a writer. ``busy_timeout = 5000`` stays as
    an explicit statement of a value we were relying on by accident.
    """

    @pytest.mark.timeout(60)
    def test_a_writer_is_not_blocked_by_a_held_read(self, tmp_path: Path) -> None:
        """The contention that raised `database is locked` on the pre-fix tree."""
        path = tmp_path / "held-read.db"
        reader_db = Database(path)
        writer_db = Database(path)

        holding = threading.Event()
        release = threading.Event()
        errors: list[BaseException] = []

        def hold_a_read_transaction() -> None:
            try:
                with reader_db._connection() as conn:
                    conn.execute("BEGIN")
                    conn.execute("SELECT count(*) FROM notes").fetchone()
                    holding.set()
                    release.wait(20.0)
            except BaseException as exc:  # pragma: no cover - reported below
                errors.append(exc)
                holding.set()

        reader = threading.Thread(target=hold_a_read_transaction, daemon=True)
        reader.start()
        assert holding.wait(5.0), "the reader never took its transaction"
        assert not errors, errors

        # The read is held for 8 s -- past the 5 s busy timeout, so a writer
        # that has to wait for it does not merely stall, it fails.
        threading.Timer(8.0, release.set).start()
        started = time.monotonic()
        with writer_db._connection() as conn:
            conn.execute(
                "INSERT INTO notes (id, title, body_markdown) VALUES (?, ?, ?)",
                ("note_peer", "peer", ""),
            )
        elapsed = time.monotonic() - started
        release.set()
        reader.join(5.0)

        assert not errors, errors
        assert elapsed < 1.0, (
            f"the writer waited {elapsed * 1000:.0f} ms behind a held read "
            "transaction; under WAL it should not wait at all"
        )

    def test_second_writer_waits_instead_of_raising_database_is_locked(
        self, tmp_path: Path
    ) -> None:
        """A REGRESSION guard, not a reproduction: this passed pre-fix too.

        Kept because it is the shape the story's charter named, and because it
        is the property the explicit `busy_timeout` now guarantees rather than
        inherits from a library default that could change.
        """
        path = tmp_path / "contended.db"
        a = Database(path)
        b = Database(path)

        holding = threading.Event()
        release = threading.Event()
        errors: list[BaseException] = []

        def hold_a_write_transaction() -> None:
            try:
                with a._connection() as conn:
                    conn.execute("BEGIN IMMEDIATE")
                    conn.execute(
                        "INSERT INTO notes (id, title, body_markdown) VALUES (?, ?, ?)",
                        ("note_hold", "held", ""),
                    )
                    holding.set()
                    release.wait(5.0)
            except BaseException as exc:  # pragma: no cover - reported below
                errors.append(exc)
                holding.set()

        writer = threading.Thread(target=hold_a_write_transaction, daemon=True)
        writer.start()
        assert holding.wait(5.0), "thread A never took its write transaction"
        assert not errors, errors

        # Thread A holds the write lock for 300 ms after this point. Pre-fix
        # (journal_mode=delete, no busy_timeout) this raised
        # `sqlite3.OperationalError: database is locked` immediately.
        threading.Timer(0.3, release.set).start()
        started = time.monotonic()
        with b._connection() as conn:
            conn.execute(
                "INSERT INTO notes (id, title, body_markdown) VALUES (?, ?, ?)",
                ("note_peer", "peer", ""),
            )
        elapsed = time.monotonic() - started
        writer.join(5.0)

        assert not errors, errors
        assert elapsed < 5.0
        rows = {row["id"] for row in
                Database(path)._conn_factory().__enter__().execute("SELECT id FROM notes")}
        assert {"note_hold", "note_peer"} <= rows

    def test_the_pragmas_match_the_module_docstring(self, tmp_path: Path) -> None:
        """`db/connection.py:3` claimed "WAL pragmas" and set only foreign_keys."""
        db = Database(tmp_path / "pragmas.db")
        with db._connection() as conn:
            assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
            assert int(conn.execute("PRAGMA busy_timeout").fetchone()[0]) == 5000
            assert int(conn.execute("PRAGMA foreign_keys").fetchone()[0]) == 1

    def test_an_existing_delete_mode_database_migrates_to_wal(self, tmp_path: Path) -> None:
        """A database created before this story opens as WAL with its rows intact."""
        path = tmp_path / "legacy.db"
        legacy = sqlite3.connect(str(path))
        legacy.execute("PRAGMA journal_mode = delete")
        legacy.execute("CREATE TABLE keepsake (id TEXT PRIMARY KEY)")
        legacy.execute("INSERT INTO keepsake VALUES ('kept')")
        legacy.commit()
        assert legacy.execute("PRAGMA journal_mode").fetchone()[0].lower() == "delete"
        legacy.close()

        db = Database(path)
        with db._connection() as conn:
            assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
            assert conn.execute("SELECT id FROM keepsake").fetchone()[0] == "kept"


# ── (e) the loopback-owner admission ────────────────────────────────────


class TestLoopbackOwnerAdmission:
    """The remote flag governs the REMOTE listener, not the local transport."""

    def test_loopback_owner_is_admitted_with_the_remote_flag_off(
        self, tmp_path: Path
    ) -> None:
        from starlette.testclient import TestClient

        db = Database(tmp_path / "loopback-owner.db")
        frames: list[tuple[str, Any]] = []
        app = _hub_app(db, frames, remote_enabled=False, client_host="127.0.0.1")
        client = TestClient(app)

        resp = client.post(
            "/api/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"Authorization": "Bearer owner-tok-123"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"jsonrpc": "2.0", "id": 1, "result": {}}

    def test_a_loopback_owner_can_write_with_the_flag_off(self, tmp_path: Path) -> None:
        """Admission is not cosmetic: the sidecar's whole path runs on it."""
        from starlette.testclient import TestClient

        db = Database(tmp_path / "loopback-owner-write.db")
        frames: list[tuple[str, Any]] = []
        client = TestClient(_hub_app(db, frames, remote_enabled=False))

        resp = _call(client, "desk.create", {"kind": "notes", "data": {"title": "local"}})
        assert resp.status_code == 200, resp.text
        assert [f for f in frames if f[0] == "desk_changed"]

    def test_a_non_loopback_request_still_gets_404_with_the_flag_off(
        self, tmp_path: Path
    ) -> None:
        """HS-174's rule is unchanged for anything that is not a local owner."""
        from starlette.testclient import TestClient

        db = Database(tmp_path / "remote-off.db")
        app = _hub_app(db, [], remote_enabled=False, client_host="203.0.113.9")
        client = TestClient(app)

        resp = client.post(
            "/api/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
            headers={"Authorization": "Bearer owner-tok-123"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"] == "streamable_http_not_enabled"


# ── the refusal outside a hub ───────────────────────────────────────────


class TestNoRuntimeRefusal:
    """Improvising a second root is what made the sidecar a second writer."""

    def test_current_refuses_with_no_root_and_no_standalone(self, monkeypatch) -> None:
        monkeypatch.delenv(composition.STANDALONE_ENV, raising=False)
        composition.uninstall()
        try:
            with pytest.raises(composition.NoRuntimeError) as excinfo:
                composition.current()
        finally:
            composition.install(composition.bare(label="pytest"))
        message = str(excinfo.value)
        assert "holdspeak" in message
        # One sentence, naming the remedy or the owner that holds the file.
        assert "holdspeak web" in message or "owns" in message

    def test_db_or_never_opens_a_database_when_it_refuses(self, monkeypatch) -> None:
        monkeypatch.delenv(composition.STANDALONE_ENV, raising=False)
        composition.uninstall()
        opened: list[str] = []
        try:
            with pytest.raises(composition.NoRuntimeError):
                composition.db_or(lambda: opened.append("opened"))
        finally:
            composition.install(composition.bare(label="pytest"))
        assert opened == []

    def test_standalone_env_permits_a_bare_root_that_shares_no_handle(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv(composition.STANDALONE_ENV, "1")
        composition.uninstall()
        try:
            root = composition.current()
            assert root.bare_root is True
            assert root.db is None
            # Each module keeps its own accessor — the pre-fix behaviour, which
            # is what a diagnosis session wants.
            assert composition.db_or(lambda: "module-handle") == "module-handle"
        finally:
            composition.install(composition.bare(label="pytest"))


# ── the honest refusals (R6) ────────────────────────────────────────────


class TestHonestRefusals:
    """A tool that cannot do its job says so as an error, not as success."""

    def test_steward_trigger_raises_instead_of_returning_success_false(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from holdspeak.mcp import server as mcp_server
        from holdspeak.mcp.families import project as project_family

        db = Database(tmp_path / "steward-refusal.db")
        monkeypatch.setattr(project_family, "get_database", lambda: db)
        import holdspeak.workbench_conductor as conductor

        monkeypatch.setattr(conductor, "_watch_service", None, raising=False)
        monkeypatch.setattr(conductor, "_steward_service", None, raising=False)

        response = mcp_server.handle_message_for_principal(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
             "params": {"name": "project.steward.trigger", "arguments": {}}},
            OWNER,
        )
        assert response is not None
        result = response["result"]
        assert result["isError"] is True, result
        text = result["content"][0]["text"]
        assert "scheduler_not_wired" in text
        assert "hub" in text and "Nothing was evaluated" in text

    def test_start_capture_names_why_it_cannot_run_here(self, tmp_path: Path) -> None:
        """Not `validation_error` — the input was fine; the controller is absent."""
        from holdspeak.mcp import tools as mcp_tools

        db = Database(tmp_path / "capture-refusal.db")
        composition.install(composition.bare(db=db, label="pytest-capture"))
        try:
            with pytest.raises(mcp_tools.ToolError) as excinfo:
                mcp_tools.dispatch("meeting.start_capture", {}, OWNER)
        finally:
            composition.install(composition.bare(label="pytest"))
        message = str(excinfo.value)
        assert "holdspeak web" in message
        assert "capture" in message.lower()
        assert "nothing to configure" in message.lower()


# ── counsel-on-built (2026-09-17): the P0 and the P1s ──────────────────


class TestRestoreRefusesUnderALiveOwner:
    """P0: `holdspeak restore` with the hub running bricked the database.

    `restore_database` unlinked `-wal`/`-shm` beneath the hub's live
    per-thread WAL connections; the next fresh reader and the next hub failed
    with `disk I/O error`. The refusal lives in `restore_database` itself, so
    every caller inherits it.
    """

    def test_restore_refuses_and_touches_nothing_while_an_owner_is_alive(
        self, tmp_path: Path
    ) -> None:
        from holdspeak.db.core import DatabaseInUse, backup_database, restore_database
        from holdspeak.runtime_lock import claim_database, release_database

        path = tmp_path / "holdspeak.db"
        hub = Database(path)
        with hub._connection() as conn:
            conn.execute("INSERT INTO notes (id, title, body_markdown) VALUES ('before','b','')")
        backup = backup_database(path)
        with hub._connection() as conn:
            conn.execute("INSERT INTO notes (id, title, body_markdown) VALUES ('after','a','')")
        before_bytes = path.read_bytes()
        wal = path.with_name(path.name + "-wal")
        wal_before = wal.read_bytes() if wal.exists() else None

        claim_database(path, port=12345)  # a live owner: this pid
        try:
            with pytest.raises(DatabaseInUse) as excinfo:
                restore_database(backup, path)
        finally:
            release_database()
        message = str(excinfo.value)
        assert "holdspeak web" in message and str(os.getpid()) in message
        assert "stop `holdspeak web` first" in message

        assert path.read_bytes() == before_bytes
        assert (wal.read_bytes() if wal.exists() else None) == wal_before
        # The live hub keeps working, and so does a fresh reader.
        with hub._connection() as conn:
            conn.execute("INSERT INTO notes (id, title, body_markdown) VALUES ('later','l','')")
        fresh = sqlite3.connect(str(path))
        assert {r[0] for r in fresh.execute("SELECT id FROM notes")} >= {"before", "after", "later"}
        fresh.close()
        hub.close()

    def test_restore_refuses_an_unlocked_open_connection_too(self, tmp_path: Path) -> None:
        """Counsel's probe held the database open WITHOUT the owner lock; the
        lock check alone let it through and bricked the file. SQLite's own
        exclusivity rule (leaving WAL) is the second gate."""
        from holdspeak.db.core import DatabaseInUse, backup_database, restore_database

        path = tmp_path / "holdspeak.db"
        hub = Database(path)
        with hub._connection() as conn:
            conn.execute("INSERT INTO notes (id, title, body_markdown) VALUES ('before','b','')")
        backup = backup_database(path)
        with hub._connection() as conn:
            conn.execute("INSERT INTO notes (id, title, body_markdown) VALUES ('after','a','')")

        with pytest.raises(DatabaseInUse, match="another process has"):
            restore_database(backup, path)

        with hub._connection() as conn:
            conn.execute("INSERT INTO notes (id, title, body_markdown) VALUES ('later','l','')")
        fresh = sqlite3.connect(str(path))
        assert {r[0] for r in fresh.execute("SELECT id FROM notes")} == {"before", "after", "later"}
        assert fresh.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        fresh.close()
        hub.close()

    def test_offline_restore_still_works(self, tmp_path: Path) -> None:
        from holdspeak.db.core import backup_database, restore_database

        path = tmp_path / "holdspeak.db"
        db = Database(path)
        with db._connection() as conn:
            conn.execute("INSERT INTO notes (id, title, body_markdown) VALUES ('before','b','')")
        backup = backup_database(path)
        with db._connection() as conn:
            conn.execute("INSERT INTO notes (id, title, body_markdown) VALUES ('after','a','')")
        db.close()

        safety = restore_database(backup, path)
        assert safety is not None and safety.exists()
        assert not path.with_name(path.name + "-wal").exists()
        again = sqlite3.connect(str(path))
        assert [r[0] for r in again.execute("SELECT id FROM notes")] == ["before"]
        assert again.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        again.close()

    def test_the_cli_surfaces_the_refusal_and_exits_non_zero(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        from types import SimpleNamespace

        import holdspeak.commands.backup as backup_cmd
        from holdspeak.db.core import backup_database
        from holdspeak.runtime_lock import claim_database, release_database

        path = tmp_path / "holdspeak.db"
        Database(path).close()
        backup = backup_database(path)
        monkeypatch.setattr(backup_cmd, "DEFAULT_DB_PATH", path)
        claim_database(path, port=1)
        try:
            code = backup_cmd.run_restore_command(SimpleNamespace(backup=str(backup), yes=True))
        finally:
            release_database()
        out = capsys.readouterr().out
        assert code == 1
        assert "Restore refused" in out and "stop `holdspeak web` first" in out


class TestNotificationIsARealNoContent:
    """P1-1: `JSONResponse(None, 204)` put a `null` body into a 204 and uvicorn
    raised "Response content longer than Content-Length" on every sidecar
    handshake."""

    def test_notification_yields_an_empty_204(self, tmp_path: Path) -> None:
        from starlette.testclient import TestClient

        db = Database(tmp_path / "notify.db")
        client = TestClient(_hub_app(db, [], remote_enabled=True))
        resp = client.post(
            "/api/mcp",
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            headers={"Authorization": "Bearer owner-tok-123"},
        )
        assert resp.status_code == 204
        assert resp.content == b""
        assert resp.headers.get("content-length", "0") == "0"


class TestEveryAskedServiceIsCarriedAndLive:
    """P1-3: `runtime_service("ask_service")` named a field the root did not
    carry, so the hub built a bare AskService while the comment claimed the
    hub's. Now `service()` rejects an unknown name, and every name a family
    asks for is a field that the hub's installed root fills."""

    @staticmethod
    def _asked_names() -> set[str]:
        import ast

        root = Path(__file__).resolve().parents[2] / "holdspeak" / "mcp"
        names: set[str] = set()
        for source in root.rglob("*.py"):
            for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
                if (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id == "runtime_service"
                        and node.args and isinstance(node.args[0], ast.Constant)):
                    names.add(str(node.args[0].value))
        return names

    def test_an_unknown_name_is_a_programming_error(self) -> None:
        with pytest.raises(KeyError, match="no field 'nope_service'"):
            composition.service("nope_service", lambda: object())

    def test_every_asked_name_is_a_field(self) -> None:
        asked = self._asked_names()
        assert asked, "no runtime_service(...) call found under holdspeak/mcp"
        assert asked <= composition.SERVICE_FIELDS, asked - composition.SERVICE_FIELDS

    @pytest.mark.timeout(120)
    def test_every_asked_name_is_live_in_the_hubs_root(self, tmp_path: Path, monkeypatch) -> None:
        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
        reset_database()
        server = MeetingWebServer(
            WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
            auth_token="t",
        )
        try:
            server._create_app()  # installs the root; never serves
            root = composition.installed()
            assert root is not None and not root.bare_root
            missing = sorted(n for n in self._asked_names() if getattr(root, n, None) is None)
            assert missing == [], f"hub root leaves these asked-for services None: {missing}"
            # And the one counsel caught is the hub's Ask transport, not a bare one.
            assert getattr(root.ask_service, "_broadcast", None) is not None
        finally:
            reset_database()


class TestNoBareAccessorInMcp:
    """P2-iii: the autouse bare root masks `NoRuntimeError` in unit tests, so
    an accessor call that bypasses the root would never be noticed there.
    This fence reads the source instead."""

    def test_every_accessor_call_under_mcp_goes_through_the_root(self) -> None:
        import ast

        root = Path(__file__).resolve().parents[2] / "holdspeak" / "mcp"
        offenders: list[str] = []
        for source in sorted(root.rglob("*.py")):
            tree = ast.parse(source.read_text(encoding="utf-8"))
            allowed: set[int] = set()
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id in {"db_or", "observer_or"}):
                    for arg in node.args:
                        allowed.add(id(arg))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = node.func.attr if isinstance(node.func, ast.Attribute) else (
                        node.func.id if isinstance(node.func, ast.Name) else "")
                    if name in {"get_database", "get_observer"}:
                        offenders.append(f"{source.relative_to(root.parent)}:{node.lineno} calls {name}()")
        assert offenders == [], "\n".join(offenders)
