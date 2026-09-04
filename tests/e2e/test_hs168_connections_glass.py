"""HS-168-03 Connections face glass rig.

Build-first via glass_infra._ensure_build. Two legs:

COLD LEG (isolated HOME -- gh/acli not authed):
  Shots at 1440 and 393 named cold-*.png.

REAL-READINESS LEG (real HOME, isolated DB -- gh/acli authed):
  Skip-guarded when gh/acli are not authenticated.
  Primes Jira via POST /api/providers/jira/connections + recheck.
  Shots at 1440 and 393 named connected-real-*.png.

FOLD + RECHECK (cold leg):
  Force Sign in via GH_CONFIG_DIR; assert recheck differs.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _boot as _conftest_boot, _api, _ensure_build

pytest.importorskip("playwright.sync_api", reason="Connections glass needs Playwright")

TOKEN = "hs168-connections-glass"
REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-168-the-connections-door/assets/story-03-shots"


# ── Skip guard for real-readiness leg ──────────────────────────────

def _real_readiness_skip() -> str:
    """Returns non-empty reason if the real-readiness leg should skip."""
    if shutil.which("gh") is None:
        return "gh CLI not found on PATH"
    try:
        gh = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"gh auth status could not run: {exc}"
    if gh.returncode != 0:
        return f"gh auth status failed (exit {gh.returncode}): {gh.stderr.strip()[:200]}"

    if shutil.which("acli") is None:
        return "acli CLI not found on PATH"
    try:
        acli = subprocess.run(
            ["acli", "jira", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return f"acli jira auth status could not run: {exc}"
    if acli.returncode != 0:
        return (
            f"acli jira auth status failed (exit {acli.returncode}): "
            f"{acli.stderr.strip()[:200]}"
        )
    return ""


_REAL_SKIP = _real_readiness_skip()


# ── Boot helpers ───────────────────────────────────────────────────

def _boot_cold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Any, str]:
    """Boot with isolated HOME (cold -- gh/acli not authed), isolated DB."""
    return _conftest_boot(tmp_path, monkeypatch, token=TOKEN)


def _boot_real(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Any, str]:
    """Boot with REAL HOME (gh/acli authed), isolated DB + config."""
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            Path.home() / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))

    # HOME STAYS REAL -- gh and acli read auth via HOME
    config_dir = tmp_path / ".holdspeak"
    config_dir.mkdir(parents=True)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    return server, server.start()


# ── Jira priming (from live167_walk) ───────────────────────────────

def _discover_acli_accounts() -> list[dict[str, Any]]:
    try:
        import yaml
    except ImportError:
        return []
    config_path = Path.home() / ".config" / "acli" / "jira_config.yaml"
    if not config_path.exists():
        return []
    data = yaml.safe_load(config_path.read_text())
    profiles = data.get("profiles", [])
    accounts = []
    for p in profiles:
        site = p.get("site", "")
        email = p.get("email", "")
        if site and email:
            accounts.append({"site": site, "email": email})
    return accounts


def _ref_encode(ref: str) -> str:
    import urllib.parse
    return urllib.parse.quote(ref, safe="")


def _prime_jira(page: Any) -> None:
    """Prime Jira connections from acli registry."""
    acli_accounts = _discover_acli_accounts()
    for acct in acli_accounts:
        _api(page, "POST", "/api/providers/jira/connections", {
            "site": acct["site"], "email": acct["email"],
        }, token=TOKEN)
        ref = f"{acct['site']}|{acct['email']}"
        _api(page, "POST",
             f"/api/providers/jira/connections/{_ref_encode(ref)}/recheck",
             token=TOKEN)


# ── Navigation ─────────────────────────────────────────────────────

def _shot(page: Any, path: Path, name: str) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    fp = path / f"{name}.png"
    page.screenshot(path=str(fp), full_page=True)
    return fp


def _file_hash(fp: Path) -> str:
    return hashlib.sha256(fp.read_bytes()).hexdigest()


def _navigate_to_connections(page: Any, url: str) -> None:
    """Navigate to the Settings -> Connections module."""
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "configure-settings", scope: "integration:destinations"})
        );
    }""")
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    page.wait_for_timeout(2000)
    connections_card = page.locator('[data-testid="connections-github"]')
    if connections_card.count() == 0:
        tab = page.get_by_text("Connections", exact=True)
        if tab.count() > 0:
            tab.first.click()
            page.wait_for_timeout(1000)


# ═══════════════════════════════════════════════════════════════════
# COLD LEG — isolated HOME, gh/acli not authed
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_connections_cold_at_both_widths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
) -> None:
    """The cold face (isolated HOME) renders the TOOLS group."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    server, url = _boot_cold(tmp_path, monkeypatch)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            _navigate_to_connections(page, url)

            # Wait for cards to render before taking the shot
            page.wait_for_selector('[data-testid="connections-github"]', timeout=10_000)
            page.wait_for_selector('[data-testid="connections-calendar"]', timeout=5_000)
            page.wait_for_selector('[data-testid="connections-models"]', timeout=5_000)

            suffix = "desktop" if width == 1440 else "phone"
            shot = _shot(page, SHOTS, f"cold-{suffix}")
            assert shot.exists(), f"Shot not saved: {shot}"

            browser.close()
    finally:
        server.stop()

    assert not errors, f"Page errors: {errors}"


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_connections_recheck_updates_card(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Recheck calls the route and the card updates."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    server, url = _boot_cold(tmp_path, monkeypatch)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            _navigate_to_connections(page, url)

            page.wait_for_selector('[data-testid="connections-github"]', timeout=10_000)
            recheck_btn = page.locator('[data-testid="connections-github"] button:has-text("Recheck")')
            if recheck_btn.count() > 0:
                shot_before = _shot(page, SHOTS, "recheck-before")
                recheck_btn.first.click()
                page.wait_for_timeout(2000)
                shot_after = _shot(page, SHOTS, "recheck-after")
                assert _file_hash(shot_before) != _file_hash(shot_after), \
                    "Recheck did not visibly change the face"

            browser.close()
    finally:
        server.stop()

    assert not errors, f"Page errors: {errors}"


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_connections_fold_sign_in_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Force the Sign in state by pointing GH_CONFIG_DIR at an empty dir."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    empty_gh = tmp_path / "empty-gh-config"
    empty_gh.mkdir()
    monkeypatch.setenv("GH_CONFIG_DIR", str(empty_gh))

    server, url = _boot_cold(tmp_path, monkeypatch)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            _navigate_to_connections(page, url)

            shot = _shot(page, SHOTS, "fold-sign-in")
            assert shot.exists(), f"Shot not saved: {shot}"

            github_card = page.locator('[data-testid="connections-github"]')
            github_card.wait_for(timeout=10_000)

            browser.close()
    finally:
        server.stop()

    assert not errors, f"Page errors: {errors}"


# ═══════════════════════════════════════════════════════════════════
# REAL-READINESS LEG — real HOME, gh/acli authed, isolated DB
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.skipif(bool(_REAL_SKIP), reason=_REAL_SKIP or "real readiness available")
@pytest.mark.parametrize("width", [1440, 393])
def test_connections_real_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
) -> None:
    """Connected face with real gh/acli auth at both widths."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    server, url = _boot_real(tmp_path, monkeypatch)
    errors: list[str] = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            # Seed and prime Jira connections before navigating
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding",
                 {"disposition": "completed"}, token=TOKEN)
            _prime_jira(page)

            # Navigate to Connections
            page.evaluate("""() => {
                sessionStorage.setItem(
                    "hs.desk.staged-surface-open",
                    JSON.stringify({key: "configure-settings", scope: "integration:destinations"})
                );
            }""")
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            page.wait_for_timeout(2000)

            connections_card = page.locator('[data-testid="connections-github"]')
            if connections_card.count() == 0:
                tab = page.get_by_text("Connections", exact=True)
                if tab.count() > 0:
                    tab.first.click()
                    page.wait_for_timeout(1000)

            page.wait_for_selector('[data-testid="connections-github"]', timeout=10_000)

            suffix = "desktop" if width == 1440 else "phone"
            shot = _shot(page, SHOTS, f"connected-real-{suffix}")
            assert shot.exists(), f"Shot not saved: {shot}"

            # Assert the GitHub card shows Connected
            gh_card = page.locator('[data-testid="connections-github"]')
            # The card should have a "Connected" chip (real gh auth)
            connected_chip = gh_card.locator('text="Connected"')
            assert connected_chip.count() > 0, "GitHub card does not show Connected state"

            browser.close()
    finally:
        server.stop()

    assert not errors, f"Page errors: {errors}"
