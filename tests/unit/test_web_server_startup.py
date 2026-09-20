"""Startup ownership and listener readiness for the meeting web server."""

from __future__ import annotations

import asyncio
import socket
import threading
from pathlib import Path
from typing import Any

import pytest


def _server(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Build a bare server against an isolated config and database."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database

    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    monkeypatch.setattr(db_core, "_db", None, raising=False)
    monkeypatch.setattr(db_core, "_observer", None, raising=False)

    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token="startup-test",
    )


@pytest.mark.timeout(30)
def test_start_waits_for_listener_after_lifespan_startup(tmp_path, monkeypatch) -> None:
    """A post-lifespan gate must keep start blocked until Uvicorn binds."""
    server = _server(tmp_path, monkeypatch)
    entered = threading.Event()
    release = threading.Event()
    returned = threading.Event()
    outcome: dict[str, Any] = {}

    async def hold_before_listener() -> None:
        entered.set()
        await asyncio.to_thread(release.wait)

    # MeetingWebServer's own startup handler is registered first and sets its
    # internal event before Uvicorn creates its listener. This handler makes
    # that ordering deterministic without adding a test sleep.
    server.app.router.on_startup.append(hold_before_listener)

    def start() -> None:
        try:
            outcome["url"] = server.start()
        except BaseException as exc:  # pragma: no cover - assertion context
            outcome["error"] = exc
        finally:
            returned.set()

    thread = threading.Thread(target=start, daemon=True)
    thread.start()
    try:
        assert entered.wait(timeout=10), "post-lifespan startup gate did not run"
        assert not returned.wait(timeout=1), (
            "start() returned before the Uvicorn listener was ready"
        )
        release.set()
        assert returned.wait(timeout=10), "start() did not return after listener readiness"
        assert "error" not in outcome, outcome
        assert outcome.get("url")
        assert server.port is not None
        with socket.create_connection((server.host, server.port), timeout=5):
            pass
    finally:
        release.set()
        server.stop()
        thread.join(timeout=10)

    assert not thread.is_alive(), "server start thread did not finish"


@pytest.mark.timeout(30)
def test_start_raises_when_uvicorn_exits_during_startup(tmp_path, monkeypatch) -> None:
    """A failed server must not publish a URL for a dead listener."""
    import holdspeak.web_server as web_server

    startup_failed = threading.Event()
    returned = threading.Event()
    outcome: dict[str, Any] = {}
    owner: dict[str, Any] = {}

    class FailedUvicornServer:
        def __init__(self, config: Any) -> None:
            self.config = config
            self.started = False
            self.should_exit = False
            owner["uvicorn"] = self

        def run(self) -> None:
            # This models Uvicorn completing lifespan and then aborting before
            # it can create a listener. A real started server would remain
            # alive until should_exit; this one never reaches started=True.
            owner["meeting"]._started.set()
            self.should_exit = True
            startup_failed.set()

    monkeypatch.setattr(web_server.uvicorn, "Server", FailedUvicornServer)
    server = _server(tmp_path, monkeypatch)
    owner["meeting"] = server

    def start() -> None:
        try:
            outcome["url"] = server.start()
        except BaseException as exc:
            outcome["error"] = exc
        finally:
            returned.set()

    thread = threading.Thread(target=start, daemon=True)
    thread.start()
    try:
        assert startup_failed.wait(timeout=10), "fake startup failure did not occur"
        assert returned.wait(timeout=10), "start() did not finish after server failure"
    finally:
        server.stop()
        thread.join(timeout=10)

    assert not thread.is_alive(), "startup failure thread did not finish"
    assert "url" not in outcome, outcome
    assert isinstance(outcome.get("error"), RuntimeError), outcome
