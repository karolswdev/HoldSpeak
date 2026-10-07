"""PHILO-14 C2: the agent's lane window on a real hub (ratified board A-4 with
C-4's station track).

A real hub on an isolated HOME. What a Hand to agent launch leaves behind,
written through the product's producers as the Conductor F2 seed does
(`docs/internal/philo/phase-14/canvas/harness/seed_f2.py`): an action item on
a meeting, a real clone with a launch worktree and one commit on its branch
(a Delivery Source), the launch on the ledger with its Work attempt bound to a
Claude Code session, the session's hook events (spooled, drained by the lane
read), a held gate proposal, HoldSpeak's drafted answer, and the PR on the
launch's follow-through. No agent runs; nothing leaves the machine.

The Needs you row's Open opens the lane (not the session window). The test
reads the lane's sections, toggles Raw, and shoots the window at 1440 and 393
to `.tmp/evidence-shots/p14-c2/`.
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the lane glass needs Playwright")

TOKEN = "p14-c2-lane"
SESSION_ID = "c1a0de00-runbook"
KEY = f"claude:{SESSION_ID}"
QUESTION = "The runbook needs a rollback owner. Jordan or Avery?"
SHOTS = evidence_dir("p14-c2")


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
    credential (kernel-admitted, as the gate hook sends it)."""
    import hashlib

    status, issued = _http(url, "POST", "/api/principals/agents", TOKEN, {"identity": KEY})
    assert status == 201, issued
    args = json.dumps({"command": command}, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(args.encode()).hexdigest()
    status, body = _http(url, "POST", "/api/gate/proposals", issued["credential"], {
        "id": proposal_id, "tool": "Bash", "args_sha256": digest, "args_head": args[:120],
        "cwd": worktree, "ttl_seconds": 3600,
        "classification": {"scope": "outside", "rule": "path_outside_worktree", "read_rule": "",
                           "push_branch": "", "root": worktree, "proposal_id": proposal_id, "args_sha256": digest},
    })
    assert status == 200 and body["state"] == "held", body
    return body


def _open_lane(page: Any) -> Any:
    open_verb = page.locator("[data-testid='arrival-coder-open']").first
    open_verb.wait_for(timeout=20000)
    open_verb.click()
    window = page.locator(".is-lane")
    window.wait_for(timeout=15000)
    page.locator("[data-testid='lane-rail']").wait_for(timeout=15000)
    return window


@pytest.mark.timeout(240)
def test_the_agents_lane_window_at_1440_and_393(tmp_path: Path, monkeypatch) -> None:
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    import holdspeak.delivery.registry as delivery_registry
    from holdspeak.agent_context import event_log
    from holdspeak.services import agent_responder

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(delivery_registry, "DEFAULT_REGISTRY_PATH", state / "delivery_sources.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
    monkeypatch.setattr(agent_responder, "DEFAULT_ANSWERS_PATH", state / "agent_answers.json")
    monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        seed = _seed(tmp_path / "home")
        mint_held_call(url, seed["worktree"])
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width, height in ((1440, 900), (393, 852)):
                page = browser.new_page(viewport={"width": width, "height": height})
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                page.reload(wait_until="load")
                _normal_chair(page)
                _settle(page)
                window = _open_lane(page)
                # The session window is not the face of a launch's session.
                assert page.locator(".is-session").count() == 0

                assert "Claude Code: Write the rollback runbook" in (window.text_content() or "")
                track = page.locator("[data-testid='lane-track']")
                track_text = track.text_content() or ""
                for word in ("BRIEF", "WORK", "COMMIT", "PR", "HELD", "ASKS", "MERGE"):
                    assert word in track_text, track_text
                assert "#413" in track_text and "1 call" in track_text and "now" in track_text
                assert page.locator("[data-testid='lane-ask'] .ask-well-question").text_content() == QUESTION
                assert "Jordan owns it. Avery reviews." in (page.locator("[data-testid='lane-ask'] .ask-well-draft").text_content() or "")
                rail = page.locator("[data-testid='lane-rail']").text_content() or ""
                for word in ("BRIEF", "READ", "SAYS", "WRITE", "RUN", "COMMIT", "PR", "HELD", "ASKS", "MERGE"):
                    assert word in rail, rail
                assert "Draft the ledger rollback runbook" in rail
                assert "psql -h staging-ledger" in rail
                assert "Your press in GitHub" in rail
                pr = page.locator("[data-testid='lane-pr']").text_content() or ""
                assert "#413" in pr and "CHECKS 6 OF 7" in pr and "1 RUNNING" in pr
                files = page.locator("[data-testid='lane-files']").text_content() or ""
                assert "docs/ledger-rollback.md" in files and "freeze.py" in files
                assert page.get_by_text("GITHUB.COM").first.is_visible()
                assert page.locator("[data-testid='lane-open-pr']").is_visible()
                assert page.locator("[data-testid='lane-stop']").is_visible()

                page.wait_for_timeout(400)
                page.screenshot(path=str(SHOTS / f"C2-lane-{width}.png"))
                if width == 393:
                    # C2b: every footer verb is whole in the frame, 44 px tall,
                    # and is the element at its own centre; no side scroll.
                    verbs = page.locator(".is-lane .surface-footer-verbs button").evaluate_all(
                        """(els) => els.map((el) => {
                            const r = el.getBoundingClientRect();
                            const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                            return {name: el.textContent.trim(), left: r.left, right: r.right, top: r.top,
                                    bottom: r.bottom, height: r.height, hit: !!hit && el.contains(hit)};
                        })""")
                    names = [v["name"] for v in verbs]
                    assert any("Stop" in n for n in names) and any("Open PR" in n for n in names), names
                    for v in verbs:
                        assert v["left"] >= 0 and v["right"] <= 393 and v["top"] >= 0 and v["bottom"] <= 852, v
                        assert v["height"] >= 44, v
                        assert v["hit"], v
                    assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")

                # Raw: the terminal pane in place of the lane, and back.
                page.locator("[data-testid='lane-raw']").click()
                page.locator("[data-testid='lane-raw-pane']").wait_for(timeout=5000)
                assert page.locator("[data-testid='lane-rail']").count() == 0
                if width == 1440:
                    page.screenshot(path=str(SHOTS / f"C2-lane-raw-{width}.png"))
                page.locator("[data-testid='lane-raw']").click()
                page.locator("[data-testid='lane-rail']").wait_for(timeout=5000)
                if width == 393:
                    # Approve the held call from the rail: the real gate route decides it.
                    held = page.locator(".lane-rail-entry").filter(has_text="psql -h staging-ledger")
                    with page.expect_response(lambda r: "/toolu_psql/decide" in r.url) as got:
                        held.locator("[data-testid='lane-approve']").click()
                    assert got.value.status == 200, got.value.text()
                    status, stored = _http(url, "GET", "/api/gate/proposals/toolu_psql", TOKEN)
                    assert stored["state"] == "approved", stored
                    held.locator("[data-testid='lane-approve']").wait_for(state="detached", timeout=10000)
                _assert_clean(page, errors)
                page.close()
            browser.close()
    finally:
        server.stop()
