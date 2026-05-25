"""Unit tests for bridge audio helpers (synth + WAV reader)."""

from __future__ import annotations

import struct
import wave

import pytest

from bridge import read_wav_pcm, synth_sine_pcm


def test_synth_sine_returns_correct_byte_length():
    """1 s of 16 kHz mono int16 = 16 000 samples × 2 bytes = 32 000 bytes."""
    pcm = synth_sine_pcm(freq_hz=440.0, duration_s=1.0, sample_rate=16_000)
    assert len(pcm) == 32_000


def test_synth_sine_amplitude_bounded():
    pcm = synth_sine_pcm(amplitude=0.3)
    samples = struct.unpack(f"<{len(pcm) // 2}h", pcm)
    peak = int(0.3 * 32767)
    assert max(samples) <= peak
    assert min(samples) >= -peak
    # And it's actually oscillating, not silent.
    assert max(samples) > peak // 2
    assert min(samples) < -peak // 2


def test_synth_sine_rejects_bad_amplitude():
    with pytest.raises(ValueError):
        synth_sine_pcm(amplitude=1.5)
    with pytest.raises(ValueError):
        synth_sine_pcm(amplitude=-0.1)


def test_synth_sine_rejects_zero_sample_rate():
    with pytest.raises(ValueError):
        synth_sine_pcm(sample_rate=0)


def test_synth_sine_short_duration():
    """500 ms produces 16_000 * 0.5 = 8_000 samples = 16_000 bytes."""
    pcm = synth_sine_pcm(duration_s=0.5)
    assert len(pcm) == 16_000


def test_read_wav_pcm_round_trip(tmp_path):
    """Write a known PCM payload to a WAV, read it back, verify identity."""
    pcm = synth_sine_pcm(duration_s=0.25)  # 250 ms
    path = tmp_path / "tone.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(pcm)

    got = read_wav_pcm(str(path))
    assert got == pcm


def test_read_wav_pcm_rejects_stereo(tmp_path):
    path = tmp_path / "stereo.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x00" * 320)
    with pytest.raises(ValueError, match="mono"):
        read_wav_pcm(str(path))


def test_read_wav_pcm_rejects_wrong_sample_rate(tmp_path):
    path = tmp_path / "44k.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(44_100)
        wav.writeframes(b"\x00" * 320)
    with pytest.raises(ValueError, match="16 kHz"):
        read_wav_pcm(str(path))


def test_read_wav_pcm_rejects_8bit(tmp_path):
    path = tmp_path / "8bit.wav"
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(1)
        wav.setframerate(16_000)
        wav.writeframes(b"\x80" * 160)
    with pytest.raises(ValueError, match="16-bit"):
        read_wav_pcm(str(path))
