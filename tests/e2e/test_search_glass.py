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
from tests._evidence import evidence_dir

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
    box = page.get_by_role("combobox", name="Find, open or ask")
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


@pytest.fixture(params=[1440, 393], ids=["desktop", "phone"])
def people_face(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    """A real People producer plus the Desk membership read used by Screen."""
    from playwright.sync_api import sync_playwright

    width = int(request.param)
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
            ctx = browser.new_context(
                viewport={"width": width, "height": 900 if width == 1440 else 852},
                device_scale_factor=1,
                has_touch=width < 720,
                is_mobile=width < 720,
                reduced_motion="reduce",
            )
            page = ctx.new_page()
            page.set_default_timeout(T)
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _api(page, "POST", "/api/people/setup", {}, token=TOKEN)
            created = _api(page, "POST", "/api/people/relationships", {
                "display_name": "Mira Okafor",
                "relationship_kind": "direct_report",
            }, token=TOKEN)
            person_id = str(created["relationship"]["id"])
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            yield page, base, width, person_id
            browser.close()
    finally:
        server.stop()


def _read_membership(page: Any, person_id: str) -> list[str]:
    directory = _api(page, "GET", "/api/directories/hs-seed-desk", token=TOKEN)
    return [str(ref) for ref in directory.get("member_ids", []) if ref]


def test_search_people_prep_ask_and_keep_remove_on_real_desk(people_face: Any) -> None:
    """The real People and directory producers drive Search and Screen."""
    page, _base, width, person_id = people_face
    shots = evidence_dir("s5-search")
    shots.mkdir(parents=True, exist_ok=True)
    person = f"people:{person_id}"

    # Search opens Mira from the real relationship producer and Cmd+Enter
    # carries the exact protected ref into the existing About surface.
    page.locator(".desk-tools-launch").first.click()
    field = page.get_by_role("combobox", name="Find, open or ask")
    field.fill("Mira")
    row = page.locator(f'[id="desk-palette-option-{person}"]')
    row.wait_for()
    assert row.get_attribute("aria-selected") == "true"
    field.press("Meta+Enter")
    about = page.get_by_test_id("ask-context")
    about.wait_for()
    # The chip is seeded with the exact protected ref. Its compact label is
    # intentionally "This person" until the person window supplies a name;
    # opening that chip proves the ref itself is carried into About.
    chip = about.get_by_test_id("ask-about-chip")
    chip.get_by_role("button", name="This person", exact=True).click()
    page.locator(f'[id="pullout:{person}"]').wait_for(timeout=T)
    page.screenshot(path=str(shots / f"search-mira-cmdenter-{width}.png"))
    # On the phone the newly opened Person pane owns the compact Back button;
    # close through the same hub window producer at both widths before the
    # keyboard verb walk.
    clear_hub_windows(page, TOKEN)
    page.reload(wait_until="load")
    _normal_chair(page)
    _settle(page)

    # ⌘K "mi", Right, Down, Enter follows the selected person's live verb
    # list to Prep 1:1. The first two object verbs remain keyboard reachable;
    # the third Down lands on Prep after Open and Ask.
    page.locator(".desk-tools-launch").first.click()
    field = page.get_by_role("combobox", name="Find, open or ask")
    field.fill("mi")
    row.wait_for()
    field.press("ArrowRight")
    field.press("ArrowDown")
    field.press("ArrowDown")
    field.press("ArrowDown")
    field.press("Enter")
    page.locator(f'[id="pullout:{person}"] [data-testid="people-prep-lens"]').wait_for(timeout=T)
    page.screenshot(path=str(shots / f"search-mira-prep-{width}.png"))
    clear_hub_windows(page, TOKEN)
    page.reload(wait_until="load")
    _normal_chair(page)
    _settle(page)

    # The same row owns its live object verbs. Keep writes the canonical Desk
    # membership, which the Screen member read then renders as a person tile.
    page.locator(".desk-tools-launch").first.click()
    field = page.get_by_role("combobox", name="Find, open or ask")
    field.fill("Mira")
    row.wait_for()
    page.get_by_role("button", name="Open actions for Mira Okafor", exact=True).click()
    page.get_by_role("group", name="Actions for Mira Okafor", exact=True).get_by_role(
        "option", name="Keep on desk Do", exact=True,
    ).click()
    for _ in range(20):
        if person in _read_membership(page, person_id):
            break
        page.wait_for_timeout(250)
    assert person in _read_membership(page, person_id)

    page.reload(wait_until="load")
    _normal_chair(page)
    screen_person = page.locator(f'[data-object-id="{person}"]')
    screen_person.wait_for(timeout=T)
    if width < 720:
        bounds = screen_person.bounding_box()
        assert bounds
        x, y = bounds["x"] + bounds["width"] / 2, bounds["y"] + bounds["height"] / 2
        touch = page.context.new_cdp_session(page)
        touch.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y, "id": 1}]})
        page.wait_for_timeout(750)
        touch.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        touch.detach()
    else:
        screen_person.click(button="right")
    menu = page.get_by_role("menu", name="Mira Okafor menu", exact=True)
    menu.get_by_role("menuitem", name="Remove from desk", exact=True).click()
    for _ in range(20):
        if person not in _read_membership(page, person_id):
            break
        page.wait_for_timeout(250)
    assert person not in _read_membership(page, person_id)
    page.screenshot(path=str(shots / f"person-remove-from-desk-{width}.png"))
