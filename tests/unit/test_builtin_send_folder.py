"""The built-in "HoldSpeak folder" Send destination (owner ruling 2026-10-05).

"Strong defaults, batteries included": a file destination always exists with
no setup. Its folder is the user's Documents folder + HoldSpeak/Sent, resolved
at SEND time; it is made on the first send and made again when it was deleted.
A SAVED folder that is missing still refuses and is never made.

Through the REAL hub (``TestClient`` over the hub's app) with the real
producers, on an isolated HOME whose Documents folder is a scratch directory.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import Hub, _boot, destination, files, room, send, send_body, sends  # noqa: E402

BUILTIN = "holdspeak-folder"


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


def sent_folder(home: Path) -> Path:
    return Path(os.path.realpath(home / "Documents")) / "HoldSpeak" / "Sent"


def press(hub: Hub, update: str, key: str) -> dict:
    resp = send(hub, send_body(hub, "inline", update, BUILTIN, key))
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── present with no setup ─────────────────────────────────────────────────


def test_a_fresh_desk_lists_the_builtin_folder_ready_on_this_device(hub: Hub, home: Path) -> None:
    listed = hub.client.get("/api/channels/destinations").json()["destinations"]
    assert [d["id"] for d in listed] == [BUILTIN]
    d = listed[0]
    assert (d["name"], d["channel"], d["builtin"], d["synced"]) == ("HoldSpeak folder", "file", True, False)
    assert d["badge"] == "local"  # the egress chip: THIS DEVICE (nothing leaves the machine)
    assert d["target"]["folder"] == str(sent_folder(home))
    assert d["target"]["display"] == "~/Documents/HoldSpeak/Sent"  # the row's short token, any HOME
    # Created on first send, never at install: no folder yet, and the check says ready, never missing.
    assert not sent_folder(home).exists()
    check = hub.client.post(f"/api/channels/destinations/{BUILTIN}/check").json()["check"]
    assert check["state"] == "ready"
    assert check["resolved"] == str(sent_folder(home))


def test_the_seed_is_idempotent_and_a_reconcile_keeps_one_row(hub: Hub) -> None:
    from holdspeak.db.reconcile import reconcile_schema

    with hub.db._connection() as conn:
        reconcile_schema(conn)
        reconcile_schema(conn)
        count = conn.execute("SELECT COUNT(*) FROM channel_destinations WHERE id=?", (BUILTIN,)).fetchone()[0]
    assert count == 1


def test_the_builtin_cannot_be_removed_or_replaced(hub: Hub, tmp_path: Path) -> None:
    removed = hub.client.request("DELETE", f"/api/channels/destinations/{BUILTIN}", json={})
    assert removed.status_code == 400 and removed.json()["code"] == "destination_builtin", removed.text
    folder = tmp_path / "other"
    folder.mkdir()
    edited = hub.client.post("/api/channels/destinations", json={
        "name": "Other", "channel": "file", "folder": str(folder), "replaces": BUILTIN})
    assert edited.status_code == 400 and edited.json()["code"] == "destination_builtin", edited.text
    listed = hub.client.get("/api/channels/destinations").json()["destinations"]
    assert [d["id"] for d in listed] == [BUILTIN]


# ── the send: made on first send, made again when deleted ─────────────────


def test_first_send_makes_the_folder_and_the_file_and_a_deleted_folder_is_made_again(hub: Hub, home: Path) -> None:
    import shutil

    _pid, update = room(hub)
    folder = sent_folder(home)
    first = press(hub, update, "builtin-1")
    assert first["outcome"] == "sent", first
    assert folder.is_dir()
    assert oct(folder.stat().st_mode & 0o777) == oct(0o755 & ~_umask())
    [written] = files(folder)
    assert first["send"]["proof"]["path"] == str(written)

    shutil.rmtree(home / "Documents" / "HoldSpeak")
    second = press(hub, update, "builtin-2")
    assert second["outcome"] == "sent", second
    again = files(folder)
    assert len(again) == 1 and again[0] != written and second["send"]["proof"]["path"] == str(again[0])


def test_an_old_file_is_never_overwritten(hub: Hub, home: Path) -> None:
    _pid, update = room(hub)
    first = press(hub, update, "keep-1")
    [old] = files(sent_folder(home))
    old_bytes = old.read_bytes()
    second = press(hub, update, "keep-2")
    assert second["outcome"] == "sent"
    after = files(sent_folder(home))
    assert len(after) == 2 and old.read_bytes() == old_bytes
    assert first["send"]["file_path"] != second["send"]["file_path"]


def test_a_name_taken_at_the_create_never_overwrites_the_old_file(hub: Hub, home: Path,
                                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services.channel_contract import FileChannel

    _pid, update = room(hub)
    press(hub, update, "taken-1")
    [old] = files(sent_folder(home))
    old_bytes = old.read_bytes()
    # The chosen name is taken between the choice and the create (a race): the exclusive create refuses.
    monkeypatch.setattr(FileChannel, "choose_path", lambda self, folder, document, send_id: str(old))
    second = press(hub, update, "taken-2")
    assert (second["outcome"], second["send"]["reason"]) == ("failed", "name_taken"), second
    assert files(sent_folder(home)) == [old] and old.read_bytes() == old_bytes


def test_the_folder_is_resolved_at_send_time_not_at_prepare(hub: Hub, home: Path, tmp_path: Path,
                                                            monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_contract

    _pid, update = room(hub)
    body = send_body(hub, "send_id", update, BUILTIN, "moved-1")  # prepared while Documents is ~/Documents
    moved = tmp_path / "moved-docs"
    monkeypatch.setattr(channel_contract, "documents_dir", lambda platform=None: str(moved))
    resp = send(hub, body)
    assert resp.status_code == 200 and resp.json()["outcome"] == "sent", resp.text
    assert len(files(moved / "HoldSpeak" / "Sent")) == 1
    assert not (home / "Documents" / "HoldSpeak").exists()
    [row] = sends(hub)
    assert row["file_path"].startswith(os.path.realpath(moved))


def test_a_saved_folder_that_is_missing_refuses_and_is_never_made(hub: Hub, tmp_path: Path) -> None:
    import shutil

    _pid, update = room(hub)
    saved = tmp_path / "share"
    dest = destination(hub, saved, name="Share")
    shutil.rmtree(saved)
    check = hub.client.post(f"/api/channels/destinations/{dest}/check").json()["check"]
    assert check["state"] == "missing"
    resp = send(hub, send_body(hub, "inline", update, dest, "saved-missing"))
    assert resp.status_code == 409 and resp.json()["code"] == "destination_changed", resp.text
    assert not saved.exists()
    assert sends(hub) == []


# ── the Documents folder per platform ────────────────────────────────────


def test_macos_resolves_documents_holdspeak_sent(home: Path) -> None:
    from holdspeak.services.channel_contract import builtin_folder, documents_dir

    assert documents_dir("darwin") == str(home / "Documents")
    assert builtin_folder("darwin") == os.path.realpath(home / "Documents" / "HoldSpeak" / "Sent")


def test_linux_reads_xdg_user_dirs(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services.channel_contract import builtin_folder, documents_dir

    config = home / ".config"
    config.mkdir()
    (config / "user-dirs.dirs").write_text(
        '# written by xdg-user-dirs-update\nXDG_DESKTOP_DIR="$HOME/Desktop"\nXDG_DOCUMENTS_DIR="$HOME/Dokumente"\n')
    assert documents_dir("linux") == str(home / "Dokumente")
    assert builtin_folder("linux").endswith("/Dokumente/HoldSpeak/Sent")
    # $XDG_CONFIG_HOME moves the file.
    other = home / "cfg"
    other.mkdir()
    (other / "user-dirs.dirs").write_text('XDG_DOCUMENTS_DIR="/srv/docs"\n')
    monkeypatch.setenv("XDG_CONFIG_HOME", str(other))
    assert documents_dir("linux") == "/srv/docs"


def test_linux_falls_back_to_home_documents(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services.channel_contract import documents_dir

    assert documents_dir("linux") == str(home / "Documents")  # no user-dirs.dirs
    config = home / ".config"
    config.mkdir()
    (config / "user-dirs.dirs").write_text('XDG_DOCUMENTS_DIR="$HOME/"\n')  # "$HOME" = no Documents folder
    assert documents_dir("linux") == str(home / "Documents")
    (config / "user-dirs.dirs").write_text("")
    monkeypatch.setenv("XDG_DOCUMENTS_DIR", str(home / "Papers"))
    assert documents_dir("linux") == str(home / "Papers")


def _umask() -> int:
    mask = os.umask(0)
    os.umask(mask)
    return mask


# ── iCloud Drive (owner ruling 2026-10-05): detect it, label it honestly ──

CLOUD_ID = b"com.apple.CloudDocs.iCloudDriveFileProvider/0A1B2C"


def _icloud(monkeypatch: pytest.MonkeyPatch, home: Path, *, synced: bool) -> list[str]:
    """macOS, and the OS-call boundary answers for the fake Documents folder only (never the real one)."""
    from holdspeak.services import channel_contract

    monkeypatch.setattr(channel_contract, "PLATFORM", "darwin")
    documents = os.path.realpath(home / "Documents")
    (home / "Documents").mkdir(exist_ok=True)
    asked: list[str] = []

    def read(path: str, name: str):
        asked.append(path)
        if synced and name == "com.apple.file-provider-domain-id" and path == documents:
            return CLOUD_ID
        return None

    monkeypatch.setattr(channel_contract, "_read_xattr", read)
    return asked


def test_icloud_documents_label_the_row_icloud_and_the_receipt_names_the_egress(
        hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    asked = _icloud(monkeypatch, home, synced=True)
    [d] = hub.client.get("/api/channels/destinations").json()["destinations"]
    assert (d["target"]["cloud"], d["synced"], d["badge"]) == ("icloud", True, "cloud")
    assert asked, "the detector never read the folder"
    check = hub.client.post(f"/api/channels/destinations/{BUILTIN}/check").json()["check"]
    assert check["state"] == "ready"
    _pid, update = room(hub)
    sent = press(hub, update, "icloud-1")
    assert sent["outcome"] == "sent", sent
    assert sent["send"]["proof"]["egress"] == "icloud"
    assert sent["send"]["badge"] == "cloud"
    [row] = sends(hub)
    assert '"egress":"icloud"' in row["proof_json"]
    # The write itself is local: the file is in the Sent folder.
    assert [str(p) for p in files(sent_folder(home))] == [sent["send"]["proof"]["path"]]


def test_plain_documents_stay_this_device(hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _icloud(monkeypatch, home, synced=False)
    [d] = hub.client.get("/api/channels/destinations").json()["destinations"]
    assert "cloud" not in d["target"] and (d["synced"], d["badge"]) == (False, "local")
    _pid, update = room(hub)
    sent = press(hub, update, "plain-1")
    assert sent["outcome"] == "sent" and "egress" not in sent["send"]["proof"], sent
    assert sent["send"]["badge"] == "local"


def test_the_sync_is_read_at_send_time(hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _pid, update = room(hub)
    _icloud(monkeypatch, home, synced=False)
    body = send_body(hub, "send_id", update, BUILTIN, "switch-1")  # prepared while plain
    _icloud(monkeypatch, home, synced=True)                        # he turns iCloud Drive on
    resp = send(hub, body)
    assert resp.status_code == 200 and resp.json()["send"]["proof"]["egress"] == "icloud", resp.text


def test_the_finder_switch_is_the_fallback(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import plistlib

    from holdspeak.services import channel_contract

    monkeypatch.setattr(channel_contract, "_read_xattr", lambda path, name: None)
    sent = str(home / "Documents" / "HoldSpeak" / "Sent")
    assert channel_contract.icloud_synced(sent, "darwin") is False
    prefs = home / "Library" / "Preferences"
    prefs.mkdir(parents=True)
    (prefs / "com.apple.finder.plist").write_bytes(plistlib.dumps({"FXICloudDriveDocuments": True}))
    assert channel_contract.icloud_synced(sent, "darwin") is True
    assert channel_contract.icloud_synced(str(home / "Desktop" / "x"), "darwin") is False
    (prefs / "com.apple.finder.plist").write_bytes(plistlib.dumps({"FXICloudDriveDesktop": True}))
    assert channel_contract.icloud_synced(str(home / "Desktop" / "x"), "darwin") is True
    assert channel_contract.icloud_synced(sent, "darwin") is False
    # Linux: no detection.
    (prefs / "com.apple.finder.plist").write_bytes(plistlib.dumps({"FXICloudDriveDocuments": True}))
    assert channel_contract.icloud_synced(sent, "linux") is False


@pytest.mark.skipif(sys.platform != "darwin", reason="a real extended attribute needs macOS")
def test_the_real_xattr_on_a_scratch_folder_is_read(home: Path) -> None:
    import subprocess

    from holdspeak.services import channel_contract

    documents = home / "Documents"
    documents.mkdir()
    sent = str(documents / "HoldSpeak" / "Sent")
    assert channel_contract.icloud_synced(sent, "darwin") is False
    subprocess.run(["xattr", "-w", "com.apple.file-provider-domain-id", CLOUD_ID.decode(), str(documents)], check=True)
    assert channel_contract.icloud_synced(sent, "darwin") is True


# ── Astra's review of #864 (2026-10-05): the five defects, fenced ─────────


def test_a_documents_symlinked_outside_home_with_the_icloud_xattr_is_icloud(
        hub: Hub, home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """D1a: the xattr is read on the RESOLVED folder's ancestors, with no HOME stop."""
    from holdspeak.services import channel_contract

    outside = tmp_path / "other-volume-docs"
    outside.mkdir()
    (home / "Documents").symlink_to(outside)
    monkeypatch.setattr(channel_contract, "PLATFORM", "darwin")
    real_outside = os.path.realpath(outside)
    monkeypatch.setattr(channel_contract, "_read_xattr",
                        lambda path, name: CLOUD_ID if path == real_outside else None)
    _pid, update = room(hub)
    sent = press(hub, update, "outside-1")
    assert sent["outcome"] == "sent", sent
    assert (sent["send"]["proof"]["egress"], sent["send"]["badge"]) == ("icloud", "cloud"), sent["send"]
    assert sent["send"]["proof"]["path"].startswith(real_outside)


@pytest.mark.parametrize("finder_switch", [True, False])
def test_a_documents_symlinked_into_icloud_drive_is_icloud_with_no_xattr(
        hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch, finder_switch: bool) -> None:
    """D1b: a resolved path inside ~/Library/Mobile Documents is iCloud Drive's own store (with or without Finder's switch)."""
    import plistlib

    from holdspeak.services import channel_contract

    store = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Documents"
    store.mkdir(parents=True)
    (home / "Documents").symlink_to(store)
    prefs = home / "Library" / "Preferences"
    prefs.mkdir(parents=True)
    (prefs / "com.apple.finder.plist").write_bytes(plistlib.dumps({"FXICloudDriveDocuments": finder_switch}))
    monkeypatch.setattr(channel_contract, "PLATFORM", "darwin")
    monkeypatch.setattr(channel_contract, "_read_xattr", lambda path, name: None)
    [d] = hub.client.get("/api/channels/destinations").json()["destinations"]
    assert (d["target"].get("cloud"), d["badge"]) == ("icloud", "cloud"), d
    _pid, update = room(hub)
    sent = press(hub, update, "mobile-1")
    assert (sent["send"]["proof"]["egress"], sent["send"]["badge"]) == ("icloud", "cloud"), sent["send"]


def test_the_finder_switch_compares_resolved_paths(home: Path, tmp_path: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """D1: Documents symlinked elsewhere, no xattr, Finder's switch on: the resolved Sent is under the resolved Documents."""
    import plistlib

    from holdspeak.services import channel_contract

    elsewhere = tmp_path / "docs-elsewhere"
    elsewhere.mkdir()
    (home / "Documents").symlink_to(elsewhere)
    prefs = home / "Library" / "Preferences"
    prefs.mkdir(parents=True)
    (prefs / "com.apple.finder.plist").write_bytes(plistlib.dumps({"FXICloudDriveDocuments": True}))
    monkeypatch.setattr(channel_contract, "_read_xattr", lambda path, name: None)
    assert channel_contract.icloud_synced(channel_contract.builtin_folder("darwin"), "darwin") is True


def test_a_take_over_after_a_failed_settle_keeps_the_icloud_egress(
        hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """D3: the egress is judged once at the boundary and stored; recovery reads the stored value."""
    from holdspeak.services import channel_service

    _icloud(monkeypatch, home, synced=True)
    _pid, update = room(hub)
    body = send_body(hub, "inline", update, BUILTIN, "recover-1")
    real = channel_service.settle_in_transaction
    failed: list[int] = []

    def settle(conn, **kwargs):
        settled = real(conn, **kwargs)
        if not failed:
            failed.append(1)
            raise RuntimeError("injected: the settle write failed after the effect")
        return settled

    monkeypatch.setattr(channel_service, "settle_in_transaction", settle)
    first = send(hub, body)
    assert first.status_code == 500, first.text
    [row] = sends(hub)
    assert (row["state"], row["egress"]) == ("dispatching", "icloud"), row
    _icloud(monkeypatch, home, synced=False)  # what the folder says NOW does not rewrite what it said at send
    again = send(hub, body)  # the same key: the take-over reads the file back
    assert again.status_code == 200, again.text
    taken = again.json()["send"]
    assert (taken["state"], taken["proof"]["egress"], taken["badge"]) == ("sent", "icloud", "cloud"), taken
    with hub.db._connection() as conn:
        history = conn.execute("SELECT proof_json FROM project_update_deliveries").fetchall()
    assert ['"egress":"icloud"' in r["proof_json"] for r in history] == [True]


@pytest.mark.parametrize(("raw", "expected"), [
    ('"$HOME/Work\\$Docs"', "{home}/Work$Docs"),
    ('"$HOME/My \\"Docs\\""', '{home}/My "Docs"'),
    ('"$HOME/back\\\\slash"', "{home}/back\\slash"),
    ('"$HOME/tick\\`s"', "{home}/tick`s"),
    ('"/srv/plain docs"', "/srv/plain docs"),
    ('"$HOME/Dokumente"', "{home}/Dokumente"),
])
def test_xdg_values_decode_their_shell_escapes(home: Path, raw: str, expected: str) -> None:
    """D4: the documented user-dirs.dirs format, decoded."""
    from holdspeak.services.channel_contract import documents_dir

    config = home / ".config"
    config.mkdir()
    (config / "user-dirs.dirs").write_text(f"XDG_DOCUMENTS_DIR={raw}\n")
    assert documents_dir("linux") == os.path.normpath(expected.format(home=home))


@pytest.mark.parametrize("raw", [
    '"$HOME/a\\nb"',        # an escape the format does not write
    '"$HOME/a$b"',          # an unescaped $
    '"$HOME/a`b`"',         # an unescaped backquote
    '"$HOME/a"b"',          # an unescaped quote
    '"${HOME}/Docs"',       # not the documented form
    "$HOME/Docs",           # not quoted
    '"Docs"',               # not absolute
])
def test_an_xdg_value_that_cannot_be_decoded_falls_back_to_home_documents(
        home: Path, raw: str, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services.channel_contract import documents_dir

    monkeypatch.setenv("XDG_DOCUMENTS_DIR", "/should/not/be/used")
    config = home / ".config"
    config.mkdir()
    (config / "user-dirs.dirs").write_text(f"XDG_DOCUMENTS_DIR={raw}\n")
    assert documents_dir("linux") == str(home / "Documents")


def test_a_real_send_on_linux_goes_to_the_decoded_folder(hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_contract

    monkeypatch.setattr(channel_contract, "PLATFORM", "linux")
    config = home / ".config"
    config.mkdir()
    (config / "user-dirs.dirs").write_text('XDG_DOCUMENTS_DIR="$HOME/Work\\$Docs"\n')
    _pid, update = room(hub)
    sent = press(hub, update, "xdg-1")
    assert sent["outcome"] == "sent", sent
    assert len(files(home / "Work$Docs" / "HoldSpeak" / "Sent")) == 1
    assert not (home / "Work\\$Docs").exists()


@pytest.mark.parametrize("synced", [True, False])
def test_trust_names_a_stop_that_exists_for_the_builtin(hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch,
                                                         synced: bool) -> None:
    """D5: the built-in cannot be parked (DELETE refuses it; Settings has no Remove), so Trust never says park."""
    from holdspeak.trust_destinations import BUILTIN_ICLOUD_STOP, BUILTIN_LOCAL_STOP

    _icloud(monkeypatch, home, synced=synced)
    status = hub.client.get("/api/setup/status").json()
    [row] = [d for d in status["trust"]["destinations"] if d["id"] == f"channel:{BUILTIN}"]
    assert row["revoke_action"] == (BUILTIN_ICLOUD_STOP if synced else BUILTIN_LOCAL_STOP), row
    assert "Park" not in row["revoke_action"]
    assert row["boundary"] == ("Outside this device" if synced else "This device")
    removed = hub.client.request("DELETE", f"/api/channels/destinations/{BUILTIN}", json={})
    assert removed.json()["code"] == "destination_builtin"
