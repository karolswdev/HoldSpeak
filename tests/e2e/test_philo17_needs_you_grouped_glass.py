"""PHILO-17 (needsyou) -- sources of one cause are ONE Needs-you row, on glass.

The walker's desk: 30 GitHub sources that cannot be checked because gh is
not signed in were 30 rows above the work. Here, on a real hub at 1440 and
393, the failures are minted by the producer: each Watch is evaluated
through ``POST /api/watches/{id}/baseline`` with an injected gh runner that
answers as a signed-out gh does. Beside them: one paused GitHub Watch in
another Room (its own repair, Open source on its Room) and two stale Jira
Watches on two sites (two egress hosts).

  * one row `GitHub · 30 sources`, `Not signed in`, one Reconnect;
  * the paused source and each Jira site are rows of their own, each Jira
    Retry names its host;
  * the hub's count, the head and the bell say one number;
  * Details lists the 30 sources;
  * Reconnect opens Settings · Connections with the GitHub row focused.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _FETCH_JS, _api, _assert_clean, _boot, _ensure_build, _normal_chair, _settle, seed_meeting_engines
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the grouped Needs-you glass needs Playwright")

TOKEN = "philo17-needsyou"
SHOTS = evidence_dir("pm/roadmap/holdspeak-philo/phase-17/needsyou-shots")
SIZES = {1440: 900, 393: 852}
SIGNED_OUT = "To get started with GitHub CLI, please run:  gh auth login"
SOURCES = "[data-testid='needs-source-row']"


def _signed_out_gh(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    cmd = args[0] if args else kwargs.get("args", [])
    return subprocess.CompletedProcess(args=cmd, returncode=4, stdout="", stderr=SIGNED_OUT)


def _utc_naive(delta: timedelta = timedelta()) -> str:
    return (datetime.now(timezone.utc).replace(tzinfo=None) + delta).isoformat()


def _insert_watch(watch_id: str, project_id: str, connector: str, query_kind: str, query: dict[str, Any],
                  *, last_success_at: str | None = None) -> None:
    from holdspeak.db import get_database

    with get_database()._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, last_success_at, "
            " last_error, project_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, '[]', 1, ?, NULL, ?, datetime('now'), datetime('now'))",
            (watch_id, connector, query_kind, f"{connector} {query_kind}", json.dumps(query, sort_keys=True),
             last_success_at, project_id),
        )


def _seed(page: Any) -> dict[str, str]:
    rooms = {}
    for key, name in (("a", "Payments ledger"), ("b", "Staff hiring")):
        created = _api(page, "POST", "/api/projects", {
            "name": name, "description": "PHILO-17 grouped sources", "command_id": f"p17-room-{key}",
        }, token=TOKEN)
        rooms[key] = created["project"]["id"]
    # 30 GitHub Watches across the two Rooms; the producer writes their error.
    for n in range(30):
        room = rooms["a"] if n % 2 == 0 else rooms["b"]
        _insert_watch(f"w-gh-{n}", room, "gh", "pull_requests", {"repository": f"acme/repo-{n:02d}"})
        # The baseline fetch is refused (gh is signed out); the producer
        # (WatchService.baseline -> record_refresh_error) records the error.
        result = page.evaluate(_FETCH_JS, ["POST", f"/api/watches/w-gh-{n}/baseline", {}, TOKEN])
        assert result["status"] >= 400, result
    # One paused GitHub Watch in Room B (paused through its own verb).
    _insert_watch("w-gh-paused", rooms["b"], "gh", "pull_requests", {"repository": "acme/paused"},
                  last_success_at=_utc_naive(-timedelta(minutes=5)))
    _api(page, "POST", "/api/watches/w-gh-paused/pause", {}, token=TOKEN)
    # Two stale Jira Watches in Room A, on two sites.
    for site in ("alpha", "beta"):
        _insert_watch(f"w-jira-{site}", rooms["a"], "jira", "issues",
                      {"projects": [site.upper()], "connection_ref": f"{site}.atlassian.net|me@acme.dev"},
                      last_success_at=_utc_naive(-timedelta(days=2)))
    return rooms


def _readers(page: Any) -> dict[str, Any]:
    return page.evaluate("""() => {
      const num = (s) => { const e = document.querySelector(s); const m = ((e && e.innerText) || '').match(/\\d+/); return m ? Number(m[0]) : null; };
      return { head: num('[data-testid=arrival-display]'), bell: num('.desk-bell strong') };
    }""")


@pytest.mark.parametrize("width", list(SIZES))
def test_one_row_per_cause_and_repair_on_the_real_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    from playwright.sync_api import sync_playwright

    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN, gh_runner=_signed_out_gh)
    seed_meeting_engines()
    errors: list[str] = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            ctx = browser.new_context(viewport={"width": width, "height": SIZES[width]}, has_touch=width < 720)
            page = ctx.new_page()
            page.set_default_timeout(30_000)
            page.on("pageerror", lambda e: errors.append(str(e)[:200]))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _seed(page)

            wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
            gh_failed = [c for c in wire["coverage"] if c.get("provider") == "github" and c["state"] == "failed"]
            assert len(gh_failed) == 30, [c.get("reason") for c in wire["coverage"]]
            assert {c["cause"] for c in gh_failed} == {"Not signed in"}, gh_failed[:2]

            page.reload(wait_until="load")
            _normal_chair(page)
            # The bell opens Needs you (PHILO-17).
            page.locator(".desk-bell").click()
            page.get_by_test_id("needs-drawer").wait_for(timeout=15_000)
            page.locator(SOURCES).first.wait_for(timeout=15_000)
            _settle(page)

            # One number: hub = head = bell.
            numbers = _readers(page)
            assert numbers["head"] == numbers["bell"] == wire["count"], (numbers, wire["count"])

            names = [n.strip() for n in page.locator(f"{SOURCES} .needs-row-name").all_inner_texts()]
            assert "GitHub · 30 sources" in names, names
            assert "GitHub · acme/paused" in names, names
            jira = [n for n in names if n.startswith("Jira")]
            assert len(jira) == 2, names
            assert len(names) == 4, names
            group = page.locator(SOURCES).filter(has_text="GitHub · 30 sources")
            assert group.locator(".needs-row-fact").inner_text().strip() == "Not signed in"
            assert "gh auth login" not in page.get_by_test_id("needs-list").inner_text()
            # Each Jira Retry names its own host.
            hosts = sorted(
                page.locator(SOURCES).filter(has_text=f"Jira · {site.upper()}")
                .locator(".egress-chip, [class*='egress']").first.inner_text().strip()
                for site in ("alpha", "beta"))
            assert hosts == ["ALPHA.ATLASSIAN.NET", "BETA.ATLASSIAN.NET"], hosts
            # The paused source opens its own Room.
            assert page.locator(SOURCES).filter(has_text="GitHub · acme/paused") \
                .get_by_role("button", name="Open source: GitHub · acme/paused").count() == 1
            page.screenshot(path=str(SHOTS / f"grouped-{width}.png"))

            # Details lists every source of the group.
            group.get_by_role("button", name="Details: GitHub · 30 sources").click()
            detail = page.get_by_test_id("needs-detail")
            detail.wait_for()
            assert detail.locator("li").count() == 30
            _settle(page)
            page.screenshot(path=str(SHOTS / f"grouped-details-{width}.png"))

            # Reconnect lands on Settings · Connections, GitHub focused.
            group.get_by_role("button", name="Reconnect: GitHub · 30 sources").click()
            page.locator("[data-testid='connections-github']").wait_for(timeout=15_000)
            page.wait_for_function(
                "() => Boolean(document.activeElement && document.activeElement.closest('[data-testid=\"connections-github\"]'))",
                timeout=10_000,
            )
            _settle(page)
            page.screenshot(path=str(SHOTS / f"reconnect-settings-{width}.png"))
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
