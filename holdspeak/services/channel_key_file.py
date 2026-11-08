"""PHILO-16 rig gap: the channel keys' plain file (now one part of ``holdspeak/keystore.py``).

``HOLDSPEAK_CHANNEL_KEYSTORE_FILE`` names a JSON file; when it is set, every
keystore slot (email, Slack, Telegram, the Line, the Phone) is kept there and
no keychain is asked. The rig envs set it to a file inside the isolated HOME.
Unset (the owner's desk), the slots live in the one sealed keystore file.

File format: ``{"<service>": {"<slot>": "<value>"}}``, mode 0600.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .. import keystore

CHANNEL_KEYSTORE_ENV = keystore.CHANNEL_KEYSTORE_ENV


def channel_keystore_path() -> Optional[Path]:
    """The file the env names, or None (the sealed keystore)."""
    return keystore.rig_path()
