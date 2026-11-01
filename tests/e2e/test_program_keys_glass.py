"""The Program window, AS RENDERED: the one thing only a real browser proves.

PG-REQ (docs/internal/betterment/programs/PROGRAMS-REQUIREMENTS-2026-10-31.md
§8, REQ12): Alt+↑ and Alt+↓ move the selected Planned step, through the real
hub on an isolated HOME at 1440 x 900. The keys go to the window from the
selected step's row (focus, keys); the order comes back from the hub
(``PATCH /api/programs/{id}/steps/{sid}`` with ``before``), and the board
draws it. Every other face of the requirements and the adjust verbs is T2
(web/src/desk/programs/__tests__/programs.app.test.tsx, from recorded
answers); fit, clip and the 12 px floor are the desk sweep's ``program`` case.
"""

from __future__ import annotations

import subprocess
import urllib.parse
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Program glass needs Playwright")

pytestmark = [pytest.mark.e2e]

TOKEN = "program-keys-glass"
SHOTS = evidence_dir("program-keys")
T = 20_000


def _titles(page: Any, wid: str) -> list[str]:
    return page.locator(f'[id="{wid}"] [data-testid=programs-step] .pg-step-name').all_inner_texts()


def test_alt_arrows_move_the_selected_planned_step_and_the_board_follows_the_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    repo = tmp_path / "program-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=Glass", "-c", "user.email=glass@example.com",
                    "commit", "-q", "--allow-empty", "-m", "start"], check=True)
    # Start's precheck: the push needs a remote (a bare one here).
    subprocess.run(["git", "init", "-q", "--bare", str(tmp_path / "program-repo-origin.git")], check=True)
    subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(tmp_path / "program-repo-origin.git")], check=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1, reduced_motion="reduce")
            page = ctx.new_page()
            page.set_default_timeout(45_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                made = _api(page, "POST", "/api/programs", {
                    "title": "The keys", "repository": str(repo), "template": "fast-cycle", "check_command": "true"}, token=TOKEN)
                pid = str(made.get("id") or (made.get("program") or {}).get("id"))
                _api(page, "POST", f"/api/programs/{pid}/plan", {"replace": True, "steps": [
                    {"title": "Indexes", "brief": "Index the scans."},
                    {"title": "Retention", "brief": "Prune the receipts."},
                    {"title": "The fan-out", "brief": "One read for the desk."},
                ]}, token=TOKEN)
                # Started, with the runner off (HOLDSPEAK_PROGRAMS=off): the steps
                # stay Ready and Planned, so each may move.
                _api(page, "POST", f"/api/programs/{pid}/start", {}, token=TOKEN)
                _api(page, "POST", f"/api/desk/windows/{urllib.parse.quote('pullout:program:' + pid, safe='')}/open", {}, token=TOKEN)
                page.goto(f"{base}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)
                wid = f"pullout:program:{pid}"
                page.locator(f'[id="{wid}"] [data-testid=programs-board]').wait_for(timeout=T)
                assert _titles(page, wid) == ["Indexes", "Retention", "The fan-out"]

                third = page.locator(f'[id="{wid}"] [data-testid=programs-step]').nth(2).get_by_test_id("programs-step-select")
                third.click()
                page.locator(f'[id="{wid}"] [data-testid=programs-step-fold]').wait_for(timeout=T)
                with page.expect_response(lambda r: "/steps/" in r.url and r.request.method == "PATCH") as moved:
                    page.keyboard.press("Alt+ArrowUp")
                assert moved.value.ok, moved.value.text()
                page.wait_for_function(
                    """wid => [...document.querySelectorAll(`[id="${wid}"] [data-testid=programs-step] .pg-step-name`)]
                      .map(n => n.textContent).join("|") === "Indexes|The fan-out|Retention" """, arg=wid, timeout=T)
                # The moved step stays selected and keeps the focus: Alt+↓ takes it back.
                assert page.evaluate("() => document.activeElement?.closest('[data-testid=programs-step]')?.textContent || ''").find("The fan-out") >= 0
                with page.expect_response(lambda r: "/steps/" in r.url and r.request.method == "PATCH") as back:
                    page.keyboard.press("Alt+ArrowDown")
                assert back.value.ok, back.value.text()
                page.wait_for_function(
                    """wid => [...document.querySelectorAll(`[id="${wid}"] [data-testid=programs-step] .pg-step-name`)]
                      .map(n => n.textContent).join("|") === "Indexes|Retention|The fan-out" """, arg=wid, timeout=T)
                # In a text well the keys are the well's: nothing moves.
                title = page.locator(f'[id="{wid}"] [data-testid=programs-step-brief] input').first
                title.focus()
                page.keyboard.press("Alt+ArrowUp")
                page.wait_for_timeout(300)
                assert _titles(page, wid) == ["Indexes", "Retention", "The fan-out"]
                page.screenshot(path=str(SHOTS / "alt-arrows-1440.png"))
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.stop()
