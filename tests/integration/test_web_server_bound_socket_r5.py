"""Conductor R5: a hub with no configured port holds its port from pick to serve.

``MeetingWebServer.start`` used to pick a free port (bind 0, close) and let
uvicorn bind it again AFTER lifespan startup. Between the two, any other
process could take the port. It now binds the socket once and hands that very
socket to uvicorn.
"""
from __future__ import annotations

import socket
import threading
import urllib.request
from unittest.mock import MagicMock

import pytest

import holdspeak.web_server as web_server_module
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def isolated_db(tmp_path):
    from holdspeak.db import get_database, reset_database

    reset_database()
    db = get_database(tmp_path / "bound-socket.db")
    yield db
    reset_database()


def _server() -> MeetingWebServer:
    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={}),
        ),
        host="127.0.0.1",
    )


def _health(url: str) -> int:
    with urllib.request.urlopen(f"{url}/health", timeout=30) as response:
        return response.status


@pytest.mark.integration
def test_the_port_is_held_during_startup_and_served_on_the_picked_socket(isolated_db, monkeypatch) -> None:
    picked: list[socket.socket] = []
    real_bind = web_server_module._bind_listen_socket

    def recording_bind(host: str, preferred: int) -> socket.socket:
        sock = real_bind(host, preferred)
        picked.append(sock)
        return sock

    monkeypatch.setattr(web_server_module, "_bind_listen_socket", recording_bind)
    server = _server()
    taken_during_startup: list[bool] = []

    async def probe() -> None:
        # Lifespan startup runs BEFORE uvicorn listens: the window the old
        # pick-close-rebind left open. Another bind of the port must fail now.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as other:
            try:
                other.bind(("127.0.0.1", int(server.port)))
            except OSError:
                taken_during_startup.append(False)
            else:
                taken_during_startup.append(True)

    server.app.router.on_startup.insert(0, probe)
    url = server.start()
    try:
        assert taken_during_startup == [False], "another socket bound the hub's port during startup"
        [sock] = picked
        assert sock.getsockname()[1] == server.port
        assert url.rstrip("/").endswith(f":{server.port}")
        listening = [
            s.fileno()
            for srv in server._server.servers  # type: ignore[union-attr]
            for s in srv.sockets
        ]
        assert sock.fileno() in listening, (sock.fileno(), listening)
        assert _health(url) == 200
    finally:
        server.stop()
    assert server._listen_sockets is None


@pytest.mark.integration
def test_concurrent_hubs_never_collide_on_a_port(isolated_db) -> None:
    for _round in range(8):
        servers = [_server(), _server()]
        urls: list[str] = []
        errors: list[BaseException] = []
        lock = threading.Lock()

        def boot(server: MeetingWebServer) -> None:
            try:
                url = server.start()
                with lock:
                    urls.append(url)
            except BaseException as exc:  # noqa: BLE001 - reported below
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=boot, args=(s,)) for s in servers]
        try:
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(60)
            assert errors == [], errors
            assert len(set(urls)) == 2, urls
            assert all(_health(url) == 200 for url in urls)
        finally:
            for server in servers:
                server.stop()
