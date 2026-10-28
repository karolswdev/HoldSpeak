"""Live slice 3 (2026-10-28): the microphone check the Live window's ready sheet reads.

Canvas ``docs/internal/betterment/canvases/live-direction-2026-10-27.html``,
direction A, Before: the Microphone row says what the hub hears *before* the
meeting starts, a level and a word ("Hearing"), and a refused grant shows the
one verb that fixes it. Until now the hub sent no level and no grant before a
meeting, so the row said "Ready", a claim nothing had read.

One short sample, on request, never a stream that stays open:

* The grant is read first, with the query half of the macOS pair only
  (``desktop_permissions``): a check never raises a system dialog. A grant
  that is refused, not asked yet, or not readable on a Mac opens no device.
* With a meeting live the meeting holds the microphone; the check says so and
  opens nothing.
* ``HOLDSPEAK_MIC_CHECK=off`` (every rig hub) opens no device and says so.
* Else it records ``SAMPLE_SECONDS`` from the configured meeting microphone and
  maps the RMS to the same 0..1 scale the meeting meter uses
  (``MeetingRecorder._level_from_audio``).
"""

from __future__ import annotations

import os
from typing import Any, Optional

from ..logging_config import get_logger

log = get_logger("meeting_session")

#: The switch that keeps a rig hub off the machine's microphone.
MIC_CHECK_ENV = "HOLDSPEAK_MIC_CHECK"
#: How long the check listens. Long enough for one spoken word or room noise.
SAMPLE_SECONDS = 0.6
SAMPLE_RATE = 16000
#: The level (0..1, -60..-10 dBFS) at or over which the row says "Hearing".
#: A dead or wrong device sends digital silence (0.0); room noise is over this.
HEARING_LEVEL = 0.1

#: Every state the check answers. The face maps each to a dot and a word.
STATES = ("hearing", "quiet", "not_allowed", "not_asked", "unknown", "in_use", "off", "failed")


def _switched_off() -> bool:
    return os.environ.get(MIC_CHECK_ENV, "").strip().lower() in {"0", "off", "false", "no"}


def _resolve_device(device: Optional[int | str]) -> Optional[int]:
    """The configured meeting microphone as a PortAudio index (None = default)."""
    from ..audio_devices import find_device_by_name, get_default_input_device

    if isinstance(device, int):
        return device
    if isinstance(device, str) and device.strip():
        found = find_device_by_name(device.strip())
        if found:
            return found.index
    default = get_default_input_device()
    return default.index if default else None


def _record_sample(device: Optional[int | str], seconds: float) -> Any:
    """Record one short mono sample. Module level, so a test replaces it."""
    import numpy as np
    import sounddevice as sd

    frames = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=_resolve_device(device),
    )
    sd.wait()
    return np.asarray(frames[:, 0], dtype=np.float32)


def _level(sample: Any) -> float:
    from ..meeting_recorder import MeetingRecorder

    return float(MeetingRecorder._level_from_audio(sample))


def check_microphone(device: Optional[int | str], *, meeting_active: bool = False) -> dict[str, Any]:
    """Read the grant, then (only when it is safe) listen once and say what was heard."""
    from ..desktop_permissions import DENIED, MICROPHONE, NOT_DETERMINED, UNKNOWN, permission

    grant = permission(MICROPHONE)
    answer: dict[str, Any] = {
        "device": device if isinstance(device, str) else ("" if device is None else str(device)),
        "permission": grant.state,
        "settings_url": grant.settings_url,
        "level": None,
        "state": "unknown",
        "seconds": SAMPLE_SECONDS,
        "error": "",
    }
    if grant.state == DENIED:
        answer["state"] = "not_allowed"
        return answer
    if grant.state == NOT_DETERMINED:
        answer["state"] = "not_asked"
        return answer
    # On a Mac an unreadable grant is not a grant: opening the device could
    # raise the system dialog. Off a Mac there is no grant to read.
    if grant.state == UNKNOWN and not grant.source.startswith("not macOS"):
        return answer
    if meeting_active:
        answer["state"] = "in_use"
        return answer
    if _switched_off():
        answer["state"] = "off"
        return answer
    try:
        sample = _record_sample(device, SAMPLE_SECONDS)
    except Exception as exc:  # noqa: BLE001 -- a refused device is an answer, not a 500
        log.info("microphone check failed: %s", exc)
        answer["state"] = "failed"
        answer["error"] = str(exc)[:200]
        return answer
    level = round(_level(sample), 3)
    answer["level"] = level
    answer["state"] = "hearing" if level >= HEARING_LEVEL else "quiet"
    return answer
