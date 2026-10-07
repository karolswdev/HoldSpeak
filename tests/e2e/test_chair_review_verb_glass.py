"""The Chair's `Review` verb, on the real hub, at 1440 and 393.

Astra's review of PR #788 (P1-3): the `Review` Button on an owned item that
is not reviewed yet did nothing. It required `open_ref`; the real producer's
action card names itself in `target_ref` (`action_item:<id>`). A meeting's
action item is saved by the real producer (`save_meeting`), it is born
`review_state=pending` with an owner, so it reads TO REVIEW. The press opens
the Follow-through window on that card, with its verbs showing.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _normal_chair, _settle

# PHILO-14 A1: the Chair is the screen of objects; these specs read its windows (tests/conftest.py).
pytestmark = pytest.mark.chair_windows_open

pytest.importorskip("playwright.sync_api", reason="Chair glass needs Playwright")

TOKEN = "chair-review-verb"
OWNED = "Draft the migration runbook"


def _seed() -> None:
    from holdspeak.db import get_database
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState

    start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
    get_database().meetings.save_meeting(MeetingState(
        id="m-review-verb", started_at=start, ended_at=start + timedelta(minutes=30), title="Planning",
        intel=IntelSnapshot(timestamp=0.0, summary="Planned.", action_items=[
            ActionItem(task=OWNED, owner="Priya"),
        ]), intel_status="completed"))


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_review_opens_the_card_in_follow_through(
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

            # The stored fact, from the real board: the producer's card has a
            # `target_ref` and no `open_ref`.
            card = _api(page, "GET", "/api/door", token=TOKEN)["board"]["unassigned"][0]
            assert card["text"] == OWNED and card["owner"] == "Priya"
            assert card["target_ref"] == f"action_item:{card['id']}"
            assert not card.get("open_ref")

            owned = rows.filter(has_text=OWNED)
            why = owned.locator(".needs-row-lamp").inner_text()
            assert "TO REVIEW" in why and "UNASSIGNED" not in why, why
            assert page.locator(".follow-through-view").count() == 0

            owned.locator("[data-verb='review']").click()

            # The press changes the Desk: Follow-through opens ON this card
            # (its verbs are showing: the card is the open one).
            view = page.locator(".follow-through-view")
            view.wait_for(timeout=10_000)
            verbs = view.get_by_label(f"Verbs for {OWNED}")
            verbs.wait_for(timeout=10_000)
            assert verbs.is_visible()
            page.screenshot(path=str(tmp_path / f"review-{width}.png"))
            browser.close()
    finally:
        server.stop()
