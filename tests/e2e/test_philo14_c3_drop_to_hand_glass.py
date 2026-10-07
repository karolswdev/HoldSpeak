"""PHILO-14 C3: drop to hand, on a real hub (ratified boards A-3 at 1440 and 393).

A real hub on an isolated HOME. The Project "Payments ledger cutover" holds
the meeting "Ledger cutover sync" and its action item "Write the cutover
comms" (the hub's own producers), and a clone filed in the Project. The hand
runs through the real routes (`/api/authority/policy`,
`/api/agent/hand/preview`, `/api/agent/hand`, `/api/agent/launches/{id}`) and
the hub's own AgentHandService; only the process edge is the K2 launch rig
(`tests/unit/test_agent_hand._rig`: git is real, tmux and the agent are
canned). No agent starts; nothing leaves the machine.

- 1440: the action item is dragged out of the drawer onto the Conductor
  drawer on the screen (the ghost and the dotted path mid-drag, the target
  lit); the confirm line waits in the drawer head; Brief ▸ shows the brief;
  Hand launches; the line reads the receipt.
- 1440, Secure: the same drop opens the launch sheet.
- 393: no drag; the drawer list's Hand to agent reaches the same line.

Shots go to `.tmp/evidence-shots/p14-c3/`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="the drop-to-hand glass needs Playwright")

TOKEN = "p14-c3-drop"
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
        page.goto(f"{self.base}/?token={TOKEN}&open=project:{PROJECT}", wait_until="load")
        _normal_chair(page)
        page.locator(".drawer-window [data-testid=drawer-facts]").wait_for(timeout=T)
        page.locator(f".drawer-window [data-object-id='action:{ACTION_ID}']").first.wait_for(timeout=T)
        _settle(page)
        return browser, page, errors

    @staticmethod
    def _clear_of_conductor(page: Any) -> None:
        """Keep the drawer clear of the Conductor drawer (A-3: it stands right of the drawers)."""
        conductor = page.locator(".desk-screen [data-object-id='drawer:conductor']").bounding_box()
        drawer = page.locator(".drawer-window").bounding_box()
        if drawer["x"] > conductor["x"] + conductor["width"] + 20:
            return
        head = page.locator(".drawer-window .desk-window-handle").first.bounding_box()
        page.mouse.move(head["x"] + head["width"] * 0.6, head["y"] + head["height"] / 2)
        page.mouse.down()
        dx = conductor["x"] + conductor["width"] + 60 - drawer["x"]
        page.mouse.move(head["x"] + head["width"] * 0.6 + dx, head["y"] + head["height"] / 2, steps=8)
        page.mouse.up()
        page.wait_for_timeout(400)

    def _drag_onto_conductor(self, page: Any, shot: str | None = None) -> None:
        self._drag_onto(page, page.locator(".desk-screen [data-object-id='drawer:conductor']"), shot)

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
                agent = page.locator(".desk-screen [data-object-id='coder:claude:smoke-session']")
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

    @pytest.mark.e2e
    def test_secure_drop_opens_the_sheet_1440(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440, mode="safe")
            try:
                self._clear_of_conductor(page)
                self._drag_onto_conductor(page)
                sheet = page.get_by_test_id("hand-sheet")
                sheet.wait_for(timeout=T)
                assert page.get_by_test_id("hand-confirm").count() == 0
                page.get_by_test_id("hand-control").wait_for(timeout=T)
                page.screenshot(path=str(SHOTS / "c3-secure-sheet-1440.png"))
                assert not (self.rig.repo.parent / "launches.json").exists() or not json.loads(
                    (self.rig.repo.parent / "launches.json").read_text()).get("launches")
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_secure_retarget_shows_the_second_agent_1440(self) -> None:
        """Astra P2 on #946: a drop on Codex after the Conductor retargets the open sheet."""
        from playwright.sync_api import sync_playwright

        _register("codex", "x1", self.rig.repo)
        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 1440, mode="safe")
            try:
                self._clear_of_conductor(page)
                self._drag_onto_conductor(page)
                sheet = page.get_by_test_id("hand-sheet")
                sheet.wait_for(timeout=T)
                assert sheet.get_by_role("radio", name="Claude Code").is_checked()
                codex = page.locator(".desk-screen [data-object-id='coder:codex:x1']")
                codex.wait_for(timeout=T)
                # The drawer stands over the Codex agent (top right): move it down.
                head = page.locator(".drawer-window .desk-window-handle").first.bounding_box()
                page.mouse.move(head["x"] + head["width"] * 0.6, head["y"] + head["height"] / 2)
                page.mouse.down()
                page.mouse.move(head["x"] + head["width"] * 0.6, head["y"] + head["height"] / 2 + 160, steps=8)
                page.mouse.up()
                page.wait_for_timeout(400)
                self._drag_onto(page, codex)
                page.wait_for_function(
                    "() => document.querySelector('[data-testid=hand-sheet] input[type=radio][value=codex]')?.checked === true",
                    timeout=T,
                )
                page.screenshot(path=str(SHOTS / "c3-secure-retarget-1440.png"))
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_escape_cancels_the_hand_not_the_drawer(self, width: int) -> None:
        """Astra P2 on #946: Escape cancels the hand; the drawer stays open."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, width)
            try:
                drawer = page.locator(".drawer-window")
                if width >= 720:
                    self._clear_of_conductor(page)
                    self._drag_onto_conductor(page)
                else:
                    drawer.get_by_text(ACTION, exact=True).first.click()
                    drawer.get_by_role("button", name="Hand to agent").click()
                line = drawer.get_by_test_id("hand-confirm")
                line.wait_for(timeout=T)
                page.keyboard.press("Escape")
                page.wait_for_timeout(400)
                assert line.count() == 0
                assert drawer.is_visible()
                page.screenshot(path=str(SHOTS / f"c3-escape-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_no_drag_at_393_in_any_view(self) -> None:
        """Astra P3 on #946: the drawer's Icons view at 393 does not lift either."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                drawer = page.locator(".drawer-window")
                drawer.get_by_role("group", name="Drawer view").get_by_role("button", name="Icons").click()
                drawer.locator(".desk-icon").first.wait_for(timeout=T)
                assert drawer.locator(".desk-icon").count() > 0
                assert page.locator(".desk-icon[draggable=true]").count() == 0
                page.screenshot(path=str(SHOTS / "c3-icons-no-drag-393.png"))
                assert not errors, errors
            finally:
                browser.close()

    @pytest.mark.e2e
    def test_the_verb_reaches_the_line_393(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._page(pw, 393)
            try:
                drawer = page.locator(".drawer-window")
                # No drag gesture at 393.
                assert page.locator(".desk-icon[draggable=true]").count() == 0
                drawer.get_by_text(ACTION, exact=True).first.click()
                drawer.get_by_role("button", name="Hand to agent").click()
                line = drawer.get_by_test_id("hand-confirm")
                line.wait_for(timeout=T)
                page.wait_for_function(
                    "() => /^CLAUDE CODE · YOLO · hs\\//.test(document.querySelector('.drawer-window .confirm-line-fact')?.textContent || '')",
                    timeout=T,
                )
                line.scroll_into_view_if_needed()
                page.screenshot(path=str(SHOTS / "c3-confirm-393.png"))
                # The line fits the window: no sideways scroll.
                assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
                line.get_by_role("button", name="Hand", exact=True).click()
                line.get_by_test_id("hand-confirm-receipt").wait_for(timeout=T)
                page.wait_for_function(
                    "() => (document.querySelector('[data-testid=hand-confirm-receipt]')?.textContent || '') === 'LAUNCHED · BRIEF SENT'",
                    timeout=30_000,
                )
                page.screenshot(path=str(SHOTS / "c3-receipt-393.png"))
                assert not errors, errors
            finally:
                browser.close()
