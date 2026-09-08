"""HS-200-05 — the hotkey's custody block, on glass.

The defect this face answers: `web_runtime.py:538-559` recorded whether the
global hotkey listener installed and NOTHING read it (the curated status
payload at `runtime/activity.py:171` dropped both keys), so the owner pressed
Right Option, got silence, and had no way to learn the cause.

Everything below runs against a REAL booted hub under an isolated HOME, and
every row drawn is rendered by the real `SpeakFace` from the real
`GET /api/dictation/readiness` payload built by the real
`_helpers._hotkey_custody`.

Exactly two things are substituted, both at the PLATFORM seam, because a test
runner cannot revoke a macOS grant:

* the three permission probes (`_ax_is_process_trusted`,
  `_iohid_check_access`, `_av_authorization_status`) — the same seam the unit
  suite uses; each returns what macOS would have returned;
* the runtime's `on_get_status`, which on a real hub is
  `WebRuntime._get_runtime_status` — here a dict carrying the two keys that
  method now exposes.

Nothing about the route, the payload shape, the derivation
(`hotkeyCustody.ts`) or the face is faked.

The five states, at 1440 and 393:

1. **all-denied** — the full block: three rows, three paths.
2. **one-denied** — only the non-granted row draws; no decorative all-clear.
3. **not-asked** — `NOT ASKED`, the first-installer state (the app is not
   even listed in the pane yet).
4. **listener-failed** — the classified reason token beside a granted set.
5. **all-granted** — the block is ABSENT, reached by pressing the one verb
   (`Re-check`) after the grant was given, which is the ratified flow.

Shots land in
``pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-05-shots``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import _api, _assert_clean, _ensure_build, _normal_chair, _settle

pytest.importorskip("playwright.sync_api", reason="voice-custody glass needs Playwright")

SHOTS = (
    Path(__file__).resolve().parents[2]
    / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-05-shots"
)
SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "hs200-05-custody"

#: The platform values each state is built from — the real constants.
AX_TRUSTED, AX_NOT_TRUSTED = True, False
HID_GRANTED, HID_DENIED, HID_NEVER_ASKED = 0, 1, 2
AV_NEVER_ASKED, AV_DENIED, AV_GRANTED = 0, 2, 3


class _Platform:
    """The machine's answers, swappable between legs."""

    def __init__(self) -> None:
        self.ax = AX_TRUSTED
        self.hid = HID_GRANTED
        self.av = AV_GRANTED
        self.status: dict[str, Any] = {
            "global_hotkey_available": True,
            "global_hotkey_error": "",
        }

    def all_denied(self) -> None:
        self.ax, self.hid, self.av = AX_NOT_TRUSTED, HID_DENIED, AV_DENIED
        self.status = {"global_hotkey_available": False,
                       "global_hotkey_error": "OSError: permission denied by the operating system"}

    def one_denied(self) -> None:
        self.ax, self.hid, self.av = AX_TRUSTED, HID_DENIED, AV_GRANTED
        self.status = {"global_hotkey_available": True, "global_hotkey_error": ""}

    def never_asked(self) -> None:
        self.ax, self.hid, self.av = AX_NOT_TRUSTED, HID_NEVER_ASKED, AV_NEVER_ASKED
        self.status = {"global_hotkey_available": False, "global_hotkey_error": ""}

    def listener_failed(self) -> None:
        self.ax, self.hid, self.av = AX_TRUSTED, HID_GRANTED, AV_GRANTED
        self.status = {"global_hotkey_available": False,
                       "global_hotkey_error": "RuntimeError: pynput is not available."}

    def all_granted(self) -> None:
        self.ax, self.hid, self.av = AX_TRUSTED, HID_GRANTED, AV_GRANTED
        self.status = {"global_hotkey_available": True, "global_hotkey_error": ""}


def _boot(tmp_path: Path, monkeypatch: Any) -> tuple[Any, str, _Platform]:
    """A real hub whose PLATFORM answers (only) are ours to script."""
    import os

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak import desktop_permissions as perms
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH", Path.home() / "Library/Caches/ms-playwright"
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    machine = _Platform()
    # The platform seam, and ONLY the platform seam.
    monkeypatch.setattr(perms, "_is_macos", lambda: True)
    monkeypatch.setattr(perms, "_ax_is_process_trusted", lambda: machine.ax)
    monkeypatch.setattr(perms, "_iohid_check_access", lambda: machine.hid)
    monkeypatch.setattr(perms, "_av_authorization_status", lambda: machine.av)

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            # On the owner's desk this is `WebRuntime._get_runtime_status`.
            on_get_status=lambda: dict(machine.status),
        ),
        auth_token=TOKEN,
    )
    return server, server.start(), machine


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)


def _stage_speak(page: Any) -> None:
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem(
            "hs.desk.staged-surface-open", JSON.stringify({key})
          );
        }""",
        ["dictate"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".speak-face").wait_for(timeout=20000)
    _settle(page)


def _shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    target = page.locator(".desk-surface-window").first
    if target.count() > 0:
        target.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path


def _no_overflow(block: Any, width: int) -> None:
    """Nothing in the block may scroll sideways — the 393 law.

    Three path tokens plus a state chip on one row is exactly the shape that
    clips, so every row is measured, not eyeballed.
    """
    assert block.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), (
        f"the HOTKEY block overflows horizontally at {width}"
    )
    rows = block.locator(".speak-hotkey-row, .speak-hotkey-head")
    for i in range(rows.count()):
        row = rows.nth(i)
        assert row.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), (
            f"a HOTKEY row overflows horizontally at {width}: "
            f"{row.inner_text()!r}"
        )


def _one_grammar(block: Any, width: int) -> None:
    """The same object is never drawn two ways (UX canon D, first rule).

    The first draft flex-wrapped the row, and the shots caught what no unit
    test could: at 640 the state chip sat right on the first row and wrapped
    to the LEFT on the next two, and at 393 the last row's chip fell out of
    the block entirely.  Every row's chip must exist, and every row's chip
    must share one right edge.
    """
    rows = block.locator(".speak-hotkey-row")
    edges: list[float] = []
    for i in range(rows.count()):
        row = rows.nth(i)
        chip = row.locator(".surface-state-chip")
        assert chip.count() == 1, (
            f"row {row.locator('.speak-hotkey-name').inner_text()!r} "
            f"has {chip.count()} state chips at {width}"
        )
        box = chip.bounding_box()
        row_box = row.bounding_box()
        assert box is not None and row_box is not None
        # Inside its own row, not spilled past it.
        assert box["x"] + box["width"] <= row_box["x"] + row_box["width"] + 1, (
            f"a state chip spills out of its row at {width}"
        )
        edges.append(round(box["x"] + box["width"], 1))
    if edges:
        assert max(edges) - min(edges) <= 1.0, (
            f"the state chips are drawn at {len(set(edges))} different right "
            f"edges at {width}: {edges}"
        )


def _walk(page: Any, machine: _Platform, width: int) -> None:
    """The five states, in the order a first-time installer meets them."""

    # ── 1. every grant refused: the full block ──
    machine.all_denied()
    _stage_speak(page)
    block = page.locator('[data-testid="speak-hotkey"]')
    block.wait_for(timeout=15000)
    for pid in ("microphone", "input_monitoring", "accessibility"):
        row = page.locator(f'[data-testid="speak-permission-{pid}"]')
        assert row.count() == 1, f"{pid} row missing"
        text = row.inner_text()
        assert "SYSTEM SETTINGS" in text and "PRIVACY & SECURITY" in text, text
        assert "DENIED" in text, text
    assert "UNAVAILABLE" in block.inner_text()
    # never a modal, never a sentence
    assert page.locator('[role="dialog"]').count() == 0
    _no_overflow(block, width)
    _one_grammar(block, width)
    _shot(page, "all-denied", width)

    # ── 2. one refused: the granted two stay silent ──
    machine.one_denied()
    _stage_speak(page)
    block = page.locator('[data-testid="speak-hotkey"]')
    block.wait_for(timeout=15000)
    assert page.locator('[data-testid="speak-permission-input_monitoring"]').count() == 1
    assert page.locator('[data-testid="speak-permission-microphone"]').count() == 0
    assert page.locator('[data-testid="speak-permission-accessibility"]').count() == 0
    # The listener DID install, and the key still will not work. The head chip
    # must not claim ACTIVE over a DENIED row (the shots caught that green).
    head = block.locator(".speak-hotkey-head")
    assert "BLOCKED" in head.inner_text(), head.inner_text()
    assert "ACTIVE" not in head.inner_text(), head.inner_text()
    _no_overflow(block, width)
    _one_grammar(block, width)
    _shot(page, "one-denied", width)

    # ── 3. never asked: the first-installer state ──
    machine.never_asked()
    _stage_speak(page)
    block = page.locator('[data-testid="speak-hotkey"]')
    block.wait_for(timeout=15000)
    assert "NOT ASKED" in block.inner_text(), block.inner_text()
    # Accessibility has no not-determined answer; it reads DENIED beside them.
    assert "DENIED" in page.locator(
        '[data-testid="speak-permission-accessibility"]'
    ).inner_text()
    _no_overflow(block, width)
    _one_grammar(block, width)
    _shot(page, "not-asked", width)

    # ── 4. the listener itself failed, with every grant in hand ──
    machine.listener_failed()
    _stage_speak(page)
    block = page.locator('[data-testid="speak-hotkey"]')
    block.wait_for(timeout=15000)
    reason = page.locator('[data-testid="speak-hotkey-reason"]')
    assert reason.inner_text() == "PYNPUT MISSING", reason.inner_text()
    # The raw exception never reaches the face (UX canon A10).
    assert "pynput is not available" not in block.inner_text()
    # A granted set draws no permission rows at all.
    assert page.locator('[data-testid^="speak-permission-"]').count() == 0
    _no_overflow(block, width)
    _one_grammar(block, width)
    _shot(page, "listener-failed", width)

    # ── 5. he grants it and presses the ONE verb: the block goes away ──
    machine.all_granted()
    page.locator('[data-testid="speak-hotkey-recheck"]').click()
    page.locator('[data-testid="speak-hotkey"]').wait_for(state="detached", timeout=15000)
    assert page.locator('[data-testid="speak-hotkey"]').count() == 0
    # ...and nothing green took its place.
    assert "HOTKEY" not in page.locator(".speak-face").inner_text()
    _shot(page, "all-granted", width)


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hotkey_custody_block_1440(tmp_path, monkeypatch):
    """The five custody states at 1440."""
    _ensure_build()
    server, url, machine = _boot(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)
            _walk(page, machine, 1440)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hotkey_custody_block_393(tmp_path, monkeypatch):
    """The same five at 393, where the path tokens fight for room."""
    _ensure_build()
    server, url, machine = _boot(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 393, "height": 852})
            _init_desk(page, url)
            _walk(page, machine, 393)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_the_custody_the_face_draws_is_the_wire_the_route_serves(tmp_path, monkeypatch):
    """The face's rows and the route's payload are the same facts.

    Every assertion above rides the face; this one names the wire it rides, so
    a face that quietly stopped reading the block would fail here too.
    """
    _ensure_build()
    server, url, machine = _boot(tmp_path, monkeypatch)
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.set_viewport_size({"width": 1440, "height": 900})
            _init_desk(page, url)

            machine.all_denied()
            body = _api(page, "GET", "/api/dictation/readiness", token=TOKEN)
            hotkey = body["hotkey"]
            assert hotkey["available"] is False
            assert hotkey["reason"] == "PERMISSION REFUSED"
            assert sorted(hotkey["missing"]) == [
                "accessibility", "input_monitoring", "microphone",
            ]
            assert [p["state"] for p in hotkey["permissions"]] == ["denied"] * 3
            # The deep link is carried and deliberately UNSPENT (the verb is
            # `Re-check`; the orchestrator ruled no deep link, 2026-09-07).
            assert all(
                p["settings_url"].startswith("x-apple.systempreferences:")
                for p in hotkey["permissions"]
            )

            machine.all_granted()
            quiet = _api(page, "GET", "/api/dictation/readiness", token=TOKEN)["hotkey"]
            assert quiet["needs_attention"] is False and quiet["missing"] == []
            assert quiet["display"] == "⌥R"

            browser.close()
    finally:
        server.stop()
