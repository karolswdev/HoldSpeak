"""HS-93-06 — kill/recovery determinism (the criterion-1 automatable core).

A real child process runs a real MeetingSession against a real SQLite database
and a real capture journal, checkpoints a transcript, and is SIGKILLed at the
``meeting.finalize_kill`` fault point — between the last durable checkpoint and
the finalize transaction. A restart (a fresh database handle, the recovery
path) must resume the SAME meeting identity: finalize-or-recoverable, no
duplicate meeting, transcript prefix intact.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.meeting_capture_journal import MeetingCaptureJournal

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_PREFIX = "the durable transcript prefix"

_CHILD_SOURCE = textwrap.dedent(
    f"""
    import json, os
    from pathlib import Path

    from holdspeak.db import get_database

    get_database(Path(os.environ["HS_KILL_DB"]))

    import numpy as np

    import holdspeak.meeting_session.session as session_module
    from holdspeak.meeting_recorder import AudioChunk
    from holdspeak.meeting_session import MeetingSession


    class Recorder:
        def __init__(self, **kwargs):
            self.on_audio_chunk = kwargs.get("on_audio_chunk")

        def start(self):
            pass

        def stop(self):
            audio = np.zeros(32000, dtype=np.float32)
            chunk = AudioChunk(audio=audio, timestamp=0.0, source="mic", duration=2.0)
            if self.on_audio_chunk is not None:
                self.on_audio_chunk(chunk)
            return [chunk], []

        def get_pending_chunks(self, since=0.0):
            return [], []

        def get_pending_device_chunks(self):
            return {{}}

        def trim_before(self, timestamp):
            pass


    class Transcriber:
        def transcribe(self, _audio):
            return {EXPECTED_PREFIX!r}


    session_module.MeetingRecorder = Recorder
    session = MeetingSession(transcriber=Transcriber())
    state = session.start()
    print(json.dumps({{"meeting_id": state.id}}), flush=True)
    session.stop()
    print("FINALIZED", flush=True)
    """
)


def _run_child(tmp_path: Path, *, fault: str | None) -> tuple[subprocess.CompletedProcess, str]:
    runner = tmp_path / "runner.py"
    runner.write_text(_CHILD_SOURCE, encoding="utf-8")
    env = dict(os.environ)
    env.pop("HOLDSPEAK_FAULT", None)
    env.update(
        {
            "HOME": str(tmp_path),
            "HS_KILL_DB": str(tmp_path / "hs.db"),
            "PYTHONPATH": str(REPO_ROOT),
        }
    )
    if fault is not None:
        env["HOLDSPEAK_FAULT"] = fault
    proc = subprocess.run(
        [sys.executable, str(runner)],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    first_line = (proc.stdout or "").strip().splitlines()
    meeting_id = json.loads(first_line[0])["meeting_id"] if first_line else ""
    return proc, meeting_id


@pytest.mark.integration
def test_kill_between_checkpoint_and_finalize_recovers_same_identity(tmp_path):
    proc, meeting_id = _run_child(tmp_path, fault="meeting.finalize_kill")

    # The child truly died by SIGKILL before finalize could run.
    assert proc.returncode == -signal.SIGKILL, proc.stderr
    assert meeting_id, proc.stdout
    assert "FINALIZED" not in proc.stdout

    # Crash-state truth: one provisional meeting at its last durable checkpoint.
    db = Database(tmp_path / "hs.db")
    meetings = db.meetings.list_meetings()
    assert [m.id for m in meetings] == [meeting_id], "exactly one meeting, no ghost"
    crashed = db.meetings.get_meeting(meeting_id)
    assert crashed.capture_status == "recording"
    assert crashed.ended_at is None
    assert crashed.capture_checkpoint_at is not None
    assert [s.text for s in crashed.segments] == [EXPECTED_PREFIX]

    # The audio journal still advertises the capture as recoverable, with
    # durable (fsynced) bytes claimed for the checkpointed audio.
    captures_root = tmp_path / ".local" / "share" / "holdspeak" / "meeting-captures"
    recoverable = MeetingCaptureJournal.recoverable(captures_root)
    assert [r["meeting_id"] for r in recoverable] == [meeting_id]
    assert recoverable[0]["status"] == "recording"
    assert recoverable[0]["durable_bytes"].get("mic", 0) > 0

    # Restart: a fresh handle recovers the SAME identity to a closed state.
    restarted = Database(tmp_path / "hs.db")
    recovered = restarted.meetings.recover_capture(meeting_id)
    assert recovered is not None
    assert recovered.id == meeting_id
    assert recovered.capture_status == "recovered"
    assert recovered.ended_at == crashed.capture_checkpoint_at
    assert [s.text for s in recovered.segments] == [EXPECTED_PREFIX]

    # No duplicate object was minted by the crash or the recovery; a repeated
    # recovery converges on the same closed state.
    assert [m.id for m in restarted.meetings.list_meetings()] == [meeting_id]
    again = restarted.meetings.recover_capture(meeting_id)
    assert again.id == meeting_id
    assert again.capture_status == "recovered"
    assert [m.id for m in restarted.meetings.list_meetings()] == [meeting_id]


@pytest.mark.integration
def test_same_run_without_fault_finalizes_cleanly(tmp_path):
    """Control lane: the identical child with the plane unarmed finalizes —
    proving the armed env is the ONLY difference (off means off)."""
    proc, meeting_id = _run_child(tmp_path, fault=None)

    assert proc.returncode == 0, proc.stderr
    assert "FINALIZED" in proc.stdout

    db = Database(tmp_path / "hs.db")
    assert [m.id for m in db.meetings.list_meetings()] == [meeting_id]
    finalized = db.meetings.get_meeting(meeting_id)
    assert finalized.capture_status == "finalized"
    assert finalized.ended_at is not None
    assert [s.text for s in finalized.segments] == [EXPECTED_PREFIX]

    captures_root = tmp_path / ".local" / "share" / "holdspeak" / "meeting-captures"
    assert MeetingCaptureJournal.recoverable(captures_root) == []
