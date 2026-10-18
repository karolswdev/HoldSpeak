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


# ── Betterment send S1: the Send face tells the truth (hub half) ────────────
#
# The process edge answers from the recon's recorded runner scripts
# (tests/fixtures/send_week/runner-*.json, copied from
# docs/internal/betterment/send/rig/): `gh` and `acli` never run, nothing
# leaves the machine. The face half replays the answers these tests record
# (web/src/desk/__tests__/fixtures/send-hub/*.json; HOLDSPEAK_WIRE_WRITE=1
# rewrites them, else each test fences their shape).

import json  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import threading  # noqa: E402
from datetime import datetime, timedelta, timezone  # noqa: E402
from typing import Any  # noqa: E402

from _philo10_send import in_thread, until  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
WEEK = REPO / "tests" / "fixtures" / "send_week"
SEND_HUB = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "send-hub"
JIRA_ACCOUNT = {"site": "acme.atlassian.net", "email": "karol@acme.example"}


class Runner:
    """The CLI process edge, answering by argv prefix from a recorded runner script.

    An answer marked ``hold`` waits until ``release`` is set (the recon's Jira
    comment that never answers)."""

    def __init__(self, name: str) -> None:
        self.answers = json.loads((WEEK / name).read_text())["answers"]
        self.calls: list[list[str]] = []
        self.release = threading.Event()
        self.held = threading.Event()

    def __call__(self, argv: Any, **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        argv = [str(a) for a in argv]
        self.calls.append(argv)
        for answer in self.answers:
            if argv[:len(answer["argv_prefix"])] == answer["argv_prefix"]:
                if answer.get("hold"):
                    self.held.set()
                    self.release.wait(60)
                    return subprocess.CompletedProcess(argv, 0, json.dumps(
                        {"id": "10502", "self": "https://acme.atlassian.net/rest/api/3/issue/PAY-12/comment/10502"}), "")
                return subprocess.CompletedProcess(argv, answer["code"], answer["stdout"], answer["stderr"])
        return subprocess.CompletedProcess(argv, 1, "", f"runner: no answer for {argv[:4]}")


def _runner(monkeypatch: pytest.MonkeyPatch, name: str) -> Runner:
    from holdspeak.services import channel_cli

    runner = Runner(name)
    monkeypatch.setattr(channel_cli, "CLI_RUNNER", runner)
    return runner


def _save(hub: Hub, **body: Any) -> dict:
    resp = hub.client.post("/api/channels/destinations", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()["destination"]


def _listed(hub: Hub, dest_id: str) -> dict:
    [row] = [d for d in hub.client.get("/api/channels/destinations").json()["destinations"] if d["id"] == dest_id]
    return row


def _scrub(value: Any, tmp_path: Path) -> Any:
    text = json.dumps(value)
    for real in {str(tmp_path), str(tmp_path.resolve())}:
        text = re.sub(re.escape(real), "/tmp/rig", text, flags=re.IGNORECASE)
    return json.loads(re.sub(r"/Users/[^/\"]+", "/Users/me", text))


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _shape(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(v) for v in value]
    return "null" if value is None else type(value).__name__


def _wire(hub: Hub, ref: str) -> dict:
    """What the Send well reads for one document: destinations, sends, each preview."""
    destinations = hub.client.get("/api/channels/destinations").json()["destinations"]
    previews = [hub.client.post("/api/channels/preview", json={"document_ref": ref, "destination_id": d["id"]}).json()
                for d in destinations]
    return {"document_ref": ref, "destinations": destinations, "sends": _sends(hub, ref), "previews": previews}


def _record(name: str, payload: dict, tmp_path: Path) -> None:
    """Write the hub's answers for the face (HOLDSPEAK_WIRE_WRITE=1), else fence their shape."""
    scrubbed = _scrub(payload, tmp_path)
    path = SEND_HUB / f"{name}.json"
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"_source": "The hub's own answers, captured by tests/unit/test_desk_send.py "
                                               "(TestClient, isolated HOME, the recon's runner scripts). "
                                               "HOLDSPEAK_WIRE_WRITE=1 rewrites this file; never hand-edit it.",
                                    **scrubbed}, indent=1, ensure_ascii=False) + "\n")
    assert path.exists(), f"no stored answers {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    stored = {k: v for k, v in json.loads(path.read_text()).items() if k != "_source"}
    assert _shape(stored) == _shape(scrubbed), f"{path.name}: the stored answers are not the hub's shape"


def test_a_good_send_is_a_good_check_and_clears_the_accounts_warning(
        hub: Hub, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The Accounts row's own check said Unreachable; then a send POSTED. The
    destination's account reads connected from that send: UNREACHABLE never
    sits next to a newer POSTED. A later sign-in failure speaks again."""
    _runner(monkeypatch, "runner-ok.json")
    # The add form's save: `gh api user` names the login (no Accounts row needed).
    github = _save(hub, name="acme/payments #42", channel="github", repo="acme/payments", kind="issue", number=42)
    assert github["account"] == {"host": "github.com", "login": "karol-arch"}, github
    assert github["connection"]["state"] == "never_checked", github
    jira = _save(hub, name="PAY-12 ticket", channel="jira", key="PAY-12", **JIRA_ACCOUNT)
    assert jira["connection"]["state"] == "never_checked", jira
    # The Accounts row's stored check (gh auth status): Unreachable, before the send.
    hub.db.automations.create_provider_connection(
        connection_id="wpc_github", provider_id="github", transport="connector_pack", state="degraded",
        capability_manifest_json="{}", capability_revision=1, discovery_state="unknown")
    hub.db.automations.update_provider_connection("wpc_github", last_checked_at="2026-10-17T18:00:00+00:00")
    assert _listed(hub, github["id"])["connection"]["state"] == "degraded"

    ref = _brief_ref(hub)
    _record("destinations-before-send", _wire(hub, ref), tmp_path)
    posted = _press(hub, ref, github["id"], "s1-github-1")
    assert posted["outcome"] == "sent", posted
    commented = _press(hub, ref, jira["id"], "s1-jira-1")
    assert commented["outcome"] == "sent", commented
    gh_row, jira_row = _listed(hub, github["id"]), _listed(hub, jira["id"])
    assert gh_row["connection"] == {"id": "wpc_github", "state": "connected",
                                    "last_checked_at": posted["send"]["settled_at"]}, gh_row
    assert jira_row["connection"]["state"] == "connected", jira_row
    _record("destinations-after-posted", _wire(hub, ref), tmp_path)

    # A newer check wins again (it is newer than the send).
    hub.db.automations.update_provider_connection(
        "wpc_github", state="degraded", last_checked_at=(datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat())
    assert _listed(hub, github["id"])["connection"]["state"] == "degraded"


def test_a_send_that_failed_on_sign_in_is_the_newest_word_on_its_account(
        hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _runner(monkeypatch, "runner-ok.json")
    github = _save(hub, name="acme/payments #42", channel="github", repo="acme/payments", kind="issue", number=42)
    ref = _brief_ref(hub)
    assert _press(hub, ref, github["id"], "s1-ok")["outcome"] == "sent"
    # gh logged out between the check before dispatch and the create: exit 4.
    runner.answers.insert(0, {"argv_prefix": ["gh", "issue", "comment"], "code": 4, "stdout": "",
                              "stderr": "To get started with GitHub CLI, please run:  gh auth login"})
    failed = _press(hub, ref, github["id"], "s1-signed-out")
    assert (failed["outcome"], failed["send"]["reason"]) == ("failed", "github_not_authenticated"), failed
    assert _listed(hub, github["id"])["connection"]["state"] == "owner_action_required"


def test_a_send_with_no_answer_past_its_limit_reads_unknown_and_its_late_answer_still_settles(
        hub: Hub, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The recon's held Jira comment: SENDING for 90 s, then no answer in time
    (the read asks the channel's recover; it never sends again), on every read,
    so also after a reload. The row is not written: the late answer settles it."""
    from holdspeak.services import channel_service

    runner = _runner(monkeypatch, "runner-bad.json")
    jira = _save(hub, name="PAY-12 ticket", channel="jira", key="PAY-12", **JIRA_ACCOUNT)
    github = _save(hub, name="acme/payments #4242", channel="github", repo="acme/payments", kind="issue", number=4242)
    ref = _brief_ref(hub)
    failed = _press(hub, ref, github["id"], "s1-not-found")
    assert (failed["outcome"], failed["send"]["reason"]) == ("failed", "github_target_not_found"), failed

    pv = hub.client.post("/api/channels/preview", json={"document_ref": ref, "destination_id": jira["id"]}).json()
    body = {"document_ref": ref, "destination_id": jira["id"], "preview_digest": pv["payload_digest"],
            "command_id": "s1-jira-held"}
    thread, answer = in_thread(lambda: hub.client.post("/api/channels/send", json=body))
    assert runner.held.wait(30)
    [row] = until(lambda: [s for s in _sends(hub, ref) if s["state"] == "dispatching"])
    started = datetime.fromisoformat(row["dispatch_started_at"])
    real_now = channel_service._now
    try:
        monkeypatch.setattr(channel_service, "_now", lambda: started + timedelta(seconds=89))
        assert [s["state"] for s in _sends(hub, ref) if s["id"] == row["id"]] == ["dispatching"]
        monkeypatch.setattr(channel_service, "_now", lambda: started + timedelta(seconds=91))
        [late] = [s for s in _sends(hub, ref) if s["id"] == row["id"]]
        assert (late["state"], late["reason"]) == ("unknown", "no_answer_in_time"), late
        # Every read says it (the face after a reload); the stored row stays dispatching.
        [one] = hub.client.get("/api/channels/sends", params={"send_id": row["id"]}).json()["sends"]
        assert (one["state"], one["reason"]) == ("unknown", "no_answer_in_time")
        assert hub.db.channel_sends.get(row["id"])["state"] == "dispatching"
        _record("sends-no-answer", _wire(hub, ref), tmp_path)
    finally:
        runner.release.set()
        thread.join(60)
        monkeypatch.setattr(channel_service, "_now", real_now)
    [settled] = answer
    assert settled.status_code == 200 and settled.json()["outcome"] == "sent", settled.text
    assert [s["state"] for s in _sends(hub, ref) if s["id"] == row["id"]] == ["sent"]
    assert sum(1 for c in runner.calls if c[:5] == ["acli", "jira", "workitem", "comment", "create"]) == 1


def test_a_saved_file_is_named_by_the_owners_local_date(
        hub: Hub, home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The recon sent at 20:29 on 17 Oct, local time (18 Oct in UTC): the name says 2026-10-17."""
    from holdspeak.services import channel_contract

    evening = datetime(2026, 10, 17, 20, 29, tzinfo=timezone(timedelta(hours=-7)))
    monkeypatch.setattr(channel_contract, "_local_now", lambda: evening)
    ref = _brief_ref(hub)
    sent = _press(hub, ref, BUILTIN, "s1-local-date")
    assert sent["outcome"] == "sent", sent
    name = Path(sent["send"]["proof"]["path"]).name
    assert name.startswith("2026-10-17-"), name
