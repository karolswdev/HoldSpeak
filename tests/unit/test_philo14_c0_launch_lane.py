"""PHILO-14 C0: the launch lane backend.

The event log per agent session (append, bound, redaction, Stop's message
kept), the worktree facts (a real temporary git repository), and the route
``GET /api/agent/launches/{id}/lane`` (FastAPI test client).
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
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


def _ingest(tmp_path, db, payload, agent="claude"):
    base = {"session_id": "s1", "cwd": str(tmp_path), "transcript_path": ""}
    return ingest_agent_hook_event(
        agent=agent, payload={**base, **payload},
        state_path=tmp_path / "agent_sessions.json", events_db_path=db.db_path,
    )


def _events(db, key="claude:s1"):
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

    rows = _events(db)
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

    rows = _events(db)
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
    assert len(_events(db)) == 1


def test_the_log_keeps_the_newest_rows_per_session(db) -> None:
    for n in range(8):
        assert event_log.append_event("claude:s1", f"t{n}", {"event": f"E{n}"}, db_path=db.db_path, keep=5)
    event_log.append_event("claude:other", "t", {"event": "X"}, db_path=db.db_path, keep=5)
    rows = _events(db)
    assert [r["event"] for r in rows] == ["E3", "E4", "E5", "E6", "E7"]
    assert len(_events(db, "claude:other")) == 1
    paged = []
    with db._connection() as conn:
        paged = event_log.list_events(conn, "claude:s1", after=rows[1]["id"], limit=2)
    assert [r["event"] for r in paged] == ["E5", "E6"]
    assert event_log.EVENT_LOG_KEEP == 2000


def test_no_database_file_means_no_write_and_no_file(tmp_path) -> None:
    missing = tmp_path / "nothing.db"
    assert event_log.append_event("claude:s1", "t", {"event": "Stop"}, db_path=missing) is False
    assert not missing.exists()


def test_a_test_registry_does_not_write_the_hubs_log(tmp_path, monkeypatch, db) -> None:
    monkeypatch.setattr(event_log, "default_db_path", lambda: db.db_path)
    ingest_agent_hook_event(
        agent="claude",
        payload={"session_id": "s1", "cwd": str(tmp_path), "hook_event_name": "SessionStart"},
        state_path=tmp_path / "s.json",
    )
    assert _events(db) == []


def test_the_default_path_is_the_hubs_database() -> None:
    from holdspeak.db.core import DEFAULT_DB_PATH

    assert event_log.default_db_path() == DEFAULT_DB_PATH


def test_the_claude_rider_reports_file_changes_after_each_tool() -> None:
    matcher = claude_hook_template()["hooks"]["PostToolUse"][0]["matcher"]
    assert set(matcher.split("|")) >= {"Bash", "Edit", "Write", "MultiEdit", "NotebookEdit"}


def test_codex_apply_patch_head_names_the_files() -> None:
    patch = "*** Begin Patch\n*** Update File: src/a.py\n@@\n-x\n+y\n*** Add File: src/b.py\n+z\n*** End Patch"
    assert event_log.tool_head("apply_patch", {"command": patch}) == "src/a.py, src/b.py"


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


def test_the_lane_route_returns_the_whole_lane(tmp_path, db, worktree, monkeypatch) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.db as db_pkg
    from holdspeak.services import agent_responder
    from holdspeak.web.routes.agent_hand import build_agent_hand_router

    registry_file = tmp_path / "agent_sessions.json"
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", registry_file)
    monkeypatch.setattr(db_pkg, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", tmp_path / "agent_answers.json")

    attempt = db.work_attempts.create(
        source_id="src_1", worktree_id="wt_1", project="desk", story_id="action-ai_1",
        kind="launch", exact=True, session_id="claude:s1", state="starting",
    )
    record = {
        "launch_schema": 1, "launch_id": "launch_abc", "state": "launched", "profile_id": "claude-default",
        "source_id": "src_1", "worktree_id": "wt_1", "branch": "hs/fix", "session": "hs-fix",
        "origin_ref": {"kind": "action", "id": "ai_1"}, "attempt_id": attempt.attempt_id,
        "launched_at": "2026-10-07T09:00:00Z", "control_mode": "yolo", "gate": "gated",
        "instruction_state": "sent", "brief_text": "Fix the login timeout.",
        "follow_through": {
            "pr": {"url": "https://github.com/a/b/pull/7", "number": 7, "state": "open",
                   "review_decision": "", "ci": "failing",
                   "checks": [{"name": "CI / test", "state": "failure", "url": "https://ci/1"}]},
            "pr_state": "pr_open",
        },
    }
    ctx = SimpleNamespace(agent_hand_reads=_reads(tmp_path, str(worktree), record))

    base = {"session_id": "s1", "cwd": str(worktree)}
    for payload in (
        {"hook_event_name": "SessionStart", "source": "startup"},
        {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_input": {"file_path": str(worktree / "a.py")}},
        {"hook_event_name": "Stop", "last_assistant_message": "Done. Should I open the PR now?"},
    ):
        session = ingest_agent_hook_event(
            agent="claude", payload={**base, **payload}, state_path=registry_file, events_db_path=db.db_path,
        )
    assert session.question, "the Stop question makes a wait"
    agent_responder.AnswerStore().put_wait("claude:s1", {
        "wait_id": session.wait_id, "state": "drafted", "verdict": "routine",
        "reason": "the brief says to open a PR", "draft": "Yes, open it.", "at": 0,
    })
    db.gate.propose(
        proposal_id="toolu_1", session_key="claude:s1", agent="claude", tool="Bash",
        args_sha256="0" * 64, args_head='{"command": "git push origin hs/fix"}',
        cwd=str(worktree), ttl_seconds=240,
    )
    db.steering.record(session_key="hs-fix", agent="claude", text="Fix the login timeout.", outcome="delivered")

    app = FastAPI()
    app.include_router(build_agent_hand_router(ctx))
    client = TestClient(app)

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

