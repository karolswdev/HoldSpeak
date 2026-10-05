"""STATUS: "Raw paths and ids on some faces (SEND well, Connections, Setup)".

A path the owner must see stays, with the home folder shown as ``~`` (as the
built-in folder did since #864). Through the REAL hub (``TestClient`` over
the hub's app) on an isolated HOME: a saved folder's row, a SAVED receipt,
and the Setup checks.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from holdspeak.runtime import composition
from holdspeak.home_paths import home_display, home_text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, destination, room, send, send_body  # noqa: E402


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


def test_home_display_shortens_the_home_folder_in_both_forms(home: Path, tmp_path: Path) -> None:
    real = os.path.realpath(home)
    assert home_display(str(home / "Documents" / "Team")) == "~/Documents/Team"
    assert home_display(os.path.join(real, "Documents", "Team")) == "~/Documents/Team"
    assert home_display(str(home)) == "~"
    outside = str(tmp_path / "Reports")
    assert home_display(outside) == outside  # a path outside HOME stays whole
    assert home_display(str(home) + "x/y") == str(home) + "x/y"  # a sibling is not HOME


def test_a_saved_folder_row_and_its_send_carry_the_short_token(hub: Hub, home: Path) -> None:
    folder = home / "Documents" / "HoldSpeak" / "Team updates"
    dest = destination(hub, folder, name="Team updates")
    row = next(d for d in hub.client.get("/api/channels/destinations").json()["destinations"] if d["id"] == dest)
    assert row["target"]["display"] == "~/Documents/HoldSpeak/Team updates"
    assert row["target"]["folder"] == str(folder)  # the stored folder is unchanged

    _pid, update = room(hub)
    result = send(hub, send_body(hub, "inline", update, dest, "paths-short-1"))
    assert result.status_code == 200, result.text
    sent = result.json()["send"]
    # The proof stays exact (the stored proof); the receipt shortens it under
    # the target's folder with the target's `display` (SendWell.shownPath).
    assert sent["target"]["display"] == "~/Documents/HoldSpeak/Team updates"
    assert sent["proof"]["path"].startswith(sent["target"]["folder"] + "/"), (sent["proof"], sent["target"])


def test_a_folder_outside_home_keeps_its_whole_path(hub: Hub, tmp_path: Path) -> None:
    folder = tmp_path / "Reports" / "Team"
    dest = destination(hub, folder)
    row = next(d for d in hub.client.get("/api/channels/destinations").json()["destinations"] if d["id"] == dest)
    assert row["target"]["display"] == str(folder)


def test_setup_checks_show_home_paths_with_a_tilde_and_no_wire_boundary(home: Path) -> None:
    from holdspeak.setup_status import build_setup_status

    status = build_setup_status(database=None)
    text = " ".join(f"{s.get('detail') or ''} {s.get('fix') or ''}" for s in status["sections"])
    for form in {str(home), os.path.realpath(home)}:
        assert form + os.sep not in text, text
    assert "same_device" not in text, text


def test_home_text_shortens_only_a_path_that_starts_with_home(home: Path) -> None:
    """Astra, #869: backup_root + HOME + "/desk.db" became backup_root + "~/desk.db"."""
    h = str(home)
    assert home_text(f"Loaded {h}/.holdspeak/config.json (config version 1)") == "Loaded ~/.holdspeak/config.json (config version 1)"
    assert home_text(f"no project root detected from cwd={h}/src") == "no project root detected from cwd=~/src"
    assert home_text(f"{h}/a.md") == "~/a.md"
    contained = f"/backup{h}/desk.db"
    assert home_text(f"Restored from {contained}") == f"Restored from {contained}"
    assert home_text(contained) == contained
    sibling = f"{h}x/notes"
    assert home_text(f"at {sibling}") == f"at {sibling}"
