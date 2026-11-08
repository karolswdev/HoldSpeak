"""The one keystore: one master key in the OS keychain, every secret in one sealed file.

Owner ruling 2026-11-07 ("Why is it multiple keychains."): the hub kept one
Keychain item per secret. A macOS Keychain item trusts the binary that made
it, so a rebuilt venv raised one access prompt per item, a background hub
never saw them, and 15 threads waited in ``find_generic_password``.

Now:

- **One Keychain item**: service ``HoldSpeak``, account
  ``keystore-master-key``, 32 random bytes in base64. On macOS the hub reads
  and writes it through ``/usr/bin/security``: the item trusts that Apple
  binary, whose path never changes, so a rebuilt venv asks nothing. Elsewhere
  it is the native ``keyring`` backend (Secret Service, Windows vault).
- **One file**: ``~/.local/share/holdspeak/keystore.enc``, mode 0600,
  AES-GCM with the master key. Its plaintext is ``{service: {slot: value}}``.
- **Read once, bounded**: the master key is read at the first use (the hub
  warms it at startup) and waits at most :data:`READ_SECONDS`. A keychain
  that does not answer is "secrets unavailable" with one log line; it is
  asked again no sooner than :data:`RETRY_SECONDS` later. Nothing waits for
  good.
- **Migration**: a slot that is not in the file is looked for once per
  process in its old Keychain item (the per-module service names). A value
  found there is written to the file, read back, and only then is the old
  item deleted. :func:`warm` does this at startup for the fixed slots;
  People and channel keys move at their first read.
- **The rig file**: ``HOLDSPEAK_CHANNEL_KEYSTORE_FILE`` names a plain 0600
  JSON file of the same shape. A rig hub keeps its secrets there and never
  asks a keychain.
"""
from __future__ import annotations

import base64
import json
import os
import secrets as _secrets
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from .logging_config import get_logger

log = get_logger("keystore")

#: The rig's plain key file (PHILO-16): set, no keychain is asked.
CHANNEL_KEYSTORE_ENV = "HOLDSPEAK_CHANNEL_KEYSTORE_FILE"
SERVICE = "HoldSpeak"
MASTER_ACCOUNT = "keystore-master-key"
#: 2026-11-07 (#1818): a keychain read waits this long, then says no.
READ_SECONDS = 2.0
#: A failed master read is asked again no sooner than this.
RETRY_SECONDS = 60.0
KEY_BYTES = 32
_MAGIC = b"HSK1"
_NONCE = 12
SECURITY = "/usr/bin/security"
#: ``security`` exit code: the item is not in the keychain.
_NOT_FOUND = 44

NATIVE_BACKENDS = frozenset({
    "keyring.backends.macOS.Keyring",
    "keyring.backends.SecretService.Keyring",
    "keyring.backends.Windows.WinVaultKeyring",
})
CHAINER = "keyring.backends.chainer.ChainerBackend"

#: The fixed slots :func:`warm` moves out of their old Keychain items.
FIXED_SLOTS: tuple[tuple[str, str], ...] = (
    ("HoldSpeak Reach", "reach.telegram.bot_token"),
    ("HoldSpeak Reach", "reach.telegram.chat"),
    ("HoldSpeak Line", "calls.line.sip_password"),
    ("HoldSpeak Line", "calls.line.telnyx_api_key"),
    ("HoldSpeak Phone", "hub-secret"),
    ("HoldSpeak Phone", "apns-key"),
)

_file_lock = threading.RLock()


class KeystoreError(RuntimeError):
    """A content-free failure: ``missing``, ``locked`` or ``unavailable``."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


# ── where the keychain is ───────────────────────────────────────────


def home_has_a_keychain() -> bool:
    """On macOS, True only when HOME holds a login keychain; True elsewhere.

    A rig's scratch HOME has none: asking would make macOS show "A keychain
    cannot be found" on the owner's screen."""
    if sys.platform != "darwin":
        return True
    keychains = Path.home() / "Library" / "Keychains"
    return any((keychains / name).exists() for name in ("login.keychain-db", "login.keychain"))


def default_path() -> Path:
    return Path.home() / ".local" / "share" / "holdspeak" / "keystore.enc"


def rig_path() -> Optional[Path]:
    value = os.environ.get(CHANNEL_KEYSTORE_ENV, "").strip()
    return Path(value).expanduser() if value else None


def _backend_name(backend: Any) -> str:
    kind = type(backend)
    return f"{kind.__module__}.{kind.__qualname__}"


def native_backend(backend: Any) -> Any:
    """The backend when it is native; a chainer's first native backend; else None."""
    if _backend_name(backend) in NATIVE_BACKENDS:
        return backend
    if _backend_name(backend) == CHAINER:
        for inner in getattr(backend, "backends", None) or ():
            if _backend_name(inner) in NATIVE_BACKENDS:
                return inner
    return None


def bounded(fn: Callable[[], Any], seconds: float = READ_SECONDS) -> Any:
    """``fn()`` in a daemon thread; :class:`TimeoutError` after ``seconds``."""
    out: list[tuple[bool, Any]] = []

    def run() -> None:
        try:
            out.append((True, fn()))
        except BaseException as exc:  # noqa: BLE001 - handed back to the caller
            out.append((False, exc))

    worker = threading.Thread(target=run, name="keystore-read", daemon=True)
    worker.start()
    worker.join(seconds)
    if not out:
        raise TimeoutError("keystore")
    ok, value = out[0]
    if not ok:
        raise value
    return value


# ── the master key's home ───────────────────────────────────────────


class SecurityMaster:
    """macOS: the master key through ``/usr/bin/security``.

    The item trusts ``/usr/bin/security`` (the binary that made it), so a new
    hub interpreter asks nothing. ``run`` is the subprocess call (tests fake it)."""

    def __init__(self, run: Optional[Callable[..., Any]] = None, seconds: float = READ_SECONDS) -> None:
        self._run = run or subprocess.run
        self._seconds = seconds

    def _call(self, args: list[str]) -> Any:
        try:
            return self._run([SECURITY, *args], capture_output=True, text=True, timeout=self._seconds)
        except subprocess.TimeoutExpired:
            raise TimeoutError("keystore") from None

    def read(self) -> Optional[str]:
        done = self._call(["find-generic-password", "-s", SERVICE, "-a", MASTER_ACCOUNT, "-w"])
        if done.returncode == _NOT_FOUND:
            return None
        if done.returncode != 0:
            raise RuntimeError(f"security exit {done.returncode}")
        return str(done.stdout or "").strip() or None

    def write(self, value: str) -> None:
        done = self._call(["add-generic-password", "-U", "-s", SERVICE, "-a", MASTER_ACCOUNT, "-w", value])
        if done.returncode != 0:
            raise RuntimeError(f"security exit {done.returncode}")


class KeyringMaster:
    """Linux and Windows: the master key in the native ``keyring`` backend."""

    def __init__(self, backend: Any, seconds: float = READ_SECONDS) -> None:
        self._backend = backend
        self._seconds = seconds

    def read(self) -> Optional[str]:
        return bounded(lambda: self._backend.get_password(SERVICE, MASTER_ACCOUNT), self._seconds) or None

    def write(self, value: str) -> None:
        bounded(lambda: self._backend.set_password(SERVICE, MASTER_ACCOUNT, value), self._seconds)


def _native_keyring() -> Any:
    try:
        import keyring

        return native_backend(keyring.get_keyring())
    except Exception as exc:  # noqa: BLE001 - no keyring: no native store
        log.info(f"keystore: no native keyring ({type(exc).__name__})")
        return None


# ── the store ────────────────────────────────────────────────────────


class Keystore:
    """One file of secrets: sealed with a master key, or plain (a rig).

    ``master`` reads and writes the master key (``None``: unavailable);
    ``legacy`` is a keyring backend holding the old per-secret items to
    move (``None``: nothing to move)."""

    def __init__(self, path: Path, *, master: Any = None, legacy: Any = None, plain: bool = False,
                 seconds: float = READ_SECONDS, clock: Callable[[], float] = time.monotonic) -> None:
        self.path = Path(path)
        self.plain = plain
        self._master = master
        self._legacy = legacy
        self._seconds = seconds
        self._clock = clock
        self._key: Optional[bytes] = None
        self._failed_at: Optional[float] = None
        self._said: Optional[str] = None
        self._master_lock = threading.Lock()
        self._checked: set[tuple[str, str]] = set()
        self._delete_old = True

    # the master key

    def _say(self, reason: str) -> None:
        if self._said != reason:
            self._said = reason
            log.warning(f"keystore: secrets unavailable ({reason})")

    def _open(self) -> Optional[bytes]:
        if self.plain:
            return b""
        if self._key is not None:
            return self._key
        with self._master_lock:
            if self._key is not None:
                return self._key
            if self._master is None:
                if self._said is None:
                    self._said = "no keychain"
                    log.info("keystore: no keychain in this HOME; secrets unavailable")
                return None
            now = self._clock()
            if self._failed_at is not None and now - self._failed_at < RETRY_SECONDS:
                return None
            try:
                key = self._read_or_make()
            except TimeoutError:
                self._failed_at = now
                self._say(f"the keychain did not answer in {self._seconds:g} s")
                return None
            except Exception as exc:  # noqa: BLE001 - a dead keychain is "unavailable"
                self._failed_at = now
                self._say(f"the keychain refused: {type(exc).__name__}")
                return None
            if key is None:
                self._failed_at = now
                return None
            self._key, self._failed_at, self._said = key, None, None
            log.info("keystore: open")
            return key

    def _read_or_make(self) -> Optional[bytes]:
        encoded = self._master.read()
        if encoded:
            key = base64.b64decode(encoded.encode("ascii"), validate=True)
            if len(key) != KEY_BYTES:
                raise ValueError("master key length")
            return key
        if self.path.exists():
            # Never seal over a file another master key holds: keep it.
            self._say(f"the master key is gone; {self.path.name} is kept as it is")
            return None
        key = _secrets.token_bytes(KEY_BYTES)
        encoded = base64.b64encode(key).decode("ascii")
        self._master.write(encoded)
        if self._master.read() != encoded:
            raise RuntimeError("master key did not read back")
        log.info("keystore: made the master key (one Keychain item)")
        return key

    def available(self) -> bool:
        return self._open() is not None

    # the file

    def _load(self) -> dict[str, dict[str, str]]:
        key = self._open()
        if key is None:
            raise KeystoreError("unavailable")
        try:
            raw = self.path.read_bytes()
        except FileNotFoundError:
            return {}
        except OSError:
            raise KeystoreError("locked") from None
        try:
            if not self.plain:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM

                if not raw.startswith(_MAGIC):
                    raise ValueError("not a keystore")
                nonce = raw[len(_MAGIC):len(_MAGIC) + _NONCE]
                raw = AESGCM(key).decrypt(nonce, raw[len(_MAGIC) + _NONCE:], _MAGIC)
            data = json.loads(raw.decode("utf-8"))
        except Exception:  # noqa: BLE001 - a bad tag or bad JSON is "locked"
            raise KeystoreError("locked") from None
        if not isinstance(data, dict):
            raise KeystoreError("locked")
        return data

    def _save(self, data: dict[str, dict[str, str]]) -> None:
        key = self._open()
        if key is None:
            raise KeystoreError("unavailable")
        body = json.dumps(data, sort_keys=True).encode("utf-8")
        if not self.plain:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            nonce = _secrets.token_bytes(_NONCE)
            body = _MAGIC + nonce + AESGCM(key).encrypt(nonce, body, _MAGIC)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            os.fchmod(fd, 0o600)  # an existing .tmp keeps its mode through O_CREAT
            with os.fdopen(fd, "wb") as handle:
                handle.write(body)
            os.replace(tmp, self.path)
            os.chmod(self.path, 0o600)
        except OSError:
            raise KeystoreError("locked") from None

    @staticmethod
    def _bucket(data: dict, service: str) -> dict[str, str]:
        bucket = data.get(service)
        if bucket is None:
            return {}
        if not isinstance(bucket, dict):
            raise KeystoreError("locked")
        return bucket

    # the slots

    def get(self, service: str, slot: str) -> str:
        with _file_lock:
            value = self._bucket(self._load(), service).get(str(slot))
        if isinstance(value, str) and value:
            return value
        moved = self._move_legacy(service, str(slot))
        if moved:
            return moved
        raise KeystoreError("missing")

    def put(self, service: str, slot: str, value: Optional[str]) -> None:
        """Keep ``value``; an empty value forgets the slot."""
        with _file_lock:
            data = self._load()
            bucket = dict(self._bucket(data, service))
            if value:
                bucket[str(slot)] = str(value)
            else:
                bucket.pop(str(slot), None)
            if bucket:
                data[service] = bucket
            else:
                data.pop(service, None)
            self._save(data)
        self._checked.add((service, str(slot)))

    def delete(self, service: str, slot: str) -> None:
        self.put(service, slot, "")

    # the move from the old per-secret items

    def _move_legacy(self, service: str, slot: str) -> str:
        legacy = self._legacy
        if legacy is None or self.plain or (service, slot) in self._checked:
            return ""
        self._checked.add((service, slot))
        try:
            value = bounded(lambda: legacy.get_password(service, slot), self._seconds)
        except Exception as exc:  # noqa: BLE001 - a slow old item: stop asking old items
            self._legacy = None
            log.warning(f"keystore: the old Keychain items did not answer ({type(exc).__name__}); "
                        "they stay where they are")
            return ""
        if not value:
            return ""
        value = str(value)
        self.put(service, slot, value)
        with _file_lock:
            if self._bucket(self._load(), service).get(slot) != value:
                log.warning(f"keystore: {service} / {slot} did not read back; the old item is kept")
                return value
        if not self._delete_old:
            return value
        try:
            bounded(lambda: legacy.delete_password(service, slot), self._seconds)
        except Exception as exc:  # noqa: BLE001 - the file holds it; the old item is harmless
            if isinstance(exc, TimeoutError):
                self._delete_old = False  # one unanswered prompt is enough: keep the rest
            log.info(f"keystore: {service} / {slot} moved; its old item stays ({type(exc).__name__})")
            return value
        log.info(f"keystore: moved {service} / {slot} from its own Keychain item into {self.path.name}")
        return value


# ── the hub's store ──────────────────────────────────────────────────

_default_lock = threading.Lock()
_defaults: dict[tuple[str, ...], Keystore] = {}


def _build(rig: Optional[Path]) -> Keystore:
    if rig is not None:
        return Keystore(rig, plain=True)
    if not home_has_a_keychain():
        return Keystore(default_path())
    legacy = _native_keyring()
    if sys.platform == "darwin":
        master: Any = SecurityMaster()
    else:
        master = KeyringMaster(legacy) if legacy is not None else None
    return Keystore(default_path(), master=master, legacy=legacy)


def default(*, rig_file: bool = True) -> Keystore:
    """The hub's keystore: the rig's plain file when its env is set (and
    ``rig_file``), else the sealed file. One per HOME and env per process."""
    rig = rig_path() if rig_file else None
    ident = (str(rig or ""), str(Path.home()))
    with _default_lock:
        store = _defaults.get(ident)
        if store is None:
            store = _defaults[ident] = _build(rig)
        return store


def use(store: Optional[Keystore], *, rig_file: bool = True) -> None:
    """Tests: make ``store`` the hub's keystore for this HOME and env (None forgets)."""
    rig = rig_path() if rig_file else None
    ident = (str(rig or ""), str(Path.home()))
    with _default_lock:
        if store is None:
            _defaults.pop(ident, None)
        else:
            _defaults[ident] = store


def forget() -> None:
    """Tests: every cached store is built again."""
    with _default_lock:
        _defaults.clear()


def warm(slots: Iterable[tuple[str, str]] = FIXED_SLOTS) -> bool:
    """Hub startup: open the master key once and move the fixed slots."""
    store = default()
    if not store.available():
        return False
    for service, slot in slots:
        try:
            store.get(service, slot)
        except KeystoreError:
            pass
    return True


class Slots:
    """One service's slots, failing in the caller's own error codes."""

    def __init__(self, service: str, error: Callable[[str], Exception], *, missing: str, locked: str,
                 unavailable: str, store: Optional[Keystore] = None, rig_file: bool = True) -> None:
        self.service = service
        self._error = error
        self._codes = {"missing": missing, "locked": locked, "unavailable": unavailable}
        self._store = store
        self._rig_file = rig_file

    def store(self) -> Keystore:
        return self._store if self._store is not None else default(rig_file=self._rig_file)

    def available(self) -> bool:
        return self.store().available()

    def _call(self, fn: Callable[[Keystore], Any]) -> Any:
        try:
            return fn(self.store())
        except KeystoreError as exc:
            raise self._error(self._codes.get(exc.code, self._codes["locked"])) from None

    def get(self, slot: str) -> str:
        return self._call(lambda s: s.get(self.service, str(slot)))

    def put(self, slot: str, value: Optional[str]) -> None:
        self._call(lambda s: s.put(self.service, str(slot), value))

    def delete(self, slot: str) -> None:
        self._call(lambda s: s.delete(self.service, str(slot)))


__all__ = [
    "CHANNEL_KEYSTORE_ENV", "FIXED_SLOTS", "KeyringMaster", "Keystore", "KeystoreError", "READ_SECONDS",
    "SecurityMaster", "Slots", "bounded", "default", "default_path", "forget", "home_has_a_keychain",
    "native_backend", "rig_path", "use", "warm",
]
