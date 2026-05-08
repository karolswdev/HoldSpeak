"""``holdspeak device-psk`` CLI: show or rotate the shared device PSK.

The PSK gates the ``/api/devices/audio`` WebSocket. ``show`` prints
the current value (generating one on first call); ``rotate`` issues
a fresh PSK and persists it. Both commands write the PSK to stdout
on the last line so callers can pipe directly into device config.
"""

from __future__ import annotations

import sys
from typing import Any

from ..config import Config
from ..device_audio import ensure_device_psk, rotate_device_psk
from ..logging_config import get_logger

log = get_logger("commands.device")


def run_device_psk_command(args: Any) -> int:
    """Run ``holdspeak device-psk show|rotate``.

    Returns a process exit code suitable for ``raise SystemExit(...)``.
    """
    action = getattr(args, "psk_action", None)
    if action not in {"show", "rotate"}:
        print(
            "Usage: holdspeak device-psk {show,rotate}",
            file=sys.stderr,
        )
        return 2

    config = Config.load()

    if action == "show":
        psk = ensure_device_psk(config)
        print(psk)
        return 0

    if action == "rotate":
        psk = rotate_device_psk(config)
        print(psk)
        log.info("device_psk_rotated")
        return 0

    return 2  # unreachable
