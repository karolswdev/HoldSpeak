"""Audio capture for HoldSpeak.

This module provides a small, hold-to-record friendly microphone recorder.
`AudioRecorder.start_recording()` returns immediately and captures audio in a
background PortAudio callback until `stop_recording()` is called.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

import numpy as np

try:
    import sounddevice as sd
except Exception as exc:  # pragma: no cover
    sd = None  # type: ignore[assignment]
    _SD_IMPORT_ERROR: Optional[BaseException] = exc
else:  # pragma: no cover
    _SD_IMPORT_ERROR = None


class AudioRecorderError(RuntimeError):
    """Raised when audio recording fails or is used incorrectly."""


def _require_sounddevice():
    if sd is None:
        raise AudioRecorderError(
            "sounddevice/PortAudio is not available. "
            "Install system PortAudio and reinstall sounddevice."
        ) from _SD_IMPORT_ERROR
    return sd


def _linear_resample_mono(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Resample a mono signal using linear interpolation.

    Args:
        audio: 1D numpy array of audio samples.
        src_rate: Source sample rate (Hz).
        dst_rate: Destination sample rate (Hz).

    Returns:
        Resampled mono audio as float32.
    """

    audio = np.asarray(audio)
    if audio.ndim != 1:
        raise ValueError("audio must be a 1D mono array")
    if src_rate <= 0 or dst_rate <= 0:
        raise ValueError("sample rates must be positive")
    if audio.size == 0 or src_rate == dst_rate:
        return audio.astype(np.float32, copy=False)

    duration_s = audio.size / float(src_rate)
    dst_len = int(round(duration_s * float(dst_rate)))
    if dst_len <= 0:
        return np.empty((0,), dtype=np.float32)

    # Interpolate onto the destination grid.
    src_x = np.arange(audio.size, dtype=np.float64)
    dst_x = np.linspace(0.0, float(audio.size - 1), num=dst_len, dtype=np.float64)
    resampled = np.interp(dst_x, src_x, audio.astype(np.float64, copy=False))
    return resampled.astype(np.float32, copy=False)


class AudioRecorder:
    """Capture microphone audio for a hold-to-record interaction.

    The recorder aims to return audio compatible with Whisper: mono, float32,
    16 kHz. If the input device can't be opened at 16 kHz, the recorder falls
    back to the device default sample rate and resamples on `stop_recording()`.
    """

    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        device: Optional[int | str] = None,
        blocksize: int = 0,
        on_level: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.sample_rate = int(sample_rate)
        self.device = device
        self.blocksize = int(blocksize)
        self.on_level = on_level

        self._lock = threading.Lock()
        self._frames: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._recording = False
        self._capture_sample_rate = self.sample_rate
        self._last_status: Optional[sd.CallbackFlags] = None

    def start_recording(self) -> None:
        """Start capturing audio from the default microphone.

        Raises:
            AudioRecorderError: If recording is already active or the audio
                device/stream cannot be opened.
        """

        with self._lock:
            if self._recording:
                raise AudioRecorderError("Recording already started")
            self._recording = True
            self._frames = []
            self._last_status = None

        sd_mod = _require_sounddevice()

        def callback(
            indata: np.ndarray,
            _frames_count: int,
            _time_info: object,
            status: sd.CallbackFlags,
        ) -> None:
            if status:
                self._last_status = status
            # `indata` is (frames, channels) float32.
            chunk = np.asarray(indata[:, 0], dtype=np.float32).copy()
            with self._lock:
                if self._recording:
                    self._frames.append(chunk)
            # Calculate RMS level and notify callback
            if self.on_level is not None:
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                # Scale to 0-1 range (assuming max RMS ~0.5 for loud speech)
                level = min(1.0, rms * 3.0)
                try:
                    self.on_level(level)
                except Exception:
                    pass

        try:
            stream, capture_rate = self._open_stream(sd_mod, callback)
            self._stream = stream
            self._capture_sample_rate = capture_rate
            self._stream.start()
        except Exception as exc:  # sounddevice raises various PortAudio errors
            with self._lock:
                self._recording = False
                self._frames = []
            self._close_stream()
            raise AudioRecorderError(f"Failed to start recording: {exc}") from exc

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the captured audio.

        Returns:
            Mono float32 numpy array at 16 kHz.

        Raises:
            AudioRecorderError: If recording was not started.
        """

        with self._lock:
            if not self._recording:
                raise AudioRecorderError("Recording not started")
            self._recording = False
            frames = self._frames
            self._frames = []
            capture_rate = self._capture_sample_rate

        self._close_stream()

        if not frames:
            return np.empty((0,), dtype=np.float32)

        audio = np.concatenate(frames).astype(np.float32, copy=False)
        if capture_rate != self.sample_rate:
            audio = _linear_resample_mono(audio, capture_rate, self.sample_rate)
        return audio

    def _open_stream(self, sd_mod, callback) -> tuple[sd.InputStream, int]:
        """Open an input stream, preferring `self.sample_rate` when possible."""

        try:
            stream = sd_mod.InputStream(
                device=self.device,
                channels=1,
                samplerate=self.sample_rate,
                dtype="float32",
                blocksize=self.blocksize,
                callback=callback,
            )
            return stream, self.sample_rate
        except sd_mod.PortAudioError:
            device_info = sd_mod.query_devices(self.device, kind="input")
            fallback_rate = int(round(float(device_info["default_samplerate"])))
            stream = sd_mod.InputStream(
                device=self.device,
                channels=1,
                samplerate=fallback_rate,
                dtype="float32",
                blocksize=self.blocksize,
                callback=callback,
            )
            return stream, fallback_rate

    def _close_stream(self) -> None:
        stream = self._stream
        self._stream = None
        if stream is None:
            return
        try:
            stream.stop()
        except Exception:
            pass
        try:
            stream.close()
        except Exception:
            pass
