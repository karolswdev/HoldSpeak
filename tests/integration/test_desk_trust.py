"""Trust (Privacy & Trust window), through the real hub (the test diet, 2026-10-11).

The hub boots over an isolated database and HOME (the rig of
``tests/unit/test_philo5_the_loop.py``). Each test saves Send destinations
through the real route and reads ``/api/setup/status`` the way the Trust
window does, asserting the fact the browser test it replaces asserted.

The wire fixtures under ``web/src/desk/__tests__/fixtures/trust-wire/`` are
what the Trust vitest (``web/src/desk/__tests__/trust.app.test.tsx``) answers
its ``fetch`` with. ``test_the_trust_wire_fixtures_carry_no_invented_field``
proves every field in them is a field the live hub sends (the scar law). To
write them again from the live hub: ``HOLDSPEAK_WRITE_WIRE_FIXTURES=1``.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
from _philo10_send import Hub, _boot  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "trust-wire"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)
    return fake


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, home: Path):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _save(hub: Hub, name: str, folder: Path, **extra: Any) -> dict[str, Any]:
    folder.mkdir(parents=True, exist_ok=True)
    resp = hub.client.post("/api/channels/destinations",
                           json={"name": name, "channel": "file", "folder": str(folder), **extra})
    assert resp.status_code == 200, resp.text
    return resp.json()["destination"]


def _trust(hub: Hub) -> dict[str, Any]:
    resp = hub.client.get("/api/setup/status")
    assert resp.status_code == 200, resp.text
    return resp.json()["trust"]


def _row(trust: dict[str, Any], name: str) -> dict[str, Any]:
    [row] = [d for d in trust["destinations"] if d["name"] == name]
    return row


def test_a_saved_folder_on_this_device_is_counted_and_sends_nothing_out(hub: Hub, home: Path) -> None:
    """replaces: tests/e2e/test_honest_faces_glass.py::test_trust_counts_the_saved_destination (the hub half)"""
    _save(hub, "Team updates", home / "Documents" / "HoldSpeak" / "Team updates")
    trust = _trust(hub)
    saved = [d for d in trust["destinations"] if d.get("saved")]
    # Two saved destinations: the built-in HoldSpeak folder and Team updates.
    assert sorted(d["name"] for d in saved) == ["HoldSpeak folder", "Team updates"], saved
    team = _row(trust, "Team updates")
    # A folder on this device is in use and sends nothing out.
    assert (team["enabled"], team["saved"], team["boundary"]) == (False, True, "This device"), team
    assert team["destination"] == "~/Documents/HoldSpeak/Team updates", team
    assert not [d for d in trust["destinations"] if d["enabled"]], trust["destinations"]
    assert trust["transcript_egress"] == "none"
    assert str(home) not in json.dumps(trust)


def test_a_synced_folder_is_an_external_destination(hub: Hub, home: Path) -> None:
    """replaces: tests/e2e/test_honest_faces_glass.py::test_trust_scope_names_a_saved_external_destination (the hub half)"""
    saved = _save(hub, "Synced updates", home / "Dropbox" / "Team updates", synced=True)
    assert saved["badge"] == "cloud", saved
    trust = _trust(hub)
    synced = _row(trust, "Synced updates")
    assert (synced["enabled"], synced["saved"], synced["boundary"]) == (True, True, "Outside this device"), synced
    assert trust["summary"] == "1 external destination enabled."


def test_a_virgin_desk_has_no_destination_and_keeps_data_here(hub: Hub) -> None:
    """replaces: tests/e2e/test_hs201_one_thing_glass.py::TestOneThing::test_chip_and_trust_agree
    (the hub half: zero destinations enabled while the actuator permission is on;
    the one saved row is the built-in HoldSpeak folder, on this device)."""
    trust = _trust(hub)
    assert not [d for d in trust["destinations"] if d["enabled"]], trust["destinations"]
    saved = [d for d in trust["destinations"] if d.get("saved")]
    assert [(d["name"], d["boundary"]) for d in saved] == [("HoldSpeak folder", "This device")], saved
    assert trust["actuators_enabled"] is True, trust
    assert trust["transcript_egress"] == "none"


# ── the wire fixtures the Trust vitest reads ─────────────────────────


def _scrub(value: Any, tmp: str) -> Any:
    if isinstance(value, dict):
        return {k: _scrub(v, tmp) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v, tmp) for v in value]
    if isinstance(value, str) and tmp in value:
        return value.replace(tmp, "/Users/owner")
    return value


def _invented(fixture: Any, live: Any, path: str = "$") -> list[str]:
    """Every field the fixture carries that the live answer does not."""
    if isinstance(fixture, dict):
        if not isinstance(live, dict):
            return [f"{path} is an object, the hub sends {type(live).__name__}"]
        out: list[str] = []
        for key, value in fixture.items():
            if key not in live:
                out.append(f"{path}.{key}")
            else:
                out.extend(_invented(value, live[key], f"{path}.{key}"))
        return out
    if isinstance(fixture, list) and fixture and isinstance(live, list) and live:
        # Rows differ in their fields (a saved destination has `saved`): each
        # fixture row must match some live row with no field the hub lacks.
        out = []
        for item in fixture:
            tries = [_invented(item, row, f"{path}[]") for row in live]
            out.extend(min(tries, key=len))
        return sorted(set(out))
    return []


def test_the_trust_wire_fixtures_carry_no_invented_field(hub: Hub, home: Path, tmp_path: Path) -> None:
    """The vitest doubles are the live hub's own answers (scar law)."""
    wire = {"status-virgin.json": {"trust": _trust(hub)}}
    _save(hub, "Team updates", home / "Documents" / "HoldSpeak" / "Team updates")
    wire["status-local.json"] = {"trust": _trust(hub)}
    _save(hub, "Synced updates", home / "Dropbox" / "Team updates", synced=True)
    wire["status-synced.json"] = {"trust": _trust(hub)}
    _check_wire(wire, tmp_path)


def _serve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, host: str) -> dict[str, Any]:
    """Start a real hub on ``host`` (a real socket) and read its trust block."""
    import httpx

    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from unittest.mock import MagicMock

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "hub.db")
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    reset_database()
    token = "trust-bind-token"
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        host=host,
        auth_token=token,
    )
    try:
        server.start()
        resp = httpx.get(
            f"http://127.0.0.1:{server.port}/api/setup/status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        assert resp.status_code == 200, resp.text
        return resp.json()["trust"]
    finally:
        server.stop()
        reset_database()
        composition.install(composition.bare(label="pytest"))


def test_a_hub_bound_to_every_interface_says_so(tmp_path: Path, home: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    """The status states the host the runtime REALLY binds, and its token.

    The route used to read ``_trust_block`` with its loopback default, so a
    hub on 0.0.0.0 read ``127.0.0.1`` and the Trust window said "no"."""
    trust = _serve(tmp_path, monkeypatch, "0.0.0.0")
    assert trust["web_bind"] == "0.0.0.0", trust
    # start() refuses an off-loopback bind with no token, so a served
    # off-loopback hub always has one, and the status says so.
    assert trust["auth_token_set"] is True, trust


def test_a_loopback_hub_says_loopback(tmp_path: Path, home: Path,
                                      monkeypatch: pytest.MonkeyPatch) -> None:
    trust = _serve(tmp_path, monkeypatch, "127.0.0.1")
    assert trust["web_bind"] == "127.0.0.1", trust
    assert trust["auth_token_set"] is True, trust


def test_the_open_to_network_wire(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """menus.app.test.tsx (the chrome over an open hub): the status a hub
    served on 0.0.0.0 states, read over its real socket.

    replaces: tests/e2e/test_hs201_one_thing_glass.py::TestOneThing::test_open_to_network_is_its_own_token
    (the hub half). A served off-loopback hub always has a token: ``start()``
    refuses the bind without one (``web_auth.nonloopback_bind_blocked``), and a
    hub with no token answers 401 to every read. So the real answer is open
    WITH a token, and the chrome's OPEN TO NETWORK token (open, no token)
    stays dark over it."""
    trust = _serve(tmp_path, monkeypatch, "0.0.0.0")
    assert (trust["web_bind"], trust["auth_token_set"]) == ("0.0.0.0", True), trust
    assert not [d for d in trust["destinations"] if d["enabled"]], trust["destinations"]
    _check_wire({"status-open.json": {"trust": trust}}, tmp_path)


def _check_wire(wire: dict[str, Any], tmp_path: Path) -> None:
    if os.environ.get("HOLDSPEAK_WRITE_WIRE_FIXTURES") == "1":
        FIXTURES.mkdir(parents=True, exist_ok=True)
        for name, body in wire.items():
            text = json.dumps(_scrub(body, str(tmp_path)), indent=2, sort_keys=True) + "\n"
            (FIXTURES / name).write_text(text)
    problems: list[str] = []
    for name, body in wire.items():
        fixture_path = FIXTURES / name
        assert fixture_path.exists(), f"missing fixture {name}; write it with HOLDSPEAK_WRITE_WIRE_FIXTURES=1"
        problems += [f"{name}: {p}" for p in _invented(json.loads(fixture_path.read_text()), body)]
    assert not problems, "a Trust vitest fixture carries a field the hub does not send: " + ", ".join(problems)
