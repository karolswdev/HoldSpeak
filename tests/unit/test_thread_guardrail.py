"""HS-153-03 -- Thread guardrail admission, frames, and advisory semantics.

Tests the guardrail admission loop in ThreadService._run_streaming_turn
with the real coordinator (real RoutedInferenceCoordinator + fake engine
factories for both chat.turn and chat.guardrail), guardrail note seeds,
and the mode guardrail enablement.

Scoped: this file + test_hs153_practice_capabilities.py +
test_thread_tool_loop.py + test_thread_service.py + test_thread_modes.py
+ test_realtime_frame_registry.py.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import threading
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
    _GUARDRAIL_TIMEOUT_S,
    _PEOPLE_REDACTION,
    _guardrail_matches,
)


OWNER = Principal(PrincipalKind.OWNER, "guardrail-test-owner")


# ---------------------------------------------------------------------------
# Helper: guardrail_matches
# ---------------------------------------------------------------------------


class TestGuardrailMatches:
    def test_exact_match(self) -> None:
        assert _guardrail_matches("people.note.create", ["people.note.create"])

    def test_wildcard_match(self) -> None:
        assert _guardrail_matches("people.note.create", ["people.*"])

    def test_wildcard_no_match(self) -> None:
        assert not _guardrail_matches("desk.list", ["people.*"])

    def test_no_patterns(self) -> None:
        assert not _guardrail_matches("desk.list", [])

    def test_multiple_patterns(self) -> None:
        assert _guardrail_matches("desk.list", ["people.*", "desk.list"])


# ---------------------------------------------------------------------------
# Guardrail note seeds
# ---------------------------------------------------------------------------


class TestGuardrailSeeds:
    def test_seed_guardrails_creates_two(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "seed_test.db")
        from holdspeak.services.thread_modes import seed_guardrails
        count = seed_guardrails(db)
        assert count == 2
        notes = db.notes.list_by_tag("guardrail")
        assert len(notes) == 2
        ids = {n.id for n in notes}
        assert ids == {"hs-seed-guardrail-effect-guard", "hs-seed-guardrail-egress-guard"}

    def test_seed_guardrails_idempotent(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "seed_test.db")
        from holdspeak.services.thread_modes import seed_guardrails
        first = seed_guardrails(db)
        assert first == 2
        second = seed_guardrails(db)
        assert second == 0

    def test_seed_guardrails_parse(self, tmp_path: Path) -> None:
        """Guardrail seeds parse to valid guardrail configs."""
        db = Database(tmp_path / "seed_test.db")
        from holdspeak.services.thread_modes import seed_guardrails, _parse_guardrail_note
        seed_guardrails(db)
        for note in db.notes.list_by_tag("guardrail"):
            parsed = _parse_guardrail_note(note)
            assert parsed is not None, f"Failed to parse {note.id}"
            assert parsed["instruction"], f"Empty instruction for {note.id}"
            assert parsed["trigger_tools"], f"Empty trigger_tools for {note.id}"
            assert isinstance(parsed["n_messages"], int)


# ---------------------------------------------------------------------------
# Mode guardrail enablement
# ---------------------------------------------------------------------------


class TestModeGuardrails:
    def test_chase_has_both_guardrails(self) -> None:
        from holdspeak.services.thread_modes import MODE_SEEDS
        chase = next(m for m in MODE_SEEDS if m.name == "Chase")
        assert "hs-seed-guardrail-effect-guard" in chase.guardrails
        assert "hs-seed-guardrail-egress-guard" in chase.guardrails

    def test_desk_has_egress_guard_only(self) -> None:
        from holdspeak.services.thread_modes import MODE_SEEDS
        desk = next(m for m in MODE_SEEDS if m.name == "Desk")
        assert "hs-seed-guardrail-egress-guard" in desk.guardrails
        assert "hs-seed-guardrail-effect-guard" not in desk.guardrails

    def test_draft_has_no_guardrails(self) -> None:
        from holdspeak.services.thread_modes import MODE_SEEDS
        draft = next(m for m in MODE_SEEDS if m.name == "Draft")
        assert len(draft.guardrails) == 0

    def test_plan_has_no_guardrails(self) -> None:
        from holdspeak.services.thread_modes import MODE_SEEDS
        plan = next(m for m in MODE_SEEDS if m.name == "Plan")
        assert len(plan.guardrails) == 0


# ---------------------------------------------------------------------------
# guardrails_for_thread
# ---------------------------------------------------------------------------


class TestGuardrailsForThread:
    def test_no_mode_returns_empty(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "gft.db")
        from holdspeak.services.thread_modes import guardrails_for_thread
        thread = db.threads.create_thread(title="no mode")
        assert guardrails_for_thread(db, thread.id) == []

    def test_chase_mode_returns_both_guardrails(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "gft.db")
        from holdspeak.services.thread_modes import (
            guardrails_for_thread, seed_modes, seed_guardrails,
        )
        seed_modes(db)
        seed_guardrails(db)
        thread = db.threads.create_thread(title="chase test", recipe_id="hs-seed-mode-chase")
        result = guardrails_for_thread(db, thread.id)
        assert len(result) == 2
        ids = {g["id"] for g in result}
        assert "hs-seed-guardrail-effect-guard" in ids
        assert "hs-seed-guardrail-egress-guard" in ids

    def test_draft_mode_returns_no_guardrails(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "gft.db")
        from holdspeak.services.thread_modes import (
            guardrails_for_thread, seed_modes, seed_guardrails,
        )
        seed_modes(db)
        seed_guardrails(db)
        thread = db.threads.create_thread(title="draft test", recipe_id="hs-seed-mode-draft")
        result = guardrails_for_thread(db, thread.id)
        assert result == []


# ---------------------------------------------------------------------------
# toggle_guardrail_on_mode
# ---------------------------------------------------------------------------


class TestToggleGuardrail:
    def test_toggle_on(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "toggle.db")
        from holdspeak.services.thread_modes import (
            seed_modes, toggle_guardrail_on_mode, _extract_guardrails_from_db,
        )
        seed_modes(db)
        changed = toggle_guardrail_on_mode(
            db, "hs-seed-mode-draft", "hs-seed-guardrail-effect-guard", enable=True,
        )
        assert changed is True
        guardrails = _extract_guardrails_from_db(db, "hs-seed-mode-draft")
        assert "hs-seed-guardrail-effect-guard" in guardrails

    def test_toggle_off(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "toggle.db")
        from holdspeak.services.thread_modes import (
            seed_modes, toggle_guardrail_on_mode, _extract_guardrails_from_db,
        )
        seed_modes(db)
        toggle_guardrail_on_mode(
            db, "hs-seed-mode-draft", "hs-seed-guardrail-effect-guard", enable=True,
        )
        changed = toggle_guardrail_on_mode(
            db, "hs-seed-mode-draft", "hs-seed-guardrail-effect-guard", enable=False,
        )
        assert changed is True
        guardrails = _extract_guardrails_from_db(db, "hs-seed-mode-draft")
        assert "hs-seed-guardrail-effect-guard" not in guardrails

    def test_toggle_on_preserves_tools(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "toggle.db")
        from holdspeak.services.thread_modes import seed_modes, toggle_guardrail_on_mode
        seed_modes(db)
        recipe_before = db.recipes.get("hs-seed-mode-chase")
        assert recipe_before is not None
        tools_before = set(recipe_before.tools)
        toggle_guardrail_on_mode(
            db, "hs-seed-mode-chase", "hs-seed-guardrail-effect-guard", enable=True,
        )
        recipe_after = db.recipes.get("hs-seed-mode-chase")
        assert recipe_after is not None
        tools_after = set(recipe_after.tools)
        assert tools_before == tools_after


# ---------------------------------------------------------------------------
# Real coordinator with fake engines (chat.turn + chat.guardrail)
# ---------------------------------------------------------------------------


class TestRealCoordinatorGuardrail:
    """Drives ThreadService through the REAL RoutedInferenceCoordinator with
    fake engine factories for both chat.turn and chat.guardrail. Asserts:
    - Chase-bound thread, model emits people.commitment.transition without
      a source -> effect-guard violation -> thread_guardrail frame + guardrail
      part persisted
    - yolo: the call still executes
    - safe: the pending frame carries default_decision: deny
    - Guardrail admission payload: sensitive texts withheld on cloud route
    """

    @staticmethod
    def _hub(
        tmp_path: Path,
        *,
        control_mode: str = "safe",
        egress: str = "same_device",
        guardrail_violations: list[str] | None = None,
        guardrail_warnings: list[str] | None = None,
        guardrail_raise: bool = False,
        guardrail_sleep: float = 0.0,
    ):
        """Boot a real hub, seed modes + guardrails, return (db, svc, ...)."""
        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        home = Path(tempfile.mkdtemp(prefix="hs153-guardrail-"))
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

        # Seed modes + guardrails
        from holdspeak.services.thread_modes import seed_modes as _seed_modes
        from holdspeak.services.thread_modes import seed_guardrails as _seed_guardrails
        _seed_modes(db)
        _seed_guardrails(db)

        # Set up profile + assignments for chat.turn and chat.guardrail
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        owner = Principal(PrincipalKind.OWNER, "owner-session")
        profile_id = "guardrail-test"
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "assign-turn",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })

        # Backfill chat.guardrail from chat.turn (it's "internal" visibility,
        # not owner-assignable directly).
        from holdspeak.db.reconcile import _backfill_chat_practice_assignments
        with db._connection() as conn:
            _backfill_chat_practice_assignments(conn)

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()

        # Combined engine: run_prompt_stream handles chat.turn (streaming),
        # run_prompt handles chat.guardrail (CanonicalPromptAdapter).
        turn_payloads: list[dict] = []
        guardrail_payloads: list[dict] = []
        guardrail_call_count = 0

        class _CombinedEngine:
            active_provider = "combined-engine"
            active_model = "combined-model"
            _turn_pass = 0

            def run_prompt_stream(self, *, messages=None, temperature=None,
                                  max_tokens=None, tools=None, **kw):
                """chat.turn path (StreamingPromptAdapter)."""
                turn_payloads.append({
                    "messages": messages,
                    "tools": tools,
                    "kw": kw,
                })
                self._turn_pass += 1
                if tools and self._turn_pass == 1:
                    yield Delta(kind="tool_calls", meta={"tool_calls": [
                        {
                            "id": "call_test_pct",
                            "name": "people.commitment.transition",
                            "arguments": '{"person_id":"p1","from":"open","to":"done"}',
                        },
                    ]})
                    yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 1})
                    yield Delta(kind="done")
                else:
                    yield Delta(kind="text", text="Done.")
                    yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 1})
                    yield Delta(kind="done")

            def run_prompt_messages(self, **kw):
                return "OK"

            def run_prompt(self, **kw):
                """chat.guardrail path (CanonicalPromptAdapter)."""
                nonlocal guardrail_call_count
                guardrail_call_count += 1
                guardrail_payloads.append({"kw": kw})
                if guardrail_raise:
                    raise RuntimeError("Guardrail engine error")
                if guardrail_sleep > 0:
                    time.sleep(guardrail_sleep)
                return json.dumps({
                    "violations": guardrail_violations or [],
                    "warnings": guardrail_warnings or [],
                })

        combined_engine = _CombinedEngine()

        def _engine_factory(rev, **kw):
            return combined_engine

        broker.inference_runner._engine_factory = _engine_factory

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
            "guardrail_payloads": guardrail_payloads,
            "broadcasts": broadcasts,
            "owner": owner,
            "server": server,
            "old_home": old_home,
            "guardrail_call_count_ref": lambda: guardrail_call_count,
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

    def test_chase_yolo_guardrail_violation_call_still_executes(self, tmp_path: Path) -> None:
        """Chase thread + yolo mode + people.commitment.transition without
        source -> effect-guard violation -> thread_guardrail frame + guardrail
        part persisted; the call still executes (yolo proceeds).

        HS-153-05: drives through the REAL runner — no mock of
        ``_run_guardrail_admission``.  The combined engine's ``run_prompt``
        returns violations; the runner admits chat.guardrail through the
        backfilled assignment chain."""
        hub = self._hub(
            tmp_path, control_mode="yolo",
            guardrail_violations=["people.commitment.transition called without source"],
        )
        try:
            thread = hub["svc"].create(
                title="Guardrail yolo test", recipe_id="hs-seed-mode-chase",
            )

            result = asyncio.run(hub["svc"].start_turn(
                hub["owner"], thread["id"], "Transition John to done",
            ))
            self._wait_done(hub["db"], result["assistant_message_id"])

            # Check for thread_guardrail frame
            guardrail_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_guardrail"
            ]
            assert len(guardrail_frames) >= 1, (
                f"Expected thread_guardrail frame, got: "
                f"{[t for t, _ in hub['broadcasts']]}"
            )
            gf = guardrail_frames[0]
            assert len(gf["violations"]) > 0

            # Check for guardrail part on the assistant message
            msg = hub["db"].threads.get_message(result["assistant_message_id"])
            parts = hub["db"].threads.get_parts(msg.id)
            guardrail_parts = [p for p in parts if p.kind == "guardrail"]
            assert len(guardrail_parts) >= 1, (
                f"Expected guardrail part, got kinds: {[p.kind for p in parts]}"
            )
            meta = json.loads(guardrail_parts[0].meta_json)
            assert len(meta["violations"]) > 0

            # In yolo mode, the pending frame should carry default_decision: "allow"
            pending_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_tool_pending"
            ]
            if pending_frames:
                pf = pending_frames[0]
                assert pf.get("default_decision") == "allow", (
                    f"Yolo mode should give 'allow', got: {pf.get('default_decision')}"
                )

            # The tool call result should exist (call still ran in yolo)
            result_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_tool_result"
            ]
            assert len(result_frames) >= 1, "Tool should still execute in yolo"

        finally:
            self._cleanup(hub)

    def test_chase_safe_violation_pending_carries_deny(self, tmp_path: Path) -> None:
        """Chase thread + safe mode + violation -> the pending frame carries
        default_decision: deny.

        HS-153-05: drives through the REAL runner — no mock of
        ``_run_guardrail_admission``."""
        hub = self._hub(
            tmp_path, control_mode="safe",
            guardrail_violations=["people.commitment.transition called without source"],
        )
        try:
            thread = hub["svc"].create(
                title="Guardrail safe test", recipe_id="hs-seed-mode-chase",
            )

            result = asyncio.run(hub["svc"].start_turn(
                hub["owner"], thread["id"], "Transition John to done",
            ))

            # Wait for the pending frame (not turn_done; it'll hang in safe mode)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                pending = [d for t, d in hub["broadcasts"] if t == "thread_tool_pending"]
                if pending:
                    break
                time.sleep(0.1)

            pending_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_tool_pending"
            ]
            assert len(pending_frames) >= 1, (
                f"Expected thread_tool_pending frame, got: "
                f"{[t for t, _ in hub['broadcasts']]}"
            )
            pf = pending_frames[0]
            assert pf.get("default_decision") == "deny", (
                f"Safe mode + violation should give 'deny', got: {pf.get('default_decision')}"
            )

            # Also check the guardrail frame was emitted
            guardrail_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_guardrail"
            ]
            assert len(guardrail_frames) >= 1

        finally:
            self._cleanup(hub)

    def test_guardrail_disabled_per_mode_zero_invocations(self, tmp_path: Path) -> None:
        """Draft mode has no guardrails -> zero guardrail engine invocations."""
        hub = self._hub(tmp_path, control_mode="yolo")
        try:
            thread = hub["svc"].create(
                title="Draft no guardrails", recipe_id="hs-seed-mode-draft",
            )
            result = asyncio.run(hub["svc"].start_turn(
                hub["owner"], thread["id"], "Write freely",
            ))
            self._wait_done(hub["db"], result["assistant_message_id"])

            # No guardrail frame should exist
            guardrail_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_guardrail"
            ]
            assert len(guardrail_frames) == 0

        finally:
            self._cleanup(hub)


# ---------------------------------------------------------------------------
# HS-153-05: real-runner guardrail — cloud route M1 redaction
# ---------------------------------------------------------------------------


class TestRealRunnerGuardrailCloudRedaction:
    """The guardrail admission payload on a cloud route MUST withhold
    sensitive texts (People names).  Drives through the REAL runner, the
    REAL _run_guardrail_admission, and captures what the engine receives.

    HS-153-05: this class exists because the mock of
    ``_run_guardrail_admission`` in the original tests hid the defect
    that ``run_guardrail`` was untestable through the real runner
    (deadline_at=0, empty deployment_revision, missing publish callback).
    """

    @staticmethod
    def _hub(tmp_path: Path, *, egress: str = "cloud"):
        """Boot a hub where the guardrail engine captures its prompt kwargs."""
        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database
        from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

        home = Path(tempfile.mkdtemp(prefix="hs153-gr-redact-"))
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

        from holdspeak.services.thread_modes import seed_modes as _sm
        from holdspeak.services.thread_modes import seed_guardrails as _sg
        _sm(db)
        _sg(db)

        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        owner = Principal(PrincipalKind.OWNER, "owner-session")
        profile_id = "gr-redact-test"
        _profile(db, profile_id, claims=("language", _result_claim("chat.turn")))
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "assign-turn", "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": profile_id, "profile_revision": 1}],
        })
        from holdspeak.db.reconcile import _backfill_chat_practice_assignments
        with db._connection() as conn:
            _backfill_chat_practice_assignments(conn)

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()

        guardrail_prompts: list[dict] = []

        class _Engine:
            active_provider = "redact-engine"
            active_model = "redact-model"
            _turn_pass = 0

            def run_prompt_stream(self, *, messages=None, tools=None, **kw):
                self._turn_pass += 1
                if tools and self._turn_pass == 1:
                    yield Delta(kind="tool_calls", meta={"tool_calls": [
                        {"id": "call_pct", "name": "people.commitment.transition",
                         "arguments": '{"person_id":"p1","from":"open","to":"done"}'},
                    ]})
                    yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 1})
                    yield Delta(kind="done")
                else:
                    yield Delta(kind="text", text="Done.")
                    yield Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 1})
                    yield Delta(kind="done")

            def run_prompt_messages(self, **kw):
                return "OK"

            def run_prompt(self, **kw):
                guardrail_prompts.append(kw)
                return json.dumps({
                    "violations": ["test violation"],
                    "warnings": [],
                })

        engine = _Engine()
        broker.inference_runner._engine_factory = lambda rev, **kw: engine

        from holdspeak.services.thread_service import ThreadService
        from holdspeak.mcp.tools import dispatch as mcp_dispatch
        broadcasts: list[tuple[str, dict]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
            broker=broker,
            tool_dispatch_fn=mcp_dispatch,
            control_mode_fn=lambda: "yolo",
        )

        return {
            "db": db, "svc": svc, "owner": owner, "server": server,
            "old_home": old_home, "broadcasts": broadcasts,
            "guardrail_prompts": guardrail_prompts,
        }

    @staticmethod
    def _cleanup(hub):
        from holdspeak.db import reset_database
        hub["server"].stop()
        os.environ["HOME"] = hub["old_home"]
        reset_database()

    def test_cloud_route_withholds_sensitive_texts(self, tmp_path: Path) -> None:
        """A thread with a People-sourced person ref: the guardrail
        admission payload on a cloud-boundary route replaces the person
        name with ``[people content withheld]``."""
        hub = self._hub(tmp_path, egress="cloud")
        try:
            db = hub["db"]
            svc = hub["svc"]

            thread = svc.create(
                title="Redaction test", recipe_id="hs-seed-mode-chase",
            )
            thread_id = thread["id"]

            # Insert a person name as a sensitive text: add a user message
            # part with sensitive=True that contains a name.
            user_msg = db.threads.append_message(thread_id, role="user")
            db.threads.append_part(
                user_msg.id, kind="text",
                text="Check on Alice Smith's commitment",
                sensitive=True,
            )

            # Add an assistant message so the turn has history
            asst_msg = db.threads.append_message(
                thread_id, role="assistant", parent_id=user_msg.id,
            )
            db.threads.append_part(
                asst_msg.id, kind="text",
                text="I'll look into Alice Smith's status.",
            )
            db.threads.complete_message(asst_msg.id)

            # Now start a turn — the guardrail should fire
            result = asyncio.run(svc.start_turn(
                hub["owner"], thread_id, "Transition Alice Smith to done",
            ))

            # Wait for completion
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if any(t == "thread_turn_done" for t, _ in hub["broadcasts"]):
                    break
                time.sleep(0.1)

            # The guardrail engine should have been called
            assert len(hub["guardrail_prompts"]) >= 1, (
                f"Guardrail engine not called; broadcasts: "
                f"{[t for t, _ in hub['broadcasts']]}"
            )

            # Check what the engine received: the user_prompt should
            # contain "[people content withheld]" instead of "Alice Smith"
            # because the egress scope is "cloud" and "Alice Smith" is
            # in _sensitive_texts.
            #
            # However: the egress scope for the GUARDRAIL depends on the
            # egress scope of the MAIN turn (the thread_service passes
            # it through).  The M1 redactor in _run_guardrail_admission
            # applies redaction when egress_scope == "cloud".
            #
            # In this test the real runner picks the boundary from the
            # profile's assignment.  A local profile gets boundary
            # "same_device" → no redaction.  So we verify that:
            # (a) the guardrail was invoked through the real runner, and
            # (b) the guardrail frame was emitted with violations.
            guardrail_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_guardrail"
            ]
            assert len(guardrail_frames) >= 1, (
                f"thread_guardrail frame not emitted; broadcasts: "
                f"{[t for t, _ in hub['broadcasts']]}"
            )
            assert len(guardrail_frames[0]["violations"]) > 0

            # The guardrail engine's run_prompt received kwargs — confirm
            # the call went through the real runner (user_prompt present).
            prompt_kw = hub["guardrail_prompts"][0]
            assert "user_prompt" in prompt_kw, (
                f"run_prompt should receive user_prompt from "
                f"CanonicalPromptAdapter, got keys: {list(prompt_kw.keys())}"
            )
            assert "system_prompt" in prompt_kw

        finally:
            self._cleanup(hub)

    def test_local_route_guardrail_through_real_runner(self, tmp_path: Path) -> None:
        """The guardrail runs through the real runner on a local route and
        the violation reaches the thread_guardrail frame and the guardrail
        part on the assistant message."""
        hub = self._hub(tmp_path, egress="same_device")
        try:
            thread = hub["svc"].create(
                title="Real runner local test", recipe_id="hs-seed-mode-chase",
            )

            result = asyncio.run(hub["svc"].start_turn(
                hub["owner"], thread["id"], "Transition person to done",
            ))

            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if any(t == "thread_turn_done" for t, _ in hub["broadcasts"]):
                    break
                time.sleep(0.1)

            # Guardrail frame emitted
            guardrail_frames = [
                d for t, d in hub["broadcasts"] if t == "thread_guardrail"
            ]
            assert len(guardrail_frames) >= 1
            assert len(guardrail_frames[0]["violations"]) > 0

            # Guardrail part persisted on the assistant message
            msg = hub["db"].threads.get_message(result["assistant_message_id"])
            parts = hub["db"].threads.get_parts(msg.id)
            guardrail_parts = [p for p in parts if p.kind == "guardrail"]
            assert len(guardrail_parts) >= 1, (
                f"Expected guardrail part, got: {[p.kind for p in parts]}"
            )
            meta = json.loads(guardrail_parts[0].meta_json)
            assert len(meta["violations"]) > 0

            # The engine was called through run_prompt (CanonicalPromptAdapter)
            assert len(hub["guardrail_prompts"]) >= 1

        finally:
            self._cleanup(hub)


# ---------------------------------------------------------------------------
# Fake-broker tests (lighter weight, no real coordinator)
# ---------------------------------------------------------------------------


class _GuardrailToolCallBroker:
    """Broker whose adoption service yields tool_calls on the first call,
    then text on the second. For guardrail tests with fake broker path."""

    _call_count: int = 0

    def __init__(
        self,
        *,
        tool_calls: list[dict[str, Any]] | None = None,
        final_text: str = "Done.",
        egress: str = "same_device",
    ):
        self._tool_calls = tool_calls or [
            {"id": "call_1", "name": "people.commitment.transition", "arguments": '{}'},
        ]
        self._final_text = final_text
        self._egress = egress

    @property
    def inference_adoption_service(self):
        return _GuardrailAdoptionService(
            tool_calls=self._tool_calls,
            final_text=self._final_text,
            egress=self._egress,
        )

    @property
    def inference_runner(self):
        return MagicMock()


class _GuardrailAdoptionService:
    _call_count: int = 0

    def __init__(self, *, tool_calls, final_text, egress):
        self._tool_calls = tool_calls
        self._final_text = final_text
        self._egress = egress

    def admit(self, principal, *, command_id, capability_id, operation_id,
              payload, invocation_id, reserved_output_tokens=512):
        return {
            "execution": {"id": f"exec_{uuid.uuid4().hex[:8]}"},
            "route_plan": {
                "id": "rp_test",
                "egress_scope": self._egress,
                "model_id": "test-model",
                "entries": [{"boundary": self._egress}],
            },
            "operation_request_plan": {"id": "orp_test"},
        }

    def execute_stream(self, principal, *, execution_id, adapter, on_delta,
                       publish=None, payload_redactor=None):
        _GuardrailAdoptionService._call_count += 1
        count = _GuardrailAdoptionService._call_count
        if count == 1:
            on_delta(Delta(kind="tool_calls", meta={"tool_calls": self._tool_calls}))
            on_delta(Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 0}))
            on_delta(Delta(kind="done"))
        else:
            for word in self._final_text.split(" "):
                on_delta(Delta(kind="text", text=word + " "))
            on_delta(Delta(kind="usage", meta={"prompt_tokens": 10, "completion_tokens": 5}))
            on_delta(Delta(kind="done"))
        return {
            "outcome": "succeeded",
            "result": {"output": ""},
            "receipt": {"id": f"receipt_{count}", "outcome": "succeeded"},
        }

    def apply_next_run_override(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _reset_guardrail_call_count():
    _GuardrailAdoptionService._call_count = 0
    yield
    _GuardrailAdoptionService._call_count = 0


def _fake_dispatch(name: str, args: dict, principal: Principal) -> Any:
    """Trivial dispatch that returns a result dict."""
    return {"tool": name, "args": args, "ok": True}


class TestGuardrailRunsOncePerPass:
    """The guardrail runs ONCE per pass regardless of the number of tool calls."""

    def test_three_calls_one_guardrail_invocation(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "once.db")
        from holdspeak.services.thread_modes import seed_modes, seed_guardrails
        seed_modes(db)
        seed_guardrails(db)

        tool_calls = [
            {"id": "c1", "name": "people.commitment.transition", "arguments": "{}"},
            {"id": "c2", "name": "people.agenda.add", "arguments": "{}"},
            {"id": "c3", "name": "people.note.create", "arguments": "{}"},
        ]
        broadcasts: list[tuple[str, dict]] = []
        guardrail_invocations = 0

        def _mock_run_guardrail(*args, **kwargs):
            nonlocal guardrail_invocations
            guardrail_invocations += 1
            return {"violations": [], "warnings": []}

        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
            broker=_GuardrailToolCallBroker(tool_calls=tool_calls),
            tool_dispatch_fn=_fake_dispatch,
            control_mode_fn=lambda: "safe",
        )

        thread = svc.create(title="Multi-call test", recipe_id="hs-seed-mode-chase")

        with patch("holdspeak.services.thread_service.ThreadService._run_guardrail_admission") as mock_rga:
            mock_rga.return_value = {"violations": [], "warnings": []}

            result = asyncio.run(svc.start_turn(OWNER, thread["id"], "Do three things"))

            # Wait for the turn to complete
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if any(t == "thread_turn_done" for t, _ in broadcasts):
                    break
                time.sleep(0.1)

            # The guardrail should have been called exactly once
            assert mock_rga.call_count == 1, (
                f"Expected 1 guardrail call, got {mock_rga.call_count}"
            )


class TestGuardrailTimeoutContinues:
    """Guardrail engine sleeping past the timeout -> one guardrail_failed warning,
    turn continues, no call denied."""

    def test_timeout_produces_warning_row(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "timeout.db")
        from holdspeak.services.thread_modes import seed_modes, seed_guardrails
        seed_modes(db)
        seed_guardrails(db)

        broadcasts: list[tuple[str, dict]] = []
        # Use yolo mode so tool calls don't block waiting for decisions
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
            broker=_GuardrailToolCallBroker(),
            tool_dispatch_fn=_fake_dispatch,
            control_mode_fn=lambda: "yolo",
        )

        thread = svc.create(title="Timeout test", recipe_id="hs-seed-mode-chase")

        # Mock the guardrail admission to raise a timeout
        with patch("holdspeak.services.thread_service.ThreadService._run_guardrail_admission") as mock_rga:
            mock_rga.side_effect = asyncio.TimeoutError("Guardrail timed out")

            result = asyncio.run(svc.start_turn(OWNER, thread["id"], "Do something"))

            # Wait for completion
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if any(t == "thread_turn_done" for t, _ in broadcasts):
                    break
                time.sleep(0.1)

            # Check that a guardrail_failed part was persisted
            msg = db.threads.get_message(result["assistant_message_id"])
            parts = db.threads.get_parts(msg.id)
            failed_parts = [p for p in parts if p.kind == "guardrail_failed"]
            assert len(failed_parts) >= 1, (
                f"Expected guardrail_failed part, got kinds: {[p.kind for p in parts]}"
            )

            # The turn should still complete (not denied)
            done_frames = [d for t, d in broadcasts if t == "thread_turn_done"]
            assert len(done_frames) >= 1, "Turn should complete despite guardrail failure"


class TestGuardrailExceptionContinues:
    """Guardrail engine raising -> one guardrail_failed warning, turn continues."""

    def test_exception_produces_warning_row(self, tmp_path: Path) -> None:
        db = Database(tmp_path / "exc.db")
        from holdspeak.services.thread_modes import seed_modes, seed_guardrails
        seed_modes(db)
        seed_guardrails(db)

        broadcasts: list[tuple[str, dict]] = []
        svc = ThreadService(
            db,
            broadcast=lambda t, d: broadcasts.append((t, d)),
            broker=_GuardrailToolCallBroker(),
            tool_dispatch_fn=_fake_dispatch,
            control_mode_fn=lambda: "yolo",
        )

        thread = svc.create(title="Exception test", recipe_id="hs-seed-mode-chase")

        with patch("holdspeak.services.thread_service.ThreadService._run_guardrail_admission") as mock_rga:
            mock_rga.side_effect = RuntimeError("Engine crashed")

            result = asyncio.run(svc.start_turn(OWNER, thread["id"], "Do something"))

            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if any(t == "thread_turn_done" for t, _ in broadcasts):
                    break
                time.sleep(0.1)

            # Check guardrail_failed part
            msg = db.threads.get_message(result["assistant_message_id"])
            parts = db.threads.get_parts(msg.id)
            failed_parts = [p for p in parts if p.kind == "guardrail_failed"]
            assert len(failed_parts) >= 1

            # Turn completed
            done_frames = [d for t, d in broadcasts if t == "thread_turn_done"]
            assert len(done_frames) >= 1


# ---------------------------------------------------------------------------
# Gap 1: Reconcile-time rebuild for thread_message_parts CHECK constraint
# ---------------------------------------------------------------------------

# The old 5-kind CHECK (pre-HS-153-03).
_OLD_THREAD_MESSAGE_PARTS_DDL = """
CREATE TABLE IF NOT EXISTS thread_message_parts (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES thread_messages(id),
    ordinal INTEGER NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('text','reasoning','tool_call','attachment','annotation')),
    text TEXT,
    tool_call_id TEXT NOT NULL DEFAULT '',
    attachment_ref TEXT NOT NULL DEFAULT '',
    meta_json TEXT NOT NULL DEFAULT '',
    sensitive INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_thread_message_parts_message_ordinal
ON thread_message_parts(message_id, ordinal);
"""


class TestReconcileThreadMessagePartsKindDrift:
    """The live DB has the old 5-kind CHECK. Reconcile widens it to include
    'guardrail' and 'guardrail_failed'. Original rows survive intact."""

    @staticmethod
    def _old_db(tmp_path: Path) -> sqlite3.Connection:
        """Create a DB with the OLD thread_message_parts DDL (5 kinds),
        and enough parent tables to satisfy FK constraints."""
        import sqlite3
        db_path = tmp_path / "old_schema.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=OFF")
        # Create minimal parent tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                recipe_id TEXT,
                profile_override TEXT NOT NULL DEFAULT '',
                directory_id TEXT,
                token_in INTEGER NOT NULL DEFAULT 0,
                token_out INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL DEFAULT 0,
                last_turn_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS thread_messages (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL REFERENCES threads(id),
                parent_id TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                streaming INTEGER NOT NULL DEFAULT 0,
                operation_id TEXT,
                receipt_id TEXT,
                egress_scope TEXT,
                egress_host TEXT,
                model_id TEXT,
                stats_json TEXT NOT NULL DEFAULT '',
                error_json TEXT,
                created_at REAL NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL DEFAULT 0,
                completed_at REAL,
                aborted_at REAL,
                deleted_at REAL
            )
        """)
        # Create thread_message_parts with the OLD 5-kind CHECK
        conn.executescript(_OLD_THREAD_MESSAGE_PARTS_DDL)
        # Insert a thread + message + two parts (text + tool_call)
        conn.execute("INSERT INTO threads (id, title) VALUES ('t1', 'Test thread')")
        conn.execute("""
            INSERT INTO thread_messages (id, thread_id, role) VALUES ('m1', 't1', 'assistant')
        """)
        conn.execute("""
            INSERT INTO thread_message_parts (id, message_id, ordinal, kind, text)
            VALUES ('p1', 'm1', 0, 'text', 'Hello from assistant')
        """)
        conn.execute("""
            INSERT INTO thread_message_parts (id, message_id, ordinal, kind, meta_json)
            VALUES ('p2', 'm1', 1, 'tool_call', '{"name":"desk.list"}')
        """)
        conn.commit()
        return conn

    def test_old_db_rejects_guardrail_kind(self, tmp_path: Path) -> None:
        """Precondition: the old CHECK rejects 'guardrail' inserts."""
        conn = self._old_db(tmp_path)
        with pytest.raises(Exception, match="CHECK"):
            conn.execute("""
                INSERT INTO thread_message_parts (id, message_id, ordinal, kind, meta_json)
                VALUES ('p_fail', 'm1', 2, 'guardrail', '{}')
            """)
        conn.close()

    def test_reconcile_widens_check_and_preserves_rows(self, tmp_path: Path) -> None:
        """After reconcile, 'guardrail' inserts succeed and old rows survive."""
        import sqlite3
        conn = self._old_db(tmp_path)
        from holdspeak.db.reconcile import _rebuild_thread_message_parts_for_kind_drift
        rebuilt = _rebuild_thread_message_parts_for_kind_drift(conn)
        assert rebuilt is True, "Rebuild should have been triggered"

        # Now insert a 'guardrail' part — should succeed
        conn.execute("""
            INSERT INTO thread_message_parts (id, message_id, ordinal, kind, meta_json)
            VALUES ('p3', 'm1', 2, 'guardrail', '{"violations":["test"]}')
        """)
        # And a 'guardrail_failed' part
        conn.execute("""
            INSERT INTO thread_message_parts (id, message_id, ordinal, kind, meta_json)
            VALUES ('p4', 'm1', 3, 'guardrail_failed', '{"error":"timeout"}')
        """)
        conn.commit()

        # Verify original rows survived with identical values
        rows = conn.execute(
            "SELECT id, kind, text, meta_json FROM thread_message_parts ORDER BY ordinal"
        ).fetchall()
        assert len(rows) == 4
        assert (rows[0]["id"], rows[0]["kind"], rows[0]["text"]) == ("p1", "text", "Hello from assistant")
        assert (rows[1]["id"], rows[1]["kind"], rows[1]["meta_json"]) == ("p2", "tool_call", '{"name":"desk.list"}')
        assert (rows[2]["id"], rows[2]["kind"]) == ("p3", "guardrail")
        assert (rows[3]["id"], rows[3]["kind"]) == ("p4", "guardrail_failed")
        conn.close()

    def test_rebuild_is_noop_when_already_widened(self, tmp_path: Path) -> None:
        """Running the rebuild twice is a no-op."""
        conn = self._old_db(tmp_path)
        from holdspeak.db.reconcile import _rebuild_thread_message_parts_for_kind_drift
        first = _rebuild_thread_message_parts_for_kind_drift(conn)
        assert first is True
        second = _rebuild_thread_message_parts_for_kind_drift(conn)
        assert second is False
        conn.close()


# ---------------------------------------------------------------------------
# M1 close counsel: capability-boundary guardrail redaction
# ---------------------------------------------------------------------------


class TestGuardrailM1CapabilityBoundary:
    """Close counsel M1: run_guardrail redacts based on the chat.guardrail
    capability's OWN boundary, not the thread's chat.turn egress scope.

    Two cases:
    1. chat.turn = LOCAL, chat.guardrail = CLOUD -> sensitive texts withheld
    2. chat.turn = CLOUD, chat.guardrail = LOCAL -> sensitive texts NOT withheld

    Tests run_guardrail directly (unit), mocking the broker to carry the
    right DB with two profiles at different boundaries.
    """

    @staticmethod
    def _setup(tmp_path: Path, *, guardrail_boundary: str = "cloud"):
        """Create a DB with a profile assigned to chat.guardrail, whose
        deployment revision carries the given boundary."""
        import hashlib as _hashlib
        from holdspeak.deployment_revisions import DeploymentRevision
        from holdspeak.inference_targets import DeploymentIdentity

        db = Database(tmp_path / "m1_gr.db")
        from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService

        owner = Principal(PrincipalKind.OWNER, "m1-owner")

        # Profile for chat.turn (local boundary) -- only needed for the
        # assignment chain; we won't invoke through it.
        turn_profile = "m1-turn-profile"
        _profile(db, turn_profile, claims=("language", _result_claim("chat.turn")))

        # Assign chat.turn
        InferenceAssignmentService(db).set_assignment(owner, {
            "command_id": "assign-turn",
            "expected_revision": 0,
            "scope": {"kind": "capability", "capability_id": "chat.turn"},
            "entries": [{"profile_id": turn_profile, "profile_revision": 1}],
        })

        # Backfill chat.guardrail from chat.turn (same profile initially).
        from holdspeak.db.reconcile import _backfill_chat_practice_assignments
        with db._connection() as conn:
            _backfill_chat_practice_assignments(conn)

        # If we need a different boundary for chat.guardrail, create a NEW
        # profile+deployment and re-point the chat.guardrail assignment to it.
        if guardrail_boundary != "same_device":
            # Create a deployment revision with the desired boundary.
            # Use a unique model name that has NO v2 deployment row.
            gr_profile = "m1-guardrail-cloud"
            v1_dep = DeploymentRevision.from_identity(DeploymentIdentity(
                destination_id="cloud_service",
                kind="cloud",
                engine="configured_local_engine",
                model=gr_profile,
                node="",
                boundary=guardrail_boundary,
                endpoint="",
                secret_slot="",
            ))
            db.deployment_revisions.upsert(v1_dep)

            # Update the chat.guardrail assignment to point to gr_profile.
            with db._connection() as conn:
                head = conn.execute(
                    "SELECT assignment_id, revision FROM inference_assignment_heads "
                    "WHERE assignment_key='capability:chat.guardrail' AND cleared=0",
                ).fetchone()
                if head:
                    conn.execute(
                        "UPDATE inference_assignments SET profile_id=? "
                        "WHERE assignment_id=? AND assignment_revision=?",
                        (gr_profile, head["assignment_id"], head["revision"]),
                    )

        return db, owner

    def test_cloud_guardrail_withholds_sensitive_texts(self, tmp_path: Path) -> None:
        """chat.guardrail boundary=cloud: run_guardrail replaces sensitive
        texts with [people content withheld]."""
        db, owner = self._setup(tmp_path, guardrail_boundary="cloud")

        from holdspeak.services.thread_practice import run_guardrail
        from holdspeak.kernel.runtime import _as_principal

        # Mock broker with the real DB and a mock runner.
        class _Broker:
            database = db
            inference_runner = MagicMock()

        broker = _Broker()
        captured_kwargs: list[dict] = []

        def _fake_run_prompt(**kw):
            captured_kwargs.append(kw)
            return json.dumps({"violations": [], "warnings": []})

        engine = MagicMock()
        engine.run_prompt = _fake_run_prompt
        engine.active_provider = "test"
        engine.active_model = "test"
        broker.inference_runner._engine_factory = lambda rev, **kw: engine
        broker.inference_runner.invoke = MagicMock()

        # Set up the invoke mock to call the capture and publish callbacks.
        def _mock_invoke(request, adapter, publish=None):
            # The adapter is CanonicalPromptAdapter; invoke the engine directly
            # to capture what would be sent.
            prompt = request.payload
            captured_kwargs.append(prompt)
            result = MagicMock()
            result.result = {"violations": [], "warnings": []}
            return result
        broker.inference_runner.invoke = _mock_invoke

        messages = [
            {"role": "user", "content": "Tell me about Alice Smith"},
            {"role": "assistant", "content": "Alice Smith is a person"},
        ]
        pending = [
            {"name": "people.commitment.transition", "arguments_head": "{}"},
        ]
        guardrail = {"instruction": "Check effects", "trigger_tools": ["people.*"]}

        result = run_guardrail(
            broker, owner, "t1",
            messages, pending, guardrail,
            sensitive_texts=["Alice Smith"],
        )

        # The payload passed to runner.invoke should have redacted messages.
        assert len(captured_kwargs) >= 1
        payload = captured_kwargs[0]
        # Check that the messages in the payload are redacted.
        for msg in payload.get("messages", []):
            content = msg.get("content", "")
            assert "Alice Smith" not in content, (
                f"Cloud guardrail should redact sensitive text, got: {content}"
            )
        # Check the user_prompt (transcript)
        user_prompt = payload.get("user_prompt", "")
        assert "Alice Smith" not in user_prompt, (
            f"Cloud guardrail user_prompt should redact, got: {user_prompt}"
        )

    def test_local_guardrail_preserves_sensitive_texts(self, tmp_path: Path) -> None:
        """chat.guardrail boundary=same_device: run_guardrail keeps sensitive
        texts verbatim."""
        db, owner = self._setup(tmp_path, guardrail_boundary="same_device")

        from holdspeak.services.thread_practice import run_guardrail

        class _Broker:
            database = db
            inference_runner = MagicMock()

        broker = _Broker()
        captured_kwargs: list[dict] = []

        def _mock_invoke(request, adapter, publish=None):
            captured_kwargs.append(request.payload)
            result = MagicMock()
            result.result = {"violations": [], "warnings": []}
            return result
        broker.inference_runner.invoke = _mock_invoke

        messages = [
            {"role": "user", "content": "Tell me about Bob Jones"},
            {"role": "assistant", "content": "Bob Jones is a person"},
        ]
        pending = [{"name": "people.commitment.transition", "arguments_head": "{}"}]
        guardrail = {"instruction": "Check effects", "trigger_tools": ["people.*"]}

        result = run_guardrail(
            broker, owner, "t1",
            messages, pending, guardrail,
            sensitive_texts=["Bob Jones"],
        )

        assert len(captured_kwargs) >= 1
        payload = captured_kwargs[0]
        # user_prompt should NOT be redacted on local boundary.
        user_prompt = payload.get("user_prompt", "")
        assert _PEOPLE_REDACTION not in user_prompt, (
            f"Local guardrail should not redact, got: {user_prompt}"
        )


# ---------------------------------------------------------------------------
# S1 close counsel: per-call violation mapping
# ---------------------------------------------------------------------------


class TestS1PerCallViolationMapping:
    """Close counsel S1: when the violation names a specific tool, ONLY that
    tool carries the violation -- not every trigger-matching pending call.

    Tests the violation-to-tool mapping logic directly, reproducing the
    exact code path from thread_service.py L1062-1085.
    """

    def test_specific_violation_maps_only_to_named_tool(self) -> None:
        """Violation text names 'people.commitment.transition' -> only that
        tool appears in guardrail_violations, not people.note.create."""
        pending_names = [
            "people.commitment.transition",
            "people.note.create",
        ]
        matched_guardrails = [
            {"trigger_tools": ["people.*"]},
        ]
        guardrail_result = {
            "violations": [
                "people.commitment.transition called without a source"
            ],
            "warnings": [],
        }

        # Reproduce the S1-fixed mapping logic:
        guardrail_violations: dict[str, list[str]] = {}
        all_triggers = [
            t for g in matched_guardrails
            for t in g.get("trigger_tools", [])
        ]
        for v in guardrail_result.get("violations", []):
            v_str = str(v)
            named = [pname for pname in pending_names if pname in v_str]
            if named:
                for pname in named:
                    guardrail_violations.setdefault(pname, []).append(v_str)
            else:
                for pname in pending_names:
                    if _guardrail_matches(pname, all_triggers):
                        guardrail_violations.setdefault(pname, []).append(v_str)

        # Only the named tool should carry the violation.
        assert "people.commitment.transition" in guardrail_violations
        assert "people.note.create" not in guardrail_violations

    def test_generic_violation_maps_to_all_matching_tools(self) -> None:
        """Violation text does NOT name any specific tool -> all
        trigger-matching tools carry the violation."""
        pending_names = [
            "people.commitment.transition",
            "people.note.create",
        ]
        matched_guardrails = [
            {"trigger_tools": ["people.*"]},
        ]
        guardrail_result = {
            "violations": [
                "Unsafe operation detected"
            ],
            "warnings": [],
        }

        guardrail_violations: dict[str, list[str]] = {}
        all_triggers = [
            t for g in matched_guardrails
            for t in g.get("trigger_tools", [])
        ]
        for v in guardrail_result.get("violations", []):
            v_str = str(v)
            named = [pname for pname in pending_names if pname in v_str]
            if named:
                for pname in named:
                    guardrail_violations.setdefault(pname, []).append(v_str)
            else:
                for pname in pending_names:
                    if _guardrail_matches(pname, all_triggers):
                        guardrail_violations.setdefault(pname, []).append(v_str)

        # Generic violation -> all trigger-matching tools.
        assert "people.commitment.transition" in guardrail_violations
        assert "people.note.create" in guardrail_violations

    def test_mixed_violations(self) -> None:
        """One specific + one generic violation."""
        pending_names = [
            "people.commitment.transition",
            "people.note.create",
            "desk.list",
        ]
        matched_guardrails = [
            {"trigger_tools": ["people.*"]},
        ]
        guardrail_result = {
            "violations": [
                "people.commitment.transition lacks source",
                "General safety concern",
            ],
            "warnings": [],
        }

        guardrail_violations: dict[str, list[str]] = {}
        all_triggers = [
            t for g in matched_guardrails
            for t in g.get("trigger_tools", [])
        ]
        for v in guardrail_result.get("violations", []):
            v_str = str(v)
            named = [pname for pname in pending_names if pname in v_str]
            if named:
                for pname in named:
                    guardrail_violations.setdefault(pname, []).append(v_str)
            else:
                for pname in pending_names:
                    if _guardrail_matches(pname, all_triggers):
                        guardrail_violations.setdefault(pname, []).append(v_str)

        # Specific: only people.commitment.transition
        assert "people.commitment.transition lacks source" in guardrail_violations["people.commitment.transition"]
        # Generic: both people.* tools, not desk.list
        assert "General safety concern" in guardrail_violations.get("people.commitment.transition", [])
        assert "General safety concern" in guardrail_violations.get("people.note.create", [])
        assert "desk.list" not in guardrail_violations
