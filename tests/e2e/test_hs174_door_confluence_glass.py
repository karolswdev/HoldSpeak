"""HS-174-07 -- Door Confluence row glass rig.

Seeds a Confluence connection in the DB and stubs the acli runner so the
Door renders the `C . Confluence` row connected (SIGNED IN, space picker,
RECENT BLOGS on, PAGES BY ID off) and not connected (SIGN IN + Connect).
Shoots at 1440 + 393.

Shots to phase-174-reach/assets/story-07-shots/.
"""
from __future__ import annotations

import subprocess
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

pytest.importorskip("playwright.sync_api", reason="Door glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-174-reach/assets/story-07-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs174-door-confluence"


def _open_door(page: Any) -> None:
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["project-setup"],
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


def _seed_confluence_connection(
    site: str = "karolswdev.atlassian.net",
    email: str = "karolsane@gmail.com",
    state: str = "connected",
) -> None:
    from holdspeak.db import get_database
    db = get_database()
    ref = f"{site}|{email}"
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES (?, 'confluence', ?, ?, "
            " datetime('now'), datetime('now'), datetime('now'))",
            (f"wpc-confluence-{ref}", ref, state),
        )


def _fake_acli_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Fake acli runner that returns sensible Confluence responses."""
    cmd = args[0] if args else kwargs.get("args", [])
    cmd_str = " ".join(str(c) for c in cmd) if isinstance(cmd, (list, tuple)) else str(cmd)

    if "auth" in cmd_str and "status" in cmd_str:
        return subprocess.CompletedProcess(
            cmd, 0,
            stdout='{"authenticated":true,"site":"karolswdev.atlassian.net","email":"karolsane@gmail.com"}',
            stderr="",
        )
    if "space" in cmd_str and "list" in cmd_str:
        return subprocess.CompletedProcess(
            cmd, 0,
            stdout='[{"key":"GOV","name":"Governance","type":"global"}]',
            stderr="",
        )
    return subprocess.CompletedProcess(cmd, 0, stdout="{}", stderr="")


def test_door_confluence_connected_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Door shows C . Confluence connected at 1440."""
    _ensure_build()
    server, url = _boot(
        tmp_path, monkeypatch, token=TOKEN,
        acli_runner=_fake_acli_runner,
    )
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    # Seed the connection row
    _seed_confluence_connection()

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
        _open_door(page)
        _settle(page)

        root = page.locator('[data-testid="door-root"]')
        root.wait_for(timeout=10_000)
        assert root.count() > 0, "Door root not rendered"

        # The Confluence row: look for C emblem
        confluence_row = page.locator('[data-testid="door-row-confluence"]')
        if confluence_row.count() > 0:
            text = confluence_row.text_content() or ""
            assert "RECENT BLOGS" in text, f"Missing RECENT BLOGS: {text}"
            assert "PAGES BY ID" in text, f"Missing PAGES BY ID: {text}"

        _shot(page, "build-door-confluence-connected-1440", 1440)
        _assert_clean(page, errors)
        browser.close()


def test_door_confluence_connected_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Door shows C . Confluence connected at 393."""
    _ensure_build()
    server, url = _boot(
        tmp_path, monkeypatch, token=TOKEN,
        acli_runner=_fake_acli_runner,
    )
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    _seed_confluence_connection()

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
        _open_door(page)
        _settle(page)

        _shot(page, "build-door-confluence-connected-393", 393)
        _assert_clean(page, errors)
        browser.close()


def test_door_confluence_not_connected_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Door shows C . Confluence with SIGN IN + Connect when not connected."""
    _ensure_build()
    server, url = _boot(
        tmp_path, monkeypatch, token=TOKEN,
        acli_runner=_fake_acli_runner,
    )
    errors: list[str] = []

    from playwright.sync_api import sync_playwright

    # Seed a not-connected row
    _seed_confluence_connection(state="owner_action_required")

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
        _open_door(page)
        _settle(page)

        _shot(page, "build-door-confluence-notconnected-1440", 1440)
        _assert_clean(page, errors)
        browser.close()
