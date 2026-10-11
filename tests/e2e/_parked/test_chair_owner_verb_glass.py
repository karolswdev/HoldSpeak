"""The Chair's `Name an owner` verb, on the real hub, at 1440 and 393.

Inventory 2026-10-03 (defect 5) and Astra's review of PR #775. A meeting's
action items are saved by the real producer (`save_meeting`); both are born
`review_state=pending`, so both sit in the Door's `unassigned` lane:

- the one WITHOUT an owner offers `Name an owner`; the press opens the owner
  well in the row; Save writes the owner; the row stays, stops saying UNASSIGNED, and the verb goes;
- the one WITH an owner reads TO REVIEW, never UNASSIGNED, and has no owner
  verb.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _normal_chair, _settle

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="Chair glass needs Playwright")

TOKEN = "chair-owner-verb"
OWNED = "Draft the migration runbook"
UNOWNED = "Book the dry run"


def _seed() -> None:
    from holdspeak.db import get_database
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState

    start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
    get_database().meetings.save_meeting(MeetingState(
        id="m-owner-verb", started_at=start, ended_at=start + timedelta(minutes=30), title="Planning",
        intel=IntelSnapshot(timestamp=0.0, summary="Planned.", action_items=[
            ActionItem(task=OWNED, owner="Priya"),
            ActionItem(task=UNOWNED),
        ]), intel_status="completed"))


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_owner_verb_only_where_no_owner_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int
) -> None:
    from playwright.sync_api import sync_playwright

    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        _seed()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            phone = width < 600
            page = browser.new_context(
                viewport={"width": width, "height": height}, has_touch=phone, is_mobile=phone,
            ).new_page()
            page.emulate_media(reduced_motion="reduce")
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)
            rows = page.locator("[data-testid='needs-row']")
            rows.first.wait_for(timeout=20_000)
            _settle(page)

            # The stored facts, from the real board: both in `unassigned`, one owned.
            board = _api(page, "GET", "/api/door", token=TOKEN)["board"]
            lane = {card["text"]: card.get("owner") for card in board["unassigned"]}
            assert lane == {OWNED: "Priya", UNOWNED: None}, lane

            owned = rows.filter(has_text=OWNED)
            unowned = rows.filter(has_text=UNOWNED)
            owned_why = owned.locator(".needs-row-lamp").inner_text()
            assert "TO REVIEW" in owned_why and "UNASSIGNED" not in owned_why, owned_why
            assert owned.get_by_role("button", name="Name an owner").count() == 0
            assert "UNASSIGNED" in unowned.locator(".needs-row-lamp").inner_text()

            verb = unowned.locator("[data-verb='name-owner']")
            verb.click()
            well = page.locator("[data-testid='needs-well']")
            well.wait_for(timeout=5_000)
            well.get_by_role("textbox").fill("Avery")
            well.get_by_role("button", name="Save").click()
            well.wait_for(state="detached", timeout=10_000)
            # The hub's board is the truth the row settles on. This item is
            # still not reviewed, so it stays in the same lane, now with an
            # owner: the row reads TO REVIEW and the owner verb is gone.
            page.wait_for_function(
                """(title) => [...document.querySelectorAll("[data-testid='needs-row']")]
                    .some((row) => row.textContent.includes(title) && row.textContent.includes("TO REVIEW"))""",
                arg=UNOWNED, timeout=10_000,
            )
            after = _api(page, "GET", "/api/door", token=TOKEN)["board"]
            assert {c["text"]: c.get("owner") for c in after["unassigned"]} == {OWNED: "Priya", UNOWNED: "Avery"}
            moved = page.locator("[data-testid='needs-row']").filter(has_text=UNOWNED)
            assert moved.count() == 1  # the row stays in Needs you
            assert moved.get_by_role("button", name="Name an owner").count() == 0
            assert "UNASSIGNED" not in moved.locator(".needs-row-lamp").inner_text()
            assert page.locator("[data-verb='name-owner']").count() == 0
            browser.close()
    finally:
        server.stop()
