"""Search (⌘K) on real glass: what only a real browser proves (the test diet).

Betterment Q3 ("Search asks"), RECON step 27: on the phone a tap on a memory
row did nothing. Here a real finger tap (Playwright touch, 393) on a memory
row opens its object: the meeting "Ledger cutover sync", found in its
transcript, opens. The rows' order, their plain words and the Ask row are vitest's
(web/src/desk/components/__tests__/search.app.test.tsx); the hub's plain
snippets are tests/unit/test_desk_search.py.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle, clear_hub_windows

pytest.importorskip("playwright.sync_api", reason="the search glass needs Playwright")

pytestmark = [pytest.mark.e2e]

REPO = Path(__file__).resolve().parents[2]
TOKEN = "search-glass"
T = 30_000


def _seed() -> None:
    from holdspeak.db import get_database

    sys.path.insert(0, str(REPO / "tests" / "unit"))
    import test_desk_needs_you as seeds

    db = get_database()
    seeds._seed_honest_faces(SimpleNamespace(db=db))
    threads = db.threads
    thread = threads.create_thread(title="Why the freeze?")
    asked = threads.append_message(thread.id, role="user")
    threads.append_part(asked.id, kind="text", text="Why the freeze?")
    threads.complete_message(asked.id)
    said = threads.append_message(thread.id, role="assistant", parent_id=asked.id)
    threads.append_part(said.id, kind="text", text="We freeze the old ledger on Nov 5 to stop dual-write drift.")
    threads.complete_message(said.id)


@pytest.fixture
def phone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from playwright.sync_api import sync_playwright

    keyfile = tmp_path / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    _seed()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 393, "height": 852}, device_scale_factor=1,
                                      has_touch=True, is_mobile=True)
            page = ctx.new_page()
            page.set_default_timeout(T)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            clear_hub_windows(page, TOKEN)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            yield page
            browser.close()
    finally:
        server.stop()


def test_a_tap_on_a_memory_row_opens_it_on_the_phone(phone: Any) -> None:
    page = phone
    page.locator(".desk-tools-launch").first.tap()
    box = page.get_by_role("combobox", name="Search tools and Desk items")
    box.fill("Why the freeze")
    rows = page.locator("#desk-tool-shelf [role=option]")
    # A memory row: the transcript line of a meeting the query's title does not name.
    row = rows.filter(has_text="Ledger cutover sync").filter(has=page.locator(".desk-deck-hit"))
    row.first.wait_for()
    # The Ask row is first: the text reads like a question.
    assert rows.first.inner_text().startswith("✦")
    row.first.tap()
    page.locator("#desk-tool-shelf").wait_for(state="detached")
    page.locator(".desk-window").filter(has_text="Ledger cutover sync").filter(has_text="Outcomes").first.wait_for()
