"""Phone (2026-10-28): the device token, the pairing token's life, revoke."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.phone import devices as devs
from holdspeak.phone.push import NullPush
from holdspeak.phone.service import OWNER, PhoneRefused, PhoneService
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.timestamps import utc_now


class _NoNumber:
    def number(self) -> str:
        return ""

    def available(self) -> tuple[bool, str]:
        return False, "no number"


@pytest.fixture
def phone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PhoneService:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "keys.json"))
    devs.forget_cached_secret()
    service = PhoneService(Database(tmp_path / "phone.db"), push=NullPush(), number=_NoNumber(),
                           kernel=lambda data: None)
    yield service
    service.stop()
    devs.forget_cached_secret()


def _pair(phone: PhoneService) -> dict:
    token = phone.pair_token(OWNER, hub_urls=["http://127.0.0.1:8765"])["token"]
    return phone.redeem({"pair_token": token, "name": "Phone", "platform": "test"})


def test_the_device_jwt_is_hs256_signed_and_checked_against_the_row(phone: PhoneService) -> None:
    paired = _pair(phone)
    header, claims, sig = paired["device_jwt"].split(".")
    import json

    assert json.loads(devs.unb64u(header))["alg"] == "HS256"
    assert json.loads(devs.unb64u(claims))["sub"] == paired["device_id"]
    assert phone.authenticate(paired["device_jwt"])["id"] == paired["device_id"]
    forged = f"{header}.{claims}.{devs.b64u(b'0' * 32)}"
    assert phone.authenticate(forged) is None
    other = devs.issue_jwt(b"another hub's secret", paired["device_id"], "k_x")
    assert phone.authenticate(other) is None


def test_revoke_is_rechecked_on_every_request(phone: PhoneService) -> None:
    paired = _pair(phone)
    assert phone.authenticate(paired["device_jwt"]) is not None
    phone.revoke(OWNER, paired["device_id"])
    assert phone.authenticate(paired["device_jwt"]) is None
    with pytest.raises(PhoneRefused):
        phone.revoke(Principal(PrincipalKind.AGENT, "a"), paired["device_id"])


def test_a_pairing_token_works_once_and_dies_after_ten_minutes(phone: PhoneService, monkeypatch) -> None:
    token = phone.pair_token(OWNER, hub_urls=[])["token"]
    phone.redeem({"pair_token": token, "name": "Phone", "platform": "test"})
    with pytest.raises(PhoneRefused) as again:
        phone.redeem({"pair_token": token, "name": "Phone", "platform": "test"})
    assert again.value.context["status"] == 401
    late = phone.pair_token(OWNER, hub_urls=[])["token"]
    eleven = utc_now() + timedelta(minutes=11)
    monkeypatch.setattr(phone, "_now", lambda: eleven)
    with pytest.raises(PhoneRefused, match="expired"):
        phone.redeem({"pair_token": late, "name": "Phone", "platform": "test"})
    with pytest.raises(PhoneRefused):
        phone.pair_token(Principal(PrincipalKind.AGENT, "a"))


def test_the_hub_secret_is_made_once_and_kept_in_the_key_store(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "keys.json"))
    devs.forget_cached_secret()
    first = devs.hub_secret()
    devs.forget_cached_secret()
    assert devs.hub_secret() == first and len(first) == 32
    assert "HoldSpeak Phone" in (tmp_path / "keys.json").read_text()
    devs.forget_cached_secret()
