"""Parked 2026-11-08 (Lane W): the cases of five thread frames no face read.

thread_turn_started, thread_status_line and thread_call_state (with
thread_guardrail and thread_compacted, whose cases now assert the persisted
row) were broadcast to nobody once the Thread window was parked. The
emitters are parked in holdspeak/kernel/_parked/thread_frames.py. These
cases are kept as text, one per original file; they are not collected.
"""


# ── from tests/unit/test_thread_service.py ──

def test_turn_broadcasts_started_with_correct_data(service: ThreadService, broadcasts) -> None:
    t = service.create(title="Broadcast test")
    result = asyncio.run(service.start_turn(OWNER, t["id"], "Check broadcasts"))
    _await_done(broadcasts, 1)

    started_frames = [(t, d) for t, d in broadcasts if t == "thread_turn_started"]
    assert len(started_frames) == 1
    _, data = started_frames[0]
    assert data["thread_id"] == result["thread_id"]
    assert data["message_id"] == result["assistant_message_id"]
    assert data["user_message_id"] == result["user_message_id"]


# ── from tests/unit/test_thread_tool_loop.py ──

    def test_status_line_emitted_on_second_pass(self, db, broadcast_fn, broadcasts):
        svc = ThreadService(
            db, broadcast=broadcast_fn,
            broker=_ToolCallBroker(),
            tool_dispatch_fn=_fake_dispatch,
        )
        t = svc.create(title="Status test")
        asyncio.run(svc.start_turn(OWNER, t["id"], "Test"))
        _wait_done(broadcasts)

        status_frames = [d for ft, d in broadcasts if ft == "thread_status_line"]
        assert len(status_frames) >= 1


# ── from tests/unit/test_thread_call_mode.py ──

    def test_patch_same_value_no_frame(self, tmp_path: Path) -> None:
        """Patching to the same value emits no frame."""
        svc, db, broadcasts = self._svc(tmp_path)
        t = svc.create(title="No Change")
        svc.patch(t["id"], call_mode=0)
        frames = [(ft, d) for ft, d in broadcasts if ft == "thread_call_state"]
        assert len(frames) == 0


# ── from tests/unit/test_thread_call_mode.py ──

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


# ── from tests/unit/test_thread_call_mode.py ──

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
