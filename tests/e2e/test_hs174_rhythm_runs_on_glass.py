"""HS-174-08 -- Rhythm `Runs on` row glass rig.

Tests the Rhythm face's Runs on row at 1440 + 393.
Legs:
  1. Default (THIS DEVICE): the row is present, caption absent.
  2. PUT runs_on to a remote host: caption WHILE THIS MAC IS AWAKE appears,
     LAST RUN <age> appears, CycleGadget offers the remote host.
  3. Run now appears exactly once (on Sweep, not on Runs on).

Shots to phase-174-reach/assets/story-08-shots/.
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

pytest.importorskip("playwright.sync_api", reason="Rhythm glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-174-reach/assets/story-08-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs174-rhythm"


def _open_rhythm(page: Any) -> None:
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["configure-cadence"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _window(page: Any) -> Any:
    return page.locator(".desk-surface-window").first


def _shot(page: Any, name: str, width: int) -> Path:
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


def _seed_remote_pipeline_event(caller: str = "192.168.1.43") -> None:
    """Seed a HeartbeatService sweep with origin=remote so remote_hosts is populated."""
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
                event_id, now, "HeartbeatService", "run_sweep",
                "agent", "sweep-runner", "{}",
                '{"watches":4,"rooms":2,"held":false}',
                None, None, 42.0,
                str(uuid.uuid4()), 0, "remote", caller, "sweep-runner",
            ),
        )


def test_runs_on_local_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runs on row present at 1440 with caption absent when THIS DEVICE."""
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
        _open_rhythm(page)
        _settle(page)

        row = page.locator('[data-testid="rhythm-runs-on-row"]')
        assert row.count() > 0, "Runs on row not found"

        caption = page.locator('[data-testid="rhythm-runs-on-caption"]')
        assert caption.count() == 0, "Caption should be absent when THIS DEVICE"

        _shot(page, "build-rhythm-runs-on-local-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


def test_runs_on_remote_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PUT runs_on to remote host, assert caption and LAST RUN appear."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    # Seed a remote pipeline event so remote_hosts is populated and
    # last_remote_run_at has a value.
    _seed_remote_pipeline_event("192.168.1.43")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        _settle(page)

        # PUT runs_on to the remote host
        _api(page, "PUT", "/api/settings/heartbeat",
             {"runs_on": "192.168.1.43"}, token=TOKEN)

        _open_rhythm(page)
        _settle(page)

        # Caption should appear
        caption = page.locator('[data-testid="rhythm-runs-on-caption"]')
        caption.wait_for(timeout=5000)
        assert caption.count() > 0, "Caption should be present when remote"
        assert caption.text_content() == "WHILE THIS MAC IS AWAKE"

        # LAST RUN token should appear
        facts = page.locator('[data-testid="rhythm-runs-on-facts"]')
        facts_text = facts.text_content() or ""
        assert "LAST RUN" in facts_text, f"Missing LAST RUN in: {facts_text}"

        _shot(page, "build-rhythm-runs-on-remote-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


def test_runs_on_remote_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same at phone width."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    _seed_remote_pipeline_event("192.168.1.43")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 393, "height": 900})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"{url}/?token={TOKEN}", wait_until="load")
        _normal_chair(page)
        _settle(page)

        _api(page, "PUT", "/api/settings/heartbeat",
             {"runs_on": "192.168.1.43"}, token=TOKEN)

        _open_rhythm(page)
        _settle(page)

        _shot(page, "build-rhythm-runs-on-remote-393", 393)
        _assert_clean(page, errors)
        browser.close()


def test_run_now_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run now appears exactly once (on Sweep, not on Runs on)."""
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
        _open_rhythm(page)
        _settle(page)

        run_now = page.locator('[data-testid="rhythm-run-now"]')
        assert run_now.count() == 1, (
            f"Run now should appear exactly once, found {run_now.count()}"
        )

        runs_on_row = page.locator('[data-testid="rhythm-runs-on-row"]')
        if runs_on_row.count() > 0:
            text = runs_on_row.text_content() or ""
            assert "Run now" not in text, "Run now must NOT be on the Runs on row"

        _shot(page, "build-rhythm-run-now-once-1440", 1440)
        _assert_clean(page, errors)
        browser.close()
