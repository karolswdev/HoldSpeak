"""Settings ▸ Reach ▸ Telegram on glass: what only a browser can show.

The pane's behaviour is proved in ``web/src/desk/reach/__tests__/reach.app.test.tsx``
from the hub's recorded answers. Here, with the same recordings: the egress
line is one line at 900, the pane fits its window at 900 × 600 and at 393 in
every state, and a question opens with the focus on Cancel. It also takes the
shots of every state (``.tmp/evidence-shots/telegram-face/``).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot, _ensure_build, clear_hub_windows_http
from .test_settings_os_grammar_glass import _bounded
from .test_settings_page_glass import TOKEN, _open_page

pytestmark = pytest.mark.e2e

ROOT = Path(__file__).resolve().parents[2]
RECORDED = ROOT / "web/src/desk/reach/__fixtures__"
SHOTS = ROOT / ".tmp/evidence-shots/telegram-face"
STATES = (
    ("not-set-up", "reach.unpaired.json", "not_set_up"),
    ("token-unchecked", "reach.token_unchecked.json", "token_unchecked"),
    ("token-checked", "reach.token_checked.json", "token_checked"),
    ("code-live", "reach.pairing_open.json", "code_live"),
    ("connected", "reach.paired.json", "connected"),
    ("test-sent", "reach.test_sent.json", "connected"),
    ("test-answered", "reach.tested.json", "connected"),
    ("token-revoked", "reach.token_revoked.json", "token_revoked"),
    ("bot-blocked", "reach.bot_blocked.json", "bot_blocked"),
    ("another-desk", "reach.another_desk.json", "another_desk"),
    ("unreachable", "reach.unreachable.json", "unreachable"),
    ("keystore-locked", "reach.keystore_locked.json", "keystore_locked"),
)


def _recorded(name: str) -> Any:
    return json.loads((RECORDED / name).read_text())


def test_telegram_setup_fits_and_asks_in_the_window(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    SHOTS.mkdir(parents=True, exist_ok=True)
    # A code is open for ten minutes: the recorded expiry is a past time, so
    # only that time field moves (the rest is the hub's own answer).
    soon = (datetime.now(timezone.utc) + timedelta(minutes=9, seconds=40)).isoformat()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (1440, 393):
                clear_hub_windows_http(base, TOKEN)
                page = browser.new_page(viewport={"width": width, "height": 900 if width == 1440 else 852},
                                        reduced_motion="reduce")
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                answer: dict[str, Any] = {"reach": _recorded("reach.unpaired.json")}
                page.route("**/api/reach", lambda route: route.fulfill(json=answer["reach"]))
                pairing = {**_recorded("reach.pairing.json"), "expires_at": soon}
                page.route("**/api/reach/telegram/pair", lambda route: route.fulfill(status=201, json=pairing))
                suffix = "900" if width == 1440 else "393"
                for state, recording, said in STATES:
                    recorded = _recorded(recording)
                    if state == "code-live":
                        recorded["channels"]["telegram"]["pairing"]["expires_at"] = soon
                    answer["reach"] = recorded
                    _open_page(page, base)
                    window = page.locator("#surface-settings")
                    window.get_by_test_id("settings-index-notices").click()
                    pane = window.get_by_test_id("reach-telegram")
                    expect(pane).to_be_visible()
                    expect(pane).to_have_attribute("data-state", said)
                    if state == "code-live":
                        # His press of New code answers with the code: the fallback row shows.
                        pane.get_by_test_id("reach-new-code").click()
                        expect(pane.get_by_test_id("reach-pair-code")).to_have_text("/pair 482 913")
                        expect(pane.get_by_test_id("reach-open-bot")).to_be_visible()
                    egress = pane.get_by_test_id("reach-egress")
                    if egress.count():
                        lines = egress.evaluate("el => new Set([...el.getClientRects()].map(r => Math.round(r.top))).size")
                        if width == 1440:
                            assert lines == 1, f"{state}: the egress line wraps to {lines} lines at 900"
                    _bounded(window)
                    assert pane.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), f"{state}-{suffix}: the pane is wider than its seat"
                    page.screenshot(path=str(SHOTS / f"{state}-{suffix}.png"))
                    if state == "connected":
                        for verb, question, name in (("reach-unpair", "reach-disconnect-question", "disconnect-question"),
                                                     ("reach-remove", "reach-remove-question", "remove-question")):
                            pane.get_by_test_id(verb).click()
                            asked = pane.get_by_test_id(question)
                            expect(asked).to_be_visible()
                            expect(asked.get_by_role("button", name="Cancel", exact=True)).to_be_focused()
                            _bounded(window)
                            page.screenshot(path=str(SHOTS / f"{name}-{suffix}.png"))
                            asked.get_by_role("button", name="Cancel", exact=True).click()
                            expect(asked).to_have_count(0)
                assert not errors, errors
                page.close()
            browser.close()
    finally:
        server.stop()
