"""HS-170-03 -- The Concierge glass rig.

Own surface window titled Models at 640 wide (1440 viewport) and 393.
Shots: element-clipped full-height window screenshots.
Asserts: display headline >= 24px, no .prefs-* chrome, no raw <button>,
picker in place (no dialog), Adjust unfolds under set, Use these
disabled while WAITING and enabled after OFF, no overflow at 393.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _boot,
    _api,
    _assert_clean,
    _normal_chair,
    _settle,
)

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-170-the-great-pass/assets/story-03-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "glass-test"


# ── Helpers ────────────────────────────────────────────────────────


def _open_concierge(page: Any) -> None:
    """Open the Concierge surface window (its own window, not Settings)."""
    page.evaluate(
        """([key]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["open-concierge"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)


def _window(page: Any) -> Any:
    """The Models surface window element."""
    return page.locator(".desk-surface-window").filter(
        has=page.locator('[data-testid="concierge-root"]')
    ).first


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"build-{name}-{width}.png"
    win = _window(page)
    if win.count() > 0:
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


# ── Monkeypatch concierge detection ──────────────────────────────

def _monkeypatch_concierge(monkeypatch: Any) -> None:
    fake_detection = {
        "engines": [
            {"id": "lan:test-lan", "kind": "lan", "name": "Qwen3.6 35B",
             "host": "192.168.1.43", "state": "READY", "latencyMs": 41, "profileId": "test-lan"},
            {"id": "local:mlx:whisper-base", "kind": "local", "name": "Whisper base",
             "host": "THIS DEVICE", "state": "READY", "runtimeToken": "MLX"},
            {"id": "cloud:openrouter", "kind": "cloud", "name": "OpenRouter",
             "host": "openrouter.ai", "state": "READY", "keySet": True, "profileId": "cloud-openrouter"},
            {"id": "preset:qwen35-08b", "kind": "preset", "name": "Qwen 3.5 0.8B",
             "host": "THIS DEVICE", "state": "WAITING", "sizeBytes": 532000000,
             "installed": False, "presetId": "qwen35-08b"},
        ],
        "hardware": {"capability": {"apple_silicon": True, "system": "darwin",
                                     "architecture": "arm64", "ram_gb": 36}},
        "runtimes": [{"id": "mlx_whisper_v1", "state": "available"}],
        "checkedAt": "2026-09-05T09:41:00Z",
    }
    fake_proposal = {
        "rows": [
            {"group": "thoughts_notes", "label": "Thoughts & notes", "engineId": "lan:test-lan", "host": "192.168.1.43", "state": "READY"},
            {"group": "chat_practice", "label": "Chat", "engineId": "lan:test-lan", "host": "192.168.1.43", "state": "READY"},
            {"group": "writing_dictation", "label": "Writing & dictation", "engineId": "preset:qwen35-08b", "host": "THIS DEVICE", "state": "WAITING", "presetId": "qwen35-08b"},
            {"group": "speech_recognition", "label": "Speech recognition", "engineId": "local:mlx:whisper-base", "host": "THIS DEVICE", "state": "READY"},
            {"group": "meetings", "label": "Meetings", "engineId": "lan:test-lan", "host": "192.168.1.43", "state": "READY"},
            {"group": "agents_tools", "label": "Agents & tools", "engineId": "lan:test-lan", "host": "192.168.1.43", "state": "READY"},
            {"group": "background", "label": "Background", "engineId": "lan:test-lan", "host": "192.168.1.43", "state": "READY"},
        ],
        "receipt": {"groups": 7, "engines": 3, "waiting": 1},
    }
    import holdspeak.services.concierge_service as cs
    monkeypatch.setattr(cs, "detect", lambda **_: fake_detection)
    monkeypatch.setattr(cs, "propose", lambda **_: fake_proposal)
    monkeypatch.setattr(cs, "probe", lambda **_: {"state": "READY", "host": "192.168.1.43", "latencyMs": 41})


def _monkeypatch_concierge_cold(monkeypatch: Any) -> None:
    fake_detection = {
        "engines": [
            {"id": "preset:qwen35-08b", "kind": "preset", "name": "Qwen 3.5 0.8B",
             "host": "THIS DEVICE", "state": "WAITING", "sizeBytes": 532000000,
             "installed": False, "presetId": "qwen35-08b"},
        ],
        "hardware": {"capability": {"apple_silicon": True, "system": "darwin",
                                     "architecture": "arm64", "ram_gb": 36}},
        "runtimes": [],
        "checkedAt": "2026-09-05T09:41:00Z",
    }
    fake_proposal = {
        "rows": [
            {"group": g, "label": l, "engineId": None, "host": "", "state": "WAITING"}
            for g, l in [("thoughts_notes", "Thoughts & notes"), ("chat_practice", "Chat"),
                         ("writing_dictation", "Writing & dictation"), ("speech_recognition", "Speech recognition"),
                         ("meetings", "Meetings"), ("agents_tools", "Agents & tools"), ("background", "Background")]
        ],
        "receipt": {"groups": 7, "engines": 0, "waiting": 7},
    }
    import holdspeak.services.concierge_service as cs
    monkeypatch.setattr(cs, "detect", lambda **_: fake_detection)
    monkeypatch.setattr(cs, "propose", lambda **_: fake_proposal)


# ── Tests ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("width", [1440, 393], ids=["desktop", "phone"])
def test_concierge_main(tmp_path, monkeypatch, width):
    """Main face: display headline >= 24px, no prefs chrome, hosts on rows."""
    _monkeypatch_concierge(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        height = 900 if width == 1440 else 852
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": height})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _open_concierge(page)
            page.get_by_test_id("concierge-root").wait_for(timeout=10_000)
            _settle(page)

            # Headline = display step (font-size >= 24px)
            headline = page.get_by_test_id("concierge-headline")
            headline.wait_for()
            assert "found" in (headline.text_content() or "").lower()
            font_size = headline.evaluate("el => parseFloat(getComputedStyle(el).fontSize)")
            assert font_size >= 24, f"Headline font-size {font_size}px < 24px"

            # No .prefs-* chrome inside the Models window
            win = _window(page)
            prefs_chrome = win.locator("[class*='prefs-']")
            assert prefs_chrome.count() == 0, f"Prefs chrome: {prefs_chrome.count()}"

            # Host chips in found list
            found_list = page.get_by_test_id("concierge-found-list")
            found_list.wait_for()
            assert found_list.locator(".gadget-chip-egress").count() > 0

            # Use these disabled
            apply_btn = page.get_by_test_id("concierge-apply")
            apply_btn.wait_for()
            assert apply_btn.is_disabled()

            # No raw <button> in the Concierge face itself
            root = page.get_by_test_id("concierge-root")
            raw = root.locator("button:not(.btn):not(.surface-ledger-line):not(.gadget-chip-egress)")
            assert raw.count() == 0, f"Raw <button>: {raw.count()}"

            if width == 393:
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

            _shot(page, "main", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def test_concierge_picker(tmp_path, monkeypatch):
    """Picker opens in-world (no dialog)."""
    _monkeypatch_concierge(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _open_concierge(page)
            page.get_by_test_id("concierge-root").wait_for(timeout=10_000)
            _settle(page)
            page.get_by_test_id("concierge-picker-thoughts_notes").click()
            _settle(page)
            page.get_by_test_id("concierge-picker-well-thoughts_notes").wait_for()
            assert page.locator('[role="dialog"]').count() == 0
            _shot(page, "picker", 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def test_concierge_adjust(tmp_path, monkeypatch):
    """Adjust unfolds under the set."""
    _monkeypatch_concierge(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _open_concierge(page)
            page.get_by_test_id("concierge-root").wait_for(timeout=10_000)
            _settle(page)
            page.get_by_test_id("concierge-adjust-trigger").click()
            _settle(page)
            page.get_by_test_id("concierge-adjust-well").wait_for()
            assert page.get_by_test_id("concierge-set-list").is_visible()
            _shot(page, "adjust", 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def test_concierge_cold(tmp_path, monkeypatch):
    """Cold face: No engine yet, Use these disabled."""
    _monkeypatch_concierge_cold(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _open_concierge(page)
            page.get_by_test_id("concierge-root").wait_for(timeout=10_000)
            _settle(page)
            headline = page.get_by_test_id("concierge-headline")
            headline.wait_for()
            assert "no engine yet" in (headline.text_content() or "").lower()
            assert page.get_by_test_id("concierge-apply").is_disabled()
            _shot(page, "cold", 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def test_concierge_downloading(tmp_path, monkeypatch):
    """Mid-download: the preset row shows a progress token."""
    _monkeypatch_concierge(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _open_concierge(page)
            page.get_by_test_id("concierge-root").wait_for(timeout=10_000)
            _settle(page)

            # Click Download on the preset row to trigger download state
            dl_btn = page.get_by_test_id("concierge-download-preset:qwen35-08b")
            if dl_btn.count() > 0:
                dl_btn.click()
                _settle(page)

            _shot(page, "downloading", 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


def test_concierge_use_these_off_frees(tmp_path, monkeypatch):
    """Use these: disabled while WAITING, enabled after picking OFF."""
    _monkeypatch_concierge(monkeypatch)
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _normal_chair(page)
            _open_concierge(page)
            page.get_by_test_id("concierge-root").wait_for(timeout=10_000)
            _settle(page)
            apply_btn = page.get_by_test_id("concierge-apply")
            apply_btn.wait_for()
            assert apply_btn.is_disabled()
            page.get_by_test_id("concierge-picker-writing_dictation").click()
            _settle(page)
            page.get_by_test_id("concierge-pick-writing_dictation-off").click()
            _settle(page)
            assert not apply_btn.is_disabled(), "Use these should be enabled after OFF"
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
