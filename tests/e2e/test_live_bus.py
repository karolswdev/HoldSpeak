"""HS-72-08 — one live bus: the web opens exactly ONE /ws per page.

Drives the REAL app in a browser (the route pre-flight's harness posture):

1. **One socket per page** — /live (whose dashboard used to own a second
   socket), /dictation (shell widgets), /presence (the chromeless HUD), and
   /setup (the onboarding listener) each open exactly one runtime WebSocket.
2. **A real broadcast reaches the widgets** — the server broadcasts a
   `runtime_activity` frame; the /presence card renders it (through the bus,
   not a private socket).
3. **Reconnect recovery** — the server is stopped and restarted on the same
   port; the page opens a fresh socket by itself (the bus's backoff).

Local runs skip cleanly when Playwright or the production bundle is absent.
Hosted CI sets ``HOLDSPEAK_REQUIRE_LIVE_BUS=1`` and installs both, turning
either absence into a collection failure.
"""
from __future__ import annotations

import importlib.util
import os
import threading
import time
from pathlib import Path

import pytest

REQUIRE_LIVE_BUS = os.environ.get("HOLDSPEAK_REQUIRE_LIVE_BUS") == "1"
if importlib.util.find_spec("playwright") is None:
    if REQUIRE_LIVE_BUS:
        raise RuntimeError("CI live-bus gate requires the Playwright package")
    pytest.skip(
        "needs Playwright + a browser",
        allow_module_level=True,
    )
BUILT_INDEX = (
    Path(__file__).resolve().parents[2]
    / "holdspeak"
    / "static"
    / "_built"
    / "index.html"
)
if not BUILT_INDEX.is_file():
    if REQUIRE_LIVE_BUS:
        raise RuntimeError("CI live-bus gate requires a built production bundle")
    pytest.skip(
        "needs a built production web bundle",
        allow_module_level=True,
    )
pytest.importorskip("fastapi.testclient", reason="requires meeting/web dependencies")

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]

def _free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# A free port, chosen once per module: the restart test reopens the same one.
# (It was a fixed 8917, shared by every run on the machine.)
PORT = _free_port()


# HS-106-02 made every request derive a principal, including on loopback, so a
# browser that never bootstraps the owner token is refused at the socket
# (`principal=none missing_right=owner`).  The real Desk gets its token from the
# tokenized first-load URL; this harness has to do the same, and both servers in
# the restart test must share one token or the reconnect authenticates against a
# credential the page has never seen.
TOKEN = "live-bus-e2e-owner-token"


def _page_url(route: str) -> str:
    return f"http://127.0.0.1:{PORT}{route}?token={TOKEN}"


def _make_server():
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: {"activity": {"state": "idle", "source": "runtime"}},
        ),
        host="127.0.0.1",
        auth_token=TOKEN,
    )


class _Uvicorn:
    def __init__(self, app):
        import uvicorn

        self._server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="error")
        )
        self._thread = threading.Thread(target=self._server.run, daemon=True)

    def start(self):
        self._thread.start()
        deadline = time.time() + 10
        while not self._server.started:
            if time.time() > deadline:
                raise RuntimeError("uvicorn did not start")
            time.sleep(0.05)

    def stop(self):
        self._server.should_exit = True
        self._thread.join(timeout=10)


@pytest.fixture(scope="module", autouse=True)
def _isolated_hub(tmp_path_factory):
    """This module's hubs read their own database and HOME. They read the
    default database before: on the tape (8 xdist workers, one HOME) every
    worker shared that file, and the hub's boot failed with "no such table:
    inference_model_acquisitions" while another worker was creating it (all
    three tests red together, 2026-10-12). The same isolation as
    glass_infra._boot; the singleton is reset on the way in and out."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database

    tmp = tmp_path_factory.mktemp("live-bus")
    home = tmp / "home"
    home.mkdir()
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("HOME", str(home))
        for key, value in {
            "HOLDSPEAK_MACOS_CALENDAR": "0", "HOLDSPEAK_AGENT_STATE": "off", "GIT_CONFIG_NOSYSTEM": "1",
            "HOLDSPEAK_TEST_NO_REAL_CLI": "1", "HOLDSPEAK_DESKTOP_NOTIFY": "0", "HOLDSPEAK_ACTIVE_TARGET": "off",
            "GH_CONFIG_DIR": str(home / ".config" / "gh"), "XDG_CONFIG_HOME": str(home / ".config"),
            "HOLDSPEAK_CHANNEL_KEYSTORE_FILE": str(home / "channel-keys.json"),
            "HOLDSPEAK_PEOPLE_KEYSTORE_FILE": str(home / "people-key.json"),
            "CLAUDE_CONFIG_DIR": str(home / ".claude"), "CODEX_HOME": str(home / ".codex"),
            "PI_CODING_AGENT_DIR": str(home / ".pi" / "agent"),
        }.items():
            mp.setenv(key, value)
        mp.delenv("ANTHROPIC_API_KEY", raising=False)
        mp.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        mp.setattr(db_core, "DEFAULT_DB_PATH", tmp / "holdspeak.db")
        reset_database()
        mp.setattr(db_core, "_db", None, raising=False)
        mp.setattr(db_core, "_observer", None, raising=False)
        yield
        reset_database()


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


def _count_runtime_sockets(page, url: str, settle_s: float = 2.5) -> int:
    sockets: list[str] = []
    page.on("websocket", lambda ws: sockets.append(ws.url))
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(int(settle_s * 1000))
    return sum(1 for u in sockets if u.rstrip("/").endswith("/ws"))


def test_every_live_page_opens_exactly_one_runtime_socket(browser):
    server = _make_server()
    uv = _Uvicorn(server.app)
    uv.start()
    try:
        for route in ("/live", "/dictation", "/presence", "/setup"):
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            n = _count_runtime_sockets(page, _page_url(route))
            page.close()
            assert n == 1, f"{route} opened {n} runtime sockets (want exactly 1)"
            assert not errors, f"{route} page errors: {errors}"
    finally:
        uv.stop()


def test_a_real_broadcast_reaches_the_presence_card_via_the_bus(browser):
    server = _make_server()
    uv = _Uvicorn(server.app)
    uv.start()
    try:
        page = browser.new_page()
        page.goto(_page_url("/presence"), wait_until="networkidle")
        page.wait_for_timeout(800)
        server.broadcast(
            "runtime_activity",
            {
                "state": "transcribing",
                "label": "Transcribing",
                "source": "dictation",
                "window": {"visible": True},
            },
        )
        page.wait_for_function(
            "() => document.querySelector('.presence-card .gadget-lamp')"
            " && document.querySelector('.presence-card .gadget-lamp').textContent.includes('Transcribing')",
            timeout=8000,
        )
        page.close()
    finally:
        uv.stop()


def test_the_bus_reconnects_after_a_server_restart(browser):
    server = _make_server()
    uv = _Uvicorn(server.app)
    uv.start()
    page = browser.new_page()
    sockets: list[str] = []
    page.on("websocket", lambda ws: sockets.append(ws.url))
    try:
        page.goto(_page_url("/presence"), wait_until="networkidle")
        page.wait_for_timeout(1000)
        first = sum(1 for u in sockets if u.rstrip("/").endswith("/ws"))
        assert first == 1
        uv.stop()
        page.wait_for_timeout(500)

        server2 = _make_server()
        uv2 = _Uvicorn(server2.app)
        uv2.start()
        try:
            deadline = time.time() + 20
            while time.time() < deadline:
                total = sum(1 for u in sockets if u.rstrip("/").endswith("/ws"))
                if total >= 2:
                    break
                page.wait_for_timeout(300)
            total = sum(1 for u in sockets if u.rstrip("/").endswith("/ws"))
            assert total >= 2, "the bus never reopened a socket after restart"
            # The reconnected stream is live: a broadcast lands on the card.
            page.wait_for_timeout(500)
            server2.broadcast(
                "runtime_activity",
                {"state": "recording", "label": "Recording", "window": {"visible": True}},
            )
            page.wait_for_function(
                "() => document.querySelector('.presence-card .gadget-lamp')"
                " && document.querySelector('.presence-card .gadget-lamp').textContent.includes('Recording')",
                timeout=8000,
            )
        finally:
            uv2.stop()
    finally:
        page.close()
        if uv._thread.is_alive():
            uv.stop()
