"""Pushes that wake a locked phone: APNs for the Apple app, a null one for rigs.

``PushProvider.send(target, payload, ttl, high_priority)`` answers ``ok``,
``unregistered`` (the token is dead: the hub forgets it) or ``error``.

- :class:`ApnsPush`: token-based APNs (an ES256 JWT from his ``.p8`` key in
  the key store, ``team_id`` and ``key_id`` beside it). A call is a VoIP push
  (topic ``<bundle>.voip``, PushKit wakes the app for CallKit); a message is
  an alert push with the reply category (``HOLDSPEAK_REPLY``) so he answers
  from the lock screen. APNs speaks HTTP/2 only (``httpx[http2]`` is a core
  dependency, RECIPE PH13); without h2 the provider answers ``error``.
- :class:`NullPush`: logs and keeps what it would have sent (the rig).

Each provider says whether it can send (:func:`http2_ready`, ``push_state``):
``ready``, ``no_key`` (no APNs key saved: the hub's fallback NullPush) or
``http2_unavailable``. The device row adds ``unregistered`` (no push token),
so the Phone section says why a push will not go.

Every payload carries the event as JSON text and its signature: HMAC-SHA256
with the device's own push secret, base64url. The app checks it before it
rings or shows anything, so a push nobody signed shows nothing. The payload
shape (``v``, the hub, the event text, ``sig``) and the cut of a long
message to fit the push limit are agentring's
(``relay/src/push/dispatcher.ts``, ``protocol/examples/push/``).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Protocol

from ..logging_config import get_logger
from .devices import b64u

log = get_logger("phone.push")

OK = "ok"
UNREGISTERED = "unregistered"
ERROR = "error"

#: APNs takes 4 KB for an alert (5 KB for VoIP); leave room for the rest.
MAX_EVENT_BYTES = 3000
REPLY_CATEGORY = "HOLDSPEAK_REPLY"
#: The device row's push word (``push_state`` on the wire).
PUSH_READY = "ready"
PUSH_NO_KEY = "no_key"
PUSH_HTTP2_UNAVAILABLE = "http2_unavailable"
PUSH_UNREGISTERED = "unregistered"
PUSH_STATES = (PUSH_READY, PUSH_NO_KEY, PUSH_HTTP2_UNAVAILABLE, PUSH_UNREGISTERED)
APNS_HOSTS = {"production": "https://api.push.apple.com", "sandbox": "https://api.sandbox.push.apple.com"}
#: The phone key store's slot for his APNs key (one JSON text: ``p8``,
#: ``key_id``, ``team_id``, ``bundle_id``, ``environment``).
APNS_SLOT = "apns-key"
#: The HoldSpeak app's bundle id (``apple/scripts/gen-device-project.rb``,
#: ``apple/App/Info.plist``): the APNs topic when he saves no other.
DEFAULT_BUNDLE_ID = "dev.holdspeak.mobile"
#: The fields of the saved key; ``p8`` is never read back to a face.
APNS_FIELDS = ("p8", "key_id", "team_id", "bundle_id")
#: The Test push's answer codes (``POST /api/phone/push/test``).
TEST_ACCEPTED = "accepted"
TEST_STALE = "stale"
TEST_REFUSED = "refused"
TEST_FAILED = "failed"


def sign(secret: str, event_json: str) -> str:
    """``base64url(HMAC-SHA256(base64url_decode(secret), utf8(event)))``."""
    from .devices import unb64u

    return b64u(hmac.new(unb64u(secret), event_json.encode("utf-8"), hashlib.sha256).digest())


def build_payload(hub: str, secret: str, event: Mapping[str, Any]) -> dict[str, str]:
    """The signed data a push carries; a long message is cut to fit."""
    text_json = json.dumps(dict(event), separators=(",", ":"), ensure_ascii=False)
    if event.get("type") == "message.new":
        message = dict((event.get("data") or {}).get("message") or {})
        text = str(message.get("text") or "")
        while len(text_json.encode("utf-8")) > MAX_EVENT_BYTES and text:
            over = len(text_json.encode("utf-8")) - MAX_EVENT_BYTES
            text = text[: max(0, len(text) - max(over, 16))]
            message["text"] = text + "…"
            cut = {**dict(event), "data": {**dict(event.get("data") or {}), "message": message, "truncated": True}}
            text_json = json.dumps(cut, separators=(",", ":"), ensure_ascii=False)
    return {"v": "1", "hub_id": hub, "event": text_json, "sig": sign(secret, text_json)}


@dataclass
class Target:
    device_id: str
    token: str
    kind: str  # call | message


class PushProvider(Protocol):
    name: str

    def send(self, target: Target, payload: Mapping[str, str], ttl: int, high_priority: bool) -> str: ...

    def push_state(self) -> str: ...


def http2_ready() -> bool:
    """True when h2 imports (``httpx[http2]``)."""
    try:
        import h2  # noqa: F401
    except ImportError:
        return False
    return True


@dataclass
class NullPush:
    """Sends nothing; keeps what it would have sent (tests read ``sent``)."""

    name: str = "null"
    sent: list[dict[str, Any]] = field(default_factory=list)
    #: ``ready`` for a rig; the hub's fallback when no APNs key is saved is
    #: ``NullPush(state="no_key")``.
    state: str = PUSH_READY

    def push_state(self) -> str:
        return self.state

    def send(self, target: Target, payload: Mapping[str, str], ttl: int, high_priority: bool) -> str:
        self.sent.append({"device_id": target.device_id, "kind": target.kind, "payload": dict(payload),
                          "ttl": ttl, "high_priority": high_priority})
        log.info(f"push (null) to {target.device_id}: {target.kind}")
        return OK


@dataclass
class ApnsKey:
    team_id: str
    key_id: str
    p8: str
    bundle_id: str
    environment: str = "production"


def apns_jwt(key: ApnsKey, *, now: Optional[float] = None) -> str:
    """The provider token: ES256 over ``{iss: team, iat}`` with ``kid`` = the key id."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

    header = b64u(json.dumps({"alg": "ES256", "kid": key.key_id}, separators=(",", ":")).encode())
    claims = b64u(json.dumps({"iss": key.team_id, "iat": int(now if now is not None else time.time())},
                             separators=(",", ":")).encode())
    private = serialization.load_pem_private_key(key.p8.encode("utf-8"), password=None)
    if not isinstance(private, ec.EllipticCurvePrivateKey):
        raise ValueError("the APNs key is not an EC key")
    der = private.sign(f"{header}.{claims}".encode("ascii"), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    return f"{header}.{claims}.{b64u(r.to_bytes(32, 'big') + s.to_bytes(32, 'big'))}"


def apns_request(key: ApnsKey, target: Target, payload: Mapping[str, str], ttl: int,
                 high_priority: bool, *, host: Optional[str] = None) -> tuple[str, dict[str, str], dict[str, Any]]:
    """The URL, headers and body of one APNs push (``host`` replaces Apple's for a test server)."""
    call = target.kind == "call"
    topic = key.bundle_id + (".voip" if call else "")
    if call:
        body: dict[str, Any] = {"aps": {}, **dict(payload)}
        push_type = "voip"
    elif target.kind == "silent":  # the Test push: wakes nothing, shows nothing
        body = {"aps": {"content-available": 1}, **dict(payload)}
        push_type = "background"
        high_priority = False  # Apple takes a background push at priority 5 only
    else:
        body = {"aps": {"alert": {"title": "HoldSpeak", "body": _alert_text(payload)},
                        "category": REPLY_CATEGORY, "mutable-content": 1, "sound": "default"}, **dict(payload)}
        push_type = "alert"
    headers = {
        "authorization": f"bearer {apns_jwt(key)}", "apns-topic": topic, "apns-push-type": push_type,
        "apns-priority": "10" if high_priority else "5",
        "apns-expiration": str(int(time.time()) + max(0, int(ttl))),
    }
    base = host or APNS_HOSTS.get(key.environment, APNS_HOSTS["production"])
    url = f"{base.rstrip('/')}/3/device/{target.token}"
    return url, headers, body


def _alert_text(payload: Mapping[str, str]) -> str:
    try:
        event = json.loads(payload.get("event") or "{}")
        return str(((event.get("data") or {}).get("message") or {}).get("text") or "A message from your desk")
    except ValueError:
        return "A message from your desk"


class ApnsPush:
    """APNs, token-based, with his key from the key store.

    ``host`` replaces Apple's host (a test's fake HTTP/2 server). The client
    speaks HTTP/2 only (``http1=False``): over TLS it offers only h2, and over
    plain ``http://`` it speaks h2 with prior knowledge."""

    name = "apns"

    def __init__(self, key: ApnsKey, *, host: Optional[str] = None) -> None:
        self._key = key
        self._host = host

    def push_state(self) -> str:
        return PUSH_READY if http2_ready() else PUSH_HTTP2_UNAVAILABLE

    def answer(self, target: Target, payload: Mapping[str, str], ttl: int,
               high_priority: bool) -> tuple[int, str]:
        """Apple's HTTP status and its ``reason`` (status 0: no answer came)."""
        if not http2_ready():  # APNs is HTTP/2 only
            log.warning("APNs push not sent: http2_unavailable (install httpx[http2])")
            return 0, PUSH_HTTP2_UNAVAILABLE
        import httpx

        url, headers, body = apns_request(self._key, target, payload, ttl, high_priority, host=self._host)
        try:
            with httpx.Client(http1=False, http2=True, timeout=10.0) as client:
                response = client.post(url, headers=headers, json=body)
        except Exception as exc:
            log.warning(f"APNs push failed: {exc}")
            return 0, str(exc)[:200]
        reason = ""
        if response.status_code != 200:
            try:
                reason = str((response.json() or {}).get("reason") or "")
            except ValueError:
                reason = response.text[:200]
        return response.status_code, reason

    def send(self, target: Target, payload: Mapping[str, str], ttl: int, high_priority: bool) -> str:
        status, reason = self.answer(target, payload, ttl, high_priority)
        if status == 200:
            return OK
        if status == 410 or (status == 400 and reason == "BadDeviceToken"):
            return UNREGISTERED
        if status:
            log.warning(f"APNs answered {status}: {reason}")
        return ERROR


def answer_code(status: int, reason: str) -> str:
    """The Test push's code for Apple's answer."""
    if status == 200:
        return TEST_ACCEPTED
    if status == 410 or (status == 400 and reason == "BadDeviceToken"):
        return TEST_STALE
    if status == 403:
        return TEST_REFUSED
    return TEST_FAILED


def read_saved_key() -> dict[str, Any]:
    """The saved key's fields as stored (``{}`` when none). Never on the wire."""
    from .devices import _store_for

    raw = _store_for(APNS_SLOT).get()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        log.warning("the saved APNs key is not readable")
        return {}
    return dict(data) if isinstance(data, dict) else {}


def saved_key_presence() -> dict[str, Any]:
    """What Settings ▸ Calls ▸ Phone ▸ Push reads: each field ``present`` or
    not, and the bundle id (not a secret). The key itself never leaves."""
    data = read_saved_key()
    return {"present": {name: bool(str(data.get(name) or "").strip()) for name in ("p8", "key_id", "team_id")},
            "bundle_id": str(data.get("bundle_id") or DEFAULT_BUNDLE_ID)}


def save_key_fields(fields: Mapping[str, Any]) -> dict[str, Any]:
    """Merge the given fields into the saved key (an empty value forgets
    one). A ``p8`` that is not an EC private key raises ``ValueError``."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    from .devices import _store_for

    data = read_saved_key()
    for name in APNS_FIELDS:
        if name not in fields:
            continue
        value = str(fields.get(name) or "").strip()
        if name == "p8" and value:
            try:
                private = serialization.load_pem_private_key(value.encode("utf-8"), password=None)
            except (ValueError, TypeError) as exc:
                raise ValueError("not_a_p8") from exc
            if not isinstance(private, ec.EllipticCurvePrivateKey):
                raise ValueError("not_a_p8")
            value += "\n"
        elif name in ("key_id", "team_id"):
            value = value.upper()
        if value:
            data[name] = value
        else:
            data.pop(name, None)
    data.setdefault("bundle_id", DEFAULT_BUNDLE_ID)
    _store_for(APNS_SLOT).put(json.dumps(data, separators=(",", ":")))
    return saved_key_presence()


def apns_from_keystore(*, host: Optional[str] = None) -> Optional[ApnsPush]:
    """His APNs key when he saved all of it (Settings ▸ Calls ▸ Phone); else
    None. ``host`` replaces Apple's (a rig's fake APNs server)."""
    data = read_saved_key()
    if not all(str(data.get(name) or "").strip() for name in APNS_FIELDS):
        return None
    try:
        return ApnsPush(ApnsKey(team_id=str(data["team_id"]), key_id=str(data["key_id"]), p8=str(data["p8"]),
                                bundle_id=str(data["bundle_id"]),
                                environment=str(data.get("environment") or "production")), host=host)
    except (KeyError, TypeError):
        log.warning("the saved APNs key is not readable")
        return None


__all__ = [
    "APNS_FIELDS", "APNS_SLOT", "DEFAULT_BUNDLE_ID", "TEST_ACCEPTED", "TEST_FAILED", "TEST_REFUSED", "TEST_STALE",
    "answer_code", "read_saved_key", "save_key_fields", "saved_key_presence",
    "ApnsKey", "ApnsPush", "ERROR", "MAX_EVENT_BYTES", "NullPush", "OK", "PUSH_HTTP2_UNAVAILABLE", "PUSH_NO_KEY",
    "PUSH_READY", "PUSH_STATES", "PUSH_UNREGISTERED", "PushProvider", "REPLY_CATEGORY", "Target", "UNREGISTERED",
    "apns_from_keystore", "apns_jwt", "apns_request", "build_payload", "http2_ready", "sign",
]
