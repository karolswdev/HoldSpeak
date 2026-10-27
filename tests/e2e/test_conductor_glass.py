"""The Conductor app, AS RENDERED: what only a real browser proves of the hand.

Owner, 2026-10-12 (push 2 of the test diet): a browser test only for drag,
focus, keys, touch, hover or an exact geometry relation. This file keeps the
REAL drag of PHILO-14 C3 (drop to hand, ratified board A-3 at 1440): an action
item dragged onto the Conductor drawer on the screen (the ghost and the dotted
path mid-drag, the target lit); the confirm line; Brief ▸; Hand launches; the
line reads the receipt; the agent registered by the real hook producer appears.

A real hub on an isolated HOME. The hand runs through the real routes and the
hub's own AgentHandService; only the process edge is the K2 launch rig
(`tests/unit/test_agent_hand._rig`: git is real, tmux and the agent are
canned). No agent starts; nothing leaves the machine.

The drag starts in the Project drawer, which is parked as a project face
(PHILO-17 U30) and opened here by its key; the Room's FILES rows and the
screen's objects carry the same `handSourceProps` (web/src/desk/hand/drag.ts).
Every other C3 leg is in web/src/desk/hand/__tests__/hand.test.tsx (Secure
opens the sheet, the retarget, Escape, no lift at 393, the 393 verb, the
CLAUDE CODE / CODEX flip).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import open_project_drawer, _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the Conductor glass needs Playwright")

TOKEN = "conductor-glass"
SHOTS = evidence_dir("p14-c3")
SIZES = {1440: 900, 393: 852}
T = 20_000
PROJECT = "p-ledger"
ACTION_ID = "m-sync-a1"
ACTION = "Write the cutover comms"


def _seed(db: Any) -> None:
    from datetime import datetime, timedelta

    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    db.projects.create_project(project_id=PROJECT, name="Payments ledger cutover", description="Nov 5.",
                               keywords=["ledger"])
    start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
    db.meetings.save_meeting(MeetingState(
        id="m-sync", started_at=start, ended_at=start + timedelta(minutes=30), title="Ledger cutover sync",
        segments=[TranscriptSegment(text="We freeze the old ledger on Nov 5.", speaker="Me", start_time=1.0, end_time=4.0)],
        intel=IntelSnapshot(timestamp=1.0, topics=["cutover"], summary="Freeze on Nov 5.", action_items=[{
            "id": ACTION_ID, "task": ACTION, "owner": None, "due": None, "status": "pending",
            "review_state": "accepted", "source_timestamp": None, "created_at": start.isoformat()}]),
        intel_status="completed"))
    db.projects.associate_meeting_project(meeting_id="m-sync", project_id=PROJECT, source="manual", confidence=1.0)


def _register(agent: str, session_id: str, cwd: Path) -> None:
    """The real hook producer: the agent's SessionStart and first prompt, as
    `holdspeak agent-hook ingest` writes them into the registry."""
    import holdspeak.agent_context as agent_context
    from holdspeak.agent_context import event_log, ingest_agent_hook_event

    for payload in (
        {"hook_event_name": "SessionStart", "source": "startup"},
        {"hook_event_name": "UserPromptSubmit", "prompt": "Work the item."},
    ):
        ingest_agent_hook_event(
            agent=agent, payload={"session_id": session_id, "cwd": str(cwd), **payload},
            state_path=agent_context.AGENT_CONTEXT_FILE, events_spool_dir=event_log.default_spool_dir(),
        )


class TestDropToHandGlass:
    """replaces: tests/e2e/test_philo14_c3_drop_to_hand_glass.py::TestDropToHandGlass::test_drag_onto_the_conductor_then_hand_1440 (moved whole)."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        from holdspeak.db import get_database
        from holdspeak.services import agent_hand_preview, agent_hand_service
        from tests.unit.test_agent_hand import _rig

        db = get_database()
        _seed(db)
        # The process edge only (the K2 rig): the hub's own service and routes run.
        rig = _rig(tmp_path / "hand", db, monkeypatch, item=("action", ACTION_ID), project=PROJECT)
        self.rig = rig
        # The clone is filed in the Project (the repository the hand resolves).
        with db._connection() as conn:
            conn.execute("INSERT INTO project_resources (project_id, resource_ref) VALUES (?, ?)",
                         (PROJECT, f"repository:{rig.source.source_id}"))
        monkeypatch.setattr(agent_hand_service, "default_agent_hand_service", lambda *a, **k: rig.hand)
        # The hub composed its own service at boot: its `hand` runs as the rig's.
        real_hand = agent_hand_service.AgentHandService.hand
        monkeypatch.setattr(agent_hand_service.AgentHandService, "hand",
                            lambda _self, *a, **k: real_hand(rig.hand, *a, **k))
        real_reads = agent_hand_preview.LaunchReads
        files = rig.repo.parent
        monkeypatch.setattr(agent_hand_preview, "LaunchReads", lambda *a, **k: real_reads(
            profiles_path=files / "profiles.json", registry_path=files / "sources.json",
            ledger_path=files / "launches.json", which=lambda name: f"/bin/{name}", runner=rig.tmux,
        ))
        try:
            yield
        finally:
            rig.tmux.ended = True
            server.stop()

    def _page(self, pw: Any, width: int, mode: str = "yolo") -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=2,
                                  has_touch=width < 720, reduced_motion="reduce")
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        _api(page, "PUT", "/api/authority/control-mode", {"control_mode": mode}, token=TOKEN)
        open_project_drawer(page, self.base, PROJECT, TOKEN)  # PHILO-17 U30: the parked drawer, by its key
        _normal_chair(page)
        page.locator(".drawer-window [data-testid=drawer-facts]").wait_for(timeout=T)
        page.locator(f".drawer-window [data-object-id='action:{ACTION_ID}']").first.wait_for(timeout=T)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _clear_of_conductor(page: Any) -> None:
        """S4: Agents is the Dock's live drop target, clear of the drawer."""
        target = page.locator(".desk-dock [data-app='conductor']")
        target.wait_for(state="visible")
        assert target.evaluate("""el => {const r=el.getBoundingClientRect();
            return el.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));}""")

    def _drag_onto_conductor(self, page: Any, shot: str | None = None) -> None:
        self._drag_onto(page, page.locator(".desk-dock [data-app='conductor']"), shot)

    def _drag_onto(self, page: Any, target: Any, shot: str | None = None) -> None:
        source = page.locator(f".drawer-window [data-object-id='action:{ACTION_ID}']").first
        sb, tb = source.bounding_box(), target.bounding_box()
        page.mouse.move(sb["x"] + sb["width"] / 2, sb["y"] + sb["height"] / 3)
        page.mouse.down()
        page.mouse.move(sb["x"] + sb["width"] / 2 - 20, sb["y"] + sb["height"] / 3 + 10, steps=4)
        page.mouse.move(tb["x"] + tb["width"] / 2, tb["y"] + tb["height"] / 3, steps=16)
        # Chromium delivers the drag's moves a beat late: settle on the target.
        for dx in (1, 0, 1, 0):
            page.wait_for_timeout(120)
            page.mouse.move(tb["x"] + tb["width"] / 2 + dx, tb["y"] + tb["height"] / 3)
        page.wait_for_timeout(200)
        if shot:
            assert page.locator(".drag-ghost").count() == 1
            assert page.locator(".drag-path line").count() == 1
            assert target.get_attribute("data-drop") == "true"
            assert source.get_attribute("data-ghost") == "true"
            page.screenshot(path=str(SHOTS / shot))
        page.mouse.up()

    @pytest.mark.e2e
    def test_drag_onto_the_conductor_then_hand_1440(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440)
            try:
                self._clear_of_conductor(page)
                self._drag_onto_conductor(page, shot="c3-drag-1440.png")
                drawer = page.locator(".drawer-window")
                line = drawer.get_by_test_id("hand-confirm")
                line.wait_for(timeout=T)
                assert page.locator(".drag-ghost").count() == 0
                fact = line.locator(".confirm-line-fact")
                page.wait_for_function(
                    "() => /^CLAUDE CODE · YOLO · hs\\//.test(document.querySelector('.drawer-window .confirm-line-fact')?.textContent || '')",
                    timeout=T,
                )
                assert line.locator(".confirm-line-title").inner_text() == ACTION
                assert "API.ANTHROPIC.COM" in line.inner_text()
                # Nothing launched before the press.
                assert not (self.rig.repo.parent / f"hs-action-{ACTION_ID}").exists()
                page.screenshot(path=str(SHOTS / "c3-confirm-1440.png"))
                line.get_by_role("button", name="Brief ▸").click()
                brief = line.get_by_test_id("hand-confirm-brief")
                brief.wait_for(timeout=T)
                assert ACTION in brief.inner_text()
                page.screenshot(path=str(SHOTS / "c3-brief-1440.png"))
                line.get_by_role("button", name="Hand", exact=True).click()
                receipt = line.get_by_test_id("hand-confirm-receipt")
                receipt.wait_for(timeout=T)
                page.wait_for_function(
                    "() => (document.querySelector('[data-testid=hand-confirm-receipt]')?.textContent || '') === 'LAUNCHED · BRIEF SENT'",
                    timeout=30_000,
                )
                page.screenshot(path=str(SHOTS / "c3-receipt-1440.png"))
                # Astra P1 on #946: the agent registers through the real hook
                # producer AFTER the launch answered; its icon appears with no
                # other desk action (the hub frames the registration; the
                # line re-reads the flights).
                # Betterment AG8: Agents owns the live rows; individual
                # session icons no longer appear on the desk floor.
                page.locator(".desk-dock [data-app='conductor']").click()
                conductor = page.locator(".conductor-window")
                conductor.wait_for(timeout=T)
                agent = conductor.locator("[data-object-id='coder:claude:smoke-session']")
                assert agent.count() == 0
                _register("claude", "smoke-session", self.rig.worktree)
                agent.wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / "c3-agent-appears-1440.png"))
                # The real route launched into a new worktree, with the item as origin.
                launches = json.loads((self.rig.repo.parent / "launches.json").read_text())["launches"]
                assert [x.get("origin_ref") for x in launches] == [{"kind": "action", "id": ACTION_ID}], launches
                assert (self.rig.repo.parent / f"hs-action-{ACTION_ID}").exists()
                (SHOTS / "c3-facts.json").write_text(json.dumps({
                    "fact": fact.inner_text(), "receipt": receipt.inner_text(),
                    "launch": {k: launches[0].get(k) for k in ("launch_id", "branch", "profile_id", "instruction_state")},
                }, indent=2))
                assert not errors, errors
            finally:
                browser.close()


class TestSessionOpenGlass:
    """Actual Conductor Open: phone frame geometry, folded controls and answer focus.

    The registry, launch projection and terminal absence are real product reads.
    No model, terminal process, key send or microphone action is performed.
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        import holdspeak.agent_context as agent_context
        import holdspeak.delivery.factory_launch as factory_launch
        from holdspeak.agent_context import event_log, ingest_agent_hook_event
        from .conductor_rig import _seed as seed_sessions

        _ensure_build()
        state = tmp_path / "home/.holdspeak"
        state.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(factory_launch, "DEFAULT_LAUNCHES_PATH", state / "agent_launches.json")
        monkeypatch.setattr(agent_context, "AGENT_CONTEXT_FILE", state / "agent_sessions.json")
        monkeypatch.setattr(event_log, "default_spool_dir", lambda: state / "agent-events")
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        seed_sessions(tmp_path / "home")
        repo = tmp_path / "home/dev/payments-ledger"
        (repo / ".git").mkdir(parents=True)
        report = "Added the rollback checkpoint. Checking the migration tests."
        transcript = tmp_path / "working-transcript.jsonl"
        transcript.write_text(json.dumps({"role": "assistant", "content": report}) + "\n")
        spool = {"state_path": agent_context.AGENT_CONTEXT_FILE, "events_spool_dir": event_log.default_spool_dir()}
        for event in (
            {"hook_event_name": "Stop", "last_assistant_message": report, "transcript_path": str(transcript)},
            {"hook_event_name": "PreToolUse", "tool_name": "Bash"},
        ):
            recorded = ingest_agent_hook_event(agent="codex", payload={"session_id": "surface-working", "cwd": str(repo), **event}, capture_messages=True, **spool)
        assert recorded.last_assistant_text == report
        ingest_agent_hook_event(agent="claude", payload={"session_id": "surface-asking", "cwd": str(repo),
            "hook_event_name": "Notification", "message": "Who owns the rollback: Jordan or Avery?"}, **spool)
        try:
            yield
        finally:
            server.stop()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_open_keeps_work_and_phone_frame_then_focuses_one_answer(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
        from .glass_infra import clear_hub_windows

        shots = evidence_dir("surface-repair-sessions")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": SIZES[width]}, reduced_motion="reduce")
            page.set_default_timeout(T)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                clear_hub_windows(page, TOKEN)
                page.goto(f"{self.base}/conductor", wait_until="load")
                _normal_chair(page)
                _settle(page)
                conductor = page.locator(".conductor-window")

                def shot(name: str, face: Any) -> None:
                    face.wait_for(state="visible")
                    _settle(page)
                    page.screenshot(path=str(shots / f"{name}-{width}.png"))
                    if width == 393:
                        bounds = face.bounding_box()
                        assert abs(bounds["x"]) < 1 and abs(bounds["width"] - width) < 1, bounds
                    assert face.locator(".desk-pullout-body").evaluate("el => el.scrollWidth <= el.clientWidth + 1")

                # #1523 (W1-KIT): one press on the row opens it; the status
                # bar's Open stays for a keyboard selection.
                conductor.locator("[data-object-id='coder:codex:surface-working'] .object-list-open").click()
                session = page.locator(".is-session")
                session.get_by_test_id("session-head").wait_for()
                shot("plain-working", session)
                assert "payments-ledger" in session.locator(".desk-window-title").inner_text()
                assert "Added the rollback checkpoint. Checking the migration tests." in session.inner_text()
                assert session.get_by_test_id("session-terminal").count() == 0
                assert not session.locator("details.desk-session-details").evaluate("el => el.open")
                session.get_by_test_id("session-open-terminal").click()
                terminal = session.get_by_test_id("session-terminal")
                terminal.get_by_text("Terminal unavailable", exact=False).wait_for()
                shot("plain-terminal-unavailable", session)
                assert terminal.get_by_role("button", name="Retry", exact=True).is_visible()
                terminal.get_by_role("button", name="Back to session", exact=True).click()
                assert terminal.count() == 0
                session.locator(".desk-gadget-close").click()

                # Asking rows lead with Answer; Get Info's existing Open is
                # the read-only door, so this test never starts capture.
                def open_asking(ref: str) -> None:
                    conductor.locator(f"[data-object-id='{ref}'] .cw-row-title").click()
                    conductor.get_by_role("button", name="Get Info", exact=True).click()
                    info = page.locator(".conductor-info-window")
                    info.get_by_role("button", name="Open", exact=True).click()

                open_asking("coder:claude:surface-asking")
                field = session.get_by_role("textbox", name="Answer", exact=True)
                field.click()
                assert field.evaluate("el => document.activeElement === el")
                shot("plain-asking", session)
                assert session.locator(".ask-well-question").count() == 1
                assert "is-listening" not in session.inner_html()
                session.locator(".desk-gadget-close").click()
                page.locator(".conductor-info-window .desk-gadget-close").click()

                # #1523 (W1-KIT): one press on the row opens it; the status
                # bar's Open stays for a keyboard selection.
                conductor.locator("[data-object-id='launch:launch_c4_recon'] .object-list-open").click()
                lane = page.locator(".is-lane")
                lane.get_by_test_id("lane-head").wait_for()
                # AG10 omits an empty timeline rather than drawing a lone brief.
                assert lane.get_by_test_id("lane-rail").count() == 0
                shot("lane-working", lane)
                assert not lane.get_by_test_id("lane-track").is_visible()
                assert "Your press in GitHub" not in lane.inner_text()
                lane.get_by_test_id("lane-raw").click()
                shot("lane-terminal-unavailable", lane)
                assert lane.get_by_test_id("lane-head").is_visible()
                assert lane.get_by_test_id("lane-raw-pane").get_by_role("button", name="Retry", exact=True).is_visible()
                assert lane.locator(".lw-keys").count() == 0
                lane.locator(".desk-gadget-close").click()

                open_asking("launch:launch_c4_runbook")
                lane.get_by_test_id("lane-ask").wait_for()
                shot("lane-asking", lane)
                assert lane.locator(".ask-well-question").count() == 1
                assert lane.get_by_test_id("lane-rail").count() == 0
                assert not errors, errors
            finally:
                browser.close()
