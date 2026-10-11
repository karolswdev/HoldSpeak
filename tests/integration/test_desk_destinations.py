"""Destinations (Settings › Connections › Destinations), through the real hub (the test diet, 2026-10-11).

The hub boots over an isolated database and HOME with the real channel plans;
only the process edge (gh / acli) is canned (``tests/unit/_philo10_cli.py``)
and the email key store is the memory store (never the real keychain). The
built-in HoldSpeak folder is parked, as on the desk the Send boards were drawn
on (``tests/e2e/glass_infra.park_builtin_folder``).

The wire fixtures under ``web/src/desk/__tests__/fixtures/destinations-wire/``
are what the Destinations vitest (``destinations.app.test.tsx``) answers its
``fetch`` with. ``test_the_destinations_wire_fixtures_carry_no_invented_field``
proves every field in them is a field the live hub sends (the scar law). To
write them again from the live hub: ``HOLDSPEAK_WRITE_WIRE_FIXTURES=1``.

The hub halves the browser tests also asserted are fenced elsewhere and cited
here, not repeated: the GitHub login read at save and the one-key Jira refusal
(``tests/unit/test_philo10_cli_channels.py``), the email key store refusal and
the sender check states (``tests/unit/test_philo10_email_channel.py``).
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
from _philo10_cli import install  # noqa: E402
from _philo10_send import Hub, _boot  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "destinations-wire"
LIST = "/api/channels/destinations?include_parked=true"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)
    return fake


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> Any:
    import keyring

    from holdspeak.services import channel_email

    memory = channel_email.MemoryEmailKeyStore()
    monkeypatch.setattr(channel_email, "KEY_STORE", lambda: memory)

    def never(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("a lane reached the real keychain")

    monkeypatch.setattr(keyring, "get_keyring", never)
    return memory


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, home: Path, store: Any):
    from holdspeak.db import reset_database
    from holdspeak.db.channels import BUILTIN_FOLDER_ID

    rig = _boot(tmp_path, monkeypatch)
    install(monkeypatch)
    with rig.db._connection() as conn:
        conn.execute("UPDATE channel_destinations SET state='parked', parked_at=datetime('now') WHERE id=?",
                     (BUILTIN_FOLDER_ID,))
    yield rig
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _json(resp: Any) -> Any:
    return resp.json()


def _folder(hub: Hub, home: Path, name: str, **extra: Any) -> dict[str, Any]:
    folder = home / name
    folder.mkdir(parents=True, exist_ok=True)
    resp = hub.client.post("/api/channels/destinations",
                           json={"name": f"Folder {name}", "channel": "file", "folder": str(folder), **extra})
    assert resp.status_code == 200, resp.text
    return resp.json()["destination"]


def _mine(hub: Hub) -> list[dict[str, Any]]:
    return [d for d in hub.client.get(LIST).json()["destinations"] if not d.get("builtin")]


def test_two_folders_save_and_edit_and_remove_park_the_old_row(hub: Hub, home: Path) -> None:
    """replaces: tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_destinations_group (the hub half)"""
    drive = _folder(hub, home, "Drive", synced=True)
    reports = _folder(hub, home, "Reports")
    assert sorted((d["name"], d["synced"]) for d in _mine(hub)) == [("Folder Drive", True), ("Folder Reports", False)]
    assert (drive["badge"], reports["badge"]) == ("cloud", "local")

    checked = hub.client.post(f"/api/channels/destinations/{reports['id']}/check", json={}).json()
    assert checked["check"]["state"] == "ready", checked

    # Edit saves a new row and parks the old one.
    edited = hub.client.post("/api/channels/destinations", json={
        "name": "Reports folder", "channel": "file", "folder": str(home / "Reports"), "replaces": reports["id"]})
    assert edited.status_code == 200, edited.text
    assert sorted((d["name"], d["state"]) for d in _mine(hub)) == [
        ("Folder Drive", "active"), ("Folder Reports", "parked"), ("Reports folder", "active")]

    # Remove parks the row with its history.
    removed = hub.client.request("DELETE", f"/api/channels/destinations/{drive['id']}", json={})
    assert removed.status_code == 200, removed.text
    assert sorted(d["state"] for d in _mine(hub)) == ["active", "parked", "parked"]


# ── the wire fixtures the Destinations vitest reads ──────────────────


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


def _live_wire(hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    import keyring.backends.fail

    from holdspeak.services import channel_email

    c = hub.client
    wire: dict[str, Any] = {"connections.json": _json(c.get("/api/connections"))}
    wire["list-empty.json"] = _json(c.get(LIST))
    _folder(hub, home, "Drive", synced=True)
    reports = _folder(hub, home, "Reports")
    wire["list-two.json"] = _json(c.get(LIST))
    wire["check-ready.json"] = _json(c.post(f"/api/channels/destinations/{reports['id']}/check", json={}))
    refused = c.post("/api/channels/destinations", json={
        "name": "Jira PAY-118 PAY-119", "channel": "jira", "site": "acme.atlassian.net",
        "email": "owner@acme.example", "key": "PAY-118 PAY-119"})
    assert refused.status_code == 400, refused.text
    wire["save-refused-jira.json"] = _json(refused)
    # The email key: first a store that is not the OS keychain (refused), then the memory store.
    real_store = channel_email.KEY_STORE
    monkeypatch.setattr(channel_email, "KEY_STORE",
                        lambda: channel_email.NativeEmailKeyStore(backend=keyring.backends.fail.Keyring()))
    key_refused = c.put("/api/channels/email-keys/sendgrid-karol-acme.io",
                        json={"api_key": "SG.glassKEY", "provider": "sendgrid"})
    assert key_refused.status_code == 400, key_refused.text
    wire["email-key-refused.json"] = _json(key_refused)
    monkeypatch.setattr(channel_email, "KEY_STORE", real_store)
    key_saved = c.put("/api/channels/email-keys/sendgrid-karol-acme.io",
                      json={"api_key": "SG.glassKEY", "provider": "sendgrid"})
    assert key_saved.status_code == 200, key_saved.text
    wire["email-key-saved.json"] = _json(key_saved)
    email = c.post("/api/channels/destinations", json={
        "name": "Email lena@acme.io", "channel": "email", "provider": "sendgrid",
        "from_email": "karol@acme.io", "from_name": "", "key_ref": "sendgrid-karol-acme.io",
        "to": ["lena@acme.io", "tomas@acme.io"], "cc": []})
    assert email.status_code == 200, email.text
    wire["list-email.json"] = _json(c.get(LIST))
    wire["check-email.json"] = _json(
        c.post(f"/api/channels/destinations/{email.json()['destination']['id']}/check", json={}))
    return wire


def test_the_destinations_wire_fixtures_carry_no_invented_field(
        hub: Hub, home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The vitest doubles are the live hub's own answers (scar law)."""
    wire = _live_wire(hub, home, monkeypatch)
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
    assert not problems, "a Destinations vitest fixture carries a field the hub does not send: " + ", ".join(problems)
