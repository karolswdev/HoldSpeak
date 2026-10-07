"""PHILO-10-03: the email channel -- a provider interface (design sections 3, 4, 4a, 6 and 8).

Every fence reaches the send through the REAL hub on an isolated HOME (the
routes, the Room's kernel path, the real ``external.egress`` admission with
the real allow-list) and stops at the HTTPS edge: ``channel_email.HTTPS_HANDLER``
is a canned handler that records what reached the wire and answers. The REAL
opener, its redirect refusal and its error processing run above it. No lane
reaches the network, and the key store is the injected memory store: a guard
makes ``keyring.get_keyring`` fail the test if anything reaches the real
keychain (grounding F17: an isolated HOME still resolves to the macOS Keychain).

| Criterion | Fences |
|---|---|
| 1 one egress child, the bytes, the digest | ``test_c1_*`` |
| 2 the outcomes through the real producer | ``test_c2_*``, ``test_c2_r*`` (R1, R2, R4, R6); R3 by a real process: ``test_c2_r3_*`` |
| 3 a transport exception leaves no key and no body | ``test_c3_*`` |
| 4 the sentinel fence | ``test_c4_*`` |
| 5 key custody | ``test_c5_*`` |
| 6 a second provider: one class, one row | ``test_c6_*`` (a Postmark-like TEST provider: its own auth header, its id in the JSON body) |
| 7 Resend, the second provider (PHILO-10-07) | ``test_c7_*``: its exact request, its id, its pinned list, its key slot, its own B11 answer |
| r2 (Codex Astra r1 on #696) | ``test_r2_*``: the REAL edge over an offline socket -- wire debug, the write transition |
"""
from __future__ import annotations

import http.client
import io
import json
import socket
import sys
import threading
import urllib.error
import urllib.request
import urllib.response
from pathlib import Path
from typing import Any, Callable, Optional

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _philo10_send import (  # noqa: E402
    SENTINEL, Hub, _boot, history, in_thread, op, ops, preview_digest, prepare, reap_past_deadline, room, send,
    sends,
)

KEY = "SG.syntheticKEY7c1e0000abcd.neverLeavesTheOpener0000"
KEY_MARK = "syntheticKEY7c1e"
SENDER_403 = ("The from address does not match a verified Sender Identity. Mail cannot be sent until this error "
              "is resolved.")
FORMS = ["send_id", "inline"]


# ── the HTTPS edge ──────────────────────────────────────────────────────────


def response(status: int, headers: Optional[dict[str, str]] = None, body: bytes = b"") -> Callable[[Any], Any]:
    def answer(req: Any) -> Any:
        raw = "".join(f"{k}: {v}\r\n" for k, v in (headers or {}).items()) + "\r\n"
        resp = urllib.response.addinfourl(io.BytesIO(body), http.client.parse_headers(io.BytesIO(raw.encode())),
                                          req.full_url, status)
        resp.msg = "canned"
        return resp
    return answer


def errors(status: int, *messages: str, field: Optional[str] = None) -> Callable[[Any], Any]:
    return response(status, {"Content-Type": "application/json"},
                    json.dumps({"errors": [{"message": m, "field": field} for m in messages]}).encode())


def raising(exc: BaseException) -> Callable[[Any], Any]:
    def answer(req: Any) -> Any:
        raise exc
    return answer


class Wire:
    """The canned HTTPS edge: records each request that reached it, answers from the script."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.script: list[Callable[[Any], Any]] = []
        self.default: Callable[[Any], Any] = response(202, {"X-Message-Id": "sg-msg-0001"})
        self.hold: str = ""
        self.entered = threading.Event()
        self.release = threading.Event()

    def handler(self) -> urllib.request.BaseHandler:
        wire = self

        class Canned(urllib.request.BaseHandler):
            def https_open(self, req: Any) -> Any:
                if wire.hold == "before":
                    wire.entered.set()
                    assert wire.release.wait(60)
                wire.requests.append({"host": req.host, "url": req.full_url, "headers": dict(req.header_items()),
                                      "body": bytes(req.data or b"")})
                if wire.hold == "after":
                    wire.entered.set()
                    assert wire.release.wait(60)
                step = wire.script.pop(0) if wire.script else wire.default
                return step(req)

        return Canned()


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> Any:
    import keyring

    from holdspeak.services import channel_email

    memory = channel_email.MemoryEmailKeyStore()
    monkeypatch.setattr(channel_email, "KEY_STORE", lambda: memory)

    def never(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("a lane reached the real keychain")

    monkeypatch.setattr(keyring, "get_keyring", never)
    return memory


@pytest.fixture
def wire(monkeypatch: pytest.MonkeyPatch) -> Wire:
    from holdspeak.services import channel_email

    canned = Wire()
    monkeypatch.setattr(channel_email, "HTTPS_HANDLER", canned.handler)
    return canned


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, store: Any, wire: Wire):
    from holdspeak.db import reset_database
    from holdspeak.kernel.external_egress import EGRESS_EXECUTIONS

    EGRESS_EXECUTIONS._results.clear()
    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def save_key(hub: Hub, key: str = KEY, key_ref: str = "sendgrid", provider: Optional[str] = "sendgrid") -> Any:
    # PHILO-15 04: Resend is the default now; these fixtures name SendGrid.
    return hub.client.put(f"/api/channels/email-keys/{key_ref}",
                          json={"api_key": key, **({"provider": provider} if provider else {})})


def email_destination(hub: Hub, **extra: Any) -> str:
    fields = {"name": "Priya by email", "channel": "email", "provider": "sendgrid", "from_email": "karol@example.com",
              "from_name": "Karol", "key_ref": "sendgrid", "to": ["Priya Raman <priya@example.com>"],
              "cc": ["lead@example.com"], **extra}
    resp = hub.client.post("/api/channels/destinations", json=fields)
    assert resp.status_code == 200, resp.text
    return resp.json()["destination"]["id"]


def ready(hub: Hub, *, body: str = f"Cutover is green. {SENTINEL}", **extra: Any) -> tuple[str, str]:
    assert save_key(hub).status_code == 200
    _pid, update = room(hub, body=body)
    return update, email_destination(hub, **extra)


def press(hub: Hub, form: str, update: str, dest: str, key: str) -> dict[str, Any]:
    if form == "send_id":
        return {"send_id": prepare(hub, update, dest)["send"]["id"], "command_id": key}
    return {"document_ref": f"project_update:{update}", "destination_id": dest, "preview_digest": preview_digest(hub, update, dest),
            "command_id": key}


def egress_ops(hub: Hub) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT o.*, r.state AS receipt_state, r.outcome AS outcome FROM kernel_operations o"
            " LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id WHERE o.name='external.egress'"
            " ORDER BY o.created_at, o.rowid")]


def journal_refs(hub: Hub, operation_id: str) -> set[str]:
    with hub.db._connection() as conn:
        rows = conn.execute("SELECT refs_json FROM kernel_journal WHERE operation_id=?", (operation_id,)).fetchall()
    return {ref for r in rows for ref in json.loads(r["refs_json"] or "[]")}


def native(hub: Hub, operation_id: str) -> dict[str, Any]:
    from holdspeak.kernel.external_egress import LOCAL_OWNER
    from holdspeak.services import project_kernel

    broker = project_kernel._broker(hub.db)
    return broker.read([f"operation:{operation_id}"], "full", "committed", LOCAL_OWNER)["objects"][0]


#: Where a body must never be: the kernel's tables, the send rows (their payload column aside: it IS the
#: frozen request), the history and the destinations. The document's own tables hold it by design.
BODY_FREE = ("kernel_operations", "kernel_receipts", "kernel_journal", "kernel_projection_stages",
             "channel_sends", "project_update_deliveries", "channel_destinations")


def dump(hub: Hub, *, skip: tuple[tuple[str, str], ...] = (), only: tuple[str, ...] = ()) -> str:
    """Every value of every table (or of *only*), as text (bytes decoded), except the named (table, column) pairs."""
    out: list[str] = []
    with hub.db._connection() as conn:
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            if only and table not in only:
                continue
            for row in conn.execute(f"SELECT * FROM '{table}'"):
                for column in row.keys():
                    if (table, column) in skip:
                        continue
                    value = row[column]
                    out.append(value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value))
    return "\n".join(out)


# ── 1: one send, one egress child, the frozen bytes on the wire, their digest admitted ──


@pytest.mark.parametrize("form", FORMS)
def test_c1_one_send_is_one_egress_child_whose_wire_bytes_and_digest_are_the_frozen_ones(
    hub: Hub, wire: Wire, form: str,
) -> None:
    update, dest = ready(hub)
    answer = send(hub, press(hub, form, update, dest, f"c1-{form}"))
    assert answer.status_code == 200, answer.text
    body = answer.json()
    [row] = [r for r in sends(hub) if r["state"] != "prepared"]
    frozen = bytes(row["payload"])
    # The one byte contract: the bytes on the wire ARE the frozen payload; the preview is parsed from them.
    [sent] = wire.requests
    assert (sent["host"], sent["url"]) == ("api.sendgrid.com", "https://api.sendgrid.com/v3/mail/send")
    assert sent["body"] == frozen and sent["headers"]["Authorization"] == f"Bearer {KEY}"
    request = json.loads(frozen)
    assert request["content"] == [{"type": "text/plain", "value": f"Cutover is green. {SENTINEL}"}]
    assert body["send"]["preview"] == {"from": "Karol <karol@example.com>",
                                       "to": ["Priya Raman <priya@example.com>"], "cc": ["lead@example.com"],
                                       "subject": request["subject"], "text": f"Cutover is green. {SENTINEL}"}
    # One external.egress CHILD of the send, under the send's authenticated principal.
    send_op = op(hub, body["operation_id"])
    [child] = egress_ops(hub)
    assert child["parent_operation_id"] == body["operation_id"]
    assert (child["principal_kind"], child["principal_identity"]) == (send_op["principal_kind"],
                                                                      send_op["principal_identity"])
    assert (child["state"], child["receipt_state"]) == ("succeeded", "succeeded")
    full = native(hub, child["operation_id"])
    assert full["canonical"]["destination"] == "api.sendgrid.com:443"
    assert full["canonical"]["data_classes"] == ["email_message"]
    # The admission binds the digest of the frozen bytes (not a digest of the destination).
    assert full["canonical"]["payload_digest"] == "sha256:" + row["payload_digest"]
    assert {f"destination:{dest}", "egress:api.sendgrid.com:443", "data-class:email_message",
            f"payload:sha256:{row['payload_digest']}"} <= journal_refs(hub, child["operation_id"])


def test_c1_two_different_bodies_are_two_different_admitted_digests(hub: Hub, wire: Wire) -> None:
    """Red on main: ``connector_runtime.py:215`` hashed only the destination (one digest for both)."""
    update, dest = ready(hub, body="First body.")
    first = send(hub, press(hub, "inline", update, dest, "c1-two-a")).json()
    _pid, other = room(hub, name="Second room", body="A different body.")
    second = send(hub, press(hub, "inline", other, dest, "c1-two-b")).json()
    digests = [native(hub, c["operation_id"])["canonical"]["payload_digest"] for c in egress_ops(hub)]
    assert digests == ["sha256:" + first["send"]["payload_digest"], "sha256:" + second["send"]["payload_digest"]]
    assert digests[0] != digests[1]
    assert [r["body"] for r in wire.requests] == [bytes(r["payload"]) for r in sends(hub)]


def test_c1_a_request_to_any_other_host_is_refused_by_the_kernel(
    hub: Hub, wire: Wire, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.plugins.gated_connector import GatedOperation
    from holdspeak.services import channel_email

    real = channel_email.SendGridProvider.plan

    def elsewhere(self: Any, body: bytes) -> Any:
        planned = real(self, body)
        return GatedOperation.outbound("evil.example", 443, request=channel_email.EmailRequest(
            "https://evil.example/v3/mail/send", body), data_classes=planned.data_classes)

    monkeypatch.setattr(channel_email.SendGridProvider, "plan", elsewhere)
    update, dest = ready(hub)
    answer = send(hub, press(hub, "inline", update, dest, "c1-host")).json()
    assert (answer["outcome"], answer["send"]["reason"]) == ("failed", "egress_refused")
    assert wire.requests == []
    [child] = egress_ops(hub)
    assert (child["receipt_state"], child["outcome"]) == (
        "refused", "external_egress_destination_not_allowed:evil.example:443")


# ── 2: the outcomes through the real producer ─────────────────────────────

OUTCOMES = [
    ("accepted", response(202, {"X-Message-Id": "sg-msg-0001"}), "sent", None),
    ("accepted-no-id", response(202), "unknown", "accepted_without_message_id"),
    ("400", errors(400, "The content value must be a string at least one character in length.", field="content"),
     "failed", "invalid_request"),
    ("401", errors(401, "The provided authorization grant is invalid, expired, or revoked"), "failed",
     "api_key_invalid"),
    ("403-sender", errors(403, SENDER_403, field="from"), "failed", "sender_not_verified"),
    ("403-other", errors(403, "You are temporarily blocked from sending."), "failed", "sendgrid_forbidden"),
    ("413", errors(413, "Payload too large"), "failed", "payload_too_large"),
    ("429", errors(429, "too many requests"), "failed", "rate_limited"),
    ("400-not-sendgrid", response(400, {"Content-Type": "text/html"}, b"<html>proxy</html>"), "unknown",
     "unpinned_400"),
    ("404", errors(404, "not found"), "unknown", "unpinned_404"),
    ("500", response(500, {}, b"oops"), "unknown", "unpinned_500"),
    ("503", errors(503, "unavailable"), "unknown", "unpinned_503"),
    ("timeout", raising(socket.timeout("timed out")), "unknown", "timeout"),
    ("timeout-url", raising(urllib.error.URLError(socket.timeout("timed out"))), "unknown", "timeout"),
    ("reset", raising(urllib.error.URLError(ConnectionResetError("reset"))), "unknown", "transport_error"),
    ("refused", raising(urllib.error.URLError(ConnectionRefusedError("refused"))), "failed", "connect_refused"),
    ("dns", raising(urllib.error.URLError(socket.gaierror("no such host"))), "failed", "dns_failed"),
    ("redirect", response(302, {"Location": "https://evil.example/steal"}), "unknown", "redirect_refused"),
    ("redirect-307", response(307, {"Location": "https://api.sendgrid.com.evil.example/"}), "unknown",
     "redirect_refused"),
]
KERNEL = {"sent": "succeeded", "failed": "failed", "unknown": "indeterminate"}


@pytest.mark.parametrize("case,answer,state,reason", OUTCOMES, ids=[c[0] for c in OUTCOMES])
def test_c2_each_answer_settles_by_the_pinned_list(
    hub: Hub, wire: Wire, case: str, answer: Any, state: str, reason: Optional[str],
) -> None:
    update, dest = ready(hub)
    wire.script = [answer]
    reply = send(hub, press(hub, "inline", update, dest, f"c2-{case}"))
    assert reply.status_code == 200, reply.text
    result = reply.json()
    assert (result["outcome"], result["send"]["reason"]) == (state, reason), result["send"]
    assert result["receipt"]["state"] == KERNEL[state]
    # The redirect is NOT followed: one request, and no Authorization reaches a second host.
    assert len(wire.requests) == 1 and wire.requests[0]["host"] == "api.sendgrid.com"
    assert [r for r in wire.requests if r["host"] != "api.sendgrid.com"] == []
    rows = history(hub, update)
    if state == "failed":
        assert rows == []  # a known non-delivery is not a delivery
    else:
        assert [r["outcome"] for r in rows] == [state]
    read_back = hub.client.get(f"/api/channels/sends?send_id={result['send']['id']}").json()["sends"][0]
    if state == "sent":
        proof = read_back["proof"]
        assert proof == {"provider": "sendgrid", "message_id": "sg-msg-0001", "word": "ACCEPTED BY SENDGRID",
                         "scope": "accepted for processing, not delivery"}
        assert result["send"]["proof"] == proof
    assert read_back["state"] == state and read_back["reason"] == reason


def test_c2_the_two_403_discriminators_map_apart(hub: Hub, wire: Wire) -> None:
    update, dest = ready(hub)
    wire.script = [errors(403, SENDER_403, field="from"), errors(403, "Access forbidden")]
    first = send(hub, press(hub, "inline", update, dest, "c2-403-a")).json()
    second = send(hub, press(hub, "inline", update, dest, "c2-403-b")).json()
    assert (first["send"]["reason"], second["send"]["reason"]) == ("sender_not_verified", "sendgrid_forbidden")
    assert second["send"]["proof"] == {"error": "Access forbidden"}


def _fail_the_settle_once(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import channel_service

    real = channel_service.settle_in_transaction
    failed: list[int] = []

    def settle(conn: Any, **kwargs: Any) -> Any:
        settled = real(conn, **kwargs)
        if not failed:
            failed.append(1)
            raise RuntimeError("injected: the settle write failed after the effect")
        return settled

    monkeypatch.setattr(channel_service, "settle_in_transaction", settle)


def _send_op(hub: Hub) -> dict[str, Any]:
    [operation] = ops(hub, "channel.send")
    return operation


@pytest.mark.parametrize("form", FORMS)
def test_c2_r1_a_failed_settle_is_taken_over_as_unknown_and_never_sent_again(
    hub: Hub, wire: Wire, monkeypatch: pytest.MonkeyPatch, form: str,
) -> None:
    update, dest = ready(hub)
    body = press(hub, form, update, dest, f"r1-{form}")
    _fail_the_settle_once(monkeypatch)
    assert send(hub, body).status_code == 500
    assert (_send_op(hub)["state"], _send_op(hub)["receipts"]) == ("claimed", 0)
    [row] = [r for r in sends(hub) if r["send_operation_id"]]
    assert row["state"] == "dispatching"
    taken_over = send(hub, body).json()
    assert (taken_over["outcome"], taken_over["send"]["reason"]) == ("unknown", "interrupted")
    replayed = send(hub, body).json()
    assert replayed["send"] == taken_over["send"]
    assert replayed["receipt"]["receipt_id"] == taken_over["receipt"]["receipt_id"]
    assert len(wire.requests) == 1  # never sent again
    assert (_send_op(hub)["state"], _send_op(hub)["receipts"]) == ("indeterminate", 1)
    assert [r["outcome"] for r in history(hub, update)] == ["unknown"]


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("hold", ["before", "after"], ids=["held-before-the-wire", "held-after-the-wire"])
def test_c2_r2_the_reaper_settles_a_silent_email_unknown_and_the_replay_answers_it(
    hub: Hub, wire: Wire, form: str, hold: str,
) -> None:
    update, dest = ready(hub)
    body = press(hub, form, update, dest, f"r2-{form}-{hold}")
    wire.hold = hold
    thread, answer = in_thread(lambda: send(hub, body))
    assert wire.entered.wait(30)
    [row] = [r for r in sends(hub) if r["state"] == "dispatching"]
    reaped = reap_past_deadline(hub)
    assert {"operation_id": row["send_operation_id"], "state": "indeterminate",
            "outcome": "execution_liveness_expired"} in reaped["reaped"], reaped
    settled = hub.db.channel_sends.get(row["id"])
    assert (settled["state"], settled["reason"]) == ("unknown", "reaped")
    assert [r["outcome"] for r in history(hub, update)] == ["unknown"]
    wire.release.set()
    thread.join(60)
    [late] = answer
    assert late.status_code == 200 and late.json()["outcome"] == "unknown", late.text
    replayed = send(hub, body).json()
    assert (replayed["outcome"], replayed["send"]["reason"]) == ("unknown", "reaped")
    assert len(wire.requests) == 1
    assert (_send_op(hub)["state"], _send_op(hub)["receipts"]) == ("indeterminate", 1)
    assert len(history(hub, update)) == 1


def test_c2_r4_a_take_over_that_wins_leaves_the_reaper_nothing(
    hub: Hub, wire: Wire, monkeypatch: pytest.MonkeyPatch,
) -> None:
    update, dest = ready(hub)
    body = press(hub, "send_id", update, dest, "r4")
    _fail_the_settle_once(monkeypatch)
    assert send(hub, body).status_code == 500
    assert send(hub, body).json()["outcome"] == "unknown"
    assert reap_past_deadline(hub)["count"] == 0
    assert (_send_op(hub)["state"], _send_op(hub)["receipts"]) == ("indeterminate", 1)
    assert len(wire.requests) == 1 and len(history(hub, update)) == 1


@pytest.mark.parametrize("form", FORMS)
def test_c2_r6_reaped_before_the_boundary_sends_nothing(
    hub: Hub, wire: Wire, monkeypatch: pytest.MonkeyPatch, form: str,
) -> None:
    from holdspeak.services.channel_email import EmailChannel

    update, dest = ready(hub)
    body = press(hub, form, update, dest, f"r6-{form}")
    entered, release = threading.Event(), threading.Event()
    real = EmailChannel.check_before_dispatch

    def check(channel: Any, target: Any, **kw: Any) -> Any:
        entered.set()
        assert release.wait(60)
        return real(channel, target, **kw)

    monkeypatch.setattr(EmailChannel, "check_before_dispatch", check)
    thread, answer = in_thread(lambda: send(hub, body))
    assert entered.wait(30)
    reap_past_deadline(hub)
    release.set()
    thread.join(60)
    assert wire.requests == [] and history(hub, update) == []
    assert all(r["state"] == "prepared" for r in sends(hub))
    assert _send_op(hub)["outcome"] == "reaped_before_dispatch"


# ── 3: a transport exception leaves neither the key nor the body ─────────────


def test_c3_every_egress_caller_records_a_sanitized_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Red on main: ``external_egress.py:290`` recorded ``f"{type(exc).__name__}: {exc}"``."""
    import holdspeak.db.core as db_core
    from holdspeak.db import Database
    from holdspeak.kernel import runtime as kernel_runtime
    from holdspeak.kernel.external_egress import EGRESS_EXECUTIONS, LOCAL_OWNER, run_external_egress

    db = Database(tmp_path / "egress.db")
    monkeypatch.setattr(db_core, "_db", db)
    broker = kernel_runtime._configure(db)

    def sender() -> None:
        raise RuntimeError(f"POST failed; Authorization: Bearer {KEY}; body={SENTINEL}")

    with pytest.raises(RuntimeError):
        run_external_egress(connector_id="any-caller", destination="hooks.example:443", data_classes=("x",),
                            payload_material={"digest": "only"}, sender=sender,
                            allowed_destinations=("hooks.example:443",), broker=broker)
    result = list(EGRESS_EXECUTIONS._results.values())[-1]
    full = broker.read([f"operation:{result['operation_id']}"], "full", "committed", LOCAL_OWNER)["objects"][0]
    assert result["error"] == "RuntimeError"
    for text in (json.dumps(result, default=str), json.dumps(full, default=str)):
        assert KEY_MARK not in text and SENTINEL not in text


def test_c3_an_email_transport_exception_carrying_the_key_and_body_leaves_neither(
    hub: Hub, wire: Wire, caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("DEBUG")
    update, dest = ready(hub)
    wire.script = [raising(RuntimeError(f"socket said: Authorization: Bearer {KEY} {SENTINEL}"))]
    result = send(hub, press(hub, "send_id", update, dest, "c3")).json()
    assert (result["outcome"], result["send"]["reason"]) == ("unknown", "transport_error")
    [child] = egress_ops(hub)
    full = native(hub, child["operation_id"])
    assert full["canonical"]["error"] == "EmailTransportError"
    assert result["send"]["proof"] is None
    places = {"native": json.dumps(full, default=str), "receipt": json.dumps(result["receipt"]),
              "logs": caplog.text,
              "database": dump(hub, skip=(("channel_sends", "payload"),), only=BODY_FREE)}
    for where, text in places.items():
        assert KEY_MARK not in text, where
        assert SENTINEL not in text, where
    assert KEY_MARK not in dump(hub) and KEY_MARK not in json.dumps(result)


# ── 4: the sentinel fence ─────────────────────────────────────────────────


def test_c4_no_key_and_no_body_in_the_journal_a_receipt_a_log_an_error_or_a_file(
    hub: Hub, wire: Wire, tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("DEBUG")
    update, dest = ready(hub)
    # SendGrid's error echoes the body and the key: both are removed before a row, a receipt or the face.
    wire.script = [response(202, {"X-Message-Id": "sg-msg-0001"}),
                   errors(400, f"bad content near '{SENTINEL}' with {KEY}", field="content")]
    sent = send(hub, press(hub, "send_id", update, dest, "c4-a")).json()
    failed = send(hub, press(hub, "inline", update, dest, "c4-b")).json()
    assert (sent["outcome"], failed["outcome"], failed["send"]["reason"]) == ("sent", "failed", "invalid_request")
    assert "[redacted]" in failed["send"]["proof"]["error"]
    body_free = dump(hub, skip=(("channel_sends", "payload"),), only=BODY_FREE)
    errors_and_receipts = json.dumps([[a["receipt"], a["send"]["reason"], a["send"]["proof"]] for a in (sent, failed)])
    for where, text in {"journal, receipts, rows": body_free, "logs": caplog.text,
                        "errors and receipts": errors_and_receipts}.items():
        assert KEY_MARK not in text, where
        assert SENTINEL not in text, where
    assert KEY_MARK not in dump(hub) and KEY_MARK not in json.dumps([sent, failed])
    # The key is nowhere on disk (the payload rows hold the body, never the key).
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert KEY_MARK.encode() not in path.read_bytes(), path
    # The journal names the destination, the egress host, the data class and the digest.
    refs = set().union(*(journal_refs(hub, c["operation_id"]) for c in egress_ops(hub)))
    assert {f"destination:{dest}", "egress:api.sendgrid.com:443", "data-class:email_message"} <= refs
    assert f"payload:sha256:{sent['send']['payload_digest']}" in refs


def test_c4_the_key_is_never_planning_material(hub: Hub, wire: Wire, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.kernel import external_egress

    seen: list[str] = []
    real = external_egress.EgressExecutionStore.bind

    def reachable(value: Any, depth: int = 0) -> None:
        """Everything the plan holds: values, and each function's closure cells and defaults, three levels down."""
        if callable(value) and hasattr(value, "__code__") and depth < 3:
            for cell in value.__closure__ or ():
                reachable(getattr(cell, "cell_contents", None), depth + 1)
            for default in (value.__defaults__ or ()) + tuple((value.__kwdefaults__ or {}).values()):
                reachable(default, depth + 1)
            return
        seen.append(repr(value))

    def bind(self: Any, **kwargs: Any) -> Any:
        for value in kwargs.values():
            reachable(value)
        return real(self, **kwargs)

    monkeypatch.setattr(external_egress.EgressExecutionStore, "bind", bind)
    update, dest = ready(hub)
    assert send(hub, press(hub, "inline", update, dest, "c4-plan")).json()["outcome"] == "sent"
    assert seen and all(KEY_MARK not in text for text in seen)
    assert wire.requests[0]["headers"]["Authorization"] == f"Bearer {KEY}"  # only the opener set it


# ── 5: key custody ─────────────────────────────────────────────────────────


def _backend(module: str, name: str, **attrs: Any) -> Any:
    kind = type(name, (), {"__module__": module, "__qualname__": name})
    backend = kind()
    for key, value in attrs.items():
        setattr(backend, key, value)
    return backend


class _Vault:
    def __init__(self) -> None:
        self.values: dict[tuple[str, str], str] = {}

    def set_password(self, service: str, user: str, value: str) -> None:
        self.values[(service, user)] = value

    def get_password(self, service: str, user: str) -> Optional[str]:
        return self.values.get((service, user))


def _native_stub(module: str = "keyring.backends.macOS", name: str = "Keyring") -> Any:
    vault = _Vault()
    return _backend(module, name, set_password=vault.set_password, get_password=vault.get_password, vault=vault)


@pytest.mark.parametrize("module,name", [("keyring.backends.macOS", "Keyring"),
                                         ("keyring.backends.SecretService", "Keyring"),
                                         ("keyring.backends.Windows", "WinVaultKeyring")])
def test_c5_a_native_backend_stores_and_reads_the_key(store: Any, module: str, name: str) -> None:
    from holdspeak.services.channel_email import NativeEmailKeyStore

    backend = _native_stub(module, name)
    native_store = NativeEmailKeyStore(backend=backend)
    native_store.put("sendgrid", KEY)
    assert native_store.get("sendgrid") == KEY
    assert backend.vault.values == {("HoldSpeak Email", "sendgrid"): KEY}
    chained = NativeEmailKeyStore(backend=_backend("keyring.backends.chainer", "ChainerBackend",
                                                   backends=[_backend("keyring.backends.fail", "Keyring"), backend]))
    assert chained.get("sendgrid") == KEY


@pytest.mark.parametrize("backend", [
    "fail", "chainer-without-native", "keyrings.alt-file", "keyrings.alt-encrypted", "null",
])
def test_c5_every_other_backend_is_refused_not_native(store: Any, backend: str) -> None:
    import keyring.backends.fail

    from holdspeak.services.channel_email import EmailKeyError, NativeEmailKeyStore

    chosen = {
        "fail": keyring.backends.fail.Keyring(),
        "chainer-without-native": _backend("keyring.backends.chainer", "ChainerBackend",
                                           backends=[keyring.backends.fail.Keyring()]),
        "keyrings.alt-file": _backend("keyrings.alt.file", "PlaintextKeyring"),
        "keyrings.alt-encrypted": _backend("keyrings.alt.file", "EncryptedKeyring"),
        "null": _backend("keyring.backends.null", "Keyring"),
    }[backend]
    with pytest.raises(EmailKeyError) as refused:
        NativeEmailKeyStore(backend=chosen)
    assert refused.value.code == "email_key_store_not_native"


@pytest.mark.parametrize("form", FORMS)
def test_c5_a_store_that_is_not_native_refuses_the_save_and_the_send_before_anything_leaves(
    hub: Hub, wire: Wire, store: Any, monkeypatch: pytest.MonkeyPatch, form: str,
) -> None:
    import keyring.backends.fail

    from holdspeak.services import channel_email

    update, dest = ready(hub)
    body = press(hub, form, update, dest, f"c5-{form}")
    monkeypatch.setattr(channel_email, "KEY_STORE",
                        lambda: channel_email.NativeEmailKeyStore(backend=keyring.backends.fail.Keyring()))
    saved = save_key(hub)
    assert (saved.status_code, saved.json()["code"]) == (400, "email_key_store_not_native")
    refused = send(hub, body)
    assert refused.json()["code"] == "email_key_store_not_native", refused.text
    assert wire.requests == [] and egress_ops(hub) == [] and history(hub, update) == []
    assert all(r["state"] == "prepared" for r in sends(hub))
    assert (_send_op(hub)["state"], _send_op(hub)["outcome"]) == ("refused", "email_key_store_not_native")


def test_c5_a_missing_key_refuses_by_name_and_the_check_says_so(hub: Hub, wire: Wire, store: Any) -> None:
    update, dest = ready(hub)
    checked = hub.client.post(f"/api/channels/destinations/{dest}/check").json()
    assert checked["check"]["state"] == "ready"
    store.values.clear()
    assert hub.client.post(f"/api/channels/destinations/{dest}/check").json()["check"]["state"] == "email_key_missing"
    refused = send(hub, press(hub, "inline", update, dest, "c5-missing"))
    assert refused.json()["code"] == "email_key_missing" and wire.requests == []


def test_c5_the_key_is_held_never_an_argument_and_the_owner_alone_saves_it(hub: Hub, store: Any) -> None:
    saved = save_key(hub)
    assert saved.status_code == 200, saved.text
    assert {k: saved.json()[k] for k in ("key_ref", "provider", "saved")} == {
        "key_ref": "sendgrid", "provider": "sendgrid", "saved": True}
    assert store.values == {"sendgrid:sendgrid": KEY}  # PHILO-10-07: the slot is <provider>:<key_ref>
    assert KEY_MARK not in saved.text
    assert KEY_MARK not in dump(hub)
    [operation] = ops(hub, "channel.save_email_key")
    assert (operation["state"], operation["principal_kind"]) == ("succeeded", "owner")
    bad = hub.client.put("/api/channels/email-keys/sendgrid", json={"api_key": "two words"})
    assert bad.json()["code"] == "email_key_invalid" and KEY_MARK not in bad.text
    assert "channel.save_email_key" not in {t["name"] for t in hub.client.post("/api/mcp", json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/list"}).json()["result"]["tools"]}


# ── the destination freezes the sender ─────────────────────────────────────


def test_the_destination_freezes_the_sender_and_refuses_bad_addresses_by_name(hub: Hub, wire: Wire) -> None:
    assert save_key(hub).status_code == 200
    dest = email_destination(hub)
    [view] = [d for d in hub.client.get("/api/channels/destinations").json()["destinations"] if d["id"] == dest]
    assert view["badge"] == "cloud"
    assert view["account"] == {"provider": "sendgrid", "from_email": "karol@example.com", "from_name": "Karol",
                               "key_ref": "sendgrid"}
    assert view["target"] == {"to": ["Priya Raman <priya@example.com>"], "cc": ["lead@example.com"]}
    for extra, code in [({"provider": "postmark"}, "email_provider_unknown"),
                        ({"to": ["not an address"]}, "email_address_invalid"),
                        ({"to": []}, "email_recipients_missing"),
                        ({"to": [f"p{i}@example.com" for i in range(15)], "cc": [f"c{i}@example.com" for i in range(6)]}, "email_recipients_too_many"),
                        ({"cc": ["priya@example.com"]}, "email_recipient_duplicate"),
                        ({"key_ref": "has space"}, "email_key_ref_invalid")]:
        resp = hub.client.post("/api/channels/destinations", json={
            "name": "x", "channel": "email", "provider": "sendgrid", "from_email": "karol@example.com",
            "to": ["priya@example.com"], **extra})
        assert resp.json()["code"] == code, (extra, resp.text)


def test_an_edited_sender_parks_the_destination_and_refuses_the_prepared_send(hub: Hub, wire: Wire) -> None:
    update, dest = ready(hub)
    prepared = prepare(hub, update, dest)["send"]
    edited = hub.client.post("/api/channels/destinations", json={
        "name": "Priya by email", "channel": "email", "provider": "sendgrid", "from_email": "other@example.com",
        "to": ["priya@example.com"], "replaces": dest})
    assert edited.status_code == 200
    refused = send(hub, {"send_id": prepared["id"]})
    assert refused.json()["code"] == "destination_parked" and wire.requests == []


def test_a_request_over_the_size_limit_is_refused_by_name(hub: Hub, wire: Wire) -> None:
    update, dest = ready(hub, body="x" * 1_000_001)
    refused = hub.client.post("/api/channels/sends", json={"document_ref": f"project_update:{update}", "destination_id": dest})
    assert refused.json()["code"] == "payload_too_large:email" and wire.requests == []


# ── 6: a second provider is one class and one table row ────────────────────


class PostmarkLikeProvider:
    """A TEST provider modelled on Postmark's contract, materially different from SendGrid's:
    its own request shape, its own auth header (``X-Postmark-Server-Token``, no Bearer), and its
    acceptance id in the JSON BODY (``MessageID``), not in a header. One class and one row."""

    name = "postmarklike"
    host = "api.postmark.test"
    port = 443

    def __init__(self) -> None:
        from holdspeak.services.channel_email import EmailLimits

        self.limits = EmailLimits(max_bytes=10_000, max_recipients=5)

    def serialize(self, message: Any) -> bytes:
        return json.dumps({"From": message.from_email, "To": ",".join(message.to), "Subject": message.subject,
                           "TextBody": message.text}, separators=(",", ":")).encode()

    def preview(self, body: bytes) -> dict[str, Any]:
        data = json.loads(body)
        return {"from": data["From"], "to": data["To"].split(","), "cc": [], "subject": data["Subject"],
                "text": data["TextBody"]}

    def plan(self, body: bytes) -> Any:
        from holdspeak.plugins.gated_connector import GatedOperation
        from holdspeak.services.channel_email import EmailRequest

        return GatedOperation.outbound(self.host, self.port, request=EmailRequest(f"https://{self.host}/email", body))

    @staticmethod
    def auth_headers(key: str) -> dict[str, str]:
        return {"X-Postmark-Server-Token": key, "Accept": "application/json"}

    def interpret(self, status: int, headers: Any, body: bytes) -> Any:
        from holdspeak.services.channel_contract import Outcome

        try:
            data = json.loads(body or b"{}")
        except ValueError:
            data = {}
        if status == 200 and data.get("ErrorCode") == 0 and data.get("MessageID"):
            return Outcome("sent", None, {"provider": self.name, "message_id": data["MessageID"]})
        return Outcome("unknown", f"unpinned_{status}")


def test_c6_a_materially_different_provider_plugs_in_with_one_class_and_one_row(
    hub: Hub, wire: Wire, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from holdspeak.services import channel_email

    monkeypatch.setitem(channel_email.EMAIL_PROVIDERS, "postmarklike", PostmarkLikeProvider())
    wire.default = response(200, {"Content-Type": "application/json"},
                            json.dumps({"ErrorCode": 0, "Message": "OK", "MessageID": "pm-0a1b"}).encode())
    assert save_key(hub, key_ref="postmarklike", provider="postmarklike").status_code == 200
    _pid, update = room(hub, body="Through a second provider.")
    dest = email_destination(hub, provider="postmarklike", key_ref="postmarklike", cc=[])
    result = send(hub, press(hub, "send_id", update, dest, "c6")).json()
    assert result["outcome"] == "sent" and result["send"]["proof"] == {"provider": "postmarklike",
                                                                       "message_id": "pm-0a1b"}
    assert result["send"]["preview"]["text"] == "Through a second provider."
    [sent] = wire.requests
    assert sent["host"] == "api.postmark.test" and json.loads(sent["body"])["TextBody"] == "Through a second provider."
    # Its OWN authentication: the token header, and no Bearer Authorization at all.
    assert sent["headers"]["X-postmark-server-token"] == KEY and "Authorization" not in sent["headers"]
    [child] = egress_ops(hub)
    full = native(hub, child["operation_id"])["canonical"]
    assert (full["destination"], full["data_classes"]) == ("api.postmark.test:443", ["email_message"])
    assert full["payload_digest"] == "sha256:" + result["send"]["payload_digest"]


# ── 7: Resend, the second provider (PHILO-10-07) ───────────────────────────

RESEND_KEY = "re_syntheticRESEND9d2f0000.neverLeavesTheOpener"
RESEND_MARK = "syntheticRESEND9d2f"
RESEND_ID = "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"
DOMAIN_403 = "The example.com domain is not verified. Please, add and verify your domain on https://resend.com/domains"
TESTING_403 = ("You can only send testing emails to your own email address (karol@example.com). To send emails to "
               "other recipients, please verify a domain at resend.com/domains")


def resend_ok(message_id: str = RESEND_ID) -> Callable[[Any], Any]:
    return response(200, {"Content-Type": "application/json"}, json.dumps({"id": message_id}).encode())


def resend_error(status: int, name: str, message: str) -> Callable[[Any], Any]:
    """Resend's error body: ``{statusCode, name, message}`` (resend.com/docs/api-reference/errors)."""
    return response(status, {"Content-Type": "application/json"},
                    json.dumps({"statusCode": status, "name": name, "message": message}).encode())


def resend_ready(hub: Hub, wire: Wire, *, body: str = f"Cutover is green. {SENTINEL}", **extra: Any) -> tuple[str, str]:
    wire.default = resend_ok()
    assert save_key(hub, RESEND_KEY, key_ref="resend", provider="resend").status_code == 200
    _pid, update = room(hub, body=body)
    return update, email_destination(hub, provider="resend", key_ref="resend", **extra)


def test_c7_resend_sends_its_exact_request_and_its_id_is_the_acceptance(hub: Hub, wire: Wire) -> None:
    update, dest = resend_ready(hub, wire)
    result = send(hub, press(hub, "send_id", update, dest, "c7-wire")).json()
    [row] = [r for r in sends(hub) if r["state"] != "prepared"]
    frozen = bytes(row["payload"])
    [sent] = wire.requests
    # The request, byte for byte: POST https://api.resend.com/emails, Bearer key, a User-Agent, text only.
    assert (sent["host"], sent["url"]) == ("api.resend.com", "https://api.resend.com/emails")
    assert sent["body"] == frozen
    assert frozen == json.dumps({"from": "Karol <karol@example.com>", "to": ["Priya Raman <priya@example.com>"],
                                 "cc": ["lead@example.com"], "subject": json.loads(frozen)["subject"],
                                 "text": f"Cutover is green. {SENTINEL}"},
                                ensure_ascii=False, separators=(",", ":")).encode()
    assert sent["headers"]["Authorization"] == f"Bearer {RESEND_KEY}"
    assert sent["headers"]["User-agent"] == "HoldSpeak"
    assert sent["headers"]["Content-type"] == "application/json"
    assert "html" not in json.loads(frozen)
    # The id in Resend's JSON body is the proof; the word names Resend; accepted, never "delivered".
    assert result["outcome"] == "sent"
    assert result["send"]["proof"] == {"provider": "resend", "message_id": RESEND_ID, "word": "ACCEPTED BY RESEND",
                                       "scope": "accepted for processing, not delivery"}
    assert result["send"]["preview"] == {"from": "Karol <karol@example.com>",
                                         "to": ["Priya Raman <priya@example.com>"], "cc": ["lead@example.com"],
                                         "subject": json.loads(frozen)["subject"],
                                         "text": f"Cutover is green. {SENTINEL}"}
    # One external.egress child to the Resend host, the frozen digest admitted.
    [child] = egress_ops(hub)
    full = native(hub, child["operation_id"])["canonical"]
    assert (full["destination"], full["data_classes"]) == ("api.resend.com:443", ["email_message"])
    assert full["payload_digest"] == "sha256:" + row["payload_digest"]
    assert {f"destination:{dest}", "egress:api.resend.com:443"} <= journal_refs(hub, child["operation_id"])


def test_c7_a_sender_name_is_kept_as_typed_and_quoted_when_it_must_be() -> None:
    from holdspeak.services.channel_email import EmailMessage, ResendProvider

    chosen = ResendProvider()
    body = chosen.serialize(EmailMessage(from_email="k@example.com", from_name="Karol Ś, Jr", to=("a@example.com",),
                                         cc=(), subject="S", text="T"))
    assert json.loads(body) == {"from": '"Karol Ś, Jr" <k@example.com>', "to": ["a@example.com"], "subject": "S",
                                "text": "T"}
    assert chosen.preview(body)["from"] == '"Karol Ś, Jr" <k@example.com>'


RESEND_OUTCOMES = [
    ("accepted", resend_ok(), "sent", None),
    ("accepted-no-id", response(200, {"Content-Type": "application/json"}, b"{}"), "unknown",
     "accepted_without_message_id"),
    ("accepted-not-json", response(200, {}, b"ok"), "unknown", "accepted_without_message_id"),
    ("400-validation", resend_error(400, "validation_error", "Invalid `to` field."), "failed",
     "resend_invalid_request"),
    ("401-missing-key", resend_error(401, "missing_api_key", "Missing API key in the authorization header."),
     "failed", "resend_key_invalid"),
    ("403-invalid-key", resend_error(403, "invalid_api_key", "API key is invalid"), "failed", "resend_key_invalid"),
    ("403-restricted", resend_error(403, "restricted_api_key", "API key is not active"), "failed",
     "resend_key_invalid"),
    ("403-suspended", resend_error(403, "suspended_api_key", "This API key is suspended"), "failed",
     "resend_key_invalid"),
    ("403-domain", resend_error(403, "validation_error", DOMAIN_403), "failed", "sender_not_verified"),
    ("403-testing", resend_error(403, "validation_error", TESTING_403), "failed", "sender_not_verified"),
    ("403-other", resend_error(403, "invalid_permission", "Access token is missing required scopes."), "failed",
     "resend_forbidden"),
    ("422-missing", resend_error(422, "missing_required_field", "The request body is missing one or more required "
                                                                "fields."), "failed", "resend_invalid_request"),
    ("422-validation", resend_error(422, "validation_error", "Invalid `from` field."), "failed",
     "resend_invalid_request"),
    ("429-rate", resend_error(429, "rate_limit_exceeded", "Too many requests."), "failed", "resend_rate_limited"),
    ("429-daily", resend_error(429, "daily_quota_exceeded", "You have exceeded your daily email sending quota."),
     "failed", "resend_quota_exceeded"),
    ("429-monthly", resend_error(429, "monthly_quota_exceeded", "monthly quota"), "failed", "resend_quota_exceeded"),
    ("403-not-resend", response(403, {"Content-Type": "text/html"}, b"<html>cloudflare</html>"), "unknown",
     "unpinned_403"),
    ("409-unpinned-name", resend_error(409, "concurrent_idempotent_requests", "in progress"), "unknown",
     "unpinned_409"),
    ("500", resend_error(500, "application_error", "An unexpected error occurred."), "unknown", "unpinned_500"),
    ("503", resend_error(503, "service_unavailable", "API is temporarily unavailable"), "unknown", "unpinned_503"),
    ("timeout", raising(socket.timeout("timed out")), "unknown", "timeout"),
    ("refused", raising(urllib.error.URLError(ConnectionRefusedError("refused"))), "failed", "connect_refused"),
    ("redirect", response(302, {"Location": "https://evil.example/steal"}), "unknown", "redirect_refused"),
    ("redirect-308", response(308, {"Location": "https://api.resend.com.evil.example/"}), "unknown",
     "redirect_refused"),
]


@pytest.mark.parametrize("case,answer,state,reason", RESEND_OUTCOMES, ids=[c[0] for c in RESEND_OUTCOMES])
def test_c7_each_resend_answer_settles_by_the_pinned_list(
    hub: Hub, wire: Wire, case: str, answer: Any, state: str, reason: Optional[str],
) -> None:
    update, dest = resend_ready(hub, wire)
    wire.script = [answer]
    reply = send(hub, press(hub, "inline", update, dest, f"c7-{case}"))
    assert reply.status_code == 200, reply.text
    result = reply.json()
    assert (result["outcome"], result["send"]["reason"]) == (state, reason), result["send"]
    assert result["receipt"]["state"] == KERNEL[state]
    # Redirects are NOT followed: one request, to Resend only.
    assert [r["host"] for r in wire.requests] == ["api.resend.com"]
    read_back = hub.client.get(f"/api/channels/sends?send_id={result['send']['id']}").json()["sends"][0]
    assert (read_back["state"], read_back["reason"]) == (state, reason)
    if state == "sent":
        assert read_back["proof"]["word"] == "ACCEPTED BY RESEND"


def test_c7_resends_error_that_echoes_the_key_and_the_body_leaves_neither(
    hub: Hub, wire: Wire, caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("DEBUG")
    update, dest = resend_ready(hub, wire)
    wire.script = [resend_error(422, "validation_error", f"bad text near '{SENTINEL}' with {RESEND_KEY}"),
                   raising(RuntimeError(f"socket said: Authorization: Bearer {RESEND_KEY} {SENTINEL}"))]
    failed = send(hub, press(hub, "send_id", update, dest, "c7-echo-a")).json()
    lost = send(hub, press(hub, "send_id", update, dest, "c7-echo-b")).json()
    assert (failed["send"]["reason"], lost["send"]["reason"]) == ("resend_invalid_request", "transport_error")
    assert "[redacted]" in failed["send"]["proof"]["error"]
    places = {"errors and receipts": json.dumps([[a["receipt"], a["send"]["reason"], a["send"]["proof"]]
                                                 for a in (failed, lost)]), "logs": caplog.text,
              "database": dump(hub, skip=(("channel_sends", "payload"),), only=BODY_FREE)}
    for where, text in places.items():
        assert RESEND_MARK not in text, where
        assert SENTINEL not in text, where
    assert RESEND_MARK not in dump(hub) and RESEND_MARK not in json.dumps([failed, lost])


def test_c7_each_provider_has_its_own_key_slot_and_one_key_never_reaches_the_other(
    hub: Hub, wire: Wire, store: Any,
) -> None:
    # The same key name for both providers: two slots, two keys.
    assert save_key(hub, KEY, key_ref="work", provider="sendgrid").status_code == 200
    assert save_key(hub, RESEND_KEY, key_ref="work", provider="resend").status_code == 200
    assert store.values == {"sendgrid:work": KEY, "resend:work": RESEND_KEY}
    _pid, update = room(hub, body="Two providers.")
    by_sendgrid = email_destination(hub, key_ref="work")
    by_resend = email_destination(hub, provider="resend", key_ref="work", name="Priya by Resend")
    wire.script = [response(202, {"X-Message-Id": "sg-msg-0001"}), resend_ok()]
    first = send(hub, press(hub, "inline", update, by_sendgrid, "c7-slot-a")).json()
    second = send(hub, press(hub, "inline", update, by_resend, "c7-slot-b")).json()
    assert (first["outcome"], second["outcome"]) == ("sent", "sent")
    assert [(r["host"], r["headers"]["Authorization"]) for r in wire.requests] == [
        ("api.sendgrid.com", f"Bearer {KEY}"), ("api.resend.com", f"Bearer {RESEND_KEY}")]
    # A key saved for SendGrid only: a Resend destination that names it is refused; nothing leaves.
    assert save_key(hub, KEY, key_ref="sg-only", provider="sendgrid").status_code == 200
    stray = email_destination(hub, provider="resend", key_ref="sg-only", name="Stray")
    assert hub.client.post(f"/api/channels/destinations/{stray}/check").json()["check"]["state"] == "email_key_missing"
    refused = send(hub, press(hub, "inline", update, stray, "c7-slot-c"))
    assert refused.json()["code"] == "email_key_missing" and len(wire.requests) == 2


def test_philo15_resend_is_the_default_provider_and_sendgrid_stays_selectable(hub: Hub, store: Any) -> None:
    """PHILO-15 04 (gap 13): a key save and a destination that name no provider take Resend."""
    saved = hub.client.put("/api/channels/email-keys/resend", json={"api_key": RESEND_KEY})
    assert saved.status_code == 200 and saved.json()["provider"] == "resend"
    assert store.values == {"resend:resend": RESEND_KEY}
    resp = hub.client.post("/api/channels/destinations", json={
        "name": "Priya by email", "channel": "email", "from_email": "karol@example.com",
        "to": ["priya@example.com"]})
    assert resp.status_code == 200, resp.text
    assert resp.json()["destination"]["account"]["provider"] == "resend"
    assert resp.json()["destination"]["account"]["key_ref"] == "resend"
    # SendGrid is still one name away.
    assert save_key(hub, KEY, key_ref="sg", provider="sendgrid").json()["provider"] == "sendgrid"
    picked = email_destination(hub, key_ref="sg", name="By SendGrid")
    [view] = [d for d in hub.client.get("/api/channels/destinations").json()["destinations"] if d["id"] == picked]
    assert view["account"]["provider"] == "sendgrid"


def test_c7_the_check_reads_the_answer_of_its_own_provider_only(hub: Hub, wire: Wire) -> None:
    """B11: a Resend 403 for a sender does not speak for the SendGrid destination of that sender."""
    update, by_resend = resend_ready(hub, wire)
    assert save_key(hub).status_code == 200
    by_sendgrid = email_destination(hub, name="Priya by SendGrid")
    wire.script = [resend_error(403, "validation_error", DOMAIN_403)]
    assert send(hub, press(hub, "inline", update, by_resend, "c7-b11")).json()["send"]["reason"] == "sender_not_verified"

    def check(dest: str) -> str:
        return hub.client.post(f"/api/channels/destinations/{dest}/check").json()["check"]["state"]

    assert (check(by_resend), check(by_sendgrid)) == ("sender_not_verified", "ready")
    # The Resend key saved again after that answer: the answer no longer speaks for it.
    assert save_key(hub, RESEND_KEY, key_ref="resend", provider="resend").status_code == 200
    assert (check(by_resend), check(by_sendgrid)) == ("key_changed", "ready")


def raw_json(status: int, body: Any) -> Callable[[Any], Any]:
    return response(status, {"Content-Type": "application/json"}, json.dumps(body).encode())


#: Codex Astra r1 on #701 (P1): an answer that is not Resend's whole, consistent error envelope never
#: claims FAILED ("NOTHING SENT"). Red at 1ac9a5f3: the first three settled failed.
ENVELOPE_PROBES = [
    ("403-unpinned-name", raw_json(403, {"name": "edge_error"}), "unpinned_403"),
    ("429-status-mismatch", raw_json(429, {"statusCode": 500, "name": "rate_limit_exceeded",
                                           "message": "Too many requests."}), "unpinned_429"),
    ("403-object-message", raw_json(403, {"statusCode": 403, "name": "validation_error",
                                          "message": {"text": DOMAIN_403}}), "unpinned_403"),
    ("403-no-status", raw_json(403, {"name": "validation_error", "message": DOMAIN_403}), "unpinned_403"),
    ("403-status-string", raw_json(403, {"statusCode": "403", "name": "invalid_api_key", "message": "x"}),
     "unpinned_403"),
    ("403-status-bool", raw_json(403, {"statusCode": True, "name": "invalid_api_key", "message": "x"}),
     "unpinned_403"),
    ("403-no-message", raw_json(403, {"statusCode": 403, "name": "invalid_api_key"}), "unpinned_403"),
    ("403-name-not-string", raw_json(403, {"statusCode": 403, "name": ["invalid_api_key"], "message": "x"}),
     "unpinned_403"),
    ("403-unknown-name", resend_error(403, "edge_error", "blocked"), "unpinned_403"),
    ("422-name-of-another-status", resend_error(422, "rate_limit_exceeded", "x"), "unpinned_422"),
    ("400-array-body", raw_json(400, [{"statusCode": 400, "name": "validation_error", "message": "x"}]),
     "unpinned_400"),
]


@pytest.mark.parametrize("case,answer,reason", ENVELOPE_PROBES, ids=[c[0] for c in ENVELOPE_PROBES])
def test_c7_r1_an_answer_that_is_not_resends_consistent_envelope_is_unknown_never_failed(
    hub: Hub, wire: Wire, case: str, answer: Any, reason: str,
) -> None:
    """Through the real save -> prepare -> send routes (the probe Codex ran), not only interpret()."""
    update, dest = resend_ready(hub, wire)
    wire.script = [answer]
    prepared = prepare(hub, update, dest)["send"]
    reply = send(hub, {"send_id": prepared["id"], "command_id": f"c7-r1-{case}"})
    assert reply.status_code == 200, reply.text
    result = reply.json()
    assert (result["outcome"], result["send"]["reason"]) == ("unknown", reason), result["send"]
    assert result["receipt"]["state"] == "indeterminate"
    read_back = hub.client.get(f"/api/channels/sends?send_id={prepared['id']}").json()["sends"][0]
    assert (read_back["state"], read_back["reason"]) == ("unknown", reason)
    assert [r["outcome"] for r in history(hub, update)] == ["unknown"]  # never "nothing sent"


def test_c7_resend_is_one_class_and_one_row() -> None:
    from holdspeak.services import channel_email

    assert list(channel_email.EMAIL_PROVIDERS) == ["sendgrid", "resend"]
    chosen = channel_email.EMAIL_PROVIDERS["resend"]
    assert isinstance(chosen, channel_email.ResendProvider)
    assert (chosen.host, chosen.url, chosen.limits.max_recipients) == (
        "api.resend.com", "https://api.resend.com/emails", 50)
    assert channel_email._manifest(chosen).allowed_hosts == ("api.resend.com",)


# ── r2 (Codex Astra r1 on #696): the REAL HTTPS edge over an offline socket ──


class OfflineSocket:
    """A connected socket with no network: records every write; can fail on the Nth write."""

    def __init__(self, fail_on_write: int = 0, reply: bytes = b"") -> None:
        self.writes: list[bytes] = []
        self.fail_on_write = fail_on_write
        self.reply = reply or (b"HTTP/1.1 202 Accepted\r\nX-Message-Id: sg-offline-1\r\n"
                               b"Content-Length: 0\r\nConnection: close\r\n\r\n")

    def sendall(self, data: Any) -> None:
        self.writes.append(bytes(data))
        if self.fail_on_write and len(self.writes) == self.fail_on_write:
            import ssl

            raise ssl.SSLEOFError(8, f"TLS failed during the write; Bearer {KEY} {SENTINEL}")

    def makefile(self, mode: str) -> Any:
        return io.BytesIO(self.reply)

    def close(self) -> None:
        pass


@pytest.fixture
def real_edge(monkeypatch: pytest.MonkeyPatch) -> Callable[..., Any]:
    """The production edge (``QuietHTTPSHandler``) with ``connect`` replaced: no DNS, no TCP, no TLS."""
    from holdspeak.services import channel_email

    # (At 0a965dbf, before r2, the production edge was urllib's own HTTPSHandler: the red run uses it.)
    monkeypatch.setattr(channel_email, "HTTPS_HANDLER",
                        getattr(channel_email, "QuietHTTPSHandler", urllib.request.HTTPSHandler))
    made: list[OfflineSocket] = []

    def use(connect_error: Optional[BaseException] = None, **socket_kw: Any) -> list[OfflineSocket]:
        def connect(connection: Any) -> None:
            if connect_error is not None:
                raise connect_error
            made.append(OfflineSocket(**socket_kw))
            connection.sock = made[-1]

        monkeypatch.setattr(http.client.HTTPSConnection, "connect", connect)
        return made

    return use


def test_r2_global_http_debug_on_prints_no_key_and_no_body(
    hub: Hub, real_edge: Any, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str],
) -> None:
    """Red at 0a965dbf: ``_opener()`` inherited ``HTTPConnection.debuglevel`` and printed the header."""
    made = real_edge()
    monkeypatch.setattr(http.client.HTTPConnection, "debuglevel", 1)
    update, dest = ready(hub)
    result = send(hub, press(hub, "inline", update, dest, "r2-debug")).json()
    printed = capfd.readouterr()
    assert result["outcome"] == "sent" and result["send"]["proof"]["message_id"] == "sg-offline-1"
    wire_bytes = b"".join(made[0].writes)
    assert f"Authorization: Bearer {KEY}".encode() in wire_bytes and SENTINEL.encode() in wire_bytes
    for stream in (printed.out, printed.err):
        assert KEY_MARK not in stream and SENTINEL not in stream
    assert http.client.HTTPConnection.debuglevel == 1  # the global is never changed


@pytest.mark.parametrize("case,connect_error,fail_on_write,state,reason", [
    ("tls-during-the-body-write", None, 2, "unknown", "tls_failed"),
    ("tls-during-the-header-write", None, 1, "unknown", "tls_failed"),
    ("tls-handshake", "ssl", 0, "failed", "tls_failed"),
    ("connection-refused", "refused", 0, "failed", "connect_refused"),
    ("dns", "dns", 0, "failed", "dns_failed"),
], ids=lambda v: v if isinstance(v, str) else None)
def test_r2_a_failure_is_failed_only_when_no_byte_was_written(
    hub: Hub, real_edge: Any, case: str, connect_error: Optional[str], fail_on_write: int, state: str, reason: str,
) -> None:
    """Red at 0a965dbf: a TLS failure during ``sendall(body)`` settled ``failed / tls_failed``."""
    import ssl

    error = {"ssl": ssl.SSLError(1, "handshake failed"), "refused": ConnectionRefusedError(61, "refused"),
             "dns": socket.gaierror(8, "no such host"), None: None}[connect_error]
    made = real_edge(connect_error=error, fail_on_write=fail_on_write)
    update, dest = ready(hub)
    result = send(hub, press(hub, "send_id", update, dest, f"r2-{case}")).json()
    assert (result["outcome"], result["send"]["reason"]) == (state, reason), result["send"]
    assert (len(made[0].writes) if made else 0) == fail_on_write
    assert [r["outcome"] for r in history(hub, update)] == ([] if state == "failed" else ["unknown"])


# ── R3: a REAL hub restart during an email send (a process killed with SIGKILL) ──

_CHILD = r'''
import json, sys, threading, time, urllib.request, urllib.response, http.client, io
from unittest.mock import MagicMock
import keyring
from holdspeak.services import channel_email
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

token, hold, wire_log, key = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
memory = channel_email.MemoryEmailKeyStore()
memory.put("sendgrid:sendgrid", key)
channel_email.KEY_STORE = lambda: memory
keyring.get_keyring = lambda: (_ for _ in ()).throw(AssertionError("real keychain"))
forever = threading.Event()

class Canned(urllib.request.BaseHandler):
    def https_open(self, req):
        if hold == "before":
            forever.wait()
        with open(wire_log, "a") as log:
            log.write(json.dumps({"host": req.host, "sha": __import__("hashlib").sha256(req.data).hexdigest()}) + "\n")
        if hold == "after":
            forever.wait()
        if hold == "slow":  # a SendGrid answer that takes 1.5 s
            time.sleep(1.5)
        raw = http.client.parse_headers(io.BytesIO(b"X-Message-Id: sg-restart\r\n\r\n"))
        resp = urllib.response.addinfourl(io.BytesIO(b""), raw, req.full_url, 202)
        resp.msg = "canned"
        return resp

channel_email.HTTPS_HANDLER = Canned
if hold == "slowkey":  # a keychain read that waits 1.5 s (the owner's unlock prompt)
    real_get = memory.get

    def slow_get(ref):
        with open(wire_log, "a") as log:
            log.write("keychain read started\n")
        time.sleep(1.5)
        return real_get(ref)

    memory.get = slow_get
server = MeetingWebServer(
    WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(), get_state=MagicMock(return_value={})),
    auth_token=token,
)
print("URL " + server.start(), flush=True)
while True:
    time.sleep(1)
'''


class _EmailHub:
    TOKEN = "philo10-03-restart-token"

    def __init__(self, home: Path, hold: str, wire_log: Path) -> None:
        import os
        import subprocess

        env = dict(os.environ, HOME=str(home))
        env.pop("HOLDSPEAK_ALLOW_REAL_HOME", None)
        self.proc = subprocess.Popen([sys.executable, "-c", _CHILD, self.TOKEN, hold, str(wire_log), KEY],
                                     cwd=str(Path(__file__).resolve().parents[2]), env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        lines: list[str] = []
        for line in self.proc.stdout:  # type: ignore[union-attr]
            lines.append(line)
            if line.startswith("URL "):
                self.url = line.split(" ", 1)[1].strip().rstrip("/")
                break
        else:  # pragma: no cover - the child died before serving
            raise AssertionError("the hub process never served:\n" + "".join(lines[-40:]))
        threading.Thread(target=lambda: [None for _ in self.proc.stdout], daemon=True).start()  # type: ignore[union-attr]

    def call(self, method: str, path: str, body: Any = None, timeout: float = 60) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(self.url + path, data=data, method=method, headers={
            "Authorization": f"Bearer {self.TOKEN}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.status, json.loads(resp.read() or b"null")
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read() or b"null")

    def kill(self) -> None:
        import signal

        self.proc.send_signal(signal.SIGKILL)
        self.proc.wait(timeout=30)


def _rows(home: Path, sql: str, *args: Any) -> list[dict[str, Any]]:
    import sqlite3

    conn = sqlite3.connect(str(home / ".local" / "share" / "holdspeak" / "holdspeak.db"))
    conn.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def _until(check: Callable[[], Any], timeout: float = 30.0) -> Any:
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("condition never held")


@pytest.mark.timeout(240)
@pytest.mark.parametrize("hold", ["before", "after"], ids=["killed-before-the-wire", "killed-after-the-wire"])
def test_c2_r3_a_restart_during_an_email_send_ends_unknown_once_and_never_sends_again(
    tmp_path: Path, hold: str,
) -> None:
    home, wire_log = tmp_path / "home", tmp_path / "wire.jsonl"
    home.mkdir()
    first = _EmailHub(home, hold, wire_log)
    try:
        assert first.call("PUT", "/api/channels/email-keys/sendgrid", {"api_key": KEY, "provider": "sendgrid"})[0] == 200
        _s, made = first.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        _s, drafted = first.call("POST", f"/api/projects/{made['project']['id']}/updates/draft", {})
        update = drafted["update"]["id"]
        assert first.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        status, saved = first.call("POST", "/api/channels/destinations", {
            "name": "Priya by email", "channel": "email", "provider": "sendgrid", "from_email": "karol@example.com",
            "to": ["priya@example.com"]})
        assert status == 200, saved
        _s, preview = first.call("POST", "/api/channels/preview", {"document_ref": f"project_update:{update}",
                                                                   "destination_id": saved["destination"]["id"]})
        body = {"document_ref": f"project_update:{update}", "destination_id": saved["destination"]["id"],
                "preview_digest": preview["payload_digest"], "command_id": f"restart-{hold}"}

        def pressing() -> None:
            try:
                first.call("POST", "/api/channels/send", body, timeout=120)
            except OSError:  # the process is killed under the caller
                pass

        threading.Thread(target=pressing, daemon=True).start()
        row = _until(lambda: next(iter(_rows(home, "SELECT * FROM channel_sends WHERE state='dispatching'")), None))
        if hold == "after":
            _until(lambda: wire_log.exists() and wire_log.read_text().strip())
    finally:
        first.kill()
    second = _EmailHub(home, "", wire_log)
    try:
        [settled] = _rows(home, "SELECT * FROM channel_sends WHERE id=?", row["id"])
        assert (settled["state"], settled["reason"]) == ("unknown", "interrupted"), settled
        [operation] = _rows(home, "SELECT o.state, r.outcome FROM kernel_operations o JOIN kernel_receipts r"
                                  " ON r.operation_id=o.operation_id WHERE o.operation_id=?", row["send_operation_id"])
        assert operation == {"state": "indeterminate", "outcome": "hub_restart_during_send"}, operation
        assert _rows(home, "SELECT outcome FROM project_update_deliveries WHERE update_id=?", update) == [
            {"outcome": "unknown"}]
        status, replayed = second.call("POST", "/api/channels/send", body)
        assert status == 200 and (replayed["outcome"], replayed["send"]["reason"]) == ("unknown", "interrupted")
        sent_lines = wire_log.read_text().splitlines() if wire_log.exists() else []
        assert len(sent_lines) == (1 if hold == "after" else 0)  # never sent again
        assert len(_rows(home, "SELECT 1 FROM project_update_deliveries WHERE update_id=?", update)) == 1
        for path in home.rglob("*"):
            if path.is_file():
                assert KEY_MARK.encode() not in path.read_bytes(), path
    finally:
        second.kill()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_r3_the_hub_answers_a_read_during_a_slow_email_send(tmp_path: Path, transport: str) -> None:
    """Round three (#695's GATE 2 for email): channel.send is ``blocking_io``, so a 1.5 s SendGrid call
    runs off the event loop and a concurrent read answers at once (a real socket hub process)."""
    import time

    home, wire_log = tmp_path / "home", tmp_path / "wire.jsonl"
    home.mkdir()
    hub = _EmailHub(home, "slow", wire_log)
    try:
        assert hub.call("PUT", "/api/channels/email-keys/sendgrid", {"api_key": KEY, "provider": "sendgrid"})[0] == 200
        _s, made = hub.call("POST", "/api/projects", {"name": "Payments ledger cutover"})
        update = hub.call("POST", f"/api/projects/{made['project']['id']}/updates/draft", {})[1]["update"]["id"]
        assert hub.call("POST", f"/api/updates/{update}/publish", {})[0] == 200
        status, saved = hub.call("POST", "/api/channels/destinations", {
            "name": "Priya by email", "channel": "email", "provider": "sendgrid", "from_email": "karol@example.com",
            "to": ["priya@example.com"]})
        assert status == 200, saved
        _s, prepared = hub.call("POST", "/api/channels/sends", {"document_ref": f"project_update:{update}",
                                                                "destination_id": saved["destination"]["id"]})
        body = {"send_id": prepared["send"]["id"]}

        def pressing() -> Any:
            if transport == "http":
                return hub.call("POST", "/api/channels/send", body)
            return hub.call("POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                                 "params": {"name": "channel.send", "arguments": body}})

        thread, answer = in_thread(pressing)
        _until(lambda: wire_log.exists() and wire_log.read_text().strip())  # the request is on the wire
        started = time.perf_counter()
        status, _listed = hub.call("GET", "/api/channels/destinations")
        read = time.perf_counter() - started
        thread.join(60)
        assert status == 200
        assert answer and answer[0][0] == 200, answer
        if transport == "mcp":
            assert answer[0][1]["result"]["isError"] is False, answer
        assert read < 0.5, f"the read waited {read:.3f} s during the email send"
        [row] = _rows(home, "SELECT state FROM channel_sends WHERE id=?", body["send_id"])
        assert row["state"] == "sent"
    finally:
        hub.kill()


@pytest.mark.timeout(240)
@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_r4_a_slow_keychain_read_in_the_destination_check_never_blocks_the_hub(tmp_path: Path, transport: str) -> None:
    """Codex Astra r2 on #696: channel.check_destination read the keychain on the event loop; an
    unrelated read waited 1.45 s (HTTP) / 1.51 s (MCP). It is ``blocking_io`` now (a real socket hub)."""
    import time

    home, log = tmp_path / "home", tmp_path / "keychain.log"
    home.mkdir()
    hub = _EmailHub(home, "slowkey", log)
    try:
        status, saved = hub.call("POST", "/api/channels/destinations", {
            "name": "Review email", "channel": "email", "provider": "sendgrid", "from_email": "karol@example.com",
            "to": ["review@example.com"]})
        assert status == 200, saved
        dest = saved["destination"]["id"]

        def check() -> Any:
            if transport == "http":
                return hub.call("POST", f"/api/channels/destinations/{dest}/check", {})
            return hub.call("POST", "/api/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
                "name": "channel.check_destination", "arguments": {"destination_id": dest}}})

        thread, answer = in_thread(check)
        _until(lambda: log.exists() and log.read_text().strip())  # the check is inside its keychain read
        started = time.perf_counter()
        status, _listed = hub.call("GET", "/api/channels/destinations")
        read = time.perf_counter() - started
        thread.join(30)
        assert status == 200 and answer and answer[0][0] == 200, answer
        assert read < 0.5, f"{transport}: the read waited {read:.3f} s during the keychain check"
    finally:
        hub.kill()
