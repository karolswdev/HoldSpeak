"""Current Speak rows, the hold-key repair door and authenticated voice commands.

The retired five-wing and permission-chip drawing checks are parked in
_parked/test_speak_five_wings_20261110.py.txt. Domain teach/custody wires
remain covered by tests/unit/test_desk_speak.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _assert_clean,
    _ensure_build,
    _normal_chair,
    _settle,
)
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="this glass needs Playwright")



# ══ the learned loop (Speak) ═══════════════════════════════════════

SHOTS = evidence_dir("speak-glass")

SHOTS.mkdir(parents=True, exist_ok=True)

TOKEN = "speak-glass"

def _boot(
    tmp_path: Path,
    monkeypatch: Any,
    *,
    on_transcribe: Any = None,
    token: str = TOKEN,
) -> tuple[Any, str]:
    """An isolated durable hub for the current Speak journal read."""
    import os

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import Database, reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            Path.home() / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    database = Database(tmp_path / "holdspeak.db")

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
            on_transcribe=on_transcribe,
        ),
        auth_token=token,
        dictation_journal_repository=database.dictation_journal,
        dictation_corrections_repository=database.dictation_corrections,
    )
    return server, server.start()

def _init_desk(page: Any, url: str, *, token: str = TOKEN) -> None:
    page.goto(f"{url}/?token={token}", wait_until="load")
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=token)
    _normal_chair(page)

def _stage_speak(page: Any) -> None:
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key})
          );
        }""",
        ["dictate"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.get_by_test_id("speak-face").wait_for(timeout=15000)
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

@pytest.mark.e2e
def test_recent_dictation_row_wraps_without_overlap_at_393(tmp_path, monkeypatch):
    """The current journal row wraps its words and keeps Copy outside them."""
    from playwright.sync_api import sync_playwright, expect
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch)
    words = "Review the platform migration with each team and record the owner of every rollback step before Friday."
    stored = server.dictation_journal.repository.record(source="dictation", transcript=words, final_text=words, target_profile="terminal")
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(viewport={"width":393,"height":852},permissions=["clipboard-read","clipboard-write"])
            page = context.new_page()
            _init_desk(page, url)
            _stage_speak(page)
            row = page.get_by_test_id("speak-recent").locator(".speak-native-row").first
            expect(row).to_contain_text(stored.final_text)
            assert row.evaluate("el => {const words=el.querySelector('div').getBoundingClientRect(),verb=el.querySelector('button').getBoundingClientRect();return words.right + 6 <= verb.left && el.scrollWidth <= el.clientWidth + 1}")
            row.get_by_role("button",name="Copy",exact=True).click()
            expect(page.get_by_test_id("speak-footer")).to_contain_text("Copied")
            assert page.evaluate("() => navigator.clipboard.readText()") == words
            _shot(page,"recent-row",393)
            browser.close()
    finally:
        server.stop()


# ══ the hotkey custody block (was test_hs200_voice_custody_glass.py) ═══

CUSTODY_SHOTS = evidence_dir("pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-05-shots")

CUSTODY_SHOTS.mkdir(parents=True, exist_ok=True)

CUSTODY_TOKEN = "hs200-05-custody"

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

def _custody_boot(tmp_path: Path, monkeypatch: Any) -> tuple[Any, str, _Platform]:
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
        auth_token=CUSTODY_TOKEN,
    )
    return server, server.start(), machine

def _custody_init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={CUSTODY_TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=CUSTODY_TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=CUSTODY_TOKEN)
    _normal_chair(page)

def _custody_stage_speak(page: Any) -> None:
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
    page.get_by_test_id("speak-face").wait_for(timeout=20000)
    _settle(page)

def _custody_shot(page: Any, name: str, width: int) -> Path:
    _settle(page)
    path = CUSTODY_SHOTS / f"{name}-{width}.png"
    target = page.locator(".desk-surface-window").first
    if target.count() > 0:
        target.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.stat().st_size > 2_000, f"Shot {name} too small ({path.stat().st_size})"
    return path

def _no_overflow(block: Any, width: int) -> None:
    assert block.evaluate("el => el.scrollWidth <= el.clientWidth + 1"), f"Hold-key notice overflows at {width}"
    assert block.evaluate("el => {const reason=el.querySelector('span').getBoundingClientRect(),verb=el.querySelector('button').getBoundingClientRect();return Math.min(reason.right,verb.right)-Math.max(reason.left,verb.left)<=1 || Math.min(reason.bottom,verb.bottom)-Math.max(reason.top,verb.top)<=1}")


def _walk(page: Any, machine: _Platform, width: int) -> None:
    """Every refused state uses the current notice and one repair door."""
    from playwright.sync_api import expect
    for name, prepare in (("all-denied",machine.all_denied),("one-denied",machine.one_denied),("not-asked",machine.never_asked),("listener-failed",machine.listener_failed)):
        prepare()
        _custody_stage_speak(page)
        block = page.get_by_test_id("speak-hotkey")
        expect(block).to_be_visible()
        wire = _api(page,"GET","/api/dictation/readiness",token=CUSTODY_TOKEN)["hotkey"]
        expected = wire.get("reason") or "Hold key needs attention"
        expect(block.locator("span").first).to_have_text(expected)
        expect(block.get_by_role("button",name="Fix hold key",exact=True)).to_be_visible()
        assert "pynput is not available" not in block.inner_text()
        _no_overflow(block,width)
        _custody_shot(page,name,width)
    block.get_by_role("button",name="Fix hold key",exact=True).click()
    expect(page.locator('#surface-settings [data-settings-section="speak"]')).to_be_visible()
    machine.all_granted()
    _custody_stage_speak(page)
    expect(page.get_by_test_id("speak-hotkey")).to_have_count(0)
    _custody_shot(page,"all-granted",width)


@pytest.mark.e2e
@pytest.mark.requires_meeting
def test_hotkey_custody_block_1440(tmp_path, monkeypatch):
    """The five custody states at 1440."""
    _ensure_build()
    server, url, machine = _custody_boot(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 1440, "height": 900})
            _custody_init_desk(page, url)
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
    server, url, machine = _custody_boot(tmp_path, monkeypatch)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": 393, "height": 852})
            _custody_init_desk(page, url)
            _walk(page, machine, 393)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# Voice command: authenticated Talk → real stored note → the returned sticky.
def _voice_command_ready_speech(self: Any, principal: Any = None) -> dict[str, Any]:
    """The disk-read speech seam: this rig supplies a ready local model."""
    _ = self, principal
    return {
        "state": "ready",
        "files": [{"key": "whisper", "label": "Speech", "size_bytes": 1, "on_device": True}],
        "bytes_total": 0,
        "bytes_done": 0,
        "percent": 100,
        "egress": None,
        "speech": {"model": "base", "backend": "auto", "state": "on_device", "ready": True, "bytes": 0},
        "local_engine": {"ready": True},
        "meaning_search": "on",
        "error": "",
        "error_code": "",
    }


@pytest.mark.timeout(120, method="thread")
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_new_note_voice_command_creates_and_opens_the_returned_sticky(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int
) -> None:
    import os
    from holdspeak.services.local_ai_setup_service import LocalAISetupService

    # Readiness is a service read. It does not replace the command dispatcher,
    # the MCP operation, the database, or the browser's authenticated socket.
    monkeypatch.setattr(LocalAISetupService, "status", _voice_command_ready_speech)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / "Library/Caches/ms-playwright")
    ))
    _ensure_build()

    server, url = _boot(
        tmp_path,
        monkeypatch,
        on_transcribe=lambda _audio, **_kwargs: "new note",
        token=TOKEN,
    )
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=[
                "--use-fake-ui-for-media-stream",
                "--use-fake-device-for-media-stream",
                "--use-file-for-fake-audio-capture=" + str(Path(__file__).resolve().parents[2] / "tests/fixtures/core_path_smoke_16k.wav"),
            ])
            page = browser.new_page(viewport={"width": width, "height": height})
            _init_desk(page, url, token=TOKEN)
            _stage_speak(page)

            # The chair also owns a Talk button. The command must travel through
            # the Speak face's authenticated stream, so scope both controls to
            # that face rather than relying on DOM order.
            speak_face = page.get_by_test_id("speak-face")
            talk = speak_face.get_by_role("button", name="Talk")
            talk.wait_for(timeout=15_000)
            talk.click()
            stop = speak_face.get_by_role("button", name="Listening · Stop")
            stop.wait_for(timeout=15_000)
            page.wait_for_timeout(500)
            stop.click()

            sticky = page.locator("[id^='pullout:note:']").first
            sticky.wait_for(timeout=20_000)
            # The pullout id is the exact server-created note id carried by the
            # fired frame, and the API read proves that object was stored.
            note_id = sticky.get_attribute("id").removeprefix("pullout:note:")
            notes = page.evaluate(
                "async (token) => (await (await fetch('/api/notes', {headers: {Authorization: 'Bearer ' + token}})).json()).notes",
                TOKEN,
            )
            assert any(str(note.get("id")) == note_id for note in notes), notes
            assert page.locator(".speak-result").count() == 0
            _settle(page)
            shot = SHOTS / f"new-note-{width}.png"
            sticky.screenshot(path=str(shot))
            assert shot.stat().st_size > 2_000
            browser.close()
    finally:
        server.stop()
