"""HS-201-02 integration path: fixture WAV to saved meeting transcript."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.unit.test_hs201_record_speech_only import _speech_only_session


pytestmark = pytest.mark.timeout(90, method="signal")


def test_record_fixture_wav_saves_nonempty_transcript_without_summary_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Record and Stop use the fixture WAV path without microphone capture."""
    db, session = _speech_only_session(tmp_path, monkeypatch)

    session.start()
    stopped = session.stop()
    saved = db.meetings.get_meeting(stopped.id)

    assert saved is not None
    assert saved.capture_status == "finalized"
    assert saved.transcription_status == "active"
    assert [segment.text for segment in saved.segments] == ["fixture speech transcript"]
    assert db.intel.get_intel_job(saved.id) is None
    assert "admission refused" not in caplog.text.lower()
