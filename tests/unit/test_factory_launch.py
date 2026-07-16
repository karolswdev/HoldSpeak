"""HS-94-07 — Agent Profiles, the worktree-create op, and Story-bound
agent launch.

Real git worktrees (the HS-94-01/04 precedent) + an injectable tmux
runner (the HS-94-06 precedent; a real Claude/Codex binary is never
required). Proven here:

- profiles are node-configured argv templates with FIXED executables
  and allow-listed option slots; a hand-edited shell smuggle is dropped
  whole, and client option values outside the closed choices refuse;
- one launch creates exactly ONE Work attempt + ONE immutable target +
  ONE spawn receipt, with the composed command carrying the profile
  argv and the Story ref (never a client byte);
- client-supplied executable/argv/command/shell/args/env/worktree.path
  refuse BY NAME, pre-execution;
- worktree.create is a DISTINCT typed op through the command envelope:
  its receipt survives a failed launch (worktree retained + named),
  and its guards (injection, out-of-root, duplicate, dirty reuse)
  refuse before any git/tmux runs;
- launch-without-rider is a retained partial state — ``starting`` →
  ``unknown``/``failed_to_register`` with the terminal still openable
  and no orphan attempt/session;
- the rider claim binds the SAME launch attempt (no duplicate row),
  and the generic HS-94-04 sweep afterwards creates nothing new.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.agent_context.sessions import ingest_agent_hook_event
from holdspeak.db import Database
from holdspeak.db.delivery_receipts import NodeReceiptLedger
from holdspeak.delivery import DeliveryRegistry
from holdspeak.delivery.attempts import WorkAttemptService, resolver_from_registry
from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
from holdspeak.delivery.factory_launch import (
    AgentProfileStore,
    LaunchLedger,
    LaunchRefused,
    LaunchService,
    execute_worktree_create,
)
from holdspeak.delivery.terminal import TerminalTargetRegistry

T0 = datetime(2026, 7, 16, 12, 0, 0, tzinfo=timezone.utc)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True
    )


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "railsproj"
    repo.mkdir(parents=True)
    (repo / "README.md").write_text("# demo\n", encoding="utf-8")
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.test")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")
    return repo


class FakeTmuxServer:
    """A tmux server double for the injectable-runner seam. git argv
    passes through to the REAL git (worktree creation is real)."""

    def __init__(self) -> None:
        self.sessions: dict[str, list[str]] = {}
        self.meta: dict[str, dict] = {}
        self._next = 1
        self.fail_new_session = False
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
            if self.fail_new_session:
                return self._err("launcher exploded")
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
        if verb == "capture-pane":
            pane = self._pane_of(argv[argv.index("-t") + 1])
            return self._ok(self.meta[pane]["content"] + "\n") if pane else self._err("no pane")
        raise AssertionError(f"unexpected tmux argv: {argv}")


@pytest.fixture
def rig(tmp_path):
    repo = _make_repo(tmp_path)
    registry = DeliveryRegistry(
        tmp_path / "sources.json", map_path=tmp_path / "absent-map.json"
    )
    source, tree = registry.register(str(repo), label="railsproj")
    tmux = FakeTmuxServer()
    targets = TerminalTargetRegistry(runner=tmux)
    audit_rows: list[dict] = []
    processor = NodeCommandProcessor(
        node_id="local",
        targets=targets,
        ledger=NodeReceiptLedger(tmp_path / "ledger.db"),
        runner=tmux,
        audit=lambda **kw: audit_rows.append(kw) or len(audit_rows),
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
    launches = LaunchLedger(tmp_path / "launches.json")
    service = LaunchService(
        profiles=profiles,
        registry=registry,
        targets=targets,
        commands=commands,
        attempts=db.work_attempts,
        ledger=launches,
        runner=tmux,
        local_node_id="local",
        wall_now=lambda: T0,
    )
    return SimpleNamespace(
        repo=repo,
        registry=registry,
        source_id=source.source_id,
        worktree_id=tree.worktree_id,
        tmux=tmux,
        targets=targets,
        processor=processor,
        commands=commands,
        db=db,
        attempts=db.work_attempts,
        profiles=profiles,
        launches=launches,
        service=service,
        audit_rows=audit_rows,
        tmp=tmp_path,
    )


def _request(rig, **over) -> dict:
    base = {
        "agent_profile_id": "claude-default",
        "source_id": rig.source_id,
        "worktree": {"mode": "existing", "worktree_id": rig.worktree_id},
        "story_ref": {"project": "demo", "story_id": "DM-1-01"},
        "session_label": "hs-dm-1-01",
    }
    base.update(over)
    return base


# ── Agent Profiles ───────────────────────────────────────────────────


def test_profile_store_seeds_fixed_executables_and_drops_a_smuggled_shell(
    tmp_path,
) -> None:
    path = tmp_path / "profiles.json"
    store = AgentProfileStore(path)
    wire = store.to_wire()
    assert wire["agent_profiles_schema"] == 1
    assert {p["profile_id"] for p in wire["profiles"]} == {
        "claude-default",
        "codex-default",
    }
    assert all(p["executable"] in ("claude", "codex") for p in wire["profiles"])

    # A hand-edited smuggle (a path executable, a metachar arg, a free
    # option) is dropped WHOLE on reload — never partially accepted.
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["profiles"].append(
        {
            "profile_id": "evil",
            "label": "evil",
            "executable": "/bin/sh",
            "args": ["-c", "rm -rf /"],
        }
    )
    doc["profiles"].append(
        {
            "profile_id": "evil2",
            "label": "evil2",
            "executable": "claude",
            "args": ["--flag", "$(reboot)"],
        }
    )
    path.write_text(json.dumps(doc), encoding="utf-8")
    reloaded = AgentProfileStore(path)
    ids = {p["profile_id"] for p in reloaded.to_wire()["profiles"]}
    assert "evil" not in ids and "evil2" not in ids
    assert {"claude-default", "codex-default"} <= ids


def test_resolve_argv_holds_the_option_allow_list(tmp_path) -> None:
    store = AgentProfileStore(tmp_path / "profiles.json")
    assert store.resolve_argv("claude-default", {"model": "opus"}) == [
        "claude",
        "--model",
        "opus",
    ]
    with pytest.raises(LaunchRefused) as exc:
        store.resolve_argv("nope", None)
    assert exc.value.reason == "profile_unknown"
    with pytest.raises(LaunchRefused) as exc:
        store.resolve_argv("claude-default", {"dangerous": "yes"})
    assert exc.value.reason == "option_not_allowed"
    with pytest.raises(LaunchRefused) as exc:
        store.resolve_argv("claude-default", {"model": "opus; rm -rf /"})
    assert exc.value.reason == "option_value_not_allowed"


# ── the launch transaction ───────────────────────────────────────────


def test_launch_creates_one_attempt_one_target_one_receipt(rig) -> None:
    record = rig.service.launch(_request(rig))
    assert record["state"] == "launched"

    # ONE attempt: kind=launch, exact, session unbound until the rider.
    attempts = rig.attempts.find_active()
    assert len(attempts) == 1
    attempt = attempts[0]
    assert attempt.kind == "launch" and attempt.exact
    assert attempt.session_id is None and attempt.state == "starting"
    assert attempt.attempt_id == record["attempt_id"]
    assert attempt.target_id == record["target"]["target_id"]

    # ONE immutable target, verifiable now.
    verified = rig.targets.verify(
        record["target"]["target_id"], record["target"]["target_generation"]
    )
    assert verified["status"] == "ok"

    # ONE spawn receipt through the envelope (node + hub halves joined).
    assert record["commands"]["worktree_create"] is None
    joined = rig.commands.receipt(record["commands"]["spawn"])
    assert joined["hub_state"] == "complete"
    assert joined["receipt"]["outcome"] == "spawned"

    # The composed command is the profile argv + Story ref, nothing else.
    spawn_argv = next(c for c in rig.tmux.calls if c[1] == "new-session")
    command = spawn_argv[5]
    assert command.startswith(f"cd {shlex.quote(str(rig.repo))} && ")
    assert "HOLDSPEAK_STORY_REF=demo/DM-1-01" in command
    assert command.endswith("exec claude")
    assert "hs-dm-1-01" in rig.tmux.sessions

    # The wire record is path-free (§13).
    assert str(rig.tmp) not in json.dumps(record)


def test_client_supplied_execution_fields_refuse_by_name(rig) -> None:
    for field in ("executable", "argv", "command", "shell", "args", "env"):
        with pytest.raises(LaunchRefused) as exc:
            rig.service.launch(_request(rig, **{field: "claude"}))
        assert exc.value.reason == f"{field}_not_client_settable"
    with pytest.raises(LaunchRefused) as exc:
        rig.service.launch(
            _request(rig, worktree={"mode": "existing", "path": "/etc"})
        )
    assert exc.value.reason == "worktree_path_not_client_settable"
    with pytest.raises(LaunchRefused) as exc:
        rig.service.launch(
            _request(rig, story_ref={"project": "demo", "story_id": "DM 01; rm"})
        )
    assert exc.value.reason == "story_ref_invalid"
    # All pre-execution: nothing touched tmux, nothing created an attempt.
    assert rig.tmux.calls == []
    assert rig.attempts.find_active() == []


def test_worktree_create_is_distinct_and_rollback_retains_it_on_launch_failure(
    rig,
) -> None:
    rig.tmux.fail_new_session = True
    record = rig.service.launch(
        _request(
            rig,
            worktree={"mode": "new", "name": "wt-hs94", "branch": "agent/hs94"},
            session_label="hs-wt-launch",
        )
    )
    assert record["state"] == "failed"
    assert record["failure"]["stage"] == "spawn"
    assert record["rollback"]["worktree"] == "retained"
    assert (
        record["rollback"]["worktree_command_id"]
        == record["commands"]["worktree_create"]
    )

    # The DISTINCT worktree-create receipt records what exists.
    joined = rig.commands.receipt(record["commands"]["worktree_create"])
    assert joined["hub_state"] == "complete"
    assert joined["receipt"]["outcome"] == "worktree_created"
    assert joined["payload_head"] == "worktree wt-hs94 -b agent/hs94"
    assert str(rig.tmp) not in joined["payload_head"]

    # The worktree is REAL and retained on disk, registered to the source.
    created = rig.tmp / "wt-hs94"
    assert created.is_dir() and (created / ".git").exists()
    source = rig.registry.get(rig.source_id)
    assert len(source.worktrees) == 2

    # No orphan: zero attempts, no target, no session.
    assert rig.attempts.find_active() == []
    assert rig.tmux.sessions == {}

    # Recovery: the retained worktree launches as `existing` once the
    # launcher works again — no re-create, no duplicate.
    rig.tmux.fail_new_session = False
    new_wt = next(
        wt for wt in source.worktrees if wt.worktree_id != rig.worktree_id
    )
    retried = rig.service.launch(
        _request(
            rig,
            worktree={"mode": "existing", "worktree_id": new_wt.worktree_id},
            session_label="hs-wt-retry",
        )
    )
    assert retried["state"] == "launched"
    assert retried["worktree_id"] == new_wt.worktree_id


def test_worktree_guards_refuse_pre_execution(rig) -> None:
    # Injection in the worktree name: refused before ANY git/tmux runs.
    for name in ("../evil", "wt;rm", "-flag", "a b"):
        with pytest.raises(LaunchRefused) as exc:
            rig.service.launch(
                _request(rig, worktree={"mode": "new", "name": name})
            )
        assert exc.value.reason == "worktree_name_invalid"
    assert not (rig.tmp / "evil").exists()

    # Injection in the branch.
    for branch in ("bad..branch", "-evil", "b ranch", "x;y"):
        with pytest.raises(LaunchRefused) as exc:
            rig.service.launch(
                _request(rig, worktree={"mode": "new", "name": "ok-wt", "branch": branch})
            )
        assert exc.value.reason == "branch_invalid"

    # Duplicate worktree (the path already exists).
    (rig.tmp / "dup-wt").mkdir()
    with pytest.raises(LaunchRefused) as exc:
        rig.service.launch(_request(rig, worktree={"mode": "new", "name": "dup-wt"}))
    assert exc.value.reason == "worktree_duplicate"

    # Unknown mode and unknown worktree id.
    with pytest.raises(LaunchRefused) as exc:
        rig.service.launch(_request(rig, worktree={"mode": "yolo"}))
    assert exc.value.reason == "worktree_mode_invalid"
    with pytest.raises(LaunchRefused) as exc:
        rig.service.launch(
            _request(rig, worktree={"mode": "existing", "worktree_id": "wt_nope"})
        )
    assert exc.value.reason == "worktree_unknown"

    # Dirty-worktree reuse refuses pre-execution.
    (rig.repo / "uncommitted.txt").write_text("dirt\n", encoding="utf-8")
    with pytest.raises(LaunchRefused) as exc:
        rig.service.launch(_request(rig))
    assert exc.value.reason == "worktree_dirty"

    # Nothing ever reached tmux; no attempt exists.
    assert rig.tmux.calls == []
    assert rig.attempts.find_active() == []


def test_worktree_create_executor_refuses_out_of_root_without_running_git(
    rig,
) -> None:
    def _never(argv, cwd=None):
        raise AssertionError(f"git must not run: {argv}")

    out = execute_worktree_create(
        {
            "name": "escape",
            "branch": "escape",
            "repo_path": str(rig.repo),
            "path": str(rig.tmp / "elsewhere" / "escape"),
        },
        runner=_never,
        audit=lambda **kw: 1,
    )
    assert out["status"] == "out_of_root"
    # And the receipt-safe detail carries no filesystem path.
    assert str(rig.tmp) not in str(out.get("detail"))


def test_worktree_create_through_the_envelope_deduplicates(rig) -> None:
    command_id = "9a7c1c2e-1b7a-4f6e-9a3d-2c1b0a990001"
    request = {
        "command_id": command_id,
        "operation": {"family": "delivery_factory", "verb": "worktree.create"},
        "payload": {
            "name": "wt-dedup",
            "branch": "wt-dedup",
            "repo_path": str(rig.repo),
            "path": str(rig.tmp / "wt-dedup"),
        },
    }
    first = rig.commands.submit(request)
    assert first["receipt"]["outcome"] == "worktree_created"
    again = rig.commands.submit(request)
    assert again["duplicate"] is True
    assert again["receipt"]["receipt_id"] == first["receipt"]["receipt_id"]
    assert (rig.tmp / "wt-dedup").is_dir()


# ── launch without a rider: retained partial state ───────────────────


def test_launch_without_rider_is_a_retained_partial_state(rig) -> None:
    record = rig.service.launch(_request(rig))
    assert record["state"] == "launched"

    # Inside the registration window nothing moves.
    assert rig.service.expire_unregistered(now=T0 + timedelta(seconds=30)) == 0

    # Past it: starting → unknown, reason failed_to_register.
    assert rig.service.expire_unregistered(now=T0 + timedelta(seconds=300)) == 1
    attempt = rig.attempts.get(record["attempt_id"])
    assert attempt.state == "unknown"
    assert attempt.session_id is None
    events = rig.attempts.events(attempt.attempt_id)
    assert any(e["reason"] == "failed_to_register" for e in events)
    assert rig.launches.get(record["launch_id"])["state"] == "failed_to_register"

    # The terminal is STILL openable: target verifies, session lives.
    verified = rig.targets.verify(
        record["target"]["target_id"], record["target"]["target_generation"]
    )
    assert verified["status"] == "ok"
    assert "hs-dm-1-01" in rig.tmux.sessions

    # No orphan: the attempt is visible (unknown), not deleted, and a
    # LATE rider still recovers it.
    state = rig.tmp / "agent_sessions.json"
    ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "late1",
            "hook_event_name": "SessionStart",
            "cwd": str(rig.repo),
        },
        state_path=state,
        env={"HOLDSPEAK_STORY_REF": "demo/DM-1-01"},
    )
    summary = rig.service.bind_rider_claims(state_path=state)
    assert summary["bound"] == 1
    recovered = rig.attempts.get(record["attempt_id"])
    assert recovered.session_id == "claude:late1"
    assert recovered.state == "working"


# ── rider binding without duplication ────────────────────────────────


def test_rider_claim_binds_the_launch_attempt_without_duplication(rig) -> None:
    record = rig.service.launch(_request(rig))
    state = rig.tmp / "agent_sessions.json"
    ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "s1",
            "hook_event_name": "SessionStart",
            "cwd": str(rig.repo),
        },
        state_path=state,
        env={"HOLDSPEAK_STORY_REF": "demo/DM-1-01"},
    )

    summary = rig.service.bind_rider_claims(state_path=state)
    assert summary["bound"] == 1

    # The SAME attempt gained the session — no new row.
    attempts = rig.attempts.find_active()
    assert len(attempts) == 1
    attempt = attempts[0]
    assert attempt.attempt_id == record["attempt_id"]
    assert attempt.kind == "launch"
    assert attempt.session_id == "claude:s1"
    assert attempt.state == "working"
    assert any(
        e["reason"] == "rider_registered"
        for e in rig.attempts.events(attempt.attempt_id)
    )
    assert rig.launches.get(record["launch_id"])["state"] == "registered"

    # The generic HS-94-04 sweep afterwards creates NOTHING new.
    generic = WorkAttemptService(
        rig.attempts, resolver=resolver_from_registry(rig.registry)
    )
    swept = generic.sync_rider_claims(state_path=state)
    assert swept["created"] == 0
    assert len(rig.attempts.find_active()) == 1

    # Re-binding is a no-op, and the bound attempt no longer expires.
    assert rig.service.bind_rider_claims(state_path=state)["bound"] == 0
    assert rig.service.expire_unregistered(now=T0 + timedelta(seconds=999)) == 0


def test_bind_skips_a_session_already_exactly_bound(rig) -> None:
    # The session is already exactly pinned to other work.
    generic = WorkAttemptService(
        rig.attempts, resolver=resolver_from_registry(rig.registry)
    )
    generic.manual_attach(
        source_id=rig.source_id,
        worktree_id=rig.worktree_id,
        project="demo",
        story_id="DM-9-99",
        session_id="claude:s1",
    )
    record = rig.service.launch(_request(rig))
    state = rig.tmp / "agent_sessions.json"
    ingest_agent_hook_event(
        agent="claude",
        payload={
            "session_id": "s1",
            "hook_event_name": "SessionStart",
            "cwd": str(rig.repo),
        },
        state_path=state,
        env={"HOLDSPEAK_STORY_REF": "demo/DM-1-01"},
    )
    summary = rig.service.bind_rider_claims(state_path=state)
    assert summary["bound"] == 0
    # The launch attempt stays honestly unbound; the manual pin stands.
    assert rig.attempts.get(record["attempt_id"]).session_id is None
