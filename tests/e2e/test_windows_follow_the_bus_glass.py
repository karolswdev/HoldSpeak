"""Two windows on one thing: a write in one moves the other, with no reload.

The owner's ask (inventory C, gap 3): "Marking work done does not move the
other windows." The hub now announces every write (one ``desk_changed`` frame,
``holdspeak/web/announce.py`` and ``OperationRegistry.invoke``); the windows
that read their own data follow it (``useOnDeskChanged``).

The proof, at 1440, on a real hub with the built bundle:

- window A: the Chair (Needs you), with the row ``Mark done: <task>``;
- window B: a second browser window on the same hub, the Follow-through board
  and then the meeting record, both showing the same action item.

``Mark done`` is pressed in A. B drops the item with no reload and no press.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, _normal_chair, _settle, seed_meeting_engines
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the glass proof needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]

TOKEN = "windows-follow-the-bus"
TASK = "Send the cut-over plan"
SHOTS = evidence_dir("docs/internal/evidence/windows-follow-the-bus")
#: The debounce is 300 ms; the owner's bar is "within about a second".
FOLLOW_BUDGET_S = 2.0


def _seed() -> None:
    from holdspeak.db import get_database
    from holdspeak.intel import ActionItem
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    began = datetime.now() - timedelta(days=2)
    get_database().meetings.save_meeting(
        MeetingState(
            id="m-glass",
            started_at=began,
            ended_at=began + timedelta(hours=1),
            title="Cut-over plan",
            segments=[TranscriptSegment(text=TASK, speaker="Me", start_time=0.0, end_time=5.0)],
            intel=IntelSnapshot(timestamp=0.0, action_items=[
                ActionItem(
                    task=TASK, owner="Me", id="ai-glass", review_state="accepted",
                    due=(datetime.now() - timedelta(days=1)).date().isoformat(),
                ),
            ]),
        )
    )


def test_mark_done_in_one_window_moves_the_other(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        seed_meeting_engines()
        _seed()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                window_a = browser.new_page(viewport={"width": 1440, "height": 1000})
                window_b = browser.new_page(viewport={"width": 1440, "height": 1000})
                for window in (window_a, window_b):
                    window.emulate_media(reduced_motion="reduce")

                window_a.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _normal_chair(window_a)
                done_in_a = window_a.get_by_role("button", name=f"Done: {TASK}", exact=True)
                done_in_a.wait_for(timeout=12_000)

                # Window B: Needs you, and the Follow-through board beside it.
                window_b.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _normal_chair(window_b)
                window_b.get_by_role("button", name="Intelligence, 1 need you").click()
                window_b.get_by_role("button", name="Follow-through", exact=True).click()
                board = window_b.locator(".desk-pullout").filter(
                    has=window_b.get_by_role("button", name="Close Intelligence")).last
                card_in_b = board.get_by_text(TASK, exact=True)
                expect(card_in_b).to_have_count(1, timeout=12_000)
                row_in_b = window_b.get_by_role("button", name=f"Done: {TASK}", exact=True)
                expect(row_in_b).to_have_count(1)
                _settle(window_b)
                window_b.screenshot(path=str(SHOTS / "1440-window-b-before.png"))

                # From here window B is only watched: no reload, no press.
                navigations: list[str] = []
                window_b.on("framenavigated", lambda frame: navigations.append(frame.url))
                window_b.on("websocket", lambda _socket: navigations.append("new socket"))

                done_in_a.click()
                pressed = time.monotonic()
                expect(card_in_b).to_have_count(0, timeout=FOLLOW_BUDGET_S * 1000)
                followed_in = time.monotonic() - pressed
                expect(row_in_b).to_have_count(0, timeout=FOLLOW_BUDGET_S * 1000)
                expect(window_b.get_by_role("button", name="Intelligence, 1 need you")).to_have_count(0)

                assert navigations == [], f"window B reloaded or reconnected: {navigations}"
                assert followed_in <= FOLLOW_BUDGET_S, followed_in
                _settle(window_b)
                window_b.screenshot(path=str(SHOTS / "1440-window-b-after.png"))
                window_a.screenshot(path=str(SHOTS / "1440-window-a-after.png"))
                (SHOTS / "followed-in.txt").write_text(f"{followed_in:.3f} s\n")
                print(f"window B followed in {followed_in:.3f} s")
            finally:
                browser.close()
    finally:
        server.stop()
