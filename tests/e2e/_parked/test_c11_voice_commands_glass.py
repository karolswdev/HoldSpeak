"""C11 voice-command glass: authenticated Talk -> real Desk write -> sticky.

The server-side command path is the real websocket and composition-root MCP
dispatcher. The only speech seam is the transcription leaf, so this test does
not replace dispatch or fabricate a Desk result. Chromium supplies a real
authenticated microphone stream at both owner viewport sizes.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .glass_infra import _ensure_build
from .test_speak_glass import _boot, _init_desk, _stage_speak, _settle

pytest.importorskip("playwright.sync_api", reason="C11 voice command glass needs Playwright")
pytestmark = [pytest.mark.e2e, pytest.mark.timeout(120, method="thread")]

REPO = Path(__file__).resolve().parents[2]
TOKEN = "c11-voice-command-glass"
WAV = REPO / "tests/fixtures/core_path_smoke_16k.wav"
SHOTS = evidence_dir("c11-voice-command-glass")


def _ready_speech(self: Any, principal: Any = None) -> dict[str, Any]:
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


@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_new_note_voice_command_creates_and_opens_the_returned_sticky(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int, height: int
) -> None:
    from holdspeak.services.local_ai_setup_service import LocalAISetupService

    # Readiness is a service read. It does not replace the command dispatcher,
    # the MCP operation, the database, or the browser's authenticated socket.
    monkeypatch.setattr(LocalAISetupService, "status", _ready_speech)
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
                "--use-file-for-fake-audio-capture=" + str(WAV),
            ])
            page = browser.new_page(viewport={"width": width, "height": height})
            _init_desk(page, url, token=TOKEN)
            _stage_speak(page)

            # The chair also owns a Talk button. The command must travel through
            # the Speak face's authenticated stream, so scope both controls to
            # that face rather than relying on DOM order.
            speak_face = page.locator(".speak-face")
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
