"""Phone (2026-10-28): the signed push payload and the APNs request."""
from __future__ import annotations

import json
from pathlib import Path

from holdspeak.phone.push import (
    MAX_EVENT_BYTES, REPLY_CATEGORY, ApnsKey, Target, apns_request, build_payload, sign,
)

PHONE = Path(__file__).resolve().parents[1] / "fixtures" / "phone"


def test_the_recorded_payload_signature_checks() -> None:
    recorded = json.loads((PHONE / "push_data.json").read_text())
    data = recorded["data"]
    assert sign(recorded["push_secret"], data["event"]) == data["sig"]
    assert sign(recorded["push_secret"], data["event"] + " ") != data["sig"]


def test_a_long_message_is_cut_to_fit_and_still_signed() -> None:
    event = {"seq": 3, "type": "message.new", "ts": "t", "data": {"message": {"text": "x" * 9000}}}
    payload = build_payload("hub_1", "c2VjcmV0", event)
    assert len(payload["event"].encode()) <= MAX_EVENT_BYTES
    assert json.loads(payload["event"])["data"]["truncated"] is True
    assert payload["sig"] == sign("c2VjcmV0", payload["event"])


def _key() -> ApnsKey:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    pem = ec.generate_private_key(ec.SECP256R1()).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    return ApnsKey(team_id="TEAM123456", key_id="KEY1234567", p8=pem, bundle_id="dev.holdspeak.app")


def test_a_call_is_a_voip_push_and_a_message_an_alert_with_the_reply_category() -> None:
    key = _key()
    payload = build_payload("hub_1", "c2VjcmV0", {"seq": 1, "type": "call.invite", "ts": "t", "data": {}})
    url, headers, body = apns_request(key, Target("dev_1", "tok", "call"), payload, 30, True)
    assert url.endswith("/3/device/tok") and headers["apns-topic"] == "dev.holdspeak.app.voip"
    assert headers["apns-push-type"] == "voip" and headers["apns-priority"] == "10"
    assert headers["authorization"].startswith("bearer ") and body["sig"] == payload["sig"]
    message = build_payload("hub_1", "c2VjcmV0", {"seq": 2, "type": "message.new", "ts": "t",
                                                  "data": {"message": {"text": "Retry the build?"}}})
    _url, headers, body = apns_request(key, Target("dev_1", "tok", "message"), message, 60, True)
    assert headers["apns-topic"] == "dev.holdspeak.app" and headers["apns-push-type"] == "alert"
    assert body["aps"]["category"] == REPLY_CATEGORY and body["aps"]["alert"]["body"] == "Retry the build?"


# ── RECIPE PH13: APNs sends for real (HTTP/2) and the device row says why it would not ──

import base64  # noqa: E402

import pytest  # noqa: E402

from holdspeak.phone import push as push_module  # noqa: E402
from holdspeak.phone.push import (  # noqa: E402
    OK, PUSH_HTTP2_UNAVAILABLE, PUSH_NO_KEY, PUSH_READY, PUSH_UNREGISTERED, UNREGISTERED, ApnsPush, NullPush,
    apns_from_keystore, apns_jwt, http2_ready,
)
from holdspeak.phone.service import device_wire  # noqa: E402
from tests.fixtures.fake_apns import FakeApns  # noqa: E402


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _verify_es256(key: ApnsKey, token: str) -> dict:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

    head, claims, sig = token.split(".")
    raw = _unb64(sig)
    assert len(raw) == 64  # JOSE r || s, not DER
    public = serialization.load_pem_private_key(key.p8.encode(), password=None).public_key()
    der = encode_dss_signature(int.from_bytes(raw[:32], "big"), int.from_bytes(raw[32:], "big"))
    public.verify(der, f"{head}.{claims}".encode(), ec.ECDSA(hashes.SHA256()))  # raises when wrong
    return {"header": json.loads(_unb64(head)), "claims": json.loads(_unb64(claims))}


def test_the_provider_token_is_es256_over_team_and_iat_with_the_key_id() -> None:
    key = _key()
    token = apns_jwt(key, now=1_761_700_000)
    parts = _verify_es256(key, token)
    assert parts["header"] == {"alg": "ES256", "kid": "KEY1234567"}
    assert parts["claims"] == {"iss": "TEAM123456", "iat": 1_761_700_000}


def test_h2_is_installed_and_apns_says_ready() -> None:
    assert http2_ready() is True
    assert ApnsPush(_key()).push_state() == PUSH_READY


def test_without_h2_apns_says_http2_unavailable_and_sends_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(push_module, "http2_ready", lambda: False)
    provider = ApnsPush(_key(), host="http://127.0.0.1:9")
    assert provider.push_state() == PUSH_HTTP2_UNAVAILABLE
    assert provider.send(Target("dev_1", "tok", "message"), {"v": "1"}, 60, True) == "error"


def test_a_call_and_a_message_reach_a_fake_apns_over_http2_signed_and_authorised() -> None:
    key = _key()
    call = build_payload("hub_1", "c2VjcmV0", {"seq": 1, "type": "call.invite", "ts": "t", "data": {}})
    message = build_payload("hub_1", "c2VjcmV0", {"seq": 2, "type": "message.new", "ts": "t",
                                                  "data": {"message": {"text": "Retry the build?"}}})
    with FakeApns() as apns:
        provider = ApnsPush(key, host=apns.url)
        assert provider.send(Target("dev_1", "calltoken", "call"), call, 30, True) == OK
        assert provider.send(Target("dev_1", "msgtoken", "message"), message, 3600, False) == OK
    first, second = apns.requests
    assert first["method"] == "POST" and first["path"] == "/3/device/calltoken"
    assert first["headers"]["apns-topic"] == "dev.holdspeak.app.voip"
    assert first["headers"]["apns-push-type"] == "voip" and first["headers"]["apns-priority"] == "10"
    assert second["path"] == "/3/device/msgtoken" and second["headers"]["apns-topic"] == "dev.holdspeak.app"
    assert second["headers"]["apns-push-type"] == "alert" and second["headers"]["apns-priority"] == "5"
    for request, payload in ((first, call), (second, message)):
        scheme, token = request["headers"]["authorization"].split(" ")
        assert scheme == "bearer" and _verify_es256(key, token)["claims"]["iss"] == "TEAM123456"
        body = request["body"]
        assert body["sig"] == sign("c2VjcmV0", body["event"]) == payload["sig"]
        assert body["event"] == payload["event"] and body["hub_id"] == "hub_1"
    assert first["body"]["aps"] == {}
    assert second["body"]["aps"]["category"] == REPLY_CATEGORY
    assert second["body"]["aps"]["alert"]["body"] == "Retry the build?"


def test_apple_saying_the_token_is_dead_is_unregistered() -> None:
    with FakeApns(answers={"dead": (410, {"reason": "Unregistered"}),
                           "bad": (400, {"reason": "BadDeviceToken"}),
                           "busy": (429, {"reason": "TooManyRequests"})}) as apns:
        provider = ApnsPush(_key(), host=apns.url)
        target = lambda token: Target("dev_1", token, "message")  # noqa: E731
        assert provider.send(target("dead"), {"v": "1"}, 60, True) == UNREGISTERED
        assert provider.send(target("bad"), {"v": "1"}, 60, True) == UNREGISTERED
        assert provider.send(target("busy"), {"v": "1"}, 60, True) == "error"


def test_the_saved_key_in_the_keystore_makes_an_apns_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.phone.devices import _store_for

    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "keys.json"))
    assert apns_from_keystore() is None
    key = _key()
    _store_for("apns-key").put(json.dumps({"team_id": key.team_id, "key_id": key.key_id, "p8": key.p8,
                                           "bundle_id": key.bundle_id, "environment": "sandbox"}))
    provider = apns_from_keystore()
    assert isinstance(provider, ApnsPush) and provider.push_state() == PUSH_READY
    url, headers, _body = apns_request(provider._key, Target("d", "tok", "call"), {"v": "1"}, 30, True)
    assert url == "https://api.sandbox.push.apple.com/3/device/tok"
    assert _verify_es256(key, headers["authorization"].split(" ")[1])["header"]["kid"] == key.key_id


@pytest.mark.parametrize(("token", "provider", "word"), [
    ("tok", PUSH_READY, "ready"),
    ("tok", PUSH_NO_KEY, "no_key"),
    ("tok", PUSH_HTTP2_UNAVAILABLE, "http2_unavailable"),
    (None, PUSH_READY, "unregistered"),
])
def test_the_device_row_carries_the_push_word(token: str | None, provider: str, word: str) -> None:
    row = {"id": "dev_1", "name": "iPhone", "platform": "ios", "state": "paired", "push_token": token,
           "paired_at": "2026-10-29T10:00:00+00:00"}
    out = device_wire(row, provider)
    assert out["push_state"] == word and out["has_push"] is bool(token)
    from holdspeak.phone.contract import Device

    assert Device.model_validate(out).push_state == word
    assert PUSH_UNREGISTERED == "unregistered"


def test_the_hub_without_a_saved_key_says_no_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.db import Database
    from holdspeak.phone.service import PhoneService

    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(tmp_path / "keys.json"))
    hub = PhoneService(Database(tmp_path / "p.db"))
    assert hub.push_state() == PUSH_NO_KEY
    rig = PhoneService(Database(tmp_path / "q.db"), push=NullPush())
    assert rig.push_state() == PUSH_READY
