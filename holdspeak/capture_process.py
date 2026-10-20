"""Child-process owner for native meeting capture (C10).

The desk process owns the Meeting identity and transcription state.  This
process owns PortAudio and the capture journal.  The pipe carries only control,
levels, and already durable PCM notifications; a stuck native close therefore
cannot hold the desk process or its audio floor.
"""

from __future__ import annotations

import threading
from multiprocessing.connection import Connection
from pathlib import Path
from queue import Empty, Full, Queue
from typing import Any

import numpy as np


_EVENT_QUEUE_MAX = 512


def run_capture_process(connection: Connection, config: dict[str, Any]) -> None:
    """Run one capture child until the parent asks it to stop."""
    from .meeting_capture_journal import MeetingCaptureJournal
    from .meeting_recorder import MeetingRecorder

    events: Queue[dict[str, Any] | None] = Queue(maxsize=_EVENT_QUEUE_MAX)

    def emit(event: dict[str, Any]) -> None:
        # Levels are advisory and may be dropped when the desk is slow. PCM,
        # readiness and terminal events are part of the capture contract:
        # block until the sender accepts them so the parent cannot finalize a
        # snapshot without knowing that the child delivered its outcome.
        if event.get("type") == "level":
            try:
                events.put_nowait(event)
            except Full:
                return
        else:
            events.put(event)

    def send_events() -> None:
        while True:
            event = events.get()
            try:
                if event is None:
                    return
                try:
                    connection.send(event)
                except (BrokenPipeError, EOFError, OSError):
                    return
            finally:
                events.task_done()

    sender = threading.Thread(target=send_events, name="capture-event-sender", daemon=True)
    sender.start()

    meeting_id = str(config["meeting_id"])
    journal = MeetingCaptureJournal(
        meeting_id,
        sample_rate=int(config["sample_rate"]),
        directory=Path(str(config["capture_directory"])),
    )

    def on_audio_chunk(chunk) -> None:
        # Checkpoint each accepted child chunk.  This is intentionally modest
        # pre-alpha work and makes a parent deadline safe: bytes already
        # admitted to the C9 writer are durable before their pipe notice.
        journal.append(chunk.source, chunk.audio)
        journal.checkpoint()
        emit(
            {
                "type": "chunk",
                "source": chunk.source,
                "timestamp": chunk.timestamp,
                "duration": chunk.duration,
                "audio": np.asarray(chunk.audio, dtype="<f4").tobytes(),
            }
        )

    def on_level(level: float, source: str) -> None:
        emit({"type": "level", "source": source, "level": float(level)})

    recorder = MeetingRecorder(
        sample_rate=int(config["sample_rate"]),
        mic_device=config.get("mic_device"),
        system_device=config.get("system_device"),
        chunk_duration=float(config.get("chunk_duration", 2.0)),
        on_mic_level=lambda level: on_level(level, "mic"),
        on_system_level=lambda level: on_level(level, "system"),
        on_audio_chunk=on_audio_chunk,
    )

    try:
        recorder.start()
        emit({"type": "ready"})
        while True:
            if not connection.poll(0.05):
                continue
            command = connection.recv()
            if not isinstance(command, dict) or command.get("command") != "stop":
                continue

            error: str | None = None
            try:
                recorder.stop()
            except Exception as exc:
                error = f"Capture child stop failed: {exc}"
            try:
                journal.seal()
            except Exception as exc:
                error = error or f"Capture journal seal failed: {exc}"
            emit(
                {
                    "type": "stopped",
                    "error": error,
                    "device_cleanup_error": recorder.device_cleanup_error,
                    "capture_failure": recorder.capture_failure,
                }
            )
            break
    except Exception as exc:
        error = f"Capture child failed: {exc}"
        try:
            journal.mark_recoverable(error)
        except Exception:
            pass
        emit({"type": "error", "error": error})
    finally:
        # Preserve event order: all chunk and terminal notices are sent before
        # the child closes its end of the pipe.
        events.join()
        events.put(None)
        events.join()
        sender.join(timeout=1.0)
        try:
            connection.close()
        except Exception:
            pass

