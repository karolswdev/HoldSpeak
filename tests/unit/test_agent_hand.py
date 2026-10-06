"""Conductor K2: Hand to agent (brief, launch, origin, MCP, /agent).

The brief composes existing grounding parts and cuts People data; the hand
service finds the item's Project repository, creates a new worktree, arms
the gate for exactly that path and launches through ``process.spawn`` with
``origin_ref`` on the launch and the attempt. tmux and the agent are faked
(the HS-94-07 precedent); git is real.
"""
from __future__ import annotations

import asyncio
import json
import shlex
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import coder_gate
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
from holdspeak.kernel.broker import Broker
from holdspeak.kernel.journal import JournalStore
from holdspeak.kernel.model import OperationSpec
from holdspeak.kernel.process_input import ProcessInputCodec
from holdspeak.kernel.process_spawn import ProcessSpawnCodec
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_brief import (
    AgentBriefRefused,
    compose_agent_brief,
    project_for_item,
)
from holdspeak.services.agent_hand_service import (
    AgentHandRefused,
    AgentHandService,
    resolve_project_repository,
    worktree_spec,
)
from holdspeak.web.routes.agent_hand import build_agent_hand_router
from tests.unit.test_factory_launch import FakeTmuxServer, T0, _make_repo

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
PROJECT = "proj-0123456789ab"


# ── seed ─────────────────────────────────────────────────────────────


def _seed(db: Database) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO projects (id, name) VALUES (?, ?)", (PROJECT, "Railsproj")
        )
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("m1", "2026-10-01T10:00:00", "Planning sync"),
        )
        conn.execute(
            "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
            "VALUES ('m1', 'We must fix the login timeout.', 'Me', 0, 1)"
        )
        conn.execute(
            "INSERT INTO meeting_projects (meeting_id, project_id, confidence) VALUES ('m1', ?, 0.9)",
            (PROJECT,),
        )
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, status) "
            "VALUES ('ai_1', 'm1', 'Fix the login timeout', 'Me', 'open')"
        )
        conn.execute(
            "INSERT INTO decisions (id, text, rationale, decided_at, source_artifact_id, source_meeting_id) "
            "VALUES ('d1', 'Use Redis for sessions', 'It is fast', '2026-10-01', 'art1', 'm1')"
        )
        conn.execute(
            "INSERT INTO artifacts (id, meeting_id, artifact_type, title, body_markdown) "
            "VALUES ('art1', 'm1', 'summary', 'Sync summary', 'The login times out after 5 s.')"
        )
        conn.execute(
            "INSERT INTO decision_records (id, decision_text, rationale, source_type, source_id, created_at, updated_at) "
            "VALUES ('dr1', 'Ship behind a flag', 'Low risk', 'decision', 'd1', '2026-10-01', '2026-10-01')"
        )
        conn.execute(
            "INSERT INTO decision_record_sources (id, record_id, source_type, source_ref, created_at) "
            "VALUES ('drs1', 'dr1', 'meeting', 'm1', '2026-10-01')"
        )
        conn.execute(
            "INSERT INTO project_items (id, project_id, item_type, title, summary) "
            "VALUES ('pi1', ?, 'risk', 'Login risk', 'Users get logged out')",
            (PROJECT,),
        )
        conn.execute(
            "INSERT INTO notes (id, title, body_markdown) VALUES ('n1', 'Login notes', "
            "'Timeout is 5 s.\n\n## People\nAlice is on leave; 1:1 Thursday.')"
        )
        conn.execute(
            "INSERT INTO project_resources (project_id, resource_ref) VALUES (?, 'note:n1')",
            (PROJECT,),
        )


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "hub.db")
    _seed(database)
    return database


# ── compose_agent_brief ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "ref, title",
    [
        ("action:ai_1", "Fix the login timeout"),
        ("decision:d1", "Use Redis for sessions"),
        ("decision_record:dr1", "Ship behind a flag"),
        ("project_item:pi1", "Login risk"),
        ("note:n1", "Login notes"),
        ("meeting:m1", "Planning sync"),
        ("artifact:art1", "Sync summary"),
    ],
)
def test_brief_composes_each_kind_with_the_stanza(db, ref, title) -> None:
    brief = compose_agent_brief(db, ref, control_mode="yolo")
    text = brief["text"]
    assert ref in brief["refs"]
    assert f'"{title}"' in text
    assert "Control mode: YOLO" in text
    assert "open a pull request" in text
    assert f"The pull request body names the item: {ref}." in text
    assert brief["bytes"] == len(text.encode("utf-8"))
    assert brief["project_id"] == PROJECT


def test_brief_carries_the_meeting_and_project_records(db) -> None:
    brief = compose_agent_brief(db, "action:ai_1", control_mode="neutral", instruction="Keep it small.")
    text = brief["text"]
    assert "meeting:m1" in brief["refs"]
    assert "We must fix the login timeout." in text
    assert "Instruction from the owner:\nKeep it small." in text
    assert "Control mode: Normal" in text
    assert "decision_record:dr1: Ship behind a flag" in text


def test_brief_reads_hs_facts_of_the_target_repo(db, tmp_path) -> None:
    repo = tmp_path / "repo"
    (repo / ".hs").mkdir(parents=True)
    (repo / ".hs" / "context.md").write_text("Run make test before a PR.\n", encoding="utf-8")
    brief = compose_agent_brief(db, "action:ai_1", control_mode="yolo", repo_path=str(repo))
    assert "Run make test before a PR." in brief["text"]


def test_brief_cuts_people(db) -> None:
    brief = compose_agent_brief(db, "note:n1", control_mode="yolo")
    assert "Timeout is 5 s." in brief["text"]
    assert "Alice" not in brief["text"]
    assert "1:1 Thursday" not in brief["text"]
    assert brief["people_cut"] >= 1


def test_brief_refuses_over_cap_by_name(db) -> None:
    with pytest.raises(AgentBriefRefused) as exc:
        compose_agent_brief(db, "action:ai_1", control_mode="yolo", cap_bytes=200)
    assert exc.value.reason == "brief_over_cap"


def test_brief_refuses_unknown_and_unsupported(db) -> None:
    with pytest.raises(AgentBriefRefused) as exc:
        compose_agent_brief(db, "action:nope", control_mode="yolo")
    assert exc.value.reason == "item_unknown"
    with pytest.raises(AgentBriefRefused) as exc:
        compose_agent_brief(db, "people:p1", control_mode="yolo")
    assert exc.value.reason == "item_kind_unsupported"


def test_project_for_item_follows_meeting_and_filing(db) -> None:
    assert project_for_item(db, "action", "ai_1") == PROJECT
    assert project_for_item(db, "note", "n1") == PROJECT
    assert project_for_item(db, "project_item", "pi1") == PROJECT
    assert project_for_item(db, "artifact", "art1") == PROJECT


# ── the hand service, end to end with tmux and the agent faked ──────


class _Tmux(FakeTmuxServer):
    ended = False
    screen = None
    on_keys = None
    #: After the first look at the pane, the pane no longer proves itself
    #: (it is not the one spawned): identity checks fail.
    identity_lost_after_peek = False
    _peeked = False

    def __call__(self, argv, cwd=None):
        if argv[0] == "tmux" and argv[1] == "capture-pane":
            self._peeked = True
        if argv[0] == "tmux" and argv[1] == "display-message" and self.identity_lost_after_peek and self._peeked:
            return self._err("can't find pane")
        if argv[0] == "tmux" and argv[1] == "has-session":
            name = argv[argv.index("-t") + 1]
            return self._ok() if name in self.sessions and not self.ended else self._err("no session")
        if argv[0] == "tmux" and argv[1] in ("send-keys", "load-buffer", "paste-buffer"):
            self.calls.append(list(argv))
            return self._ok()
        result = super().__call__(argv, cwd)
        if argv[0] == "tmux" and argv[1] == "new-session" and self.screen is not None and result.returncode == 0:
            pane = self.sessions[argv[argv.index("-s") + 1]][0]
            self.meta[pane]["content"] = self.screen()
        return result


def _rig(
    tmp_path, db, monkeypatch, *, which=None, screen=None, register_when=None,
    item=("action", "ai_1"), project=PROJECT, agent="claude", text_fails=False,
):
    """Real git, a real kernel broker and receipts, the real steering path;
    tmux and the agent are canned (the process edge only). The clone is
    registered under the Project's name (the repository drawer's label)."""
    repo = _make_repo(tmp_path)
    registry = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
    source, _ = registry.register(str(repo), label="railsproj")
    tmux = _Tmux()
    targets = TerminalTargetRegistry(runner=tmux)
    typed: list = []
    keys_sent: list = []

    def text_transport(*, pane, text, submit=True):
        if text_fails:
            raise RuntimeError("tmux refused the paste")
        typed.append((pane, text))

    def keys_transport(*, pane, keys):
        keys_sent.append((pane, [value for _kind, value in keys]))
        on_keys = getattr(tmux, "on_keys", None)
        if on_keys is not None:
            on_keys(pane, [value for _kind, value in keys])

    # No transport reaches a real tmux server: text and keys are recorded.
    processor = NodeCommandProcessor(
        node_id="local", targets=targets, ledger=NodeReceiptLedger(tmp_path / "ledger.db"),
        runner=tmux, audit=lambda **kw: 1, wall_now=lambda: T0,
        text_transport=text_transport, keys_transport=keys_transport,
    )
    commands = HubCommandService(
        repo=db.delivery_receipts, processor=processor, local_node_id="local",
        mode_loader=lambda: "neutral", wall_now=lambda: T0,
    )
    launches = LaunchLedger(tmp_path / "launches.json")
    service = LaunchService(
        profiles=AgentProfileStore(tmp_path / "profiles.json"),
        registry=registry, targets=targets, commands=commands,
        attempts=db.work_attempts, ledger=launches, runner=tmux,
        local_node_id="local", wall_now=lambda: T0, which=which,
    )
    spawn = ProcessSpawnCodec(service, db.delivery_receipts)
    process_input = ProcessInputCodec(db.delivery_receipts)
    broker = Broker(
        JournalStore(db._connection),
        (
            OperationSpec(spawn.name, spawn.version, spawn, "agent.submit", "propose"),
            OperationSpec(process_input.name, process_input.version, process_input, "agent.submit", "propose"),
        ),
    )
    service.bind_kernel(broker)
    gate_path = tmp_path / "gate.json"
    monkeypatch.setattr(coder_gate, "GATE_CONFIG_FILE", gate_path)
    settings = tmp_path / "spawn-settings.json"
    monkeypatch.setattr(coder_gate, "write_spawn_settings", lambda: settings)
    # K6: the per-launch --mcp-config files stay in this test's directory.
    monkeypatch.setattr("holdspeak.delivery.agent_mcp.mcp_config_dir", lambda: tmp_path / "mcp")
    monkeypatch.setattr("holdspeak.delivery.first_message.LAUNCH_POLL_SECONDS", 0.05)
    monkeypatch.setattr("holdspeak.delivery.first_message.TRUST_WAIT_SECONDS", 1.0)
    if screen is not None:
        tmux.screen = lambda: screen(worktree)
    # The rider: the launched agent's SessionStart reports its Story claim
    # from the new worktree (what `agent-hook ingest` writes).
    worktree = (repo.parent / f"hs-{item[0]}-{item[1]}").resolve()

    def claims(**_kw):
        if not worktree.exists():
            return []
        if register_when is not None and not register_when(tmux):
            return []
        return [{
            "session_key": f"{agent}:smoke-session", "agent": agent, "lifecycle": "working",
            "repo_root": str(worktree), "cwd": str(worktree),
            "story_claim": {"project": project, "story_id": f"{item[0]}-{item[1]}", "claimed_by": f"rider:{agent}"},
        }]

    monkeypatch.setattr("holdspeak.agent_context.sessions.list_agent_story_claims", claims)
    hand = AgentHandService(
        db, launch_service=lambda: service, control_mode=lambda: "yolo",
        gate_path=gate_path, project_map={"projects": {}},
    )
    return SimpleNamespace(
        text_transport=text_transport, keys_transport=keys_transport,
        typed=typed, keys_sent=keys_sent, worktree=worktree, broker=broker,
        repo=repo, registry=registry, source=source, tmux=tmux, service=service,
        launches=launches, hand=hand, gate_path=gate_path, settings=settings, db=db,
        commands=commands,
    )


def test_hand_launches_claude_in_a_new_worktree_with_origin(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    result = rig.hand.hand(OWNER, "action", "ai_1", instruction="Keep it small.")

    assert result["status"] == "launched", result
    assert result["worktree"] == {"name": "hs-action-ai_1", "branch": "hs/action-ai_1"}
    assert result["story_ref"] == {"project": PROJECT, "story_id": "action-ai_1"}
    assert result["origin_ref"] == {"kind": "action", "id": "ai_1"}
    assert result["gate"] == "gated"
    assert result["brief"]["bytes"] > 0 and "action:ai_1" in result["brief"]["refs"]

    # The new worktree is real, on its branch, next to the repository.
    worktree = rig.repo.parent / "hs-action-ai_1"
    assert (worktree / ".git").exists()

    # origin_ref rides the launch record and the Work attempt.
    record = rig.launches.get(result["launch_id"])
    assert record["origin_ref"] == {"kind": "action", "id": "ai_1"}
    attempt = db.work_attempts.get(result["attempt_id"])
    assert attempt.origin_ref == "action:ai_1"
    assert attempt.to_wire()["origin_ref"] == {"kind": "action", "id": "ai_1"}
    assert attempt.story_id == "action-ai_1"

    # The gate holds Bash for exactly the new worktree, and the spawn
    # carries HoldSpeak's settings.
    gate = json.loads(rig.gate_path.read_text(encoding="utf-8"))
    assert gate["armed"] is False
    assert gate["repos"] == {str(worktree.resolve()): ["Bash"]}
    assert gate["armed_paths"] == [str(worktree.resolve())]
    spawn_argv = next(c for c in rig.tmux.calls if c[1] == "new-session")
    command = spawn_argv[spawn_argv.index("-s") + 2]
    assert command.startswith(f"cd {shlex.quote(str(worktree.resolve()))} && ")
    assert f"--settings {rig.settings}" in command
    assert "HOLDSPEAK_STORY_REF=" + shlex.quote(f"{PROJECT}/action-ai_1") in command

    # The brief waits for the rider, then is the first process.input child
    # of the spawn: the session binds the SAME launch attempt.
    assert result["instruction_state"] == "pending"
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    assert record["commands"]["instruction"]
    attempt = db.work_attempts.get(result["attempt_id"])
    assert attempt.session_id == "claude:smoke-session"
    rig.tmux.ended = True


def _wait_for(read, key, value, timeout=30.0):
    import time

    deadline = time.monotonic() + timeout
    while True:
        row = read() or {}
        if row.get(key) == value or time.monotonic() > deadline:
            assert row.get(key) == value, row
            return row
        time.sleep(0.05)


def test_hand_refuses_no_repository(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    with db._connection() as conn:
        conn.execute("UPDATE projects SET name='Unrelated' WHERE id=?", (PROJECT,))
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "action", "ai_1")
    assert exc.value.reason == "no_repository"


@pytest.mark.parametrize(
    "missing, reason", [("tmux", "tmux_absent"), ("claude", "executable_absent")]
)
def test_hand_preflight_refuses_before_any_envelope(tmp_path, db, monkeypatch, missing, reason) -> None:
    rig = _rig(tmp_path, db, monkeypatch, which=lambda name: None if name == missing else f"/bin/{name}")
    with pytest.raises(AgentHandRefused) as exc:
        rig.hand.hand(OWNER, "action", "ai_1")
    assert exc.value.reason == reason
    assert rig.tmux.calls == []
    assert not (rig.repo.parent / "hs-action-ai_1").exists()
    assert not rig.gate_path.exists()


def test_launch_preflight_refuses_by_name(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch, which=lambda name: None if name == "codex" else f"/bin/{name}")
    request = {
        "agent_profile_id": "codex-default",
        "source_id": rig.source.source_id,
        "worktree": worktree_spec("action", "ai_1"),
        "story_ref": {"project": PROJECT, "story_id": "action-ai_1"},
    }
    from holdspeak.delivery.factory_launch import LaunchRefused

    with pytest.raises(LaunchRefused) as exc:
        rig.service.launch(request)
    assert exc.value.reason == "executable_absent"
    assert rig.tmux.calls == []


def test_resolve_repository_registers_a_project_map_entry(tmp_path, db) -> None:
    repo = _make_repo(tmp_path / "clone")
    registry = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
    assert registry.sources() == []
    source = resolve_project_repository(
        db, PROJECT, registry, project_map={"projects": {"railsproj": str(repo)}}
    )
    assert source is not None and registry.get(source.source_id) is not None
    assert resolve_project_repository(db, None, registry, project_map={"projects": {}}) is None


# ── the route, the MCP tool, the Thread command ─────────────────────


class _FakeHand:
    def __init__(self) -> None:
        self.calls = []

    def hand_item(self, principal, *, kind, id, **kw):  # noqa: A002
        return self.hand(principal, kind, id, **kw)

    def hand(self, principal, kind, item_id, **kw):
        self.calls.append((kind, item_id, kw))
        if item_id == "missing":
            raise AgentHandRefused("no_repository")
        return {"status": "launched", "launch_id": "launch_x", "attempt_id": "att_x",
                "worktree": {"name": "hs-action-1", "branch": "hs/action-1"},
                "brief": {"bytes": 10, "refs": ["action:1"], "people_cut": 0}}


def test_route_hands_and_refuses_by_name() -> None:
    fake = _FakeHand()
    app = FastAPI()
    app.include_router(build_agent_hand_router(SimpleNamespace(agent_hand_service=fake, delivery_service=None)))
    client = TestClient(app)
    ok = client.post("/api/agent/hand", json={"kind": "action", "id": "1", "instruction": "go"})
    assert ok.status_code == 202
    assert ok.json()["launch_id"] == "launch_x"
    assert fake.calls[0][2]["instruction"] == "go"
    refused = client.post("/api/agent/hand", json={"kind": "action", "id": "missing"})
    assert refused.status_code == 409 and refused.json()["error"] == "no_repository"
    assert client.post("/api/agent/hand", json={"kind": "action"}).status_code == 400
    bad = client.post("/api/agent/hand", json={"kind": "people", "id": "p1"})
    assert bad.status_code == 400 and bad.json()["error"] == "invalid_arguments"


def test_operation_refuses_an_agent_principal() -> None:
    from holdspeak import operations

    fake = _FakeHand()
    ops = operations.bind_available({"agent_hand_service": fake})
    agent = Principal(PrincipalKind.AGENT, "agent:tmux:x")
    from holdspeak.services.errors import ServiceError

    with pytest.raises(ServiceError) as exc:
        ops.invoke(agent, "agent.hand", {"kind": "action", "id": "1"})
    assert exc.value.code == "owner_required"
    assert fake.calls == []
    assert ops.invoke(OWNER, "agent.hand", {"kind": "action", "id": "1"})["launch_id"] == "launch_x"


def test_mcp_tool_is_registered_and_classified_egress() -> None:
    from holdspeak.mcp import tool_authority
    from holdspeak.mcp.families import FAMILIES

    names = {tool["name"] for family in FAMILIES for tool in family.TOOLS}
    assert "agent.hand" in names
    assert tool_authority.TOOL_AUTHORITY["agent.hand"] == tool_authority.EGRESS
    assert "agent.hand" in tool_authority.THREAD_EXCLUDED


def test_spawn_settings_carry_rider_and_gate_hooks(tmp_path) -> None:
    path = coder_gate.write_spawn_settings(tmp_path / "s.json", project_root=tmp_path)
    hooks = json.loads(path.read_text(encoding="utf-8"))["hooks"]
    commands = {
        event: [h["command"] for entry in entries for h in entry["hooks"]]
        for event, entries in hooks.items()
    }
    rider = f"uv run --project {tmp_path.resolve()} holdspeak agent-hook ingest --agent claude"
    gate = f"uv run --project {tmp_path.resolve()} holdspeak gate hook"
    for event in ("SessionStart", "UserPromptSubmit", "Notification", "PostToolUse", "Stop", "SessionEnd", "CwdChanged"):
        assert rider in commands[event], event
    assert gate in commands["PreToolUse"]
    assert gate in commands["SessionStart"]


def test_derived_story_ref_holds_the_token_rule() -> None:
    from holdspeak.delivery.factory_launch import LaunchRefused, derived_story_ref

    assert derived_story_ref("desk", "note", "n1") == {"project": "desk", "story_id": "note-n1"}
    with pytest.raises(LaunchRefused) as exc:
        derived_story_ref("desk", "note", "x" * 80)
    assert exc.value.reason == "story_ref_invalid"


def test_origin_ref_refuses_bad_tokens(tmp_path, db, monkeypatch) -> None:
    from holdspeak.delivery.factory_launch import LaunchRefused

    rig = _rig(tmp_path, db, monkeypatch)
    request = {
        "agent_profile_id": "claude-default",
        "source_id": rig.source.source_id,
        "worktree": worktree_spec("action", "ai_1"),
        "story_ref": {"project": PROJECT, "story_id": "action-ai_1"},
        "origin_ref": {"kind": "people", "id": "p1"},
    }
    with pytest.raises(LaunchRefused) as exc:
        rig.service.launch(request)
    assert exc.value.reason == "origin_ref_invalid"
    assert rig.tmux.calls == []


def test_resolve_repository_matches_a_room_github_watch_by_origin(tmp_path, db) -> None:
    import subprocess

    repo = _make_repo(tmp_path / "clone")
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin",
                    "git@github.com:acme/railsproj.git"], check=True)
    registry = DeliveryRegistry(tmp_path / "sources.json", map_path=tmp_path / "absent.json")
    registered, _ = registry.register(str(repo))
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches (id, connector_id, query_kind, query_json, project_id) "
            "VALUES ('w1', 'gh', 'pulls', ?, ?)",
            (json.dumps({"repository": "acme/railsproj"}), PROJECT),
        )
        conn.execute("UPDATE projects SET name='Other name' WHERE id=?", (PROJECT,))
    source = resolve_project_repository(db, PROJECT, registry, project_map={"projects": {}})
    assert source is not None and source.source_id == registered.source_id


def test_hand_arms_only_its_worktree_not_other_listed_repos(tmp_path, db, monkeypatch) -> None:
    rig = _rig(tmp_path, db, monkeypatch)
    other = tmp_path / "other-repo"
    other.mkdir()
    coder_gate.save_gate_config(
        coder_gate.GateConfig(armed=False, repos={str(other.resolve()): ["Bash"]}), rig.gate_path
    )
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "launched", result
    _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    rig.tmux.ended = True
    config = coder_gate.load_gate_config(rig.gate_path)
    worktree = (rig.repo.parent / "hs-action-ai_1").resolve()
    assert config.armed is False  # the master switch is not touched
    assert coder_gate.gate_matches(config, cwd=str(worktree), tool="Bash")
    assert not coder_gate.gate_matches(config, cwd=str(other.resolve()), tool="Bash")


# ── folder trust: answered once, only for this launch's worktree ─────


def _trust_screen(path, cursor_on_yes=False):
    no, yes = ("  ", "\u276f ") if cursor_on_yes else ("\u276f ", "  ")
    shown = str(path)
    return (
        " Accessing workspace:\n\n " + shown[:40] + "\n " + shown[40:] + "\n\n"
        " Quick safety check: Is this a project you created or one you trust? (Like your\n"
        " own code, a well-known open source project, or work from your team).\n\n"
        f" {no}No, exit\n {yes}Yes, I trust this folder\n\n Enter to confirm \u00b7 Esc to cancel"
    )


def _trusting_tmux(rig):
    """The fake Claude: Down moves the cursor, Enter on Yes clears the prompt."""
    state = {"cursor_on_yes": False}

    def on_keys(pane, keys):
        for key in keys:
            if key == "Down":
                state["cursor_on_yes"] = True
                rig.tmux.meta[pane]["content"] = _trust_screen(rig.worktree, cursor_on_yes=True)
            elif key == "Enter" and state["cursor_on_yes"]:
                rig.tmux.meta[pane]["content"] = "Claude Code ready\n\u276f "

    rig.tmux.on_keys = on_keys


def test_trust_prompt_for_this_worktree_gets_exactly_one_confirm(tmp_path, db, monkeypatch) -> None:
    rig = _rig(
        tmp_path, db, monkeypatch,
        screen=lambda worktree: _trust_screen(worktree),
        register_when=lambda tmux: all("trust" not in m["content"] for m in tmux.meta.values()),
    )
    rig.worktree = (rig.repo.parent / "hs-action-ai_1").resolve()
    _trusting_tmux(rig)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    rig.tmux.ended = True
    assert record["trust_state"] == "answered"
    sequence = [key for _pane, keys in rig.keys_sent for key in keys]
    assert sequence == ["Down", "Enter"]  # one confirm, never typed blindly
    assert len(record["commands"]["trust"]) == 2  # each key a receipted process.input
    assert len(rig.typed) == 1 and "action:ai_1" in rig.typed[0][1]  # then the brief


def test_any_other_screen_gets_nothing(tmp_path, db, monkeypatch) -> None:
    rig = _rig(
        tmp_path, db, monkeypatch,
        screen=lambda worktree: "Welcome to Claude Code\n\u276f Dark mode\n  Light mode",
    )
    result = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
    rig.tmux.ended = True
    assert record["trust_state"] == "not_seen"
    assert rig.keys_sent == []


def test_a_trust_prompt_for_another_folder_gets_nothing(tmp_path, db, monkeypatch) -> None:
    rig = _rig(
        tmp_path, db, monkeypatch,
        screen=lambda worktree: _trust_screen(tmp_path / "somewhere-else", cursor_on_yes=True),
        register_when=lambda tmux: False,
    )
    result = rig.hand.hand(OWNER, "action", "ai_1")
    record = _wait_for(lambda: rig.launches.get(result["launch_id"]), "trust_state", "not_seen")
    rig.tmux.ended = True
    assert rig.keys_sent == []
    assert record["instruction_state"] == "pending"
