"""HS-200-07 (C4) -- coverage and partial results, on glass.

Three arrival states and the shade, at 1440 and 393, over REAL data (no
patched service): a Watch that cannot check is a failed source, and the
arrival must never speak "Nothing needs you" over it.

  complete-empty     -- no source unobserved: the all-clear line stands.
  partial-empty      -- zero items but one source failed: the all-clear
                        line is GONE, the COVERAGE token and the repair
                        row with its owning verb stand in its place.
  one-failed-healthy -- a healthy Room's item beside the failed source.
  shade-coverage     -- the same truth behind the bell.

Shots to phase-200-the-working-practice/assets/story-07-shots/.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _ensure_build,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="Coverage glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-07-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs200-coverage"


# ── Seed helpers (real rows; the failure is a real Watch error) ──────


def _seed_project(project_id: str, name: str) -> str:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "'2026-09-01T00:00:00', '2026-09-06T10:00:00')",
            (project_id, name),
        )
    return project_id


def _seed_gh_connection(login: str = "karolswdev") -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', ?, 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
            (login,),
        )


def _utc_naive(delta: timedelta = timedelta()) -> str:
    """connector_watches stores NAIVE UTC (project_service.aware_iso)."""
    return (datetime.now(timezone.utc).replace(tzinfo=None) + delta).isoformat()


def _seed_watch(
    project_id: str,
    *,
    watch_id: str,
    repository: str,
    snapshot: list[dict[str, Any]] | None = None,
    last_success_at: str | None = None,
    last_error: str | None = None,
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, 'gh', 'pull_requests', 'gh pull_requests', ?, ?, 1, "
            " ?, ?, ?, datetime('now'), datetime('now'))",
            (
                watch_id,
                json.dumps({"repository": repository}, sort_keys=True),
                json.dumps(snapshot or []),
                last_success_at,
                last_error,
                project_id,
            ),
        )


def _seed_failed_source_only() -> None:
    """One Room whose only Watch cannot check: zero items, coverage partial."""
    _seed_gh_connection()
    _seed_project("proj-beta", "Governance")
    _seed_watch("proj-beta", watch_id="w-beta", repository="karolswdev/Beta",
                last_error="401 Bad credentials")


def _seed_healthy_and_failed() -> None:
    """A healthy Room with one item, beside the Room that cannot check."""
    _seed_gh_connection()
    _seed_project("proj-alpha", "Q4 Platform")
    _seed_watch(
        "proj-alpha", watch_id="w-alpha", repository="karolswdev/HoldSpeak",
        last_success_at=_utc_naive(-timedelta(minutes=10)),
        snapshot=[{
            "number": 612, "title": "Rig settles animations before every shot",
            "state": "OPEN",
            "url": "https://github.com/karolswdev/HoldSpeak/pull/612",
            "reviewRequests": ["karolswdev"],
            "updatedAt": _utc_naive(-timedelta(days=3)),
        }],
    )
    _seed_failed_source_only()


# ── Shot helper ─────────────────────────────────────────────────────


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _open_shade(page: Any) -> None:
    bell = page.locator(".desk-bell")
    bell.wait_for(timeout=10000)
    bell.click()
    page.locator(".desk-shade").wait_for(timeout=5000)
    _settle(page)


def _arrive(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)


def _no_raw_buttons(page: Any) -> int:
    return page.evaluate("""() => {
        const chair = document.querySelector('[data-testid="chair"]');
        if (!chair) return 0;
        let raw = 0;
        for (const btn of chair.querySelectorAll('button')) {
            const cls = btn.className;
            if (!cls.includes('btn') && !cls.includes('desk-mic') &&
                !cls.includes('surface-ledger-line')) raw++;
        }
        return raw;
    }""")


# ── Legs ────────────────────────────────────────────────────────────


def _run_complete_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """No unobserved source: the all-clear line is lawful."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            _settle(page)

            wire = _api(page, "GET", "/api/desk/needs-you", token=TOKEN)
            assert wire["complete"] is True, wire.get("coverage")
            assert wire["count"] == 0

            headline = page.get_by_test_id("arrival-display").text_content() or ""
            assert headline.strip() == "Nothing needs you", headline
            assert page.get_by_test_id("arrival-coverage").count() == 0, \
                "COVERAGE section is absent when coverage is complete (A.8)"

            _shot(page, "build-arrival-complete-empty", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_partial_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """Zero items over a failed source: NO all-clear, coverage + repair."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            _seed_failed_source_only()
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            _settle(page)

            wire = _api(page, "GET", "/api/desk/needs-you", token=TOKEN)
            assert wire["count"] == 0, wire["items"]
            assert wire["complete"] is False, wire["coverage"]
            failed = [c for c in wire["coverage"] if c["state"] == "failed"]
            assert failed, wire["coverage"]
            assert failed[0]["repair"]["verb"] == "Reconnect", failed[0]

            headline = page.get_by_test_id("arrival-display").text_content() or ""
            assert "nothing needs you" not in headline.lower(), \
                f"an empty PARTIAL result must not speak the all-clear: {headline}"

            section = page.get_by_test_id("arrival-coverage")
            assert section.count() == 1, "COVERAGE section present on a partial result"
            section_text = section.text_content() or ""
            assert "COVERAGE · 3 OF 4" in section_text, section_text
            assert page.get_by_test_id("arrival-coverage-token").count() >= 1
            observed = page.get_by_test_id("arrival-coverage-observed").first
            assert (observed.text_content() or "").strip(), "the row names its observation"
            verb = page.get_by_test_id("arrival-coverage-verb").first
            assert (verb.text_content() or "").strip() == "Reconnect", verb.text_content()
            assert _no_raw_buttons(page) == 0, "every verb is the library Button"

            _shot(page, "build-arrival-partial-empty", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_one_failed_among_healthy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """A healthy Room's item stands beside the unobserved source."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            _seed_healthy_and_failed()
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
            _settle(page)

            wire = _api(page, "GET", "/api/desk/needs-you", token=TOKEN)
            assert wire["count"] >= 1, wire
            assert wire["complete"] is False, wire["coverage"]
            states = {c["source_id"]: c["state"] for c in wire["coverage"]}
            assert states["watch:w-alpha"] == "available", states
            assert states["watch:w-beta"] == "failed", states

            headline = page.get_by_test_id("arrival-display").text_content() or ""
            assert "need you" in headline.lower(), headline
            assert page.get_by_test_id("arrival-needs-you").count() == 1
            assert page.get_by_test_id("arrival-coverage").count() == 1, \
                "a partial result names its gap even when items exist"
            assert _no_raw_buttons(page) == 0

            _shot(page, "build-arrival-one-failed", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_shade_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """The shade carries the same truth: no 'Nothing missed' over a gap."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _arrive(page, url)
            _seed_failed_source_only()
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)
            _open_shade(page)

            section = page.get_by_test_id("shade-coverage")
            assert section.count() == 1, "COVERAGE section present in the shade"
            row = page.get_by_test_id("shade-coverage-row").first
            text = row.text_content() or ""
            # The row names the SOURCE that was not observed (the Watch's
            # provider + scope), not the Room that owns it.
            assert "karolswdev/Beta" in text, text
            assert "CANT CHECK" in text.upper(), text
            assert page.get_by_test_id("shade-coverage-verb").count() >= 1
            assert page.locator("text=Nothing missed").count() == 0, \
                "the shade's all-clear line is gone over incomplete coverage"

            _shot(page, "build-shade-coverage", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── Pytest entry points ─────────────────────────────────────────────


class TestCoverageGlass:
    """HS-200-07 -- the coverage face at both viewports."""

    def test_arrival_complete_empty_1440(self, tmp_path, monkeypatch) -> None:
        _run_complete_empty(tmp_path, monkeypatch, 1440)

    def test_arrival_complete_empty_393(self, tmp_path, monkeypatch) -> None:
        _run_complete_empty(tmp_path, monkeypatch, 393)

    def test_arrival_partial_empty_1440(self, tmp_path, monkeypatch) -> None:
        _run_partial_empty(tmp_path, monkeypatch, 1440)

    def test_arrival_partial_empty_393(self, tmp_path, monkeypatch) -> None:
        _run_partial_empty(tmp_path, monkeypatch, 393)

    def test_arrival_one_failed_among_healthy_1440(self, tmp_path, monkeypatch) -> None:
        _run_one_failed_among_healthy(tmp_path, monkeypatch, 1440)

    def test_arrival_one_failed_among_healthy_393(self, tmp_path, monkeypatch) -> None:
        _run_one_failed_among_healthy(tmp_path, monkeypatch, 393)

    def test_shade_coverage_1440(self, tmp_path, monkeypatch) -> None:
        _run_shade_coverage(tmp_path, monkeypatch, 1440)

    def test_shade_coverage_393(self, tmp_path, monkeypatch) -> None:
        _run_shade_coverage(tmp_path, monkeypatch, 393)
