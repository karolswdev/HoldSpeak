"""Conductor R2: launch credentials and ownership survive a hub restart; no
token on argv; a hub-minted session credential ends with its session.

1. Durability. A launch-bound credential, its palette, its launch grants
   (memory read, decision proposals, project additions) and its ownership
   (origin item, created records) live through a hub restart: the real hub
   app is rebuilt from the same database after the process memory is gone.
   A revoke before the restart stays a refusal after it. Expired rows are
   not loaded. The token is stored only as its SHA-256.
2. No token on argv. The spawn's tmux argv carries no token; a 0600 file
   in a 0700 directory carries it, and the session's first shell reads it,
   deletes it and runs the agent. Not in any log either.
   The bootstrap runs with no user shell and tracing off, so a traced rc
   file never prints the token (real tmux). A session that does not read
   its file is not reported spawned; nothing is left behind.
4. Astra round 1 on #911: a revoke, rotation, issue or ownership write that
   does not reach SQLite is never acknowledged; a slow reload or a wall
   clock set back never extends a credential; a rebound target leaves its
   old owner on disk too; a launch credential that expired (or was revoked)
   while the hub was down ends its LIVE grants at start.
5. A credential the hub minted for one Claude session (``claude:<id>``)
   ends on every SessionEnd, /clear and /resume included; the launch's own
   process credential still stays over /clear and /resume.

Real producers: the real hub app (``MeetingWebServer``) over HTTP, the real
credential store and database, the real K2 launch engine. Only tmux and the
agent process are faked, at the process boundary.
"""
from __future__ import annotations

import logging
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak import coder_factory, coder_gate
from holdspeak.db import Database
from holdspeak.mcp.palettes import CONDUCTOR, resolve_palette
from holdspeak.principals import AgentCredentialStore, agent_credentials, launch_reader
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402

from tests.unit._spawn_env import env_file_of, token_of  # noqa: E402
from tests.unit.test_agent_hand import OWNER, _rig, _seed, _wait_for  # noqa: E402
from tests.unit.test_conductor_k6_agent_mcp import (  # noqa: E402
    _call,
    _client,
    _codex_launch,
    _launch_credential,
    _reach,
    _result,
    _rpc,
    _spawn,
)


def _clear_store() -> None:
    for credential in agent_credentials.list_credentials():
        agent_credentials.revoke(credential.principal.identity)


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    (tmp_path / "hub").mkdir()
    _clear_store()
    hub = _boot(tmp_path / "hub", monkeypatch)
    yield hub
    _clear_store()
    agent_credentials.detach()
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.fixture
def db(tmp_path):
    (tmp_path / "rig").mkdir(exist_ok=True)
    database = Database(tmp_path / "rig" / "launch.db")
    _seed(database)
    return database


def _restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Hub:
    """The hub process ends (its memory and its hooks are gone, nothing is
    revoked) and the real app is rebuilt from the same database."""
    from holdspeak.db import reset_database
    from holdspeak.services import conductor_launch

    agent_credentials._forget_memory()
    agent_credentials.launch_revoked_hooks.clear()
    monkeypatch.setattr(conductor_launch, "_HOOK_INSTALLED", False)
    reset_database()
    composition.install(composition.bare(label="pytest"))
    return _boot(tmp_path / "hub", monkeypatch)


# ── 1. Durability ────────────────────────────────────────────────────


def test_a_launch_survives_a_hub_restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hub: Hub) -> None:
    from holdspeak.services import desk_delegation, project_delegation
    from holdspeak.services.conductor_launch import grant_decision_proposals, grant_project_additions

    _reach(hub, False)
    own = hub.client.post("/api/projects", json={"name": "Launch project"}).json()["project"]
    owner_note = hub.root.primitive_service.create_note(OWNER, title="Owner plan", body_markdown="keep")["id"]
    launch_id = "launch_r2restart001"
    identity = coder_factory.launch_identity(launch_id)
    credential = _launch_credential(launch_id, scope=("action:ai_1",), project=own["id"])
    assert grant_decision_proposals(OWNER, identity, ttl_seconds=3600) is not None
    assert grant_project_additions(OWNER, identity, own["id"], ttl_seconds=3600) is not None
    agent = _client(hub, credential.token)
    is_error, note = _result(_call(agent, "desk.create", {"kind": "notes", "data": {"title": "Agent note"}}))
    assert is_error is False, note
    before = agent_credentials.derive_credential(credential.token)
    tools_before = {t["name"] for t in _rpc(agent, "tools/list").json()["result"]["tools"]}

    hub = _restart(tmp_path, monkeypatch)
    agent = _client(hub, credential.token)

    # The same credential: palette, launch, Project, scope and ownership.
    after = agent_credentials.derive_credential(credential.token)
    assert after is not None, "the restart ended the agent's access"
    assert after.id == before.id
    assert after.palette == before.palette == resolve_palette(CONDUCTOR)
    assert after.palette_name == CONDUCTOR
    assert (after.launch_id, after.project_id) == (launch_id, own["id"])
    assert agent_credentials.in_scope(launch_id, "action:ai_1")
    assert agent_credentials.created_by(launch_id, f"note:{note['id']}")
    assert not agent_credentials.created_by(launch_id, f"note:{owner_note}")
    assert launch_reader(after.principal), "memory read ends with the restart"
    # Over HTTP: the same tools, its own Note editable, the owner's refused.
    tools_after = {t["name"] for t in _rpc(agent, "tools/list").json()["result"]["tools"]}
    assert tools_after == tools_before
    is_error, edited = _result(_call(agent, "desk.update", {"kind": "notes", "id": note["id"], "data": {"title": "Agent note v2"}}))
    assert is_error is False and edited["title"] == "Agent note v2", edited
    is_error, body = _result(_call(agent, "desk.update", {"kind": "notes", "id": owner_note, "data": {"title": "Hijacked"}}))
    assert is_error and body["code"] == "not_this_launch", body
    # The grants: a decision is still proposed; the Project still takes a link.
    is_error, made = _result(_call(agent, "desk.create", {"kind": "decisions", "data": {"title": "After restart"}}))
    assert is_error is False and made["status"] == "proposed", made
    assert desk_delegation.live_grant(identity)
    assert own["id"] in project_delegation.live_projects(identity)

    # A revoke after the restart still ends the grants (the hook is back).
    assert coder_factory.revoke_launch(launch_id) is True
    assert not desk_delegation.live_grant(identity)
    assert project_delegation.live_projects(identity) == []
    assert _rpc(agent, "tools/list").status_code == 401

    # ... and stays a refusal through the next restart.
    hub = _restart(tmp_path, monkeypatch)
    agent = _client(hub, credential.token)
    assert agent_credentials.derive(credential.token) is None
    assert _rpc(agent, "tools/list").status_code == 401
    assert not agent_credentials.in_scope(launch_id, "action:ai_1")
    assert not agent_credentials.created_by(launch_id, f"note:{note['id']}")


def test_a_revoke_before_the_restart_stays_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hub: Hub) -> None:
    _reach(hub, False)
    credential = _launch_credential("launch_r2revoked01", scope=("action:ai_1",))
    assert _rpc(_client(hub, credential.token), "tools/list").status_code == 200
    assert agent_credentials.revoke(credential.principal.identity)
    hub = _restart(tmp_path, monkeypatch)
    assert agent_credentials.derive(credential.token) is None
    assert _rpc(_client(hub, credential.token), "tools/list").status_code == 401


def test_a_hand_launch_survives_a_restart(tmp_path: Path, db, monkeypatch: pytest.MonkeyPatch, hub: Hub) -> None:
    """The real K2 launch: the spawn's credential and the Hand to agent
    grants are the same after the restart."""
    from holdspeak.services import desk_delegation

    _reach(hub, False)
    rig = _rig(tmp_path / "rig", db, monkeypatch)
    result = rig.hand.hand(OWNER, "action", "ai_1")
    assert result["status"] == "launched", result
    launch_id = result["launch_id"]
    token = token_of(_spawn(rig)[0])
    _wait_for(lambda: rig.launches.get(launch_id), "instruction_state", "sent")
    rig.tmux.ended = True

    hub = _restart(tmp_path, monkeypatch)
    agent = _client(hub, token)
    assert agent_credentials.in_scope(launch_id, "action:ai_1")
    assert desk_delegation.live_grant(coder_factory.launch_identity(launch_id))
    is_error, made = _result(_call(agent, "desk.create", {"kind": "decisions", "data": {"title": "Proposed"}}))
    assert is_error is False and made["status"] == "proposed", made


def test_the_store_keeps_only_the_hash_and_drops_expired_rows(tmp_path: Path) -> None:
    database = Database(tmp_path / "creds.db")
    mono, wall = [100.0], [1_000_000.0]
    store = AgentCredentialStore(clock=lambda: mono[0], wall_clock=lambda: wall[0])
    store.attach(database)
    short = store.issue("claude:short", ttl_seconds=5)
    long = store.issue("agent:launch:l1", ttl_seconds=600, palette=frozenset({"desk.get"}),
                       palette_name="X", launch_id="l1", scope_items=("action:a1",))
    store.scope_add("l1", "note:n1")
    store.bind_target("agent:launch:l1", "sess-l1", "%3")
    raw = b"".join(p.read_bytes() for p in tmp_path.glob("creds.db*"))
    assert short.token.encode() not in raw and long.token.encode() not in raw

    # A new process 10 s later, on another monotonic clock.
    wall[0] += 10.0
    fresh = AgentCredentialStore(clock=lambda: 5.0, wall_clock=lambda: wall[0])
    assert fresh.attach(database) == 1
    assert fresh.derive(short.token) is None
    reloaded = fresh.derive_credential(long.token)
    assert reloaded is not None and reloaded.palette == frozenset({"desk.get"})
    assert reloaded.expires_at == pytest.approx(5.0 + 590.0)
    assert fresh.in_scope("l1", "action:a1") and fresh.created_by("l1", "note:n1")
    assert not fresh.created_by("l1", "action:a1"), "the origin item is in scope, not created"
    # The bound targets came back: a kill of the pane revokes.
    assert fresh.revoke_targets(["%3"]) is True
    with database._connection() as conn:
        rows = {r["identity"]: (r["revoked_at"] is not None, r["revocation_reason"])
                for r in conn.execute("SELECT identity, revoked_at, revocation_reason FROM agent_credentials")}
    assert rows == {"claude:short": (True, "expired"), "agent:launch:l1": (True, "revoked")}


# ── 2. No token on argv ──────────────────────────────────────────────


def test_the_spawn_puts_no_token_on_argv_and_the_session_reads_it(tmp_path: Path, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    out = tmp_path / "seen"
    calls: list[list[str]] = []
    modes: list[int] = []

    def runner(argv: list[str]):
        calls.append(list(argv))
        if argv[1] == "new-session":
            env_file = env_file_of(argv)
            modes.append(stat.S_IMODE(env_file.stat().st_mode))
            modes.append(stat.S_IMODE(env_file.parent.stat().st_mode))
            # The session's first process, for real: tmux runs these words.
            done = subprocess.run(argv[argv.index("-s") + 2:], capture_output=True, text=True, timeout=20)
            return type("Done", (), {"returncode": done.returncode, "stdout": "", "stderr": done.stderr})()
        if argv[1] == "list-panes":
            return type("Done", (), {"returncode": 0, "stdout": "%9\n", "stderr": ""})()
        return type("Done", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    command = f'printf %s "$HOLDSPEAK_AGENT_CREDENTIAL" > {out}'
    result = coder_factory.spawn("r2-argv", command=command, launch_id="launch_r2argv0001",
                                 runner=runner, audit=lambda **_: 1)
    assert result["status"] == "spawned", result
    token = out.read_text(encoding="utf-8")
    credential = agent_credentials.derive_credential(token)
    assert credential is not None and credential.launch_id == "launch_r2argv0001"
    assert modes == [0o600, 0o700]
    assert not env_file_of(calls[0]).exists(), "the shell deletes the file after reading it"
    for argv in calls:
        assert not any(token in arg for arg in argv), argv
    assert token not in caplog.text
    coder_factory.revoke_launch("launch_r2argv0001")


def test_a_failed_spawn_leaves_no_credential_file(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def runner(argv: list[str]):
        calls.append(list(argv))
        return type("Done", (), {"returncode": 1, "stdout": "", "stderr": "server exited"})()

    result = coder_factory.spawn("r2-fail", command="true", runner=runner, audit=lambda **_: 1)
    assert result["status"] == "error"
    assert not env_file_of(calls[0]).exists()


@pytest.mark.parametrize("agent", ["claude", "codex"])
def test_no_launch_argv_or_log_carries_the_token(tmp_path, db, monkeypatch, agent, caplog) -> None:
    caplog.set_level(logging.DEBUG)
    if agent == "codex":
        rig, _result_, argv, _command = _codex_launch(tmp_path, db, monkeypatch, "yolo")
    else:
        rig = _rig(tmp_path / "rig", db, monkeypatch)
        rig.service._control_mode = lambda: "yolo"
        result = rig.hand.hand(OWNER, "action", "ai_1")
        assert result["status"] == "launched", result
        argv, _command = _spawn(rig)
        _wait_for(lambda: rig.launches.get(result["launch_id"]), "instruction_state", "sent")
        rig.tmux.ended = True
    token = token_of(argv)
    assert agent_credentials.derive(token) is not None
    for call in rig.tmux.calls:
        assert not any(token in str(arg) for arg in call), call
    assert token not in caplog.text


# ── 3. A hub-minted session credential ends with its session ─────────


def _forward(hub: Hub, monkeypatch: pytest.MonkeyPatch, token: str) -> Any:
    from urllib.parse import urlsplit

    agent = _client(hub, token)

    def send(request, _timeout):
        response = agent.request(request.get_method(), urlsplit(request.full_url).path,
                                 headers=dict(request.header_items()))
        return response.status_code, response.json()

    monkeypatch.setattr(coder_gate, "_send", send)
    return agent


@pytest.mark.parametrize("reason", ["clear", "resume", "logout", "prompt_input_exit", "other"])
def test_a_hub_minted_session_credential_ends_on_every_session_end(hub: Hub, monkeypatch, reason) -> None:
    hub_url = "http://127.0.0.1:8765"
    monkeypatch.delenv("HOLDSPEAK_AGENT_CREDENTIAL", raising=False)
    credential = agent_credentials.issue("claude:r2-s1")
    cache = coder_gate._credential_path(hub_url, "claude:r2-s1")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(credential.token, encoding="utf-8")
    _forward(hub, monkeypatch, credential.token)
    assert coder_gate.run_session_end({"session_id": "r2-s1", "reason": reason}, hub_url=hub_url) is True
    assert agent_credentials.derive(credential.token) is None
    assert not cache.exists()


@pytest.mark.parametrize("reason,revoked", [("clear", False), ("resume", False), ("logout", True)])
def test_the_launch_process_credential_still_stays_over_clear(hub: Hub, monkeypatch, reason, revoked) -> None:
    _reach(hub, False)
    credential = _launch_credential("launch_r2clear0001")
    _forward(hub, monkeypatch, credential.token)
    monkeypatch.setenv("HOLDSPEAK_AGENT_CREDENTIAL", credential.token)
    coder_gate.run_session_end({"session_id": "r2-s2", "reason": reason}, hub_url="http://127.0.0.1:8765")
    assert (agent_credentials.derive(credential.token) is None) is revoked


def test_the_new_tables_use_named_inserts() -> None:
    source = (Path(__file__).resolve().parents[2] / "holdspeak" / "principals.py").read_text(encoding="utf-8")
    for table in ("agent_credentials", "agent_launch_ownership"):
        for chunk in source.split(f"INTO {table}")[1:]:
            assert chunk.lstrip().startswith("("), f"positional INSERT into {table}"


# ── 4. Astra round 1 on #911 ─────────────────────────────────────────


def _refuse(database: Database, table: str, event: str) -> None:
    """A real SQLite refusal of every *event* on *table*."""
    with database._connection() as conn:
        conn.execute(f"CREATE TRIGGER r2_refuse_{table}_{event} BEFORE {event} ON {table} "
                     "BEGIN SELECT RAISE(ABORT, 'disk refused'); END")


def _allow(database: Database, table: str, event: str) -> None:
    with database._connection() as conn:
        conn.execute(f"DROP TRIGGER r2_refuse_{table}_{event}")


def _store(database: Database, mono: list[float] | None = None, wall: list[float] | None = None,
           boot: str = "boot-1") -> AgentCredentialStore:
    mono = mono if mono is not None else [100.0]
    wall = wall if wall is not None else [1_000_000.0]
    store = AgentCredentialStore(clock=lambda: mono[0], wall_clock=lambda: wall[0], boot_id=lambda: boot)
    store.attach(database)
    return store


def test_a_revoke_that_is_not_written_is_not_acknowledged(tmp_path: Path) -> None:
    database = Database(tmp_path / "c.db")
    store = _store(database)
    cred = store.issue("claude:r2-rv")
    _refuse(database, "agent_credentials", "UPDATE")
    assert store.revoke("claude:r2-rv") is False, "a revoke SQLite refused was acknowledged"
    assert store.derive(cred.token) is None, "refused in memory at once"
    _allow(database, "agent_credentials", "UPDATE")
    store.issue("claude:r2-other")  # the next write retries the queued revoke
    assert _store(database).derive(cred.token) is None, "the revoke came back after a restart"


def test_a_rotation_whose_revoke_is_not_written_issues_nothing(tmp_path: Path) -> None:
    from holdspeak.principals import CredentialPersistError

    database = Database(tmp_path / "c.db")
    store = _store(database)
    old = store.issue("claude:r2-rot")
    _refuse(database, "agent_credentials", "UPDATE")
    with pytest.raises(CredentialPersistError):
        store.issue("claude:r2-rot")
    assert store.derive(old.token) is None
    assert [c.principal.identity for c in store.list_credentials()] == []


def test_an_issue_and_its_scope_are_one_write(tmp_path: Path) -> None:
    from holdspeak.principals import CredentialPersistError

    database = Database(tmp_path / "c.db")
    store = _store(database)
    _refuse(database, "agent_launch_ownership", "INSERT")
    with pytest.raises(CredentialPersistError):
        store.issue("agent:launch:l9", launch_id="l9", scope_items=("action:a9",))
    assert store.list_credentials() == [] and not store.in_scope("l9", "action:a9")
    with database._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM agent_credentials").fetchone()[0] == 0


def test_an_ownership_write_that_fails_owns_nothing(tmp_path: Path) -> None:
    from holdspeak.principals import CredentialPersistError

    database = Database(tmp_path / "c.db")
    store = _store(database)
    store.issue("agent:launch:l8", launch_id="l8")
    _refuse(database, "agent_launch_ownership", "INSERT")
    with pytest.raises(CredentialPersistError):
        store.scope_add("l8", "note:n8")
    assert not store.created_by("l8", "note:n8")


def test_a_slow_reload_never_extends_a_credential(tmp_path: Path) -> None:
    database = Database(tmp_path / "c.db")
    mono, wall = [100.0], [1_000_000.0]
    store = _store(database, mono, wall)
    cred = store.issue("claude:r2-slow", ttl_seconds=1)
    mono[0] += 0.5
    wall[0] += 0.5

    class Slow:  # a 1.6 s SQLite lock while the rows are read
        def __init__(self, inner):
            self.inner = inner

        def _connection(self):
            mono[0] += 1.6
            wall[0] += 1.6
            return self.inner._connection()

    fresh = AgentCredentialStore(clock=lambda: mono[0], wall_clock=lambda: wall[0], boot_id=lambda: "boot-1")
    assert fresh.attach(Slow(database)) == 0
    assert fresh.derive(cred.token) is None


def test_a_wall_clock_set_back_never_extends_a_credential(tmp_path: Path) -> None:
    database = Database(tmp_path / "c.db")
    mono, wall = [100.0], [1_000_000.0]
    store = _store(database, mono, wall)
    cred = store.issue("claude:r2-back", ttl_seconds=10)
    mono[0] += 20.0          # the deadline passed ...
    wall[0] -= 100.0         # ... and the wall clock was set back
    fresh = _store(database, mono, wall)
    assert fresh.derive(cred.token) is None


def test_a_rebound_target_leaves_its_old_owner_on_disk(tmp_path: Path) -> None:
    database = Database(tmp_path / "c.db")
    store = _store(database)
    a = store.issue("agent:tmux:a")
    store.issue("agent:tmux:b")
    store.bind_target("agent:tmux:a", "%3")
    store.bind_target("agent:tmux:b", "%3")
    assert store.revoke("agent:tmux:b") is True
    assert store.revoke_targets(["%3"]) is False
    fresh = _store(database)
    assert fresh.revoke_targets(["%3"]) is False, "after a restart %3 was A's again"
    assert fresh.derive(a.token) is not None


def _grant_launch(identity: str, project_id: str) -> None:
    from holdspeak.services.conductor_launch import grant_decision_proposals, grant_project_additions

    assert grant_decision_proposals(OWNER, identity, ttl_seconds=3600) is not None
    assert grant_project_additions(OWNER, identity, project_id, ttl_seconds=3600) is not None


@pytest.mark.parametrize("downtime", ["expired", "revoked_before_grants"])
def test_a_launch_ended_while_the_hub_was_down_ends_its_grants_at_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hub: Hub, downtime: str,
) -> None:
    from holdspeak.services import desk_delegation, project_delegation

    own = hub.client.post("/api/projects", json={"name": "Launch project"}).json()["project"]
    launch_id = f"launch_r2down{downtime[:4]}"
    identity = coder_factory.launch_identity(launch_id)
    credential = _launch_credential(launch_id, project=own["id"])
    _grant_launch(identity, own["id"])
    assert desk_delegation.live_grant(identity)
    with hub.db._connection() as conn:
        if downtime == "expired":  # the deadline passed while the hub was down
            conn.execute("UPDATE agent_credentials SET expires_at = 1.0, mono_expires_at = 1.0 WHERE id = ?",
                         (credential.id,))
        else:  # the hub stopped between the credential's revoke and its grants'
            conn.execute("UPDATE agent_credentials SET revoked_at = 1.0, revocation_reason = 'revoked' "
                         "WHERE id = ?", (credential.id,))

    hub = _restart(tmp_path, monkeypatch)
    assert agent_credentials.derive(credential.token) is None
    assert not desk_delegation.live_grant(identity)
    assert project_delegation.live_projects(identity) == []
    with hub.db._connection() as conn:
        row = conn.execute("SELECT revoked_at, revocation_reason FROM agent_credentials WHERE id = ?",
                           (credential.id,)).fetchone()
    assert row["revoked_at"] is not None


def test_a_failed_credential_file_write_leaves_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(coder_factory, "credential_env_dir", lambda: tmp_path / "agent-env")
    def broken_write(_fd, _data):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(coder_factory.os, "write", broken_write)
    calls: list[list[str]] = []
    result = coder_factory.spawn("r2-nofile", command="true", launch_id="launch_r2nofile01",
                                 runner=lambda argv: calls.append(argv), audit=lambda **_: 1)
    assert result["status"] == "error", result
    assert calls == [], "tmux ran without a credential file"
    assert agent_credentials.launch_credential("agent:launch:launch_r2nofile01") is None
    assert list(coder_factory.credential_env_dir().glob("*")) == []


def test_a_session_that_never_reads_its_file_is_not_spawned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(coder_factory, "START_TIMEOUT_SECONDS", 0.3)
    calls: list[list[str]] = []

    def runner(argv: list[str]):  # tmux answers 0; the session died before its bootstrap
        calls.append(list(argv))
        return type("Done", (), {"returncode": 0, "stdout": "%4\n", "stderr": ""})()

    result = coder_factory.spawn("r2-dead", command="true", launch_id="launch_r2dead0001",
                                 runner=runner, audit=lambda **_: 1)
    assert result["status"] == "error" and "did not start" in result["detail"], result
    assert not env_file_of(calls[0]).exists()
    assert agent_credentials.launch_credential("agent:launch:launch_r2dead0001") is None


def _tmux_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, zshenv: str) -> None:
    import shutil

    if shutil.which("tmux") is None or not Path("/bin/zsh").exists():
        pytest.skip("needs tmux and zsh")
    home = tmp_path / "zhome"
    home.mkdir()
    (home / ".zshenv").write_text(zshenv, encoding="utf-8")
    import tempfile

    # A tmux socket path must stay short (sun_path): not under pytest's tmp.
    sock = Path(tempfile.mkdtemp(prefix="hsr2-", dir="/tmp"))
    monkeypatch.setattr(sys.modules[__name__], "_SOCKETS", [*_SOCKETS, sock])
    monkeypatch.setenv("ZDOTDIR", str(home))
    monkeypatch.setenv("SHELL", "/bin/zsh")
    monkeypatch.setenv("TMUX_TMPDIR", str(sock))
    monkeypatch.delenv("TMUX", raising=False)


_SOCKETS: list[Path] = []


def _kill_tmux() -> None:
    import shutil

    subprocess.run(["tmux", "kill-server"], capture_output=True, timeout=10)
    for sock in _SOCKETS:
        shutil.rmtree(sock, ignore_errors=True)


def _pane(name: str) -> str:
    done = subprocess.run(["tmux", "capture-pane", "-p", "-J", "-S", "-", "-t", name],
                          capture_output=True, text=True, timeout=10)
    return done.stdout


def test_a_traced_shell_never_prints_the_token_on_real_tmux(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(coder_factory, "credential_env_dir", lambda: tmp_path / "agent-env")
    import time

    _tmux_env(tmp_path, monkeypatch, "set -x\nsetopt verbose\n")
    seen = tmp_path / "seen"
    try:
        result = coder_factory.spawn(
            "r2trace", command=f"printenv HOLDSPEAK_AGENT_CREDENTIAL > {seen}; echo r2-started; sleep 30",
            launch_id="launch_r2trace001", audit=lambda **_: 1)
        assert result["status"] == "spawned", result
        deadline = time.monotonic() + 15
        while "r2-started" not in _pane("r2trace") and time.monotonic() < deadline:
            time.sleep(0.1)
        pane = _pane("r2trace")
        token = seen.read_text(encoding="utf-8").strip()
        assert agent_credentials.derive(token) is not None
        assert "r2-started" in pane and "+" in pane, "the rc file did not trace (the fence proves nothing)"
        assert token not in pane, pane
        assert list(coder_factory.credential_env_dir().glob("*")) == []
    finally:
        _kill_tmux()
        coder_factory.revoke_launch("launch_r2trace001")


def test_an_rc_file_that_exits_leaves_no_plaintext_on_real_tmux(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(coder_factory, "credential_env_dir", lambda: tmp_path / "agent-env")
    _tmux_env(tmp_path, monkeypatch, "exit 3\n")
    try:
        coder_factory.spawn("r2exit", command="sleep 30", launch_id="launch_r2exit0001", audit=lambda **_: 1)
        assert list(coder_factory.credential_env_dir().glob("*")) == [], "the plaintext file stayed"
    finally:
        _kill_tmux()
        coder_factory.revoke_launch("launch_r2exit0001")
