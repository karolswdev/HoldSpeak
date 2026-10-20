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
import multiprocessing as mp
from pathlib import Path
from queue import Empty, Full, Queue
from typing import Any, Callable, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .audio import AudioSource

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
from .errors import HoldSpeakError
from .logging_config import get_logger

log = get_logger("meeting")

# Native CoreAudio teardown can wait forever. Saving accepted audio must not.
_NATIVE_STOP_TIMEOUT_SECONDS = 1.0
_CAPTURE_QUEUE_MAX_CHUNKS = 64
_CAPTURE_QUEUE_POLL_SECONDS = 0.05
_CAPTURE_PROCESS_STOP_TIMEOUT_SECONDS = 1.0


class MeetingRecorderError(HoldSpeakError):
    """Raised when meeting recording fails."""

    code: str = "MEETING_RECORDER_ERROR"


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

    # MeetingSession uses this capability marker so established recorder
    # doubles keep the in-process journal callback during recovery tests.
    capture_process_supported = True

    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        mic_device: Optional[int | str] = None,
        system_device: Optional[int | str] = None,
        chunk_duration: float = 2.0,  # Process in 2-second chunks
        on_mic_level: Optional[Callable[[float], None]] = None,
        on_system_level: Optional[Callable[[float], None]] = None,
        on_audio_chunk: Optional[Callable[[AudioChunk], None]] = None,
        capture_directory: Optional[Path] = None,
        meeting_id: Optional[str] = None,
        process_factory: Optional[Callable[..., Any]] = None,
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
        self.on_audio_chunk = on_audio_chunk
        self._capture_directory = capture_directory
        self._meeting_id = meeting_id
        self._process_factory = process_factory
        self._capture_process_mode = capture_directory is not None and bool(meeting_id)

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
        self.device_cleanup_error: Optional[str] = None
        # A queue refusal is a capture failure, not an accepted chunk.  Keep
        # this separate from native device cleanup so callers can report the
        # actual audio loss without claiming that Stop saved it.
        self.capture_failure: Optional[str] = None
        self._start_time: Optional[float] = None
        self._buffer = DualStreamBuffer()
        self._capture_queue: Queue[AudioChunk] = Queue(maxsize=_CAPTURE_QUEUE_MAX_CHUNKS)
        self._writer_thread: Optional[threading.Thread] = None
        self._capture_process: Any = None
        self._capture_connection: Any = None
        self._capture_reader_thread: Optional[threading.Thread] = None
        self._capture_ready = threading.Event()
        self._capture_stopped = threading.Event()
        self._capture_process_exited = False
        # Phase 14: registered AIPI-Lite-class device streams.
        # Each maps device_id → (source, label, last_drain_monotonic).
        # The recorder doesn't capture device audio itself; the
        # WebSocket route pushes PCM into the source, and the
        # session's transcription loop polls ``get_pending_device_chunks``.
        self._device_sources: dict[str, "AudioSource"] = {}
        self._device_labels: dict[str, str] = {}
        self._device_last_drain: dict[str, float] = {}

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
            if self.device_cleanup_error and not self._capture_process_mode:
                raise MeetingRecorderError(
                    "Audio device did not close."
                )
            self._recording = True
            self._start_time = time.time()
            self._buffer.clear()
            self.capture_failure = None
            if self._capture_process_mode:
                # Each Record gets a fresh child.  A previous child timeout
                # must not turn into a desk-wide restart refusal.
                self.device_cleanup_error = None
            if not self._capture_process_mode and (
                self._writer_thread is None or not self._writer_thread.is_alive()
            ):
                self._capture_queue = Queue(maxsize=_CAPTURE_QUEUE_MAX_CHUNKS)
                self._writer_thread = threading.Thread(
                    target=self._drain_capture_queue,
                    name="meeting-audio-writer",
                    daemon=True,
                )
                self._writer_thread.start()

        log.info("Starting meeting recording")

        if self._capture_process_mode:
            try:
                self._start_capture_process()
            except Exception as exc:
                with self._lock:
                    self._recording = False
                raise MeetingRecorderError(f"Failed to start capture process: {exc}") from exc
            return

        # Start mic stream
        try:
            self._start_mic_stream()
        except Exception as e:
            with self._lock:
                self._recording = False
            self._wait_for_writer()
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

        if self._capture_process_mode:
            return self._stop_capture_process()

        # Abort streams so native teardown does not wait for queued buffers.
        self._stop_streams()
        # An admitted queue item is part of the capture contract.  Wait for
        # the writer to finish its journal callback before taking the snapshot.
        self._wait_for_writer()
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

    def trim_before(self, timestamp: float) -> None:
        """Release checkpointed audio while retaining the active overlap window.

        MeetingSession calls this only after the corresponding transcript state
        has committed to SQLite.  Recorder memory is therefore bounded by one
        transcription interval plus overlap, independent of meeting length.
        """
        self._buffer.trim_before(timestamp)

    # ------------------------------------------------------------------
    # Phase 14: device stream coordination (HS-14-06)
    # ------------------------------------------------------------------
    def register_device_stream(
        self,
        device_id: str,
        source: "AudioSource",
        *,
        label: str,
    ) -> None:
        """Register a remote audio source as an additional meeting stream.

        Audio actually arrives on this source via
        :meth:`holdspeak.device_audio.RemoteAudioRecorder.push` from
        the WebSocket dispatcher; the recorder polls it on the same
        cadence as the local mic / system buffers.
        """
        with self._lock:
            self._device_sources[device_id] = source
            self._device_labels[device_id] = label
            self._device_last_drain[device_id] = (
                self._start_time if self._start_time is not None else time.time()
            )

    def unregister_device_stream(self, device_id: str) -> None:
        with self._lock:
            self._device_sources.pop(device_id, None)
            self._device_labels.pop(device_id, None)
            self._device_last_drain.pop(device_id, None)

    def device_label(self, device_id: str) -> Optional[str]:
        with self._lock:
            return self._device_labels.get(device_id)

    def registered_device_ids(self) -> list[str]:
        with self._lock:
            return list(self._device_sources.keys())

    def get_pending_device_chunks(self) -> dict[str, list[AudioChunk]]:
        """Drain every registered device source.

        Returns ``{device_id: [AudioChunk]}``. Each device produces
        at most one chunk per call (the concatenation of everything
        that has been pushed since the last drain). The chunk's
        ``timestamp`` is the meeting-relative time at which the
        previous drain ended; ``duration`` is the audio length.
        """
        result: dict[str, list[AudioChunk]] = {}
        now = time.time()
        with self._lock:
            for device_id, source in list(self._device_sources.items()):
                drain = getattr(source, "drain", None)
                if drain is None:
                    continue
                try:
                    audio = drain()
                except Exception as exc:  # pragma: no cover - defensive
                    log.error(f"Device {device_id!r} drain failed: {exc}")
                    continue
                if audio.size == 0:
                    self._device_last_drain[device_id] = now
                    continue
                duration = audio.size / float(self.sample_rate)
                start_meeting = self._start_time if self._start_time is not None else now
                last_drain = self._device_last_drain.get(device_id, start_meeting)
                timestamp = max(0.0, last_drain - start_meeting)
                chunk = AudioChunk(
                    audio=audio,
                    timestamp=timestamp,
                    source=device_id,
                    duration=duration,
                )
                result[device_id] = [chunk]
                self._device_last_drain[device_id] = now
        return result

    @property
    def capture_process_exited(self) -> bool:
        """Whether the child owning native audio has exited after Stop."""
        return self._capture_process_exited

    @property
    def capture_process_pid(self) -> Optional[int]:
        """PID of the active native capture child, when one is running."""
        process = self._capture_process
        pid = getattr(process, "pid", None) if process is not None else None
        return int(pid) if pid is not None else None

    def _start_capture_process(self) -> None:
        from .capture_process import run_capture_process

        context = mp.get_context("spawn")
        parent_connection, child_connection = context.Pipe(duplex=True)
        config = {
            "meeting_id": self._meeting_id,
            "capture_directory": str(self._capture_directory),
            "sample_rate": self.sample_rate,
            "mic_device": self._mic_device,
            "system_device": self._system_device,
            "chunk_duration": self.chunk_duration,
        }
        factory = self._process_factory or context.Process
        process = factory(
            target=run_capture_process,
            args=(child_connection, config),
            daemon=True,
        )
        process.start()
        if self._process_factory is None:
            try:
                child_connection.close()
            except Exception:
                pass

        self._capture_connection = parent_connection
        self._capture_process = process
        self._capture_ready.clear()
        self._capture_stopped.clear()
        self._capture_process_exited = False
        self._capture_reader_thread = threading.Thread(
            target=self._read_capture_events,
            name="meeting-capture-events",
            daemon=True,
        )
        self._capture_reader_thread.start()

        if not self._capture_ready.wait(5.0):
            error = self.capture_failure or "Capture child did not become ready"
            self._terminate_capture_process()
            raise MeetingRecorderError(error)

    def _read_capture_events(self) -> None:
        connection = self._capture_connection
        if connection is None:
            return
        while True:
            try:
                event = connection.recv()
            except (EOFError, OSError):
                if not self._capture_stopped.is_set():
                    self.capture_failure = self.capture_failure or (
                        "Capture process exited before delivering its terminal status"
                    )
                return
            if not isinstance(event, dict):
                continue
            event_type = event.get("type")
            if event_type == "ready":
                self._capture_ready.set()
            elif event_type == "level":
                callback = self.on_mic_level if event.get("source") == "mic" else self.on_system_level
                if callback is not None:
                    try:
                        callback(float(event.get("level", 0.0)))
                    except Exception:
                        pass
            elif event_type == "chunk":
                try:
                    audio = np.frombuffer(event.get("audio", b""), dtype="<f4").copy()
                    chunk = AudioChunk(
                        audio=audio,
                        timestamp=float(event.get("timestamp", 0.0)),
                        source=str(event.get("source", "mic")),
                        duration=float(event.get("duration", 0.0)),
                    )
                    if chunk.source == "mic":
                        self._buffer.add_mic_chunk(chunk.audio, chunk.timestamp, chunk.duration)
                    else:
                        self._buffer.add_system_chunk(chunk.audio, chunk.timestamp, chunk.duration)
                    if self.on_audio_chunk is not None:
                        self.on_audio_chunk(chunk)
                except Exception as exc:
                    self.capture_failure = f"Capture child chunk failed: {exc}"
            elif event_type == "error":
                self.capture_failure = str(event.get("error") or "Capture child failed")
            elif event_type == "stopped":
                self._capture_stopped.set()
                capture_failure = event.get("capture_failure")
                if capture_failure:
                    self.capture_failure = str(capture_failure)
                error = event.get("error")
                if error:
                    self.capture_failure = self.capture_failure or str(error)
                cleanup_error = event.get("device_cleanup_error")
                if cleanup_error:
                    self.device_cleanup_error = str(cleanup_error)

    def _stop_capture_process(self) -> tuple[list[AudioChunk], list[AudioChunk]]:
        process = self._capture_process
        connection = self._capture_connection
        if process is None or connection is None:
            self._capture_process_exited = True
            return self._buffer.get_all_chunks()

        try:
            connection.send({"command": "stop"})
        except (BrokenPipeError, EOFError, OSError) as exc:
            self.capture_failure = self.capture_failure or (
                "Capture process exited before delivering its terminal status; "
                f"stop command failed: {exc}"
            )

        deadline = time.monotonic() + _CAPTURE_PROCESS_STOP_TIMEOUT_SECONDS
        while process.is_alive() and time.monotonic() < deadline:
            process.join(timeout=min(0.05, max(0.0, deadline - time.monotonic())))

        if process.is_alive():
            self.device_cleanup_error = (
                "Capture process did not exit within 1 second; child terminated."
            )
            self.capture_failure = self.capture_failure or (
                "Capture process ended before all accepted audio and its terminal status "
                "were delivered; recover the journal"
            )
            self._terminate_capture_process()
        else:
            process.join(timeout=0.0)

        self._capture_process_exited = not process.is_alive()
        reader = self._capture_reader_thread
        if reader is not None and reader is not threading.current_thread():
            reader.join(timeout=0.2)
        if not self._capture_stopped.is_set():
            self.capture_failure = self.capture_failure or (
                "Capture process ended before delivering its terminal status; recover the journal"
            )
        try:
            connection.close()
        except Exception:
            pass
        self._capture_process = None
        self._capture_connection = None
        mic_chunks, system_chunks = self._buffer.get_all_chunks()
        log.info(
            "Capture child exited: %s mic chunks, %s system chunks",
            len(mic_chunks),
            len(system_chunks),
        )
        return mic_chunks, system_chunks

    def _terminate_capture_process(self) -> None:
        process = self._capture_process
        if process is None:
            return
        try:
            process.terminate()
            process.join(timeout=0.2)
        except Exception:
            pass
        if process.is_alive():
            kill = getattr(process, "kill", None)
            if callable(kill):
                try:
                    kill()
                    process.join(timeout=0.2)
                except Exception:
                    pass

    def _commit_audio_chunk(self, chunk: np.ndarray, timestamp: float, source: str) -> bool:
        """Admit a copied PCM chunk without doing disk work on the callback."""
        duration = len(chunk) / self.sample_rate
        # sounddevice owns its callback buffer after return.  The callbacks
        # already copy their input; this copy also protects direct producers
        # that use this seam in tests or the ffmpeg reader.
        accepted = AudioChunk(
            np.asarray(chunk, dtype=np.float32).copy(), timestamp, source, duration
        )
        self._ensure_writer_started()
        overflow = False
        with self._lock:
            if not self._recording:
                return False
            try:
                self._capture_queue.put_nowait(accepted)
            except Full:
                self.capture_failure = (
                    "Audio capture queue overflow: chunk refused; Stop cannot claim it"
                )
                overflow = True
        if overflow:
            # Keep logging out of the callback's cutoff lock.  The refusal is
            # already recorded in capture_failure before this diagnostic runs.
            log.error(self.capture_failure)
            return False
        return True

    def _ensure_writer_started(self) -> None:
        """Start the queue writer for direct callback seam tests as well as start()."""
        with self._lock:
            if self._writer_thread is not None and self._writer_thread.is_alive():
                return
            self._writer_thread = threading.Thread(
                target=self._drain_capture_queue,
                name="meeting-audio-writer",
                daemon=True,
            )
            self._writer_thread.start()

    def _drain_capture_queue(self) -> None:
        """Move admitted chunks to memory and the journal off the audio thread."""
        while True:
            try:
                item = self._capture_queue.get(timeout=_CAPTURE_QUEUE_POLL_SECONDS)
            except Empty:
                with self._lock:
                    if not self._recording and self._capture_queue.empty():
                        return
                continue

            try:
                if item.source == "mic":
                    self._buffer.add_mic_chunk(item.audio, item.timestamp, item.duration)
                else:
                    self._buffer.add_system_chunk(item.audio, item.timestamp, item.duration)
                if self.on_audio_chunk is not None:
                    self.on_audio_chunk(item)
            except Exception as exc:
                self.capture_failure = f"Audio capture writer failed: {exc}"
                log.error(self.capture_failure)
            finally:
                self._capture_queue.task_done()

    def _wait_for_writer(self) -> None:
        writer = self._writer_thread
        if writer is not None and writer is not threading.current_thread():
            writer.join()

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

            if not self._commit_audio_chunk(chunk, timestamp, "mic"):
                return

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

            if not self._commit_audio_chunk(chunk, timestamp, "system"):
                return

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
        """Bound native cleanup without making audio saving wait for a driver."""
        with self._lock:
            streams = [(self._mic_stream, "mic"), (self._system_stream, "system")]
            self._mic_stream = None
            self._system_stream = None
        pending: list[tuple[str, threading.Event, dict[str, str]]] = []
        errors = []
        for stream, name in streams:
            if stream is None:
                continue
            done = threading.Event()
            result: dict[str, str] = {}

            def cleanup(stream=stream, name=name, done=done, result=result):
                try:
                    abort = getattr(stream, "abort", None)
                    if callable(abort):
                        try:
                            abort()
                        except Exception as exc:
                            log.debug("Error aborting %s stream: %s", name, exc)
                    else:
                        # Compatibility for old test doubles and alternate
                        # stream implementations. Real sounddevice streams
                        # take the abort branch above.
                        try:
                            stream.stop()
                        except Exception as exc:
                            log.debug("Error stopping %s stream: %s", name, exc)
                    try:
                        stream.close()
                    except Exception as exc:
                        result["error"] = f"{name} audio device did not close"
                        log.warning("Error closing %s stream: %s", name, exc)
                finally:
                    done.set()

            try:
                threading.Thread(target=cleanup, name=f"meeting-{name}-cleanup", daemon=True).start()
            except Exception as exc:
                errors.append(f"{name} audio device did not close")
                log.warning("Could not start %s audio cleanup: %s", name, exc)
                continue
            pending.append((name, done, result))

        deadline = time.monotonic() + _NATIVE_STOP_TIMEOUT_SECONDS
        for name, done, result in pending:
            if not done.wait(max(0.0, deadline - time.monotonic())):
                errors.append(f"{name} audio device did not close")
            elif result.get("error"):
                errors.append(result["error"])
        if errors:
            self.device_cleanup_error = "; ".join(errors) + "."
            log.warning(self.device_cleanup_error)
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
                    if not self._commit_audio_chunk(chunk, timestamp, "system"):
                        return

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
