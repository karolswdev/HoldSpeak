#!/usr/bin/env python3
"""Measure the post-release hold-key path on a fixed 16 kHz utterance."""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import time
import wave
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from holdspeak.config import Config
from holdspeak.desktop_typing import type_text_from_owner_gesture
from holdspeak.dictation_runner import run_dictation_pipeline
from holdspeak.intel.providers import effective_dictation_llm
from holdspeak.text_processor import TextProcessor
from holdspeak.transcribe import Transcriber
from holdspeak.typer import TextTyper
from holdspeak.voice_typing import VoiceTypingSession

_REPO = Path(__file__).resolve().parents[1]
_DEFAULT_AUDIO = _REPO / "tests" / "fixtures" / "core_path_smoke_16k.wav"


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000.0, 3)


def _load_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as source:
        if (
            source.getframerate() != 16000
            or source.getnchannels() != 1
            or source.getsampwidth() != 2
        ):
            raise ValueError("audio must be mono 16-bit PCM at 16 kHz")
        raw = source.readframes(source.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


class _FixtureSource:
    def __init__(self, audio: np.ndarray) -> None:
        self.audio = audio

    def start_recording(self) -> None:
        return None

    def stop_recording(self) -> np.ndarray:
        return self.audio.copy()


class _SeamSink:
    name = "captured_injection_seam"

    def type(self, text: str) -> None:
        if not text.strip():
            raise ValueError("refusing to benchmark an empty effect")

    def verify(self, text: str) -> None:
        return None

    def close(self) -> None:
        return None


class _DriverSink:
    name = "desktop_type_text_kernel_to_texttyper_driver"

    class _Keyboard:
        def __init__(self) -> None:
            self.events: list[tuple[str, str]] = []

        def press(self, key: Any) -> None:
            self.events.append(("press", str(key)))

        def release(self, key: Any) -> None:
            self.events.append(("release", str(key)))

    class _LandingTyper:
        def __init__(self, sink: Any) -> None:
            self.sink = sink

        def type_text(self, text: str, **kwargs: Any) -> None:
            self.sink.driver.type_text(text, **kwargs)
            self.sink.landed_at = time.perf_counter()

    def __init__(self) -> None:
        self.driver = TextTyper()
        self.keyboard = self._Keyboard()
        self.driver._keyboard = self.keyboard
        self.typer = self._LandingTyper(self)
        self.landed_at: float | None = None

    def type(self, text: str) -> None:
        self.keyboard.events.clear()
        self.landed_at = None
        type_text_from_owner_gesture(
            text,
            typer=self.typer,
            gesture="hold_release",
            submit=False,
            requested_target="focused",
            delivery_method="latency_probe",
        )

    def verify(self, text: str) -> None:
        if not text.strip() or len(self.keyboard.events) != 4:
            raise RuntimeError("TextTyper did not execute one paste chord")

    def close(self) -> None:
        return None


class _TextEditSink:
    name = "macos_textedit_real_typing"

    def __init__(self) -> None:
        if platform.system() != "Darwin":
            raise RuntimeError("the TextEdit typing sink requires macOS")
        self.typer = TextTyper()
        self._script(
            'tell application "TextEdit"\n'
            "activate\n"
            "make new document\n"
            "end tell\n"
            "delay 0.4"
        )

    @staticmethod
    def _script(source: str) -> str:
        completed = subprocess.run(
            ["osascript", "-e", source],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout

    def prepare(self) -> None:
        self._script(
            'tell application "TextEdit"\n'
            'set text of front document to ""\n'
            "activate\n"
            "end tell\n"
            "delay 0.15"
        )

    def type(self, text: str) -> None:
        self.typer.type_text(text, submit=False)

    def verify(self, text: str) -> None:
        landed = self._script('tell application "TextEdit" to get text of front document')
        if text.strip() not in landed:
            raise RuntimeError(f"TextEdit did not receive the typed text; got {landed!r}")

    def close(self) -> None:
        try:
            self._script('tell application "TextEdit" to close front document saving no')
        except Exception:
            pass


def _capture(audio: np.ndarray) -> tuple[np.ndarray, float]:
    session = VoiceTypingSession()
    source = _FixtureSource(audio)
    if not session.begin(source, owner="hotkey"):
        raise RuntimeError("fixture could not acquire the voice session")
    started = time.perf_counter()
    captured = session.end(owner="hotkey")
    elapsed = _ms(started)
    if captured is None:
        raise RuntimeError("fixture capture returned no audio")
    return captured, elapsed


def _percentiles(rows: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for key in rows[0]:
        values = sorted(row[key] for row in rows)
        result[key] = {
            "min": round(values[0], 3),
            "median": round(statistics.median(values), 3),
            "max": round(values[-1], 3),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", type=Path, default=_DEFAULT_AUDIO)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--backend", choices=("auto", "mlx", "faster-whisper"), default=None
    )
    parser.add_argument(
        "--typing-mode", choices=("textedit", "driver", "seam"), default="driver"
    )
    parser.add_argument(
        "--pipeline", choices=("active", "off"), default="active"
    )
    args = parser.parse_args()
    if args.runs < 1 or args.warmups < 0:
        parser.error("--runs must be positive and --warmups cannot be negative")

    config = Config.load()
    audio = _load_wav(args.audio)
    audio_duration_ms = round(len(audio) / 16.0, 3)
    effective = effective_dictation_llm(config.dictation.runtime)
    endpoint = str(effective.base_url or "local")

    selected_model = args.model or config.model.name
    selected_backend = args.backend or config.model.backend
    load_started = time.perf_counter()
    transcriber = Transcriber(
        model_name=selected_model,
        backend=selected_backend,
        language=config.model.language,
        timeout_seconds=config.model.transcribe_timeout_seconds,
    )
    model_load_ms = _ms(load_started)
    processor = TextProcessor(spoken_symbols=config.dictation.spoken_symbols)
    sink: Any
    if args.typing_mode == "textedit":
        sink = _TextEditSink()
    elif args.typing_mode == "driver":
        sink = _DriverSink()
    else:
        sink = _SeamSink()

    pipeline_was_enabled = config.dictation.pipeline.enabled
    if args.pipeline == "off":
        config.dictation.pipeline.enabled = False

    rows: list[dict[str, float]] = []
    transcripts: list[str] = []
    total_iterations = args.warmups + args.runs
    try:
        for index in range(total_iterations):
            if hasattr(sink, "prepare"):
                sink.prepare()
            release_started = time.perf_counter()
            captured, capture_stop_ms = _capture(audio)

            started = time.perf_counter()
            transcript = transcriber.transcribe(captured)
            transcribe_ms = _ms(started)

            started = time.perf_counter()
            processed = processor.process(transcript)
            punctuation_ms = _ms(started)

            started = time.perf_counter()
            final_text = run_dictation_pipeline(
                processed,
                config=config,
                server=None,
                audio_duration_s=len(captured) / 16000.0,
                transcribed_at=datetime.now(),
            )
            pipeline_ms = _ms(started)

            started = time.perf_counter()
            sink.type(final_text)
            landed_at = getattr(sink, "landed_at", None)
            if landed_at is None:
                type_ms = _ms(started)
                release_to_landed_ms = _ms(release_started)
            else:
                type_ms = round((landed_at - started) * 1000.0, 3)
                release_to_landed_ms = round((landed_at - release_started) * 1000.0, 3)
            sink.verify(final_text)

            row = {
                "capture_stop_ms": capture_stop_ms,
                "transcribe_ms": transcribe_ms,
                "punctuation_ms": punctuation_ms,
                "pipeline_ms": pipeline_ms,
                "type_ms": type_ms,
                "release_to_landed_ms": release_to_landed_ms,
            }
            if index >= args.warmups:
                rows.append(row)
                transcripts.append(final_text)
            print(
                f"run={index + 1} warmup={str(index < args.warmups).lower()} "
                + " ".join(f"{key}={value:.3f}" for key, value in row.items())
            )
    finally:
        config.dictation.pipeline.enabled = pipeline_was_enabled
        sink.close()

    result = {
        "schema": "holdspeak.dictation-latency/v1",
        "audio": str(args.audio.resolve().relative_to(_REPO)),
        "audio_duration_ms": audio_duration_ms,
        "machine": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "model": {
            "name": selected_model,
            "backend": transcriber.backend,
            "configured_backend": config.model.backend,
            "load_ms": model_load_ms,
        },
        "pipeline": {
            "mode": args.pipeline,
            "configured_enabled": pipeline_was_enabled,
            "endpoint": endpoint,
        },
        "typing_sink": sink.name,
        "warmups": args.warmups,
        "runs": args.runs,
        "samples_ms": rows,
        "summary_ms": _percentiles(rows),
        "transcript_sha256": [
            "sha256:" + __import__("hashlib").sha256(text.encode()).hexdigest()
            for text in transcripts
        ],
        "live_owner_segment_not_measured": (
            "physical key hold plus microphone acquisition; when typing_sink is the "
            "driver probe, focused-app landing is also unmeasured. The fixed WAV enters "
            "the same VoiceTypingSession end -> transcribe -> process -> pipeline -> "
            "desktop.type_text -> TextTyper driver path"
        ),
    }
    print("HS107_BASELINE " + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
