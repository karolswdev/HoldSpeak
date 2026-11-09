# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_cadence_mcp.py to restore.

# ruff: noqa


# --- TestCadenceStatus: P2: dispatches to a fake service and asserts the fake's canned answer comes back
class TestCadenceStatus:
    def test_dispatch(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.status", {})
        assert payload["enabled"] is True
        assert payload["pressure"] == "normal"


# --- TestCadenceLoops: P2: dispatches to a fake service and asserts the fake's canned answer comes back
class TestCadenceLoops:
    def test_dispatch_default(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.loops", {})
        assert len(payload["loops"]) == 1
        assert payload["loops"][0]["id"] == "loop-1"

    def test_dispatch_include_terminal(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.loops", {"include_terminal": True})
        assert len(payload["loops"]) == 1


# --- TestCadenceGetLoop::test_dispatch_async_wrapped: P2: dispatches to a fake service and asserts the fake's canned answer comes back
# (was a method of class TestCadenceGetLoop)
def test_dispatch_async_wrapped(self, _patch_cadence: FakeCadenceService) -> None:
    """get_loop is async; dispatch wraps it in _run()."""
    payload = _call_ok("cadence.get_loop", {"loop_id": "loop-42"})
    assert payload["id"] == "loop-42"
    assert payload["next_action"]["kind"] == "nudge"


# --- TestCadenceGetLoop::test_proves_run_wrapping: P2: dispatches to a fake service and asserts the fake's canned answer comes back
# (was a method of class TestCadenceGetLoop)
def test_proves_run_wrapping(self, monkeypatch: pytest.MonkeyPatch) -> None:
    """Prove _run wrapping by verifying a canned coroutine executes."""
    call_log: list[str] = []

    async def _canned_get_loop(self: Any, principal: Any, loop_id: str) -> dict[str, Any]:
        call_log.append(f"get_loop:{loop_id}")
        return {"id": loop_id, "status": "open", "next_action": {"kind": "check"}}

    class StubService:
        get_loop = _canned_get_loop

    monkeypatch.setattr(cadence_mod, "_service", lambda: StubService())
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

    payload = _call_ok("cadence.get_loop", {"loop_id": "coro-proof"})
    assert payload["id"] == "coro-proof"
    assert call_log == ["get_loop:coro-proof"]


# --- TestCadenceBrief: P2: dispatches to a fake service and asserts the fake's canned answer comes back
class TestCadenceBrief:
    def test_dispatch(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.brief", {})
        assert payload["headline"] == "All quiet"


# --- TestCadenceCloseout: P2: dispatches to a fake service and asserts the fake's canned answer comes back
class TestCadenceCloseout:
    def test_dispatch(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.closeout", {})
        assert "recs" in payload


# --- TestCadenceHistory: P2: dispatches to a fake service and asserts the fake's canned answer comes back
class TestCadenceHistory:
    def test_dispatch_default(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.history", {})
        assert "nudges" in payload

    def test_dispatch_with_limit(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.history", {"limit": 10})
        assert "nudges" in payload


# --- TestCadenceAudit: P2: dispatches to a fake service and asserts the fake's canned answer comes back
class TestCadenceAudit:
    def test_dispatch(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.audit", {})
        assert "loops" in payload


# --- TestCadenceSnooze::test_dispatch_with_until: P2: dispatches to a fake service and asserts the fake's canned answer comes back
# (was a method of class TestCadenceSnooze)
def test_dispatch_with_until(self, _patch_cadence: FakeCadenceService) -> None:
    payload = _call_ok("cadence.snooze", {"loop_id": "loop-1", "until": "2026-08-17T00:00:00"})
    assert payload["id"] == "loop-1"


# --- TestCadenceSnooze::test_dispatch_with_hours: P2: dispatches to a fake service and asserts the fake's canned answer comes back
# (was a method of class TestCadenceSnooze)
def test_dispatch_with_hours(self, _patch_cadence: FakeCadenceService) -> None:
    payload = _call_ok("cadence.snooze", {"loop_id": "loop-1", "hours": 12})
    assert payload["id"] == "loop-1"


# --- TestCadenceSetStatus::test_dispatch: P2: dispatches to a fake service and asserts the fake's canned answer comes back
# (was a method of class TestCadenceSetStatus)
def test_dispatch(self, _patch_cadence: FakeCadenceService) -> None:
    payload = _call_ok("cadence.set_status", {"loop_id": "loop-1", "status": "closed"})
    assert payload["status"] == "closed"


# --- TestCadenceRunNow: P2: dispatches to a fake service and asserts the fake's canned answer comes back
class TestCadenceRunNow:
    def test_dispatch(self, _patch_cadence: FakeCadenceService) -> None:
        payload = _call_ok("cadence.run_now", {})
        assert payload["open_loops"] == 3


# --- TestCadenceApplyCloseout::test_dispatch: P2: dispatches to a fake service and asserts the fake's canned answer comes back
# (was a method of class TestCadenceApplyCloseout)
def test_dispatch(self, _patch_cadence: FakeCadenceService) -> None:
    payload = _call_ok("cadence.apply_closeout", {
        "decisions": [{"loop_id": "loop-1", "action": "close"}],
    })
    assert payload["applied"] == 1
