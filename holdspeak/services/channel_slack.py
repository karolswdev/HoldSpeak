"""PHILO-11-02: the Slack incoming-webhook channel.

Slack is one declared transport.  The complete webhook URL is held in the
native keyring and is read for local checks and dispatch.  The operation plan
contains the frozen request bytes, the exact Slack host, the payload digest,
and no credential.  The HTTP edge is injectable for the recording HTTPS rig;
the default edge never follows redirects and does not print request material.
"""
from __future__ import annotations

import http.client
import json
import re
import secrets
import socket
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional
from urllib.parse import urlparse

from ..plugins.gated_connector import (
    ConnectorOperationRefused,
    GatedOperation,
    WriteConnectorManifest,
    build_gated_connector,
)
from .channel_contract import CHANNELS, ChannelRefused, Document, Outcome, redact, sha256
from .errors import ValidationError

DATA_CLASS = "slack_message"
HOST = "hooks.slack.com"
PORT = 443
MAX_TEXT_CHARACTERS = 39_000
TIMEOUT = 30.0
_BODY_READ = 64 * 1024
_HEADER_COUNT = 50
_HEADER_CHARS = 500
_KEY_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,99}$")


@dataclass(frozen=True)
class SlackRequest:
    """The request plan.  It deliberately has no URL: the URL is the secret."""

    body: bytes
    content_type: str = "application/json"


@dataclass(frozen=True)
class HttpAnswer:
    """Bounded response material after the webhook URL has been scrubbed."""

    status: int
    headers: Mapping[str, str]
    body: bytes = b""


class SlackKeyError(RuntimeError):
    """Content-free key custody failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class MemorySlackKeyStore:
    """Test-only in-memory key store; production wiring uses the native keyring."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def get(self, key_ref: str) -> str:
        value = self.values.get(str(key_ref))
        if not value:
            raise SlackKeyError("slack_webhook_missing")
        return value

    def put(self, key_ref: str, key: str) -> None:
        self.values[str(key_ref)] = str(key)


class NativeSlackKeyStore:
    """The OS keychain only: macOS Keychain, Secret Service, or Windows vault."""

    service_name = "HoldSpeak Slack"
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
        name = _backend_name(backend)
        if name in cls.ALLOWED_BACKENDS:
            return backend
        if name == cls.CHAINER:
            for inner in getattr(backend, "backends", None) or ():
                if _backend_name(inner) in cls.ALLOWED_BACKENDS:
                    return inner
        raise SlackKeyError("slack_key_store_not_native")

    def get(self, key_ref: str) -> str:
        try:
            value = self._backend.get_password(self.service_name, str(key_ref))
        except Exception:
            value, locked = None, True
        else:
            locked = False
        if locked:
            raise SlackKeyError("slack_key_store_locked")
        if not value:
            raise SlackKeyError("slack_webhook_missing")
        return str(value)

    def put(self, key_ref: str, key: str) -> None:
        try:
            self._backend.set_password(self.service_name, str(key_ref), str(key))
        except Exception:
            raise SlackKeyError("slack_key_store_locked") from None


def default_key_store() -> Any:
    """The keychain; a file store when ``HOLDSPEAK_CHANNEL_KEYSTORE_FILE`` is set (a rig hub)."""
    from .channel_key_file import FileChannelKeyStore, channel_keystore_path

    path = channel_keystore_path()
    if path is not None:
        return FileChannelKeyStore(path, NativeSlackKeyStore.service_name, SlackKeyError, "slack_webhook_missing",
                                   "slack_key_store_locked")
    return NativeSlackKeyStore()


KEY_STORE: Callable[[], Any] = default_key_store


def _backend_name(backend: Any) -> str:
    kind = type(backend)
    return f"{kind.__module__}.{kind.__qualname__}"


def key_slot(key_ref: str) -> str:
    """The stable, nonsecret slot name required by the destination account."""

    return f"slack:{key_ref}"


def valid_key_ref(value: Any) -> str:
    text = str(value or "").strip()
    if not _KEY_REF.fullmatch(text):
        raise ValidationError(
            "A Slack key name is 1-100 letters, digits, '_', '.', '@' or '-'",
            code="slack_key_ref_invalid",
        )
    return text


def mint_key_ref() -> str:
    """Mint a new slot for every webhook save, without a credential fingerprint."""

    return "slack_" + secrets.token_hex(16)


def validate_webhook_url(value: Any) -> str:
    """Admit one strict Slack incoming-webhook URL without echoing its secret."""

    text = str(value or "").strip()
    try:
        parsed = urlparse(text)
        port = parsed.port
    except ValueError:
        port = None
        parsed = None
    valid = bool(
        parsed
        and parsed.scheme.lower() == "https"
        and (parsed.hostname or "").lower() == HOST
        and (port is None or port == PORT)
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
        and parsed.path.startswith("/services/")
        and len(parsed.path) > len("/services/")
    )
    if not valid:
        raise ChannelRefused("slack_webhook_invalid", "The Slack webhook must use hooks.slack.com:443", status=400)
    return text


def save_key(key_ref: str, webhook_url: str) -> None:
    """Validate and save the whole URL in its Slack keychain slot."""

    ref = valid_key_ref(key_ref)
    url = validate_webhook_url(webhook_url)
    try:
        KEY_STORE().put(key_slot(ref), url)
    except SlackKeyError:
        raise
    except Exception:
        raise SlackKeyError("slack_key_store_locked") from None


def read_key(key_ref: str) -> str:
    """Read the URL for local validation or the credential-bearing dispatch edge."""

    ref = valid_key_ref(key_ref)
    try:
        return validate_webhook_url(KEY_STORE().get(key_slot(ref)))
    except SlackKeyError:
        raise
    except ChannelRefused:
        raise SlackKeyError("slack_webhook_invalid") from None
    except Exception:
        raise SlackKeyError("slack_key_store_locked") from None


def markdown_to_slack(text: Any) -> str:
    """Convert the supported Markdown constructs to Slack text deterministically."""

    link = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
    bold = re.compile(r"\*\*([^*\n]+)\*\*|__([^_\n]+)__")
    lines: list[str] = []
    for source in str(text or "").splitlines(keepends=True):
        ending = "\n" if source.endswith("\n") else ""
        line = source[:-1] if ending else source
        heading = re.match(r"^\s*#{1,6}\s+(.*?)\s*$", line)
        if heading:
            line = f"*{heading.group(1)}*"
        line = link.sub(lambda match: f"<{match.group(2)}|{match.group(1)}>", line)
        line = bold.sub(lambda match: f"*{match.group(1) or match.group(2)}*", line)
        lines.append(line + ending)
    return "".join(lines)


def _payload_text(payload: bytes) -> str:
    try:
        data = json.loads(bytes(payload).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ChannelRefused("payload_changed", "The Slack payload is not valid JSON", status=400) from None
    if not isinstance(data, dict) or set(data) != {"text"} or not isinstance(data.get("text"), str):
        raise ChannelRefused("payload_changed", "The Slack payload is not a text message", status=400)
    return data["text"]


def _manifest() -> WriteConnectorManifest:
    return WriteConnectorManifest(
        connector_id="channel_slack",
        permission="network:outbound",
        label="Slack incoming webhook (Send)",
        allowed_hosts=(HOST,),
    )


class QuietHTTPSHandler(urllib.request.HTTPSHandler):
    """HTTPS edge with no request debug output and a sent-byte transition."""

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


HTTPS_HANDLER: Callable[[], urllib.request.BaseHandler] = QuietHTTPSHandler


class SlackTransportError(Exception):
    """Sanitized transport failure; ``left`` says whether bytes may have left."""

    def __init__(self, code: str, *, left: bool) -> None:
        self.code = code
        self.left = left
        super().__init__(code)


class _RefuseRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        return None


def _opener() -> tuple[urllib.request.OpenerDirector, Any]:
    opener = urllib.request.OpenerDirector()
    edge = HTTPS_HANDLER()
    for handler in (edge, _RefuseRedirect(), urllib.request.HTTPDefaultErrorHandler(), urllib.request.HTTPErrorProcessor()):
        opener.add_handler(handler)
    return opener, edge


def _classify(reason: Any) -> tuple[str, bool]:
    if isinstance(reason, ConnectionRefusedError):
        return "connect_refused", False
    if isinstance(reason, socket.gaierror):
        return "dns_failed", False
    if isinstance(reason, ssl.SSLError):
        return "tls_failed", True
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "timeout", True
    return "transport_error", True


def _scrub(text: str, secret: str) -> str:
    return text.replace(secret, "[redacted]") if secret else text


def _answer(status: int, headers: Any, raw: bytes, secret: str) -> HttpAnswer:
    kept: dict[str, str] = {}
    for name, value in list(headers.items() if headers is not None else ())[:_HEADER_COUNT]:
        kept[str(name).lower()] = _scrub(str(value)[:_HEADER_CHARS], secret)
    body = bytes(raw[:_BODY_READ])
    if secret:
        body = body.replace(secret.encode(), b"[redacted]")
    return HttpAnswer(status=int(status), headers=kept, body=body)


def transmit(op: GatedOperation, key_ref: str) -> HttpAnswer:
    """Read the URL and perform exactly one POST at the credential-bearing edge."""

    request = op.request
    if not isinstance(request, SlackRequest):
        raise SlackTransportError("plan_refused", left=False)
    try:
        webhook_url = read_key(key_ref)
    except SlackKeyError as exc:
        raise SlackTransportError(exc.code, left=False) from None
    parsed = urlparse(webhook_url)
    if (parsed.hostname or "").lower() != HOST or (parsed.port is not None and parsed.port != PORT):
        raise SlackTransportError("slack_webhook_invalid", left=False)
    wire = urllib.request.Request(
        webhook_url,
        data=bytes(request.body),
        method="POST",
        headers={"Content-Type": request.content_type, "User-Agent": "HoldSpeak"},
    )
    opener, edge = _opener()
    code, left = "", False
    try:
        with opener.open(wire, timeout=TIMEOUT) as response:
            return _answer(response.status, response.headers, response.read(_BODY_READ), webhook_url)
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
        if sent_any is not None:
            left = bool(sent_any)
        raise SlackTransportError(code, left=left)
    return _answer(status, headers, raw, webhook_url)


def _authority(seam: Any) -> tuple[Any, str, Any]:
    if seam is not None:
        return seam.principal, str(seam.parent_operation_id), seam.broker
    from . import project_kernel

    handle = project_kernel.current()
    if handle is None:
        raise RuntimeError("a Slack send runs only inside its admitted channel.send")
    return handle.principal, handle.operation_id, handle.broker


class SlackChannel:
    """One incoming-webhook Slack channel on the Phase 10 lifecycle."""

    name = "slack"
    addressed = False
    host = HOST
    port = PORT
    max_text_characters = MAX_TEXT_CHARACTERS

    @staticmethod
    def badge(synced: bool) -> str:
        return "cloud"

    @staticmethod
    def validate_webhook(value: Any) -> str:
        return validate_webhook_url(value)

    def target_at_save(self, fields: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        label = " ".join(str(fields.get("channel_label") or "").split())
        if not label or len(label) > 120:
            raise ValidationError("A Slack destination needs a channel label (120 characters at most)",
                                  code="slack_channel_label_invalid")
        key_ref = valid_key_ref(fields.get("key_ref") or mint_key_ref())
        return {"key_ref": key_ref}, {"channel_label": label}

    def save_key(self, key_ref: str, webhook_url: str) -> None:
        save_key(key_ref, webhook_url)

    @staticmethod
    def read_key(key_ref: str) -> str:
        return read_key(key_ref)

    def serialize(self, document: Document) -> bytes:
        text = markdown_to_slack(document.body_md)
        if len(text) > MAX_TEXT_CHARACTERS:
            raise ChannelRefused(
                "payload_too_large:slack",
                f"The Slack text is {len(text)} characters; Slack takes {MAX_TEXT_CHARACTERS}",
                status=400,
                size=len(text),
                limit=MAX_TEXT_CHARACTERS,
            )
        return json.dumps({"text": text}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def preview(payload: bytes, account: Optional[Mapping[str, Any]] = None) -> dict[str, Any]:
        return {"text": _payload_text(bytes(payload))}

    def plan(self, payload: bytes) -> GatedOperation:
        body = bytes(payload)
        text = _payload_text(body)
        if len(text) > MAX_TEXT_CHARACTERS:
            raise ChannelRefused(
                "payload_too_large:slack",
                f"The Slack text is {len(text)} characters; Slack takes {MAX_TEXT_CHARACTERS}",
                status=400,
                size=len(text),
                limit=MAX_TEXT_CHARACTERS,
            )
        return GatedOperation.outbound(
            HOST,
            PORT,
            request=SlackRequest(body),
            data_classes=(DATA_CLASS,),
            payload_digest=sha256(body),
        )

    def check_destination(self, target: Mapping[str, Any], *, account: Mapping[str, Any], **_: Any) -> str:
        """Check key custody without posting a test message."""

        valid_key_ref(account.get("key_ref"))
        try:
            read_key(str(account.get("key_ref") or ""))
        except SlackKeyError as exc:
            return exc.code
        return "ready"

    def check_before_dispatch(self, target: Mapping[str, Any], account: Optional[Mapping[str, Any]] = None,
                              **_: Any) -> None:
        account = account or {}
        try:
            read_key(valid_key_ref(account.get("key_ref")))
        except SlackKeyError as exc:
            raise ChannelRefused(exc.code, "The Slack webhook cannot be read", status=400) from None

    def interpret(self, status: int, headers: Mapping[str, str], body: bytes) -> Outcome:
        raw = bytes(body)
        text = raw.decode("utf-8", errors="replace").strip()
        if status == 200:
            if raw == b"ok":
                return Outcome("sent", None, {
                    "word": "POSTED",
                    "destination": f"{HOST}:{PORT}",
                    "posted_at": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
                })
            return Outcome("unknown", "ack_missing")
        if status == 400 and text == "invalid_payload":
            return Outcome("failed", "invalid_payload")
        if status == 403 and text == "action_prohibited":
            return Outcome("failed", "action_prohibited")
        if status == 404 and text == "channel_not_found":
            return Outcome("failed", "channel_not_found")
        if status == 410 and text == "channel_is_archived":
            return Outcome("failed", "channel_is_archived")
        if status == 429:
            retry_after = str(headers.get("retry-after") or headers.get("Retry-After") or "").strip()
            if retry_after and len(retry_after) <= 20 and retry_after.isdigit():
                return Outcome("failed", "rate_limited", {"retry_after": retry_after[:20]})
            return Outcome("unknown", "unpinned_429")
        if 300 <= status < 400:
            return Outcome("unknown", "redirect_refused")
        if status == 500 and text == "rollup_error":
            return Outcome("unknown", "rollup_error")
        return Outcome("unknown", f"unpinned_{status}")

    def dispatch(self, row: Mapping[str, Any], seam: Any = None) -> Outcome:
        body, digest = bytes(row["payload"]), str(row["payload_digest"])
        if sha256(body) != digest:
            return Outcome("failed", "payload_changed")
        try:
            op = self.plan(body)
        except ChannelRefused as exc:
            return Outcome("failed", exc.code)
        if bytes(op.request.body) != body:
            return Outcome("failed", "plan_refused")
        principal, parent, broker = _authority(seam)
        account = json.loads(row["account_json"] or "{}")
        key_ref = str(account.get("key_ref") or "")
        connector = build_gated_connector(
            _manifest(),
            plan=lambda _proposal: op,
            interpret=lambda raw, _op: raw,
            opener=lambda planned: transmit(planned, key_ref),
            principal=principal,
            parent_operation_id=parent,
            broker=broker,
        )
        try:
            answer = connector(None)
        except ConnectorOperationRefused as exc:
            return Outcome("failed", "egress_refused", {"error": redact(exc.reason, body)})
        except SlackTransportError as exc:
            return Outcome("unknown" if exc.left else "failed", exc.code)
        return self.interpret(answer.status, answer.headers, answer.body)

    def recover(self, row: Mapping[str, Any]) -> Outcome:
        return Outcome("unknown", "interrupted")


CHANNELS["slack"] = SlackChannel()


__all__ = [
    "DATA_CLASS", "HOST", "MAX_TEXT_CHARACTERS", "HttpAnswer", "MemorySlackKeyStore", "NativeSlackKeyStore",
    "KEY_STORE", "SlackChannel", "SlackKeyError", "SlackRequest", "SlackTransportError", "HTTPS_HANDLER",
    "markdown_to_slack", "mint_key_ref", "key_slot", "read_key", "save_key", "transmit", "valid_key_ref",
    "validate_webhook_url",
]
