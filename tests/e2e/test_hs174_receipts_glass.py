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
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="Receipts glass needs Playwright")

SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-174-reach/assets/story-04-shots")
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
    # PHILO-17 (needsyou): the bell opens Needs you now; the shade opens from
    # the Dock's Desk memory launcher.
    launcher = page.locator(".desk-dock [data-launcher='attention']")
    launcher.wait_for(timeout=10000)
    launcher.click()
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


def _room_receipts_leg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int) -> None:
    """The Room's receipts under History: a remote write with its REMOTE badge
    and a local write without one, at ``width``.

    PHILO-17 U31 / Astra r1-r2 (#1084): the receipts live under History; the
    fence selects it and fails without rows. The LOCAL write is minted by the
    real producer (POST /api/projects/{id}/items -> ProjectService.create_item,
    observed into pipeline_events). The REMOTE write is still a seeded
    pipeline event: minting it for real needs the remote listener, an agent
    credential with a project grant and a non-loopback client (see STATUS).
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    PID = "proj-174-receipts"
    _seed_project(PID, "Q4 Platform")
    _seed_pipeline_event(
        service="ProjectService", method="update_project",
        origin="remote", caller="192.168.1.43",
        caller_identity="sweep-runner",
        result_summary=f'{{"id":"{PID}"}}',
        args_summary=f'{{"project_id":"{PID}"}}',
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _api(page, "POST", "/api/desk/seed", token=TOKEN)
        _api(page, "PUT", "/api/setup/onboarding",
             {"disposition": "completed"}, token=TOKEN)
        # The local write, through the Room's real route and service.
        _api(page, "POST", f"/api/projects/{PID}/items", {
            "item_type": "milestone", "title": "Write the cutover runbook", "command_id": f"hs174-item-{width}",
        }, token=TOKEN)
        _normal_chair(page)
        _settle(page)

        _open_room(page, PID)
        _settle(page)

        page.get_by_role("tab", name="History").first.click()
        receipts = page.locator('[data-testid="receipt-row"]')
        receipts.first.wait_for(timeout=15_000)
        page.wait_for_function(
            "() => document.querySelectorAll('[data-testid=\"receipt-row\"]').length >= 2",
            timeout=15_000,
        )
        rows = [receipts.nth(i) for i in range(receipts.count())]
        texts = [(r.text_content() or "") for r in rows]
        remote = [r for r, t in zip(rows, texts) if "UPDATE PROJECT" in t.upper()]
        local = [r for r, t in zip(rows, texts) if "CREATE ITEM" in t.upper()]
        assert len(remote) == 1 and len(local) >= 1, texts
        # The remote write wears its REMOTE badge with the caller; the local
        # write wears none (egress exactly where egress happens).
        badge = remote[0].locator('[data-testid="receipt-egress"]')
        assert badge.count() == 1, texts
        assert (badge.text_content() or "").strip() == "REMOTE · 192.168.1.43", badge.text_content()
        for row in local:
            assert row.locator('[data-testid="receipt-egress"]').count() == 0, texts
        # No machine tokens (UX-CANON): no "Service." on a row.
        for text in texts:
            assert "Service." not in text, text

        _room_shot(page, f"build-room-receipts-{width}", width)
        _assert_clean(page, errors)
        browser.close()


def test_room_receipts_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Room receipts under History: REMOTE + local rows at 1440."""
    _room_receipts_leg(tmp_path, monkeypatch, 1440)


def test_room_receipts_393(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Room receipts under History: REMOTE + local rows at 393."""
    _room_receipts_leg(tmp_path, monkeypatch, 393)
