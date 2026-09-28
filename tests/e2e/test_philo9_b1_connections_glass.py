"""PHILO-9-02 B1 -- the Connections face reads each row's own check age, AS RENDERED.

The real hub (isolated HOME and database) with the REAL adapters; the only
seam is their subprocess runner (a canned ``gh`` / ``acli``). The rig:

* GitHub probed once through ``POST /api/connections/github/recheck``
  (stored now: "Connected · Checked now");
* Jira row ``alpha`` added and probed through the real routes, its stored
  check then set two hours back in the database (a data seed of a time, so
  two rows show two different ages: "Connected · Checked 2 h ago");
* Jira row ``beta`` added and never probed ("Never checked");
* Confluence: no row, never probed ("Never checked").

At 1440 and 393 the fence reads each card's state chip: the words are there,
visible, and the chip stays inside its card and the viewport. The page makes
no ``gh`` / ``acli`` call while it loads (the list is a cached read).

Red on main: the list probes on every read and stamps the read time; the
chips carry no age ("Connected"), the unchecked row reads "Sign in", and the
empty Confluence card reads "Not set up".
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _settle
from .test_hs168_connections_glass import TOKEN, _navigate_to_connections
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the Connections glass needs Playwright")

SHOTS = evidence_dir(
    "pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/assets/story-02-shots"
)
EMAIL = "owner@example.com"
ALPHA, BETA = "alpha.atlassian.net", "beta.atlassian.net"


class CountingRunner:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        if argv[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(
                argv, 0, stdout="Logged in to github.com account karol-test (keyring)\n", stderr="")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "switch"]:
            return subprocess.CompletedProcess(argv, 0, stdout="switched\n", stderr="")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "status"]:
            site = argv[argv.index("--site") + 1] if "--site" in argv else ALPHA
            return subprocess.CompletedProcess(
                argv, 0, stdout=f"✓ Authenticated\n  Site: {site}\n  Email: {EMAIL}\n", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected")


_CHIP_JS = """(card) => {
  const chip = card.querySelector('.surface-state-chip');
  if (!chip) return null;
  const r = chip.getBoundingClientRect(), c = card.getBoundingClientRect();
  const style = getComputedStyle(chip);
  return {
    text: chip.textContent.slice((chip.querySelector('.surface-state-chip-icon')?.textContent || '').length).trim(),
    visible: style.visibility !== 'hidden' && style.display !== 'none' && r.width > 0,
    insideCard: r.left >= c.left - 0.5 && r.right <= c.right + 0.5,
    insideViewport: r.left >= 0 && r.right <= window.innerWidth,
  };
}"""


def _chip(page: Any, testid: str) -> dict[str, Any]:
    card = page.locator(f'[data-testid="{testid}"]')
    card.first.wait_for(state="visible", timeout=10_000)
    card.first.scroll_into_view_if_needed()
    info = card.first.evaluate(_CHIP_JS)
    assert info is not None, f"{testid}: no state chip"
    return info


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_each_card_shows_its_own_age(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    _ensure_build()
    from playwright.sync_api import sync_playwright

    gh, acli = CountingRunner(), CountingRunner()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=gh, acli_runner=acli)
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 1100})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")

            _api(page, "POST", "/api/connections/github/recheck", token=TOKEN)
            for site in (ALPHA, BETA):
                _api(page, "POST", "/api/providers/jira/connections",
                     {"site": site, "email": EMAIL}, token=TOKEN)
            _api(page, "POST", f"/api/providers/jira/connections/{ALPHA}%7C{EMAIL}/recheck", token=TOKEN)

            from holdspeak.db import get_database
            two_hours = (datetime.now(timezone.utc) - timedelta(hours=2, minutes=5)).isoformat()
            get_database().automations.update_provider_connection(
                f"wpc_jira_{ALPHA}|{EMAIL}", last_checked_at=two_hours)

            gh.calls.clear()
            acli.calls.clear()
            _navigate_to_connections(page, url)
            page.wait_for_selector('[data-testid="connections-github"]', timeout=10_000)
            _settle(page)

            chips = {
                "connections-github": "Connected · Checked now",
                f"connections-jira-conn-{ALPHA}|{EMAIL}": "Connected · Checked 2 h ago",
                f"connections-jira-conn-{BETA}|{EMAIL}": "Never checked",
                "connections-confluence": "Never checked",
            }
            for testid, want in chips.items():
                info = _chip(page, testid)
                assert info["text"] == want, f"{testid}: {info['text']!r} != {want!r}"
                assert info["visible"], f"{testid}: chip not visible"
                assert info["insideCard"], f"{testid}: chip leaves its card at {width}"
                assert info["insideViewport"], f"{testid}: chip leaves the viewport at {width}"

            # Calendar and Models: local reads, no age.
            assert _chip(page, "connections-calendar")["text"] == "Not set up"
            assert "Checked" not in _chip(page, "connections-models")["text"]

            assert gh.calls == [] and acli.calls == [], (gh.calls, acli.calls)

            page.locator('[data-testid="connections-github"]').first.evaluate(
                "el => el.scrollIntoView({block: 'start'})")
            _settle(page)
            suffix = "desktop" if width == 1440 else "phone"
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / f"b1-connections-{suffix}.png"), full_page=True)
            browser.close()
    finally:
        server.stop()

    assert not errors, f"Page errors: {errors}"


# ── Codex Astra r1 finding 7: the empty Jira card says its own state ─────


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
@pytest.mark.parametrize("acli", ["present", "absent"])
def test_the_empty_jira_card_shows_its_own_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                 width: int, acli: str) -> None:
    """No Jira row: the card's chip is the tool's own state, never a hardcoded "Not set up".

    ``acli`` on PATH (a local ``shutil.which``, no subprocess): "Never checked";
    missing: "acli missing". Red at 24576f25: "Not set up" in both branches.
    """
    import shutil

    _ensure_build()
    from playwright.sync_api import sync_playwright

    real_which = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name, *a, **k: (
        ("/usr/local/bin/acli" if acli == "present" else None) if name == "acli" else real_which(name, *a, **k)))
    gh, runner = CountingRunner(), CountingRunner()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=gh, acli_runner=runner)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 1100})
            page.emulate_media(reduced_motion="reduce")
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _navigate_to_connections(page, url)
            _settle(page)
            info = _chip(page, "connections-jira")
            want = "Never checked" if acli == "present" else "acli missing"
            assert info["text"] == want, f"{info['text']!r} != {want!r}"
            assert info["visible"] and info["insideCard"] and info["insideViewport"], info
            suffix = "desktop" if width == 1440 else "phone"
            SHOTS.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(SHOTS / f"b1-jira-empty-{acli}-{suffix}.png"), full_page=True)
            browser.close()
    finally:
        server.stop()
