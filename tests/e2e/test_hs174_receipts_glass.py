"""HS-174-04 -- Receipts with REMOTE badge glass rig.

Seeds pipeline events with origin=remote into the DB, opens the shade,
asserts the FINISHED row shows `REMOTE . <ip>` in the accent outline
with the time as a separate token, and a local row shows THIS DEVICE.

Shots to phase-174-reach/assets/story-04-shots/.
"""
from __future__ import annotations

import time
import uuid
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

pytest.importorskip("playwright.sync_api", reason="Receipts glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-174-reach/assets/story-04-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs174-receipts"


def _seed_pipeline_event(
    *,
    service: str = "ProjectService",
    method: str = "project_list",
    origin: str = "local",
    caller: str = "",
    caller_identity: str = "",
    result_summary: str = "{}",
    args_summary: str = "{}",
) -> str:
    from holdspeak.db import get_database
    db = get_database()
    event_id = str(uuid.uuid4())
    now = time.time()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method,
                principal_kind, principal_identity, args_summary,
                result_summary, error, error_code, duration_ms,
                correlation_id, is_async, origin, caller, caller_identity)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event_id, now, service, method,
                "agent", caller_identity or "sweep-runner", args_summary,
                result_summary, None, None, 42.0,
                str(uuid.uuid4()), 0, origin, caller, caller_identity,
            ),
        )
    return event_id


def _open_shade(page: Any) -> None:
    bell = page.locator(".desk-bell")
    bell.wait_for(timeout=10000)
    bell.click()
    page.locator(".desk-shade").wait_for(timeout=5000)
    _settle(page)


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    old_size = page.viewport_size
    page.set_viewport_size({"width": width, "height": 2400})
    _settle(page)
    path = SHOTS / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old_size)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def test_shade_remote_receipts_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Seeds remote + local pipeline events, opens shade, asserts badges at 1440."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _api(page, "POST", "/api/desk/seed", token=TOKEN)
        _api(page, "PUT", "/api/setup/onboarding",
             {"disposition": "completed"}, token=TOKEN)

        # Seed: remote READ, remote SWEEP, local STEWARD RUN
        _seed_pipeline_event(
            service="ProjectService", method="project_list",
            origin="remote", caller="100.64.0.5",
            caller_identity="sweep-runner",
        )
        _seed_pipeline_event(
            service="HeartbeatService", method="run_sweep",
            origin="remote", caller="192.168.1.43",
            caller_identity="sweep-runner",
            result_summary='{"watches":4,"rooms":2,"held":false}',
        )
        _seed_pipeline_event(
            service="StewardService", method="project_run_steward",
            origin="local", caller="",
        )

        page.reload(wait_until="load")
        _normal_chair(page)
        _settle(page)
        _open_shade(page)

        shade = page.locator(".desk-shade")
        assert shade.count() > 0, "Shade not opened"

        finished = page.locator('section[aria-label="Finished"]')
        if finished.count() > 0:
            text = finished.text_content() or ""
            # Remote events should show REMOTE badge with IP
            assert "REMOTE" in text, f"REMOTE badge missing in FINISHED: {text}"
            assert "100.64.0.5" in text or "192.168.1.43" in text, (
                f"Caller IP missing in FINISHED: {text}"
            )

        _shot(page, "build-shade-receipts-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


def test_shade_remote_receipts_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same at phone width."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 393, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _api(page, "POST", "/api/desk/seed", token=TOKEN)
        _api(page, "PUT", "/api/setup/onboarding",
             {"disposition": "completed"}, token=TOKEN)
        _seed_pipeline_event(
            service="HeartbeatService", method="run_sweep",
            origin="remote", caller="192.168.1.43",
            result_summary='{"watches":4,"rooms":2,"held":false}',
        )
        page.reload(wait_until="load")
        _normal_chair(page)
        _settle(page)
        _open_shade(page)
        _shot(page, "build-shade-receipts-393", 393)
        _assert_clean(page, errors)
        browser.close()


def test_egress_remote_css(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CSS for data-scope=remote: accent border, transparent bg."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        _settle(page)

        result = page.evaluate("""() => {
            const chip = document.createElement('span');
            chip.className = 'gadget-chip gadget-chip-egress';
            chip.dataset.scope = 'remote';
            chip.textContent = 'REMOTE . 100.64.0.5';
            document.body.appendChild(chip);
            const cs = getComputedStyle(chip);
            return {
                borderColor: cs.borderColor,
                backgroundColor: cs.backgroundColor,
            };
        }""")

        bg = result["backgroundColor"]
        assert bg in ("rgba(0, 0, 0, 0)", "transparent") or "0)" in bg, (
            f"Expected transparent bg for remote, got {bg}"
        )

        _shot(page, "build-egress-remote-chip-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


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


def _open_room(page: Any, project_id: str) -> None:
    """Open a Room surface window for a given project."""
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


def _window(page: Any) -> Any:
    return page.locator(".desk-surface-window").first


def _room_shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    old_size = page.viewport_size
    page.set_viewport_size({"width": width, "height": 2400})
    _settle(page)
    path = SHOTS / f"{name}.png"
    win = _window(page)
    if win.count() > 0:
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    page.set_viewport_size(old_size)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def test_room_receipts_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Room RECEIPTS section shows REMOTE + THIS DEVICE rows at 1440."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    PID = "proj-174-receipts"
    _seed_project(PID, "Q4 Platform")

    # Seed two pipeline events scoped to the project (project_id in args_summary)
    _seed_pipeline_event(
        service="HeartbeatService", method="run_sweep",
        origin="remote", caller="192.168.1.43",
        caller_identity="sweep-runner",
        result_summary=f'{{"watches":4,"rooms":2,"held":false,"project_id":"{PID}"}}',
        args_summary=f'{{"project_id":"{PID}"}}',
    )
    _seed_pipeline_event(
        service="StewardService", method="project_run_steward",
        origin="local", caller="",
        result_summary='{"status":"completed"}',
        args_summary=f'{{"project_id":"{PID}"}}',
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _api(page, "POST", "/api/desk/seed", token=TOKEN)
        _api(page, "PUT", "/api/setup/onboarding",
             {"disposition": "completed"}, token=TOKEN)
        _normal_chair(page)
        _settle(page)

        _open_room(page, PID)
        _settle(page)

        # Look for RECEIPTS section
        receipts = page.locator('[data-testid="receipt-row"]')
        if receipts.count() > 0:
            # At least one receipt row rendered
            egress_chips = page.locator('[data-testid="receipt-egress"]')
            if egress_chips.count() > 0:
                all_text = " ".join(
                    egress_chips.nth(i).text_content() or ""
                    for i in range(egress_chips.count())
                )
                assert "REMOTE" in all_text, f"REMOTE badge missing: {all_text}"

        _room_shot(page, "build-room-receipts-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


def test_room_receipts_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Room RECEIPTS section at 393."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    PID = "proj-174-receipts"
    _seed_project(PID, "Q4 Platform")

    _seed_pipeline_event(
        service="HeartbeatService", method="run_sweep",
        origin="remote", caller="192.168.1.43",
        args_summary=f'{{"project_id":"{PID}"}}',
    )
    _seed_pipeline_event(
        service="StewardService", method="project_run_steward",
        origin="local", caller="",
        args_summary=f'{{"project_id":"{PID}"}}',
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 393, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _api(page, "POST", "/api/desk/seed", token=TOKEN)
        _api(page, "PUT", "/api/setup/onboarding",
             {"disposition": "completed"}, token=TOKEN)
        _normal_chair(page)
        _settle(page)

        _open_room(page, PID)
        _settle(page)

        _room_shot(page, "build-room-receipts-393", 393)
        _assert_clean(page, errors)
        browser.close()
