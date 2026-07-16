"""HS-94-07 — the factory HTTP surface + remote factory verbs through
the HS-94-06 envelope, assembled in-test (the delivery-router
precedent).

Proven here:

- ``GET /profiles`` lists the node-configured templates (fixed
  executables only);
- ``POST /launch`` launches from {profile, source, worktree, story} and
  refuses a smuggled executable/argv/shell BY NAME with a typed 400;
- ``GET /discover`` yields panes/sessions as IMMUTABLE targets with
  node + source/worktree + profile — no pre-known ``pane:%N``, no
  filesystem path on the wire;
- kill by the DISCOVERED generation rides the envelope: a duplicate
  command_id returns the SAME receipt with ONE execution, and the
  node + hub receipt halves join by command_id;
- remote rename claims through the queue leg, executes once on the
  node, reports its receipt back, and deduplicates on replay.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.coder_steering import arm, clear_grants
from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery import DeliveryRegistry
from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
from holdspeak.delivery.factory_launch import (
    AgentProfileStore,
    LaunchLedger,
    LaunchService,
)
from holdspeak.delivery.terminal import TerminalTargetRegistry
from holdspeak.web.context import WebContext
from holdspeak.web.routes.delivery_factory import build_delivery_factory_router

T0 = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)
KEY = "claude:hs94-factory"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    )


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir(parents=True)
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.test")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")
    return repo


class FakeTmuxServer:
    """tmux double for the injectable-runner seam; git passes through
    to the real binary."""

    def __init__(self) -> None:
        self.sessions: dict[str, list[str]] = {}
        self.meta: dict[str, dict] = {}
        self._next = 1
        self.calls: list[list[str]] = []

    @staticmethod
    def _ok(out: str = "") -> SimpleNamespace:
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    @staticmethod
    def _err(msg: str) -> SimpleNamespace:
        return SimpleNamespace(returncode=1, stdout="", stderr=msg)

    def _pane_of(self, target: str) -> str | None:
        text = str(target)
        if text.startswith("%"):
            return text if text in self.meta else None
        panes = self.sessions.get(text.split(":")[0])
        return panes[0] if panes else None

    def __call__(self, argv, cwd=None):
        if argv[0] == "git":
            return subprocess.run(
                argv, cwd=cwd, capture_output=True, text=True, timeout=60
            )
        self.calls.append(list(argv))
        verb = argv[1]
        if verb == "new-session":
            name = argv[argv.index("-s") + 1]
            if name in self.sessions:
                return self._err(f"duplicate session: {name}")
            command = argv[5] if len(argv) > 5 else ""
            path = shlex.split(command)[1] if command.startswith("cd ") else "/"
            pane = f"%{self._next}"
            self._next += 1
            self.sessions[name] = [pane]
            self.meta[pane] = {"session": name, "path": path, "content": f"{name} up"}
            return self._ok()
        if verb == "list-panes":
            fmt = argv[argv.index("-F") + 1]
            if "-a" in argv:
                panes = list(self.meta)
            else:
                name = argv[argv.index("-t") + 1].split(":")[0]
                if name not in self.sessions:
                    return self._err("no session")
                panes = list(self.sessions[name])
            lines = [
                fmt.replace("#{session_name}", self.meta[p]["session"])
                .replace("#{pane_id}", p)
                .replace("#{pane_current_path}", self.meta[p]["path"])
                for p in panes
            ]
            return self._ok("\n".join(lines) + "\n")
        if verb == "display-message":
            pane = self._pane_of(argv[argv.index("-t") + 1])
            return self._ok(pane + "\n") if pane else self._err("no pane")
        if verb == "kill-session":
            target = argv[argv.index("-t") + 1]
            pane = self._pane_of(target)
            name = (
                self.meta[pane]["session"]
                if pane
                else (target if target in self.sessions else None)
            )
            if name is None:
                return self._err("no session")
            for p in self.sessions.pop(name):
                self.meta.pop(p, None)
            return self._ok()
        if verb == "kill-pane":
            target = argv[argv.index("-t") + 1]
            if target not in self.meta:
                return self._err("no pane")
            name = self.meta.pop(target)["session"]
            self.sessions[name].remove(target)
            if not self.sessions[name]:
                self.sessions.pop(name)
            return self._ok()
        if verb == "rename-session":
            old, new = argv[argv.index("-t") + 1], argv[-1]
            if old not in self.sessions:
                return self._err(f"session not found: {old}")
            panes = self.sessions.pop(old)
            self.sessions[new] = panes
            for p in panes:
                self.meta[p]["session"] = new
            return self._ok()
        raise AssertionError(f"unexpected tmux argv: {argv}")


@pytest.fixture(autouse=True)
def _fresh_grants():
    clear_grants()
    yield
    clear_grants()


@pytest.fixture
def rig(tmp_path):
    repo = _make_repo(tmp_path)
    registry = DeliveryRegistry(
        tmp_path / "sources.json", map_path=tmp_path / "absent-map.json"
    )
    source, tree = registry.register(str(repo), label="proj")
    tmux = FakeTmuxServer()
    targets = TerminalTargetRegistry(runner=tmux)
    processor = NodeCommandProcessor(
        node_id="local",
        targets=targets,
        ledger=NodeReceiptLedger(tmp_path / "ledger.db"),
        runner=tmux,
        audit=lambda **kw: 1,
        wall_now=lambda: T0,
    )
    db = Database(tmp_path / "hub.db")
    commands = HubCommandService(
        repo=db.delivery_receipts,
        processor=processor,
        local_node_id="local",
        mode_loader=lambda: "neutral",
        wall_now=lambda: T0,
    )
    profiles = AgentProfileStore(tmp_path / "profiles.json")
    service = LaunchService(
        profiles=profiles,
        registry=registry,
        targets=targets,
        commands=commands,
        attempts=db.work_attempts,
        ledger=LaunchLedger(tmp_path / "launches.json"),
        runner=tmux,
        local_node_id="local",
        wall_now=lambda: T0,
    )
    app = FastAPI()
    app.include_router(
        build_delivery_factory_router(
            WebContext(get_state=lambda: {}),
            service=service,
            profiles=profiles,
            sync_on_read=False,
        )
    )
    return SimpleNamespace(
        client=TestClient(app),
        repo=repo,
        source_id=source.source_id,
        worktree_id=tree.worktree_id,
        tmux=tmux,
        targets=targets,
        processor=processor,
        commands=commands,
        service=service,
        tmp=tmp_path,
    )


def _launch_body(rig, **over) -> dict:
    body = {
        "agent_profile_id": "codex-default",
        "source_id": rig.source_id,
        "worktree": {"mode": "existing", "worktree_id": rig.worktree_id},
        "story_ref": {"project": "demo", "story_id": "DM-1-01"},
        "session_label": "hs-route-launch",
    }
    body.update(over)
    return body


# ── the routes ───────────────────────────────────────────────────────


def test_profiles_route_lists_only_fixed_launchers(rig) -> None:
    res = rig.client.get("/api/delivery/factory/profiles")
    assert res.status_code == 200
    doc = res.json()
    assert doc["agent_profiles_schema"] == 1
    assert doc["known_executables"] == ["claude", "codex"]
    assert {p["executable"] for p in doc["profiles"]} <= {"claude", "codex"}


def test_launch_route_launches_and_refuses_by_name(rig) -> None:
    ok = rig.client.post("/api/delivery/factory/launch", json=_launch_body(rig))
    assert ok.status_code == 200
    record = ok.json()
    assert record["state"] == "launched"
    assert record["target"]["target_id"].startswith("term_")
    assert "hs-route-launch" in rig.tmux.sessions

    smuggled = rig.client.post(
        "/api/delivery/factory/launch",
        json=_launch_body(rig, executable="/bin/sh", session_label="hs-evil"),
    )
    assert smuggled.status_code == 400
    assert smuggled.json()["error"] == "executable_not_client_settable"

    bad_option = rig.client.post(
        "/api/delivery/factory/launch",
        json=_launch_body(
            rig,
            options={"sandbox": "danger; rm -rf /"},
            session_label="hs-bad-option",
        ),
    )
    assert bad_option.status_code == 400
    assert bad_option.json()["error"] == "option_value_not_allowed"
    assert "hs-evil" not in rig.tmux.sessions
    assert "hs-bad-option" not in rig.tmux.sessions


def test_discover_yields_immutable_targets_path_free(rig) -> None:
    launched = rig.client.post(
        "/api/delivery/factory/launch", json=_launch_body(rig)
    ).json()
    res = rig.client.get("/api/delivery/factory/discover")
    assert res.status_code == 200
    doc = res.json()
    assert doc["discover_schema"] == 1
    assert doc["status"] == "ok"
    (row,) = doc["targets"]
    assert row["node_id"] == "local"
    assert row["session"] == "hs-route-launch"
    assert row["target_id"] == launched["target"]["target_id"]
    assert row["target_generation"] == launched["target"]["target_generation"]
    assert row["source_id"] == rig.source_id
    assert row["worktree_id"] == rig.worktree_id
    assert row["profile_id"] == "codex-default"
    assert row["story_ref"] == {"project": "demo", "story_id": "DM-1-01"}
    assert row["attempt_id"] == launched["attempt_id"]
    assert row["session_bound"] is False
    # §13: no filesystem path crosses to the wire.
    assert str(rig.tmp) not in json.dumps(doc)


# ── remote factory verbs through the envelope ────────────────────────


def test_kill_by_discovered_generation_is_idempotent_with_joined_receipts(
    rig,
) -> None:
    launched = rig.service.launch(_launch_body(rig, session_label="hs-kill-me"))
    row = next(
        r
        for r in rig.service.discover()["targets"]
        if r["session"] == "hs-kill-me"
    )
    # Kill is gated like a steer: arm the pane the discovery named.
    armed = arm(KEY, row["pane_id"], runner=rig.tmux, control_mode="neutral")
    assert armed["status"] == "armed"

    command_id = "5b2e6c2e-6b7a-4f6e-9a3d-2c1b0a990002"
    request = {
        "command_id": command_id,
        "target_id": row["target_id"],
        "target_generation": row["target_generation"],
        "operation": {"family": "coder_factory", "verb": "factory.kill"},
        "payload": {"session_key": KEY, "scope": "session"},
    }
    before = rig.processor.executions
    first = rig.commands.submit(request)
    assert first["receipt"]["state"] == "succeeded"
    assert first["receipt"]["outcome"] == "killed"
    assert "hs-kill-me" not in rig.tmux.sessions

    # The lost-response retry: SAME command_id, SAME receipt, ONE kill.
    again = rig.commands.submit(request)
    assert again["duplicate"] is True
    assert again["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]
    assert rig.processor.executions == before + 1

    # Node + hub receipt halves join by command_id.
    joined = rig.commands.receipt(command_id)
    assert joined["hub_state"] == "complete"
    assert joined["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]
    assert rig.processor.ledger.get(command_id)["outcome"] == "killed"

    # A dead target refuses TYPED for a fresh command — never a blind hit
    # on whatever reused the address.
    fresh = rig.commands.submit({**request, "command_id": None})
    assert fresh["receipt"]["state"] == "refused"
    assert fresh["receipt"]["outcome"] == "target_gone"
    assert launched["attempt_id"]  # the attempt row outlives the process


def test_remote_rename_claims_executes_once_and_reports_back(rig) -> None:
    rig.service.launch(_launch_body(rig, session_label="hs-old-name"))
    sent = rig.commands.submit(
        {
            "node_id": "node_r9",
            "operation": {"family": "coder_factory", "verb": "factory.rename"},
            "payload": {"target_session": "hs-old-name", "new_name": "hs-new-name"},
            "expected_sequence": 1,
        }
    )
    assert sent["state"] == "sent"
    cid = sent["command_id"]

    # The remote node claims its queue and executes through the SAME
    # processor code a local command uses (§2: local is a node, not a
    # special case) — with its OWN durable dedup ledger.
    remote_node = NodeCommandProcessor(
        node_id="node_r9",
        targets=TerminalTargetRegistry(runner=rig.tmux),
        ledger=NodeReceiptLedger(rig.tmp / "remote-ledger.db"),
        runner=rig.tmux,
        audit=lambda **kw: 1,
        wall_now=lambda: T0,
    )
    (envelope,) = rig.commands.claim_for_node("node_r9")
    receipt = remote_node.process(envelope)
    assert receipt["outcome"] == "renamed"
    assert "hs-new-name" in rig.tmux.sessions
    assert "hs-old-name" not in rig.tmux.sessions

    # A replayed claim deduplicates on the node: same receipt, no rerun.
    replay = remote_node.process(envelope)
    assert replay["receipt_id"] == receipt["receipt_id"]
    assert len([c for c in rig.tmux.calls if c[1] == "rename-session"]) == 1

    # The results leg joins the node half into the hub Receipt.
    ack = rig.commands.record_results("node_r9", [receipt])
    assert ack["processed"] == 1
    joined = rig.commands.receipt(cid)
    assert joined["hub_state"] == "complete"
    assert joined["receipt"]["outcome"] == "renamed"
    assert joined["payload_head"] == "rename hs-old-name -> hs-new-name"
