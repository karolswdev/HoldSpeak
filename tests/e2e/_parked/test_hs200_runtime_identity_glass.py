"""HS-200-02 -- the Settings > System runtime-identity glass rig.

Build-first via glass_infra._ensure_build. Two legs on an isolated HOME:

  - HEALTHY: the process started with the bundle that is on disk, owns its
    database and matches the schema. Every C1 token renders; NO repair chip
    (a healthy runtime is silent -- the canon forbids a counter of zero).
  - REPAIR: the bundle stamp moved under the running process. STALE BUNDLE
    flies as a chip; the database path stays inside the RAW fold.

Both legs assert the library fence (no raw <button>), no page errors and no
overflow, and shoot 1440 + 393.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _settle,
    REPO,
)
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="the identity glass needs Playwright")

TOKEN = "hs200-runtime-identity"
SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-02-shots")
BUILT = REPO / "holdspeak" / "static" / "_built"


def _navigate_to_system(page: Any, url: str) -> None:
    """Land directly on Settings > System (the scope selects the pane)."""
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    page.evaluate("""() => {
        sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "configure-settings", scope: "system"})
        );
    }""")
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    # PHILO-17 U35: the identity tokens live in the System RAW fold (attached, folded).
    page.locator('[data-testid="runtime-backend"]').wait_for(state="attached", timeout=15_000)


def _shot(page: Any, name: str) -> Path:
    _settle(page)
    SHOTS.mkdir(parents=True, exist_ok=True)
    fp = SHOTS / f"{name}.png"
    page.screenshot(path=str(fp), full_page=True)
    return fp


def _assert_library_only(page: Any) -> None:
    """Every verb in the runtime block is the library Button."""
    raw = page.evaluate("""() => {
        const row = document.querySelector('[data-testid="runtime-backend"]');
        if (!row) return -1;
        const group = row.closest('.gadget-group') || document;
        let raw = 0;
        for (const btn of group.querySelectorAll('button')) {
            if (!btn.classList.contains('btn') && !btn.classList.contains('btn--chrome') &&
                !btn.classList.contains('surface-ledger-line') &&
                !btn.classList.contains('gadget-cycle')) raw++;
        }
        return raw;
    }""")
    assert raw == 0, f"Found {raw} raw <button> elements in the runtime block"


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_runtime_identity_healthy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
) -> None:
    """A matched hub shows its identity and flies no repair chip."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    from holdspeak import runtime_identity as ri
    from holdspeak import runtime_lock as rl

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        # This process is the hub: capture its identity and claim its database.
        import holdspeak.db.core as db_core

        ri.reset_runtime_identity()
        ri.capture_runtime_identity(db_path=Path(db_core.DEFAULT_DB_PATH), force=True)
        rl.claim_database(Path(db_core.DEFAULT_DB_PATH), port=server.port)

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            _navigate_to_system(page, url)

            assert page.locator('[data-testid="runtime-repair"]').count() == 0
            # PHILO-17 U35: build hashes and the schema are diagnostics: folded
            # under RAW until he opens it.
            assert not page.locator('[data-testid="runtime-schema"]').is_visible()
            fold = page.locator("details.gadget-fold", has=page.locator('[data-testid="runtime-backend"]'))
            fold.locator("summary").click()
            page.locator('[data-testid="runtime-backend"]').wait_for(timeout=5_000)
            assert page.locator('[data-testid="runtime-schema"]').inner_text().startswith("SCHEMA ")
            assert page.locator('[data-testid="runtime-bundle"]').inner_text() != "NONE"
            assert page.locator('[data-testid="runtime-document"]').inner_text() != "NONE"
            _assert_library_only(page)

            suffix = "desktop" if width == 1440 else "phone"
            assert _shot(page, f"runtime-identity-healthy-{suffix}").exists()
            _assert_clean(page, errors)
            browser.close()
    finally:
        rl.release_database()
        ri.reset_runtime_identity()
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
@pytest.mark.parametrize("width", [1440, 393])
def test_runtime_identity_stale_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    width: int,
) -> None:
    """The checkout moved under the process: STALE BUNDLE, path in RAW only."""
    _ensure_build()
    from playwright.sync_api import sync_playwright

    from holdspeak import runtime_identity as ri
    from holdspeak import runtime_lock as rl

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        import holdspeak.db.core as db_core

        ri.reset_runtime_identity()
        ri.capture_runtime_identity(db_path=Path(db_core.DEFAULT_DB_PATH), force=True)
        rl.claim_database(Path(db_core.DEFAULT_DB_PATH), port=server.port)
        # Rebuild the bundle under the running process. The hub reads the
        # on-disk stamp through read_bundle_build_id; patch that read, never
        # the shared stamp file: two xdist workers rewrote and "restored" it
        # in parallel and left 0000rebuilt0000 behind (PHILO-17 words: the
        # healthy leg then saw STALE BUNDLE).
        monkeypatch.setattr(ri, "read_bundle_build_id", lambda directory=None: "0000rebuilt0000")

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda error: errors.append(str(error)))

            _navigate_to_system(page, url)

            chips = page.locator('[data-testid="runtime-repair"]')
            assert chips.count() == 1
            assert "STALE BUNDLE" in chips.inner_text()
            # C1: the filesystem path never sits on the ordinary surface.
            path_cell = page.locator('[data-testid="runtime-path"]')
            assert path_cell.count() == 1
            assert not path_cell.is_visible(), "the database path is outside the RAW fold"
            _assert_library_only(page)

            suffix = "desktop" if width == 1440 else "phone"
            assert _shot(page, f"runtime-identity-stale-{suffix}").exists()
            _assert_clean(page, errors)
            browser.close()
    finally:
        rl.release_database()
        ri.reset_runtime_identity()
        server.stop()
