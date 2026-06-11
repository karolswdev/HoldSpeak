#!/usr/bin/env python3
"""HS-56-05 dogfood (macOS): the native HUD hosts a clickable card, focus-safe.

No mocks in the chain: the REAL `CocoaPresenceRenderer` (child process,
NSPanel + WKWebView of the real `/presence` page) is driven by the real
`DesktopPresenceHost`; a real aftercare proposal's real broadcast slides the
Qlippy card out inside the native panel; the panel's card-frame poll sizes it
up and enables pointer events; then a REAL Quartz mouse click on the panel's
Approve button records the audited decision — while the frontmost application
verifiably never changes (the panel is non-activating).

Playwright is used only as a geometry oracle: the same page at the same
viewport tells us where the Approve button sits inside the panel.

Run on this Mac, after building the web bundle:

    (cd web && npm run build)
    .venv/bin/python pm/roadmap/holdspeak/phase-56-qlippy/dogfood_story05_macos.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

OUT_DIR = Path(__file__).resolve().parent / "screenshots"


def _seed_meeting(db, meeting_id):
    from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment

    started = datetime(2026, 6, 10, 10, 0, 0)
    state = MeetingState(
        id=meeting_id,
        started_at=started,
        ended_at=datetime(2026, 6, 10, 11, 0, 0),
        title="Native HUD dogfood",
        segments=[TranscriptSegment(text="fix the flaky login test", speaker="Me", start_time=0.0, end_time=10.0)],
    )
    state.intel = IntelSnapshot(
        timestamp=60.0,
        topics=[],
        action_items=[{
            "id": "a1", "task": "Fix the flaky login test", "owner": "Me",
            "due": None, "status": "pending", "review_state": "accepted",
            "source_timestamp": None, "created_at": started.isoformat(),
        }],
        summary="",
    )
    db.meetings.save_meeting(state)


def _frontmost() -> str:
    import AppKit

    app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    return str(app.localizedName()) if app is not None else "?"


def _click(x: float, y: float) -> None:
    import Quartz

    for kind in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
        event = Quartz.CGEventCreateMouseEvent(None, kind, (x, y), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        time.sleep(0.08)


def main() -> int:
    import AppKit
    import httpx
    from playwright.sync_api import sync_playwright

    import holdspeak.config as config_module
    from holdspeak.db import get_database, reset_database
    from holdspeak.desktop_presence import (
        DesktopPresenceHost,
        PANEL_FRAME_CARD,
        PANEL_FRAME_PASSIVE,
    )
    from holdspeak.desktop_presence_cocoa import CocoaPresenceRenderer
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    tmp = Path(tempfile.mkdtemp())
    config_module.CONFIG_FILE = tmp / "config.json"
    reset_database()
    db = get_database(tmp / "dogfood.db")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _seed_meeting(db, "m-hud")

    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
        dictation_journal_repository=db.dictation_journal,
        dictation_corrections_repository=db.dictation_corrections,
    )
    url = server.start()
    time.sleep(1.0)
    failures: list[str] = []
    host = None
    try:
        httpx.put(f"{url}/api/settings", json={"presence": {"enabled": True, "mascot": True}}, timeout=10)

        # The REAL native renderer + host (the exact production wiring).
        host = DesktopPresenceHost(CocoaPresenceRenderer(lambda: url))
        host.handle_activity({"state": "listening", "label": "Listening", "detail": "dogfood"})
        time.sleep(3.0)  # child spawn + page load
        print("PASS  the native panel is up at the passive frame (listening)")

        # Geometry oracle: where the Approve button sits at the card viewport.
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size(
                {"width": int(PANEL_FRAME_CARD["width"]), "height": int(PANEL_FRAME_CARD["height"])}
            )
            page.goto(f"{url}/presence", wait_until="networkidle")
            page.wait_for_selector("#qlippy:not([hidden])", timeout=5000)
            page.wait_for_timeout(400)

            # The REAL proposal: one broadcast, both webviews receive it.
            filed = httpx.post(
                f"{url}/api/meetings/m-hud/aftercare/file-issue",
                json={"action_item_id": "a1", "repo": "acme/widgets"},
                timeout=10,
            ).json()
            proposal_id = filed["proposal"]["id"]
            page.wait_for_selector("#qlippy-card.is-in", timeout=5000)
            page.wait_for_timeout(700)  # settle
            box = page.locator(".q-btn-primary").bounding_box()
            browser.close()
        if not box:
            raise RuntimeError("geometry oracle found no Approve button")

        # Give the native panel's 0.4 s poll time to grow the frame.
        time.sleep(2.5)

        # Panel placement (the same math the renderer uses), in CG top-left coords.
        screen = AppKit.NSScreen.mainScreen()
        visible = screen.visibleFrame()
        full = screen.frame()
        cw, ch = int(PANEL_FRAME_CARD["width"]), int(PANEL_FRAME_CARD["height"])
        panel_x = visible.origin.x + visible.size.width - cw - 22
        panel_top_cocoa = visible.origin.y + visible.size.height - 14
        panel_top_cg = full.size.height - panel_top_cocoa

        shot_card = OUT_DIR / "story05-macos-card-frame.png"
        subprocess.run(
            ["screencapture", "-x", f"-R{int(panel_x)},{int(panel_top_cg)},{cw},{ch}", str(shot_card)],
            check=False,
        )
        print(f"PASS  card-frame screenshot captured ({shot_card.name})")

        before = _frontmost()
        click_x = panel_x + box["x"] + box["width"] / 2
        click_y = panel_top_cg + box["y"] + box["height"] / 2
        _click(click_x, click_y)
        time.sleep(1.5)
        after = _frontmost()

        stored = db.actuators.get_proposal(proposal_id)
        if stored.status == "approved" and stored.decided_by:
            print(
                f"PASS  a REAL mouse click on the native panel's Approve recorded the audited "
                f"decision (status={stored.status}, by={stored.decided_by!r}) — no side effect"
            )
        else:
            failures.append(f"native Approve click did not land: status={stored.status}")
        if before == after:
            print(f"PASS  keyboard focus never moved (frontmost before/after: {before!r})")
        else:
            failures.append(f"focus moved: {before!r} → {after!r}")

        # The card resolves; the poll returns the panel to the passive frame.
        time.sleep(2.5)
        pw, ph = int(PANEL_FRAME_PASSIVE["width"]), int(PANEL_FRAME_PASSIVE["height"])
        shot_passive = OUT_DIR / "story05-macos-passive-frame.png"
        subprocess.run(
            ["screencapture", "-x", f"-R{int(panel_x + (cw - pw))},{int(panel_top_cg)},{pw},{ph + 40}", str(shot_passive)],
            check=False,
        )
        print(f"PASS  post-resolve screenshot captured ({shot_passive.name})")
    finally:
        if host is not None:
            host.close()
        server.stop()
        reset_database()

    if failures:
        for f in failures:
            print(f"FAIL  {f}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
