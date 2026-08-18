"""Local, write-only custody for destination API keys.

Profile records, sync payloads and the inference-target API deliberately never
contain credentials.  This small local sidecar stores only a profile's
injective environment-slot name, never its profile id, and is read afresh on
every lookup so changes take effect without restarting the hub.
"""
from __future__ import annotations

import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Literal


class ProfileKeyStoreError(RuntimeError):
    """A content-free custody error; never include a key or file contents."""


KeyState = Literal["set", "deleted", "missing"]


class ProfileKeyStore:
    VERSION = 1

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else Path.home() / ".holdspeak" / "profile-custody" / "profile-keys.json"

    def state(self, slot: str) -> tuple[KeyState, str | None]:
        data = self._read()
        entry = data["entries"].get(slot)
        if entry is None:
            return "missing", None
        if not isinstance(entry, dict) or entry.get("state") not in {"set", "deleted"}:
            raise ProfileKeyStoreError("Profile key store is unavailable")
        if entry["state"] == "deleted":
            return "deleted", None
        value = entry.get("value")
        if not isinstance(value, str) or not value:
            raise ProfileKeyStoreError("Profile key store is unavailable")
        return "set", value

    def set(self, slot: str, value: str) -> None:
        if not isinstance(value, str) or not value:
            raise ProfileKeyStoreError("Profile key value is invalid")
        with self._lock():
            data = self._read()
            data["entries"][slot] = {"state": "set", "value": value}
            self._write(data)

    def delete(self, slot: str) -> None:
        with self._lock():
            data = self._read()
            data["entries"][slot] = {"state": "deleted"}
            self._write(data)

    def _read(self) -> dict[str, object]:
        # Readiness must not leave a custody directory behind. An absent parent
        # simply means no local entry yet; any existing parent is still checked
        # before we trust a file beneath it.
        if not os.path.lexists(self.path.parent):
            return {"version": self.VERSION, "entries": {}}
        self._ensure_parent()
        if not os.path.lexists(self.path):
            return {"version": self.VERSION, "entries": {}}
        expected = self._assert_safe_file(self.path)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = -1
        try:
            fd = os.open(self.path, flags)
            opened = os.fstat(fd)
            if (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino):
                raise ProfileKeyStoreError("Profile key store is unavailable")
            with os.fdopen(fd, "r", encoding="utf-8") as handle:
                fd = -1
                raw = json.load(handle)
        except ProfileKeyStoreError:
            raise
        except Exception as exc:
            raise ProfileKeyStoreError("Profile key store is unavailable") from None
        finally:
            if fd >= 0:
                os.close(fd)
        if not isinstance(raw, dict) or raw.get("version") != self.VERSION or not isinstance(raw.get("entries"), dict):
            raise ProfileKeyStoreError("Profile key store is unavailable")
        return raw

    def _write(self, data: dict[str, object]) -> None:
        self._ensure_parent()
        fd, temp_name = tempfile.mkstemp(prefix=".profile-keys-", dir=self.path.parent)
        temp = Path(temp_name)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, separators=(",", ":"), sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self.path)
            if os.name != "nt":
                directory = os.open(self.path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
        finally:
            if temp.exists():
                temp.unlink(missing_ok=True)

    @staticmethod
    def _assert_safe_file(path: Path) -> os.stat_result:
        try:
            info = path.lstat()
        except OSError as exc:
            raise ProfileKeyStoreError("Profile key store is unavailable") from None
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ProfileKeyStoreError("Profile key store is unavailable")
        if hasattr(os, "getuid") and info.st_uid != os.getuid():
            raise ProfileKeyStoreError("Profile key store is unavailable")
        if info.st_mode & 0o077:
            raise ProfileKeyStoreError("Profile key store is unavailable")
        return info

    def _ensure_parent(self) -> None:
        parent = self.path.parent
        if not os.path.lexists(parent):
            try:
                parent.mkdir(mode=0o700, parents=True)
            except OSError:
                raise ProfileKeyStoreError("Profile key store is unavailable") from None
        try:
            info = parent.lstat()
        except OSError:
            raise ProfileKeyStoreError("Profile key store is unavailable") from None
        if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
            raise ProfileKeyStoreError("Profile key store is unavailable")
        if hasattr(os, "getuid") and info.st_uid != os.getuid():
            raise ProfileKeyStoreError("Profile key store is unavailable")
        if info.st_mode & 0o077:
            raise ProfileKeyStoreError("Profile key store is unavailable")

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self._ensure_parent()
        lock = self.path.with_suffix(self.path.suffix + ".lock")
        flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(lock, flags, 0o600)
        try:
            os.fchmod(fd, 0o600)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or (hasattr(os, "getuid") and info.st_uid != os.getuid()) or info.st_mode & 0o077:
                raise ProfileKeyStoreError("Profile key store is unavailable")
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)


def _default_profile_key_store() -> ProfileKeyStore:
    return ProfileKeyStore()


def resolve_profile_key(slot: str, *, store: ProfileKeyStore | None = None) -> str | None:
    """Stored value wins; a tombstone deliberately suppresses inherited env."""
    state, value = (store or _default_profile_key_store()).state(slot)
    if state == "set":
        return value
    if state == "deleted":
        return None
    value = os.environ.get(slot, "").strip()
    return value or None
