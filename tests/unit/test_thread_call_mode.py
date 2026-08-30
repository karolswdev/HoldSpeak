"""HS-154-03 -- call_mode: schema reconcile, PATCH toggle, frame, real coordinator.

Acceptance criteria:
1. Reconcile: a pre-change-DDL DB gains call_mode default 0, rows intact.
2. PATCH toggles + validates (400 on non-0/1); GET returns it; the frame fires.
3. A real-coordinator turn on a call_mode=1 thread emits THINKING transition frames.
"""
from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.db.schema import SCHEMA_SQL
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_service import ThreadService
from holdspeak.services.errors import ValidationError

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


# ---------------------------------------------------------------------------
# 1. Schema reconcile — the 153 pattern
# ---------------------------------------------------------------------------


class TestCallModeReconcile:
    """Adding call_mode to an existing DB via the generic reconcile."""

    @staticmethod
    def _pre_change_schema() -> str:
        """Return the SCHEMA_SQL with call_mode removed from threads."""
        # Build a schema without the call_mode column
        lines = SCHEMA_SQL.split("\n")
        result = []
        for line in lines:
            if "call_mode" in line and "INTEGER NOT NULL DEFAULT 0" in line:
                continue
            result.append(line)
        return "\n".join(result)

    @staticmethod
    def _old_db(tmp_path: Path) -> sqlite3.Connection:
        """Create a DB with the pre-change schema + some thread rows."""
        conn = sqlite3.connect(str(tmp_path / "pre_change.db"))
        conn.row_factory = sqlite3.Row
        conn.executescript(TestCallModeReconcile._pre_change_schema())
        # Insert a thread row (without call_mode column)
        now = time.time()
        conn.execute(
            """INSERT INTO threads
               (id, title, recipe_id, profile_override, directory_id,
                parent_thread_id, status_line, token_in, token_out,
                created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            ("th_old_1", "Old Thread", "", "", "", "", "", 100, 200, now, now),
        )
        conn.execute(
            """INSERT INTO threads
               (id, title, recipe_id, profile_override, directory_id,
                parent_thread_id, status_line, token_in, token_out,
                created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            ("th_old_2", "Another Thread", "recipe-a", "", "", "", "", 50, 75, now, now),
        )
        conn.commit()
        return conn

    def test_pre_change_db_has_no_call_mode(self, tmp_path: Path) -> None:
        """Precondition: the old schema has no call_mode column."""
        conn = self._old_db(tmp_path)
        cols = [row[1] for row in conn.execute("PRAGMA table_info(threads)")]
        assert "call_mode" not in cols
        conn.close()

    def test_reconcile_adds_call_mode_default_0(self, tmp_path: Path) -> None:
        """After reconcile, call_mode exists with default 0, old rows intact."""
        from holdspeak.db.reconcile import reconcile_schema

        conn = self._old_db(tmp_path)
        changed = reconcile_schema(conn)
        assert changed is True

        # Column exists
        cols = [row[1] for row in conn.execute("PRAGMA table_info(threads)")]
        assert "call_mode" in cols

        # Old rows have default 0
        rows = conn.execute(
            "SELECT id, title, call_mode, token_in, token_out FROM threads ORDER BY id"
        ).fetchall()
        assert len(rows) == 2
        assert (rows[0]["id"], rows[0]["call_mode"]) == ("th_old_1", 0)
        assert (rows[0]["token_in"], rows[0]["token_out"]) == (100, 200)
        assert (rows[1]["id"], rows[1]["call_mode"]) == ("th_old_2", 0)
        assert rows[1]["title"] == "Another Thread"
        conn.close()

    def test_reconcile_is_idempotent(self, tmp_path: Path) -> None:
        """Running reconcile twice is a no-op the second time."""
        from holdspeak.db.reconcile import reconcile_schema

        conn = self._old_db(tmp_path)
        reconcile_schema(conn)
        second = reconcile_schema(conn)
        assert second is False
        conn.close()


# ---------------------------------------------------------------------------
# 2. PATCH toggle + GET + frame
# ---------------------------------------------------------------------------


class TestCallModePatch:
    """PATCH {call_mode} through ThreadService.patch."""

    @staticmethod
    def _svc(tmp_path: Path):
        db = Database(tmp_path / "patch.db")
        broadcasts: list[tuple[str, dict]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
        )
        return svc, db, broadcasts

    def test_new_thread_has_call_mode_0(self, tmp_path: Path) -> None:
        svc, db, _ = self._svc(tmp_path)
        result = svc.create(title="Fresh")
        assert result["call_mode"] == 0

    def test_patch_call_mode_1(self, tmp_path: Path) -> None:
        svc, db, broadcasts = self._svc(tmp_path)
        t = svc.create(title="Toggle")
        result = svc.patch(t["id"], call_mode=1)
        assert result["call_mode"] == 1
        # Frame emitted
        frames = [(ft, d) for ft, d in broadcasts if ft == "thread_call_state"]
        assert len(frames) == 1
        assert frames[0][1]["state"] == "listening"
        assert frames[0][1]["thread_id"] == t["id"]

    def test_patch_call_mode_0(self, tmp_path: Path) -> None:
        svc, db, broadcasts = self._svc(tmp_path)
        t = svc.create(title="Toggle Off")
        svc.patch(t["id"], call_mode=1)
        broadcasts.clear()
        result = svc.patch(t["id"], call_mode=0)
        assert result["call_mode"] == 0
        frames = [(ft, d) for ft, d in broadcasts if ft == "thread_call_state"]
        assert len(frames) == 1
        assert frames[0][1]["state"] == "off"

    def test_patch_same_value_no_frame(self, tmp_path: Path) -> None:
        """Patching to the same value emits no frame."""
        svc, db, broadcasts = self._svc(tmp_path)
        t = svc.create(title="No Change")
        svc.patch(t["id"], call_mode=0)
        frames = [(ft, d) for ft, d in broadcasts if ft == "thread_call_state"]
        assert len(frames) == 0

    def test_patch_invalid_value_400(self, tmp_path: Path) -> None:
        svc, db, _ = self._svc(tmp_path)
        t = svc.create(title="Invalid")
        with pytest.raises(ValidationError, match="call_mode must be 0 or 1"):
            svc.patch(t["id"], call_mode=2)
        with pytest.raises(ValidationError, match="call_mode must be 0 or 1"):
            svc.patch(t["id"], call_mode=-1)

    def test_get_returns_call_mode(self, tmp_path: Path) -> None:
        svc, db, _ = self._svc(tmp_path)
        t = svc.create(title="Get Test")
        svc.patch(t["id"], call_mode=1)
        got = svc.get(t["id"])
        assert got["call_mode"] == 1


# ---------------------------------------------------------------------------
# 3. Real coordinator emits THINKING frame
# ---------------------------------------------------------------------------


class TestCallModeRealCoordinatorThinking:
    """A real coordinator turn on a call_mode=1 thread emits THINKING frames."""

    @staticmethod
    def _hub(tmp_path: Path):
        """Boot a real hub, return (db, svc, broadcasts, owner, server, old_home)."""
        import os
        import tempfile
        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
        from holdspeak.kernel.inference_stream import Delta

        home = Path(tempfile.mkdtemp(prefix="hs154-call-"))
        old_home = os.environ.get("HOME", "")
        os.environ["HOME"] = str(home)
        config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
        db_core.DEFAULT_DB_PATH = tmp_path / "holdspeak.db"
        reset_database()

        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
            ),
        )
        url = server.start()
        db = get_database()

        # Profile + assignment for chat.turn
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        owner = Principal(PrincipalKind.OWNER, "call-owner")
        profile_id = "call-mode-test"
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "call-assign",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()

        class _FakeEngine:
            active_provider = "fake-call"
            active_model = "call-model"
            def run_prompt_stream(self, *, messages=None, temperature=None,
                                  max_tokens=None, **kw):
                yield Delta(kind="text", text="Heard you. ")
                yield Delta(kind="usage", meta={"prompt_tokens": 1, "completion_tokens": 1})
                yield Delta(kind="done")
            def run_prompt_messages(self, **kw):
                return "Heard you. "
            def run_prompt(self, **kw):
                return "Heard you. "

        engine = _FakeEngine()
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

        from holdspeak.mcp.tools import dispatch as mcp_dispatch
        broadcasts: list[tuple[str, dict]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
            broker=broker,
            tool_dispatch_fn=mcp_dispatch,
        )
        return db, svc, broadcasts, owner, server, old_home

    @staticmethod
    def _wait_done(db, msg_id, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = db.threads.get_message(msg_id)
            if msg and not msg.streaming:
                return
            time.sleep(0.2)
        pytest.fail("Turn did not complete within timeout")

    def test_call_mode_1_turn_emits_thinking_then_listening(self, tmp_path: Path) -> None:
        """A turn on a call_mode=1 thread emits THINKING at start and LISTENING at done."""
        from holdspeak.db import reset_database

        db, svc, broadcasts, owner, server, old_home = self._hub(tmp_path)
        try:
            thread = svc.create(title="Call Mode Turn")
            # Set call_mode=1
            svc.patch(thread["id"], call_mode=1)
            broadcasts.clear()

            result = asyncio.run(svc.start_turn(owner, thread["id"], "Test utterance"))
            self._wait_done(db, result["assistant_message_id"])

            call_frames = [(ft, d) for ft, d in broadcasts if ft == "thread_call_state"]
            assert len(call_frames) >= 2, f"Expected >=2 call_state frames, got {call_frames}"
            # First frame: thinking (at turn start)
            assert call_frames[0][1]["state"] == "thinking"
            assert call_frames[0][1]["thread_id"] == thread["id"]
            # Last frame: listening (at turn done, since call_mode is still 1)
            assert call_frames[-1][1]["state"] == "listening"
            assert call_frames[-1][1]["thread_id"] == thread["id"]

            server.stop()
        finally:
            import os
            os.environ["HOME"] = old_home
            reset_database()

    def test_call_mode_0_turn_emits_no_call_frames(self, tmp_path: Path) -> None:
        """A turn on a call_mode=0 thread emits no call_state frames."""
        from holdspeak.db import reset_database

        db, svc, broadcasts, owner, server, old_home = self._hub(tmp_path)
        try:
            thread = svc.create(title="No Call Mode")
            broadcasts.clear()

            result = asyncio.run(svc.start_turn(owner, thread["id"], "Regular turn"))
            self._wait_done(db, result["assistant_message_id"])

            call_frames = [(ft, d) for ft, d in broadcasts if ft == "thread_call_state"]
            assert len(call_frames) == 0, f"Expected 0 call_state frames, got {call_frames}"

            server.stop()
        finally:
            import os
            os.environ["HOME"] = old_home
            reset_database()
