"""PHILO-10-02: the GitHub and Atlassian channels, the nudge, and the steward's prepare.

Through the REAL hub on an isolated HOME (``TestClient`` over the hub's app and
``/api/mcp``) with the real producers: a published update from the Room's own
routes, destinations saved by ``channel.save_destination``, each channel's REAL
``plan`` and ``interpret``, the real kernel (``subprocess.exec`` children of the
send). Only the process edge is canned (``_philo10_cli.Canned``). The two GATES
from Codex Astra r2 on #692 come first. The mutation list (each fence red on a
deliberate in-code mutation, and the nudge fences red on main) is recorded in
the evidence.
"""
from __future__ import annotations

import json
import os
import random
import string
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_cli import EMAIL, SITE, Canned, install, save  # noqa: E402
from _philo10_send import SENTINEL, Hub, _boot, history, in_thread, prepare, room, send, sends, until  # noqa: E402

CHANNELS = ["github", "jira", "confluence"]


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ops(hub: Hub, name: str | None = None) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        rows = [dict(r) for r in conn.execute(
            "SELECT o.operation_id, o.name, o.state, o.principal_kind, o.principal_identity, o.parent_operation_id,"
            " r.outcome AS outcome, (SELECT COUNT(*) FROM kernel_receipts x WHERE x.operation_id=o.operation_id)"
            " AS receipts FROM kernel_operations o LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id"
            " ORDER BY o.created_at, o.rowid")]
    return [r for r in rows if name is None or r["name"] == name]


def _dest(hub: Hub, channel: str, **fields: Any) -> str:
    saved = save(hub, channel, **fields)
    assert "destination" in saved, saved
    return saved["destination"]["id"]


def _receipt_texts(hub: Hub) -> str:
    """Every receipt, journal row and subprocess native result the hub keeps, as one text."""
    from holdspeak.kernel.subprocess_exec import EXECUTIONS

    with hub.db._connection() as conn:
        parts = [json.dumps([dict(r) for r in conn.execute(f"SELECT * FROM {table}")], default=str)
                 for table in ("kernel_receipts", "kernel_operations", "kernel_journal")]
    parts.append(json.dumps([EXECUTIONS.read(native) for native in list(EXECUTIONS._plans)], default=str))
    return "\n".join(parts)


# ── GATE 1: the redactor's cost is bounded; the named code survives ─────────


def _rnd(n: int, alphabet: str = string.ascii_letters + " ", seed: int = 7) -> str:
    rng = random.Random(seed)
    return "".join(rng.choice(alphabet) for _ in range(n))


def test_gate1_the_redactors_worst_case_is_bounded() -> None:
    """Codex's two measured cases (8.68 s, 26.99 s on story 01) and adversarial payloads at the scan limit."""
    from holdspeak.services.channel_contract import ERROR_LIMIT, REDACT_SCAN_LIMIT, redact

    error = _rnd(2000, seed=11)  # not a substring of the payloads (a different seed): every window is a full scan
    cases = {
        "2000-char error x 10 MiB": (error, (_rnd(1024 * 1024) * 10).encode()),
        "repetitive 10 MiB": ("a" * 1990 + "zzzzzzzzzz", (("a" * 9 + "b") * (1024 * 1024)).encode()),
        "2000-char error x the scan limit": (error, _rnd(REDACT_SCAN_LIMIT).encode()),
    }
    for pattern in ("a" * 9 + "b", "ab", "aab", "a" * 30 + "b"):
        payload = (pattern * (REDACT_SCAN_LIMIT // len(pattern) + 1))[:REDACT_SCAN_LIMIT].encode()
        cases[f"near-miss {pattern[:5]}..({len(pattern)}) at the limit"] = (_rnd(2000, "ab", seed=11), payload)
    for name, (text, payload) in cases.items():
        started = time.perf_counter()
        cleaned = redact(text, payload)
        elapsed = time.perf_counter() - started
        assert elapsed < 2.0, f"{name}: {elapsed:.2f} s"
        assert len(cleaned) <= ERROR_LIMIT
    # Over the scan limit nothing of the text survives (fail closed, never a leak).
    big = ("SENTINEL-OVER-LIMIT " * (REDACT_SCAN_LIMIT // 10)).encode()
    assert redact("gh: parse error near SENTINEL-OVER-LIMIT here", big) == "[redacted]"
    # An excerpt is still removed inside the limit (story 01's promise kept).
    assert "PRIVATE-94c2" not in redact("parse error near SENTINEL-BODY-PRIVATE-94c2", b"x SENTINEL-BODY-PRIVATE-94c2 y")


def test_gate1_a_document_with_the_clis_error_phrase_keeps_the_named_code(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    """The real producer: the document says "permission denied"; gh answers it. The code survives, the text does not."""
    canned = install(monkeypatch)
    canned.answers[("gh", "issue", "comment")] = lambda argv: (
        1, "", "gh: permission denied to acme/payments for this account (HTTP 403)")
    _pid, update = room(hub, body="Blocked: gh: permission denied to acme/payments for this account.\n")
    dest = _dest(hub, "github")
    answer = send(hub, {"send_id": prepare(hub, update, dest)["send"]["id"]})
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert (body["outcome"], body["send"]["reason"]) == ("failed", "github_permission_denied")
    assert body["receipt"]["outcome"] == "github_permission_denied"
    [operation] = _ops(hub, "channel.send")
    assert (operation["state"], operation["outcome"]) == ("failed", "github_permission_denied")
    # The free text went through the redactor: the document's phrase is gone from it.
    assert "permission denied to acme" not in json.dumps(body["send"]["proof"])


# ── GATE 2: the hub answers during a slow send (a real socket hub) ──────────


@pytest.mark.timeout(240)
@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_gate2_the_hub_answers_a_read_during_a_slow_send(tmp_path: Path, transport: str) -> None:
    from test_philo10_send_restart import HubProcess

    home, folder = tmp_path / "home", tmp_path / "out"
    home.mkdir()
    folder.mkdir()
    hub = HubProcess(home, hold="slow")
    try:
        status, made = hub.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        pid = made["project"]["id"]
        update = hub.call("POST", f"/api/projects/{pid}/updates/draft", {})[1]["update"]["id"]
        assert hub.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        status, saved = hub.call("POST", "/api/channels/destinations",
                                 {"name": "Team folder", "channel": "file", "folder": str(folder)})
        assert status == 200, saved
        dest = saved["destination"]["id"]
        baseline = time.perf_counter()
        assert hub.call("GET", "/api/channels/destinations")[0] == 200
        baseline = time.perf_counter() - baseline
        status, prepared = hub.call("POST", "/api/channels/sends", {"update_id": update, "destination_id": dest})
        body = {"send_id": prepared["send"]["id"]}

        def press() -> Any:
            if transport == "http":
                return hub.call("POST", "/api/channels/send", body)
            return hub.call("POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                 "params": {"name": "channel.send", "arguments": body}})

        thread, answer = in_thread(press)
        _started(home)
        started = time.perf_counter()
        status, _listed = hub.call("GET", "/api/channels/destinations")
        read = time.perf_counter() - started
        thread.join(30)
        assert status == 200
        assert answer and answer[0][0] == 200, answer
        # The dispatch sleeps 1.5 s; the concurrent read must not wait for it.
        assert read < 0.5, f"the read waited {read:.3f} s during the send (baseline {baseline:.3f} s)"
    finally:
        hub.kill()


def _started(home: Path) -> None:
    import sqlite3

    db = home / ".local" / "share" / "holdspeak" / "holdspeak.db"

    def dispatching() -> bool:
        conn = sqlite3.connect(str(db))
        try:
            return conn.execute("SELECT 1 FROM channel_sends WHERE state='dispatching'").fetchone() is not None
        finally:
            conn.close()

    until(dispatching)
    time.sleep(0.1)


# ── one channel.send; its CLI children parented, under the owner ───────────


@pytest.mark.parametrize("channel", CHANNELS)
def test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner(
    hub: Hub, monkeypatch: pytest.MonkeyPatch, channel: str,
) -> None:
    canned = install(monkeypatch)
    _pid, update = room(hub, body=f"Status: green.\n\n{SENTINEL}\n")
    dest = _dest(hub, channel)
    answer = send(hub, {"send_id": prepare(hub, update, dest)["send"]["id"]})
    assert answer.status_code == 200 and answer.json()["outcome"] == "sent", answer.text
    [operation] = _ops(hub, "channel.send")
    assert (operation["state"], operation["receipts"]) == ("succeeded", 1)
    children = _ops(hub, "subprocess.exec")
    expected = 1 if channel == "github" else 3  # Atlassian: switch, status, create
    assert len(children) == expected, children
    for child in children:
        assert child["parent_operation_id"] == operation["operation_id"], child
        assert (child["principal_kind"], child["principal_identity"]) == ("owner", "owner-session"), child
        assert (child["state"], child["receipts"]) == ("succeeded", 1), child
    # The identity read (GitHub) is a classified read, not an operation.
    creates = canned.creates()
    assert len(creates) == 1


# ── the argv carries no body; the file is the frozen bytes; forbidden plans ──


@pytest.mark.parametrize("channel", CHANNELS)
def test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes(
    hub: Hub, monkeypatch: pytest.MonkeyPatch, channel: str,
) -> None:
    from holdspeak.services import channel_contract

    canned = install(monkeypatch)
    _pid, update = room(hub, body=f"Status: green.\n\n{SENTINEL}\n")
    dest = _dest(hub, channel)
    prepared = prepare(hub, update, dest)["send"]
    assert send(hub, {"send_id": prepared["id"]}).json()["outcome"] == "sent"
    [create] = canned.creates()
    manifest = channel_contract.CHANNELS[channel].manifest
    assert any(tuple(create.argv[:len(p)]) == p for p in manifest.allowed_argv_prefixes), create.argv
    assert all(SENTINEL not in part for part in create.argv), create.argv
    assert channel_contract.sha256(create.body) == prepared["payload_digest"]
    assert create.mode == 0o600
    for call in canned.calls:
        assert all(SENTINEL not in part for part in call.argv)
    assert SENTINEL not in _receipt_texts(hub)
    # The private file is gone after the command.
    path = create.argv[create.argv.index("--from-json" if channel == "confluence" else "--body-file") + 1]
    assert not os.path.exists(path) and not os.path.exists(os.path.dirname(path))


def test_a_plan_with_a_forbidden_flag_or_a_second_key_cannot_be_built(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services.channel_cli import CLI_CHANNELS, _guard
    from holdspeak.services.channel_contract import ChannelRefused

    jira = CLI_CHANNELS["jira"]
    for flag in ("--jql", "--filter", "--edit-last", "--jql=project=PAY"):
        with pytest.raises(ValueError):
            _guard(("acli", "jira", "workitem", "comment", "create", "--key", "PAY-1", flag, "x"), jira.manifest)
    with pytest.raises(ValueError):
        _guard(("acli", "jira", "workitem", "delete", "--key", "PAY-1"), jira.manifest)
    for key in ("PAY-1,PAY-2", "PAY-1 PAY-2"):
        with pytest.raises(ChannelRefused) as refused:
            jira.plan({"key": key}, "/tmp/x")
        assert refused.value.code == "jira_key_not_single"
    # Saving a destination with two keys is refused by name, with its receipt.
    install(monkeypatch)
    saved = save(hub, "jira", key="PAY-1,PAY-2")
    assert saved["code"] == "jira_key_not_single", saved
    [operation] = _ops(hub, "channel.save_destination")
    assert (operation["state"], operation["outcome"]) == ("refused", "jira_key_not_single")


# ── the acli lock: a second Atlassian send waits ────────────────────────────


def test_an_atlassian_send_runs_inside_the_acli_lock_and_a_second_waits(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    canned = install(monkeypatch)
    entered, release = threading.Event(), threading.Event()
    creates: list[str] = []

    def hold(argv: list[str]) -> None:
        creates.append(argv[1])
        if len(creates) == 1:
            entered.set()
            assert release.wait(30)

    canned.on_create = hold
    _pid, update = room(hub)
    jira, confluence = _dest(hub, "jira"), _dest(hub, "confluence")
    first = prepare(hub, update, jira)["send"]["id"]
    second = prepare(hub, update, confluence)["send"]["id"]
    t1, a1 = in_thread(lambda: send(hub, {"send_id": first}))
    assert entered.wait(30)
    t2, a2 = in_thread(lambda: send(hub, {"send_id": second}))
    until(lambda: any(s["state"] == "dispatching" and s["id"] == second for s in sends(hub)))
    time.sleep(0.5)
    # The second send crossed its boundary but runs no acli command while the first holds the lock.
    assert [c.argv[1] for c in canned.calls] == ["jira", "jira", "jira"], [c.argv[:4] for c in canned.calls]
    release.set()
    t1.join(30)
    t2.join(30)
    assert a1[0].json()["outcome"] == "sent" and a2[0].json()["outcome"] == "sent"
    order = [(c.argv[1], c.argv[2], c.argv[3]) for c in canned.calls]
    assert order == [("jira", "auth", "switch"), ("jira", "auth", "status"), ("jira", "workitem", "comment"),
                     ("confluence", "auth", "switch"), ("confluence", "auth", "status"),
                     ("confluence", "blog", "create")], order


def test_a_status_that_names_another_account_never_creates(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    canned = install(monkeypatch)
    canned.answers[("acli", "jira", "auth", "status")] = lambda argv: (
        0, f"✓ Authenticated\n  Site: {SITE}\n  Email: someone-else@acme.example\n", "")
    _pid, update = room(hub)
    answer = send(hub, {"send_id": prepare(hub, update, _dest(hub, "jira"))["send"]["id"]}).json()
    assert (answer["outcome"], answer["send"]["reason"]) == ("failed", "atlassian_identity_unverified")
    assert canned.creates() == []


# ── the GitHub identity ─────────────────────────────────────────────────────


def test_a_github_destination_saved_as_a_is_refused_when_gh_is_b(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    canned = install(monkeypatch, Canned(login="login-a"))
    _pid, update = room(hub)
    dest = _dest(hub, "github")
    assert hub.client.get("/api/channels/destinations").json()["destinations"][0]["account"] == {
        "host": "github.com", "login": "login-a"}
    prepared = prepare(hub, update, dest)["send"]["id"]
    canned.login = "login-b"  # gh auth switch by hand
    refused = send(hub, {"send_id": prepared})
    assert refused.status_code == 409 and refused.json()["code"] == "github_identity_changed", refused.text
    [operation] = _ops(hub, "channel.send")
    assert (operation["state"], operation["outcome"]) == ("refused", "github_identity_changed")
    assert canned.creates() == [] and _ops(hub, "subprocess.exec") == []
    assert [s["state"] for s in sends(hub)] == ["prepared"]
    # The Phase 9 connection row says B: it is shown, never the identity.
    hub.db.automations.create_provider_connection(
        connection_id="wpc_github", provider_id="github", transport="connector_pack", state="connected",
        capability_manifest_json="{}", capability_revision=1, discovery_state="unknown")
    hub.db.automations.update_provider_connection("wpc_github", external_connection_ref="login-b",
                                                  last_checked_at="2026-09-28T00:00:00+00:00")
    again = send(hub, {"send_id": prepared})
    assert again.json()["code"] == "github_identity_changed", again.text
    # The destination names that connection and shows its Phase 9 state (never_checked before the row).
    [listed] = hub.client.get("/api/channels/destinations").json()["destinations"]
    assert listed["connection"] == {"id": "wpc_github", "state": "connected",
                                    "last_checked_at": "2026-09-28T00:00:00+00:00"}
    canned.login = "login-a"  # back as A (the row still says B): the send goes
    sent = send(hub, {"send_id": prepared}).json()
    assert sent["outcome"] == "sent", sent
    # Not logged in at all: refused by its own name.
    canned.answers[("gh", "api", "user")] = lambda argv: (1, "", "error connecting to github.com")
    other = prepare(hub, update, dest)["send"]["id"]
    assert send(hub, {"send_id": other}).json()["code"] == "github_not_logged_in"


# ── the size limits, refused by name ───────────────────────────────────────


@pytest.mark.parametrize("channel,limit", [("github", 65_536), ("jira", 32_767)])
def test_an_oversize_body_is_refused_by_name_before_any_dispatch(
    hub: Hub, monkeypatch: pytest.MonkeyPatch, channel: str, limit: int,
) -> None:
    canned = install(monkeypatch)
    dest = _dest(hub, channel)
    _pid, fits = room(hub, name="Fits", body="\u00e9" * limit)  # characters, not bytes
    assert prepare(hub, fits, dest)["send"]["size"] == 2 * limit
    _pid, update = room(hub, name="Too long", body="x" * (limit + 1))
    refused = hub.client.post("/api/channels/sends", json={"update_id": update, "destination_id": dest})
    assert refused.status_code == 400 and refused.json()["code"] == f"payload_too_large:{channel}", refused.text
    assert canned.creates() == []


# ── the Confluence title ────────────────────────────────────────────────────


def test_the_confluence_title_is_in_the_frozen_digest_and_never_in_argv_or_a_receipt(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.services.channel_contract import sha256

    title = "TITLE-SENTINEL-4d1e"
    canned = install(monkeypatch)
    _pid, update = room(hub, name=f"Cutover {title}")
    prepared = prepare(hub, update, _dest(hub, "confluence"))["send"]
    assert title in prepared["preview"]["title"]
    assert send(hub, {"send_id": prepared["id"]}).json()["outcome"] == "sent"
    [create] = canned.creates()
    frozen = json.loads(create.body)
    assert title in frozen["title"] and sha256(create.body) == prepared["payload_digest"]
    for call in canned.calls:
        assert all(title not in part for part in call.argv) and "--title" not in call.argv
    assert title not in _receipt_texts(hub)


# ── the outcome clauses ─────────────────────────────────────────────────────


_CREATE = {"github": ("gh", "issue", "comment"), "jira": ("acli", "jira", "workitem", "comment", "create"),
           "confluence": ("acli", "confluence", "blog", "create")}
_PINNED = {"github": (4, "", "gh: authentication required", "github_not_authenticated"),
           "jira": (1, "", "Error: work item PAY-7 does not exist", "jira_not_found"),
           "confluence": (1, "", "Error: unauthorized: use acli confluence auth login", "atlassian_unauthorized")}


def _timeout(argv: list[str]) -> Any:
    raise subprocess.TimeoutExpired(argv, 60)


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("case", ["unpinned_exit", "exit0_no_proof", "exit0_malformed", "timeout", "pinned"])
def test_only_a_pinned_error_is_failed_everything_else_unknown(
    hub: Hub, monkeypatch: pytest.MonkeyPatch, channel: str, case: str,
) -> None:
    canned = install(monkeypatch)
    answers = {
        "unpinned_exit": lambda argv: (2, "", "Error: something went sideways"),
        "exit0_no_proof": lambda argv: (0, "", ""),
        "exit0_malformed": lambda argv: (0, "https://github.com/other/repo/issues/1#issuecomment-5\n{not json", ""),
        "timeout": _timeout,
        "pinned": lambda argv: _PINNED[channel][:3],
    }
    canned.answers[_CREATE[channel]] = answers[case]
    _pid, update = room(hub)
    answer = send(hub, {"send_id": prepare(hub, update, _dest(hub, channel))["send"]["id"]})
    assert answer.status_code == 200, answer.text
    body = answer.json()
    [operation] = _ops(hub, "channel.send")
    if case == "pinned":
        assert (body["outcome"], body["send"]["reason"]) == ("failed", _PINNED[channel][3])
        assert operation["state"] == "failed"
        assert history(hub, update) == []
    else:
        assert body["outcome"] == "unknown", body
        assert operation["state"] == "indeterminate"
        assert [h["outcome"] for h in history(hub, update)] == ["unknown"]
        if case == "timeout":
            assert body["send"]["reason"] == "timeout"
    assert operation["receipts"] == 1 and len(canned.creates()) == 1


# ── the take-over of a CLI send never dispatches again ─────────────────────


@pytest.mark.parametrize("channel", CHANNELS)
def test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create(
    hub: Hub, monkeypatch: pytest.MonkeyPatch, channel: str,
) -> None:
    from holdspeak.services import channel_service

    canned = install(monkeypatch)
    real = channel_service.settle_in_transaction
    failed: list[int] = []

    def settle(conn: Any, **kwargs: Any) -> Any:
        settled = real(conn, **kwargs)
        if not failed:
            failed.append(1)
            raise RuntimeError("injected: the settle write failed after the effect")
        return settled

    monkeypatch.setattr(channel_service, "settle_in_transaction", settle)
    _pid, update = room(hub)
    body = {"send_id": prepare(hub, update, _dest(hub, channel))["send"]["id"], "command_id": f"cli-{channel}"}
    assert send(hub, body).status_code == 500
    assert [s["state"] for s in sends(hub)] == ["dispatching"]
    taken_over = send(hub, body)
    assert taken_over.status_code == 200, taken_over.text
    assert (taken_over.json()["outcome"], taken_over.json()["send"]["reason"]) == ("unknown", "interrupted")
    replayed = send(hub, body).json()
    assert (replayed["outcome"], replayed["operation_id"]) == ("unknown", taken_over.json()["operation_id"])
    assert len(canned.creates()) == 1
    [operation] = _ops(hub, "channel.send")
    assert (operation["state"], operation["receipts"]) == ("indeterminate", 1)
    assert [h["outcome"] for h in history(hub, update)] == ["unknown"]


# ── the nudge (F4, F5) ──────────────────────────────────────────────────────


def _nudge(hub: Hub) -> str:
    from test_philo5_the_loop_r2 import _nudge_step

    return _nudge_step(hub)


def test_f5_the_nudges_gh_child_is_parented_under_the_owner(hub: Hub, monkeypatch: pytest.MonkeyPatch) -> None:
    def gh(argv: list[str], **_kwargs: Any) -> Any:
        return subprocess.CompletedProcess(argv, 0, "https://github.com/example/payments/pull/7#issuecomment-1\n", "")

    monkeypatch.setattr(hub.root.project_steward_service, "_subprocess_runner", gh)
    resp = hub.client.post(f"/api/nudges/{_nudge(hub)}/send", json={"text": f"A look, please. {SENTINEL}"})
    assert resp.status_code == 200, resp.text
    [nudge] = _ops(hub, "nudge.send")
    [child] = _ops(hub, "subprocess.exec")
    assert child["parent_operation_id"] == nudge["operation_id"], (child, nudge)
    assert (child["principal_kind"], child["principal_identity"]) == ("owner", "owner-session"), child
    assert SENTINEL not in _receipt_texts(hub)


def test_f4_a_nudge_whose_gh_times_out_is_unknown_and_never_offered_again(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def gh(argv: list[str], **_kwargs: Any) -> Any:
        calls.append(list(argv))
        raise subprocess.TimeoutExpired(argv, 30)

    monkeypatch.setattr(hub.root.project_steward_service, "_subprocess_runner", gh)
    step_id = _nudge(hub)
    resp = hub.client.post(f"/api/nudges/{step_id}/send", json={"text": "A look, please."})
    assert resp.status_code == 200, resp.text
    answer = resp.json()
    assert answer["outcome"] == "unknown" and answer["success"] is False, answer
    step = hub.db.steward_steps.get_step(step_id)
    stored = json.loads(step["receipt_json"])
    assert step["state"] == "unknown" and stored["outcome"] == "unknown" and stored["reason"] == "timeout"
    [nudge] = _ops(hub, "nudge.send")
    assert (nudge["state"], nudge["outcome"]) == ("indeterminate", "timeout")
    pid = step["idempotency_key"].split(":")[1]
    assert hub.client.get(f"/api/projects/{pid}/nudges", params={"state": "proposed"}).json()["nudges"] == []
    again = hub.client.post(f"/api/nudges/{step_id}/send", json={"text": "A look, please."})
    assert again.status_code == 409 and again.json()["code"] == "nudge_not_proposed", again.text
    assert len(calls) == 1


def test_a_nudge_whose_settle_fails_after_the_comment_never_posts_twice_and_the_reaper_says_unknown(
    hub: Hub, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """nudge.send takes no command key: a second press is a new operation. The step crossed its boundary
    (``sending``) before gh ran, so the second press is refused; the real reaper then ends it UNKNOWN."""
    from _philo10_send import reap_past_deadline

    calls: list[list[str]] = []

    def gh(argv: list[str], **_kwargs: Any) -> Any:
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, "https://github.com/example/payments/pull/7#issuecomment-1\n", "")

    service = hub.root.project_steward_service
    monkeypatch.setattr(service, "_subprocess_runner", gh)
    real_append = service._ledger.append_in_transaction
    failed: list[int] = []

    def append(conn: Any, *args: Any, **kwargs: Any) -> Any:
        if not failed:
            failed.append(1)
            raise RuntimeError("injected: the settle write failed after the comment")
        return real_append(conn, *args, **kwargs)

    step_id = _nudge(hub)
    monkeypatch.setattr(service._ledger, "append_in_transaction", append)
    first = hub.client.post(f"/api/nudges/{step_id}/send", json={"text": "A look, please."})
    assert first.status_code == 500, first.text
    assert hub.db.steward_steps.get_step(step_id)["state"] == "sending"
    [nudge] = _ops(hub, "nudge.send")
    assert (nudge["state"], nudge["receipts"]) == ("claimed", 0)
    second = hub.client.post(f"/api/nudges/{step_id}/send", json={"text": "A look, please."})
    assert second.status_code == 409 and second.json()["code"] == "nudge_not_proposed", second.text
    assert len(calls) == 1
    reap_past_deadline(hub)
    step = hub.db.steward_steps.get_step(step_id)
    assert (step["state"], json.loads(step["receipt_json"])["outcome"]) == ("unknown", "unknown")
    [ended] = [o for o in _ops(hub, "nudge.send") if o["operation_id"] == nudge["operation_id"]]
    assert (ended["state"], ended["receipts"]) == ("indeterminate", 1)
    assert len(calls) == 1


# ── the steward prepares; it never sends (Q5) ──────────────────────────────


def _steward_run(hub: Hub, pid: str) -> dict[str, Any]:
    started = hub.client.post(f"/api/projects/{pid}/steward/runs", json={})
    assert started.status_code in (200, 202), started.text
    run_id = started.json().get("run_id") or started.json()["run"]["id"]
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        run = hub.db.steward_runs.get_run(run_id) or {}
        if run.get("state") in {"completed", "failed", "interrupted", "cancelled"}:
            return run
        time.sleep(0.05)
    raise AssertionError(f"run {run_id} never ended")


def test_the_steward_prepares_a_send_as_its_runs_child_and_its_send_is_refused(
    hub: Hub, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.services import project_steward_service as module
    from _philo10_send import destination

    pid, update = room(hub)
    dest = destination(hub, tmp_path / "out")
    policy = hub.client.put(f"/api/projects/{pid}/steward/policy", json={
        "eligible_effect_kinds": ["prepare_send"], "bounds": {"send_destination_ids": [dest]}})
    assert policy.status_code == 200, policy.text
    attempts: list[Any] = []
    real = module.ProjectStewardService._effect_prepare_send

    def prepare_then_try_to_send(self: Any, principal: Any, run_id: str, project_id: str) -> Any:
        receipt = real(self, principal, run_id, project_id)
        from holdspeak.services.channel_service import ChannelService
        from holdspeak.services.project_kernel import ProjectKernelRefused

        send_id = receipt["prepared"][0]
        try:  # a steward that tries to send its prepared row, through the real child path
            self._child(principal, "channel.send", {"send_id": send_id},
                        lambda: ChannelService(self._db).send(principal, send_id=send_id))
        except ProjectKernelRefused as exc:
            attempts.append(exc.code)
        return receipt

    monkeypatch.setattr(module.ProjectStewardService, "_effect_prepare_send", prepare_then_try_to_send)
    run = _steward_run(hub, pid)
    [prepare_op] = _ops(hub, "channel.prepare")
    assert prepare_op["parent_operation_id"] == run["operation_id"], prepare_op
    assert (prepare_op["state"], prepare_op["receipts"]) == ("succeeded", 1)
    [row] = sends(hub)
    assert (row["state"], row["prepare_operation_id"]) == ("prepared", prepare_op["operation_id"])
    assert (row["prepared_by_kind"], row["prepared_by_identity"]) == (prepare_op["principal_kind"],
                                                                      prepare_op["principal_identity"])
    assert attempts == ["owner_principal_required"], attempts
    [send_op] = _ops(hub, "channel.send")
    # Refused at admission (the codec), before the kernel records its parent: the receipt stands.
    assert (send_op["state"], send_op["outcome"], send_op["receipts"]) == ("refused", "owner_principal_required", 1)
    assert list((tmp_path / "out").iterdir()) == []  # nothing was sent
    # A second run does not prepare the same update to the same destination again.
    monkeypatch.setattr(module.ProjectStewardService, "_effect_prepare_send", real)
    _steward_run(hub, pid)
    assert len(sends(hub)) == 1
    # The owner sends it.
    assert send(hub, {"send_id": row["id"]}).json()["outcome"] == "sent"


def test_the_scheduled_steward_prepares_under_its_own_identity(hub: Hub, tmp_path: Path) -> None:
    from holdspeak.principals import Principal, PrincipalKind
    from _philo10_send import destination

    pid, _update = room(hub)
    dest = destination(hub, tmp_path / "out")
    assert hub.client.put(f"/api/projects/{pid}/steward/policy", json={
        "unattended_enabled": True, "eligible_effect_kinds": ["prepare_send"],
        "bounds": {"send_destination_ids": [dest]}}).status_code == 200
    answer = hub.root.project_steward_service.start_scheduled(
        Principal(PrincipalKind.SCHEDULER, "local-steward-conductor"), pid, "p10-02")
    until(lambda: any(o["operation_id"] == answer["operation_id"] and o["receipts"] for o in _ops(hub)))
    [prepare_op] = _ops(hub, "channel.prepare")
    assert prepare_op["parent_operation_id"] == answer["operation_id"]
    assert (prepare_op["principal_kind"], prepare_op["principal_identity"], prepare_op["state"]) == (
        "scheduler", "local-steward-conductor", "succeeded")
    [row] = sends(hub)
    assert (row["state"], row["prepared_by_kind"]) == ("prepared", "scheduler")


# ── a REAL kill during a CLI create; the restart answers UNKNOWN once ───────

_FAKE_GH = """#!/bin/sh
# A fake gh on PATH (the process edge; no account): the identity read answers,
# the comment records its pid and the body file's mode, then hangs until killed.
if [ "$1" = "api" ] && [ "$2" = "user" ]; then echo '{"login":"octo-owner"}'; exit 0; fi
if [ "$2" = "comment" ]; then
  body=""; prev=""
  for a in "$@"; do if [ "$prev" = "--body-file" ]; then body="$a"; fi; prev="$a"; done
  echo "$$ $(stat -f %Lp "$body" 2>/dev/null || stat -c %a "$body")" >> "$FAKE_GH_LOG"
  exec sleep 600
fi
exit 1
"""


@pytest.mark.timeout(240)
def test_a_real_kill_during_a_gh_create_ends_unknown_once_and_the_replay_never_runs_gh_again(tmp_path: Path) -> None:
    import signal
    import sqlite3

    from test_philo10_send_restart import HubProcess

    home, bin_dir, log = tmp_path / "home", tmp_path / "bin", tmp_path / "gh.log"
    home.mkdir()
    bin_dir.mkdir()
    fake = bin_dir / "gh"
    fake.write_text(_FAKE_GH)
    fake.chmod(0o755)
    env = {"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}", "FAKE_GH_LOG": str(log)}
    db = home / ".local" / "share" / "holdspeak" / "holdspeak.db"

    def rows(sql: str, *args: Any) -> list[dict[str, Any]]:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in conn.execute(sql, args).fetchall()]
        finally:
            conn.close()

    first = HubProcess(home, extra_env=env)
    pids: list[int] = []
    try:
        pid = first.call("POST", "/api/projects", {"name": "Payments ledger cutover"})[1]["project"]["id"]
        update = first.call("POST", f"/api/projects/{pid}/updates/draft", {})[1]["update"]["id"]
        assert first.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        status, saved = first.call("POST", "/api/channels/destinations", {
            "name": "Scratch issue", "channel": "github", "repo": "acme/scratch", "kind": "issue", "number": 1})
        assert status == 200, saved
        assert saved["destination"]["account"]["login"] == "octo-owner"
        status, prepared = first.call("POST", "/api/channels/sends",
                                      {"update_id": update, "destination_id": saved["destination"]["id"]})
        body = {"send_id": prepared["send"]["id"], "command_id": "kill-during-gh"}

        def press() -> None:
            try:
                first.call("POST", "/api/channels/send", body, timeout=120)
            except OSError:
                pass

        threading.Thread(target=press, daemon=True).start()
        until(lambda: log.exists() and log.read_text().strip())
        [line] = log.read_text().strip().splitlines()
        pids.append(int(line.split()[0]))
        assert line.split()[1] == "600"  # the body file the real gh would read is 0600
        [row] = rows("SELECT * FROM channel_sends WHERE state='dispatching'")
    finally:
        first.kill()
        for gh_pid in pids:
            try:
                os.kill(gh_pid, signal.SIGKILL)
            except OSError:
                pass
    second = HubProcess(home, extra_env=env)
    try:
        [settled] = rows("SELECT * FROM channel_sends WHERE id=?", row["id"])
        assert (settled["state"], settled["reason"]) == ("unknown", "interrupted"), settled
        [operation] = rows("SELECT o.state, r.outcome FROM kernel_operations o JOIN kernel_receipts r"
                           " ON r.operation_id=o.operation_id WHERE o.operation_id=?", row["send_operation_id"])
        assert operation == {"state": "indeterminate", "outcome": "hub_restart_during_send"}, operation
        status, replayed = second.call("POST", "/api/channels/send", body)
        assert status == 200 and (replayed["outcome"], replayed["send"]["reason"]) == ("unknown", "interrupted")
        assert len(log.read_text().strip().splitlines()) == 1  # gh never ran again
        history_rows = rows("SELECT outcome FROM project_update_deliveries WHERE update_id=?", update)
        assert history_rows == [{"outcome": "unknown"}]
    finally:
        second.kill()


# ── GATE 2, round two: every call that can run a CLI answers off the loop ──

_SLOW_GH = """#!/bin/sh
# A slow fake gh (1.5 s at the process edge, no account).
sleep 1.5
if [ "$1" = "api" ] && [ "$2" = "user" ]; then echo '{"login":"octo-owner"}'; exit 0; fi
if [ "$1" = "auth" ] && [ "$2" = "status" ]; then echo "Logged in to github.com account octo-owner"; exit 0; fi
exit 1
"""


@pytest.mark.timeout(240)
@pytest.mark.parametrize("call", ["mcp-save-destination", "http-save-destination", "mcp-recheck", "http-recheck"])
def test_gate2_a_slow_cli_read_in_setup_or_recheck_never_blocks_the_hub(tmp_path: Path, call: str) -> None:
    """Codex Astra r1 finding 2: MCP channel.save_destination's identity read blocked a read 1.73 s."""
    from test_philo10_send_restart import HubProcess

    home, bin_dir = tmp_path / "home", tmp_path / "bin"
    home.mkdir()
    bin_dir.mkdir()
    fake = bin_dir / "gh"
    fake.write_text(_SLOW_GH)
    fake.chmod(0o755)
    hub = HubProcess(home, extra_env={"PATH": f"{bin_dir}:{os.environ.get('PATH', '')}"})
    try:
        destination = {"name": "Scratch issue", "channel": "github", "repo": "acme/scratch", "kind": "issue",
                       "number": 1}

        def slow() -> Any:
            if call == "http-save-destination":
                return hub.call("POST", "/api/channels/destinations", destination)
            if call == "http-recheck":
                return hub.call("POST", "/api/connections/github/recheck", {})
            name, args = (("channel.save_destination", destination) if call == "mcp-save-destination"
                          else ("connection.recheck", {"provider_id": "github"}))
            return hub.call("POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                 "params": {"name": name, "arguments": args}})

        thread, answer = in_thread(slow)
        time.sleep(0.4)  # the call is inside its 1.5 s gh read
        started = time.perf_counter()
        status, _listed = hub.call("GET", "/api/channels/destinations")
        read = time.perf_counter() - started
        thread.join(30)
        assert status == 200
        assert answer and answer[0][0] == 200, answer
        if call.startswith("mcp"):
            assert answer[0][1]["result"]["isError"] is False, answer
        assert read < 0.5, f"{call}: the read waited {read:.3f} s during the slow gh call"
    finally:
        hub.kill()


# ── #694 merged: one authority table, one owner-press flag, one blocking_io flag ──


def test_the_sends_are_egress_owner_presses_and_blocking_io_in_the_one_table() -> None:
    """``blocking_io`` (threading) lives on the descriptor; authority lives in ``mcp/tool_authority.py``.

    The two axes differ (``connection.recheck`` is work yet blocks on gh; ``channel.discard`` is egress
    yet writes only the database), so each has ONE source and this census ties them: every blocking
    operation has an authority row, and the two sends are EGRESS, owner presses and blocking.
    """
    from holdspeak import operations
    from holdspeak.kernel.channel_send import owner_press_operations
    from holdspeak.mcp.tool_authority import EGRESS, TOOL_AUTHORITY

    blocking = {d.name for d in operations.DESCRIPTORS if d.blocking_io}
    assert blocking == {"channel.send", "channel.save_destination", "nudge.send", "connection.recheck"}
    assert all(name in TOOL_AUTHORITY for name in blocking), blocking - set(TOOL_AUTHORITY)
    for name in ("channel.send", "nudge.send"):
        assert TOOL_AUTHORITY[name] == EGRESS and name in owner_press_operations() and name in blocking, name
    # The kernel's steward-child refusal reads the SAME flag the descriptors declare (no second list).
    assert owner_press_operations() == frozenset(d.name for d in operations.DESCRIPTORS if d.owner_press)
