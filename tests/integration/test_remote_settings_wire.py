"""The hub's own Settings > Other devices answers (the test diet, 2026-10-11).

``web/src/pages/cores/__tests__/remoteAccess.test.tsx`` replays these answers.
Its typed credential carried ``palette`` as an array; the hub sends the issued
palette's NAME, a string (``holdspeak/web/routes/mcp_http.py``, PHILO-9-07).
This test boots the real hub on an isolated HOME, issues a credential through
the route, and fences the stored answers against the hub's shape
(``HOLDSPEAK_WIRE_WRITE=1`` rewrites them). Nothing is typed by hand (the SCAR
LAW).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402
from tests.integration import test_desk_agents_wire as wire  # noqa: E402

pytestmark = pytest.mark.timeout(240)

WIRE_DIR = REPO / "web" / "src" / "pages" / "cores" / "__tests__" / "wire"
BY = "tests/integration/test_remote_settings_wire.py"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database

    yield seeds._boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any) -> Any:
    assert response.status_code == 200, (response.status_code, response.text[:300])
    return response.json()


def test_the_remote_settings_answers_are_the_hubs(hub: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.principals import AgentCredentialStore

    monkeypatch.setattr(wire, "WIRE_DIR", WIRE_DIR)
    # The hub's credential store is one per process; a store of its own keeps
    # credentials other tests issued in this worker out of the answer.
    monkeypatch.setattr(hub.server.app.state, "agent_credentials", AgentCredentialStore())
    off = _ok(hub.client.get("/api/settings/remote"))
    _ok(hub.client.put("/api/settings/remote", json={"enabled": True, "bind_host": "100.64.0.2", "port": 8765}))
    issued = _ok(hub.client.post("/api/settings/remote/credentials",
                                 json={"identity": "sweep-runner", "palette": "PROJECT"}))
    listed = _ok(hub.client.get("/api/settings/remote"))

    # The palette is the issued NAME, a string, in the issue answer and the list.
    assert issued["palette"] == "PROJECT"
    [credential] = listed["credentials"]
    assert credential["palette"] == "PROJECT"

    url = str(hub.client.base_url)
    wire._fence("remote-settings.off", off, tmp_path, url, by=BY)
    wire._fence("remote-settings.issued", {**issued, "token": "hs_agent_redacted"}, tmp_path, url, by=BY)
    wire._fence("remote-settings.one-credential", listed, tmp_path, url, by=BY)
