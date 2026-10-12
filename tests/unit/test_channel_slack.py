"""PHILO-11-02: the Slack incoming-webhook channel.

These fences exercise the channel producer itself.  The real hub fences in the
integration lane add the kernel egress child; this file keeps the network edge
and keyring in memory so a unit run can never send to Slack or write a native
keychain.
"""
from __future__ import annotations

import http.client
import io
import json
import socket
import ssl
import urllib.response
from typing import Any, Callable

import pytest

from holdspeak.services.channel_contract import ChannelRefused, Document


WEBHOOK = "https://hooks.slack.com/services/T000/B000/secret-path"
BODY = "The frozen body."


def _response(status: int, body: bytes = b"", headers: dict[str, str] | None = None) -> Callable[[Any], Any]:
    def answer(request: Any) -> Any:
        raw = "".join(f"{key}: {value}\r\n" for key, value in (headers or {}).items()) + "\r\n"
        response = urllib.response.addinfourl(
            io.BytesIO(body), http.client.parse_headers(io.BytesIO(raw.encode())), request.full_url, status
        )
        response.msg = "canned"
        return response

    return answer


class Wire:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.answer: Callable[[Any], Any] = _response(200, b"ok")

    def handler(self) -> Any:
        wire = self

        class Handler(__import__("urllib.request", fromlist=["BaseHandler"]).BaseHandler):
            def https_open(self, request: Any) -> Any:
                wire.requests.append({
                    "host": request.host,
                    "url": request.full_url,
                    "headers": dict(request.header_items()),
                    "body": bytes(request.data or b""),
                })
                return wire.answer(request)

        return Handler()


@pytest.fixture
def slack(monkeypatch: pytest.MonkeyPatch):
    from holdspeak.services import channel_slack

    store = channel_slack.MemorySlackKeyStore()
    monkeypatch.setattr(channel_slack, "KEY_STORE", lambda: store)
    return channel_slack.SlackChannel(), store


def test_save_target_has_only_label_and_key_reference_and_url_rule(slack: Any) -> None:
    channel, _store = slack
    account, target = channel.target_at_save({"key_ref": "work", "channel_label": "#leads"})
    assert account == {"key_ref": "work"}
    assert target == {"channel_label": "#leads"}

    for value in (
        "http://hooks.slack.com/services/T/B/K",
        "https://evil.example/services/T/B/K",
        "https://hooks.slack.com:0/services/T/B/K",
        "https://hooks.slack.com:8443/services/T/B/K",
        "https://hooks.slack.com/not-services/T/B/K",
    ):
        with pytest.raises(ChannelRefused) as caught:
            channel.validate_webhook(value)
        assert caught.value.code == "slack_webhook_invalid"

    assert channel.validate_webhook(WEBHOOK) == WEBHOOK


@pytest.mark.parametrize(
    "value",
    [
        "http://hooks.slack.com/services/T/B/K",
        "https://evil.example/services/T/B/K",
        "https://hooks.slack.com:0/services/T/B/K",
        "https://hooks.slack.com:8443/services/T/B/K",
        "https://hooks.slack.com/not-services/T/B/K",
        "https://hooks.slack.com/services/T/B/K?leak=yes",
    ],
)
def test_real_save_key_rejects_every_non_admitted_webhook_url(slack: Any, value: str) -> None:
    _channel, _store = slack
    from holdspeak.services import channel_slack

    with pytest.raises(channel_slack.ChannelRefused) as caught:
        channel_slack.save_key("work", value)
    assert caught.value.code == "slack_webhook_invalid"


def test_real_save_key_accepts_default_and_explicit_443(slack: Any) -> None:
    _channel, store = slack
    from holdspeak.services import channel_slack

    channel_slack.save_key("default", WEBHOOK)
    channel_slack.save_key("explicit", WEBHOOK.replace("hooks.slack.com/", "hooks.slack.com:443/"))
    assert store.values == {"slack:default": WEBHOOK, "slack:explicit": WEBHOOK.replace(
        "hooks.slack.com/", "hooks.slack.com:443/"
    )}


def test_markdown_is_serialized_once_and_preview_is_read_from_frozen_bytes(slack: Any) -> None:
    channel, _store = slack
    document = Document(
        ref="project_update:one",
        title="Update",
        body_md="# Heading\n\n**Bold** and [the link](https://example.test/a).\n- one",
    )
    payload = channel.serialize(document)
    assert payload == json.dumps(
        {"text": "*Heading*\n\n*Bold* and <https://example.test/a|the link>.\n- one"},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode()
    assert channel.preview(payload) == {"text": "*Heading*\n\n*Bold* and <https://example.test/a|the link>.\n- one"}


def test_size_refusal_is_named_before_dispatch(slack: Any) -> None:
    channel, _store = slack
    document = Document(ref="project_update:long", title="Long", body_md="x" * 39_001)
    with pytest.raises(ChannelRefused) as caught:
        channel.serialize(document)
    assert caught.value.code == "payload_too_large:slack"
    assert caught.value.context["size"] == 39_001
    assert caught.value.context["limit"] == 39_000


def test_multibyte_text_limit_counts_characters_in_serialize_and_plan(slack: Any) -> None:
    channel, _store = slack
    accepted = channel.serialize(Document(ref="project_update:unicode", title="U", body_md="é" * 39_000))
    assert channel.preview(accepted) == {"text": "é" * 39_000}
    assert channel.plan(accepted).payload_digest

    too_long = json.dumps({"text": "é" * 39_001}, ensure_ascii=False, separators=(",", ":")).encode()
    with pytest.raises(ChannelRefused) as caught_serialize:
        channel.serialize(Document(ref="project_update:unicode", title="U", body_md="é" * 39_001))
    with pytest.raises(ChannelRefused) as caught_plan:
        channel.plan(too_long)
    for caught in (caught_serialize, caught_plan):
        assert caught.value.code == "payload_too_large:slack"
        assert caught.value.context["size"] == 39_001
        assert caught.value.context["limit"] == 39_000


@pytest.mark.parametrize(
    ("status", "body", "headers", "state", "reason"),
    [
        (200, b"ok", {}, "sent", None),
        (200, b"OK", {}, "unknown", "ack_missing"),
        (400, b"invalid_payload", {}, "failed", "invalid_payload"),
        (403, b"action_prohibited", {}, "failed", "action_prohibited"),
        (404, b"channel_not_found", {}, "failed", "channel_not_found"),
        (410, b"channel_is_archived", {}, "failed", "channel_is_archived"),
        (429, b"rate_limited", {"Retry-After": "7"}, "failed", "rate_limited"),
        (500, b"rollup_error", {}, "unknown", "rollup_error"),
        (503, b"unavailable", {}, "unknown", "unpinned_503"),
        (302, b"", {"Location": "https://evil.example/"}, "unknown", "redirect_refused"),
    ],
)
def test_pinned_outcomes(status: int, body: bytes, headers: dict[str, str], state: str, reason: str) -> None:
    from holdspeak.services.channel_slack import SlackChannel

    outcome = SlackChannel().interpret(status, headers, body)
    assert (outcome.state, outcome.reason) == (state, reason)
    if state == "sent":
        assert outcome.proof["word"] == "POSTED"
        assert "link" not in outcome.proof
    if status == 429:
        assert outcome.proof == {"retry_after": "7"}


def test_transmit_reads_memory_key_and_sends_frozen_bytes_only(slack: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_slack

    channel, store = slack
    store.put(channel_slack.key_slot("work"), WEBHOOK)
    wire = Wire()
    monkeypatch.setattr(channel_slack, "HTTPS_HANDLER", wire.handler)
    document = Document(ref="project_update:one", title="Update", body_md=BODY)
    payload = channel.serialize(document)
    operation = channel.plan(payload)
    answer = channel_slack.transmit(operation, "work")
    assert answer.status == 200 and answer.body == b"ok"
    assert wire.requests[0]["host"] == "hooks.slack.com"
    assert wire.requests[0]["url"] == WEBHOOK
    assert wire.requests[0]["body"] == payload
    assert WEBHOOK not in json.dumps(wire.requests[0]["headers"])


def test_transport_errors_do_not_expose_webhook(slack: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_slack

    channel, store = slack
    store.put(channel_slack.key_slot("work"), WEBHOOK)

    def raises(_request: Any) -> Any:
        raise RuntimeError(f"TLS failed for {WEBHOOK}")

    class Handler(__import__("urllib.request", fromlist=["BaseHandler"]).BaseHandler):
        def https_open(self, request: Any) -> Any:
            return raises(request)

    monkeypatch.setattr(channel_slack, "HTTPS_HANDLER", lambda: Handler())
    payload = channel.serialize(Document(ref="project_update:one", title="Update", body_md=BODY))
    with pytest.raises(channel_slack.SlackTransportError) as caught:
        channel_slack.transmit(channel.plan(payload), "work")
    assert caught.value.code == "transport_error"
    assert WEBHOOK not in str(caught.value)


def _fake_backend(module: str, name: str, **attrs: Any) -> Any:
    attrs["__module__"] = module
    return type(name, (), attrs)()


class _Vault:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def put(self, service: str, user: str, value: str) -> None:
        self.values[(service, user)] = value

    def get(self, service: str, user: str) -> str | None:
        return self.values.get((service, user))


@pytest.mark.parametrize(
    ("module", "name"),
    [
        ("keyring.backends.macOS", "Keyring"),
        ("keyring.backends.SecretService", "Keyring"),
        ("keyring.backends.Windows", "WinVaultKeyring"),
    ],
)
def test_native_key_store_accepts_only_the_three_native_backends(module: str, name: str) -> None:
    from holdspeak.services.channel_slack import NativeSlackKeyStore

    vault = _Vault()
    backend = _fake_backend(module, name, set_password=vault.put, get_password=vault.get, vault=vault)
    store = NativeSlackKeyStore(backend=backend)
    store.put("slack:work", WEBHOOK)
    assert store.get("slack:work") == WEBHOOK
    assert vault.values == {("HoldSpeak Slack", "slack:work"): WEBHOOK}

    chained = NativeSlackKeyStore(backend=_fake_backend(
        "keyring.backends.chainer", "ChainerBackend",
        backends=[_fake_backend("keyring.backends.fail", "Keyring"), backend],
    ))
    assert chained.get("slack:work") == WEBHOOK


@pytest.mark.parametrize(
    "backend",
    [
        _fake_backend("keyring.backends.fail", "Keyring"),
        _fake_backend("keyrings.alt.file", "PlaintextKeyring"),
        _fake_backend("keyring.backends.chainer", "ChainerBackend", backends=[]),
    ],
)
def test_non_native_key_store_is_refused_by_name(backend: Any) -> None:
    from holdspeak.services.channel_slack import NativeSlackKeyStore, SlackKeyError

    with pytest.raises(SlackKeyError) as caught:
        NativeSlackKeyStore(backend=backend)
    assert caught.value.code == "slack_key_store_not_native"


def test_native_key_store_distinguishes_locked_and_missing_without_os_keychain() -> None:
    from holdspeak.services.channel_slack import NativeSlackKeyStore, SlackKeyError

    def locked(*_args: Any) -> Any:
        raise RuntimeError("locked")

    locked_store = NativeSlackKeyStore(backend=_fake_backend(
        "keyring.backends.macOS", "Keyring", set_password=locked, get_password=locked,
    ))
    with pytest.raises(SlackKeyError) as caught_get:
        locked_store.get("slack:work")
    with pytest.raises(SlackKeyError) as caught_put:
        locked_store.put("slack:work", WEBHOOK)
    assert caught_get.value.code == caught_put.value.code == "slack_key_store_locked"

    missing_store = NativeSlackKeyStore(backend=_fake_backend(
        "keyring.backends.macOS", "Keyring", set_password=lambda *_args: None, get_password=lambda *_args: None,
    ))
    with pytest.raises(SlackKeyError) as missing:
        missing_store.get("slack:work")
    assert missing.value.code == "slack_webhook_missing"


class _OfflineSocket:
    def __init__(self, fail: BaseException | None = None) -> None:
        self.fail = fail
        self.writes: list[bytes] = []

    def sendall(self, data: Any) -> None:
        self.writes.append(bytes(data))
        if self.fail is not None:
            raise self.fail

    def makefile(self, _mode: str) -> Any:
        return io.BytesIO(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok")

    def close(self) -> None:
        return None


@pytest.mark.parametrize(
    ("connect_error", "fail_after_connect", "expected_left", "expected_code"),
    [
        (ConnectionRefusedError("refused"), None, False, "connect_refused"),
        (ssl.SSLError("handshake"), None, False, "tls_failed"),
        (socket.gaierror("dns"), None, False, "dns_failed"),
        (None, ssl.SSLError("dropped after write"), True, "tls_failed"),
    ],
)
def test_quiet_https_edge_tracks_before_and_after_byte_failures(
    slack: Any,
    monkeypatch: pytest.MonkeyPatch,
    connect_error: BaseException | None,
    fail_after_connect: BaseException | None,
    expected_left: bool,
    expected_code: str,
) -> None:
    channel, store = slack
    from holdspeak.services import channel_slack

    store.put(channel_slack.key_slot("work"), WEBHOOK)
    made: list[_OfflineSocket] = []

    def connect(connection: Any) -> None:
        if connect_error is not None:
            raise connect_error
        made.append(_OfflineSocket(fail_after_connect))
        connection.sock = made[-1]

    monkeypatch.setattr(http.client.HTTPSConnection, "connect", connect)
    monkeypatch.setattr(channel_slack, "HTTPS_HANDLER", channel_slack.QuietHTTPSHandler)
    payload = channel.serialize(Document(ref="project_update:edge", title="E", body_md="edge"))
    with pytest.raises(channel_slack.SlackTransportError) as caught:
        channel_slack.transmit(channel.plan(payload), "work")
    assert caught.value.code == expected_code
    assert caught.value.left is expected_left
    if expected_left:
        assert made and made[0].writes


def test_native_keyring_is_never_constructed_by_unit_fixture(slack: Any) -> None:
    from holdspeak.services import channel_slack

    _channel, store = slack
    assert isinstance(store, channel_slack.MemorySlackKeyStore)
    assert store.values == {}
