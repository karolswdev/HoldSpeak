"""The Agents app in a real browser: long questions wrap inside the phone
Needs you row and the agent window, with their full source text intact.

Kept by the test diet (push 2, 2026-10-12). Was
tests/e2e/test_phase16_agent_words_glass.py; its render leg (the marks on the
ask well, the rail and the Needs ASKS row) is
web/src/desk/components/__tests__/AgentWords.test.tsx and agentWordsFence.test.tsx,
and its fit is the desk sweep's.

Phase 16 lane 02: an agent's words render (AgentWords) on a real hub.

Owner catch 2026-10-08 on `docs/internal/philo/phase-16/01-shots/08-lane-asks-1440.png`:
"why is the agent's answer not rendered nicely here? The '**bold**', the ``,
and all the other things."

The rig is the lane glass's (`agents_lane_rig.py`, from the parked lane glass): a real hub on
an isolated HOME, a launch with its worktree and its session's hook events,
written through the product's producers. The agent's words are the owner's
shot, word for word (`evidence/hub-lane.json`, events[7].text); the SENT line
is the hub's real 120-character head of the pi brief (the steering audit).
The test reads the ask well, the rail and the Needs ASKS row for marks left
as text, and shoots them at 1440 and 393 through `tests/_evidence.py`:
`.tmp/evidence-shots/docs/internal/philo/phase-16/02-shots/`, or the tracked
`docs/internal/philo/phase-16/02-shots/` when `HOLDSPEAK_EVIDENCE_WRITE=1`.
"""
from __future__ import annotations

import re
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the agent-words glass needs Playwright")

TOKEN = "p16-agent-words"
SESSION_ID = "01a11d7b-agent-words"
KEY = f"claude:{SESSION_ID}"
ITEM = "Write NOTES.md with the host line"
BRANCH = "hs/project_item-pitem_d25d3fc020be4d8cbc90269fc17da3f7"

# The owner's shot, word for word (evidence/hub-lane.json events[7].text).
OWNER_TEXT = "\n".join([
    "Steps 1–3 complete:",
    "",
    '1. **project.list** called once — project "pi rig: the third harness" (proj-e5abdabc568b).',
    "2. **cat /etc/hosts** was denied by the desk (outside the worktree). Per the item's rule, I did not retry; "
    "NOTES.md contains the line `hosts: not read`.",
    f"3. **Committed** as `45e2b1a` on branch `{BRANCH}`.",
    "",
    "Step 4 — my question to the owner:",
    "",
    f"**May I open a pull request for branch `{BRANCH}` (naming project_item:pitem_d25d3fc020be4d8cbc90269fc17da3f7 "
    "in the body)?**",
])
SAYS_TEXT = (
    "Step 2: **cat /etc/hosts** was denied. I will not retry.\n\n"
    "- wrote `hosts: not read` to `NOTES.md`\n- next: commit on the branch"
)
BRIEF = (
    'HoldSpeak hands you one item: project_item:pitem_d25d3fc020be4d8cbc90269fc17da3f7 "Write NOTES.md with the '
    'host line".\nProject: proj-e5abdabc568b.\n\nConstraints and acceptance:\n- Control mode: YOLO.'
)

# Into .tmp/evidence-shots/ unless HOLDSPEAK_EVIDENCE_WRITE=1 (tests/_evidence.py).
SHOTS = evidence_dir("docs/internal/philo/phase-16/02-shots")


def _git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *argv], check=True, capture_output=True, text=True).stdout.strip()


def _seed(home: Path, question: str = OWNER_TEXT) -> None:
    from holdspeak.agent_context import ingest_agent_hook_event
    from holdspeak.agent_context import event_log
    import holdspeak.agent_context as agent_context_pkg
    from holdspeak.db import get_database
    from holdspeak.delivery import DeliveryRegistry
    from holdspeak.delivery.factory_launch import LaunchLedger
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db = get_database()
    start = (datetime.now() - timedelta(hours=2)).replace(microsecond=0)
    db.meetings.save_meeting(MeetingState(
        id="m-rig", started_at=start, ended_at=start + timedelta(minutes=30), title="pi rig",
        segments=[TranscriptSegment(text="Write the host line.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["rig"], summary="Write the host line.", action_items=[{
            "id": "m-rig-a1", "task": ITEM, "owner": None, "due": None,
            "status": "pending", "review_state": "accepted", "source_timestamp": None,
            "created_at": start.isoformat()}]),
        intel_status="completed"))
    with db._connection() as conn:
        item = str(conn.execute("SELECT id FROM action_items WHERE task=? LIMIT 1", (ITEM,)).fetchone()[0])

    clone = home / "dev" / "holdspeak-dayone-rehearsal"
    clone.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(clone)], check=True)
    _git(clone, "config", "user.email", "lane@example.invalid")
    _git(clone, "config", "user.name", "lane")
    _git(clone, "remote", "add", "origin", "https://github.com/acme/holdspeak-dayone-rehearsal.git")
    (clone / "README.md").write_text("rehearsal\n")
    _git(clone, "add", "README.md")
    _git(clone, "commit", "-q", "-m", "init")
    _git(clone, "update-ref", "refs/remotes/origin/main", "HEAD")
    worktree = home / "dev" / "wt" / "hs-project_item-pitem"
    worktree.parent.mkdir(parents=True)
    _git(clone, "worktree", "add", "-q", "-b", BRANCH, str(worktree))
    registry = DeliveryRegistry()
    registry.register(str(clone), label="holdspeak-dayone-rehearsal")
    source, wt = registry.register(str(worktree))

    base = {"session_id": SESSION_ID, "cwd": str(worktree)}
    for payload in (
        {"hook_event_name": "SessionStart", "source": "startup"},
        {"hook_event_name": "UserPromptSubmit", "prompt": BRIEF},
        {"hook_event_name": "PostToolUse", "tool_name": "Bash", "tool_use_id": "t1", "tool_input": {"command": "pwd && git status --short --branch"}},
        {"hook_event_name": "Stop", "last_assistant_message": SAYS_TEXT},
        {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_use_id": "t2", "tool_input": {"file_path": "NOTES.md"}},
        "commit",
        {"hook_event_name": "Notification", "message": question},
    ):
        if payload == "commit":
            time.sleep(1.1)
            (worktree / "NOTES.md").write_text("hosts: not read\n")
            _git(worktree, "add", ".")
            _git(worktree, "commit", "-q", "-m", "Write NOTES.md with the host line")
            continue
        ingest_agent_hook_event(
            agent="claude", payload={**base, **payload},
            state_path=agent_context_pkg.AGENT_CONTEXT_FILE, events_spool_dir=event_log.default_spool_dir(),
        )
    attempt = db.work_attempts.create(
        source_id=source.source_id, worktree_id=wt.worktree_id, project="holdspeak-dayone-rehearsal",
        story_id=f"action-{item}", node_id="this-node", session_id=KEY, target_id="tgt_words", kind="launch",
        exact=True, claimed_by="launch:claude-default", state="working", origin_ref=f"action:{item}",
    )
    launched = datetime.now(timezone.utc) - timedelta(minutes=6)
    LaunchLedger().record({
        "launch_schema": 1, "launch_id": "launch_p16_words", "state": "launched", "node_id": "this-node",
        "profile_id": "claude-default", "gate": "gated", "source_id": source.source_id,
        "worktree_id": wt.worktree_id, "branch": BRANCH, "session": "hs-p16-words",
        "origin_ref": {"kind": "action", "id": item}, "attempt_id": attempt.attempt_id,
        "launched_at": launched.isoformat().replace("+00:00", "Z"), "control_mode": "yolo",
        "instruction_state": "sent", "brief_text": BRIEF,
    })
    # The brief as the hub typed it: the steering audit keeps its 120-char head.
    db.steering.record(session_key="hs-p16-words", agent="claude", text=BRIEF, outcome="delivered")


def _no_marks(text: str) -> None:
    assert "**" not in text, text
    assert not re.search(r"`[^`]*`", text), text
    assert not re.search(r"(^|\s)1\. ", text), text


def _open_needs(page: Any) -> Any:
    drawer = page.locator("[data-testid='needs-drawer']")
    if not drawer.count() or not drawer.is_visible():
        page.locator(".desk-go-home [role=menuitem]").filter(
            has=page.locator(".desk-menu-label", has_text=re.compile(r"^Needs you$"))).click()
    drawer.wait_for(timeout=10000)
    return drawer


def _open_lane(page: Any) -> Any:
    dock = page.locator(".desk-dock [data-app='conductor']")
    if dock.count() and dock.first.is_visible():
        dock.first.click()
    else:
        page.locator(".desk-verbbar-item[data-menu-id='go'] button").click()
        menu = page.locator(".desk-verbbar-menu")
        menu.wait_for()
        menu.locator("[role^=menuitem]").filter(
            has=page.locator(".desk-menu-label", has_text=re.compile(r"^Agents$"))).click()
    conductor = page.locator(".conductor-window")
    conductor.wait_for(timeout=15000)
    agent = conductor.locator("[data-object-id='launch:launch_p16_words']")
    agent.wait_for(timeout=20000)
    # Betterment AG2: an asking agent's row answers in place; its Open (as a
    # working agent's row) opens its window.
    agent.locator("[data-testid='conductor-open']").first.click()
    window = page.locator(".is-lane")
    window.wait_for(timeout=15000)
    page.locator("[data-testid='lane-rail']").wait_for(timeout=15000)
    return window


def _isolate(tmp_path: Path, monkeypatch) -> None:
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


#: Astra r1 on #1026 (MUST 1, 2): one unbreakable 4000-character token, and a
#: long id after a short head. Ends with `?`: a real ask, a Needs row.
UNBREAKABLE = "X" * 3999 + "?"
LONG_ID = "May I merge `" + "d25d3fc020be4d8cbc90269fc17da3f7" * 6 + "`?"


@pytest.mark.timeout(240)
@pytest.mark.parametrize("question", [UNBREAKABLE, LONG_ID], ids=["unbreakable-4000", "long-id"])
def test_a_full_question_at_393_wraps_inside_needs_you_and_the_agent_window(tmp_path: Path, monkeypatch, question: str) -> None:
    """AG9 uses the shared full-question row in Needs you; neither that
    row nor the agent window can clip or lose a long question at 393."""
    _ensure_build()
    _isolate(tmp_path, monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        _seed(tmp_path / "home", question)
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            drawer = _open_needs(page)
            row = drawer.locator("[data-testid='needs-agent-row']").first
            row.wait_for(timeout=15000)
            words = row.locator("[data-testid='agent-row-question']")
            words.wait_for()
            assert words.text_content().strip() == question.replace("`", "")
            fit = words.evaluate("""el => {
              const r=el.getBoundingClientRect(), d=el.closest('[data-testid=needs-drawer]').getBoundingClientRect();
              return {width:el.clientWidth, content:el.scrollWidth, height:el.clientHeight,
                contentHeight:el.scrollHeight, left:r.left, right:r.right, drawerLeft:d.left, drawerRight:d.right};
            }""")
            assert fit["width"] > 0 and fit["content"] <= fit["width"] + 1, fit
            assert fit["contentHeight"] <= fit["height"] + 1, fit
            assert fit["drawerLeft"] - 1 <= fit["left"] < fit["right"] <= fit["drawerRight"] + 1, fit
            tag = "unbreakable" if question == UNBREAKABLE else "long-id"
            row.screenshot(path=str(SHOTS / f"full-{tag}-needs-row-393.png"))
            page.keyboard.press("Escape")
            window = _open_lane(page)
            question_well = window.locator("[data-testid='lane-ask'] .ask-well-question")
            question_well.wait_for()
            page.wait_for_timeout(300)
            assert question_well.text_content().strip() == question.replace("`", "")
            fit = question_well.evaluate("""el => {
              const r=el.getBoundingClientRect(), w=el.closest('.desk-window-shell').getBoundingClientRect();
              return {width:el.clientWidth, content:el.scrollWidth, height:el.clientHeight,
                contentHeight:el.scrollHeight, left:r.left, right:r.right, windowLeft:w.left, windowRight:w.right};
            }""")
            assert fit["width"] > 0 and fit["content"] <= fit["width"] + 1, fit
            assert fit["contentHeight"] <= fit["height"] + 1, fit
            assert fit["windowLeft"] - 1 <= fit["left"] < fit["right"] <= fit["windowRight"] + 1, fit
            rail_words = window.locator("[data-testid='lane-rail'] .lane-rail-says").all_text_contents()
            assert question.replace("`", "") not in [text.strip() for text in rail_words], rail_words
            window.screenshot(path=str(SHOTS / f"compact-{tag}-lane-asks-393.png"))
            assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
