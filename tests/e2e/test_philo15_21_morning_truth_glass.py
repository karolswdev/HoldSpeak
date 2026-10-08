"""PHILO-15 lane 21 (B60, B61, B69, B74): the second morning, as rendered
(1440 and 393).

Rehearsal 2 at 07:05: "3 need you", two of them STALE source rows that
HoldSpeak caused itself (the Heartbeat sweep was held by quiet hours), Retry
only reloaded the list, and the Room read "ON TRACK · CHECKED 10H AGO" with a
next check in the past.

This rig makes that morning on a fresh HOME on any clock: quiet hours that
hold NOW (began 8 hours ago), a GitHub Watch checked 10 hours ago (fresh when
quiet hours began) and a meeting Watch checked 20 hours ago (late before
them). The real Heartbeat sweep runs and is held. Then the faces:

* Needs you: the GitHub row reads QUIET UNTIL <end> and is not counted; the
  meeting row reads STALE, is counted, and its Retry re-checks it through the
  hub's single-Watch route and leaves a receipt.
* The Room head reads QUIET UNTIL <end>, never a next check in the past.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the morning glass needs Playwright")

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(600, method="thread")]

TOKEN = "philo15-21-morning"
SHOTS = evidence_dir("docs/internal/philo/phase-15/21-shots")
SIZES = {1440: 900, 393: 852}
PROJECT = "prj-hygiene"
REPO = "karolswdev/holdspeak-dayone-rehearsal-1558"


def _naive_utc(delta: timedelta) -> str:
    return (datetime.now(timezone.utc).replace(tzinfo=None) - delta).isoformat(timespec="seconds")


def _the_second_morning() -> str:
    """The rehearsal's sources, then the real Heartbeat sweep (held).
    Returns the quiet end as the face prints it (HH:MM, local)."""
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.heartbeat_service import HeartbeatService

    db = get_database()
    db.projects.create_project(project_id=PROJECT, name="Rehearsal repo hygiene")
    due = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(timespec="seconds")
    with db._connection() as conn:
        for wid, connector, kind, query, checked in (
            ("w-gh", "gh", "pull_requests", {"repository": REPO}, timedelta(hours=10)),
            ("w-mtg", "meeting", "meetings", {"project_id": PROJECT}, timedelta(hours=20)),
        ):
            conn.execute(
                "INSERT INTO connector_watches "
                "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, state, "
                " last_success_at, next_evaluation_at, project_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, '[]', 1, 'active', ?, ?, ?, datetime('now'), datetime('now'))",
                (wid, connector, kind, f"{connector} watch", json.dumps(query),
                 _naive_utc(checked), due, PROJECT),
            )
    hour = datetime.now().astimezone().hour
    hb = HeartbeatService(db)
    hb.update_settings({"quiet_hours": {"start": (hour - 8) % 24, "end": (hour + 2) % 24}})
    receipt = hb.run_sweep(Principal(PrincipalKind.OWNER, "heartbeat-conductor"))
    assert receipt["held"] is True and receipt["quiet_hold"]["sources"] == 2, receipt
    end = datetime.fromisoformat(receipt["quiet_hold"]["until"]).astimezone()
    return f"{end:%H:%M}"


def _shell(page: Any, name: str) -> Any:
    return page.locator(f".desk-window-shell.chair-window[aria-label='{name}']")


def _press(page: Any, loc: Any, width: int) -> None:
    loc.first.wait_for()
    if width < 720:
        loc.first.tap()
    else:
        loc.first.click()
    page.wait_for_timeout(300)


def _menu_pick(page: Any, width: int, name: str) -> None:
    if width < 720:
        _press(page, page.locator(".desk-verbbar-item[data-menu-id='go'] button"), width)
    else:
        _press(page, page.locator(".desk-verbbar-item[data-menu-id='window'] button"), width)
        page.locator(".desk-verbbar-menu [role='menuitem']:has-text('Chair')").hover()
    _press(page, page.locator(f".desk-menu-list [role='menuitemcheckbox']:has-text('{name}')"), width)


class TestTheSecondMorning:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        keyfile = tmp_path / "people.key"
        keyfile.write_text("{}")
        keyfile.chmod(0o600)
        monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
        _ensure_build()
        server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
        self.base = base
        self.quiet_end = _the_second_morning()
        try:
            yield
        finally:
            server.stop()

    def _stage(self, page: Any, key: str, scope: str) -> None:
        page.evaluate("""([key, scope]) => sessionStorage.setItem("hs.desk.staged-surface-open",
            JSON.stringify({key, scope}))""", [key, scope])
        page.reload(wait_until="load")
        _normal_chair(page)

    @pytest.mark.parametrize("width", list(SIZES))
    def test_needs_you_and_the_room_at_seven(self, width: int) -> None:
        from playwright.sync_api import sync_playwright

        quiet = f"QUIET UNTIL {self.quiet_end}"
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]},
                                      device_scale_factor=1, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            try:
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
                _normal_chair(page)
                page.locator("[data-testid=desk-screen]").wait_for()

                # B60 + B74: Needs you at seven.
                _menu_pick(page, width, "Needs you")
                needs = _shell(page, "Needs you")
                needs.get_by_test_id("needs-drawer").wait_for()
                sources = needs.get_by_test_id("needs-source-row")
                sources.first.wait_for()
                gh = sources.filter(has_text="GitHub")
                mtg = sources.filter(has_text="Meetings")
                gh.wait_for()
                mtg.wait_for()
                assert quiet in gh.inner_text(), gh.inner_text()
                assert f"GitHub · {REPO}" in gh.inner_text()
                assert gh.get_attribute("data-counted") == "false"
                assert "STALE" in mtg.inner_text() and mtg.get_attribute("data-counted") == "true"
                assert "observed yesterday" in mtg.inner_text() or "observed " in mtg.inner_text()
                head = needs.get_by_test_id("arrival-display").inner_text().strip()
                counted = needs.locator("[data-testid='needs-list'] li.needs-row[data-counted='true']").count()
                assert head.startswith(f"{counted} "), (head, counted)
                _settle(page)
                page.screenshot(path=str(SHOTS / f"21-needs-quiet-{width}.png"))

                # B61: Retry re-checks THAT source and leaves a receipt.
                _press(page, mtg.get_by_role("button", name="Retry: Meetings"), width)
                receipt = needs.get_by_test_id("needs-source-receipt")
                receipt.wait_for()
                assert receipt.inner_text().startswith("CHECKED · Meetings · "), receipt.inner_text()
                page.wait_for_function(
                    """() => ![...document.querySelectorAll("[data-testid='needs-source-row']")]
                        .some((li) => li.textContent.includes("Meetings"))""")
                _settle(page)
                page.screenshot(path=str(SHOTS / f"21-needs-retry-{width}.png"))

                # B69: the Room head says the same: QUIET UNTIL, no past next check.
                self._stage(page, "open-project-memory", f"project:{PROJECT}")
                page.locator("[data-testid=room-body]").wait_for()
                word = page.get_by_test_id("room-sources-word")
                word.wait_for()
                assert word.inner_text().strip() == quiet, word.inner_text()
                assert "ON TRACK · CHECKED" not in page.get_by_test_id("room-head").inner_text()
                empty = page.get_by_test_id("needs-you-empty")
                if empty.count():
                    assert f"quiet until {self.quiet_end}" in empty.inner_text(), empty.inner_text()
                _settle(page)
                page.screenshot(path=str(SHOTS / f"21-room-head-quiet-{width}.png"))
                assert not errors, errors
            finally:
                browser.close()
