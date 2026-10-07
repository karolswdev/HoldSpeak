"""PHILO-14 C0: the launch lane backend.

The event log per agent session (append, bound, redaction, Stop's message
kept), the worktree facts (a real temporary git repository), and the route
``GET /api/agent/launches/{id}/lane`` (FastAPI test client).
"""
from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from holdspeak.agent_context import event_log, ingest_agent_hook_event
from holdspeak.agent_context.hooks import claude_hook_template
from holdspeak.db import Database
from holdspeak.services import launch_lane as lane_mod

SECRET = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2"


@pytest.fixture
def db(tmp_path) -> Database:
    database = Database(tmp_path / "hub.db")
    yield database
    database.close()


def _spool(tmp_path) -> Path:
    return tmp_path / "agent-events"


def _ingest(tmp_path, db, payload, agent="claude"):
    base = {"session_id": "s1", "cwd": str(tmp_path), "transcript_path": ""}
    return ingest_agent_hook_event(
        agent=agent, payload={**base, **payload},
        state_path=tmp_path / "agent_sessions.json", events_spool_dir=_spool(tmp_path),
    )


def _events(db, key="claude:s1", spool=None):
    if spool is not None:
        event_log.drain_spool(db._connection, spool_dir=spool)
    with db._connection() as conn:
        return event_log.list_events(conn, key)


# ── the event log ─────────────────────────────────────────────────────


def test_every_event_is_appended_with_a_redacted_head(tmp_path, db) -> None:
    _ingest(tmp_path, db, {"hook_event_name": "SessionStart", "source": "startup"})
    _ingest(tmp_path, db, {
        "hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": "toolu_1",
        "tool_input": {"command": f"git push https://x:{SECRET}@github.com/a/b " + "y" * 300},
    })
    _ingest(tmp_path, db, {
        "hook_event_name": "PostToolUse", "tool_name": "MultiEdit",
        "tool_input": {"file_path": "/repo/src/app.py", "edits": [{"old_string": "a", "new_string": "b"}]},
    })
    _ingest(tmp_path, db, {
        "hook_event_name": "Notification", "notification_type": "permission_prompt",
        "message": "Claude needs your permission to use Bash",
    })
    _ingest(tmp_path, db, {"hook_event_name": "SessionEnd", "reason": "exit"})

    rows = _events(db, spool=_spool(tmp_path))
    assert [r["event"] for r in rows] == [
        "SessionStart", "PostToolUse", "PostToolUse", "Notification", "SessionEnd",
    ]
    bash = rows[1]
    assert bash["tool"] == "Bash"
    assert SECRET not in bash["head"] and "[redacted]" in bash["head"]
    assert len(bash["head"]) <= event_log.COMMAND_HEAD_CHARS
    assert bash["detail"] == {"tool_use_id": "toolu_1"}
    assert rows[2]["head"] == "/repo/src/app.py"
    assert rows[3]["text"] == "Claude needs your permission to use Bash"
    assert rows[3]["detail"] == {"notification_type": "permission_prompt"}
    assert rows[0]["detail"] == {"source": "startup"}
    assert rows[4]["detail"] == {"reason": "exit"}
    # The overwritten record stays as it was: the last event only.
    state = json.loads((tmp_path / "agent_sessions.json").read_text())
    assert state["sessions"]["claude:s1"]["hook_event_name"] == "SessionEnd"


def test_stop_message_is_kept_whole_redacted_and_capped(tmp_path, db) -> None:
    message = "I changed the timeout. Should I also update the docs?\n" + ("word " * 600)
    _ingest(tmp_path, db, {"hook_event_name": "Stop", "last_assistant_message": message})
    _ingest(tmp_path, db, {"hook_event_name": "UserPromptSubmit", "prompt": "yes"})
    huge = f"token={SECRET} " + ("x" * 20_000)
    _ingest(tmp_path, db, {"hook_event_name": "Stop", "last_assistant_message": huge})

    rows = _events(db, spool=_spool(tmp_path))
    assert rows[0]["text"] == message.strip(), "a message under 8 KB is kept whole"
    assert rows[1]["text"] == "yes"
    assert SECRET not in rows[2]["text"] and rows[2]["text"].startswith("[redacted]")
    assert len(rows[2]["text"].encode("utf-8")) <= event_log.TEXT_MAX_BYTES


def test_a_duplicate_event_from_a_second_hook_source_is_appended_once(tmp_path, db) -> None:
    payload = {
        "hook_event_name": "PostToolUse", "tool_name": "Edit", "tool_use_id": "toolu_9",
        "tool_input": {"file_path": "/repo/a.py"},
    }
    _ingest(tmp_path, db, payload)
    _ingest(tmp_path, db, payload)
    assert len(_events(db, spool=_spool(tmp_path))) == 1


def test_the_log_keeps_the_newest_rows_per_session(tmp_path, db) -> None:
    spool = _spool(tmp_path)
    for n in range(8):
        assert event_log.spool_event("claude:s1", f"t{n}", {"event": f"E{n}"}, spool_dir=spool)
    event_log.spool_event("claude:other", "t", {"event": "X"}, spool_dir=spool)
    assert event_log.drain_spool(db._connection, spool_dir=spool, keep=5) == 9
    rows = _events(db)
    assert [r["event"] for r in rows] == ["E3", "E4", "E5", "E6", "E7"]
    assert len(_events(db, "claude:other")) == 1
    with db._connection() as conn:
        paged = event_log.list_events(conn, "claude:s1", after=rows[1]["id"], limit=2)
    assert [r["event"] for r in paged] == ["E5", "E6"]
    assert event_log.EVENT_LOG_KEEP == 2000
    assert [n for n in os.listdir(spool) if n.endswith(".json")] == [], "a drained file goes"


def test_a_redrain_of_the_same_file_adds_no_twin(tmp_path, db) -> None:
    spool = _spool(tmp_path)
    event_log.spool_event("claude:s1", "t", {"event": "Stop"}, spool_dir=spool)
    [name] = [n for n in os.listdir(spool) if n.endswith(".json")]
    kept = (spool / name).read_bytes()
    event_log.drain_spool(db._connection, spool_dir=spool)
    (spool / name).write_bytes(kept)  # a drain that died after its commit
    event_log.drain_spool(db._connection, spool_dir=spool)
    assert len(_events(db)) == 1


def test_the_spool_files_are_private(tmp_path) -> None:
    spool = _spool(tmp_path)
    event_log.spool_event("claude:s1", "t", {"event": "Stop"}, spool_dir=spool)
    [name] = [n for n in os.listdir(spool) if n.endswith(".json")]
    assert stat.S_IMODE(os.stat(spool).st_mode) == 0o700
    assert stat.S_IMODE(os.stat(spool / name).st_mode) == 0o600


def test_a_test_registry_does_not_write_the_hubs_spool(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: _spool(tmp_path))
    ingest_agent_hook_event(
        agent="claude",
        payload={"session_id": "s1", "cwd": str(tmp_path), "hook_event_name": "SessionStart"},
        state_path=tmp_path / "s.json",
    )
    assert not _spool(tmp_path).exists()


def test_the_hook_does_not_wait_on_a_busy_hub_writer(tmp_path, db) -> None:
    """Astra R1 P1: a real writer held BEGIN IMMEDIATE and the hook took
    2.2 s and lost the event. The hook now spools: no database, no wait."""
    writer = sqlite3.connect(str(db.db_path), timeout=0)
    writer.execute("BEGIN IMMEDIATE")
    try:
        started = time.perf_counter()
        _ingest(tmp_path, db, {"hook_event_name": "Stop", "last_assistant_message": "Done?"})
        elapsed = time.perf_counter() - started
    finally:
        writer.rollback()
        writer.close()
    assert elapsed < 0.2, f"the hook waited {elapsed:.3f} s"
    assert [r["text"] for r in _events(db, spool=_spool(tmp_path))] == ["Done?"]


def test_the_real_hook_command_spools_and_never_touches_the_database(tmp_path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    payload = {"session_id": "s1", "cwd": str(tmp_path), "hook_event_name": "Stop",
               "last_assistant_message": "Done?"}
    done = subprocess.run(
        [sys.executable, "-m", "holdspeak.cli_entry", "agent-hook", "ingest", "--agent", "claude"],
        input=json.dumps(payload), capture_output=True, text=True, timeout=60,
        env={**os.environ, "HOME": str(home)},
    )
    assert done.returncode == 0, done.stderr
    spool = home / ".holdspeak" / "agent-events"
    assert len([n for n in os.listdir(spool) if n.endswith(".json")]) == 1
    assert not (home / ".local" / "share" / "holdspeak" / "holdspeak.db").exists()


def test_events_spooled_before_the_table_exists_arrive_after_reconcile(tmp_path) -> None:
    """Astra R1 P1: an old schema lost the event. Now the files wait."""
    path = tmp_path / "old.db"
    sqlite3.connect(str(path)).close()   # a database without the table
    spool = _spool(tmp_path)
    event_log.spool_event("claude:s1", "t", {"event": "Stop", "text": "kept"}, spool_dir=spool)

    @contextlib.contextmanager
    def raw():
        conn = sqlite3.connect(str(path))
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    assert event_log.drain_spool(raw, spool_dir=spool) == 0
    assert len([n for n in os.listdir(spool) if n.endswith(".json")]) == 1, "the file waits"
    database = Database(path)   # the hub opens: the schema reconciles
    try:
        assert [r["text"] for r in _events(database, spool=spool)] == ["kept"]
    finally:
        database.close()


def test_the_claude_rider_reports_file_changes_after_each_tool() -> None:
    matcher = claude_hook_template()["hooks"]["PostToolUse"][0]["matcher"]
    assert set(matcher.split("|")) >= {"Bash", "Edit", "Write", "MultiEdit", "NotebookEdit"}


def test_codex_apply_patch_head_names_the_files() -> None:
    patch = "*** Begin Patch\n*** Update File: src/a.py\n@@\n-x\n+y\n*** Add File: src/b.py\n+z\n*** End Patch"
    assert event_log.tool_head("apply_patch", {"command": patch}) == "src/a.py, src/b.py"
    # An unknown shape claims no file (the Codex payload is not verified).
    assert event_log.tool_head("apply_patch", "raw text") is None
    assert event_log.tool_head("apply_patch", {"command": "echo hi"}) is None


# ── the worktree facts ────────────────────────────────────────────────


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout


@pytest.fixture
def worktree(tmp_path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "README.md").write_text("hi\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "base")
    wt = tmp_path / "hs-fix"
    _git(repo, "worktree", "add", "-q", str(wt), "-b", "hs/fix")
    (wt / "a.py").write_text("x = 1\n")
    _git(wt, "add", ".")
    _git(wt, "commit", "-qm", "Add a")
    (wt / "README.md").write_text("hello\n")
    _git(wt, "commit", "-qam", "Change readme")
    (wt / "scratch.txt").write_text("u\n")
    (wt / "a.py").write_text("x = 2\n")
    lane_mod.clear_facts_cache()
    return wt


def test_worktree_facts_read_commits_files_and_counts(worktree) -> None:
    facts = lane_mod.worktree_facts("launch_1", str(worktree))
    assert facts["base"] == "main"
    assert facts["branch"] == "hs/fix"
    assert [c["subject"] for c in facts["commits"]] == ["Change readme", "Add a"]
    assert all(isinstance(c["at"], int) and c["sha"] for c in facts["commits"])
    assert sorted((f["status"], f["path"]) for f in facts["files"]) == [("A", "a.py"), ("M", "README.md")]
    assert facts["uncommitted"] == {"staged": 0, "modified": 1, "untracked": 1}


def test_worktree_facts_are_cached_for_five_seconds(worktree) -> None:
    calls: list[list[str]] = []

    def runner(argv):
        calls.append(argv)
        return subprocess.run(argv, capture_output=True, text=True, timeout=5)

    now = [100.0]
    lane_mod.worktree_facts("launch_2", str(worktree), runner=runner, clock=lambda: now[0])
    first = len(calls)
    assert first > 0
    now[0] += 4.0
    lane_mod.worktree_facts("launch_2", str(worktree), runner=runner, clock=lambda: now[0])
    assert len(calls) == first, "a read within the TTL runs no git"
    now[0] += 2.0
    lane_mod.worktree_facts("launch_2", str(worktree), runner=runner, clock=lambda: now[0])
    assert len(calls) == 2 * first
    assert all(argv[:3] == ["git", "-C", str(worktree.resolve())] for argv in calls)


def test_worktree_facts_never_read_outside_the_worktree(worktree, tmp_path) -> None:
    inside = worktree / "sub"
    inside.mkdir()
    facts = lane_mod.worktree_facts("l3", str(inside))
    assert facts["not_read"] == "the worktree folder is not the top of a git worktree"
    assert "commits" not in facts
    assert lane_mod.worktree_facts("l4", str(tmp_path / "gone"))["not_read"] == "the worktree is gone"
    assert lane_mod.worktree_facts("l5", "")["not_read"] == "the launch has no worktree"
    plain = tmp_path / "plain"
    plain.mkdir()
    assert lane_mod.worktree_facts("l6", str(plain))["not_read"] == "the worktree is not a git worktree"


# ── the route ─────────────────────────────────────────────────────────


def _reads(tmp_path, worktree_path: str, record: dict):
    from holdspeak.delivery.factory_launch import LaunchLedger

    ledger = LaunchLedger(tmp_path / "agent_launches.json")
    ledger.record(record)
    source = SimpleNamespace(
        source_id="src_1", worktrees=[SimpleNamespace(worktree_id="wt_1", path=worktree_path, branch="hs/fix")],
    )
    return SimpleNamespace(
        launcher=lambda: SimpleNamespace(_ledger=ledger),
        registry=lambda: SimpleNamespace(get=lambda sid: source if sid == "src_1" else None),
    )


def _lane(tmp_path, db, worktree, monkeypatch, *, secret: str = ""):
    """The lane route over real stores; ``secret`` is planted in every text
    field the lane serves."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.db as db_pkg
    from holdspeak.services import agent_responder
    from holdspeak.web.routes.agent_hand import build_agent_hand_router

    s = f" {secret}" if secret else ""
    registry_file = tmp_path / "agent_sessions.json"
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", registry_file)
    monkeypatch.setattr(db_pkg, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", tmp_path / "agent_answers.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: _spool(tmp_path))
    if secret:
        (worktree / f"leak-{secret}.txt").write_text("x\n")
        _git(worktree, "add", ".")
        _git(worktree, "commit", "-qm", f"Add key{s}")

    attempt = db.work_attempts.create(
        source_id="src_1", worktree_id="wt_1", project="desk", story_id="action-ai_1",
        kind="launch", exact=True, session_id="claude:s1", state="starting",
    )
    record = {
        "launch_schema": 1, "launch_id": "launch_abc", "state": "launched", "profile_id": "claude-default",
        "source_id": "src_1", "worktree_id": "wt_1", "branch": "hs/fix", "session": "hs-fix",
        "origin_ref": {"kind": "action", "id": "ai_1"}, "attempt_id": attempt.attempt_id,
        "launched_at": "2026-10-07T09:00:00Z", "control_mode": "yolo", "gate": "gated",
        "instruction_state": "sent", "brief_text": f"Fix the login timeout.{s}",
        "follow_through": {
            "pr": {"url": "https://github.com/a/b/pull/7", "number": 7, "state": "open",
                   "review_decision": "", "ci": "failing",
                   "checks": [{"name": f"CI / test{s}", "state": "failure", "url": f"https://ci/1?{s.strip()}"}]},
            "pr_state": "pr_open",
        },
    }
    ctx = SimpleNamespace(agent_hand_reads=_reads(tmp_path, str(worktree), record))

    base = {"session_id": "s1", "cwd": str(worktree)}
    for payload in (
        {"hook_event_name": "SessionStart", "source": f"startup{s}"},
        {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_use_id": f"toolu_w{s}",
         "tool_input": {"file_path": str(worktree / "a.py")}},
        {"hook_event_name": "Stop", "last_assistant_message": "Done. Should I open the PR now?"},
    ):
        session = ingest_agent_hook_event(
            agent="claude", payload={**base, **payload}, state_path=registry_file,
            events_spool_dir=_spool(tmp_path),
        )
    assert session.question, "the Stop question makes a wait"
    agent_responder.AnswerStore().put_wait("claude:s1", {
        "wait_id": session.wait_id, "state": "drafted", "verdict": "routine",
        "reason": f"the brief says to open a PR{s}", "draft": f"Yes, open it.{s}", "at": 0,
    })
    # The raw JSON as the head: a caller that did not redact (the hub redacts too).
    db.gate.propose(
        proposal_id="toolu_1", session_key="claude:s1", agent="claude", tool="Bash",
        args_sha256="0" * 64, args_head=json.dumps({"command": f"git push origin hs/fix{s}"}),
        cwd=str(worktree), ttl_seconds=240,
    )
    db.steering.record(
        session_key="hs-fix", agent="claude", text=f"Fix the login timeout.{s}", outcome="delivered",
        detail=f"sent{s}" if secret else None,
    )
    app = FastAPI()
    app.include_router(build_agent_hand_router(ctx))
    return TestClient(app)


def test_the_lane_route_returns_the_whole_lane(tmp_path, db, worktree, monkeypatch) -> None:
    client = _lane(tmp_path, db, worktree, monkeypatch)
    assert client.get("/api/agent/launches/nope/lane").status_code == 404
    response = client.get("/api/agent/launches/launch_abc/lane")
    assert response.status_code == 200, response.text
    body = response.json()

    launch = body["launch"]
    assert launch["brief_text"] == "Fix the login timeout."
    assert launch["branch"] == "hs/fix" and launch["launched_at"] == "2026-10-07T09:00:00Z"
    assert launch["control_mode"] == "yolo" and launch["agent"] == "claude"
    assert launch["origin_ref"] == {"kind": "action", "id": "ai_1"}
    assert launch["session_key"] == "claude:s1"
    assert launch["worktree_path"].endswith("hs-fix")
    pr = body["follow_through"]["pr"]
    assert pr["ci"] == "failing" and pr["checks"][0]["name"] == "CI / test"
    wait = body["wait"]
    assert wait["kind"] == "TO ANSWER" and wait["question"] == "Done. Should I open the PR now?"
    assert wait["draft"] == {"verdict": "routine", "reason": "the brief says to open a PR", "text": "Yes, open it."}
    assert [e["event"] for e in body["events"]] == ["SessionStart", "PostToolUse", "Stop"]
    assert body["events"][2]["text"] == "Done. Should I open the PR now?"
    assert [a["text_head"] for a in body["answers"]] == ["Fix the login timeout."]
    assert [c["subject"] for c in body["worktree"]["commits"]] == ["Change readme", "Add a"]
    assert {f["path"] for f in body["worktree"]["files"]} == {"a.py", "README.md"}
    assert body["attempt_events"] and body["usage"] is None
    assert [(g["id"], g["state"]) for g in body["gated"]] == [("toolu_1", "held")]

    paged = client.get("/api/agent/launches/launch_abc/lane?after=%d&limit=1" % body["events"][0]["id"]).json()
    assert [e["event"] for e in paged["events"]] == ["PostToolUse"]
    assert paged["events_next_after"] == paged["events"][0]["id"]



def test_no_secret_reaches_the_lane(tmp_path, db, worktree, monkeypatch) -> None:
    """Astra R1 P1: a secret in each served field (gate head, answer head and
    detail, draft, check name and link, event detail, commit subject, file
    name, brief) never reaches the route."""
    from holdspeak.memory.defense import redact

    assert redact(SECRET) != SECRET, "the planted value is a secret shape"
    client = _lane(tmp_path, db, worktree, monkeypatch, secret=SECRET)
    response = client.get("/api/agent/launches/launch_abc/lane")
    assert response.status_code == 200, response.text
    assert SECRET not in response.text
    assert SECRET[:12] not in response.text, "no cut head of the secret either"
    body = response.json()
    assert "[redacted]" in body["gated"][0]["args_head"]
    assert "[redacted]" in body["answers"][0]["text_head"]
    assert "[redacted]" in body["wait"]["draft"]["text"]
    assert any("[redacted]" in f["path"] for f in body["worktree"]["files"])


def test_the_stored_heads_are_redacted_before_the_cut() -> None:
    from holdspeak.coder_gate import redact_args

    command = {"command": "x" * 90 + f" {SECRET} " + "y" * 200}
    digest, head = redact_args(command)
    assert SECRET[:8] not in head and len(head) <= 120
    import hashlib

    canonical = json.dumps(command, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    assert digest == hashlib.sha256(canonical.encode()).hexdigest(), "the hash is over the real call"


def test_steering_keeps_the_real_hash_and_a_redacted_head(db) -> None:
    import hashlib

    text = "a" * 100 + f" {SECRET}"
    db.steering.record(session_key="k", text=text, outcome="delivered", detail=f"why {SECRET}")
    [row] = db.steering.list(session_key="k")
    assert row.text_sha256 == hashlib.sha256(text.encode()).hexdigest()
    assert SECRET[:8] not in row.text_head and SECRET not in (row.detail or "")


def test_a_failed_event_read_is_marked_not_empty(tmp_path, db, worktree, monkeypatch) -> None:
    """Astra R1 P2: a failed read is never served as an empty list."""
    client = _lane(tmp_path, db, worktree, monkeypatch)
    with db._connection() as conn:
        conn.execute("DROP TABLE agent_session_events")
    body = client.get("/api/agent/launches/launch_abc/lane").json()
    assert set(body["events"]) == {"not_read"} and "events" in body["events"]["not_read"]
    assert body["events_next_after"] is None
    assert isinstance(body["gated"], list) and isinstance(body["answers"], list)


def test_a_failed_session_read_is_marked(tmp_path, db, worktree, monkeypatch) -> None:
    import holdspeak.agent_context as agent_context_pkg

    client = _lane(tmp_path, db, worktree, monkeypatch)

    def broken():
        raise OSError("registry unreadable")

    monkeypatch.setattr(agent_context_pkg, "list_agent_sessions", broken)
    body = client.get("/api/agent/launches/launch_abc/lane").json()
    assert "not_read" in body["session"] and "not_read" in body["wait"]
