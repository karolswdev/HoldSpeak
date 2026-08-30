"""HS-151-06 — the conductor-wiring pin (the attended leg's catch).

The production `start_meeting_fn` wired at web_server startup was born
broken in HS-136-01 and NO production fire ever succeeded: the lambdas
referenced an out-of-scope name AND probed runtime-private method names
the WebRuntimeCallbacks contract never carries, while the `if hasattr`
guards parsed inside the lambda bodies so boot never raised. Every
walk wired its own harness callbacks and never exercised this path.

This pin invokes the ACTUAL wired functions — no harness substitute —
against both a minimal harness bundle (must no-op, never raise) and a
runtime-shaped spy (must set the HS-147-04 pending seam on the
on_start owner and call through with the principal).
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def live_server(tmp_path, monkeypatch):
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    # The conductor is a PROCESS-GLOBAL singleton created once; under
    # xdist another hub test in this worker may have wired it already,
    # leaving stale start/stop fns from a dead server. Reset it so THIS
    # server's startup wires fresh (the exact fragility this pin guards).
    import holdspeak.scheduled_recording_conductor as src
    if src._conductor is not None:
        try:
            src._conductor.stop()
        except Exception:
            pass
        src._conductor = None
    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token="pin",
    )
    server.start()
    try:
        yield server
    finally:
        server.stop()
        reset_database()


def _wired_fns():
    from holdspeak import scheduled_recording_conductor as src

    conductor = src._conductor
    assert conductor is not None, "the conductor must be running after startup"
    assert callable(conductor._start_meeting_fn), "start_meeting_fn must be wired"
    assert callable(conductor._stop_meeting_fn), "stop_meeting_fn must be wired"
    return conductor._start_meeting_fn, conductor._stop_meeting_fn


class _SpyRuntime:
    """Runtime-shaped: carries the pending seam and a bound start method."""

    def __init__(self) -> None:
        self.pending_title = None
        self.pending_calendar_event_id = None
        self.starts: list = []
        self.stops: int = 0

    def _start_meeting(self, *, principal=None):
        self.starts.append({
            "principal": principal,
            "title": self.pending_title,
            "cal": self.pending_calendar_event_id,
        })
        return {"ok": True}

    def _on_meeting_stop(self):
        self.stops += 1
        return {"stopped": True}


def test_wired_fire_and_stop_reach_the_contract(live_server):
    from holdspeak.web_server import WebRuntimeCallbacks

    start_fn, stop_fn = _wired_fns()

    # 1. The harness bundle has no on_start/on_meeting_stop: both wired
    #    functions must NO-OP — never raise. (The historic failures:
    #    NameError('callbacks'); then a silent hasattr no-op.)
    assert start_fn(principal=object(), title="pin", calendar_event_id=None) is None
    assert stop_fn() is None

    # 2. A runtime-shaped callbacks bundle: the fire sets the HS-147-04
    #    pending seam ON THE on_start OWNER and calls through with the
    #    principal; the stop calls on_meeting_stop.
    spy = _SpyRuntime()
    live_server._callbacks = WebRuntimeCallbacks(
        on_bookmark=lambda *_: None,
        on_stop=lambda: None,
        get_state=lambda: {},
        on_start=spy._start_meeting,
        on_meeting_stop=spy._on_meeting_stop,
    )
    marker = object()
    result = start_fn(principal=marker, title="1:1 w/ Pin", calendar_event_id="ev-1")
    assert result == {"ok": True}
    assert spy.starts and spy.starts[0]["principal"] is marker
    assert spy.starts[0]["title"] == "1:1 w/ Pin"
    assert spy.starts[0]["cal"] == "ev-1"
    assert stop_fn() == {"stopped": True}
    assert spy.stops == 1
