"""The one keystore (holdspeak/keystore.py): one master key, one sealed file.

Every keychain here is a fake: no test reads or writes the real macOS
Keychain, and ``keyring.get_keyring`` fails the test if it is reached.
"""
from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Optional

import pytest

from holdspeak import keystore
from holdspeak.keystore import Keystore, KeystoreError


class FakeMaster:
    """The one Keychain item."""

    def __init__(self, value: Optional[str] = None) -> None:
        self.value = value
        self.reads = 0
        self.writes = 0

    def read(self) -> Optional[str]:
        self.reads += 1
        return self.value

    def write(self, value: str) -> None:
        self.writes += 1
        self.value = value


class FakeKeyring:
    """The old per-secret Keychain items."""

    def __init__(self, items: Optional[dict[tuple[str, str], str]] = None, *, fail_delete: bool = False) -> None:
        self.items = dict(items or {})
        self.fail_delete = fail_delete

    def get_password(self, service: str, slot: str) -> Optional[str]:
        return self.items.get((service, slot))

    def set_password(self, service: str, slot: str, value: str) -> None:
        self.items[(service, slot)] = value

    def delete_password(self, service: str, slot: str) -> None:
        if self.fail_delete:
            raise RuntimeError("denied")
        self.items.pop((service, slot), None)


@pytest.fixture(autouse=True)
def _no_real_keychain(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    import keyring

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv(keystore.CHANNEL_KEYSTORE_ENV, raising=False)
    monkeypatch.setattr(keyring, "get_keyring", lambda: pytest.fail("the real keyring was reached"))
    monkeypatch.setattr(keystore.subprocess, "run", lambda *a, **k: pytest.fail("/usr/bin/security was run"))
    keystore.forget()
    yield
    keystore.forget()


def _store(tmp_path: Path, **kwargs: Any) -> Keystore:
    kwargs.setdefault("master", FakeMaster())
    return Keystore(tmp_path / "keystore.enc", **kwargs)


def test_a_secret_round_trips_through_one_sealed_file(tmp_path: Path) -> None:
    master = FakeMaster()
    store = _store(tmp_path, master=master)
    store.put("HoldSpeak Reach", "reach.telegram.bot_token", "123456:" + "a" * 35)
    store.put("HoldSpeak Line", "calls.line.sip_password", "sip-secret")
    assert store.get("HoldSpeak Reach", "reach.telegram.bot_token") == "123456:" + "a" * 35
    raw = store.path.read_bytes()
    assert raw.startswith(b"HSK1") and b"sip-secret" not in raw and b"123456" not in raw
    assert oct(store.path.stat().st_mode & 0o777) == "0o600"
    # A second process (a new Keystore on the same master) reads the same file.
    again = Keystore(store.path, master=master)
    assert again.get("HoldSpeak Line", "calls.line.sip_password") == "sip-secret"
    again.delete("HoldSpeak Line", "calls.line.sip_password")
    with pytest.raises(KeystoreError, match="missing"):
        again.get("HoldSpeak Line", "calls.line.sip_password")
    assert master.writes == 1 and master.reads >= 2


def test_one_keychain_item_holds_every_secret(tmp_path: Path) -> None:
    """Fails on main (no ``holdspeak.keystore``): the Telegram token, a Line
    secret, an email key and a People key all live in the one file, and the
    keychain holds exactly one item, the master key."""
    from holdspeak.line import secrets as line
    from holdspeak.people.keys import NativeKeyStore
    from holdspeak.services import channel_email, telegram_reach

    master = FakeMaster()
    store = _store(tmp_path, master=master, legacy=FakeKeyring())
    keystore.use(store)
    keystore.use(store, rig_file=False)

    telegram_reach._write(telegram_reach.TOKEN_SLOT, "123456:" + "b" * 35)
    line.write(line.SIP_PASSWORD, "sip-secret")
    channel_email.NativeEmailKeyStore().put("resend:main", "re_key")
    people = NativeKeyStore(store=store)
    people.put("people-key-v1:one", b"k" * 32)

    assert telegram_reach.bot_token() == "123456:" + "b" * 35
    assert line.read(line.SIP_PASSWORD) == "sip-secret"
    assert channel_email.NativeEmailKeyStore().get("resend:main") == "re_key"
    assert people.get("people-key-v1:one") == b"k" * 32
    assert master.writes == 1  # one Keychain item, made once
    assert sorted(store._load()) == ["HoldSpeak Email", "HoldSpeak Line", "HoldSpeak People", "HoldSpeak Reach"]


def test_a_keychain_that_does_not_answer_is_unavailable_within_the_deadline(tmp_path: Path) -> None:
    gate = threading.Event()

    class Slow(FakeKeyring):
        def get_password(self, service: str, slot: str) -> Optional[str]:
            gate.wait(10)
            return None

    store = _store(tmp_path, master=keystore.KeyringMaster(Slow(), seconds=0.2), seconds=0.2)
    keystore.use(store)
    from holdspeak.services import telegram_reach

    started = time.monotonic()
    with pytest.raises(KeystoreError, match="unavailable"):
        store.get("HoldSpeak Reach", "reach.telegram.bot_token")
    assert time.monotonic() - started < 1.5
    # A route never sees the failure, and never waits again before the retry.
    started = time.monotonic()
    assert telegram_reach.bot_token() == ""
    assert telegram_reach.paired_chat() is None
    with pytest.raises(telegram_reach.TelegramRefused):
        telegram_reach._write(telegram_reach.TOKEN_SLOT, "x")
    assert time.monotonic() - started < 0.2
    gate.set()


def test_a_security_timeout_is_unavailable_and_asks_again_after_the_retry(tmp_path: Path) -> None:
    calls: list[list[str]] = []
    answers: list[Any] = [subprocess.TimeoutExpired("security", 2.0)]

    def run(args: list[str], **_kw: Any) -> Any:
        calls.append(args)
        answer = answers.pop(0) if answers else subprocess.CompletedProcess(args, 44, "", "")
        if isinstance(answer, BaseException):
            raise answer
        return answer

    now = [100.0]
    master = keystore.SecurityMaster(run=run)
    store = _store(tmp_path, master=master, clock=lambda: now[0])
    assert store.available() is False
    assert store.available() is False and len(calls) == 1  # no second ask inside the retry window
    now[0] += keystore.RETRY_SECONDS + 1
    stored: dict[str, str] = {}

    def run_ok(args: list[str], **_kw: Any) -> Any:
        calls.append(args)
        if args[1] == "add-generic-password":
            stored["v"] = args[args.index("-w") + 1]
            return subprocess.CompletedProcess(args, 0, "", "")
        if "v" in stored:
            return subprocess.CompletedProcess(args, 0, stored["v"] + "\n", "")
        return subprocess.CompletedProcess(args, 44, "", "")

    master._run = run_ok
    assert store.available() is True
    assert all(c[0] == "/usr/bin/security" for c in calls)
    assert [c[1] for c in calls[1:]] == ["find-generic-password", "add-generic-password", "find-generic-password"]
    assert calls[2][calls[2].index("-s") + 1] == "HoldSpeak" and "-U" in calls[2]


def test_migration_moves_each_old_item_into_the_file_then_deletes_it(tmp_path: Path) -> None:
    import base64

    from holdspeak.people.keys import NativeKeyStore

    people_key = base64.b64encode(b"p" * 32).decode("ascii")
    old = FakeKeyring({
        ("HoldSpeak Reach", "reach.telegram.bot_token"): "123456:" + "c" * 35,
        ("HoldSpeak Reach", "reach.telegram.chat"): '{"id": "42"}',
        ("HoldSpeak People", "people-key-v1:abc"): people_key,
    })
    store = _store(tmp_path, legacy=old)
    keystore.use(store)
    assert keystore.warm() is True
    assert ("HoldSpeak Reach", "reach.telegram.bot_token") not in old.items
    assert store._load()["HoldSpeak Reach"] == {"reach.telegram.bot_token": "123456:" + "c" * 35,
                                                "reach.telegram.chat": '{"id": "42"}'}
    # A dynamic slot (a People key id) moves at its first read.
    assert NativeKeyStore(store=store).get("people-key-v1:abc") == b"p" * 32
    assert old.items == {}
    # A slot that was never anywhere asks the old items once per process.
    with pytest.raises(KeystoreError, match="missing"):
        store.get("HoldSpeak Line", "calls.line.sip_password")
    old.items[("HoldSpeak Line", "calls.line.sip_password")] = "late"
    with pytest.raises(KeystoreError, match="missing"):
        store.get("HoldSpeak Line", "calls.line.sip_password")


def test_migration_never_loses_a_secret(tmp_path: Path) -> None:
    # The file cannot be written: the old item stays.
    old = FakeKeyring({("HoldSpeak Reach", "reach.telegram.bot_token"): "tok"})
    blocked = tmp_path / "ro"
    blocked.mkdir()
    store = Keystore(blocked / "sub" / "keystore.enc", master=FakeMaster(), legacy=old)
    store.available()  # the master key is made before the folder is closed
    blocked.chmod(0o500)
    try:
        with pytest.raises(KeystoreError, match="locked"):
            store.get("HoldSpeak Reach", "reach.telegram.bot_token")
    finally:
        blocked.chmod(0o700)
    assert old.items == {("HoldSpeak Reach", "reach.telegram.bot_token"): "tok"}
    # The delete is refused: the value is served from the file; the old item is harmless.
    old2 = FakeKeyring({("HoldSpeak Line", "calls.line.sip_password"): "sip"}, fail_delete=True)
    store2 = _store(tmp_path, legacy=old2)
    assert store2.get("HoldSpeak Line", "calls.line.sip_password") == "sip"
    assert store2._load()["HoldSpeak Line"] == {"calls.line.sip_password": "sip"}
    # A delete that waits on a prompt: the move goes on, the later old items stay.
    gate = threading.Event()

    class Prompting(FakeKeyring):
        def delete_password(self, service: str, slot: str) -> None:
            gate.wait(10)

    old3 = Prompting({("HoldSpeak Reach", "a"): "1", ("HoldSpeak Reach", "b"): "2"})
    store3 = Keystore(tmp_path / "three.enc", master=FakeMaster(), legacy=old3, seconds=0.2)
    assert store3.get("HoldSpeak Reach", "a") == "1"
    started = time.monotonic()
    assert store3.get("HoldSpeak Reach", "b") == "2"
    assert time.monotonic() - started < 0.2  # no second wait on a delete
    gate.set()


def test_a_lost_master_key_never_seals_over_the_file(tmp_path: Path) -> None:
    first = _store(tmp_path)
    first.put("HoldSpeak Reach", "reach.telegram.bot_token", "tok")
    before = first.path.read_bytes()
    gone = FakeMaster()  # the Keychain item was removed
    second = Keystore(first.path, master=gone)
    with pytest.raises(KeystoreError, match="unavailable"):
        second.get("HoldSpeak Reach", "reach.telegram.bot_token")
    assert gone.writes == 0 and first.path.read_bytes() == before
    # Another master key cannot open it: locked, never overwritten.
    other = Keystore(first.path, master=FakeMaster(keystore.base64.b64encode(b"z" * 32).decode()))
    with pytest.raises(KeystoreError, match="locked"):
        other.get("HoldSpeak Reach", "reach.telegram.bot_token")
    assert first.path.read_bytes() == before


def test_only_a_native_keyring_backend_may_hold_the_master_key() -> None:
    def fake(module: str, name: str, **attrs: Any) -> Any:
        attrs["__module__"] = module
        return type(name, (), attrs)()

    for module, name in (("keyring.backends.macOS", "Keyring"), ("keyring.backends.SecretService", "Keyring"),
                         ("keyring.backends.Windows", "WinVaultKeyring")):
        native = fake(module, name)
        assert keystore.native_backend(native) is native
        chained = fake("keyring.backends.chainer", "ChainerBackend",
                       backends=[fake("keyring.backends.fail", "Keyring"), native])
        assert keystore.native_backend(chained) is native
    for refused in (fake("keyring.backends.fail", "Keyring"), fake("keyrings.alt.file", "PlaintextKeyring"),
                    fake("keyrings.alt.file", "EncryptedKeyring"), fake("keyring.backends.null", "Keyring"),
                    fake("keyring.backends.chainer", "ChainerBackend", backends=[])):
        assert keystore.native_backend(refused) is None


def test_the_rig_file_is_plain_and_never_asks_a_keychain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import telegram_reach

    path = tmp_path / "keys.json"
    monkeypatch.setenv(keystore.CHANNEL_KEYSTORE_ENV, str(path))
    telegram_reach._write(telegram_reach.TOKEN_SLOT, "tok")
    assert telegram_reach.bot_token() == "tok"
    assert keystore.json.loads(path.read_text()) == {"HoldSpeak Reach": {"reach.telegram.bot_token": "tok"}}


def test_a_home_with_no_keychain_is_unavailable_without_asking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(keystore.sys, "platform", "darwin")
    store = keystore.default()
    assert store.available() is False
    assert keystore.warm() is False
    with pytest.raises(KeystoreError, match="unavailable"):
        store.put("HoldSpeak Reach", "x", "y")
