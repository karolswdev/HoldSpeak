"""Audio wire-format constants + WAV/sine helpers.

Single source of truth for the 16 kHz mono int16-LE format HoldSpeak's
RemoteAudioRecorder expects (see DEVICE_PROTOCOL.md §4). Both the WAV
reader and the test-audio sine synth derive their parameters from
`SAMPLE_RATE_HZ` and `BYTES_PER_SAMPLE` so a future format change
moves in lockstep.
"""

from __future__ import annotations

import array
import math
import wave

# Audio wire format (DEVICE_PROTOCOL.md §4) — HoldSpeak's
# RemoteAudioRecorder accepts 16 kHz mono int16-LE PCM.
SAMPLE_RATE_HZ = 16_000
BYTES_PER_SAMPLE = 2  # int16 LE → 2 bytes/sample
BYTES_PER_SECOND = SAMPLE_RATE_HZ * BYTES_PER_SAMPLE  # 32_000
# 100 ms-per-chunk pace for `--send-test-audio`. Matches typical
# voice_assistant datagram cadence and stays well under HoldSpeak's
# 2 s server-side buffer cap so longer test files don't drop earlier
# audio.
TEST_AUDIO_CHUNK_MS = 100
TEST_AUDIO_CHUNK_BYTES = (BYTES_PER_SECOND * TEST_AUDIO_CHUNK_MS) // 1000  # 3200

# Bounded audio buffer between DeviceLeg (producer) and HoldSpeakLeg (consumer).
# 500 chunks is comfortably more than the 2 s buffer HoldSpeak's
# RemoteAudioRecorder enforces server-side; if HoldSpeak is down the bridge
# will overflow this and structured-warn before HoldSpeak's overflow trips.
AUDIO_QUEUE_MAXSIZE = 500

# Bounded queue of outbound control frames (start/stop/etc.) ready to be
# JSON-serialised and sent on the WS by HoldSpeakLeg's _control_sender.
# 100 is plenty — control frames are user-event-driven, not streamed.
CONTROL_QUEUE_MAXSIZE = 100


def synth_sine_pcm(
    freq_hz: float = 440.0,
    duration_s: float = 1.0,
    sample_rate: int = SAMPLE_RATE_HZ,
    amplitude: float = 0.3,
) -> bytes:
    """Return `duration_s` seconds of a sine wave as 16 kHz mono int16-LE PCM.

    Used by `--audio-loopback` to verify the WS audio path without a real
    device. `amplitude` is in [0, 1] relative to int16 max.
    """
    if not 0.0 <= amplitude <= 1.0:
        raise ValueError("amplitude must be in [0, 1]")
    if sample_rate <= 0:
        raise ValueError("sample_rate must be positive")
    n_samples = int(round(sample_rate * duration_s))
    peak = int(amplitude * 32767)
    samples = array.array(
        "h",
        (
            int(peak * math.sin(2.0 * math.pi * freq_hz * i / sample_rate))
            for i in range(n_samples)
        ),
    )
    return samples.tobytes()


def read_wav_pcm(path: str) -> bytes:
    """Read a 16 kHz mono int16 WAV file and return raw PCM bytes.

    Validates format strictly — HoldSpeak's `RemoteAudioRecorder` expects
    16 kHz mono int16 LE on the wire (DEVICE_PROTOCOL.md §4); resampling
    on the bridge side is out of phase 2 scope.
    """
    with wave.open(path, "rb") as wav:
        if wav.getnchannels() != 1:
            raise ValueError(
                f"{path}: expected mono WAV, got {wav.getnchannels()} channels"
            )
        if wav.getsampwidth() != BYTES_PER_SAMPLE:
            raise ValueError(
                f"{path}: expected 16-bit samples, got {wav.getsampwidth() * 8}-bit"
            )
        if wav.getframerate() != SAMPLE_RATE_HZ:
            raise ValueError(
                f"{path}: expected 16 kHz sample rate, got {wav.getframerate()} Hz"
            )
        return wav.readframes(wav.getnframes())
