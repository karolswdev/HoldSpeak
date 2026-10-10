"""The Floor list on the real hub, at 1440 and 393: select, Get Info, Rename, Filed.

Inventory 2026-10-03 (defect 8) and Astra's review of PR #794.

- PHILO-14 A2: the list is the ObjectList species. A real pointer press on
  the row (its name, its kind cell, its edges) selects it into the Ask
  context and does not open; a second press clears it; a double press or
  Enter opens. There is no `[ ]` / `[x]` mark: the selection is the row.
- Get Info opens for a decision and a thread; Rename persists on the hub
  (decision by `title` over PUT, thread by `title` over PATCH).
- A Filed zone in Get Info dives into that zone (the list has no zone windows).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from .glass_infra import _api, _boot, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="Floor list glass needs Playwright")

TOKEN = "floor-list-glass"
ROW = ".desk-list-sortable .object-list-row"
NAME = ".object-list-open"


def _row(page, title: str):
    return page.locator(ROW).filter(has=page.locator(".object-list-name-word", has_text=title)).first


def _selected(page) -> list[str]:
    return page.locator(f"{ROW}[aria-selected='true'] .object-list-name-word").evaluate_all(
        "els => els.map(e => e.textContent)")


def _info_for(page, title: str):
    row = _row(page, title)
    row.evaluate("e => e.scrollIntoView({block: 'center'})")
    row.locator(NAME).click(button="right")
    page.get_by_role("menuitem", name="Get Info").click()
    info = page.locator(".desk-info-window").last
    info.wait_for(timeout=5_000)
    return info


def _rename(page, info, new_name: str) -> None:
    info.get_by_title("Rename").click()
    field = info.get_by_role("textbox", name="Name")
    field.fill(new_name)
    field.press("Enter")


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_select_get_info_rename_and_filed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int
) -> None:
    from playwright.sync_api import sync_playwright

    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    phone = width < 600
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_context(
                viewport={"width": width, "height": height}, has_touch=phone, is_mobile=phone,
            ).new_page()
            page.emulate_media(reduced_motion="reduce")
            errors: list[str] = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.goto(f"{base}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            note = _api(page, "POST", "/api/notes", {"title": "Rollout risks", "body_markdown": "x"}, token=TOKEN)["note"]
            decision = _api(page, "POST", "/api/decisions", {"title": "Freeze the old ledger"}, token=TOKEN)["decision"]
            thread = _api(page, "POST", "/api/threads", {"title": "Cutover thread"}, token=TOKEN)
            thread_id = (thread.get("thread") or thread)["id"]
            zone = _api(page, "POST", "/api/directories", {"name": "Launch"}, token=TOKEN)["directory"]
            _api(page, "PUT", f"/api/directories/{zone['id']}/members/note:{note['id']}", {}, token=TOKEN)
            page.goto(f"{base}/?token={TOKEN}&view=list", wait_until="load")
            _normal_chair(page)
            page.get_by_role("button", name="Floor").first.click()
            page.locator(".desk-list-sortable").wait_for(timeout=20_000)
            _settle(page)

            # ── 1. real pointer hits ─────────────────────────────────
            row = _row(page, "Freeze the old ledger")
            centre = "e => e.scrollIntoView({block: 'center'})"  # clear of the bars at the foot
            row.evaluate(centre)
            box = row.bounding_box()
            assert box and box["height"] >= 44, box
            assert "[x]" not in page.locator(".desk-listmode").inner_text()
            assert "[ ]" not in page.locator(".desk-listmode").inner_text()
            kind = row.locator("[data-col='kind']")
            kb = kind.bounding_box() if kind.is_visible() else None
            points = [
                (box["x"] + 60, box["y"] + box["height"] / 2),
                (box["x"] + box["width"] / 2, box["y"] + 3),
                (box["x"] + box["width"] / 2, box["y"] + box["height"] - 3),
            ] + ([(kb["x"] + min(12, kb["width"] / 2), kb["y"] + kb["height"] / 2)] if kb else [])
            press = page.touchscreen.tap if phone else page.mouse.click
            want = True
            for x, y in points:
                press(x, y)
                page.wait_for_timeout(350)  # past the double-press window
                assert (_selected(page) == ["Freeze the old ledger"]) is want, (x, y, _selected(page))
                assert page.locator(".desk-pullout").count() == 0, f"a press on the row at {(x, y)} opened it"
                want = not want
            if _selected(page):
                press(*points[0])
                page.wait_for_timeout(350)
            assert _selected(page) == []

            # Enter (and a double press) opens the row.
            row.locator(NAME).focus()
            page.keyboard.press("Enter")
            page.locator(".desk-pullout").first.wait_for(timeout=5_000)
            for _ in range(3):
                if page.locator(".desk-pullout").count() == 0:
                    break
                close = page.locator(".desk-pullout").first.get_by_role("button", name="Close").first
                close.click() if close.count() else page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            assert page.locator(".desk-pullout").count() == 0, "the opened window did not close"

            # ── 2. Get Info + Rename, persisted on the hub ───────────
            info = _info_for(page, "Freeze the old ledger")
            _rename(page, info, "Freeze on Nov 6")
            page.wait_for_function(
                "(t) => [...document.querySelectorAll('.object-list-name-word')].some(e => e.textContent.includes(t))",
                arg="Freeze on Nov 6", timeout=5_000)
            page.wait_for_timeout(500)
            got = _api(page, "GET", f"/api/decisions/{decision['id']}", token=TOKEN)
            assert (got.get("decision") or got)["title"] == "Freeze on Nov 6"
            page.keyboard.press("Escape")
            if page.locator(".desk-info-window").count():
                page.locator(".desk-info-window").last.get_by_role("button", name="Close").first.click()

            info = _info_for(page, "Cutover thread")
            _rename(page, info, "Cutover talk")
            page.wait_for_timeout(800)
            got = _api(page, "GET", f"/api/threads/{thread_id}", token=TOKEN)
            assert (got.get("thread") or got)["title"] == "Cutover talk"
            if page.locator(".desk-info-window").count():
                page.locator(".desk-info-window").last.get_by_role("button", name="Close").first.click()

            # ── 3. a Filed zone dives ────────────────────────────────
            info = _info_for(page, "Rollout risks")
            info.get_by_role("button", name="Launch").click()
            page.wait_for_timeout(600)
            assert page.locator(".desk-info-window").count() == 0
            titles = page.locator(f"{ROW} .object-list-name-word").all_inner_texts()
            assert len(titles) == 1 and "Rollout risks" in titles[0], titles
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
