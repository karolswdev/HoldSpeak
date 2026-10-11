"""The Send well (the Chair's Brief): the hub half of the built-in folder.

The test diet (2026-10-11) moves the hub facts of
tests/e2e/test_builtin_send_folder_glass.py here: the same seed (a decision
made through ``POST /api/decisions``, a brief made by ``POST
/api/brief/generate``), the same routes, the same isolated HOME whose
Documents folder is a scratch directory, the same iCloud xattr monkeypatch.
The face half (one row picked with no click, the row words, SAVED) is in
web/src/desk/__tests__/send.app.test.tsx.

Through the REAL hub (``TestClient`` over the hub's app, tests/unit/_philo10_send.py).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, files  # noqa: E402

BUILTIN = "holdspeak-folder"
NAME = "HoldSpeak folder"


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_DOCUMENTS_DIR", raising=False)
    return fake


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, home: Path):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _sent(home: Path) -> Path:
    return Path(os.path.realpath(home / "Documents")) / "HoldSpeak" / "Sent"


def _icloud(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    """The e2e's own boundary double: the OS xattr call answers iCloud for
    the isolated HOME's Documents only."""
    from holdspeak.services import channel_contract

    documents = os.path.realpath(home / "Documents")
    os.makedirs(documents, exist_ok=True)
    monkeypatch.setattr(channel_contract, "PLATFORM", "darwin")
    monkeypatch.setattr(channel_contract, "_read_xattr", lambda path, name: (
        b"com.apple.CloudDocs.iCloudDriveFileProvider/glass" if path == documents else None))


def _brief_ref(hub: Hub) -> str:
    """The e2e's seed: one decision, then the brief the Chair sends."""
    made = hub.client.post("/api/decisions", json={
        "title": "Freeze the old ledger on Nov 3", "status": "proposed",
        "decision_markdown": "Freeze the old ledger on Nov 3."})
    assert made.status_code in (200, 201), made.text
    brief = hub.client.post("/api/brief/generate", json={})
    assert brief.status_code == 200, brief.text
    return f"monday_brief:{brief.json()['id']}"


def _press(hub: Hub, ref: str, dest: str, key: str) -> dict:
    """The face's press: the preview (its digest), then Send with that digest."""
    pv = hub.client.post("/api/channels/preview", json={"document_ref": ref, "destination_id": dest})
    assert pv.status_code == 200, pv.text
    resp = hub.client.post("/api/channels/send", json={
        "document_ref": ref, "destination_id": dest,
        "preview_digest": pv.json()["payload_digest"], "command_id": key})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _sends(hub: Hub, ref: str) -> list[dict]:
    resp = hub.client.get("/api/channels/sends", params={"document_ref": ref})
    assert resp.status_code == 200, resp.text
    return resp.json()["sends"]


@pytest.mark.parametrize("docs", ["plain", "icloud"])
def test_a_fresh_desk_sends_the_brief_into_documents_holdspeak_sent(
        hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch, docs: str) -> None:
    """replaces: tests/e2e/test_builtin_send_folder_glass.py::TestBuiltinSendFolderGlass::test_the_builtin_folder_is_one_picked_row_and_send_writes_into_documents (hub half)"""
    if docs == "icloud":
        _icloud(monkeypatch, home)
    sent = _sent(home)

    # A fresh desk lists ONE destination: the built-in folder.
    listed = hub.client.get("/api/channels/destinations").json()["destinations"]
    assert [d["id"] for d in listed] == [BUILTIN], listed
    [d] = listed
    assert (d["name"], d["channel"], d["builtin"]) == (NAME, "file", True)
    # The face reads the row's folder by name and the ~ token on hover.
    assert d["target"]["display"] == "~/Documents/HoldSpeak/Sent"
    assert d["target"].get("cloud") == ("icloud" if docs == "icloud" else None)

    ref = _brief_ref(hub)
    assert not sent.exists(), "the folder is made by the first send, never before"

    result = _press(hub, ref, BUILTIN, f"builtin-{docs}")
    assert result["outcome"] == "sent", result
    [row] = _sends(hub, ref)
    assert row["state"] == "sent" and row["destination_id"] == BUILTIN, row
    # ONE file, written into the isolated HOME's Documents/HoldSpeak/Sent.
    assert [str(p) for p in files(sent)] == [row["proof"]["path"]], (files(sent), row["proof"])
    assert row["proof"].get("egress") == ("icloud" if docs == "icloud" else None), row["proof"]


def test_a_send_to_a_saved_folder_never_makes_the_builtin_folder(hub: Hub, home: Path, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_builtin_send_folder_glass.py::TestBuiltinSendFolderGlass::test_a_phase11_brief_send_to_a_saved_folder_with_the_builtin_present (hub half)"""
    sent = _sent(home)
    team = (tmp_path / "Reports" / "Team").resolve()
    team.mkdir(parents=True)
    saved = hub.client.post("/api/channels/destinations",
                            json={"name": "Team folder", "channel": "file", "folder": str(team)})
    assert saved.status_code == 200, saved.text
    team_id = saved.json()["destination"]["id"]
    listed = hub.client.get("/api/channels/destinations").json()["destinations"]
    assert sorted(d["name"] for d in listed) == sorted([NAME, "Team folder"]), listed

    ref = _brief_ref(hub)
    first = _press(hub, ref, team_id, "team-1")
    assert first["outcome"] == "sent", first
    [row] = _sends(hub, ref)
    assert row["destination_name"] == "Team folder" and row["state"] == "sent", row
    assert len(files(team)) == 1
    assert not sent.exists(), "a send to a saved folder never makes the built-in folder"

    second = _press(hub, ref, BUILTIN, "builtin-1")
    assert second["outcome"] == "sent", second
    rows = _sends(hub, ref)
    assert len(rows) == 2 and {r["destination_name"] for r in rows if r["state"] == "sent"} == {"Team folder", NAME}, rows
    assert len(files(sent)) == 1
    assert len(files(team)) == 1
