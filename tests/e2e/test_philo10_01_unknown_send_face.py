"""PHILO-10-01 round two (Codex Astra r1, finding 1): a channel send whose result
is UNKNOWN is never shown as a delivery on the Room's existing face.

Fenced AS RENDERED through the real hub on an isolated HOME at 1440x900 and
393x852, with the real producers only: two saved folder destinations, one
normal and one whose folder path leaves no room for the file's name (the OS
refuses the create with ENAMETOOLONG, which is off the pinned FAILED list, so
the file channel settles UNKNOWN). No response is substituted.

The ratified count semantics (PHILO-9-03 Q2): the chip counts deliveries.
An UNKNOWN row is not one: the list chip counts only the delivered rows and a
warning chip names the unknown ones; the history row reads
`⚠ RESULT UNKNOWN · CHECK <destination>` (the existing StateChip species, its
warning state). PHILO-10-04 (the owner's A2, 2026-09-29): the record word is
DELIVERY ×N / DELIVERY N, the same counts; a SENT row names its channel word
and proof (SAVED + the exact path).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _api_allow_error, _boot, _ensure_build, _settle
from .test_philo9_03_room_face_glass import FACTS, SIZES, T, WIDTHS, _delivery_time
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Room face glass needs Playwright")

TOKEN = "philo10-01-unknown-face"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-01-shots")
NAME = "Payments ledger cutover"
EXTRA = r"""() => {
  const text = (sel) => [...document.querySelectorAll(sel)].filter((e) => e.getBoundingClientRect().height > 0)
    .map((e) => e.innerText.replace(/\s+/g, ' ').trim());
  return {
    unknown_chips: text('[data-testid=update-unknown-chip]'),
    row_outcomes: [...document.querySelectorAll('[data-testid=delivery-row] [data-outcome]')]
      .map((e) => e.getAttribute('data-outcome')),
    row_lead_states: [...document.querySelectorAll('[data-testid=delivery-row] [data-outcome] .surface-state-chip')]
      .map((e) => e.getAttribute('data-state')),
  };
}"""


def _long_folder(root: Path) -> Path:
    """A folder the OS accepts whose path leaves no room for the send's file name."""
    limit = os.pathconf("/", "PC_PATH_MAX")
    folder = root.resolve()
    while len(str(folder)) < limit - 25:
        folder = folder / ("a" * min(100, limit - 25 - len(str(folder)) - 1 or 1))
    folder.mkdir(parents=True, exist_ok=True)
    return folder


class TestUnknownSendFace:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        _ensure_build()
        self.tmp = tmp_path
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.server, self.base = server, base
        try:
            yield
        finally:
            server.stop()

    def _open(self, pw: Any, width: int) -> tuple[Any, Any, list[str]]:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, device_scale_factor=1)
        page = ctx.new_page()
        page.set_default_timeout(45_000)
        errors: list[str] = []
        page.on("pageerror", lambda e: errors.append(str(e)[:200]))
        page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
        _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
        return browser, page, errors

    def _send(self, page: Any, uid: str, name: str, folder: Path) -> tuple[int, Any]:
        dest = _api(page, "POST", "/api/channels/destinations",
                    {"name": name, "channel": "file", "folder": str(folder)}, token=TOKEN)["destination"]["id"]
        send_id = _api(page, "POST", "/api/channels/sends", {"document_ref": f"project_update:{uid}", "destination_id": dest},
                       token=TOKEN)["send"]["id"]
        return _api_allow_error(page, "POST", "/api/channels/send", {"send_id": send_id}, token=TOKEN)

    def _shot(self, page: Any, name: str, width: int) -> None:
        page.mouse.move(1, 1)
        _settle(page)
        page.screenshot(path=str(SHOTS / f"{name}-{width}.png"))

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_an_unknown_send_is_never_shown_as_delivered(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser, page, errors = self._open(pw, width)
            try:
                pid = _api(page, "POST", "/api/projects", {"name": NAME}, token=TOKEN)["project"]["id"]
                uid = _api(page, "POST", f"/api/projects/{pid}/updates/draft", {"generator": "deterministic"},
                           token=TOKEN)["update"]["id"]
                # PHILO-15 B64: an update with no verified claim is refused; the owner's saved line is reviewed.
                _api(page, "PUT", f"/api/updates/{uid}", {"body_md": "## Progress\n\nThe ledger cutover is on track.\n"}, token=TOKEN)
                _api(page, "POST", f"/api/updates/{uid}/publish", {}, token=TOKEN)
                (self.tmp / "out").mkdir()
                ok_status, ok = self._send(page, uid, "Team folder", self.tmp / "out")
                bad_status, bad = self._send(page, uid, "Long path folder", _long_folder(self.tmp / "deep"))
                ups = _api(page, "GET", f"/api/projects/{pid}/updates", token=TOKEN)["updates"]
                hub = next(u for u in ups if u["id"] == uid)["deliveries"]
                # The real producer: one SENT, one UNKNOWN (no proof), both in the history.
                assert (ok_status, ok["send"]["state"]) == (200, "sent"), ok
                assert bad["send"]["state"] == "unknown" and not bad["send"].get("proof_json"), (bad_status, bad)
                assert [(d["delivered_to"], d["outcome"]) for d in hub] == [
                    ("Team folder", "sent"), ("Long path folder", "unknown")], hub

                page.evaluate("""([key, scope]) => sessionStorage.setItem('hs.desk.staged-surface-open',
                    JSON.stringify({key, scope}))""", ["open-project-memory", f"project:{pid}"])
                page.reload(wait_until="load")
                page.locator("[data-testid=room-body]").wait_for(timeout=T)
                page.wait_for_timeout(900)
                page.locator("[data-testid=updates-verb]").click()
                page.locator("[data-testid=update-list]").wait_for(timeout=T)
                page.wait_for_timeout(400)
                listed = {**page.evaluate(FACTS), **page.evaluate(EXTRA)}
                self._shot(page, "unknown-1-list", width)
                page.locator(f"[data-testid=update-list-item]:has([data-update-id='{uid}'])").first.click()
                page.locator("[data-testid=update-editor]").wait_for(timeout=T)
                page.locator("[data-testid=delivery-row]").nth(1).wait_for(timeout=T)
                page.wait_for_timeout(400)
                opened = {**page.evaluate(FACTS), **page.evaluate(EXTRA)}
                page.locator("[data-testid=delivery-row]").nth(1).scroll_into_view_if_needed()
                self._shot(page, "unknown-2-history", width)
                (SHOTS / f"unknown-send-{width}.json").write_text(json.dumps(
                    {"hub": hub, "listed": listed, "opened": opened}, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

                # The list: DELIVERED counts only the delivered row; the unknown one has its own chip.
                assert listed["delivered_chips"] == ["✓ DELIVERY ×1"], listed["delivered_chips"]
                assert listed["unknown_chips"] == ["⚠ RESULT UNKNOWN ×1"], listed["unknown_chips"]
                # The history: the head counts one delivery; the unknown row says so and names where to check.
                assert opened["delivery_head"] == "DELIVERY 1", opened["delivery_head"]
                assert opened["delivery_rows"] == [
                    f"✓ Team folder SAVED {ok['send']['proof']['path']} {_delivery_time(hub[0]['delivered_at'])}",
                    f"⚠ RESULT UNKNOWN · CHECK Long path folder FILE NOT CONFIRMED {_delivery_time(hub[1]['delivered_at'])}",
                ], opened["delivery_rows"]
                assert opened["row_outcomes"] == ["sent", "unknown"], opened["row_outcomes"]
                assert opened["row_lead_states"] == ["success", "warning"], opened["row_lead_states"]
                for facts in (listed, opened):
                    assert not facts["h_overflow"] and facts["small_text_count"] == 0, facts["small_text"]
                    assert facts["raw_buttons"] == [] and not facts["modal"], facts["raw_buttons"]
                assert not errors, errors
            finally:
                browser.close()
