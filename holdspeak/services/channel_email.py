"""PHILO-10-03: the email channel -- a provider interface (``design/send-lifecycle.md`` section 8).

The owner's ruling (Q1, 2026-09-28): "Not mail.app since it wouldn't work on
non-Macs. Let's have it declare an interface that would allow us to plug it
into major providers like sendgrid and so on."

* :class:`EmailProvider` -- ONE Protocol: ``name``, ``host``, ``limits``,
  ``serialize(message)``, ``preview(body)``, ``plan(body)``,
  ``auth_headers(key)`` (its own authentication, called only by the dispatch
  opener) and ``interpret(status, headers, body)`` (bounded response material:
  the status, the headers and a size-capped body, the key removed). :data:`EMAIL_PROVIDERS` -- ONE
  registry table. No discovery, no entry points. A second provider is one class
  and one row; no caller changes (Postmark, Mailgun, SES, SMTP: the BACKLOG).
* **One byte contract** (Codex Astra r3 condition 1): at prepare the message is
  serialized ONCE into the provider's exact request body; those bytes are the
  frozen payload and its digest. The preview is parsed back from them; dispatch
  transmits them; their digest is the ``payload_digest`` of the ``external.egress``
  child (data class ``email_message``), a CHILD of the send under the send's
  authenticated principal, through the send's broker (the network seam, section 6).
* **Key custody** (condition 2): the key lives in the OS keychain through
  ``keyring``, behind a native-only allow-list (macOS Keychain, Linux Secret
  Service, Windows Credential Manager); any other backend is refused
  ``email_key_store_not_native``. The key is never planning material: not in
  the payload, the :class:`GatedOperation`, the admission's material, the
  sender's args or kwargs. Only the dispatch opener (:func:`transmit`) reads it
  and sets the header. Redirects are NOT followed (a 3xx is UNKNOWN
  ``redirect_refused``). A transport exception leaves only a fixed code
  (:class:`EmailTransportError`), raised outside the handler so it carries no
  context.
* **SendGrid** and **Resend** (PHILO-10-07) are the implementations. SendGrid: ``202`` + ``X-Message-Id`` is SENT and
  its word is ACCEPTED BY SENDGRID (accepted for processing, never "delivered");
  FAILED only on a pinned whole-request rejection (a status on the list AND
  SendGrid's own ``errors`` answer); everything else is UNKNOWN. Resend: ``200`` +
  ``{"id"}`` is ACCEPTED BY RESEND, by the same rules. Text only. Each key has its
  own keychain slot per provider (:func:`key_slot`).

Tests replace :data:`KEY_STORE` (a memory store: never the real keychain) and
:data:`HTTPS_HANDLER` (a canned handler at the HTTPS edge: never the network).
"""
from __future__ import annotations

import http.client
import json
import re
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, replace
from email.headerregistry import Address
from email.utils import formataddr, parseaddr
from typing import Any, Callable, Mapping, Optional, Protocol
from urllib.parse import urlparse

from ..plugins.gated_connector import (
    ConnectorOperationRefused,
    GatedOperation,
    WriteConnectorManifest,
    build_gated_connector,
)
from .channel_contract import CHANNELS, ERROR_LIMIT, REDACTED, ChannelRefused, Document, Outcome, redact, sha256
from .errors import ValidationError

#: The data class every email egress declares.
DATA_CLASS = "email_message"

# ── the contract ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EmailMessage:
    """What the owner sends: text only in this phase."""

    from_email: str
    from_name: str
    to: tuple[str, ...]
    cc: tuple[str, ...]
    subject: str
    text: str


@dataclass(frozen=True)
class EmailLimits:
    """Refused by name before dispatch: ``payload_too_large:email``, ``email_recipients_too_many``."""

    max_bytes: int
    max_recipients: int


@dataclass(frozen=True)
class EmailRequest:
    """What the dispatch opener sends: the URL and the frozen bytes. Never a credential."""

    url: str
    body: bytes
    content_type: str = "application/json"


@dataclass(frozen=True)
class HttpAnswer:
    """The bounded response material a provider interprets (the key already removed from it)."""

    status: int
    #: Lower-cased names; at most ``_HEADER_COUNT`` headers of ``_HEADER_CHARS`` characters.
    headers: Mapping[str, str]
    #: The response body, at most ``_BODY_READ`` bytes.
    body: bytes = b""


class EmailProvider(Protocol):
    """One email provider: the byte contract, the plan and the outcome rules."""

    name: str
    host: str
    limits: EmailLimits

    def serialize(self, message: EmailMessage) -> bytes:
        """At PREPARE: the provider's exact request body (frozen with its digest)."""

    def preview(self, body: bytes) -> dict[str, Any]:
        """From, To, Cc, Subject and the text, parsed from the frozen bytes (never raw JSON)."""

    def plan(self, body: bytes) -> GatedOperation:
        """The outbound op: the frozen bytes unchanged, NO key."""

    def auth_headers(self, key: str) -> Mapping[str, str]:
        """The provider's own authentication headers; called ONLY by the dispatch opener."""

    def interpret(self, status: int, headers: Mapping[str, str], body: bytes) -> Outcome:
        """SENT with the provider's id, FAILED on a pinned whole-request rejection, else UNKNOWN."""


# ── the addresses ───────────────────────────────────────────────────────────

_ADDRESS = re.compile(r"^[^@\s<>\",]+@[^@\s<>\",]+\.[^@\s<>\",]+$")
_KEY_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,99}$")


def canonical_address(text: Any) -> str:
    """One address, parsed by ``email.utils.parseaddr`` and rendered again: ``Name <a@b.c>`` or ``a@b.c``."""
    name, addr = parseaddr(str(text or "").strip())
    if not _ADDRESS.fullmatch(addr or ""):
        raise ValidationError(f"Not an email address: {str(text or '')[:120]}", code="email_address_invalid")
    return formataddr((name, addr)) if name else addr


def _mailbox(text: str) -> dict[str, str]:
    name, addr = parseaddr(text)
    return {"email": addr, "name": name} if name else {"email": addr}


def _rendered(box: Mapping[str, Any]) -> str:
    name, addr = str(box.get("name") or ""), str(box.get("email") or "")
    return formataddr((name, addr)) if name else addr


# ── SendGrid: the first implementation ──────────────────────────────────────


class SendGridProvider:
    """``POST https://api.sendgrid.com/v3/mail/send`` (text/plain only).

    The pinned list (Codex Astra r3 finding 5; PROVISIONAL until the owner's
    real-account send pins the strings): a 4xx is FAILED only when SendGrid
    itself answered it (its ``errors`` array: the request was validated and
    rejected whole) and its status is on the list; ``403`` is split by its
    discriminator. Everything else is UNKNOWN with a named reason.
    """

    name = "sendgrid"
    host = "api.sendgrid.com"
    port = 443
    url = "https://api.sendgrid.com/v3/mail/send"
    #: PROVISIONAL (design section 3): 1 MB and 20 recipients, before the published limits are pinned.
    limits = EmailLimits(max_bytes=1_000_000, max_recipients=20)
    #: The face word for SENT: accepted for processing, never "delivered".
    WORD = "ACCEPTED BY SENDGRID"
    PINNED = {400: "invalid_request", 401: "api_key_invalid", 413: "payload_too_large", 429: "rate_limited"}
    #: The 403 discriminator: the from address is not a verified Sender Identity.
    SENDER_IDENTITY = "verified sender identity"

    def serialize(self, message: EmailMessage) -> bytes:
        personalization: dict[str, Any] = {"to": [_mailbox(a) for a in message.to]}
        if message.cc:
            personalization["cc"] = [_mailbox(a) for a in message.cc]
        sender = {"email": message.from_email, **({"name": message.from_name} if message.from_name else {})}
        body = {"personalizations": [personalization], "from": sender, "subject": message.subject,
                "content": [{"type": "text/plain", "value": message.text}]}
        return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def preview(self, body: bytes) -> dict[str, Any]:
        data = json.loads(bytes(body).decode("utf-8"))
        first = (data.get("personalizations") or [{}])[0]
        text = next((str(c.get("value") or "") for c in data.get("content") or []
                     if c.get("type") == "text/plain"), "")
        return {"from": _rendered(data.get("from") or {}), "to": [_rendered(b) for b in first.get("to") or []],
                "cc": [_rendered(b) for b in first.get("cc") or []], "subject": str(data.get("subject") or ""),
                "text": text}

    def plan(self, body: bytes) -> GatedOperation:
        return GatedOperation.outbound(self.host, self.port, request=EmailRequest(self.url, bytes(body)),
                                       data_classes=(DATA_CLASS,), payload_digest=sha256(bytes(body)))

    @staticmethod
    def auth_headers(key: str) -> dict[str, str]:
        return {"Authorization": "Bearer " + key}

    def interpret(self, status: int, headers: Mapping[str, str], body: bytes) -> Outcome:
        error_excerpt = sendgrid_errors(body) if status >= 400 else ()
        message_id = str(headers.get("x-message-id") or "").strip()
        excerpt = "; ".join(m for _f, m in error_excerpt if m)
        detail = {"error": excerpt} if excerpt else {}
        if status == 202:
            if not message_id:
                return Outcome("unknown", "accepted_without_message_id")
            return Outcome("sent", None, {"provider": self.name, "message_id": message_id, "word": self.WORD,
                                          "scope": "accepted for processing, not delivery"})
        if 300 <= status < 400:
            return Outcome("unknown", "redirect_refused", detail)
        if error_excerpt and status == 403:
            if any(self.SENDER_IDENTITY in m.lower() for _f, m in error_excerpt):
                return Outcome("failed", "sender_not_verified", detail)
            return Outcome("failed", "sendgrid_forbidden", detail)
        if error_excerpt and status in self.PINNED:
            return Outcome("failed", self.PINNED[status], detail)
        return Outcome("unknown", f"unpinned_{status}", detail)


def sendgrid_errors(raw: bytes) -> tuple[tuple[str, str], ...]:
    """SendGrid's own error answer: ``errors[].field`` / ``errors[].message``, bounded; () when absent."""
    try:
        data = json.loads(bytes(raw).decode("utf-8", errors="replace"))
    except ValueError:
        return ()
    found = data.get("errors") if isinstance(data, dict) else None
    if not isinstance(found, list):
        return ()
    return tuple((str(item.get("field") or "")[:80], str(item.get("message") or "")[:500])
                 for item in found[:10] if isinstance(item, dict))


# ── Resend: the second implementation (PHILO-10-07, the owner's closing-review ruling) ──


class ResendProvider:
    """``POST https://api.resend.com/emails`` (text only), the contract read from Resend's API reference
    (resend.com/docs/api-reference/emails/send-email and /errors, 2026-09-29).

    ``200`` + ``{"id": ...}`` in the JSON body is SENT; its word is ACCEPTED BY RESEND (accepted, never
    "delivered"). A 4xx is FAILED only when the body is Resend's whole, consistent error envelope (a JSON
    object: an integer ``statusCode`` EQUAL to the HTTP status, a string ``name``, a string ``message``;
    :func:`resend_error`) AND the (status, name) pair is on the pinned list. A pinned ``403
    validation_error`` whose message says the domain is not verified (or that a test sender sends only to
    its owner) is ``sender_not_verified``. Everything else -- an unknown name, a name of another status, a
    malformed or inconsistent envelope -- is UNKNOWN (Codex Astra r1 on #701: never a false "nothing sent").
    """

    name = "resend"
    host = "api.resend.com"
    port = 443
    url = "https://api.resend.com/emails"
    #: Resend takes 50 ``to`` addresses and 40 MB with attachments; HoldSpeak sends text only.
    limits = EmailLimits(max_bytes=1_000_000, max_recipients=50)
    #: The face word for SENT: accepted for processing, never "delivered".
    WORD = "ACCEPTED BY RESEND"
    #: Resend refuses a request with no User-Agent (403); this one names HoldSpeak.
    USER_AGENT = "HoldSpeak"
    PINNED = {
        (400, "validation_error"): "resend_invalid_request",
        (401, "missing_api_key"): "resend_key_invalid",
        (403, "invalid_api_key"): "resend_key_invalid",
        (403, "restricted_api_key"): "resend_key_invalid",
        (403, "suspended_api_key"): "resend_key_invalid",
        (403, "invalid_permission"): "resend_forbidden",
        (403, "validation_error"): "resend_forbidden",
        (422, "validation_error"): "resend_invalid_request",
        (422, "missing_required_field"): "resend_invalid_request",
        (422, "missing_required_parameter"): "resend_invalid_request",
        (422, "invalid_parameter"): "resend_invalid_request",
        (429, "rate_limit_exceeded"): "resend_rate_limited",
        (429, "daily_quota_exceeded"): "resend_quota_exceeded",
        (429, "monthly_quota_exceeded"): "resend_quota_exceeded",
    }
    #: The 403 discriminators: the from domain is not verified in Resend.
    SENDER_NOT_VERIFIED = ("domain is not verified", "only send testing emails to your own email address")

    def serialize(self, message: EmailMessage) -> bytes:
        # ``Name <address>`` with the name kept as typed (quoted when it must be; never RFC 2047 encoded).
        sender = (str(Address(display_name=message.from_name, addr_spec=message.from_email))
                  if message.from_name else message.from_email)
        body: dict[str, Any] = {"from": sender, "to": list(message.to)}
        if message.cc:
            body["cc"] = list(message.cc)
        body.update({"subject": message.subject, "text": message.text})
        return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    def preview(self, body: bytes) -> dict[str, Any]:
        data = json.loads(bytes(body).decode("utf-8"))
        return {"from": str(data.get("from") or ""), "to": [str(a) for a in data.get("to") or []],
                "cc": [str(a) for a in data.get("cc") or []], "subject": str(data.get("subject") or ""),
                "text": str(data.get("text") or "")}

    def plan(self, body: bytes) -> GatedOperation:
        return GatedOperation.outbound(self.host, self.port, request=EmailRequest(self.url, bytes(body)),
                                       data_classes=(DATA_CLASS,), payload_digest=sha256(bytes(body)))

    @classmethod
    def auth_headers(cls, key: str) -> dict[str, str]:
        return {"Authorization": "Bearer " + key, "User-Agent": cls.USER_AGENT}

    def interpret(self, status: int, headers: Mapping[str, str], body: bytes) -> Outcome:
        envelope = resend_error(body, status) if status >= 400 else None
        name, message = envelope or ("", "")
        detail = {"error": message} if message else {}
        if status == 200:
            message_id = resend_id(body)
            if not message_id:
                return Outcome("unknown", "accepted_without_message_id")
            return Outcome("sent", None, {"provider": self.name, "message_id": message_id, "word": self.WORD,
                                          "scope": "accepted for processing, not delivery"})
        if 300 <= status < 400:
            return Outcome("unknown", "redirect_refused", detail)
        if envelope is None or (status, name) not in self.PINNED:
            return Outcome("unknown", f"unpinned_{status}", detail)
        if (status, name) == (403, "validation_error") and any(m in message.lower() for m in self.SENDER_NOT_VERIFIED):
            return Outcome("failed", "sender_not_verified", detail)
        return Outcome("failed", self.PINNED[status, name], detail)


def resend_error(raw: bytes, status: int) -> Optional[tuple[str, str]]:
    """Resend's own error envelope, validated whole: ``(name, message)`` bounded, or None.

    A JSON object with an integer ``statusCode`` equal to *status* (a bool is not an integer), a string
    ``name`` and a string ``message``. Anything else is not Resend's answer, and it proves nothing.
    """
    try:
        data = json.loads(bytes(raw).decode("utf-8", errors="replace"))
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    answered, name, message = data.get("statusCode"), data.get("name"), data.get("message")
    if type(answered) is not int or answered != int(status) or not isinstance(name, str) or not isinstance(message, str):
        return None
    return name[:80], message[:500]


def resend_id(raw: bytes) -> str:
    """The id Resend gives an accepted email (``{"id": ...}``), bounded; "" when absent."""
    try:
        data = json.loads(bytes(raw).decode("utf-8", errors="replace"))
    except ValueError:
        return ""
    found = data.get("id") if isinstance(data, dict) else None
    return found.strip()[:200] if isinstance(found, str) else ""


#: THE registry table: provider name -> its implementation. One row per provider.
EMAIL_PROVIDERS: dict[str, EmailProvider] = {"sendgrid": SendGridProvider(), "resend": ResendProvider()}


def provider(name: Any) -> EmailProvider:
    found = EMAIL_PROVIDERS.get(str(name or ""))
    if found is None:
        raise ChannelRefused("email_provider_unknown", f"No email provider named {str(name or '')[:40]}", status=400)
    return found


# ── the key: custody on every platform ───────────────────────────────────


class EmailKeyError(RuntimeError):
    """A content-free key-custody failure: its code only."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class MemoryEmailKeyStore:
    """Test-only: the People ``MemoryKeyStore`` precedent. Never built by production wiring."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key_ref: str) -> str:
        value = self.values.get(key_ref)
        if not value:
            raise EmailKeyError("email_key_missing")
        return value

    def put(self, key_ref: str, key: str) -> None:
        self.values[key_ref] = str(key)


class NativeEmailKeyStore:
    """The OS keychain only (``holdspeak/people/keys.py`` allow-list, plus Windows); no file, no env."""

    service_name = "HoldSpeak Email"
    ALLOWED_BACKENDS = frozenset({
        "keyring.backends.macOS.Keyring",
        "keyring.backends.SecretService.Keyring",
        "keyring.backends.Windows.WinVaultKeyring",
    })
    CHAINER = "keyring.backends.chainer.ChainerBackend"

    def __init__(self, backend: Any = None) -> None:
        if backend is None:
            import keyring

            backend = keyring.get_keyring()
        self._backend = self.native(backend)

    @classmethod
    def native(cls, backend: Any) -> Any:
        """The backend itself when it is native; a chainer's first native backend; else refused."""
        name = _backend_name(backend)
        if name in cls.ALLOWED_BACKENDS:
            return backend
        if name == cls.CHAINER:
            for inner in getattr(backend, "backends", None) or ():
                if _backend_name(inner) in cls.ALLOWED_BACKENDS:
                    return inner
        raise EmailKeyError("email_key_store_not_native")

    def get(self, key_ref: str) -> str:
        try:
            value = self._backend.get_password(self.service_name, key_ref)
        except Exception:
            value, locked = None, True
        else:
            locked = False
        if locked:
            raise EmailKeyError("email_key_store_locked")
        if not value:
            raise EmailKeyError("email_key_missing")
        return str(value)

    def put(self, key_ref: str, key: str) -> None:
        try:
            self._backend.set_password(self.service_name, key_ref, str(key))
        except Exception:
            failed = True
        else:
            failed = False
        if failed:
            raise EmailKeyError("email_key_store_locked")


def _backend_name(backend: Any) -> str:
    kind = type(backend)
    return f"{kind.__module__}.{kind.__qualname__}"


#: The key store the hub uses (tests: a :class:`MemoryEmailKeyStore`).
KEY_STORE: Callable[[], Any] = NativeEmailKeyStore


def key_slot(provider_name: str, key_ref: str) -> str:
    """The keychain item for a provider's key: ``<provider>:<key_ref>`` (``:`` is never in a key_ref),
    so a SendGrid key and a Resend key never share a slot, and one provider's key never reaches the other."""
    return f"{provider_name}:{key_ref}"


def read_key(provider_name: str, key_ref: str) -> str:
    """The key, or a content-free :class:`EmailKeyError` (not native, missing, locked)."""
    return KEY_STORE().get(key_slot(provider_name, key_ref))


def save_key(provider_name: str, key_ref: str, key: str) -> None:
    KEY_STORE().put(key_slot(provider_name, key_ref), key)


def valid_key_ref(value: Any) -> str:
    text = str(value or "").strip()
    if not _KEY_REF.fullmatch(text):
        raise ValidationError("A key name is 1-100 letters, digits, '_', '.', '@' or '-'", code="email_key_ref_invalid")
    return text


# ── the dispatch opener: the one place the key is read ──────────────────────

class QuietHTTPSHandler(urllib.request.HTTPSHandler):
    """The credential-bearing HTTPS edge (Codex Astra r1 on #696, findings 1 and 2).

    * Wire debug is forced OFF for THIS transport only: ``http.client``'s
      ``debuglevel`` prints every header (the key) and the body; the global
      ``HTTPConnection.debuglevel`` is never read or changed here.
    * ``sent_any`` says whether a byte of the request may have left: it turns
      True just before the first write to a connected socket. A failure while
      it is False (DNS, a refused connection, the TLS handshake) proves nothing
      was sent; any failure after it is UNKNOWN.
    """

    def __init__(self) -> None:
        super().__init__(debuglevel=0)
        self.sent_any = False

    def https_open(self, req: Any) -> Any:
        edge = self

        class TrackedConnection(http.client.HTTPSConnection):
            debuglevel = 0

            def set_debuglevel(self, level: int) -> None:
                self.debuglevel = 0

            def send(self, data: Any) -> None:
                if self.sock is None and self.auto_open:
                    self.connect()
                edge.sent_any = True
                super().send(data)

        return self.do_open(TrackedConnection, req, context=self._context)


#: The HTTPS edge (tests: a canned handler, so no lane reaches the network).
HTTPS_HANDLER: Callable[[], urllib.request.BaseHandler] = QuietHTTPSHandler
#: Seconds for the whole exchange; past it the answer is UNKNOWN (``timeout``).
TIMEOUT = 30.0
_BODY_READ = 64 * 1024
_HEADER_COUNT = 50
_HEADER_CHARS = 500


class EmailTransportError(Exception):
    """A sanitized transport failure: a FIXED code, never the text of what failed.

    ``left``: the request may have left (UNKNOWN); ``False``: it is known it
    did not (FAILED: the key, a refused connection, DNS, TLS).
    """

    def __init__(self, code: str, *, left: bool) -> None:
        self.code = code
        self.left = left
        super().__init__(code)


class _RefuseRedirect(urllib.request.HTTPRedirectHandler):
    """Redirects are disabled: a 3xx is answered as itself, and no header reaches a second host."""

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def _opener() -> tuple[urllib.request.OpenerDirector, Any]:
    opener = urllib.request.OpenerDirector()
    edge = HTTPS_HANDLER()
    for handler in (edge, _RefuseRedirect(), urllib.request.HTTPDefaultErrorHandler(),
                    urllib.request.HTTPErrorProcessor()):
        opener.add_handler(handler)
    return opener, edge


def _classify(reason: Any) -> tuple[str, bool]:
    if isinstance(reason, ConnectionRefusedError):
        return "connect_refused", False
    if isinstance(reason, socket.gaierror):
        return "dns_failed", False
    if isinstance(reason, ssl.SSLError):
        # A TLS failure can come after body bytes were written: UNKNOWN unless
        # the edge proves nothing was sent (``sent_any`` False, in transmit).
        return "tls_failed", True
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "timeout", True
    return "transport_error", True


def _scrub(text: str, key: str) -> str:
    return text.replace(key, REDACTED) if key else text


def _answer(status: int, headers: Any, raw: bytes, key: str) -> HttpAnswer:
    """The bounded response material: the key removed from every header and from the body."""
    kept: dict[str, str] = {}
    for name, value in list(headers.items() if headers is not None else ())[:_HEADER_COUNT]:
        kept[str(name).lower()] = _scrub(str(value)[:_HEADER_CHARS], key)
    body = bytes(raw[:_BODY_READ]).replace(key.encode(), REDACTED.encode()) if key else bytes(raw[:_BODY_READ])
    return HttpAnswer(status=int(status), headers=kept, body=body)


def transmit(op: GatedOperation, key_ref: str, chosen: Any) -> HttpAnswer:
    """The dispatch opener: the key read HERE, the provider's own auth headers set HERE, the frozen
    bytes POSTed once, no redirect followed.

    Every failure leaves as :class:`EmailTransportError` with a fixed code,
    raised AFTER its handler so no exception text (a header, the key, the
    body) travels with it. A failure is FAILED (``left`` False) only when the
    edge proves no byte was written.
    """
    request: EmailRequest = op.request
    parsed = urlparse(request.url)
    host, port = op.address or ("", 0)
    if parsed.scheme != "https" or (parsed.hostname or "") != host or (parsed.port or 443) != port:
        raise EmailTransportError("url_not_admitted", left=False)
    code, left = "", False
    try:
        key = read_key(chosen.name, key_ref)
    except EmailKeyError as exc:
        code = exc.code
    except Exception:
        code = "email_key_store_locked"
    if code:
        raise EmailTransportError(code, left=False)
    wire = urllib.request.Request(request.url, data=bytes(request.body), method="POST",
                                  headers={"Content-Type": request.content_type})
    for name, value in dict(chosen.auth_headers(key)).items():
        wire.add_header(str(name), str(value))
    opener, edge = _opener()
    try:
        with opener.open(wire, timeout=TIMEOUT) as response:
            return _answer(response.status, response.headers, response.read(_BODY_READ), key)
    except urllib.error.HTTPError as exc:
        try:
            raw = exc.read(_BODY_READ)
        except Exception:
            raw = b""
        status, headers = exc.code, exc.headers
    except urllib.error.URLError as exc:
        code, left = _classify(exc.reason)
    except (TimeoutError, socket.timeout):
        code, left = "timeout", True
    except Exception:
        code, left = "transport_error", True
    if code:
        sent_any = getattr(edge, "sent_any", None)
        if sent_any is not None:  # the real edge knows whether a byte was written
            left = bool(sent_any)
        raise EmailTransportError(code, left=left)
    return _answer(status, headers, raw, key)


# ── the channel ───────────────────────────────────────────────────────────


def _manifest(chosen: EmailProvider) -> WriteConnectorManifest:
    return WriteConnectorManifest(connector_id=f"email-{chosen.name}", permission="network:outbound",
                                  label=f"Email ({chosen.name})", allowed_hosts=(chosen.host,))


def _authority(seam: Any) -> tuple[Any, str, Any]:
    """The send's authority for its egress child: its principal, its operation, its broker."""
    if seam is not None:
        return seam.principal, str(seam.parent_operation_id), seam.broker
    from . import project_kernel

    handle = project_kernel.current()
    if handle is None:
        raise RuntimeError("an email send runs only inside its admitted channel.send")
    return handle.principal, handle.operation_id, handle.broker


class EmailChannel:
    """The email channel: the destination freezes the sender, the provider and the key's NAME."""

    name = "email"
    #: Its bytes name the sender and the recipients: serialized per destination.
    addressed = True

    @staticmethod
    def badge(synced: bool) -> str:
        return "cloud"

    # -- save --------------------------------------------------------------

    def target_at_save(self, fields: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """``({provider, from_email, from_name, key_ref}, {to, cc})``, validated by name."""
        chosen_name = str(fields.get("provider") or "sendgrid")
        chosen = provider(chosen_name)
        from_email = canonical_address(fields.get("from_email"))
        if "<" in from_email:
            raise ValidationError("The sender is one bare address; its name goes in from_name",
                                  code="email_address_invalid")
        from_name = " ".join(str(fields.get("from_name") or "").split())
        if len(from_name) > 120:
            raise ValidationError("The sender's name is 120 characters at most", code="email_address_invalid")
        key_ref = valid_key_ref(fields.get("key_ref") or chosen_name)
        target = {"to": [canonical_address(a) for a in fields.get("to") or []],
                  "cc": [canonical_address(a) for a in fields.get("cc") or []]}
        self._recipients(target, chosen)
        return {"provider": chosen_name, "from_email": from_email, "from_name": from_name, "key_ref": key_ref}, target

    @staticmethod
    def _recipients(target: Mapping[str, Any], chosen: EmailProvider) -> None:
        everyone = [parseaddr(a)[1].lower() for a in [*(target.get("to") or []), *(target.get("cc") or [])]]
        if not target.get("to"):
            raise ChannelRefused("email_recipients_missing", "An email destination needs at least one To address",
                                 status=400)
        if len(everyone) > chosen.limits.max_recipients:
            raise ChannelRefused("email_recipients_too_many",
                                 f"{len(everyone)} recipients; {chosen.name} takes {chosen.limits.max_recipients}",
                                 status=400)
        if len(set(everyone)) != len(everyone):
            raise ChannelRefused("email_recipient_duplicate", "An address is listed twice", status=400)

    # -- the bytes ---------------------------------------------------------

    def serialize(self, document: Document, destination: Mapping[str, Any]) -> bytes:
        """The provider's exact request body for *document* to *destination* (the one byte contract)."""
        account = json.loads(destination.get("account_json") or "{}")
        target = json.loads(destination.get("target_json") or "{}")
        chosen = provider(account.get("provider"))
        self._recipients(target, chosen)
        body = chosen.serialize(EmailMessage(
            from_email=str(account.get("from_email") or ""), from_name=str(account.get("from_name") or ""),
            to=tuple(target.get("to") or ()), cc=tuple(target.get("cc") or ()), subject=document.title,
            text=document.body_md))
        if len(body) > chosen.limits.max_bytes:
            raise ChannelRefused("payload_too_large:email",
                                 f"The request is {len(body)} bytes; {chosen.name} takes {chosen.limits.max_bytes}",
                                 status=400)
        return body

    def preview(self, payload: bytes, account: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        """From, To, Cc, Subject and the text, parsed from the frozen request body."""
        return provider((account or {}).get("provider")).preview(bytes(payload))

    # -- before the boundary -------------------------------------------------

    def check_before_dispatch(self, target: Mapping[str, Any], account: Optional[Mapping[str, Any]] = None,
                              **_: Any) -> None:
        """The provider is known, the recipients fit, and the key store is native and holds the key."""
        account = account or {}
        chosen = provider(account.get("provider"))
        self._recipients(target, chosen)
        try:
            read_key(chosen.name, valid_key_ref(account.get("key_ref")))
        except EmailKeyError as exc:
            raise ChannelRefused(exc.code, f"The {chosen.name} key cannot be read: {exc.code}", status=400) from None
        return None

    # -- the effect (after the boundary committed) ------------------------------

    def dispatch(self, row: Mapping[str, Any], seam: Any = None) -> Outcome:
        """The frozen bytes, once, as an ``external.egress`` CHILD of the send."""
        account = json.loads(row["account_json"] or "{}")
        chosen = EMAIL_PROVIDERS.get(str(account.get("provider") or ""))
        if chosen is None:
            return Outcome("failed", "email_provider_unknown")
        body, digest = bytes(row["payload"]), str(row["payload_digest"])
        if sha256(body) != digest:
            return Outcome("failed", "payload_changed")
        op = chosen.plan(body)
        if (op.kind != "outbound" or not isinstance(op.request, EmailRequest) or bytes(op.request.body) != body):
            return Outcome("failed", "plan_refused")
        # The channel owns what the admission binds: the data class, the frozen digest, the journal refs.
        op = replace(op, data_classes=(DATA_CLASS,), payload_digest=digest, subject_refs=(
            f"destination:{row['destination_id']}", f"payload:sha256:{digest}"))
        principal, parent, broker = _authority(seam)
        key_ref = str(account.get("key_ref") or "")
        connector = build_gated_connector(
            _manifest(chosen), plan=lambda _proposal: op, interpret=lambda raw, _op: raw,
            opener=lambda planned: transmit(planned, key_ref, chosen), principal=principal,
            parent_operation_id=parent, broker=broker)
        try:
            answer = connector(None)
        except ConnectorOperationRefused as exc:
            # The kernel refused the child: nothing left (a known non-delivery).
            return Outcome("failed", "egress_refused", {"error": redact(exc.reason, body)})
        except EmailTransportError as exc:
            return Outcome("unknown" if exc.left else "failed", exc.code)
        outcome = chosen.interpret(answer.status, answer.headers, answer.body)
        if outcome.proof.get("error"):
            # Cut BEFORE the excerpt scan (story 02's GATE 1): the scan's cost is bounded by 240 characters.
            cut = " ".join(str(outcome.proof["error"]).split())[:ERROR_LIMIT]
            outcome = replace(outcome, proof={**outcome.proof, "error": redact(cut, body)})
        return outcome

    def recover(self, row: Mapping[str, Any]) -> Outcome:
        """A ``dispatching`` row found by a take-over: NEVER send again. HoldSpeak cannot know."""
        return Outcome("unknown", "interrupted")


CHANNELS["email"] = EmailChannel()

__all__ = [
    "DATA_CLASS", "EMAIL_PROVIDERS", "EmailChannel", "EmailKeyError", "EmailLimits", "EmailMessage",
    "EmailProvider", "EmailRequest", "EmailTransportError", "HttpAnswer", "MemoryEmailKeyStore",
    "NativeEmailKeyStore", "ResendProvider", "SendGridProvider", "canonical_address", "key_slot", "transmit",
]
