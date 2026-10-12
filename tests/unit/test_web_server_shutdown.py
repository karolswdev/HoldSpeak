"""The hub's shutdown stops every conductor its startup started.

Successor of the parked source pin
``test_phase200_ci_isolation::test_the_shutdown_handler_stops_every_conductor_it_started``
(HS-200-03): a conductor that outlives its app keeps ticking against a
database nobody owns. This boots a real MeetingWebServer, sees the always-on
conductors running, stops the server, and reads each conductor module's
global: every one must be cleared.
"""
from __future__ import annotations

import importlib

CONDUCTORS = (
    "holdspeak.calendar_ingest_conductor",
    "holdspeak.workbench_conductor",
    "holdspeak.scheduled_recording_conductor",
    "holdspeak.intel_queue_conductor",
    "holdspeak.memory_conductor",
    "holdspeak.defaults_conductor",
)
# Started unconditionally at startup (the others may refuse, e.g. a hub that
# does not own the database starts no intel-queue drainer).
ALWAYS_STARTED = ("holdspeak.workbench_conductor", "holdspeak.scheduled_recording_conductor")


def test_stopping_the_server_clears_every_conductor(tmp_path, monkeypatch) -> None:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token="shutdown",
    )
    server.start()
    try:
        running = {name: importlib.import_module(name)._conductor for name in ALWAYS_STARTED}
        assert all(conductor is not None for conductor in running.values()), running
    finally:
        server.stop()
        reset_database()

    leaked = {
        name: module._conductor
        for name in CONDUCTORS
        if (module := importlib.import_module(name))._conductor is not None
    }
    assert leaked == {}, f"conductors still set after shutdown: {sorted(leaked)}"

