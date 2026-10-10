"""PHILO-14 C4: the Conductor drawer on a real hub (ratified boards A-1, A-4).

A real hub on an isolated HOME, seeded as the Conductor F2 seed does
(`docs/internal/philo/phase-14/canvas/harness/seed_f2.py`), through the
product's producers: three action items on a meeting, two hook-reported
sessions (Claude Code asks "The runbook needs a rollback owner. Jordan or
Avery?", Codex works), and three launches on the ledger with their Work
attempts: the runbook bound to Claude Code, the reconciliation job bound to
Codex, the freeze flag with PR #412 open on its follow-through. No agent
runs; nothing leaves the machine.

The Dock's Conductor (1440) and the `/conductor` address (393) open the
Conductor window; it lists the ready agents and the three launched agents
with their lamps, asking first; its head says `2 at work` with `1 ASK` (no
`N OF M`: the hub counts no running tmux session here). At 393 every verb of
the selected asking agent and of its Stop confirmation is whole in the
window, 44 px, the element at its centre. Open on the asking agent opens its
lane, read before its question is asserted. Shots to `.tmp/evidence-shots/p14-c4/`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the Conductor glass needs Playwright")

TOKEN = "p14-c4-conductor"
QUESTION = "The runbook needs a rollback owner. Jordan or Avery?"
SHOTS = evidence_dir("p14-c4")
T = 20_000


def _seed(home: Path) -> None:
    import holdspeak.agent_context as agent_context_pkg
    from holdspeak.agent_context import event_log, ingest_agent_hook_event
    from holdspeak.db import get_database
    from holdspeak.delivery.factory_launch import LaunchLedger
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db = get_database()
    start = (datetime.now() - timedelta(hours=2)).replace(microsecond=0)
    tasks = ["Write the rollback runbook", "Shard the reconciliation job", "Add the ledger freeze flag"]
    db.meetings.save_meeting(MeetingState(
        id="m-cutover", started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger cutover sync",
        segments=[TranscriptSegment(text="We freeze the ledger on Nov 12.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary="We freeze the ledger on Nov 12.", action_items=[{
            "id": f"m-cutover-a{i}", "task": task, "owner": None, "due": None, "status": "pending",
            "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}
            for i, task in enumerate(tasks)]),
        intel_status="completed"))
    with db._connection() as conn:
        ids = {task: str(conn.execute("SELECT id FROM action_items WHERE task=? LIMIT 1", (task,)).fetchone()[0])
               for task in tasks}

    spool = {"state_path": agent_context_pkg.AGENT_CONTEXT_FILE, "events_spool_dir": event_log.default_spool_dir()}
    ingest_agent_hook_event(agent="claude", payload={
        "session_id": "c1a0de00-runbook", "cwd": str(home / "dev" / "payments-ledger-runbook"),
        "hook_event_name": "Notification", "message": QUESTION}, **spool)
    ingest_agent_hook_event(agent="codex", payload={
        "session_id": "c0dex000-recon", "cwd": str(home / "dev" / "payments-ledger-recon"),
        "hook_event_name": "PreToolUse", "tool_name": "Bash"}, **spool)

    launched = datetime.now(timezone.utc) - timedelta(minutes=30)
    iso = launched.isoformat().replace("+00:00", "Z")
    launches = [
        ("launch_c4_runbook", tasks[0], "claude-default", "claude:c1a0de00-runbook", None),
        ("launch_c4_recon", tasks[1], "codex-default", "codex:c0dex000-recon", None),
        ("launch_c4_flag", tasks[2], "claude-default", None, {
            "pr": {"number": 412, "url": "https://github.com/acme/payments-ledger/pull/412", "state": "open"},
            "pr_state": "pr_open"}),
    ]
    ledger = LaunchLedger()
    for launch_id, task, profile, session_key, follow in launches:
        item = ids[task]
        attempt = db.work_attempts.create(
            source_id="src_ledger", worktree_id=f"wt_{launch_id}", project="payments-ledger",
            story_id=f"action-{item}", node_id="this-node", session_id=session_key, target_id=f"tgt_{launch_id}",
            kind="launch", exact=True, claimed_by=f"launch:{profile}", state="working", origin_ref=f"action:{item}")
        record: dict[str, Any] = {
            "launch_schema": 1, "launch_id": launch_id, "state": "launched", "node_id": "this-node",
            "profile_id": profile, "gate": "gated", "branch": f"hs/action-{item}", "session": f"hs-{launch_id}",
            "origin_ref": {"kind": "action", "id": item}, "attempt_id": attempt.attempt_id,
            "launched_at": iso, "control_mode": "normal", "instruction_state": "sent",
        }
        if follow:
            record["follow_through"] = follow
        ledger.record(record)


def _verbs_in_frame(page: Any, expected: set[str]) -> list[str]:
    verbs = page.locator(".conductor-window .surface-footer-verbs button").evaluate_all(
        """(els) => {
            const frame = document.querySelector('.conductor-window').getBoundingClientRect();
            return els.map((el) => {
                const r = el.getBoundingClientRect();
                const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                return {name: el.textContent.trim(), left: r.left, right: r.right, top: r.top, bottom: r.bottom,
                        height: r.height, hit: !!hit && el.contains(hit),
                        frame: {left: frame.left, right: frame.right, top: frame.top, bottom: frame.bottom}};
            });
        }""")
    names = [v["name"] for v in verbs]
    assert expected <= set(names), names
    for v in verbs:
        f = v["frame"]
        assert v["left"] >= f["left"] and v["right"] <= f["right"], v
        assert v["top"] >= f["top"] and v["bottom"] <= f["bottom"], v
        assert v["right"] <= 393 and v["bottom"] <= 852, v
        assert v["height"] >= 44, v
        assert v["hit"], v
    return names


@pytest.mark.timeout(240)
def test_the_conductor_drawer_at_1440_and_393(tmp_path: Path, monkeypatch) -> None:
    _ensure_build()
    import holdspeak.agent_context as agent_context_pkg
    import holdspeak.delivery.factory_launch as factory_launch
    from holdspeak.agent_context import event_log

    state = tmp_path / "home" / ".holdspeak"
    state.mkdir(parents=True)
    monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
    monkeypatch.setattr(agent_context_pkg, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
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
                # PHILO-16 (16b): one hub is one desk; this page starts on an empty desk.
                from .glass_infra import clear_hub_windows

                clear_hub_windows(page, TOKEN)
                if width == 1440:
                    page.reload(wait_until="load")
                    _normal_chair(page)
                    _settle(page)
                    # The Dock's Agents entry is the Conductor now.
                    dock = page.locator(".desk-dock [data-app='conductor']")
                    dock.wait_for(timeout=T)
                    assert "Conductor" in (dock.text_content() or "")
                    assert page.locator(".desk-dock [data-app='surface-companion']").count() == 0
                    dock.click()
                else:
                    # The Conductor's address opens the same window.
                    page.goto(f"{url}/conductor", wait_until="load")
                    _normal_chair(page)
                    _settle(page)
                window = page.locator(".conductor-window")
                window.wait_for(timeout=T)
                asking = window.locator("[data-object-id='launch:launch_c4_runbook']")
                asking.wait_for(timeout=T)
                for name in ("Claude Code: rollback runbook", "Codex: reconciliation job", "Claude Code: ledger freeze flag"):
                    # PHILO-15 B40 (ruling): an icon label is at most two lines, cut in
                    # the middle by fitName; the whole name is its title and aria-label.
                    assert window.locator(f"[title='{name}'], [aria-label^='{name}']").count() > 0, name
                two_lines = window.locator(".desk-icon-name").evaluate_all(
                    "(els) => els.map((e) => [e.title, Math.round(e.getBoundingClientRect().height),"
                    " parseFloat(getComputedStyle(e).lineHeight) || 16])")
                for title, height, line in two_lines:
                    assert height <= line * 2 + 4, (title, height, line)
                # The ready agents (whatever this Mac has installed: the hub's own read).
                assert window.locator("[data-object-id='agent:claude']").count() == 1
                assert window.locator("[data-object-id='agent:codex']").count() == 1
                labels = {
                    "launch:launch_c4_runbook": "ASKS",
                    "launch:launch_c4_recon": "WORKS",
                    "launch:launch_c4_flag": "PR #412",
                }
                for object_id, lamp in labels.items():
                    member = window.locator(f"[data-object-id='{object_id}']")
                    text = (member.get_attribute("aria-label") or "") + (member.text_content() or "")
                    assert lamp in text, (object_id, text)
                head = window.locator("[data-testid='conductor-head']").text_content() or ""
                # Phase 16: `2 at work` is the window's one big fact (the
                # AppHead); the ask is a lamp token on the strip beside it.
                fact = window.locator("[data-testid='conductor-head'] .kit-disp").text_content() or ""
                assert fact == "2 at work" and "1 ASK" in head, (fact, head)
                # The cap is the hub's count (`live_launches`: no tmux session
                # runs here), never the client's: no `N OF M`.
                assert " OF " not in head, head
                assert "NOT READ" not in head, head
                # Asking first in every view.
                first = window.locator("[data-object-id]").first.get_attribute("data-object-id")
                assert first == "launch:launch_c4_runbook", first
                page.wait_for_timeout(400)
                page.screenshot(path=str(SHOTS / f"C4-conductor-{width}.png"))
                if width == 393:
                    assert page.evaluate("document.scrollingElement.scrollWidth <= window.innerWidth")

                asking.click()
                if width == 393:
                    # Astra r1 P1: every verb of the selected asking agent, and of
                    # its Stop confirmation, is whole inside the WINDOW's box, 44 px
                    # tall, and the element at its own centre.
                    _verbs_in_frame(page, {"Get Info", "Stop", "Answer", "Open"})
                    page.screenshot(path=str(SHOTS / "C4-conductor-selected-393.png"))
                    window.locator("[data-testid='conductor-stop']").click()
                    window.locator("[data-testid='conductor-stop-confirm']").wait_for(timeout=T)
                    names = _verbs_in_frame(page, {"Back", "Stop · sure? (ends the agent's session)"})
                    assert "Answer" not in names and "Open" not in names, names
                    page.screenshot(path=str(SHOTS / "C4-conductor-stop-confirm-393.png"))
                    window.get_by_role("button", name="Back", exact=True).click()

                # Open on the asking agent: its lane window, read before it is read.
                window.get_by_role("button", name="Open", exact=True).click()
                lane = page.locator(".is-lane")
                lane.wait_for(timeout=T)
                lane.locator("[data-testid='lane-rail']").wait_for(timeout=T)
                lane.get_by_text(QUESTION).first.wait_for(timeout=T)
                if width == 1440:
                    page.wait_for_timeout(300)
                    page.screenshot(path=str(SHOTS / f"C4-conductor-lane-{width}.png"))
                _assert_clean(page, errors)
                page.close()
            browser.close()
    finally:
        server.stop()
