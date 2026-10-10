"""PHILO-17 transcribe — the meeting saved with its audio only gets ONE verb.

A meeting recorded while speech was not set up keeps its audio (the real
capture journal) and says "NO TRANSCRIPT · SPEECH NOT SET UP" (#1066). While
speech is still not set up, the record offers "Set up speech" and no
Transcribe. Once speech is set up (a readiness double: the rig never
downloads), the record and its list row offer "Transcribe"; a press writes
the transcript into the SAME meeting (a replay transcriber: no model).

Shots land in .tmp/evidence-shots/philo17/transcribe/<step>-<width>.png.
"""
from __future__ import annotations

import re
import wave
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from .glass_infra import _api, _api_allow_error, _assert_clean, _boot, _ensure_build, _normal_chair, _settle
from tests._evidence import evidence_dir

pytest.importorskip("playwright.sync_api", reason="transcribe glass needs Playwright")

SHOTS = evidence_dir("philo17/transcribe")
SHOTS.mkdir(parents=True, exist_ok=True)
TOKEN = "philo17-transcribe"
MEETING = "p17-audio-only"
LINE = "we ship the speech fix on friday"
FIXTURE_WAV = Path(__file__).parents[1] / "fixtures" / "core_path_smoke_16k.wav"


class _ReplayTranscriber:
    def transcribe(self, _audio: Any, **_kwargs: Any) -> str:
        return LINE


def _seed_audio_only(db: Any) -> None:
    """A meeting saved record-only (speech_not_set_up), its audio in the real journal."""
    from holdspeak.meeting_capture_journal import MeetingCaptureJournal
    from holdspeak.meeting_session import MeetingState

    now = datetime.now()
    meeting = MeetingState(
        id=MEETING, title="Standup with audio only",
        started_at=now - timedelta(minutes=2), ended_at=now, segments=[],
    )
    meeting.capture_status = "finalized"
    meeting.intel_status = "disabled"
    meeting.transcription_status = "record_only"
    meeting.transcription_status_detail = {
        "family": "speech-recognition-route-assignments",
        "reason_code": "speech_not_set_up",
        "repair": "set_up_speech",
    }
    db.meetings.save_meeting(meeting)
    with wave.open(str(FIXTURE_WAV), "rb") as wav:
        audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    journal = MeetingCaptureJournal(MEETING)
    journal.append("mic", audio)
    journal.finalize()


def _open_meetings(page: Any) -> None:
    page.evaluate("""() => {
        localStorage.removeItem('hs.desk.workspace.v1');
        sessionStorage.setItem('hs.desk.staged-surface-open', JSON.stringify({key:'review-meetings'}));
    }""")
    page.reload(wait_until="load")
    _normal_chair(page)
    row = page.get_by_test_id(f"meeting-row-{MEETING}")
    row.wait_for(timeout=20_000)


def _open_record(page: Any) -> None:
    page.get_by_test_id(f"meeting-row-{MEETING}").locator(".meetings-stream-row-body").click()
    page.get_by_test_id("meeting-speech-missing").first.wait_for(timeout=20_000)


def _shot(page: Any, name: str, width: int) -> None:
    _settle(page)
    path = SHOTS / f"{name}-{width}.png"
    page.screenshot(path=str(path))
    assert path.stat().st_size > 2_000


@pytest.mark.e2e
@pytest.mark.parametrize("width,height", [(1440, 900), (393, 852)])
def test_an_audio_only_meeting_is_transcribed_in_place(tmp_path: Path, monkeypatch: Any, width: int, height: int) -> None:
    from holdspeak.db import get_database
    from holdspeak.kernel.runtime import _configure
    from holdspeak.web.routes import meeting_import as import_route

    _ensure_build()
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people-keys.json"))
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    db = get_database()
    _configure(db)
    monkeypatch.setattr(import_route, "_transcriber_factory", lambda _cfg: _ReplayTranscriber())
    _seed_audio_only(db)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_viewport_size({"width": width, "height": height})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
            _api(page, "POST", "/api/desk/seed", token=TOKEN)
            _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
            _normal_chair(page)

            # 1. Speech not set up (the rig HOME has no model): Set up speech, no Transcribe.
            assert _api(page, "GET", "/api/setup/local-ai", token=TOKEN)["speech"]["ready"] is False
            _open_meetings(page)
            _open_record(page)
            setup = page.get_by_test_id("meeting-transcribe-speech-setup-verb")
            setup.wait_for(timeout=20_000)
            assert re.match(r"^Set up speech · \d+ MB$", setup.inner_text().strip()), setup.inner_text()
            assert page.get_by_role("button", name="Transcribe", exact=True).count() == 0
            status, refused = _api_allow_error(page, "POST", f"/api/meetings/{MEETING}/transcribe", token=TOKEN)
            assert status == 409 and refused.get("code") == "speech_not_set_up", (status, refused)
            _shot(page, "not-set-up", width)

            # 2. Speech set up (a readiness double): the row and the record say Transcribe.
            monkeypatch.setattr(
                "holdspeak.whisper_models.speech_readiness",
                lambda name, backend, *, home=None: {
                    "model": name or "base", "backend": "mlx", "state": "on_device", "ready": True, "bytes": 0,
                },
            )
            _open_meetings(page)
            _open_record(page)
            record_verb = page.get_by_test_id("meeting-transcribe-verb")
            record_verb.wait_for(timeout=20_000)
            assert record_verb.inner_text().strip() == "Transcribe"
            if width >= 1440:
                # The narrowed rail keeps the row's verb at desktop width.
                assert page.get_by_test_id("row-transcribe-verb").count() == 1
            _shot(page, "ready", width)

            # 3. Transcribe: the transcript lands on the SAME meeting.
            record_verb.click()
            page.locator("#surface-meetings").get_by_text(LINE, exact=True).first.wait_for(timeout=30_000)
            saved = db.meetings.get_meeting(MEETING)
            assert saved is not None and [seg.text for seg in saved.segments] == [LINE]
            assert saved.transcription_status == "complete"
            assert page.get_by_test_id("meeting-transcribe-verb").count() == 0
            assert page.get_by_test_id("meeting-speech-missing").count() == 0
            _shot(page, "transcribed", width)
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
