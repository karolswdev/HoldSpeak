"""Device, presence, mesh, and wake-word configuration (HS-117-12).

Extracted from the monolithic ``holdspeak/config.py``.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DeviceConfig:
    """Remote-audio-device config (AIPI-Lite & compatible clients).

    The PSK is generated lazily on first use by
    :func:`holdspeak.device_audio.ensure_device_psk` so existing
    installs that never touch the device path don't get their
    config rewritten on upgrade.
    """

    psk: str = ""


@dataclass
class PresenceConfig:
    """Desktop-presence config (HS-43-04).

    The ambient native HUD/tray is off by default and now **config-backed** -- a
    UI toggle flips ``enabled`` (persisted via /api/settings); the runtime starts
    or stops the presence host live. The legacy ``HOLDSPEAK_DESKTOP_PRESENCE=1``
    environment variable is retained only as a power-user / headless override
    (it force-enables regardless of this flag), no longer the only path.
    """

    enabled: bool = False
    # HS-56-01: Qlippy, the mascot layer on the presence surface -- a second
    # opt-in on top of ``enabled`` (existing presence users keep the minimal
    # ring). Off by default; unset is byte-identical.
    mascot: bool = False


@dataclass
class MeshConfig:
    """Mesh / LAN-discovery config (HSM-15-10).

    When ``holdspeak web`` binds off-loopback it advertises itself on the LAN
    via Bonjour (``_holdspeak._tcp``) so a companion (the iPad) can FIND it by
    name instead of hand-typing host/port. ``device_name`` is the advertised
    name; empty (the default) means "use the machine hostname". Loopback binds
    advertise nothing.
    """

    device_name: str = ""

    def __post_init__(self) -> None:
        self.device_name = str(self.device_name or "").strip()


@dataclass
class WakeWordConfig:
    """The wake word (HS-60): hands-free ARMING of dictation, off by default.

    The conditions baked in: the wake word never types directly -- the
    default ``action`` is ``"preview"`` (the result is journaled and shown,
    typed only on an explicit confirm); ``"type"`` is the user's explicit
    opt-in (configuring is consent, the voice-commands model). File-edited
    values are normalized tolerantly here; the settings route validates
    strictly (clean 400s).
    """

    enabled: bool = False
    model: str = "hey_jarvis"
    threshold: float = 0.5
    armed_window_seconds: float = 8.0
    action: str = "preview"  # "preview" | "type"

    def __post_init__(self) -> None:
        self.enabled = bool(self.enabled)
        self.model = str(self.model or "hey_jarvis").strip() or "hey_jarvis"
        try:
            self.threshold = float(self.threshold)
        except (TypeError, ValueError):
            self.threshold = 0.5
        self.threshold = min(1.0, max(0.0, self.threshold))
        try:
            self.armed_window_seconds = float(self.armed_window_seconds)
        except (TypeError, ValueError):
            self.armed_window_seconds = 8.0
        self.armed_window_seconds = min(30.0, max(2.0, self.armed_window_seconds))
        action = str(self.action or "preview").strip().lower()
        self.action = action if action in ("preview", "type") else "preview"
