"""The agent's lane rig (PHILO-14 C2), lifted verbatim from
`test_philo14_c2_lane_glass.py` (the test diet, 2026-10-11): that file is
parked and its successors read the same seed. A real hub on an isolated HOME;
what a Hand to coder launch leaves behind, written through the product's
producers: an action item on a meeting, a real clone with a launch worktree
and one commit on its branch, the launch on the ledger with its Work attempt
bound to a Claude Code session, the session's hook events, HoldSpeak's
drafted answer and the PR on the launch's follow-through.

Importers: the lane glass files and `tests/integration/test_desk_agents_wire.py`.
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

TOKEN = "p14-c2-lane"
SESSION_ID = "c1a0de00-runbook"
KEY = f"claude:{SESSION_ID}"
QUESTION = "The runbook needs a rollback owner. Jordan or Avery?"


def _git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *argv], check=True, capture_output=True, text=True).stdout.strip()


def _seed(home: Path) -> dict[str, Any]:
    from holdspeak.agent_context import ingest_agent_hook_event
    from holdspeak.agent_context import event_log
    import holdspeak.agent_context as agent_context_pkg
    from holdspeak.db import get_database
    from holdspeak.delivery import DeliveryRegistry
    from holdspeak.delivery.factory_launch import LaunchLedger
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.services import agent_responder

    db = get_database()
    start = (datetime.now() - timedelta(hours=2)).replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id="m-cutover", started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger cutover sync",
        segments=[TranscriptSegment(text="We freeze the ledger on Nov 12.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="We freeze the ledger on Nov 12.", action_items=[{
            "id": "m-cutover-a1", "task": "Write the rollback runbook", "owner": None, "due": None,
            "status": "pending", "review_state": "accepted", "source_timestamp": None,
            "created_at": start.isoformat()}]),
        intel_status="completed"))
    with db._connection() as conn:
        item = str(conn.execute("SELECT id FROM action_items WHERE task=? LIMIT 1", ("Write the rollback runbook",)).fetchone()[0])

    # A clone with origin/main, one launch worktree, one commit on its branch.
    clone = home / "dev" / "payments-ledger"
    clone.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(clone)], check=True)
    _git(clone, "config", "user.email", "lane@example.invalid")
    _git(clone, "config", "user.name", "lane")
    _git(clone, "remote", "add", "origin", "https://github.com/acme/payments-ledger.git")
    (clone / "README.md").write_text("payments ledger\n")
    _git(clone, "add", "README.md")
    _git(clone, "commit", "-q", "-m", "init")
    _git(clone, "update-ref", "refs/remotes/origin/main", "HEAD")
    branch = "hs/write-the-rollback-runbook"
    worktree = home / "dev" / "wt" / "hs-action-runbook"
    worktree.parent.mkdir(parents=True)
    _git(clone, "worktree", "add", "-q", "-b", branch, str(worktree))
    registry = DeliveryRegistry()
    registry.register(str(clone), label="payments-ledger")
    source, wt = registry.register(str(worktree))

    # The session's hook events (spooled; the lane read drains them).
    base = {"session_id": SESSION_ID, "cwd": str(worktree)}
    for payload in (
        {"hook_event_name": "SessionStart", "source": "startup"},
        {"hook_event_name": "UserPromptSubmit", "prompt": "Write the ledger rollback runbook."},
        {"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_use_id": "t1", "tool_input": {"file_path": "ledger/freeze.py"}},
        {"hook_event_name": "PostToolUse", "tool_name": "Grep", "tool_use_id": "t2", "tool_input": {"path": "docs/runbooks"}},
        {"hook_event_name": "PostToolUse", "tool_name": "Read", "tool_use_id": "t3", "tool_input": {"file_path": "docs/runbooks/README.md"}},
        {"hook_event_name": "Stop", "last_assistant_message": "I will draft the runbook from the freeze decision and the Nov 12 rollback window."},
        {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_use_id": "t4", "tool_input": {"file_path": "docs/ledger-rollback.md"}},
        {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": "t5", "tool_input": {"command": "pytest tests/runbooks -q"}},
        "commit",
        {"hook_event_name": "Notification", "message": QUESTION},
    ):
        if payload == "commit":
            # The agent commits after its test run (the worktree's git log
            # keeps whole seconds: a second later, so the rail orders it).
            time.sleep(1.1)
            (worktree / "docs").mkdir()
            (worktree / "docs" / "ledger-rollback.md").write_text("# Ledger rollback\n")
            (worktree / "freeze.py").write_text("FROZEN = True\n")
            _git(worktree, "add", ".")
            _git(worktree, "commit", "-q", "-m", "Draft the ledger rollback runbook")
            continue
        session = ingest_agent_hook_event(
            agent="claude", payload={**base, **payload},
            state_path=agent_context_pkg.AGENT_CONTEXT_FILE, events_spool_dir=event_log.default_spool_dir(),
        )
    # HoldSpeak's drafted answer to this wait (the responder sees it drafted).
    agent_responder.AnswerStore().put_wait(KEY, {
        "wait_id": session.wait_id, "state": "drafted", "verdict": "real",
        "reason": "it names a person", "draft": "Jordan owns it. Avery reviews.", "at": 0,
    })
    attempt = db.work_attempts.create(
        source_id=source.source_id, worktree_id=wt.worktree_id, project="payments-ledger", story_id=f"action-{item}",
        node_id="this-node", session_id=KEY, target_id="tgt_runbook", kind="launch", exact=True,
        claimed_by="launch:claude-default", state="working", origin_ref=f"action:{item}",
    )
    launched = datetime.now(timezone.utc) - timedelta(minutes=20)
    LaunchLedger().record({
        "launch_schema": 1, "launch_id": "launch_c2_runbook", "state": "launched", "node_id": "this-node",
        "profile_id": "claude-default", "gate": "gated", "source_id": source.source_id,
        "worktree_id": wt.worktree_id, "branch": branch, "session": "hs-runbook",
        "origin_ref": {"kind": "action", "id": item}, "attempt_id": attempt.attempt_id,
        "launched_at": launched.isoformat().replace("+00:00", "Z"), "control_mode": "normal",
        "instruction_state": "sent",
        "brief_text": "Write the ledger rollback runbook.\n\nSources: the freeze decision; the Nov 12 window.\nChecks: the runbook names an owner.",
        "follow_through": {
            "pr": {"number": 413, "url": "https://github.com/acme/payments-ledger/pull/413", "state": "open",
                   "review_decision": "", "ci": "pending",
                   "checks": [{"name": f"ci / {n}", "state": "success", "url": ""} for n in range(6)]
                   + [{"name": "ci / e2e", "state": "in_progress", "url": ""}]},
            "pr_state": "pr_open",
        },
    })
    return {"item": item, "worktree": str(worktree)}


PSQL = "psql -h staging-ledger -c 'select count(*) from entries'"


def _http(url: str, method: str, path: str, token: str, body: Any = None) -> tuple[int, Any]:
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        f"{url}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()[:400]


def mint_held_call(url: str, worktree: str, command: str = PSQL, proposal_id: str = "toolu_psql") -> dict:
    """A held call through the real gate route, with the agent's own
    credential (kernel-admitted), in the body the gate hook builds
    (`coder_gate.redact_call`: the hash, the 120-char head, the length of the
    shown command)."""
    from holdspeak.coder_gate import redact_call

    status, issued = _http(url, "POST", "/api/principals/agents", TOKEN, {"identity": KEY})
    assert status == 201, issued
    call = redact_call({"command": command})
    digest = call.sha256
    status, body = _http(url, "POST", "/api/gate/proposals", issued["credential"], {
        "id": proposal_id, "tool": "Bash", "args_sha256": digest, "args_head": call.head,
        "args_len": call.length, "cwd": worktree, "ttl_seconds": 3600,
        "classification": {"scope": "outside", "rule": "path_outside_worktree", "read_rule": "",
                           "push_branch": "", "root": worktree, "proposal_id": proposal_id, "args_sha256": digest},
    })
    assert status == 200 and body["state"] == "held", body
    return body


def _open_lane(page: Any) -> Any:
    """The real entry: Go -> Conductor -> Open on the asking agent.
    PHILO-17 (doors, #1078): the Conductor left the Dock; its doors are its
    desk drawer and Go (both widths). Go fronts an open Conductor, also one
    another view left seated (one hub is one desk), and never toggles it."""
    import re as _re

    page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
    page.locator("[role^=menuitem]").filter(
        has=page.locator(".desk-menu-label", has_text=_re.compile(r"^Conductor$"))).last.click()
    conductor = page.locator(".conductor-window")
    conductor.wait_for(timeout=15000)
    agent = conductor.locator("[data-object-id='launch:launch_c2_runbook']")
    agent.wait_for(timeout=20000)
    # An icon names its lamp in its label (1440); a list row in its State cell (393).
    said = (agent.get_attribute("aria-label") or "") + (agent.text_content() or "")
    assert "ASKS" in said, said
    agent.click()
    conductor.get_by_role("button", name="Open", exact=True).click()
    window = page.locator(".is-lane")
    window.wait_for(timeout=15000)
    page.locator("[data-testid='lane-rail']").wait_for(timeout=15000)
    return window
