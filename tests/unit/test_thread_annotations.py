"""HS-153-04 -- Annotations: draft parts, promote on send, assembler prefix,
real coordinator payload capture, reconcile of the ``draft`` column.
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError, ValidationError
from holdspeak.services.thread_service import ThreadService

OWNER = Principal(PrincipalKind.OWNER, "owner-session")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "annotations.db")


@pytest.fixture
def broadcasts() -> list[tuple[str, dict]]:
    return []


@pytest.fixture
def broadcast_fn(broadcasts):
    def _broadcast(msg_type: str, data: Any) -> None:
        broadcasts.append((msg_type, data))
    return _broadcast


class FakeBroker:
    """Minimal broker for non-coordinator tests."""

    def __init__(self, *, output: str = "Reply from assistant"):
        self._output = output

    @property
    def inference_adoption_service(self) -> "FakeAdoptionService":
        return FakeAdoptionService(output=self._output)

    @property
    def inference_runner(self) -> None:
        return None


class FakeAdoptionService:
    def __init__(self, output: str = "Reply from assistant"):
        self._output = output

    def admit(self, principal, **kw):
        return {
            "status": "admitted",
            "route_plan": {
                "entries": [{"boundary": "same_device", "profile_id": "test"}],
                "egress_scope": "same_device",
                "model_id": "test-model",
            },
        }


class FakeRunner:
    def __init__(self, output: str = "Reply from assistant"):
        self._output = output

    def run(self, route_plan, payload, *, on_delta, invocation_id="", **kw):
        from holdspeak.kernel.inference_stream import Delta
        on_delta(Delta(kind="text", text=self._output))
        on_delta(Delta(kind="usage", meta={"prompt_tokens": 5, "completion_tokens": 3}))
        on_delta(Delta(kind="done"))


@pytest.fixture
def service(db, broadcast_fn):
    broker = FakeBroker()
    return ThreadService(db, broadcast=broadcast_fn, broker=broker)


# ---------------------------------------------------------------------------
# Repository layer
# ---------------------------------------------------------------------------

class TestDraftParts:
    def test_append_draft_part(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Annotate test")
        msg = db.threads.append_message(thread.id, role="user")
        part = db.threads.append_part(
            msg.id, kind="annotation", text="test note", draft=True,
            meta_json=json.dumps({"source": "owner", "quote": "hello", "comment": "yes"}),
        )
        assert part.draft is True
        assert part.kind == "annotation"

    def test_draft_message_for_returns_draft(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Annotate test")
        msg = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(
            msg.id, kind="annotation", text="note", draft=True,
            meta_json=json.dumps({"source": "owner", "quote": "q", "comment": "c"}),
        )
        dm = db.threads.draft_message_for(thread.id)
        assert dm is not None
        assert dm.id == msg.id

    def test_draft_message_for_returns_none_when_promoted(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Annotate test")
        msg = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(
            msg.id, kind="annotation", text="note", draft=True,
        )
        db.threads.promote_drafts(msg.id)
        dm = db.threads.draft_message_for(thread.id)
        assert dm is None

    def test_is_draft_message(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Draft check")
        msg = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(msg.id, kind="annotation", text="x", draft=True)
        assert db.threads.is_draft_message(msg.id) is True
        # After adding a non-draft part, it's no longer a pure draft.
        db.threads.append_part(msg.id, kind="text", text="y", draft=False)
        assert db.threads.is_draft_message(msg.id) is False

    def test_delete_part(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Delete test")
        msg = db.threads.append_message(thread.id, role="user")
        part = db.threads.append_part(msg.id, kind="annotation", text="note", draft=True)
        assert db.threads.delete_part(part.id) is True
        # Message should also be deleted (no remaining parts).
        assert db.threads.get_message(msg.id) is None

    def test_delete_part_keeps_message_if_others_remain(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Partial delete")
        msg = db.threads.append_message(thread.id, role="user")
        p1 = db.threads.append_part(msg.id, kind="annotation", text="a", draft=True)
        db.threads.append_part(msg.id, kind="annotation", text="b", draft=True)
        db.threads.delete_part(p1.id)
        assert db.threads.get_message(msg.id) is not None
        remaining = db.threads.get_parts(msg.id)
        assert len(remaining) == 1

    def test_promote_drafts(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Promote test")
        msg = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(msg.id, kind="annotation", text="a", draft=True)
        db.threads.append_part(msg.id, kind="annotation", text="b", draft=True)
        count = db.threads.promote_drafts(msg.id)
        assert count == 2
        parts = db.threads.get_parts(msg.id)
        for p in parts:
            assert p.draft is False

    def test_draft_parts_returns_only_draft(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Draft parts")
        msg = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(msg.id, kind="annotation", text="a", draft=True)
        db.threads.append_part(msg.id, kind="text", text="b", draft=False)
        # Not a pure draft message, so draft_parts should return empty.
        parts = db.threads.draft_parts(thread.id)
        assert len(parts) == 0

    def test_draft_parts_for_pure_draft(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Pure draft")
        msg = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(msg.id, kind="annotation", text="a", draft=True)
        db.threads.append_part(msg.id, kind="annotation", text="b", draft=True)
        parts = db.threads.draft_parts(thread.id)
        assert len(parts) == 2

    def test_second_annotation_reuses_draft_message(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Reuse draft")
        msg = db.threads.append_message(thread.id, role="user")
        db.threads.append_part(msg.id, kind="annotation", text="first", draft=True)
        dm1 = db.threads.draft_message_for(thread.id)
        # Second annotation goes on the same draft message.
        db.threads.append_part(dm1.id, kind="annotation", text="second", draft=True)
        dm2 = db.threads.draft_message_for(thread.id)
        assert dm2.id == dm1.id
        parts = db.threads.draft_parts(thread.id)
        assert len(parts) == 2


# ---------------------------------------------------------------------------
# Service layer: GET hides draft, send promotes
# ---------------------------------------------------------------------------

class TestServiceDraftAnnotations:
    def test_get_hides_draft_message_from_transcript(self, db: Database, broadcast_fn) -> None:
        broker = FakeBroker()
        svc = ThreadService(db, broadcast=broadcast_fn, broker=broker)
        thread = svc.create(title="Hide draft")
        tid = thread["id"]
        # Create a draft message with an annotation.
        msg = db.threads.append_message(tid, role="user")
        db.threads.append_part(
            msg.id, kind="annotation", text="note", draft=True,
            meta_json=json.dumps({"source": "owner", "quote": "q", "comment": "c"}),
        )
        result = svc.get(tid)
        # The draft message should not be in the transcript.
        msg_ids = [m["id"] for m in result["messages"]]
        assert msg.id not in msg_ids
        # But the draft annotations should be exposed.
        assert len(result["draft_annotations"]) == 1
        assert result["draft_annotations"][0]["id"] is not None

    def test_get_shows_promoted_message_in_transcript(self, db: Database, broadcast_fn) -> None:
        broker = FakeBroker()
        svc = ThreadService(db, broadcast=broadcast_fn, broker=broker)
        thread = svc.create(title="Promoted")
        tid = thread["id"]
        msg = db.threads.append_message(tid, role="user")
        db.threads.append_part(msg.id, kind="annotation", text="note", draft=True)
        db.threads.promote_drafts(msg.id)
        db.threads.append_part(msg.id, kind="text", text="hello")
        result = svc.get(tid)
        msg_ids = [m["id"] for m in result["messages"]]
        assert msg.id in msg_ids
        assert len(result["draft_annotations"]) == 0


# ---------------------------------------------------------------------------
# Real coordinator: annotation prefix in admitted payload
# ---------------------------------------------------------------------------

class TestRealCoordinatorAnnotationPayload:
    """Drives ThreadService through the REAL RoutedInferenceCoordinator with a
    fake engine that captures the admitted payload.  Asserts:
    - Draft annotation is promoted on send
    - The admitted payload's user content starts with the annotation prefix
    - After the turn, no draft parts remain
    """

    @staticmethod
    def _hub(tmp_path: Path):
        """Boot a real hub, seed modes, return (db, svc, payloads, owner, server, old_home)."""
        import os
        import tempfile
        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
        from holdspeak.kernel.inference_stream import Delta

        home = Path(tempfile.mkdtemp(prefix="hs153-annot-"))
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

        from holdspeak.services.thread_modes import seed_modes as _seed_modes
        _seed_modes(db)

        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        owner = Principal(PrincipalKind.OWNER, "owner-session")
        profile_id = "annotation-payload-test"
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "annot-assign",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()

        payloads: list[dict] = []

        class _CapturingEngine:
            active_provider = "capture-engine"
            active_model = "capture-model"

            def run_prompt_stream(self, *, messages=None, temperature=None,
                                  max_tokens=None, tools=None, **kw):
                payloads.append({
                    "messages": messages,
                    "tools": tools,
                    "kw": kw,
                })
                yield Delta(kind="text", text="Noted. ")
                yield Delta(kind="usage", meta={"prompt_tokens": 1, "completion_tokens": 1})
                yield Delta(kind="done")

            def run_prompt_messages(self, **kw):
                return "Noted."

            def run_prompt(self, **kw):
                return "Noted."

        engine = _CapturingEngine()
        broker.inference_runner._engine_factory = lambda _rev, **_kw: engine

        broadcasts: list[tuple[str, dict]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
            broker=broker,
        )

        return db, svc, payloads, broadcasts, owner, server, old_home

    @staticmethod
    def _wait_done(db, msg_id, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = db.threads.get_message(msg_id)
            if msg and not msg.streaming:
                return
            time.sleep(0.2)
        pytest.fail("Turn did not complete within timeout")

    def test_annotation_prefix_in_payload(self, tmp_path: Path) -> None:
        """Draft annotation -> promoted on send -> payload's user content starts
        with 'The owner annotated: ...' -> no drafts remain after."""
        from holdspeak.db import reset_database

        db, svc, payloads, broadcasts, owner, server, old_home = self._hub(tmp_path)
        try:
            thread = svc.create(title="Annotation payload test")
            tid = thread["id"]

            # Create a draft annotation.
            msg = db.threads.append_message(tid, role="user")
            db.threads.append_part(
                msg.id,
                kind="annotation",
                text='The owner annotated: «important point» — I agree with this',
                draft=True,
                meta_json=json.dumps({
                    "source": "owner",
                    "quote": "important point",
                    "comment": "I agree with this",
                    "anchor_message_id": "fake-anchor",
                }),
            )

            # Verify draft exists before send.
            draft = db.threads.draft_message_for(tid)
            assert draft is not None, "Draft message should exist before send"

            # Send a turn.
            result = asyncio.run(svc.start_turn(owner, tid, "Please elaborate"))
            self._wait_done(db, result["assistant_message_id"])

            # Verify the payload.
            assert len(payloads) >= 1, "Engine was not called"
            user_messages = [
                m for m in payloads[0]["messages"] if m["role"] == "user"
            ]
            assert len(user_messages) >= 1, "No user message in payload"
            last_user = user_messages[-1]["content"]
            assert last_user.startswith("The owner annotated:"), (
                f"User content should start with annotation prefix, got: {last_user[:80]}"
            )
            assert "«important point»" in last_user
            assert "Please elaborate" in last_user

            # Verify no draft parts remain.
            draft_after = db.threads.draft_message_for(tid)
            assert draft_after is None, "No draft message should remain after send"

            server.stop()
        finally:
            import os
            os.environ["HOME"] = old_home
            reset_database()

    def test_second_annotation_reuses_draft_before_send(self, tmp_path: Path) -> None:
        """Two annotations before Send -> same draft message -> both in payload."""
        from holdspeak.db import reset_database

        db, svc, payloads, broadcasts, owner, server, old_home = self._hub(tmp_path)
        try:
            thread = svc.create(title="Two annotations")
            tid = thread["id"]

            # First annotation.
            msg = db.threads.append_message(tid, role="user")
            db.threads.append_part(
                msg.id, kind="annotation",
                text='The owner annotated: «first» — comment one',
                draft=True,
                meta_json=json.dumps({
                    "source": "owner", "quote": "first",
                    "comment": "comment one", "anchor_message_id": "a1",
                }),
            )
            # Second annotation on the same draft.
            db.threads.append_part(
                msg.id, kind="annotation",
                text='The owner annotated: «second» — comment two',
                draft=True,
                meta_json=json.dumps({
                    "source": "owner", "quote": "second",
                    "comment": "comment two", "anchor_message_id": "a2",
                }),
            )

            result = asyncio.run(svc.start_turn(owner, tid, "Go"))
            self._wait_done(db, result["assistant_message_id"])

            assert len(payloads) >= 1
            user_messages = [
                m for m in payloads[0]["messages"] if m["role"] == "user"
            ]
            last_user = user_messages[-1]["content"]
            assert "«first»" in last_user
            assert "«second»" in last_user
            assert "Go" in last_user

            server.stop()
        finally:
            import os
            os.environ["HOME"] = old_home
            reset_database()


# ---------------------------------------------------------------------------
# Reconcile: draft column added to existing DB
# ---------------------------------------------------------------------------

class TestReconcileDraftColumn:
    def test_pre_change_ddl_gains_draft_column(self, tmp_path: Path) -> None:
        """An existing DB without the ``draft`` column gains it via reconcile,
        existing rows get default 0, and inserts with draft=1 succeed."""
        import sqlite3
        from holdspeak.db.schema import SCHEMA_SQL
        from holdspeak.db.reconcile import reconcile_schema

        db_path = tmp_path / "reconcile-draft.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")

        # Create the schema WITHOUT the draft column (simulate old DB).
        # Remove the ",\n    draft ..." line and its trailing comma.
        old_schema = SCHEMA_SQL.replace(
            "    sensitive INTEGER NOT NULL DEFAULT 0,\n    draft INTEGER NOT NULL DEFAULT 0",
            "    sensitive INTEGER NOT NULL DEFAULT 0",
        )
        conn.executescript(old_schema)

        # Insert a row into thread_message_parts to verify it survives.
        conn.execute(
            """INSERT INTO threads (id, title, recipe_id, profile_override,
               directory_id, parent_thread_id, status_line,
               token_in, token_out, created_at, updated_at)
               VALUES ('t1','Test','','','','','',0,0,1.0,1.0)"""
        )
        conn.execute(
            """INSERT INTO thread_messages (id, thread_id, role,
               created_at, updated_at)
               VALUES ('m1','t1','user',1.0,1.0)"""
        )
        conn.execute(
            """INSERT INTO thread_message_parts (id, message_id, ordinal,
               kind, text, sensitive)
               VALUES ('p1','m1',0,'text','Hello',0)"""
        )
        conn.commit()

        # Verify draft column does NOT exist yet.
        cols = {row[1] for row in conn.execute("PRAGMA table_info('thread_message_parts')")}
        assert "draft" not in cols, "Precondition: draft column should not exist"

        # Run reconcile.
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True

        # Verify draft column exists.
        cols_after = {row[1] for row in conn.execute("PRAGMA table_info('thread_message_parts')")}
        assert "draft" in cols_after, "Draft column should exist after reconcile"

        # Existing row has default draft=0.
        row = conn.execute(
            "SELECT draft FROM thread_message_parts WHERE id='p1'"
        ).fetchone()
        assert row is not None
        assert int(row["draft"]) == 0

        # New insert with draft=1 succeeds.
        conn.execute(
            """INSERT INTO thread_message_parts (id, message_id, ordinal,
               kind, text, sensitive, draft)
               VALUES ('p2','m1',1,'annotation','note',0,1)"""
        )
        conn.commit()
        row2 = conn.execute(
            "SELECT draft FROM thread_message_parts WHERE id='p2'"
        ).fetchone()
        assert int(row2["draft"]) == 1

        conn.close()
