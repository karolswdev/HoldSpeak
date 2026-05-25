"""AIPI-Lite ↔ HoldSpeak bridge — package re-exports.

A stateless async forwarder between the AIPI-Lite ESPHome API and
HoldSpeak's `/api/devices/audio` WebSocket. The legs (`DeviceLeg`,
`HoldSpeakLeg`) live in their own modules; this `__init__` exists to
preserve the flat `from bridge import X` import surface tests + callers
have always used.

Run:    python -m bridge
Plan:   pm/roadmap/aipi-lite/phase-2-bridge-protocol-translator/
Wire:   ~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md
"""

from __future__ import annotations

# Re-export everything tests + external callers use as `from bridge import X`.
# The submodules (e.g. `bridge.reconnect`) remain canonical; this is a
# convenience facade so the package layout doesn't break the public API.
from bridge.audio import (
    AUDIO_QUEUE_MAXSIZE,
    BYTES_PER_SAMPLE,
    BYTES_PER_SECOND,
    CONTROL_QUEUE_MAXSIZE,
    SAMPLE_RATE_HZ,
    TEST_AUDIO_CHUNK_BYTES,
    TEST_AUDIO_CHUNK_MS,
    read_wav_pcm,
    synth_sine_pcm,
)
from bridge.cli import (
    _audio_loopback,
    _check,
    _run,
    _send_test_audio,
    main,
)
from bridge.device import DeviceLeg
from bridge.holdspeak import HoldSpeakLeg
from bridge.lcd import (
    _ACTIVITY_SYMBOLS,
    DEFAULT_ACTIVITY_SYMBOL,
    ERROR_ACTIVITY_SYMBOL,
    ERROR_FLASH_MS,
    LINK_CONNECTING,
    LINK_OFFLINE,
    LINK_ONLINE,
    SESSION_BUSY_FLASH_MS,
    _format_activity,
    _pick_activity_symbol,
)
from bridge.logging_setup import configure_logging
from bridge.reconnect import (
    RECONNECT_FLOOR_S,
    RECONNECT_JITTER,
    RECONNECT_SCHEDULE_S,
    _backoff_seconds,
    _close_code_reason,
    reconnect_with_backoff,
)
from bridge.settings import Settings, load_settings

__all__ = [
    # Public surface
    "DeviceLeg",
    "HoldSpeakLeg",
    "Settings",
    "configure_logging",
    "load_settings",
    "main",
    "reconnect_with_backoff",
    # Audio constants + helpers
    "AUDIO_QUEUE_MAXSIZE",
    "BYTES_PER_SAMPLE",
    "BYTES_PER_SECOND",
    "CONTROL_QUEUE_MAXSIZE",
    "SAMPLE_RATE_HZ",
    "TEST_AUDIO_CHUNK_BYTES",
    "TEST_AUDIO_CHUNK_MS",
    "read_wav_pcm",
    "synth_sine_pcm",
    # LCD constants + helpers
    "DEFAULT_ACTIVITY_SYMBOL",
    "ERROR_ACTIVITY_SYMBOL",
    "ERROR_FLASH_MS",
    "LINK_CONNECTING",
    "LINK_OFFLINE",
    "LINK_ONLINE",
    "SESSION_BUSY_FLASH_MS",
    # Reconnect helpers
    "RECONNECT_FLOOR_S",
    "RECONNECT_JITTER",
    "RECONNECT_SCHEDULE_S",
]
