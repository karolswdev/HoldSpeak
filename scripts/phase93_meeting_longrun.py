#!/usr/bin/env python3
"""HS-93-06 — the bounded long-run meeting capture protocol.

Drives a REAL ``MeetingWebServer`` (TCP, the production device-audio WebSocket
ingest route) plus a REAL ``MeetingSession`` with the real capture journal and
SQLite checkpoint pipeline, feeding synthetic audio at an accelerated pace on
two lanes:

- the **device lane**: int16 PCM frames over ``/api/devices/audio`` into the
  registry's ``RemoteAudioRecorder``, attached to the session exactly as the
  production runtime attaches a device;
- the **mic lane**: float32 chunks into the recorder's mic buffer, driving the
  journal's fsync appends and the meeting's checkpoint clock.

Only the hardware (PortAudio streams) and Whisper are synthetic — journal,
checkpoints, database, WebSocket ingest, transcription loop cadence, and the
served ``/api/state`` are the production code paths.

Each sample interval records RSS, checkpoint clock, segment counts, and the
validity of every recovery surface (journal manifest, recoverable listing,
meeting row). The run fails unless memory growth stays under the slope
threshold, checkpoints advance, recovery files stay valid at every sample, and
the meeting finalizes as exactly one identity.

    .venv/bin/python scripts/phase93_meeting_longrun.py                # 5-minute lane
    .venv/bin/python scripts/phase93_meeting_longrun.py --minutes 30   # owner lane
    .venv/bin/python scripts/phase93_meeting_longrun.py --minutes 120  # owner lane

The machine-readable trace lands in the HS-93-06 evidence directory by default.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

DEFAULT_OUTPUT_DIR = (
    ROOT / "pm/roadmap/holdspeak/phase-93-effortless-holdspeak/evidence/hs-93-06"
)
DEVICE_ID = "longrun-device"
DEVICE_LABEL = "Longrun"
PSK = "phase93-longrun-psk-0000000000"


class SyntheticTranscriber:
    """Deterministic, model-free transcription: the protocol measures the
    capture/checkpoint pipeline, not Whisper."""

    def __init__(self) -> None:
        self.calls = 0

    def transcribe(self, audio: "np.ndarray") -> str:
        self.calls += 1
        seconds = audio.size / 16000.0
        return f"synthetic segment {self.calls} covering {seconds:.1f} seconds"


def _rss_kib(pid: int) -> int:
    out = subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)], text=True)
    return int(out.strip() or "0")


def _slope_kib_per_min(samples: list[dict]) -> float:
    """Least-squares slope of RSS over elapsed minutes, skipping warmup."""
    if len(samples) < 4:
        return 0.0
    warmup = max(2, len(samples) // 10)
    xs = [s["elapsed_seconds"] / 60.0 for s in samples[warmup:]]
    ys = [float(s["rss_kib"]) for s in samples[warmup:]]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom <= 0:
        return 0.0
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom


def run(args: argparse.Namespace) -> int:
    scratch = Path(tempfile.mkdtemp(prefix="holdspeak-phase93-longrun-"))
    os.environ["HOME"] = str(scratch)
    os.environ.pop("HOLDSPEAK_FAULT", None)

    import holdspeak.config as config_module
    from holdspeak.config import Config

    config_module.CONFIG_FILE = scratch / "config.json"
    Config().save(config_module.CONFIG_FILE)

    from holdspeak.db import get_database, reset_database

    reset_database()
    db = get_database(scratch / "holdspeak.db")

    import holdspeak.meeting_session.session as session_module
    from holdspeak.device_audio import DEVICE_HANDSHAKE_VERSION, DeviceRegistry
    from holdspeak.meeting_recorder import AudioChunk, MeetingRecorder
    from holdspeak.meeting_session import MeetingSession
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    recorders: list["SyntheticRecorder"] = []

    class SyntheticRecorder(MeetingRecorder):
        """The real recorder minus hardware: buffers, device-stream drain,
        trim, and journal callbacks are the production implementations."""

        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)
            recorders.append(self)

        def _resolve_mic_device(self, device):
            return None

        def _resolve_system_device(self, device):
            return None

        def start(self) -> None:
            with self._lock:
                self._recording = True
                self._start_time = time.time()
                self._buffer.clear()

        def stop(self):
            with self._lock:
                self._recording = False
            return self._buffer.get_all_chunks()

        def push_mic(self, audio: "np.ndarray", timestamp: float, duration: float) -> None:
            self._buffer.add_mic_chunk(audio, timestamp, duration)
            if self.on_audio_chunk is not None:
                self.on_audio_chunk(
                    AudioChunk(audio=audio, timestamp=timestamp, source="mic", duration=duration)
                )

    session_module.MeetingRecorder = SyntheticRecorder

    registry = DeviceRegistry()
    transcriber = SyntheticTranscriber()
    session = MeetingSession(transcriber=transcriber)
    session.TRANSCRIBE_INTERVAL = float(args.transcribe_interval)

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda _label: {"timestamp": 0.0, "label": "longrun"},
            on_stop=lambda: {"status": "stopped"},
            get_state=session._get_state_dict,
            device_registry=registry,
            device_psk_provider=lambda: PSK,
        ),
        host="127.0.0.1",
    )
    url = server.start()
    time.sleep(0.8)

    from urllib.request import urlopen

    from websockets.sync.client import connect as ws_connect

    ws = ws_connect(url.replace("http://", "ws://") + "/api/devices/audio")
    ws.send(json.dumps({
        "type": "hello",
        "device_id": DEVICE_ID,
        "label": DEVICE_LABEL,
        "psk": PSK,
        "version": DEVICE_HANDSHAKE_VERSION,
    }))
    ack = json.loads(ws.recv(timeout=10))
    assert ack.get("type") == "hello-ack", f"device handshake failed: {ack}"

    state = session.start()
    meeting_id = state.id
    recorder = recorders[-1]

    descriptor = registry.get(DEVICE_ID)
    source = registry.recorder_for(DEVICE_ID)
    assert descriptor is not None and source is not None
    # The accelerated pace outruns the 2 s live-buffer default between drains;
    # size the buffer to hold several transcription intervals of pushed audio.
    source.max_buffer_seconds = max(
        4.0,
        float(args.chunk_seconds) * float(args.push_hz)
        * float(args.transcribe_interval) * 4.0,
    )
    session.attach_device(descriptor, source)

    duration_seconds = float(args.minutes) * 60.0
    deadline = time.time() + duration_seconds
    stop_event = threading.Event()
    pusher_errors: list[str] = []

    chunk_samples = int(16000 * float(args.chunk_seconds))
    ramp = (np.linspace(-0.05, 0.05, chunk_samples).astype(np.float32))
    pcm16 = (ramp * 32767.0).astype("<i2").tobytes()

    def pusher() -> None:
        synthetic_clock = 0.0
        period = 1.0 / float(args.push_hz)
        try:
            while not stop_event.is_set() and time.time() < deadline:
                ws.send(pcm16)
                recorder.push_mic(ramp, synthetic_clock, float(args.chunk_seconds))
                synthetic_clock += float(args.chunk_seconds)
                stop_event.wait(period)
        except Exception as exc:  # surfaced in the summary; fails the run
            pusher_errors.append(f"{type(exc).__name__}: {exc}")

    pusher_thread = threading.Thread(target=pusher, name="LongrunPusher", daemon=True)
    pusher_thread.start()

    from holdspeak.meeting_capture_journal import MeetingCaptureJournal

    captures_root = scratch / ".local" / "share" / "holdspeak" / "meeting-captures"
    manifest_path = captures_root / meeting_id / "capture.json"

    samples: list[dict] = []
    problems: list[str] = []
    started_wall = time.time()

    while time.time() < deadline:
        time.sleep(min(float(args.interval_seconds), max(0.0, deadline - time.time())))
        now = time.time()
        row = db.meetings.get_meeting(meeting_id)
        manifest_ok, manifest = False, {}
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_ok = manifest.get("status") == "recording" and manifest.get("error") is None
        except (OSError, ValueError):
            manifest_ok = False
        recoverable_ids = [r.get("meeting_id") for r in MeetingCaptureJournal.recoverable(captures_root)]
        try:
            with urlopen(f"{url}/api/state", timeout=5) as resp:
                live_state = json.loads(resp.read().decode("utf-8"))
            served_ok = live_state.get("id") == meeting_id
        except Exception:
            served_ok = False

        sample = {
            "at": datetime.now().isoformat(timespec="seconds"),
            "elapsed_seconds": round(now - started_wall, 1),
            "rss_kib": _rss_kib(os.getpid()),
            "capture_status": getattr(row, "capture_status", None),
            "checkpoint_seconds": float(getattr(row, "capture_checkpoint_seconds", 0.0) or 0.0),
            "segments": len(getattr(row, "segments", []) or []),
            "journal_durable_mic_bytes": int((manifest.get("durable_bytes") or {}).get("mic", 0)),
            "recovery_valid": bool(
                row is not None
                and getattr(row, "capture_status", "") == "recording"
                and manifest_ok
                and meeting_id in recoverable_ids
            ),
            "served_ok": served_ok,
        }
        samples.append(sample)
        if not sample["recovery_valid"]:
            problems.append(f"recovery surface invalid at {sample['elapsed_seconds']}s: {sample}")
        if not served_ok:
            problems.append(f"/api/state not serving the live meeting at {sample['elapsed_seconds']}s")

    stop_event.set()
    pusher_thread.join(timeout=10)
    try:
        ws.close()
    except Exception:
        pass

    final_state = session.stop()
    server.stop()

    final_row = db.meetings.get_meeting(meeting_id)
    all_meetings = [m.id for m in db.meetings.list_meetings()]
    final_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    slope = _slope_kib_per_min(samples)
    checkpoints = [s["checkpoint_seconds"] for s in samples]
    monotonic = all(b >= a for a, b in zip(checkpoints, checkpoints[1:]))
    verdicts = {
        "bounded_memory_growth": slope <= float(args.rss_slope_limit_kib_per_min),
        "checkpoints_advancing": bool(
            samples and monotonic and checkpoints[-1] > checkpoints[0] >= 0.0
        ),
        "recovery_valid_at_every_sample": all(s["recovery_valid"] for s in samples),
        "served_at_every_sample": all(s["served_ok"] for s in samples),
        "pusher_clean": not pusher_errors,
        "finalized_single_identity": (
            final_state.id == meeting_id
            and getattr(final_row, "capture_status", "") == "finalized"
            and final_manifest.get("status") == "finalized"
            and all_meetings == [meeting_id]
        ),
        "transcript_grew": len(getattr(final_row, "segments", []) or []) > 0,
    }

    trace = {
        "protocol": "phase93_meeting_longrun",
        "captured_at": datetime.now().isoformat(timespec="seconds"),
        "config": {
            "minutes": float(args.minutes),
            "interval_seconds": float(args.interval_seconds),
            "push_hz": float(args.push_hz),
            "chunk_seconds": float(args.chunk_seconds),
            "transcribe_interval": float(args.transcribe_interval),
            "rss_slope_limit_kib_per_min": float(args.rss_slope_limit_kib_per_min),
            "acceleration_factor": float(args.push_hz) * float(args.chunk_seconds),
        },
        "meeting_id": meeting_id,
        "samples": samples,
        "summary": {
            "sample_count": len(samples),
            "rss_start_kib": samples[0]["rss_kib"] if samples else None,
            "rss_end_kib": samples[-1]["rss_kib"] if samples else None,
            "rss_slope_kib_per_min": round(slope, 2),
            "checkpoint_seconds_start": checkpoints[0] if checkpoints else None,
            "checkpoint_seconds_end": checkpoints[-1] if checkpoints else None,
            "final_segments": len(getattr(final_row, "segments", []) or []),
            "journal_durable_mic_bytes": int(
                (final_manifest.get("durable_bytes") or {}).get("mic", 0)
            ),
            "pusher_errors": pusher_errors,
            "problems": problems,
            "verdicts": verdicts,
        },
    }

    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    minutes_label = (
        str(int(args.minutes)) if float(args.minutes).is_integer() else str(args.minutes)
    )
    trace_path = output_dir / f"longrun-trace-{minutes_label}min.json"
    trace_path.write_text(json.dumps(trace, indent=2), encoding="utf-8")

    print(f"trace -> {trace_path}")
    for key, value in trace["summary"].items():
        if key not in {"problems", "verdicts", "pusher_errors"}:
            print(f"  {key}: {value}")
    for name, ok in verdicts.items():
        print(f"  verdict {name}: {'PASS' if ok else 'FAIL'}")
    for problem in problems[:10]:
        print(f"  problem: {problem}")

    reset_database()
    return 0 if all(verdicts.values()) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minutes", type=float, default=5.0,
                        help="wall-clock run length (5 = CI-less local lane; 30/120 = owner lanes)")
    parser.add_argument("--interval-seconds", type=float, default=5.0,
                        help="sampling interval for RSS/checkpoint/recovery checks")
    parser.add_argument("--push-hz", type=float, default=10.0,
                        help="synthetic chunk pushes per second (per lane)")
    parser.add_argument("--chunk-seconds", type=float, default=1.0,
                        help="synthetic audio seconds per pushed chunk")
    parser.add_argument("--transcribe-interval", type=float, default=2.0,
                        help="session transcription/checkpoint cadence in seconds")
    parser.add_argument("--rss-slope-limit-kib-per-min", type=float, default=1024.0,
                        help="fail when RSS grows faster than this after warmup")
    parser.add_argument("--output", default=None,
                        help="trace output directory (default: HS-93-06 evidence)")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
