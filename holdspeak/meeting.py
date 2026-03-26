"""Meeting mode recorder for HoldSpeak.

Captures audio from both microphone (you) and system audio (remote participants)
simultaneously for full meeting transcription with speaker differentiation.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

try:
    import sounddevice as sd
except Exception as exc:  # pragma: no cover
    sd = None  # type: ignore[assignment]
    _SD_IMPORT_ERROR: Optional[BaseException] = exc
else:  # pragma: no cover
    _SD_IMPORT_ERROR = None

from .audio import _linear_resample_mono
from .audio_devices import (
    find_blackhole,
    find_device_by_name,
    find_pulse_monitor_source,
    get_default_input_device,
)
from .logging_config import get_logger

log = get_logger("meeting")


class MeetingRecorderError(RuntimeError):
    """Raised when meeting recording fails."""


def _require_sounddevice():
    if sd is None:
        raise MeetingRecorderError(
            "sounddevice/PortAudio is not available. "
            "Install system PortAudio and reinstall sounddevice."
        ) from _SD_IMPORT_ERROR
    return sd


@dataclass
class AudioChunk:
    """A timestamped chunk of audio from one source."""

    audio: np.ndarray  # float32 mono at target sample rate
    timestamp: float  # Seconds since recording start
    source: str  # "mic" or "system"
    duration: float  # Duration in seconds

    @property
    def end_time(self) -> float:
        return self.timestamp + self.duration


@dataclass
class TranscriptSegment:
    """A transcribed segment with speaker label."""

    text: str
    speaker: str  # "Me" or "Remote" or custom label
    timestamp: float
    duration: float

    def __str__(self) -> str:
        ts = time.strftime("%H:%M:%S", time.gmtime(self.timestamp))
        return f"[{ts}] {self.speaker}: {self.text}"


@dataclass
class DualStreamBuffer:
    """Synchronized buffers for two audio streams."""

    mic_chunks: list[AudioChunk] = field(default_factory=list)
    system_chunks: list[AudioChunk] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def add_mic_chunk(self, audio: np.ndarray, timestamp: float, duration: float) -> None:
        with self.lock:
            self.mic_chunks.append(AudioChunk(audio, timestamp, "mic", duration))

    def add_system_chunk(self, audio: np.ndarray, timestamp: float, duration: float) -> None:
        with self.lock:
            self.system_chunks.append(AudioChunk(audio, timestamp, "system", duration))

    def get_chunks_since(self, timestamp: float) -> tuple[list[AudioChunk], list[AudioChunk]]:
        """Get all chunks with timestamp >= given time."""
        with self.lock:
            mic = [c for c in self.mic_chunks if c.timestamp >= timestamp]
            system = [c for c in self.system_chunks if c.timestamp >= timestamp]
            return mic, system

    def get_all_chunks(self) -> tuple[list[AudioChunk], list[AudioChunk]]:
        """Get all buffered chunks."""
        with self.lock:
            return list(self.mic_chunks), list(self.system_chunks)

    def clear(self) -> None:
        """Clear all buffered chunks."""
        with self.lock:
            self.mic_chunks.clear()
            self.system_chunks.clear()

    def trim_before(self, timestamp: float) -> None:
        """Remove chunks that end before the given timestamp."""
        with self.lock:
            self.mic_chunks = [c for c in self.mic_chunks if c.end_time > timestamp]
            self.system_chunks = [c for c in self.system_chunks if c.end_time > timestamp]


class MeetingRecorder:
    """Dual-stream audio recorder for meeting transcription.

    Captures audio from both:
    - Microphone (your voice)
    - System audio via BlackHole (remote participants)

    Audio is captured at 16kHz mono (Whisper-compatible) and buffered
    with timestamps for synchronized processing.
    """

    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        mic_device: Optional[int | str] = None,
        system_device: Optional[int | str] = None,
        chunk_duration: float = 2.0,  # Process in 2-second chunks
        on_mic_level: Optional[Callable[[float], None]] = None,
        on_system_level: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Initialize the meeting recorder.

        Args:
            sample_rate: Target sample rate (default 16kHz for Whisper).
            mic_device: Microphone device index or name (None for default).
            system_device: System audio device index or name (None to auto-detect BlackHole).
            chunk_duration: Duration of audio chunks for processing.
            on_mic_level: Callback for mic audio level updates (0.0-1.0).
            on_system_level: Callback for system audio level updates (0.0-1.0).
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.on_mic_level = on_mic_level
        self.on_system_level = on_system_level

        # Resolve devices
        self._mic_device = self._resolve_mic_device(mic_device)
        self._system_device = self._resolve_system_device(system_device)
        self._system_pulse_source: Optional[str] = None
        if sys.platform.startswith("linux") and (
            system_device is None
            or (isinstance(system_device, str) and "monitor" in system_device.lower())
        ):
            self._system_pulse_source = find_pulse_monitor_source(
                system_device if isinstance(system_device, str) else None
            )

        # State
        self._lock = threading.Lock()
        self._recording = False
        self._start_time: Optional[float] = None
        self._buffer = DualStreamBuffer()

        # Streams
        self._mic_stream: Optional[sd.InputStream] = None
        self._system_stream: Optional[sd.InputStream] = None
        self._system_ffmpeg_proc: Optional[subprocess.Popen[bytes]] = None
        self._system_ffmpeg_thread: Optional[threading.Thread] = None
        self._mic_capture_rate: int = sample_rate
        self._system_capture_rate: int = sample_rate
        # Smoothed levels (so UI bars actually move and don't jitter wildly)
        self._mic_level_smooth: float = 0.0
        self._system_level_smooth: float = 0.0

        log.info(
            f"MeetingRecorder initialized: mic={self._mic_device}, "
            f"system={self._system_device}, rate={sample_rate}"
        )

    @staticmethod
    def _level_from_audio(chunk: np.ndarray) -> float:
        """Map audio chunk to a stable 0..1 level suitable for UI meters."""
        if chunk.size == 0:
            return 0.0

        # Use RMS -> dBFS, then map a useful range to 0..1.
        rms = float(np.sqrt(np.mean(chunk * chunk)))
        db = 20.0 * float(np.log10(rms + 1e-12))  # ~[-inf..0]

        # Map [-60dB..-10dB] to [0..1] (tuned for human voice and typical system audio).
        db_min, db_max = -60.0, -10.0
        level = (db - db_min) / (db_max - db_min)
        if level < 0.0:
            return 0.0
        if level > 1.0:
            return 1.0
        return level

    def _resolve_mic_device(self, device: Optional[int | str]) -> Optional[int]:
        """Resolve mic device to an index."""
        if device is None:
            default = get_default_input_device()
            if default:
                log.info(f"Using default mic: {default.name}")
                return default.index
            return None
        if isinstance(device, int):
            return device
        found = find_device_by_name(device)
        if found:
            return found.index
        log.warning(f"Mic device '{device}' not found, using default")
        return None

    def _resolve_system_device(self, device: Optional[int | str]) -> Optional[int]:
        """Resolve system audio device to an index."""
        if sys.platform.startswith("linux"):
            if device is None:
                monitor = find_device_by_name("monitor")
                if monitor and monitor.is_input:
                    log.info(f"Using monitor input device for system audio: {monitor.name}")
                    return monitor.index
                # No PortAudio-visible monitor; we'll fall back to Pulse monitor via ffmpeg if available.
                log.info("No PortAudio monitor source found; will try ffmpeg PulseAudio fallback")
                return None

            if isinstance(device, int):
                return device

            # If the user provided a pulse monitor source name, prefer ffmpeg fallback.
            if "monitor" in device.lower() and find_pulse_monitor_source(device):
                return None

            found = find_device_by_name(device)
            if found:
                return found.index
            log.warning(f"System device '{device}' not found")
            return None

        if device is None:
            blackhole = find_blackhole()
            if blackhole:
                log.info(f"Using BlackHole for system audio: {blackhole.name}")
                return blackhole.index
            log.warning("BlackHole not found - system audio capture unavailable")
            return None
        if isinstance(device, int):
            return device
        found = find_device_by_name(device)
        if found:
            return found.index
        log.warning(f"System device '{device}' not found")
        return None

    @property
    def has_system_audio(self) -> bool:
        """Check if system audio capture is available."""
        return self._system_device is not None or self._system_pulse_source is not None

    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        with self._lock:
            return self._recording

    @property
    def recording_duration(self) -> float:
        """Get current recording duration in seconds."""
        with self._lock:
            if not self._recording or self._start_time is None:
                return 0.0
            return time.time() - self._start_time

    def start(self) -> None:
        """Start recording from both audio streams.

        Raises:
            MeetingRecorderError: If already recording or devices unavailable.
        """
        with self._lock:
            if self._recording:
                raise MeetingRecorderError("Already recording")
            self._recording = True
            self._start_time = time.time()
            self._buffer.clear()

        log.info("Starting meeting recording")

        # Start mic stream
        try:
            self._start_mic_stream()
        except Exception as e:
            with self._lock:
                self._recording = False
            raise MeetingRecorderError(f"Failed to start mic recording: {e}") from e

        # Start system capture (if available). Prefer PortAudio, fall back to ffmpeg PulseAudio monitor.
        if self._system_device is not None or self._system_pulse_source is not None:
            started_system = False

            if self._system_device is not None:
                try:
                    self._start_system_stream()
                    started_system = True
                except Exception as e:
                    log.warning(f"PortAudio system capture failed: {e}")

            if not started_system and self._system_pulse_source is not None:
                try:
                    self._start_system_ffmpeg()
                    started_system = True
                    with self._lock:
                        self._system_device = None
                    self._system_stream = None
                except Exception as e:
                    log.error(f"ffmpeg PulseAudio system capture failed: {e}")

            if not started_system:
                # Continue with mic-only recording (and mark system audio unavailable
                # so UI doesn't show a "stuck" system meter).
                with self._lock:
                    self._system_device = None
                    self._system_pulse_source = None
                self._system_stream = None
                if self.on_system_level is not None:
                    try:
                        self.on_system_level(0.0)
                    except Exception:
                        pass

        log.info("Meeting recording started")

    def stop(self) -> tuple[list[AudioChunk], list[AudioChunk]]:
        """Stop recording and return all captured chunks.

        Returns:
            Tuple of (mic_chunks, system_chunks).

        Raises:
            MeetingRecorderError: If not recording.
        """
        with self._lock:
            if not self._recording:
                raise MeetingRecorderError("Not recording")
            self._recording = False

        log.info("Stopping meeting recording")

        # Stop streams
        self._stop_streams()

        # Get all chunks
        mic_chunks, system_chunks = self._buffer.get_all_chunks()
        log.info(f"Recording stopped: {len(mic_chunks)} mic chunks, {len(system_chunks)} system chunks")

        return mic_chunks, system_chunks

    def get_pending_chunks(self, since: float = 0.0) -> tuple[list[AudioChunk], list[AudioChunk]]:
        """Get chunks since a given timestamp without stopping.

        Args:
            since: Get chunks with timestamp >= this value.

        Returns:
            Tuple of (mic_chunks, system_chunks).
        """
        return self._buffer.get_chunks_since(since)

    def _start_mic_stream(self) -> None:
        """Start the microphone input stream."""

        def callback(indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags):
            if status:
                log.debug(f"Mic stream status: {status}")

            with self._lock:
                if not self._recording or self._start_time is None:
                    return
                start_time = self._start_time
                capture_rate = self._mic_capture_rate

            # Calculate timestamp
            timestamp = time.time() - start_time

            # Extract mono audio
            chunk = np.asarray(indata[:, 0], dtype=np.float32).copy()

            # Resample if needed
            if capture_rate != self.sample_rate:
                chunk = _linear_resample_mono(chunk, capture_rate, self.sample_rate)

            duration = len(chunk) / self.sample_rate
            self._buffer.add_mic_chunk(chunk, timestamp, duration)

            # Level callback
            if self.on_mic_level is not None:
                level = self._level_from_audio(chunk)
                # Exponential smoothing for nicer UI behavior
                self._mic_level_smooth = (0.25 * level) + (0.75 * self._mic_level_smooth)
                try:
                    self.on_mic_level(self._mic_level_smooth)
                except Exception:
                    pass

        stream, capture_rate = self._open_stream(self._mic_device, callback)
        self._mic_stream = stream
        self._mic_capture_rate = capture_rate
        self._mic_stream.start()
        log.info(f"Mic stream started at {capture_rate}Hz")

    def _start_system_stream(self) -> None:
        """Start the system audio input stream."""

        def callback(indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags):
            if status:
                log.debug(f"System stream status: {status}")

            with self._lock:
                if not self._recording or self._start_time is None:
                    return
                start_time = self._start_time
                capture_rate = self._system_capture_rate

            # Calculate timestamp
            timestamp = time.time() - start_time

            # Extract mono audio
            chunk = np.asarray(indata[:, 0], dtype=np.float32).copy()

            # Resample if needed
            if capture_rate != self.sample_rate:
                chunk = _linear_resample_mono(chunk, capture_rate, self.sample_rate)

            duration = len(chunk) / self.sample_rate
            self._buffer.add_system_chunk(chunk, timestamp, duration)

            # Level callback
            if self.on_system_level is not None:
                level = self._level_from_audio(chunk)
                self._system_level_smooth = (0.25 * level) + (0.75 * self._system_level_smooth)
                try:
                    self.on_system_level(self._system_level_smooth)
                except Exception:
                    pass

        stream, capture_rate = self._open_stream(self._system_device, callback)
        self._system_stream = stream
        self._system_capture_rate = capture_rate
        self._system_stream.start()
        log.info(f"System stream started at {capture_rate}Hz")

    def _open_stream(self, device: Optional[int], callback) -> tuple[sd.InputStream, int]:
        """Open an input stream, preferring target sample rate."""
        sd_mod = _require_sounddevice()
        try:
            stream = sd_mod.InputStream(
                device=device,
                channels=1,
                samplerate=self.sample_rate,
                dtype="float32",
                callback=callback,
            )
            return stream, self.sample_rate
        except sd_mod.PortAudioError:
            # Fall back to device default rate
            device_info = sd_mod.query_devices(device, kind="input")
            fallback_rate = int(round(float(device_info["default_samplerate"])))
            stream = sd_mod.InputStream(
                device=device,
                channels=1,
                samplerate=fallback_rate,
                dtype="float32",
                callback=callback,
            )
            return stream, fallback_rate

    def _stop_streams(self) -> None:
        """Stop and close all audio streams."""
        for stream, name in [(self._mic_stream, "mic"), (self._system_stream, "system")]:
            if stream is None:
                continue
            try:
                stream.stop()
            except Exception as e:
                log.debug(f"Error stopping {name} stream: {e}")
            try:
                stream.close()
            except Exception as e:
                log.debug(f"Error closing {name} stream: {e}")

        self._mic_stream = None
        self._system_stream = None
        self._stop_system_ffmpeg()

    def _stop_system_ffmpeg(self) -> None:
        proc = self._system_ffmpeg_proc
        if proc is None:
            return

        try:
            proc.terminate()
            proc.wait(timeout=2.0)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        finally:
            self._system_ffmpeg_proc = None
            self._system_ffmpeg_thread = None

    def _start_system_ffmpeg(self) -> None:
        source = self._system_pulse_source
        if not source:
            raise MeetingRecorderError("No PulseAudio monitor source available for ffmpeg fallback")

        if not source.endswith(".monitor") and find_pulse_monitor_source(source):
            source = f"{source}.monitor"

        cmd = [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "pulse",
            "-i",
            source,
            "-ac",
            "1",
            "-ar",
            str(self.sample_rate),
            "-f",
            "f32le",
            "pipe:1",
        ]

        try:
            proc: subprocess.Popen[bytes] = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise MeetingRecorderError("ffmpeg not found. Install ffmpeg to capture system audio.") from exc

        if proc.stdout is None:
            proc.kill()
            raise MeetingRecorderError("Failed to start ffmpeg (no stdout)")

        self._system_ffmpeg_proc = proc

        def reader() -> None:
            bytes_per_sample = 4  # f32le
            target_samples = int(round(self.chunk_duration * self.sample_rate))
            target_bytes = target_samples * bytes_per_sample
            buf = bytearray()

            while True:
                with self._lock:
                    if not self._recording or self._start_time is None:
                        break
                    start_time = self._start_time

                data = proc.stdout.read(4096)
                if not data:
                    break
                buf.extend(data)

                while len(buf) >= target_bytes:
                    chunk_bytes = bytes(buf[:target_bytes])
                    del buf[:target_bytes]
                    chunk = np.frombuffer(chunk_bytes, dtype=np.float32).copy()
                    duration = len(chunk) / self.sample_rate
                    timestamp = max(0.0, (time.time() - start_time) - duration)
                    self._buffer.add_system_chunk(chunk, timestamp, duration)

                    if self.on_system_level is not None:
                        level = self._level_from_audio(chunk)
                        self._system_level_smooth = (0.25 * level) + (0.75 * self._system_level_smooth)
                        try:
                            self.on_system_level(self._system_level_smooth)
                        except Exception:
                            pass

        self._system_ffmpeg_thread = threading.Thread(target=reader, daemon=True)
        self._system_ffmpeg_thread.start()
        log.info(f"System audio capture started via ffmpeg PulseAudio source: {source}")


def concatenate_chunks(chunks: list[AudioChunk]) -> np.ndarray:
    """Concatenate a list of audio chunks into a single array.

    Args:
        chunks: List of AudioChunk objects.

    Returns:
        Concatenated float32 audio array, or empty array if no chunks.
    """
    if not chunks:
        return np.empty((0,), dtype=np.float32)

    # Sort by timestamp
    sorted_chunks = sorted(chunks, key=lambda c: c.timestamp)
    return np.concatenate([c.audio for c in sorted_chunks]).astype(np.float32)
