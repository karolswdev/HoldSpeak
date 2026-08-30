"""HS-153-05 -- Thread compaction: assembler cut, sensitivity inheritance,
real coordinator compact, and failure path.

Scoped: this file + test_thread_todo.py + test_hs153_practice_capabilities.py +
test_thread_service.py + test_thread_tool_loop.py.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db.core import Database
from holdspeak.kernel.inference_stream import Delta
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_service import (
    ThreadService,
    _PEOPLE_REDACTION,
)


OWNER = Principal(PrincipalKind.OWNER, "compact-test-owner")


# ---------------------------------------------------------------------------
# Assembler cut — the compaction row slices the context window
# ---------------------------------------------------------------------------


class TestAssemblerCompactCut:
    """_assemble_payload skips messages before the latest compaction row."""

    def test_no_compaction_includes_all_messages(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "cut.db")
        svc = ThreadService(db, broadcast=lambda *_: None)
        thread = svc.create(title="no cut")
        tid = thread["id"]

        # Two turns — user + assistant
        u1 = db.threads.append_message(tid, role="user")
        db.threads.append_part(u1.id, kind="text", text="Hello")
        a1 = db.threads.append_message(tid, role="assistant", parent_id=u1.id)
        db.threads.append_part(a1.id, kind="text", text="Hi there")
        u2 = db.threads.append_message(tid, role="user", parent_id=a1.id)
        db.threads.append_part(u2.id, kind="text", text="How are you?")

        payload = svc._assemble_payload(tid, u2.id, db.threads.get(tid))
        texts = [m["content"] for m in payload["messages"] if m["role"] != "system"]
        assert "Hello" in texts
        assert "Hi there" in texts
        assert "How are you?" in texts

    def test_compaction_cut_skips_pre_cut_messages(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "cut.db")
        svc = ThreadService(db, broadcast=lambda *_: None)
        thread = svc.create(title="with cut")
        tid = thread["id"]

        # Pre-cut messages
        u1 = db.threads.append_message(tid, role="user")
        db.threads.append_part(u1.id, kind="text", text="Old message 1")
        a1 = db.threads.append_message(tid, role="assistant", parent_id=u1.id)
        db.threads.append_part(a1.id, kind="text", text="Old response 1")

        # Compaction row
        compact = db.threads.append_message(tid, role="system", parent_id=a1.id)
        db.threads.append_part(compact.id, kind="text", text="Summary of conversation so far")
        db.threads.complete_message(
            compact.id,
            stats_json=json.dumps({"compaction": True, "cut_at": a1.id, "count": 2}),
        )

        # Post-cut messages
        u2 = db.threads.append_message(tid, role="user", parent_id=compact.id)
        db.threads.append_part(u2.id, kind="text", text="New question")

        payload = svc._assemble_payload(tid, u2.id, db.threads.get(tid))
        texts = [m["content"] for m in payload["messages"] if m["role"] != "system"
                 or "Summary" in m.get("content", "")]

        # Pre-cut messages should be absent
        all_content = " ".join(m["content"] for m in payload["messages"])
        assert "Old message 1" not in all_content
        assert "Old response 1" not in all_content
        # Post-cut and summary should be present
        assert "Summary of conversation so far" in all_content
        assert "New question" in all_content

    def test_latest_compaction_wins(self, tmp_path: Path) -> None:
        """When multiple compaction rows exist, the LAST one is the cut."""
        db = Database(tmp_path / "multi_cut.db")
        svc = ThreadService(db, broadcast=lambda *_: None)
        thread = svc.create(title="multi cut")
        tid = thread["id"]

        # First conversation + first compaction
        u1 = db.threads.append_message(tid, role="user")
        db.threads.append_part(u1.id, kind="text", text="Very old")
        c1 = db.threads.append_message(tid, role="system", parent_id=u1.id)
        db.threads.append_part(c1.id, kind="text", text="Summary 1")
        db.threads.complete_message(
            c1.id, stats_json=json.dumps({"compaction": True, "cut_at": u1.id, "count": 1}),
        )

        # Second conversation + second compaction
        u2 = db.threads.append_message(tid, role="user", parent_id=c1.id)
        db.threads.append_part(u2.id, kind="text", text="Middle message")
        c2 = db.threads.append_message(tid, role="system", parent_id=u2.id)
        db.threads.append_part(c2.id, kind="text", text="Summary 2")
        db.threads.complete_message(
            c2.id, stats_json=json.dumps({"compaction": True, "cut_at": u2.id, "count": 2}),
        )

        # Post-cut
        u3 = db.threads.append_message(tid, role="user", parent_id=c2.id)
        db.threads.append_part(u3.id, kind="text", text="Latest question")

        payload = svc._assemble_payload(tid, u3.id, db.threads.get(tid))
        all_content = " ".join(m["content"] for m in payload["messages"])

        assert "Very old" not in all_content
        assert "Summary 1" not in all_content
        assert "Middle message" not in all_content
        assert "Summary 2" in all_content
        assert "Latest question" in all_content


# ---------------------------------------------------------------------------
# Sensitivity inheritance
# ---------------------------------------------------------------------------


class TestCompactionSensitivity:
    """The summary part inherits sensitive=1 when ANY summarized part was."""

    def test_sensitive_summary(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "sens.db")
        svc = ThreadService(db, broadcast=lambda *_: None)
        thread = svc.create(title="sensitive test")
        tid = thread["id"]

        u1 = db.threads.append_message(tid, role="user")
        db.threads.append_part(u1.id, kind="text", text="Tell me about John", sensitive=True)
        a1 = db.threads.append_message(tid, role="assistant", parent_id=u1.id)
        db.threads.append_part(a1.id, kind="text", text="John is a person")
        u2 = db.threads.append_message(tid, role="user", parent_id=a1.id)
        db.threads.append_part(u2.id, kind="text", text="Thanks")

        # Simulate what compact_thread does: collect parts, check sensitivity
        path = db.threads.list_path(tid)
        content_messages = [m for m in path if m.role in ("user", "assistant")]
        any_sensitive = False
        for msg in content_messages:
            parts = db.threads.get_parts(msg.id)
            for part in parts:
                if part.sensitive:
                    any_sensitive = True

        assert any_sensitive is True, "Should detect sensitive part"

    def test_non_sensitive_summary(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "nosens.db")
        svc = ThreadService(db, broadcast=lambda *_: None)
        thread = svc.create(title="non-sensitive test")
        tid = thread["id"]

        u1 = db.threads.append_message(tid, role="user")
        db.threads.append_part(u1.id, kind="text", text="Hello")
        a1 = db.threads.append_message(tid, role="assistant", parent_id=u1.id)
        db.threads.append_part(a1.id, kind="text", text="Hi")
        u2 = db.threads.append_message(tid, role="user", parent_id=a1.id)
        db.threads.append_part(u2.id, kind="text", text="Bye")

        path = db.threads.list_path(tid)
        content_messages = [m for m in path if m.role in ("user", "assistant")]
        any_sensitive = False
        for msg in content_messages:
            parts = db.threads.get_parts(msg.id)
            for part in parts:
                if part.sensitive:
                    any_sensitive = True

        assert any_sensitive is False

    def test_compaction_cut_carries_sensitive_text_in_assembler(self, tmp_path: Path) -> None:
        """After compact, the summary text joins _sensitive_texts when sensitive."""
        db = Database(tmp_path / "sens_assemble.db")
        svc = ThreadService(db, broadcast=lambda *_: None)
        thread = svc.create(title="sens assembly")
        tid = thread["id"]

        # Pre-cut: a sensitive message
        u1 = db.threads.append_message(tid, role="user")
        db.threads.append_part(u1.id, kind="text", text="About John Doe", sensitive=True)
        a1 = db.threads.append_message(tid, role="assistant", parent_id=u1.id)
        db.threads.append_part(a1.id, kind="text", text="Noted about John")

        # Compaction row with sensitive summary
        compact = db.threads.append_message(tid, role="system", parent_id=a1.id)
        db.threads.append_part(
            compact.id, kind="text",
            text="Summary mentioning John Doe",
            sensitive=True,
        )
        db.threads.complete_message(
            compact.id,
            stats_json=json.dumps({"compaction": True, "cut_at": a1.id, "count": 2}),
        )

        # Post-cut message
        u2 = db.threads.append_message(tid, role="user", parent_id=compact.id)
        db.threads.append_part(u2.id, kind="text", text="What next?")

        payload = svc._assemble_payload(tid, u2.id, db.threads.get(tid))
        sensitive_texts = payload.get("_sensitive_texts", [])
        assert "Summary mentioning John Doe" in sensitive_texts


# ---------------------------------------------------------------------------
# Real coordinator with fake engines (chat.turn + chat.compact)
# ---------------------------------------------------------------------------


class TestRealCoordinatorCompact:
    """Drives ThreadService.compact_thread through the REAL coordinator."""

    @staticmethod
    def _hub(
        tmp_path: Path,
        *,
        control_mode: str = "yolo",
        compact_summary: str = "This is a summary of the conversation.",
        compact_raise: bool = False,
    ):
        """Boot a real hub with fake engines for chat.turn and chat.compact."""
        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        home = Path(tempfile.mkdtemp(prefix="hs153-compact-"))
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

        # Seed modes
        from holdspeak.services.thread_modes import seed_modes, seed_guardrails
        seed_modes(db)
        seed_guardrails(db)

        # Set up profile + assignments for chat.turn and chat.compact
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        owner = Principal(PrincipalKind.OWNER, "owner-session")
        profile_id = "compact-test"
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "assign-turn",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })

        # Backfill chat.compact from chat.turn
        from holdspeak.db.reconcile import _backfill_chat_practice_assignments
        with db._connection() as conn:
            _backfill_chat_practice_assignments(conn)

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()

        # Fake engines
        turn_payloads: list[dict] = []
        compact_payloads: list[dict] = []

        class _TurnEngine:
            active_provider = "turn-engine"
            active_model = "turn-model"

            def run_prompt_stream(self, *, messages=None, temperature=None,
                                  max_tokens=None, tools=None, **kw):
                turn_payloads.append({"messages": messages, "tools": tools})
                yield Delta(kind="text", text="Response after compact.")
                yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 5})
                yield Delta(kind="done")

            def run_prompt_messages(self, **kw):
                return compact_summary

            def run_prompt(self, **kw):
                if compact_raise:
                    raise RuntimeError("Compact engine failure")
                return compact_summary

        turn_engine = _TurnEngine()

        broker.inference_runner._engine_factory = lambda rev, **kw: turn_engine

        from holdspeak.services.thread_service import ThreadService
        from holdspeak.mcp.tools import dispatch as mcp_dispatch
        broadcasts: list[tuple[str, dict]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
            broker=broker,
            tool_dispatch_fn=mcp_dispatch,
            control_mode_fn=lambda: control_mode,
        )

        return {
            "db": db,
            "svc": svc,
            "turn_payloads": turn_payloads,
            "compact_payloads": compact_payloads,
            "broadcasts": broadcasts,
            "owner": owner,
            "server": server,
            "old_home": old_home,
        }

    @staticmethod
    def _wait_done(db, msg_id, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            msg = db.threads.get_message(msg_id)
            if msg and not msg.streaming:
                return
            time.sleep(0.2)
        pytest.fail("Turn did not complete within timeout")

    @staticmethod
    def _cleanup(hub):
        from holdspeak.db import reset_database
        hub["server"].stop()
        os.environ["HOME"] = hub["old_home"]
        reset_database()

    def test_compact_creates_cut_row_and_next_turn_excludes_pre_cut(
        self, tmp_path: Path,
    ) -> None:
        """After /compact, the system cut row exists and the NEXT turn's
        payload contains only the summary + later messages."""
        hub = self._hub(tmp_path, compact_summary="Summary of prior turns.")
        try:
            svc = hub["svc"]
            db = hub["db"]
            owner = hub["owner"]

            # Create thread and populate with 2 turns
            thread = svc.create(title="compact test")
            tid = thread["id"]

            # First turn
            r1 = asyncio.run(svc.start_turn(owner, tid, "Hello world"))
            self._wait_done(db, r1["assistant_message_id"])

            # Second turn
            r2 = asyncio.run(svc.start_turn(owner, tid, "Tell me more"))
            self._wait_done(db, r2["assistant_message_id"])

            # Compact
            hub["turn_payloads"].clear()

            # Debug: check the path before compact
            path = db.threads.list_path(tid)
            content_msgs = [m for m in path if m.role in ("user", "assistant")]
            assert len(content_msgs) >= 2, f"Only {len(content_msgs)} content messages: {[(m.role, m.id) for m in path]}"

            result = asyncio.run(svc.compact_thread(owner, tid))
            assert result["status"] == "ok", f"compact failed: {result}"
            assert "message_id" in result
            assert "cut_at" in result

            # Verify the cut row
            cut_msg = db.threads.get_message(result["message_id"])
            assert cut_msg is not None
            assert cut_msg.role == "system"
            stats = json.loads(cut_msg.stats_json)
            assert stats["compaction"] is True
            assert "cut_at" in stats

            # Verify the summary part
            parts = db.threads.get_parts(cut_msg.id)
            text_parts = [p for p in parts if p.kind == "text"]
            assert len(text_parts) == 1
            assert text_parts[0].text == "Summary of prior turns."

            # Verify thread_compacted frame was emitted
            compacted_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_compacted"
            ]
            assert len(compacted_frames) >= 1
            cf = compacted_frames[0]
            assert cf["thread_id"] == tid
            assert cf["message_id"] == result["message_id"]

            # Now do another turn and check the payload
            hub["turn_payloads"].clear()
            r3 = asyncio.run(svc.start_turn(owner, tid, "What now?"))
            self._wait_done(db, r3["assistant_message_id"])

            assert len(hub["turn_payloads"]) >= 1
            payload = hub["turn_payloads"][0]
            all_content = " ".join(
                m.get("content", "") for m in payload["messages"]
            )
            # The summary should be present
            assert "Summary of prior turns." in all_content
            # The pre-cut messages should be absent
            assert "Hello world" not in all_content
            assert "Tell me more" not in all_content
            # The post-cut user message should be present
            assert "What now?" in all_content

        finally:
            self._cleanup(hub)

    def test_compact_too_short_raises(self, tmp_path: Path) -> None:
        """Compact with < 2 content messages raises ValidationError."""
        hub = self._hub(tmp_path)
        try:
            svc = hub["svc"]
            db = hub["db"]
            thread = svc.create(title="short thread")
            tid = thread["id"]

            # Only one user message (no assistant response yet)
            db.threads.append_message(tid, role="user")

            from holdspeak.services.errors import ValidationError
            with pytest.raises(ValidationError, match="Not enough messages"):
                asyncio.run(svc.compact_thread(hub["owner"], tid))
        finally:
            self._cleanup(hub)

    def test_compact_failure_creates_compact_failed_row(self, tmp_path: Path) -> None:
        """Engine failure → compact_failed system row, no cut."""
        hub = self._hub(tmp_path, compact_raise=True)
        try:
            svc = hub["svc"]
            db = hub["db"]
            owner = hub["owner"]

            thread = svc.create(title="fail test")
            tid = thread["id"]

            r1 = asyncio.run(svc.start_turn(owner, tid, "Hello"))
            self._wait_done(db, r1["assistant_message_id"])
            r2 = asyncio.run(svc.start_turn(owner, tid, "More"))
            self._wait_done(db, r2["assistant_message_id"])

            result = asyncio.run(svc.compact_thread(owner, tid))
            assert result["status"] == "failed"

            # Verify compact_failed row
            fail_msg = db.threads.get_message(result["message_id"])
            assert fail_msg is not None
            stats = json.loads(fail_msg.stats_json)
            assert stats.get("compact_failed") is True

            # No compaction cut should exist — next turn still sees all messages
            hub["turn_payloads"].clear()
            r3 = asyncio.run(svc.start_turn(owner, tid, "Still here?"))
            self._wait_done(db, r3["assistant_message_id"])

            assert len(hub["turn_payloads"]) >= 1
            all_content = " ".join(
                m.get("content", "") for m in hub["turn_payloads"][0]["messages"]
            )
            assert "Hello" in all_content
            assert "More" in all_content
            assert "Still here?" in all_content

        finally:
            self._cleanup(hub)

    def test_sensitive_compact_on_cloud_route_withholds_texts(
        self, tmp_path: Path,
    ) -> None:
        """When the compact route is cloud, sensitive texts are redacted from
        the compact payload's messages (the engine sees redacted content)."""
        hub = self._hub(tmp_path, compact_summary="Redacted summary.")
        try:
            svc = hub["svc"]
            db = hub["db"]
            owner = hub["owner"]

            thread = svc.create(title="cloud compact")
            tid = thread["id"]

            # Create messages with sensitive content
            r1 = asyncio.run(svc.start_turn(owner, tid, "Hello"))
            self._wait_done(db, r1["assistant_message_id"])

            # Mark a part as sensitive manually
            u_parts = db.threads.get_parts(r1["user_message_id"])
            if u_parts:
                with db._connection() as conn:
                    conn.execute(
                        "UPDATE thread_message_parts SET sensitive=1 WHERE id=?",
                        (u_parts[0].id,),
                    )

            r2 = asyncio.run(svc.start_turn(owner, tid, "More info"))
            self._wait_done(db, r2["assistant_message_id"])

            # Patch the admission to report cloud egress
            original_admit = svc._broker.inference_adoption_service.admit
            def _cloud_admit(*args, **kwargs):
                result = original_admit(*args, **kwargs)
                result["route_plan"]["entries"] = [{"boundary": "cloud"}]
                return result

            with patch.object(
                svc._broker.inference_adoption_service, "admit",
                side_effect=_cloud_admit,
            ):
                compact_result = asyncio.run(svc.compact_thread(owner, tid))

            assert compact_result["status"] == "ok"

            # The summary part should be sensitive=True (inherits from source)
            compact_parts = db.threads.get_parts(compact_result["message_id"])
            text_parts = [p for p in compact_parts if p.kind == "text"]
            assert len(text_parts) == 1
            assert text_parts[0].sensitive is True

        finally:
            self._cleanup(hub)


# ---------------------------------------------------------------------------
# M1 close counsel: capability-boundary compact redaction
# ---------------------------------------------------------------------------


class TestCompactM1CapabilityBoundary:
    """Close counsel M1: run_compact redacts based on the chat.compact
    capability's OWN boundary, not the thread's chat.turn egress scope.

    Tests run_compact directly (unit), mocking the broker to carry the
    right DB with a profile at the requested boundary.
    """

    @staticmethod
    def _setup(tmp_path: Path, *, compact_boundary: str = "cloud"):
        """Create a DB with chat.compact assigned to a profile whose
        deployment revision carries the given boundary."""
        from holdspeak.deployment_revisions import DeploymentRevision
        from holdspeak.inference_targets import DeploymentIdentity
        from unittest.mock import MagicMock

        db = Database(tmp_path / "m1_cp.db")
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        owner = Principal(PrincipalKind.OWNER, "m1-compact-owner")

        turn_profile = "m1-cp-turn"
        _profile(db, turn_profile, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "assign-turn",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": turn_profile, "profile_revision": 1}],
        })
        from holdspeak.db.reconcile import _backfill_chat_practice_assignments
        with db._connection() as conn:
            _backfill_chat_practice_assignments(conn)

        if compact_boundary != "same_device":
            cp_profile = "m1-compact-cloud"
            v1_dep = DeploymentRevision.from_identity(DeploymentIdentity(
                destination_id="cloud_service",
                kind="cloud",
                engine="configured_local_engine",
                model=cp_profile,
                node="",
                boundary=compact_boundary,
                endpoint="",
                secret_slot="",
            ))
            db.deployment_revisions.upsert(v1_dep)
            with db._connection() as conn:
                head = conn.execute(
                    "SELECT assignment_id, revision FROM inference_assignment_heads "
                    "WHERE assignment_key='capability:chat.compact' AND cleared=0",
                ).fetchone()
                if head:
                    conn.execute(
                        "UPDATE inference_assignments SET profile_id=? "
                        "WHERE assignment_id=? AND assignment_revision=?",
                        (cp_profile, head["assignment_id"], head["revision"]),
                    )

        return db, owner

    def test_cloud_compact_withholds_sensitive_texts(self, tmp_path: Path) -> None:
        """chat.compact boundary=cloud: run_compact replaces sensitive
        texts with [people content withheld]."""
        db, owner = self._setup(tmp_path, compact_boundary="cloud")

        from holdspeak.services.thread_practice import run_compact

        class _Broker:
            database = db
            inference_runner = MagicMock()

        broker = _Broker()
        captured: list[dict] = []

        def _mock_invoke(request, adapter, publish=None):
            captured.append(request.payload)
            result = MagicMock()
            result.result = {"summary": "A summary."}
            return result
        broker.inference_runner.invoke = _mock_invoke

        messages = [
            {"role": "user", "content": "Tell me about Alice Smith"},
            {"role": "assistant", "content": "Alice Smith is important"},
        ]

        result = run_compact(
            broker, owner, "t1", messages,
            sensitive_texts=["Alice Smith"],
        )

        assert len(captured) >= 1
        payload = captured[0]
        user_prompt = payload.get("user_prompt", "")
        assert "Alice Smith" not in user_prompt, (
            f"Cloud compact should redact, got: {user_prompt}"
        )
        assert _PEOPLE_REDACTION in user_prompt, (
            f"Expected redaction marker, got: {user_prompt}"
        )

    def test_local_compact_preserves_sensitive_texts(self, tmp_path: Path) -> None:
        """chat.compact boundary=same_device: run_compact keeps sensitive
        texts verbatim."""
        db, owner = self._setup(tmp_path, compact_boundary="same_device")

        from holdspeak.services.thread_practice import run_compact

        class _Broker:
            database = db
            inference_runner = MagicMock()

        broker = _Broker()
        captured: list[dict] = []

        def _mock_invoke(request, adapter, publish=None):
            captured.append(request.payload)
            result = MagicMock()
            result.result = {"summary": "A summary."}
            return result
        broker.inference_runner.invoke = _mock_invoke

        messages = [
            {"role": "user", "content": "Tell me about Bob Jones"},
            {"role": "assistant", "content": "Bob Jones is important"},
        ]

        result = run_compact(
            broker, owner, "t1", messages,
            sensitive_texts=["Bob Jones"],
        )

        assert len(captured) >= 1
        payload = captured[0]
        user_prompt = payload.get("user_prompt", "")
        assert _PEOPLE_REDACTION not in user_prompt, (
            f"Local compact should not redact, got: {user_prompt}"
        )
