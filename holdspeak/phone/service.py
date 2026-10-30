"""``PhoneService``: the one service behind the Phone routes and the MCP tools.

Pair a phone, list and revoke it; messages both ways with replies, each
reply read once (``get_replies``, which waits instead of polling and says
that silence is never consent); calls with the gate (his press, unless the
Program may call and the level allows), the ring timer, missed → a message
and a Needs you row; Reach (the desk's own decision to message or call him,
:mod:`.phone_rules`, a ``phone.reach`` kernel operation each); the event log
and the ``phone_changed`` frame.

The transports, in order (design §5): the HoldSpeak app when a phone is
paired (it rings through a VoIP push and answers on its socket); else his
number through Calls (:mod:`.transport_number`). With both, the app rings
first and the number rings when the app does not answer.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import threading
import time
from datetime import timedelta
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from ..services.errors import ServiceError
from ..timestamps import parse_stamp, utc_iso, utc_now
from . import devices as devs
from . import phone_on
from .calls import FINAL, RERING_SECONDS, RING_SECONDS, RingTimers, can_move, missed_words
from .events import PhoneEvents
from .phone_rules import KINDS, Hold, level_of, reach as reach_rule
from .push import ERROR, PUSH_NO_KEY, PUSH_READY, PUSH_UNREGISTERED, NullPush, OK, UNREGISTERED, Target, build_payload
from .store import PhoneStore
from .transport_number import CALL_WAIT_SECONDS, NumberTransport

log = get_logger("phone.service")

OWNER = Principal(PrincipalKind.OWNER, "owner-phone")
FRAME = "phone_changed"

MAX_TEXT = 500
MAX_REASON = 200
MAX_CONTEXT = 4000
MAX_WAIT_S = 3600
#: A Program step's agent may send this many messages an hour.
STEP_MESSAGES_PER_HOUR = 3
#: The follow-up sweep (Normal: a call after 10 min without a reply).
SWEEP_SECONDS = 60.0
#: Reaches older than this are not followed up, and leave Needs you.
FOLLOW_HOURS = 24
#: The line of a message released when quiet hours end.
HELD_OVERNIGHT = "Held overnight: "

SILENCE = ("No reply yet. Silence is never consent: keep the safe default, and do not act as if he agreed. "
           "Wait again with wait_s, or carry on with the parts that need no answer.")


class PhoneRefused(ServiceError):
    """A named refusal; HTTP and MCP answer ``{error, code, detail}``."""

    def __init__(self, code: str, detail: str, status: int = 409) -> None:
        super().__init__(code, detail, context={"status": status})


def _is_owner(principal: Any) -> bool:
    return getattr(principal, "kind", None) is PrincipalKind.OWNER


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(8)}"


def _minutes_since(stamp: Any, now: Any) -> float:
    at = parse_stamp(stamp)
    return max(0.0, (now - at).total_seconds() / 60.0) if at is not None else 0.0


def _settings() -> Any:
    from ..config import Config

    return Config.load().calls


def message_wire(row: Mapping[str, Any]) -> dict[str, Any]:
    keys = ("id", "seq", "direction", "text", "reply_to", "created_at", "delivered_at", "read_at", "origin_ref",
            "program_step_id")
    return {key: row.get(key) for key in keys if row.get(key) is not None or key in ("id", "seq", "direction", "text",
                                                                                      "created_at")}


def call_wire(row: Mapping[str, Any]) -> dict[str, Any]:
    duration = None
    answered, ended = parse_stamp(row.get("answered_at")), parse_stamp(row.get("ended_at"))
    if answered is not None and ended is not None:
        duration = round((ended - answered).total_seconds(), 1)
    out = {
        "id": row["id"], "seq": int(row.get("seq") or 0), "direction": row["direction"],
        "reason": row.get("reason") or "", "urgent": bool(row.get("urgent")), "state": row["state"],
        "transport": row.get("transport") or "number", "created_at": row["created_at"],
        "answered_at": row.get("answered_at"), "ended_at": row.get("ended_at"), "end_reason": row.get("end_reason"),
        "duration_s": duration, "transcript_ref": row.get("transcript_ref"), "decision": row.get("decision"),
    }
    return {key: value for key, value in out.items() if value is not None or key in ("reason",)}


def device_wire(row: Mapping[str, Any], provider_state: Optional[str] = None) -> dict[str, Any]:
    """One device on the wire. ``push_state`` (RECIPE PH13) says why a push
    will not go: ``unregistered`` (no push token) first, else the provider's
    word (``ready`` | ``no_key`` | ``http2_unavailable``) when it is known."""
    has_push = bool(row.get("push_token"))
    out = {
        "id": row["id"], "name": row.get("name") or "", "platform": row.get("platform") or "",
        "state": row["state"], "has_push": has_push, "push_kind": row.get("push_kind"),
        "push_state": provider_state if has_push else PUSH_UNREGISTERED,
        "sip_identity": row.get("sip_identity"), "paired_at": row["paired_at"],
        "last_seen_at": row.get("last_seen_at"), "revoked_at": row.get("revoked_at"),
    }
    return {key: value for key, value in out.items() if value is not None or key in ("has_push",)}


class PhoneService:
    """The hub's phone (one per hub process)."""

    def __init__(
        self, db: Any, *, push: Any = None, number: Optional[NumberTransport] = None,
        broadcast: Optional[Callable[[str, Any], None]] = None, ring_seconds: float = RING_SECONDS,
        rering_seconds: float = RERING_SECONDS, kernel: Optional[Callable[[Mapping[str, Any]], Optional[str]]] = None,
        hub_urls: Optional[Callable[[], list[str]]] = None, settings: Optional[Callable[[], Any]] = None,
        apns_host: Optional[str] = None,
    ) -> None:
        self.db = db
        self.store = PhoneStore(db)
        self.events = PhoneEvents(self.store)
        self._push = push
        #: A push the caller gave (a rig) stays; else his saved key is read
        #: again after he changes it.
        self._push_given = push is not None
        #: Replaces Apple's host (a rig's fake APNs server).
        self._apns_host = apns_host
        self.number = number or NumberTransport()
        self._bus = broadcast
        self._kernel = kernel
        self._hub_urls = hub_urls or (lambda: [])
        self._settings = settings or _settings
        self.timers = RingTimers(on_timeout=self._ring_timeout, on_rering=self._rering,
                                 ring_seconds=ring_seconds, rering_seconds=rering_seconds)
        self._contexts: dict[str, str] = {}
        self._answers: dict[str, dict[str, Any]] = {}
        self._waiters: dict[str, threading.Event] = {}
        self._fell_back: set[str] = set()
        self._lock = threading.RLock()
        self._replies = threading.Condition()
        self._sweeper: Optional[threading.Thread] = None
        self._stop = threading.Event()
        #: origin prefix -> "is the thing still waiting on him?" (the sweep
        #: does not ask again about a thing he settled elsewhere).
        self._open_checks: dict[str, Callable[[str], bool]] = {}

    # ── wiring ────────────────────────────────────────────────────────

    def push(self) -> Any:
        if self._push is None:
            from .push import apns_from_keystore

            try:
                self._push = apns_from_keystore(host=self._apns_host) or NullPush(state=PUSH_NO_KEY)
            except Exception as exc:
                log.info(f"phone push: no APNs key ({exc})")
                self._push = NullPush(state=PUSH_NO_KEY)
        return self._push

    def push_state(self) -> str:
        """The provider's push word (``ready`` | ``no_key`` | ``http2_unavailable``)."""
        try:
            word = getattr(self.push(), "push_state", None)
            return str(word()) if callable(word) else PUSH_READY
        except Exception as exc:
            log.info(f"phone push state: {exc}")
            return PUSH_NO_KEY

    def device_wire(self, row: Mapping[str, Any]) -> dict[str, Any]:
        return device_wire(row, self.push_state() if row.get("push_token") else None)

    # ── his Apple push key (Settings ▸ Calls ▸ Phone ▸ Push) ─────────

    def push_key(self, principal: Any) -> dict[str, Any]:
        """Where each part of his key is (``present``), never the key."""
        if not _is_owner(principal):
            raise PhoneRefused("owner_principal_required", "Only the owner reads the push key.", 403)
        from .push import saved_key_presence

        return {**saved_key_presence(), "push_state": self.push_state()}

    def save_push_key(self, principal: Any, body: Mapping[str, Any]) -> dict[str, Any]:
        """Keep the given parts (``p8``, ``key_id``, ``team_id``, ``bundle_id``)
        in the key store; the answer says ``present``, never the key."""
        if not _is_owner(principal):
            raise PhoneRefused("owner_principal_required", "Only the owner saves the push key.", 403)
        from .push import APNS_FIELDS, save_key_fields

        fields = {name: body[name] for name in APNS_FIELDS if name in body}
        if not fields:
            raise PhoneRefused("nothing_to_save", "Send p8, key_id, team_id or bundle_id.", 400)
        try:
            save_key_fields(fields)
        except ValueError:
            raise PhoneRefused("not_a_p8", "This is not an Apple push key. Paste the whole .p8 file.", 400) from None
        except Exception as exc:
            log.warning(f"phone push key not saved: {exc}")
            raise PhoneRefused("keystore_unavailable", "The keystore did not take the key. Nothing changed.", 503) from exc
        if not self._push_given:
            self._push = None  # the next push reads the saved key again
        return self.push_key(principal)

    def test_push(self, principal: Any) -> dict[str, Any]:
        """One silent push to the newest paired phone; Apple's answer as a code
        (``accepted`` | ``stale`` | ``refused`` | ``failed``) with its status."""
        if not _is_owner(principal):
            raise PhoneRefused("owner_principal_required", "Only the owner sends a test push.", 403)
        from .push import answer_code

        provider = self.push()
        if not callable(getattr(provider, "answer", None)):
            raise PhoneRefused(PUSH_NO_KEY, "Save your Apple push key, its Key ID and Team ID first.", 409)
        rows = sorted((row for row in self.paired() if row.get("push_token")),
                      key=lambda row: str(row.get("paired_at") or ""), reverse=True)
        if not rows:
            raise PhoneRefused("no_push_token", "No paired phone sent a push token. Open the app once.", 409)
        row = rows[0]
        event = {"seq": 0, "type": "push.test", "ts": self._stamp(), "data": {}}
        payload = build_payload(self.hub(), devs.push_secret(self._secret(), row["jwt_kid"]), event)
        status, reason = provider.answer(Target(row["id"], str(row["push_token"]), "silent"), payload, 60, False)
        return {"answer": answer_code(status, reason), "status": status, "reason": reason, "device_id": row["id"]}

    def _secret(self) -> bytes:
        return devs.hub_secret()

    def hub(self) -> str:
        return devs.hub_id(self._secret())

    def _frame(self, kind: str, ident: str, state: str) -> None:
        bus = self._bus
        if bus is None:
            try:
                from ..runtime import composition

                bus = composition.broadcast()
            except Exception:
                bus = None
        if bus is None:
            return
        broadcast = bus
        try:
            broadcast("phone_changed", {"kind": kind, "id": ident, "state": state})
        except Exception as exc:
            log.debug(f"phone frame dropped: {exc}")

    def _now(self) -> Any:
        return utc_now()

    def _stamp(self) -> str:
        return utc_iso(self._now())

    # ── pairing and devices ───────────────────────────────────────────

    def pair_token(self, principal: Any, *, hub_urls: Optional[list[str]] = None) -> dict[str, Any]:
        """A 10-minute token and the QR that carries it (owner only). The QR
        names the address he pressed Pair on (over Tailscale, his phone's way
        in)."""
        if not _is_owner(principal):
            raise PhoneRefused("owner_principal_required", "Only the owner pairs a phone.", 403)
        token = "pt_" + secrets.token_urlsafe(24)
        now = self._now()
        expires = utc_iso(now + timedelta(seconds=devs.PAIR_SECONDS))
        self.store.save_device({"id": _new_id("dev"), "name": "", "platform": "", "jwt_kid": devs.token_hash(token),
                                "state": "pairing", "paired_at": utc_iso(now)})
        urls = [url for url in (hub_urls if hub_urls is not None else self._hub_urls()) if url]
        return {"token": token, "qr_payload": devs.qr_payload(token=token, hub_urls=urls,
                                                              expires_at=expires, hub=self.hub()),
                "qr_png_base64": None, "expires_at": expires}

    def redeem(self, body: Mapping[str, Any]) -> dict[str, Any]:
        """The app redeems a pairing token once; its device token."""
        from pydantic import ValidationError as PydanticError

        from .contract import PairRequest

        try:
            request = PairRequest.model_validate(dict(body or {}))
        except PydanticError as exc:
            raise PhoneRefused("pair_invalid", f"The pairing request is not valid: {exc.errors()[0]['msg']}.", 400)
        with self._lock:
            row = self.store.device_by_kid(devs.token_hash(request.pair_token))
            created = parse_stamp((row or {}).get("paired_at"))
            fresh = created is not None and (self._now() - created).total_seconds() <= devs.PAIR_SECONDS
            if row is None or row["state"] != "pairing" or not fresh:
                raise PhoneRefused("invalid_pairing_token",
                                   "The pairing code is not valid, has expired or was used. Press Pair again.", 401)
            kid = "k_" + secrets.token_hex(12)
            now = self._stamp()
            row.update({"name": request.name.strip(), "platform": request.platform, "push_token": request.push_token,
                        "push_kind": request.push_kind or ("apns" if request.push_token else None),
                        "sip_identity": request.sip_identity, "jwt_kid": kid, "state": "paired",
                        "paired_at": now, "last_seen_at": now})
            self.store.save_device(row)
        self.events.append("device.paired", {"device": self.device_wire(row)})
        self._frame("device", row["id"], "paired")
        secret = self._secret()
        return {"device_id": row["id"], "device_jwt": devs.issue_jwt(secret, row["id"], kid),
                "push_secret": devs.push_secret(secret, kid), "hub_id": devs.hub_id(secret)}

    def authenticate(self, token: str) -> Optional[dict[str, Any]]:
        """The paired device a token belongs to, or None. The row is read on
        every request, so a revoke refuses the token at once."""
        claims = devs.read_jwt(self._secret(), token)
        if claims is None:
            return None
        row = self.store.get_device(claims["sub"])
        if row is None or row["state"] != "paired" or row["jwt_kid"] != claims["kid"]:
            return None
        seen = parse_stamp(row.get("last_seen_at"))
        if seen is None or (self._now() - seen).total_seconds() > 30:
            self.store.touch_device(row["id"], self._stamp())
        return row

    def devices(self, principal: Any) -> dict[str, Any]:
        rows = [row for row in self.store.list_devices() if row["state"] != "pairing"]
        return {"devices": [self.device_wire(row) for row in rows]}

    def paired(self) -> list[dict[str, Any]]:
        return [row for row in self.store.list_devices() if row["state"] == "paired"]

    def revoke(self, principal: Any, device_id: str) -> dict[str, Any]:
        if not _is_owner(principal):
            raise PhoneRefused("owner_principal_required", "Only the owner revokes a phone.", 403)
        with self._lock:
            row = self.store.get_device(device_id)
            if row is None or row["state"] == "pairing":
                raise PhoneRefused("device_unknown", "There is no such phone.", 404)
            if row["state"] != "revoked":
                row.update({"state": "revoked", "revoked_at": self._stamp(), "push_token": None})
                self.store.save_device(row)
                self.events.append("device.revoked", {"device_id": device_id, "at": row["revoked_at"]})
        closed = self.events.close_device(device_id)
        self._frame("device", device_id, "revoked")
        return {"device": self.device_wire(row), "sockets_closed": closed}

    # ── push ──────────────────────────────────────────────────────────

    def _push_event(self, event: Mapping[str, Any], kind: str, ttl: int, *, high: bool = True) -> bool:
        """Push one event to every paired phone with a push token; True when one took it."""
        if not phone_on():
            return False
        took = False
        secret = self._secret()
        for row in self.paired():
            token = str(row.get("push_token") or "")
            if not token:
                continue
            payload = build_payload(self.hub(), devs.push_secret(secret, row["jwt_kid"]), event)
            try:
                result = self.push().send(Target(row["id"], token, kind), payload, ttl, high)
            except Exception as exc:
                log.warning(f"phone push failed: {exc}")
                result = ERROR
            if result == OK:
                took = True
            elif result == UNREGISTERED:
                row["push_token"] = None
                self.store.save_device(row)
        return took

    def _quiet(self, at: Any = None) -> bool:
        """Inside quiet hours at ``at`` (default now, from :meth:`_now`)?"""
        from ..cadence.scheduler import in_quiet_hours
        from ..services.heartbeat_service import read_quiet_hours

        start, end = read_quiet_hours(self.db)
        moment = at if at is not None else self._now()
        return in_quiet_hours(moment.astimezone(), start, end)

    # ── messages ──────────────────────────────────────────────────────

    def send_message(
        self, principal: Any, text: str, reply_to: Optional[str] = None, *, device: Optional[Mapping[str, Any]] = None,
        origin_ref: Optional[str] = None, program_step_id: Optional[str] = None, queue: bool = False,
    ) -> dict[str, Any]:
        """One line to his phone (or, from his phone, to the desk)."""
        from ..redaction import redact_secrets

        text = " ".join(str(text or "").split()) if "\n" not in str(text or "") else str(text or "").strip()
        if not text:
            raise PhoneRefused("text_required", "Write the message first.", 400)
        if len(text) > MAX_TEXT:
            raise PhoneRefused("text_too_long", f"A message is at most {MAX_TEXT} characters. Make it shorter.", 400)
        if redact_secrets(text) != text:
            raise PhoneRefused("secret_refused", "The message has a secret in it. Nothing was sent. Take it out.", 400)
        parent = None
        if reply_to:
            parent = self.store.get_message(str(reply_to))
            if parent is None:
                raise PhoneRefused("reply_unknown", "There is no such message to answer.", 404)
        if device is not None:
            direction = "from_phone"
        elif _is_owner(principal) and parent is not None and parent["direction"] == "to_phone":
            direction, origin_ref = "from_phone", origin_ref or "desk"  # he answers at the desk
        else:
            direction = "to_phone"
        if direction == "to_phone" and program_step_id and not _is_owner(principal):
            since = utc_iso(self._now() - timedelta(hours=1))
            if self.store.count_step_messages_since(str(program_step_id), since) >= STEP_MESSAGES_PER_HOUR:
                raise PhoneRefused("too_many_messages",
                                   f"A step may send {STEP_MESSAGES_PER_HOUR} messages an hour. Nothing was sent. "
                                   "Wait for his reply with phone.get_replies.", 429)
        with self._lock:
            row = {"id": _new_id("msg"), "seq": 0, "direction": direction, "text": text,
                   "reply_to": parent["id"] if parent else None, "created_at": self._stamp(),
                   "delivered_at": None, "read_at": None, "origin_ref": origin_ref,
                   "program_step_id": program_step_id}
            self.store.save_message(row)
            event = self.events.append("message.new", lambda seq: {"message": message_wire({**row, "seq": seq})})
            row["seq"] = event["seq"]
            if direction == "to_phone":
                live = any(self.events.subscribers(device["id"]) for device in self.paired())
                pushed = False
                if not (queue or self._quiet()):
                    pushed = self._push_event(event, "message", 28 * 24 * 3600)
                if pushed or live:
                    row["delivered_at"] = self._stamp()
            self.store.save_message(row)
        if row["delivered_at"]:
            self.events.append("message.delivered", {"msg_id": row["id"], "at": row["delivered_at"]})
        if direction == "from_phone":
            with self._replies:
                self._replies.notify_all()
        self._frame("message", row["id"], "delivered" if row["delivered_at"] else "sent")
        return message_wire(row)

    def send_from_desk(self, text: str, *, origin_ref: Optional[str] = None,
                       program_step_id: Optional[str] = None, queue: bool = False) -> dict[str, Any]:
        """The desk itself writes to his phone (a Reach, a later answer)."""
        return self.send_message(OWNER, str(text or "")[:MAX_TEXT], origin_ref=origin_ref,
                                 program_step_id=program_step_id, queue=queue)

    def messages(self, *, after_seq: int = 0) -> dict[str, Any]:
        return {"messages": [message_wire(row) for row in self.store.list_messages(after_seq=after_seq)],
                "last_seq": self.events.last_seq()}

    def get_replies(self, wait_s: Any = 0) -> dict[str, Any]:
        """His new replies, each once; waits up to ``wait_s`` for one."""
        try:
            wait = max(0.0, min(float(wait_s or 0), float(MAX_WAIT_S)))
        except (TypeError, ValueError):
            raise PhoneRefused("wait_invalid", "wait_s is a number of seconds, 0 to 3600.", 400)
        deadline = time.monotonic() + wait
        while True:
            with self._lock:
                rows = self.store.unread_replies()
                for row in rows:
                    row["read_at"] = self._stamp()
                    self.store.save_message(row)
            if rows:
                for row in rows:
                    self.events.append("message.read", {"msg_id": row["id"], "at": row["read_at"], "by": "desk"})
                    self._frame("message", row["id"], "read")
                return {"replies": [message_wire(row) for row in rows]}
            left = deadline - time.monotonic()
            if left <= 0:
                return {"replies": [], "note": SILENCE}
            with self._replies:
                self._replies.wait(timeout=min(left, 5.0))

    def mark_read(self, message_id: str, *, by: str) -> dict[str, Any]:
        with self._lock:
            row = self.store.get_message(message_id)
            if row is None:
                raise PhoneRefused("message_unknown", "There is no such message.", 404)
            if not row.get("read_at"):
                row["read_at"] = self._stamp()
                self.store.save_message(row)
                self.events.append("message.read", {"msg_id": row["id"], "at": row["read_at"], "by": by})
        self._frame("message", row["id"], "read")
        return message_wire(row)

    def let_wait(self, principal: Any, message_id: str) -> dict[str, Any]:
        """He lets an ask wait: it leaves Needs you; the thread keeps it."""
        if not _is_owner(principal):
            raise PhoneRefused("owner_principal_required", "Only the owner decides that.", 403)
        row = self.store.get_message(message_id)
        if row is None:
            raise PhoneRefused("message_unknown", "There is no such message.", 404)
        self.events.append("message.wait", {"msg_id": row["id"], "at": self._stamp(), "by": "desk"})
        self._frame("message", row["id"], "waiting")
        return message_wire(row)

    # ── calls ─────────────────────────────────────────────────────────

    def _transport(self) -> str:
        if self.paired():
            return "app"
        ready, why = self.number.available()
        if ready:
            return "number"
        raise PhoneRefused(
            "no_line", f"No call: no phone is paired and {why}. Nothing was sent. "
            "Pair a phone, or add your line in Settings ▸ Calls.")

    def _may_call(self, program_step_id: Optional[str]) -> tuple[bool, str]:
        """An agent's call goes out without his press only when its Program
        (or step) may call and the level is not Secure."""
        if not program_step_id:
            return False, ""
        try:
            from ..services.program_service import default_program_service

            programs = default_program_service(self.db)
            step = programs.store.get_step(str(program_step_id))
            program = programs.store.get_program(step["program_id"]) if step else None
        except Exception:
            return False, ""
        if not step or not program:
            return False, ""
        level = level_of(program.get("control"))
        return bool(step.get("may_call") or program.get("may_call")) and level != "secure", level

    def call(
        self, principal: Any, *, reason: str, context: str = "", urgent: bool = False, wait: bool = False,
        program_step_id: Optional[str] = None, origin_ref: Optional[str] = None, gate: bool = True,
    ) -> dict[str, Any]:
        """The phone rings. EGRESS: the owner's press, or an agent's call that
        waits in Needs you unless its Program may call and the level allows."""
        from ..redaction import redact_secrets
        from ..services.program_rules import is_core

        reason = " ".join(str(reason or "").split())
        context = str(context or "").strip()
        if not reason:
            raise PhoneRefused("reason_required", "Say in one sentence why the phone rings.", 400)
        if len(reason) > MAX_REASON or len(context) > MAX_CONTEXT:
            raise PhoneRefused("too_long", f"The reason is at most {MAX_REASON} characters and the context "
                                           f"at most {MAX_CONTEXT}.", 400)
        if redact_secrets(reason) != reason or redact_secrets(context) != context:
            raise PhoneRefused("secret_refused", "The call has a secret in it. Nothing was sent. Take it out.", 400)
        if self.store.open_calls():
            raise PhoneRefused("busy", "A call is on now. Send a message instead.")
        owner = _is_owner(principal)
        if urgent and not owner and not is_core({"finding_text": f"{reason} {context}"}).startswith("a finding"):
            urgent = False  # urgent is for security and data loss, or when he asked for a call
        transport = self._transport()
        allowed = owner or not gate
        if not allowed:
            allowed, _level = self._may_call(program_step_id)
        now = self._stamp()
        with self._lock:
            row = {"id": _new_id("pcall"), "seq": 0, "direction": "to_phone", "reason": reason,
                   "context_digest": "sha256:" + hashlib.sha256(context.encode("utf-8")).hexdigest()[:16],
                   "urgent": bool(urgent), "state": "ringing" if allowed else "held", "created_at": now,
                   "transport": transport, "decision": None}
            self._contexts[row["id"]] = context
            self._waiters[row["id"]] = threading.Event()
            self.store.save_call(row)
        if not allowed:
            event = self.events.append("call.held", lambda seq: {"call": call_wire({**row, "seq": seq})})
            row["seq"] = event["seq"]
            self.store.save_call(row)
            self._frame("call", row["id"], "held")
            answer = {"call_id": row["id"], "state": "held",
                      "words": "The call waits for his press in Needs you. Send a message meanwhile."}
            return answer
        self._ring(row)
        if not wait:
            return {"call_id": row["id"], "state": "ringing"}
        return self.wait_answer(row["id"])

    def wait_answer(self, call_id: str, seconds: float = CALL_WAIT_SECONDS) -> dict[str, Any]:
        waiter = self._waiters.get(call_id)
        if waiter is not None:
            waiter.wait(seconds)
        return self.answer(call_id)

    def answer(self, call_id: str) -> dict[str, Any]:
        row = self.store.get_call(call_id)
        if row is None:
            raise PhoneRefused("call_unknown", "There is no such call.", 404)
        extra = self._answers.get(call_id, {})
        wire = call_wire(row)
        return {"call_id": call_id, "state": row["state"], "transcript": list(extra.get("transcript") or []),
                "end_reason": row.get("end_reason"), "duration_s": wire.get("duration_s"),
                "decision": row.get("decision")}

    def ring_held(self, principal: Any, call_id: str) -> dict[str, Any]:
        """His press on a held call (Call now)."""
        if not _is_owner(principal):
            raise PhoneRefused("owner_principal_required", "Only the owner lets a held call ring.", 403)
        with self._lock:
            row = self._call(call_id)
            if not can_move(row["state"], "ringing") or row["state"] != "held":
                raise PhoneRefused("invalid_state", f"The call is {row['state']}.")
            if self.store.open_calls():
                raise PhoneRefused("busy", "A call is on now.")
            row["transport"] = self._transport()
            row["state"] = "ringing"
            self.store.save_call(row)
            self._waiters.setdefault(call_id, threading.Event())
        self._ring(row)
        return call_wire(self._call(call_id))

    def call_again(self, principal: Any, call_id: str) -> dict[str, Any]:
        """A missed call, again (his press): a new call with the same reason."""
        if not _is_owner(principal):
            raise PhoneRefused("owner_principal_required", "Only the owner calls again.", 403)
        old = self._call(call_id)
        made = self.call(principal, reason=old.get("reason") or "Your desk called", urgent=bool(old.get("urgent")),
                         context=self._contexts.get(call_id, ""))
        self.events.append("message.wait", {"msg_id": f"call:{call_id}", "at": self._stamp(), "by": "desk"})
        return made

    def _call(self, call_id: str) -> dict[str, Any]:
        row = self.store.get_call(call_id)
        if row is None:
            raise PhoneRefused("call_unknown", "There is no such call.", 404)
        return row

    def _save_call_event(self, row: dict[str, Any], type_: str, data: Mapping[str, Any]) -> None:
        event = self.events.append(type_, data)
        row["seq"] = event["seq"]
        self.store.save_call(row)
        self._frame("call", row["id"], row["state"])

    def _ring(self, row: dict[str, Any]) -> None:
        if row["transport"] == "app":
            seconds = self.timers.ring_seconds
            expires = utc_iso(self._now() + timedelta(seconds=seconds))
            event = self.events.append("call.invite", lambda seq: {"call": call_wire({**row, "seq": seq}),
                                                                   "expires_at": expires})
            row["seq"] = event["seq"]
            self.store.save_call(row)
            self._frame("call", row["id"], "ringing")
            self.timers.ringing(row["id"])
            self._push_event(event, "call", max(1, int(seconds)))
            return
        self._ring_number(row)

    def _ring_number(self, row: dict[str, Any]) -> None:
        row["transport"] = "number"
        row["state"] = "ringing"
        event = self.events.append("call.invite", lambda seq: {"call": call_wire({**row, "seq": seq})})
        row["seq"] = event["seq"]
        self.store.save_call(row)
        self._frame("call", row["id"], "ringing")
        call_id = row["id"]

        def on_end(info: dict[str, Any]) -> None:
            self._number_ended(call_id, info)

        def on_failed(word: str, detail: str) -> None:
            self._number_failed(call_id, word, detail)

        def run() -> None:
            placed = self.number.place(reason=row["reason"], context=self._contexts.get(call_id, ""),
                                       on_end=on_end, on_failed=on_failed)
            if placed:
                with self._lock:
                    current = self._call(call_id)
                    current["calls_turn_id"] = placed
                    if current["state"] == "ringing":
                        current["state"] = "answered"
                        current["answered_at"] = self._stamp()
                        self._save_call_event(current, "call.answered",
                                              {"call_id": call_id, "at": current["answered_at"], "by": "phone"})

        threading.Thread(target=run, name=f"phone-call-{call_id}", daemon=True).start()

    def _number_ended(self, call_id: str, info: Mapping[str, Any]) -> None:
        with self._lock:
            row = self._call(call_id)
            row["calls_turn_id"] = info.get("calls_turn_id") or row.get("calls_turn_id")
            duration = info.get("duration_s")
            now = self._now()
            if not row.get("answered_at"):
                row["answered_at"] = utc_iso(now - timedelta(seconds=float(duration or 0)))
            row.update({"state": "ended", "ended_at": utc_iso(now),
                        "end_reason": str(info.get("end_reason") or "ended"),
                        "transcript_ref": info.get("note_ref") or (f"call:{row['calls_turn_id']}"
                                                                   if row.get("calls_turn_id") else None),
                        "decision": info.get("decision")})
            self._answers[call_id] = {"transcript": list(info.get("transcript") or [])}
            self._save_call_event(row, "call.ended", {"call_id": call_id, "at": row["ended_at"], "by": "phone",
                                                      "end_reason": row["end_reason"], "duration_s": duration})
        self._finish(call_id)

    def _number_failed(self, call_id: str, word: str, detail: str) -> None:
        with self._lock:
            row = self._call(call_id)
            if word in {"no_answer", "rejected", "busy"}:
                row["state"] = "missed"
                self._save_call_event(row, "call.missed", {"call_id": call_id, "at": self._stamp(), "by": "timeout",
                                                           "rings": 1})
            else:
                row.update({"state": "ended", "ended_at": self._stamp(), "end_reason": word or "failed"})
                self._save_call_event(row, "call.ended", {"call_id": call_id, "at": row["ended_at"],
                                                          "end_reason": row["end_reason"]})
                log.info(f"phone call on the number did not go out: {word} {detail}")
        if word in {"no_answer", "rejected", "busy"}:
            self._missed_final(call_id)
        else:
            self._finish(call_id)

    def _ring_timeout(self, call_id: str) -> None:
        with self._lock:
            row = self.store.get_call(call_id)
            if row is None or row["state"] != "ringing" or row["transport"] != "app":
                return
            rings = self.timers.rings(call_id)
            row["state"] = "missed"
            self._save_call_event(row, "call.missed", {"call_id": call_id, "at": self._stamp(), "by": "timeout",
                                                       "rings": rings})
        self._push_event({"type": "call.missed", "data": {"call_id": call_id}}, "call", 30)
        if row.get("urgent") and rings < 2:
            self.timers.rering_later(call_id)
            return
        self._missed_final(call_id)

    def _rering(self, call_id: str) -> None:
        with self._lock:
            row = self.store.get_call(call_id)
            if row is None or row["state"] != "missed":
                return
            row["state"] = "ringing"
            self.store.save_call(row)
        self._ring(row)

    def _missed_final(self, call_id: str) -> None:
        """The app did not answer: the number rings when it can; else the
        missed call is one message with its reason, and a Needs you row."""
        row = self._call(call_id)
        ready, _why = self.number.available()
        if row["transport"] == "app" and ready and call_id not in self._fell_back:
            self._fell_back.add(call_id)
            with self._lock:
                row["state"] = "ringing"
                self.store.save_call(row)
            self._ring_number(row)
            return
        try:
            self.send_from_desk(missed_words(row), origin_ref=f"phone_call:{call_id}")
        except Exception as exc:
            log.warning(f"the missed-call message was not written: {exc}")
        self._finish(call_id)

    def _finish(self, call_id: str) -> None:
        self.timers.stop(call_id)
        waiter = self._waiters.get(call_id)
        if waiter is not None:
            waiter.set()

    def accept(self, call_id: str, *, device: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        with self._lock:
            row = self._call(call_id)
            if row["state"] != "ringing":
                raise PhoneRefused("invalid_state", f"The call is {row['state']}.")
            self.timers.stop(call_id)
            row["state"], row["answered_at"] = "answered", self._stamp()
            self._save_call_event(row, "call.answered", {"call_id": call_id, "at": row["answered_at"],
                                                         "by": "phone" if device else "desk"})
        return call_wire(row)

    def decline(self, call_id: str, *, device: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        with self._lock:
            row = self._call(call_id)
            if row["state"] == "held":
                row.update({"state": "ended", "ended_at": self._stamp(), "end_reason": "let_wait"})
                self._save_call_event(row, "call.ended", {"call_id": call_id, "at": row["ended_at"], "by": "desk",
                                                          "end_reason": "let_wait"})
            elif row["state"] == "ringing":
                row.update({"state": "declined", "ended_at": self._stamp(), "end_reason": "declined"})
                self._save_call_event(row, "call.declined", {"call_id": call_id, "at": row["ended_at"],
                                                             "by": "phone" if device else "desk"})
            else:
                raise PhoneRefused("invalid_state", f"The call is {row['state']}.")
        self._finish(call_id)
        return call_wire(row)

    def end(self, call_id: str, *, device: Optional[Mapping[str, Any]] = None,
            transcript: Optional[list[dict[str, str]]] = None, decision: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        with self._lock:
            row = self._call(call_id)
            if row["state"] in FINAL or row["state"] == "missed":
                raise PhoneRefused("invalid_state", f"The call is {row['state']}.")
            if row["state"] == "held":
                return self.decline(call_id)
            row.update({"state": "ended", "ended_at": self._stamp(),
                        "end_reason": "hung_up" if row.get("answered_at") else "canceled"})
            if decision is not None:
                row["decision"] = dict(decision)
            if transcript:
                self._answers[call_id] = {"transcript": list(transcript)}
            wire = call_wire(row)
            self._save_call_event(row, "call.ended", {"call_id": call_id, "at": row["ended_at"],
                                                      "by": "phone" if device else "desk",
                                                      "end_reason": row["end_reason"],
                                                      "duration_s": wire.get("duration_s")})
        self._finish(call_id)
        return call_wire(row)

    def get_call(self, call_id: str) -> dict[str, Any]:
        row = self._call(call_id)
        return {**call_wire(row), "transcript": list(self._answers.get(call_id, {}).get("transcript") or [])}

    def calls(self) -> dict[str, Any]:
        return {"calls": [call_wire(row) for row in self.store.list_calls()]}

    # ── reach (design §6) ─────────────────────────────────────────────

    def _reaches(self, origin_ref: str) -> list[dict[str, Any]]:
        since = utc_iso(self._now() - timedelta(hours=FOLLOW_HOURS))
        return [event for event in self.store.events_of_type("reach", since)
                if (event["data"] or {}).get("origin_ref") == origin_ref]

    def _facts(self, origin_ref: Optional[str], kind: str, extra: Mapping[str, Any]) -> dict[str, Any]:
        cfg = self._settings()
        facts: dict[str, Any] = {"quiet": self._quiet(), "urgent_dnd": bool(getattr(cfg, "phone_urgent_dnd", False)),
                                 "word": (getattr(cfg, "phone_reach", {}) or {}).get(kind),
                                 "call_active": bool(self.store.open_calls())}
        try:
            from ..desk_presence import seconds_since_seen

            seen = seconds_since_seen()
            facts["away"] = seen is None or seen >= 30 * 60
        except Exception:
            facts["away"] = True
        if origin_ref:
            earlier = self._reaches(origin_ref)
            if earlier:
                last = earlier[-1]
                facts["recent_minutes"] = _minutes_since(last["ts"], self._now())
                message_id = next((e["data"].get("msg_id") for e in reversed(earlier) if e["data"].get("msg_id")), None)
                if message_id:
                    facts["messaged"] = True
                    message = self.store.get_message(message_id) or {}
                    # From when it reached him: a message held overnight
                    # waits from the morning release, not from 23:30.
                    facts["minutes_without_reply"] = _minutes_since(
                        message.get("delivered_at") or message.get("created_at"), self._now())
                    facts["replied"] = bool(self.store.replies_to(message_id))
        facts.update({key: value for key, value in dict(extra or {}).items() if value is not None})
        return facts

    def reach(
        self, kind: str, *, level: Any, text: str, reason: Optional[str] = None, context: Optional[str] = None,
        origin_ref: Optional[str] = None, may_call: bool = False, program_step_id: Optional[str] = None,
        facts: Optional[Mapping[str, Any]] = None,
    ) -> dict[str, Any]:
        """The desk decides to reach him (§6): a message, a call, or a hold;
        one ``phone.reach`` kernel operation and one ``reach`` event."""
        if kind not in KINDS:
            raise PhoneRefused("reach_kind_unknown", f"There is no reach rule for {kind!r}.", 400)
        level = level_of(level)
        all_facts = self._facts(origin_ref, kind, {**dict(facts or {}), "may_call": bool(may_call)})
        outcome = reach_rule(level, kind, all_facts)
        result: dict[str, Any] = {"kind": kind, "level": level, "rule": outcome.rule, "origin_ref": origin_ref,
                                  "may_call": bool(may_call), "reason": (reason or text)[:MAX_REASON]}
        if isinstance(outcome, Hold):
            result.update({"held": True, "why": outcome.reason, "queued": outcome.queued, "channel": "message"})
            if not outcome.queued:
                return {**result, "line": f"Did not reach you: {outcome.reason}"}
            # quiet hours: the message is written, its push waits
            message = self.send_from_desk(text, origin_ref=origin_ref, program_step_id=program_step_id, queue=True)
            result["msg_id"] = message["id"]
            line = "Reached you: a message, held for the morning"
        elif outcome.channel == "call":
            try:
                made = self.call(OWNER, reason=reason or text[:MAX_REASON], context=context or text,
                                 urgent=outcome.urgent, origin_ref=origin_ref, program_step_id=program_step_id,
                                 gate=False)
                result.update({"held": False, "channel": "call", "urgent": outcome.urgent, "call_id": made["call_id"]})
                line = "Reached you: a call" + (", urgent" if outcome.urgent else "")
            except PhoneRefused as exc:
                message = self.send_from_desk(text, origin_ref=origin_ref, program_step_id=program_step_id)
                result.update({"held": False, "channel": "message", "msg_id": message["id"],
                               "rule": f"{outcome.rule}; no call ({exc.code}), a message instead"})
                line = "Reached you: a message (no call went out)"
        else:
            message = self.send_from_desk(text, origin_ref=origin_ref, program_step_id=program_step_id)
            result.update({"held": False, "channel": "message", "msg_id": message["id"]})
            line = "Reached you: a message"
        self._record_reach(result)
        return {**result, "line": line}

    def _record_reach(self, result: Mapping[str, Any]) -> None:
        data = {key: result.get(key) for key in ("kind", "channel", "rule", "level", "urgent", "may_call", "queued",
                                                 "reason", "origin_ref", "msg_id", "call_id")}
        data = {key: value for key, value in data.items() if value is not None}
        data.setdefault("urgent", False)
        data["queued"] = bool(data.get("queued"))
        self.events.append("reach", data)
        try:
            if self._kernel is not None:
                self._kernel(data)
            else:
                from ..kernel.phone_ops import record_reach

                record_reach(self.db, data)
        except Exception as exc:
            log.warning(f"phone.reach kernel receipt not written: {exc}")

    def sweep(self) -> list[dict[str, Any]]:
        """The follow-up: a reach message with no reply is asked again by the
        rules (Normal: a call after 10 minutes when the Program may call)."""
        done: list[dict[str, Any]] = []
        since = utc_iso(self._now() - timedelta(hours=FOLLOW_HOURS))
        seen: set[str] = set()
        for event in reversed(self.store.events_of_type("reach", since)):
            data = event["data"] or {}
            origin = str(data.get("origin_ref") or "")
            if not origin or origin in seen:
                continue
            seen.add(origin)
            if data.get("channel") != "message" or data.get("kind") not in ("core_question", "agent_question"):
                continue
            message_id = data.get("msg_id")
            if not message_id or self.store.replies_to(str(message_id)):
                continue
            message = self.store.get_message(str(message_id))
            if message is None or not self._still_open(origin):
                continue
            facts = self._facts(origin, str(data["kind"]), {"may_call": bool(data.get("may_call"))})
            outcome = reach_rule(data.get("level"), str(data["kind"]), facts)
            if isinstance(outcome, Hold) or outcome.channel != "call":
                continue
            done.append(self.reach(str(data["kind"]), level=data.get("level"), text=message["text"],
                                   reason=data.get("reason"), origin_ref=origin, may_call=bool(data.get("may_call")),
                                   program_step_id=message.get("program_step_id")))
        return done

    def open_check(self, prefix: str, check: Callable[[str], bool]) -> None:
        """Name how the sweep reads whether a thing (an ``origin_ref`` that
        starts with ``prefix``) still waits on him."""
        self._open_checks[str(prefix)] = check

    def _still_open(self, origin: str) -> bool:
        for prefix, check in list(self._open_checks.items()):
            if origin.startswith(prefix):
                try:
                    return bool(check(origin))
                except Exception as exc:
                    log.debug(f"phone open check failed for {origin}: {exc}")
                    return True
        return True

    # ── the morning release (PH14) ────────────────────────────────────

    def release_held(self) -> list[dict[str, Any]]:
        """Quiet hours ended: each message written in them and not yet on
        his phone goes out now, in order, one push each, its line "Held
        overnight: …", and one ``message.delivered`` event each."""
        from ..cadence.scheduler import in_quiet_hours
        from ..services.heartbeat_service import read_quiet_hours

        if not phone_on() or self._quiet():
            return []
        start, end = read_quiet_hours(self.db)
        if start == end or not any(row.get("push_token") for row in self.paired()):
            return []
        since = utc_iso(self._now() - timedelta(hours=FOLLOW_HOURS))
        held = []
        for row in self.store.recent_messages(limit=200):
            if row["direction"] != "to_phone" or row.get("delivered_at") or str(row["created_at"]) < since:
                continue
            made = parse_stamp(row["created_at"])
            if made is None or not in_quiet_hours(made.astimezone(), start, end) or self.store.replies_to(row["id"]):
                continue
            held.append(row)
        released: list[dict[str, Any]] = []
        for row in sorted(held, key=lambda item: (int(item.get("seq") or 0), str(item["id"]))):
            wire = {**message_wire(row), "text": f"{HELD_OVERNIGHT}{row['text']}"[:MAX_TEXT]}
            event = {"seq": row["seq"], "type": "message.new", "ts": self._stamp(), "data": {"message": wire}}
            if not self._push_event(event, "message", 28 * 24 * 3600):
                continue
            with self._lock:
                row["delivered_at"] = self._stamp()
                self.store.save_message(row)
            self.events.append("message.delivered", {"msg_id": row["id"], "at": row["delivered_at"]})
            self._frame("message", row["id"], "delivered")
            released.append(message_wire(row))
        return released

    def tick(self) -> None:
        """One minute of the phone's runner: the morning release, then the
        follow-up (a message released now waits its 10 minutes from now)."""
        try:
            self.release_held()
        except Exception as exc:
            log.warning(f"phone morning release failed: {exc}")
        try:
            self.sweep()
        except Exception as exc:
            log.warning(f"phone sweep failed: {exc}")

    def start(self) -> None:
        """The follow-up sweep and the morning release, once a minute, off the loop."""
        if not phone_on() or (self._sweeper is not None and self._sweeper.is_alive()):
            return
        self._stop.clear()

        def loop() -> None:
            while not self._stop.wait(SWEEP_SECONDS):
                self.tick()

        self._sweeper = threading.Thread(target=loop, name="phone-sweep", daemon=True)
        self._sweeper.start()

    def stop(self) -> None:
        self._stop.set()
        self.timers.stop_all()

    # ── status and Needs you ──────────────────────────────────────────

    def status(self, principal: Any = None) -> dict[str, Any]:
        from ..services.heartbeat_service import read_quiet_hours

        cfg = self._settings()
        start, end = read_quiet_hours(self.db)
        ready, why = self.number.available()
        level = _desk_level()
        reach = {}
        for kind in KINDS:
            own = (getattr(cfg, "phone_reach", {}) or {}).get(kind)
            from .phone_rules import table

            word, _rule = table(level, kind, {"may_call": True})
            reach[kind] = {"word": own or ("call" if word.startswith("call") else word), "own": bool(own),
                           "level_word": "call" if word.startswith("call") else word}
        today = utc_iso(self._now() - timedelta(hours=24))
        reaches = self.store.events_of_type("reach", today)
        calls = [row for row in self.store.list_calls() if str(row["created_at"]) >= today]
        return {
            "on": phone_on(), "devices": [self.device_wire(row) for row in self.paired()],
            "line": {"number_set": bool(self.number.number()), "ready": ready,
                     "words": "Ready" if ready else (why[:1].upper() + why[1:])},
            "quiet_hours": {"start": start, "end": end, "now": self._quiet()},
            "urgent_dnd": bool(getattr(cfg, "phone_urgent_dnd", False)), "level": level, "reach": reach,
            "last_reach": reaches[-1] if reaches else None,
            "today": {"reaches": len(reaches), "calls": len(calls),
                      "answered": sum(1 for row in calls if row.get("answered_at"))},
            "last_seq": self.events.last_seq(),
        }

    def needs_you_items(self) -> list[dict[str, Any]]:
        """What waits on him: asks with no reply, missed calls, held calls,
        messages that never reached a phone (``needs_you_membership.phone_items``)."""
        if not phone_on():
            return []
        now = self._now()
        since = utc_iso(now - timedelta(hours=FOLLOW_HOURS))
        waited = {str((e["data"] or {}).get("msg_id")) for e in self.store.events_of_type("message.wait", since)}
        asked = {str((e["data"] or {}).get("msg_id")) for e in self.store.events_of_type("reach", since)
                 if (e["data"] or {}).get("kind") in ("core_question", "agent_question")}
        items: list[dict[str, Any]] = []
        missed_msgs: set[str] = set()
        for row in self.store.list_calls(limit=100):
            if str(row["created_at"]) < since or f"call:{row['id']}" in waited:
                continue
            if row["state"] == "held":
                items.append({"kind": "held_call", "id": row["id"], "call_id": row["id"], "reason": row["reason"],
                              "since": row["created_at"], "minutes": int(_minutes_since(row["created_at"], now))})
        paired = bool(self.paired())
        for row in self.store.recent_messages(limit=200):
            if row["direction"] != "to_phone" or str(row["created_at"]) < since or row["id"] in waited:
                continue
            if self.store.replies_to(row["id"]):
                continue
            minutes = int(_minutes_since(row["created_at"], now))
            origin = str(row.get("origin_ref") or "")
            if origin.startswith("phone_call:"):
                call = self.store.get_call(origin.split(":", 1)[1])
                if call is None or f"call:{call['id']}" in waited:
                    continue
                missed_msgs.add(row["id"])
                items.append({"kind": "missed_call", "id": call["id"], "call_id": call["id"], "msg_id": row["id"],
                              "reason": call["reason"], "since": row["created_at"], "minutes": minutes})
            elif row["id"] in asked or row["text"].rstrip().endswith("?"):
                items.append({"kind": "asked", "id": row["id"], "msg_id": row["id"], "text": row["text"],
                              "since": row["created_at"], "minutes": minutes, "reached": paired})
            elif not paired and not row.get("delivered_at"):
                items.append({"kind": "waiting", "id": row["id"], "msg_id": row["id"], "text": row["text"],
                              "since": row["created_at"], "minutes": minutes})
        return items


def _desk_level() -> str:
    try:
        from ..config import Config

        return level_of(Config.load().control_mode)
    except Exception:
        return "normal"


_DEFAULT: Optional[PhoneService] = None
_DEFAULT_DB: Any = None
_DEFAULT_LOCK = threading.Lock()


def default_phone_service(db: Any = None) -> PhoneService:
    """The process's one Phone service over the hub database."""
    global _DEFAULT, _DEFAULT_DB
    if db is None:
        from ..db import get_database
        from ..runtime import composition

        db = composition.db_or(get_database)
    with _DEFAULT_LOCK:
        if _DEFAULT is None or _DEFAULT_DB is not db:
            if _DEFAULT is not None:
                _DEFAULT.stop()
            _DEFAULT = PhoneService(db, apns_host=os.environ.get("HOLDSPEAK_APNS_HOST") or None)
            _DEFAULT_DB = db
        return _DEFAULT


__all__ = ["FRAME", "PhoneRefused", "PhoneService", "SILENCE", "call_wire", "default_phone_service", "device_wire",
           "message_wire"]
