"""PHILO-16 rig gap: a file key store for the channel keys (email, Slack).

``HOLDSPEAK_CHANNEL_KEYSTORE_FILE`` names a JSON file; when it is set, the
email and Slack channels keep their keys there instead of the OS keychain.
The rig envs set it to a file inside the isolated HOME, so a rig hub never
reads or writes the owner's Keychain. Unset (the owner's desk), the channels
use the keychain as before. The precedent is the People
``HOLDSPEAK_PEOPLE_KEYSTORE_FILE`` (``holdspeak/people/keys.py``).

File format: ``{"<service>": {"<slot>": "<value>"}}``, mode 0600.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Callable, Optional

CHANNEL_KEYSTORE_ENV = "HOLDSPEAK_CHANNEL_KEYSTORE_FILE"

_lock = threading.Lock()


def channel_keystore_path() -> Optional[Path]:
    """The file the env names, or None (the keychain)."""
    value = os.environ.get(CHANNEL_KEYSTORE_ENV, "").strip()
    return Path(value).expanduser() if value else None


class FileChannelKeyStore:
    """One channel's slots in the shared key file. Errors are the channel's own codes."""

    def __init__(
        self, path: Path, service: str, error: Callable[[str], Exception], missing_code: str, locked_code: str,
    ) -> None:
        self._path = Path(path)
        self._service = service
        self._error = error
        self._missing = missing_code
        self._locked = locked_code

    def _load(self) -> dict[str, dict[str, str]]:
        """The whole file; an unreadable or malformed file is the channel's ``locked`` code."""
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            raise self._error(self._locked) from None
        if not isinstance(data, dict):
            raise self._error(self._locked)
        return data

    def _bucket(self, data: dict) -> dict[str, str]:
        bucket = data.get(self._service)
        if bucket is None:
            return {}
        if not isinstance(bucket, dict):
            raise self._error(self._locked)
        return bucket

    def get(self, key_ref: str) -> str:
        with _lock:
            value = self._bucket(self._load()).get(str(key_ref))
        if not isinstance(value, str) or not value:
            raise self._error(self._missing)
        return value

    def put(self, key_ref: str, key: str) -> None:
        with _lock:
            data = self._load()
            bucket = dict(self._bucket(data))
            bucket[str(key_ref)] = str(key)
            data[self._service] = bucket
            tmp = self._path.with_suffix(self._path.suffix + ".tmp")
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                os.fchmod(fd, 0o600)  # an existing .tmp keeps its mode through O_CREAT
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(data, handle)
                os.replace(tmp, self._path)
                os.chmod(self._path, 0o600)
            except OSError:
                raise self._error(self._locked) from None
