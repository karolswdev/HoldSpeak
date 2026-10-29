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
