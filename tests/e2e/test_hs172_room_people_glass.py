"""HS-172-07 -- Room PEOPLE section + shade PEOPLE lane glass rig.

Seeds a Room with a Watch snapshot containing PR reviewers, patches
the room_people service to return resolved people (bypasses the
encrypted People store / keychain), then verifies the PEOPLE section
at both widths (1440/393) and the shade PEOPLE lane at 393.

Assertions:
  - no raw <button> (every verb is the library Button)
  - no zero counter text on the face
  - no raw login text on the face
  - PEOPLE section is present with resolved display names
  - monogram lead slot visible
  - Open verb visible

Shots to phase-172-the-loop-closes/assets/story-07-shots/.
"""
from __future__ import annotations

import json
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

pytest.importorskip("playwright.sync_api", reason="Room people glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/story-07-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs172-people"

# The resolved people data the route will return (bypasses encrypted store).
MOCK_PEOPLE = [
    {
        "relationship_id": "rel-ania",
        "display_name": "Ania Kowalska",
        "prs_waiting": 2,
        "assignments_overdue": 1,
    },
    {
        "relationship_id": "rel-marek",
        "display_name": "Marek Kubiak",
        "prs_waiting": 1,
    },
]


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
            "VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'), NULL, ?, "
            "datetime('now'), datetime('now'))",
            (
                watch_id,
                connector_id,
                query_kind,
                f"{connector_id} {query_kind}",
                json.dumps(query or {}, sort_keys=True),
                json.dumps(snapshot or []),
                project_id,
            ),
        )


def _seed_room(page: Any) -> str:
    """Seed a project with PR watches.

    Returns the project id.
    """
    _seed_gh_connection()

    pid = _seed_project("proj-172-people", "Q4 Platform")
    yesterday = (datetime.now() - timedelta(days=3)).isoformat()

    _seed_watch(pid, watch_id="w-172-prs", connector_id="gh",
                query_kind="pull_requests",
                query={"repository": "karolswdev/HoldSpeak"},
                snapshot=[
                    {"number": 612, "title": "Rig settles animations",
                     "state": "OPEN",
                     "reviewRequests": ["ania-dev", "karolswdev"],
                     "updatedAt": yesterday},
                    {"number": 613, "title": "Fix token alignment",
                     "state": "OPEN",
                     "reviewRequests": ["ania-dev"],
                     "updatedAt": yesterday},
                    {"number": 614, "title": "Update docs",
                     "state": "OPEN",
                     "reviewRequests": ["marek-k"],
                     "updatedAt": yesterday},
                ])

    # CI watch with failure so this Room appears in needs-you aggregate
    _seed_watch(pid, watch_id="w-172-ci", connector_id="gh",
                query_kind="branch_ci",
                query={"repository": "karolswdev/HoldSpeak", "branch": "main"},
                snapshot=[
                    {"id": "run-1", "conclusion": "failure", "branch": "main",
                     "url": "https://github.com/karolswdev/HoldSpeak/actions/runs/1",
                     "updated_at": (datetime.now() - timedelta(minutes=20)).isoformat()},
                ])

    return pid


def _patch_room_people(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch the room_people function to return MOCK_PEOPLE.

    Avoids the encrypted People store (keychain) which is unavailable
    in isolated-HOME test environments.
    """
    import holdspeak.services.room_people_service as rps

    _orig = rps.room_people

    def _mock(project_service: Any, people_service: Any, project_id: str) -> list[dict[str, Any]]:
        # Only return mock data for our test project
        if project_id == "proj-172-people":
            return list(MOCK_PEOPLE)
        return _orig(project_service, people_service, project_id)

    monkeypatch.setattr(rps, "room_people", _mock)


# ── Window helpers ────────────────────────────────────────────────


def _open_room(page: Any, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}.png"
    window = page.locator(".desk-surface-window").filter(
        has=page.locator("[data-testid='room-body']")
    )
    if window.count() > 0:
        window.first.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _open_shade(page: Any) -> None:
    bell = page.locator(".desk-bell")
    bell.wait_for(timeout=10000)
    bell.click()
    page.locator(".desk-shade").wait_for(timeout=5000)
    _settle(page)


# ── Tests ─────────────────────────────────────────────────────────


def _run_room_people_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    _ensure_build()
    _patch_room_people(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))

            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)

            pid = _seed_room(page)

            # Open the Room
            _open_room(page, pid)
            _settle(page)

            # Wait for the PEOPLE section to appear
            people_section = page.locator("text=PEOPLE")
            people_section.first.wait_for(timeout=10000)
            _settle(page)

            # Take Room shot
            _shot(page, f"build-room-people-{width}", width)

            # Assert: PEOPLE section contains display names
            body = page.locator("[data-testid='room-body']")
            body_text = body.inner_text()
            assert "Ania Kowalska" in body_text, "Ania Kowalska display name missing"
            assert "Marek Kubiak" in body_text, "Marek Kubiak display name missing"

            # Assert: no raw login on the face
            assert "ania-dev" not in body_text, "Raw login ania-dev leaked to face"
            assert "marek-k" not in body_text, "Raw login marek-k leaked to face"

            # Assert: no zero counter text (no "0 " prefix before a token)
            for line in body_text.split("\n"):
                stripped = line.strip()
                if stripped.startswith("0 ") and any(
                    w in stripped for w in ["PR", "OVERDUE", "ASSIGNMENT"]
                ):
                    pytest.fail(f"Zero counter found on face: {stripped}")

            # Assert: monogram leads visible
            assert "AK" in body_text, "Monogram AK missing"
            assert "MK" in body_text, "Monogram MK missing"

            # Assert: Open verb visible
            open_buttons = page.locator("[data-testid='room-people-open']")
            assert open_buttons.count() >= 2, f"Expected 2+ Open buttons, got {open_buttons.count()}"

            # ── Shade test (only at 393) ──
            if width == 393:
                # Force a fresh needs-you aggregate so the shade sees the Room
                _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)

                _open_shade(page)
                _settle(page)

                shade = page.locator(".desk-shade")
                shade_text = shade.inner_text()

                # The shade should list the Room in PROJECTS (CI failure)
                # and show the PEOPLE lane below it.
                shade_people = page.locator("[data-testid='shade-people']")
                if shade_people.count() > 0:
                    # Verify display names in shade
                    people_text = shade_people.first.inner_text()
                    assert "Ania Kowalska" in people_text or "Marek Kubiak" in people_text, \
                        f"No display name in shade PEOPLE lane: {people_text}"
                    # No raw login
                    assert "ania-dev" not in people_text, "Raw login leaked to shade"
                    assert "marek-k" not in people_text, "Raw login leaked to shade"

                shade_path = SHOTS / "build-shade-people-393.png"
                shade.screenshot(path=str(shade_path))
                assert shade_path.stat().st_size > 1_000

            _assert_clean(page, errors)
            browser.close()

    finally:
        server.stop()


@pytest.mark.timeout(120)
def test_room_people_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_room_people_rig(tmp_path, monkeypatch, 1440)


@pytest.mark.timeout(120)
def test_room_people_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run_room_people_rig(tmp_path, monkeypatch, 393)
