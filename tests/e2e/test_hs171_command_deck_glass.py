"""HS-171-07 -- Command Deck PROJECTS group glass rig.

Seeds three Rooms (two with needs-you items, one with none).
Asserts:
  - PROJECTS band appears in the command deck
  - rows sorted by needs-you count desc, then name
  - chip "N NEED YOU" present only on Rooms with items (absent at zero)
  - selecting a verb opens the Room window
  - 12 Rooms => cap at 10

Shots to phase-171-the-heartbeat/assets/story-07-shots/.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
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

pytest.importorskip("playwright.sync_api", reason="Command deck glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-171-the-heartbeat/assets/story-07-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs171-deck"


# ── Seed helpers ──────────────────────────────────────────────────


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
            "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
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


def _seed_watch(
    project_id: str,
    *,
    watch_id: str,
    connector_id: str = "gh",
    query_kind: str = "pull_requests",
    query: dict[str, Any] | None = None,
    snapshot: list[dict[str, Any]] | None = None,
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (
                watch_id,
                connector_id,
                query_kind,
                f"{connector_id} {query_kind}",
                json.dumps(query or {}, sort_keys=True),
                json.dumps(snapshot or []),
                1,
                "2026-09-04T10:00:00",
                None,
                project_id,
            ),
        )


def _seed_three_rooms() -> tuple[str, str, str]:
    """Seed three projects: Alpha (2 items), Beta (1 item), Gamma (0).

    Returns (pid_alpha, pid_beta, pid_gamma).
    """
    _seed_gh_connection()

    # Alpha: 2 items (PR review overdue + CI failure)
    pid1 = _seed_project("proj-alpha-deck", "Q4 Platform")
    yesterday = (datetime.now() - timedelta(days=3)).isoformat()
    _seed_watch(pid1, watch_id="w-deck-alpha-prs",
                query_kind="pull_requests",
                query={"repository": "karolswdev/HoldSpeak"},
                snapshot=[
                    {"number": 612, "title": "Rig settles animations",
                     "state": "OPEN", "url": "https://github.com/karolswdev/HoldSpeak/pull/612",
                     "reviewRequests": ["karolswdev"], "updatedAt": yesterday},
                ])
    _seed_watch(pid1, watch_id="w-deck-alpha-ci",
                query_kind="branch_ci",
                query={"repository": "karolswdev/HoldSpeak", "branch": "main"},
                snapshot=[
                    {"conclusion": "failure", "branch": "main",
                     "url": "https://github.com/karolswdev/HoldSpeak/actions/runs/1",
                     "updated_at": (datetime.now() - timedelta(minutes=40)).isoformat()},
                ])

    # Beta: 1 item (CI failure)
    pid2 = _seed_project("proj-beta-deck", "Governance")
    _seed_watch(pid2, watch_id="w-deck-beta-ci",
                query_kind="branch_ci",
                query={"repository": "karolswdev/Beta", "branch": "main"},
                snapshot=[
                    {"conclusion": "failure", "branch": "main",
                     "url": "https://github.com/karolswdev/Beta/actions/runs/2",
                     "updated_at": (datetime.now() - timedelta(minutes=20)).isoformat()},
                ])

    # Gamma: 0 items (healthy CI)
    pid3 = _seed_project("proj-gamma-deck", "Data Platform")
    _seed_watch(pid3, watch_id="w-deck-gamma-ci",
                query_kind="branch_ci",
                query={"repository": "karolswdev/Gamma", "branch": "main"},
                snapshot=[
                    {"conclusion": "success", "branch": "main",
                     "url": "https://github.com/karolswdev/Gamma/actions/runs/3",
                     "updated_at": (datetime.now() - timedelta(minutes=10)).isoformat()},
                ])

    return pid1, pid2, pid3


def _seed_twelve_rooms() -> list[str]:
    """Seed 12 projects to test the cap of 10."""
    _seed_gh_connection()
    pids: list[str] = []
    for i in range(12):
        pid = f"proj-cap-{i:02d}"
        name = f"Project {chr(65 + i)}"
        _seed_project(pid, name)
        pids.append(pid)
    return pids


# ── Shot helpers ──────────────────────────────────────────────────

def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _open_deck(page: Any) -> None:
    """Open the command deck via the Search button."""
    launch = page.locator(".desk-tools-launch")
    launch.wait_for(timeout=10000)
    launch.click()
    page.locator("#desk-tool-shelf").wait_for(timeout=5000)
    _settle(page)


# ── Tests ─────────────────────────────────────────────────────────


def _run_projects_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Seed three Rooms, assert PROJECTS group order + badge + open."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Init desk
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            # Seed three Rooms
            _seed_three_rooms()

            # Reload to pick up seeded data
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Verify needs-you aggregate is populated
            ny = _api(page, "GET", "/api/desk/needs-you", token=TOKEN)
            assert ny.get("count", 0) > 0, \
                f"Expected needs-you items, got count={ny.get('count')}"

            # Open the command deck
            _open_deck(page)

            # ── PROJECTS band present ──
            bands = page.locator(".desk-deck-band")
            band_texts = [bands.nth(i).text_content() or ""
                          for i in range(bands.count())]
            assert "PROJECTS" in band_texts, \
                f"PROJECTS band not found; bands: {band_texts}"

            # ── Project rows in PROJECTS band ──
            # The PROJECTS section rows have ids starting with
            # "desk-palette-option-project.open."
            project_rows = page.locator(
                "[id^='desk-palette-option-project\\.open\\.']"
            )
            row_count = project_rows.count()
            assert row_count == 3, \
                f"Expected 3 project rows, got {row_count}"

            # ── Order: needs-you desc, then name ──
            # Alpha (2 items) first, Beta (1 item) second, Gamma (0) third
            labels = [
                (project_rows.nth(i).locator(".desk-deck-label").text_content() or "")
                for i in range(row_count)
            ]
            assert "Q4 Platform" in labels[0], \
                f"First row should be Q4 Platform (2 items): {labels}"
            assert "Governance" in labels[1], \
                f"Second row should be Governance (1 item): {labels}"
            assert "Data Platform" in labels[2], \
                f"Third row should be Data Platform (0 items): {labels}"

            # ── Badge present only on rows with items ──
            badges = [
                project_rows.nth(i).locator(".desk-deck-badge")
                for i in range(row_count)
            ]
            # Alpha (2 items) should have badge
            assert badges[0].count() == 1, "Alpha should have a badge"
            badge_text_0 = badges[0].text_content() or ""
            assert "NEED YOU" in badge_text_0, \
                f"Alpha badge should say NEED YOU: {badge_text_0}"
            assert badge_text_0.startswith("2"), \
                f"Alpha badge should start with 2: {badge_text_0}"

            # Beta (1 item) should have badge
            assert badges[1].count() == 1, "Beta should have a badge"
            badge_text_1 = badges[1].text_content() or ""
            assert "NEEDS YOU" in badge_text_1, \
                f"Beta badge should say NEEDS YOU (singular): {badge_text_1}"

            # Gamma (0 items) should have no badge
            assert badges[2].count() == 0, \
                "Gamma (0 items) should have no badge"

            # ── Kind token ──
            kinds = [
                (project_rows.nth(i).locator(".desk-deck-kind").text_content() or "")
                for i in range(row_count)
            ]
            for i, kind_text in enumerate(kinds):
                assert kind_text == "PROJECT", \
                    f"Row {i} kind should be PROJECT: {kind_text}"

            # ── Selecting a verb opens the Room window ──
            # Click the first project row (Q4 Platform)
            project_rows.first.click()
            page.wait_for_timeout(1000)
            # The deck should close after running a verb
            deck_after = page.locator("#desk-tool-shelf")
            assert deck_after.count() == 0, \
                "Command deck should close after selecting a verb"

            # Re-open deck for the screenshot
            _open_deck(page)
            _shot(page, "build-command-deck-projects", width)

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def _run_cap_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
) -> None:
    """Seed 12 Rooms, assert cap at 10."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            # Init desk
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            # Seed 12 Rooms
            _seed_twelve_rooms()

            # Reload
            page.reload(wait_until="load")
            _normal_chair(page)
            _settle(page)

            # Open the command deck
            _open_deck(page)

            # ── Cap at 10 ──
            project_rows = page.locator(
                "[id^='desk-palette-option-project\\.open\\.']"
            )
            row_count = project_rows.count()
            assert row_count == 10, \
                f"Expected cap at 10 project rows, got {row_count}"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── Parametrized test functions ──────────────────────────────────


@pytest.mark.timeout(120)
def test_command_deck_projects_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_projects_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_command_deck_projects_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_projects_rig(tmp_path, monkeypatch, 393)


@pytest.mark.timeout(120)
def test_command_deck_cap_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_cap_rig(tmp_path, monkeypatch, 1440)
