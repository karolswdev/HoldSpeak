"""Phase 16 lane 02: an agent's words render (AgentWords) on a real hub.

Owner catch 2026-10-08 on `docs/internal/philo/phase-16/01-shots/08-lane-asks-1440.png`:
"why is the agent's answer not rendered nicely here? The '**bold**', the ``,
and all the other things."

The rig is the lane glass's (`test_philo14_c2_lane_glass.py`): a real hub on
an isolated HOME, a launch with its worktree and its session's hook events,
written through the product's producers. The agent's words are the owner's
shot, word for word (`evidence/hub-lane.json`, events[7].text); the SENT line
is the hub's real 120-character head of the pi brief (the steering audit).
The test reads the ask well, the rail and the Needs ASKS row for marks left
as text, and shoots them at 1440 and 393 to
`docs/internal/philo/phase-16/02-shots/` when `HOLDSPEAK_P16_SHOTS=1` (else
to `.tmp/evidence-shots/p16-agent-words/`).
"""
from __future__ import annotations

import os
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

if os.environ.get("HOLDSPEAK_P16_SHOTS") == "1":
    SHOTS = Path(__file__).resolve().parents[2] / "docs" / "internal" / "philo" / "phase-16" / "02-shots"
    SHOTS.mkdir(parents=True, exist_ok=True)
else:
    SHOTS = evidence_dir("p16-agent-words")


def _git(cwd: Path, *argv: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *argv], check=True, capture_output=True, text=True).stdout.strip()


def _seed(home: Path) -> None:
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
        {"hook_event_name": "Notification", "message": OWNER_TEXT},
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
    if not page.locator("[data-testid='needs-drawer']").count():
        icon = page.locator(".desk-screen [data-object-id='drawer:needs']")
        icon.focus()
        page.keyboard.press("Enter")
    drawer = page.locator("[data-testid='needs-drawer']")
    drawer.wait_for(timeout=10000)
    return drawer


def _open_lane(page: Any) -> Any:
    dock = page.locator(".desk-dock [data-app='conductor']")
    if dock.count() and dock.first.is_visible():
        dock.first.click()
    else:
        from urllib.parse import urlsplit

        origin = "{0.scheme}://{0.netloc}".format(urlsplit(page.url))
        page.goto(f"{origin}/conductor", wait_until="load")
        _normal_chair(page)
        _settle(page)
    conductor = page.locator(".conductor-window")
    conductor.wait_for(timeout=15000)
    agent = conductor.locator("[data-object-id='launch:launch_p16_words']")
    agent.wait_for(timeout=20000)
    agent.click()
    conductor.get_by_role("button", name="Open", exact=True).click()
    window = page.locator(".is-lane")
    window.wait_for(timeout=15000)
    page.locator("[data-testid='lane-rail']").wait_for(timeout=15000)
    return window


@pytest.mark.timeout(240)
def test_an_agents_words_render_on_the_lane_and_the_needs_row(tmp_path: Path, monkeypatch) -> None:
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
        _seed(tmp_path / "home")
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

                # The Needs ASKS row: the words in one or two lines, marks drawn.
                drawer = _open_needs(page)
                row = drawer.locator("[data-testid='needs-row']").filter(has_text="project.list").first
                row.wait_for(timeout=15000)
                words = row.locator(".needs-row-words")
                assert words.count() == 1
                shown = words.text_content() or ""
                _no_marks(shown)
                assert shown.startswith("Steps 1–3 complete: · project.list"), shown
                # A cut line ends on a whole word and `…`.
                if shown.endswith("…"):
                    whole = set(re.sub(r"\*\*|`|^\d\. ", "", OWNER_TEXT, flags=re.M).split())
                    assert shown[:-1].split()[-1] in whole, shown
                assert words.locator("strong").first.text_content().strip() == "project.list"
                page.wait_for_timeout(300)
                row.screenshot(path=str(SHOTS / f"needs-asks-row-{width}.png"))
                page.screenshot(path=str(SHOTS / f"needs-asks-{width}.png"))
                page.keyboard.press("Escape")

                # The lane: the ask well, the SENT line, the rail.
                window = _open_lane(page)
                ask = page.locator("[data-testid='lane-ask'] .ask-well-question")
                ask_text = ask.text_content() or ""
                _no_marks(ask_text)
                assert ask.locator("ol > li").count() == 3
                assert ask.locator("strong").first.text_content() == "project.list"
                assert ask.locator("code").filter(has_text="hosts: not read").count() == 1
                receipt = page.locator("[data-testid='lane-receipt']").text_content() or ""
                assert receipt.startswith("SENT · ") and "HoldSpeak hands you one item" in receipt, receipt
                assert not re.search(r"\sP$", receipt), receipt
                rail = page.locator("[data-testid='lane-rail']")
                _no_marks(rail.text_content() or "")
                assert rail.locator(".lane-rail-says strong").first.text_content() == "cat /etc/hosts"
                # Nothing leaves the frame at 393: no side scroll, the ask well inside the window.
                assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")
                over = ask.evaluate(
                    "(el) => [...el.querySelectorAll('*')].filter((n) => n.scrollWidth > el.clientWidth + 1).length"
                )
                assert over == 0, over
                page.wait_for_timeout(400)
                page.screenshot(path=str(SHOTS / f"lane-ask-well-{width}.png"))
                says = rail.locator(".lane-rail-entry").filter(has_text="SAYS").first
                says.scroll_into_view_if_needed()
                says.screenshot(path=str(SHOTS / f"lane-rail-says-{width}.png"))
                asks = rail.locator(".lane-rail-entry").filter(has=page.locator(".lane-rail-words-line")).first
                asks.scroll_into_view_if_needed()
                asks.screenshot(path=str(SHOTS / f"lane-rail-asks-{width}.png"))
                _assert_clean(page, errors)
                page.close()
            browser.close()
    finally:
        server.stop()
