"""PHILO-11-02: the Slack channel operations through a real hub.

The source document is made by the project/update producer.  The key store
and HTTPS edge are injected only at the transport seams, so no real keychain
or Slack request is possible.  Every channel operation still crosses the
normal HTTP route, operation registry, kernel admission and send lifecycle.
"""
from __future__ import annotations

import http.client
import io
import json
from pathlib import Path
import socket
import ssl
import sys
from typing import Any, Callable, Optional
import urllib.request
import urllib.response
import urllib.error

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
from _philo10_send import Hub, _boot, ops, room, sends  # noqa: E402
from datetime import datetime
from fastapi.testclient import TestClient
import holdspeak.config as config_module
import holdspeak.plugins.builtin.webhook_post_actuator as webhook_module
from holdspeak.config import Config
from holdspeak.db import Database, get_database, reset_database
from holdspeak.meeting_session import IntelSnapshot, MeetingState
from holdspeak.principals import UNAUTHENTICATED
from holdspeak.services import credential_service, settings_service
from holdspeak.services.settings_service import SettingsService
from holdspeak.slack_export import document_markdown_for
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

URL = "https://hooks.slack.com/services/T000/B000/secret-credential"
URL_MARK = "secret-credential"


def response(status: int, body: bytes = b"ok", headers: Optional[dict[str, str]] = None) -> Callable[[Any], Any]:
    def answer(req: Any) -> Any:
        raw = "".join(f"{k}: {v}\r\n" for k, v in (headers or {}).items()) + "\r\n"
        result = urllib.response.addinfourl(io.BytesIO(body), http.client.parse_headers(io.BytesIO(raw.encode())),
                                            req.full_url, status)
        result.msg = "canned"
        return result
    return answer


def raising(error: BaseException) -> Callable[[Any], Any]:
    def answer(_req: Any) -> Any:
        raise error
    return answer


def egress_rows(hub: Hub) -> list[dict[str, Any]]:
    with hub.db._connection() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT o.*, r.state AS receipt_state FROM kernel_operations o "
            "LEFT JOIN kernel_receipts r ON r.operation_id=o.operation_id "
            "WHERE o.name='external.egress' ORDER BY o.created_at, o.rowid")]


def database_text(hub: Hub) -> str:
    values: list[str] = []
    with hub.db._connection() as conn:
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in tables:
            for row in conn.execute(f"SELECT * FROM '{table}'"):
                values.extend(str(value) for value in row)
    return "\n".join(values)


class Wire:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.script: list[Callable[[Any], Any]] = []
        self.failure: Optional[BaseException] = None
        self.failure_after = False

    def handler(self) -> urllib.request.BaseHandler:
        wire = self

        class Canned(urllib.request.BaseHandler):
            sent_any = False

            def https_open(self, req: Any) -> Any:
                wire.requests.append({"host": req.host, "url": req.full_url,
                                      "headers": dict(req.header_items()), "body": bytes(req.data or b"")})
                if wire.failure is not None:
                    self.sent_any = wire.failure_after
                    raise wire.failure
                try:
                    return (wire.script.pop(0) if wire.script else response(200))(req)
                except BaseException:
                    # A scripted response failure occurs after this edge has
                    # accepted the request bytes (the after-write case).
                    self.sent_any = True
                    raise

        return Canned()


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database
    from holdspeak.runtime import composition
    from holdspeak.services import channel_slack
    import keyring

    memory = channel_slack.MemorySlackKeyStore()
    wire = Wire()
    monkeypatch.setattr(channel_slack, "KEY_STORE", lambda: memory)
    monkeypatch.setattr(channel_slack, "HTTPS_HANDLER", wire.handler)
    monkeypatch.setattr(keyring, "get_keyring", lambda: (_ for _ in ()).throw(
        AssertionError("Slack test reached the real keychain")))
    yielded = _boot(tmp_path, monkeypatch)
    try:
        yield yielded, memory, wire
    finally:
        reset_database()
        composition.install(composition.bare(label="pytest"))


def save_webhook(hub: Hub, url: str = URL) -> str:
    result = hub.client.post("/api/channels/slack-webhooks", json={"webhook_url": url})
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["saved"] is True and body["key_ref"]
    assert URL_MARK not in result.text
    return body["key_ref"]


def slack_destination(hub: Hub, key_ref: str, *, replaces: Optional[str] = None) -> str:
    body: dict[str, Any] = {"name": "Slack leads", "channel": "slack", "key_ref": key_ref,
                            "channel_label": "#leads"}
    if replaces:
        body["replaces"] = replaces
    result = hub.client.post("/api/channels/destinations", json=body)
    assert result.status_code == 200, result.text
    destination = result.json()["destination"]
    assert destination["channel"] == "slack"
    assert destination["account"] == {"key_ref": key_ref}
    assert destination["target"] == {"channel_label": "#leads"}
    assert URL_MARK not in result.text
    return destination["id"]


def _frame(api: Any, destination: str) -> tuple[str, str]:
    """What the sent update adds around its body on Slack (PHILO-15 B53: the
    heading "<Project> · Update · <date>"), read off a real preview."""
    _project, probe = room(api, body="zq")
    text = api.client.post("/api/channels/preview", json={
        "document_ref": f"project_update:{probe}", "destination_id": destination,
    }).json()["preview"]["text"]
    head, _, tail = text.partition("zq")
    assert head.startswith("*Payments ledger cutover · Update · "), text
    return head, tail


def test_save_check_preview_prepare_and_send_use_the_real_slack_producer(
    hub: Any, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str],
) -> None:
    caplog.set_level("DEBUG")
    # replaces: tests/e2e/test_philo11_05b_meeting_faces_glass.py::TestMeetingFacesGlass::test_the_meeting_faces_and_slack_destinations (the hub half: save, check, preview, prepare, send, size refusal)
    api, memory, wire = hub
    key_ref = save_webhook(api)
    assert memory.values == {f"slack:{key_ref}": URL}
    _project, update = room(api, body="# Heading\n\n**bold** and [docs](https://example.test/docs)")
    destination = slack_destination(api, key_ref)

    checked = api.client.post(f"/api/channels/destinations/{destination}/check")
    assert checked.status_code == 200 and checked.json()["check"]["state"] == "ready"
    assert wire.requests == []

    preview = api.client.post("/api/channels/preview", json={
        "document_ref": f"project_update:{update}", "destination_id": destination,
    })
    assert preview.status_code == 200, preview.text
    preview_body = preview.json()
    head, tail = _frame(api, destination)
    from holdspeak.services.document_sources import render_document

    assert preview_body["preview"] == {
        "text": head + "*Heading*\n\n*bold* and <https://example.test/docs|docs>" + tail,
        "markdown": render_document(api.db, f"project_update:{update}").body_md,
    }

    prepared = api.client.post("/api/channels/sends", json={
        "document_ref": f"project_update:{update}", "destination_id": destination,
    })
    assert prepared.status_code == 200, prepared.text
    send_row = prepared.json()["send"]
    frozen = bytes(api.db.channel_sends.get(send_row["id"])["payload"])
    assert json.loads(frozen) == {"text": preview_body["preview"]["text"]}
    assert send_row["payload_digest"] == preview_body["payload_digest"]

    sent = api.client.post("/api/channels/send", json={"send_id": send_row["id"]})
    assert sent.status_code == 200, sent.text
    assert sent.json()["outcome"] == "sent"
    assert sent.json()["send"]["proof"]["word"] == "POSTED"
    assert "link" not in sent.json()["send"]["proof"]
    assert wire.requests[0]["host"] == "hooks.slack.com"
    assert wire.requests[0]["body"] == frozen
    assert URL_MARK not in json.dumps(sent.json())
    assert URL_MARK not in database_text(api)
    assert len(sends(api)) == 1 and len(ops(api, "external.egress")) == 1

    [child] = egress_rows(api)
    send_operation = next(item for item in ops(api) if item["operation_id"] == sent.json()["operation_id"])
    assert child["parent_operation_id"] == send_operation["operation_id"]
    assert (child["principal_kind"], child["principal_identity"]) == (
        send_operation["principal_kind"], send_operation["principal_identity"])
    from holdspeak.kernel.external_egress import LOCAL_OWNER
    from holdspeak.services import project_kernel

    broker = project_kernel._broker(api.db)
    native = broker.read([f"operation:{child['operation_id']}"], "full", "committed", LOCAL_OWNER)["objects"][0]
    assert native["canonical"]["destination"] == "hooks.slack.com:443"
    assert native["canonical"]["data_classes"] == ["slack_message"]
    assert native["canonical"]["payload_digest"] == "sha256:" + send_row["payload_digest"]
    assert URL_MARK not in json.dumps(native)
    assert URL_MARK not in checked.text + preview.text + prepared.text + sent.text
    assert URL_MARK not in caplog.text
    output = capsys.readouterr()
    assert URL_MARK not in output.out + output.err


@pytest.mark.parametrize(
    "label,answer,state,reason",
    [
        ("ok", response(200, b"ok"), "sent", None),
        ("invalid", response(400, b"invalid_payload"), "failed", "invalid_payload"),
        ("prohibited", response(403, b"action_prohibited"), "failed", "action_prohibited"),
        ("missing", response(404, b"channel_not_found"), "failed", "channel_not_found"),
        ("archived", response(410, b"channel_is_archived"), "failed", "channel_is_archived"),
        ("rate_limited", response(429, b"rate_limited", {"Retry-After": "12"}), "failed", "rate_limited"),
        ("rollup", response(500, b"rollup_error"), "unknown", "rollup_error"),
        ("other_5xx", response(503, b"unavailable"), "unknown", "unpinned_503"),
        ("redirect", response(302, b"", {"Location": "https://evil.example/steal"}), "unknown", "redirect_refused"),
        ("wrong_ok", response(200, b"OK"), "unknown", "ack_missing"),
        ("unlisted", response(418, b"teapot"), "unknown", "unpinned_418"),
        ("timeout", raising(socket.timeout(URL)), "unknown", "timeout"),
        ("secret_echo", response(400, URL.encode()), "unknown", "unpinned_400"),
    ],
)
def test_each_slack_outcome_is_interpreted_by_the_real_send(
    hub: Any, label: str, answer: Callable[[Any], Any], state: str, reason: Optional[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("DEBUG")
    api, _memory, wire = hub
    key_ref = save_webhook(api)
    _project, update = room(api, body=f"outcome {label}")
    destination = slack_destination(api, key_ref)
    wire.script = [answer]
    sent = api.client.post("/api/channels/send", json={
        "document_ref": f"project_update:{update}", "destination_id": destination,
        "preview_digest": api.client.post("/api/channels/preview", json={
            "document_ref": f"project_update:{update}", "destination_id": destination,
        }).json()["payload_digest"],
    })
    assert sent.status_code == 200, sent.text
    result = sent.json()
    assert URL_MARK not in sent.text + database_text(api) + caplog.text
    assert (result["outcome"], result["send"]["reason"]) == (state, reason), result
    assert len(wire.requests) == 1 and wire.requests[0]["host"] == "hooks.slack.com"
    if state == "failed":
        assert api.db.channel_sends.get(result["send"]["id"])["state"] == "failed"
    else:
        assert api.db.channel_sends.get(result["send"]["id"])["state"] == state
    if state == "sent":
        assert result["send"]["proof"]["word"] == "POSTED"
        assert "link" not in result["send"]["proof"]


@pytest.mark.parametrize(
    ("status", "answer_body", "headers", "outcome", "reason"),
    [(500, b"rollup_error", {}, "unknown", "rollup_error"),
     (429, b"rate_limited", {"Retry-After": "12"}, "failed", "rate_limited")],
    ids=["unknown", "rate_limited"],
)
def test_unknown_replay_and_rate_limit_never_post_again(
    hub: Any, status: int, answer_body: bytes, headers: dict[str, str], outcome: str, reason: str,
) -> None:
    api, _memory, wire = hub
    key_ref = save_webhook(api)
    _project, update = room(api, body="one press")
    destination = slack_destination(api, key_ref)
    preview = api.client.post("/api/channels/preview", json={
        "document_ref": f"project_update:{update}", "destination_id": destination,
    }).json()
    wire.script = [response(status, answer_body, headers)]
    body = {"document_ref": f"project_update:{update}", "destination_id": destination,
            "preview_digest": preview["payload_digest"], "command_id": "one-press"}
    first = api.client.post("/api/channels/send", json=body).json()
    second = api.client.post("/api/channels/send", json=body).json()
    assert first["outcome"] == second["outcome"] == outcome
    assert first["send"]["reason"] == second["send"]["reason"] == reason
    assert len(wire.requests) == 1


def test_an_agent_cannot_press_slack_send(hub: Any) -> None:
    api, _memory, wire = hub
    key_ref = save_webhook(api)
    _project, update = room(api, body="owner press")
    destination = slack_destination(api, key_ref)
    prepared = api.client.post("/api/channels/sends", json={
        "document_ref": f"project_update:{update}", "destination_id": destination,
    }).json()["send"]
    from test_philo9_steward_admission import _agent

    agent = _agent(api)
    refused = agent.post("/api/channels/send", json={"send_id": prepared["id"]})
    assert refused.status_code == 403 and refused.json()["code"] == "owner_principal_required"
    assert wire.requests == []


@pytest.mark.parametrize(
    ("label", "error", "after", "state", "reason"),
    [
        ("connect_before", urllib.error.URLError(ConnectionRefusedError("refused")), False, "failed", "connect_refused"),
        ("dns_before", urllib.error.URLError(socket.gaierror("dns")), False, "failed", "dns_failed"),
        ("tls_before", urllib.error.URLError(ssl.SSLError("handshake")), False, "failed", "tls_failed"),
        ("timeout_before", socket.timeout("before write"), False, "failed", "timeout"),
        ("tls_after", urllib.error.URLError(ssl.SSLError("dropped after write")), True, "unknown", "tls_failed"),
        ("timeout_after", socket.timeout("after write"), True, "unknown", "timeout"),
    ],
)
def test_transport_failure_records_whether_bytes_may_have_left(
    hub: Any, label: str, error: BaseException, after: bool, state: str, reason: str,
) -> None:
    api, _memory, wire = hub
    key_ref = save_webhook(api)
    _project, update = room(api, body=f"transport {label}")
    destination = slack_destination(api, key_ref)
    preview = api.client.post("/api/channels/preview", json={
        "document_ref": f"project_update:{update}", "destination_id": destination,
    }).json()
    wire.failure = error
    wire.failure_after = after
    sent = api.client.post("/api/channels/send", json={
        "document_ref": f"project_update:{update}", "destination_id": destination,
        "preview_digest": preview["payload_digest"],
    })
    assert sent.status_code == 200, sent.text
    result = sent.json()
    assert (result["outcome"], result["send"]["reason"]) == (state, reason), result
    assert len(wire.requests) == 1 and wire.requests[0]["host"] == "hooks.slack.com"


def test_size_refusal_is_real_and_carries_size_and_limit_before_wire(hub: Any) -> None:
    api, _memory, wire = hub
    key_ref = save_webhook(api)
    destination = slack_destination(api, key_ref)
    head, tail = _frame(api, destination)
    _project, update = room(api, body="x" * (39_001 - len(head) - len(tail)))
    ref = f"project_update:{update}"

    refused = api.client.post("/api/channels/preview", json={
        "document_ref": ref, "destination_id": destination,
    })
    assert refused.status_code == 400
    body = refused.json()
    assert body["code"] == "payload_too_large:slack"
    assert body["size"] == 39_001 and body["limit"] == 39_000

    prepared = api.client.post("/api/channels/sends", json={
        "document_ref": ref, "destination_id": destination,
    })
    assert prepared.status_code == 400, prepared.text
    assert prepared.json()["code"] == "payload_too_large:slack"
    assert prepared.json()["size"] == 39_001 and prepared.json()["limit"] == 39_000

    inline = api.client.post("/api/channels/send", json={
        "document_ref": ref, "destination_id": destination, "preview_digest": "0" * 64,
    })
    assert inline.status_code == 400, inline.text
    assert inline.json()["code"] == "payload_too_large:slack"
    assert inline.json()["size"] == 39_001 and inline.json()["limit"] == 39_000

    is_error, mcp = api.mcp("channel.preview", {"document_ref": ref, "destination_id": destination})
    assert is_error is True
    assert mcp.get("size") == 39_001 and mcp.get("limit") == 39_000
    assert wire.requests == []


def test_slack_size_is_text_characters_in_preview_and_prepared_send(hub: Any) -> None:
    api, _memory, wire = hub
    key_ref = save_webhook(api)
    destination = slack_destination(api, key_ref)
    head, tail = _frame(api, destination)
    fill = "é" * (39_000 - len(head) - len(tail))
    _project, update = room(api, body=fill)
    args = {"document_ref": f"project_update:{update}", "destination_id": destination}
    preview = api.client.post("/api/channels/preview", json=args)
    prepared = api.client.post("/api/channels/sends", json=args)
    assert preview.status_code == prepared.status_code == 200
    assert preview.json()["size"] == prepared.json()["send"]["size"] == 39_000
    frozen = bytes(api.db.channel_sends.get(prepared.json()["send"]["id"])["payload"])
    assert len(frozen) > 39_000
    assert json.loads(frozen)["text"] == preview.json()["preview"]["text"] == head + fill + tail
    assert wire.requests == []


def test_replacing_slack_destination_parks_old_and_old_prepare_refuses(hub: Any) -> None:
    api, _memory, wire = hub
    old_key = save_webhook(api)
    _project, update = room(api, body="replace me")
    old_destination = slack_destination(api, old_key)
    prepared = api.client.post("/api/channels/sends", json={
        "document_ref": f"project_update:{update}", "destination_id": old_destination,
    }).json()["send"]
    new_key = save_webhook(api, "https://hooks.slack.com/services/T000/B000/new-secret")
    new_destination = slack_destination(api, new_key, replaces=old_destination)
    assert new_destination != old_destination
    refused = api.client.post("/api/channels/send", json={"send_id": prepared["id"]})
    assert refused.status_code in {400, 409} and refused.json()["code"] == "destination_parked"
    checked = api.client.post(f"/api/channels/destinations/{old_destination}/check")
    assert checked.status_code == 200 and checked.json()["check"]["state"] == "parked"
    assert wire.requests == []


@pytest.mark.parametrize("url", [
    "http://hooks.slack.com/services/T/B/K",
    "https://slack.com/services/T/B/K",
    "https://hooks.slack.com:8443/services/T/B/K",
    "https://hooks.slack.com/services/T/B/K?secret=leak",
])
def test_invalid_webhook_is_refused_at_save_without_key_or_wire(hub: Any, url: str) -> None:
    api, memory, wire = hub
    refused = api.client.post("/api/channels/slack-webhooks", json={"webhook_url": url})
    assert refused.status_code == 400
    assert refused.json()["code"] == "slack_webhook_invalid"
    assert url not in refused.text
    assert memory.values == {}
    assert wire.requests == []


# ── merged from tests/integration/test_philo11_slack_rewrite.py ──
# PHILO-11-02 fences for retiring the legacy Slack aftercare path.
#
# These checks exercise the real Config, settings serializers, settings writer,
# aftercare route, and desk actuator route.  Slack channel delivery belongs to the
# channel worker; this file only proves that the old Settings webhook path cannot
# still publish or expose its retained config value.


pytest.importorskip("fastapi.testclient")


pytestmark = [pytest.mark.requires_meeting]

SENTINEL = "https://hooks.slack.com/services/SENTINEL/DO-NOT-RETURN"


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", path)
    return path


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    database = get_database(tmp_path / "rewrite.db")
    yield database
    reset_database()


@pytest.fixture
def seeded(db: Database) -> Database:
    db.meetings.save_meeting(
        MeetingState(
            id="m-rewrite",
            started_at=datetime(2026, 9, 30, 10, 0, 0),
            title="Rewrite boundary",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    {
                        "id": "a1",
                        "task": "Keep the channel boundary",
                        "owner": "Astra",
                        "due": "Friday",
                        "status": "pending",
                        "review_state": "accepted",
                        "source_timestamp": None,
                        "created_at": datetime(2026, 9, 30, 10, 0, 0).isoformat(),
                    }
                ],
            ),
        )
    )
    return db


@pytest.fixture
def client(db: Database, settings_path: Path) -> TestClient:
    _ = db
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


def _save_legacy_config(path: Path, *, mode: str = "yolo") -> None:
    config = Config()
    config.control_mode = mode
    config.meeting.slack_webhook_url = SENTINEL
    config.save(path=path)


def test_old_config_loads_but_aftercare_does_not_advertise_slack(
    client: TestClient, settings_path: Path, seeded: Database
) -> None:
    _save_legacy_config(settings_path)

    response = client.get("/api/meetings/m-rewrite/aftercare")

    assert response.status_code == 200
    assert "slack_configured" not in response.json()
    assert SENTINEL not in response.text
    assert Config.load(settings_path).meeting.slack_webhook_url == SENTINEL


def test_settings_read_and_write_keep_the_retained_field_private(
    db: Database, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _save_legacy_config(settings_path, mode="neutral")
    config = Config.load(settings_path)

    # Reproduce the charter red case: removing only the credential registrations
    # leaves the retained Config field exposed by both serializers and writable.
    monkeypatch.delitem(settings_service.SECRET_PATHS, "slack_webhook_url", raising=False)
    monkeypatch.delitem(credential_service.SECRET_PATHS, "slack_webhook_url", raising=False)

    settings_payload = settings_service.redacted_settings(config)
    credential_payload = credential_service.redacted_settings(config)
    assert SENTINEL not in repr(settings_payload)
    assert SENTINEL not in repr(credential_payload)

    assert Config.load(settings_path).meeting.slack_webhook_url == SENTINEL


def test_settings_write_ignores_the_retained_field(
    db: Database, settings_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _save_legacy_config(settings_path, mode="neutral")
    monkeypatch.delitem(settings_service.SECRET_PATHS, "slack_webhook_url", raising=False)
    monkeypatch.delitem(credential_service.SECRET_PATHS, "slack_webhook_url", raising=False)

    before = Config.load(settings_path).meeting.slack_webhook_url
    SettingsService(db).update_settings(
        UNAUTHENTICATED,
        {"meeting": {"slack_webhook_url": "https://hooks.slack.com/services/ATTACKER"}},
    )
    assert Config.load(settings_path).meeting.slack_webhook_url == before


def test_posture_aftercare_route_is_parked_and_never_posts(
    client: TestClient,
    settings_path: Path,
    seeded: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _save_legacy_config(settings_path)
    calls: list[tuple[str, object]] = []

    def fake_post(url: str, body: object, *, timeout: float):
        calls.append((url, body))
        return webhook_module.WebhookResponse(status=200, body="ok")

    monkeypatch.setattr(webhook_module, "_default_post", fake_post)
    response = client.post(
        "/api/meetings/m-rewrite/export/slack", json={"what": "digest"}
    )

    assert response.status_code == 400
    assert response.json() == {"success": False, "error": "slack_moved_to_channel"}
    assert calls == []


def test_meeting_slack_proposal_approval_is_parked_but_rejection_works(
    client: TestClient, db: Database, settings_path: Path, seeded: Database
) -> None:
    _save_legacy_config(settings_path, mode="neutral")
    proposal = db.actuators.record_proposal(
        meeting_id="m-rewrite",
        window_id="m-rewrite:aftercare",
        plugin_id="webhook_post",
        plugin_version="1",
        idempotency_key="legacy-slack-approval-1",
        target="slack",
        action="post_message",
        preview="historical Slack proposal",
        payload={"body": {"text": "historical Slack proposal"}},
        required_capabilities=["actuator"],
        fixed_destination=True,
    )

    approved = client.post(
        f"/api/meetings/m-rewrite/proposals/{proposal.id}/decision",
        json={"decision": "approved", "decided_by": "owner"},
    )
    assert approved.status_code == 400
    assert approved.json() == {"success": False, "error": "slack_moved_to_channel"}
    assert db.actuators.get_proposal(proposal.id).status == "proposed"

    rejected = client.post(
        f"/api/meetings/m-rewrite/proposals/{proposal.id}/decision",
        json={"decision": "rejected", "decided_by": "owner"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["success"] is True
    assert rejected.json()["proposal"]["status"] == "rejected"


def test_desk_slack_target_is_parked(
    client: TestClient, settings_path: Path, seeded: Database
) -> None:
    _save_legacy_config(settings_path)

    response = client.post(
        "/api/desk/actuators/slack/propose", json={"text": "free text"}
    )

    assert response.status_code == 400
    assert response.json()["error"] == "slack_moved_to_channel"


def test_historical_slack_proposals_remain_readable(
    client: TestClient, db: Database, settings_path: Path, seeded: Database
) -> None:
    _save_legacy_config(settings_path, mode="neutral")
    proposal = db.actuators.record_proposal(
        meeting_id="m-rewrite",
        window_id="m-rewrite:aftercare",
        plugin_id="webhook_post",
        plugin_version="1",
        idempotency_key="legacy-slack-receipt-1",
        target="slack",
        action="post_message",
        preview="historical proposal",
        payload={"body": {"text": "historical proposal"}},
        required_capabilities=["actuator"],
        fixed_destination=True,
    )

    response = client.get("/api/meetings/m-rewrite/proposals")

    assert response.status_code == 200
    rows = response.json()["proposals"]
    assert any(row["id"] == proposal.id for row in rows)
    assert SENTINEL not in response.text

    # Mint the retained historical receipt through its real database lifecycle.
    # This records a past outcome; it invokes no connector or network edge.
    db.actuators.transition_proposal(proposal.id, to_status="approved", actor="historical-owner")
    receipt = db.actuators.transition_proposal(
        proposal.id, to_status="executed", actor="historical-owner",
        result={"status": 200, "body": "ok"},
    )
    history = client.get("/api/meetings/m-rewrite/proposals").json()["proposals"]
    retained = next(row for row in history if row["id"] == proposal.id)
    assert retained["status"] == "executed" and retained["result"] == receipt.result
    assert retained["executed_at"] == receipt.executed_at
    assert db.actuators.last_execution_receipt("slack") == receipt.executed_at


def test_legacy_slack_connector_is_removed() -> None:
    import holdspeak.slack_export as slack_export

    assert not hasattr(slack_export, "build_slack_connector")
    assert document_markdown_for(
        {"meeting_title": "A meeting", "meeting_date": "2026-09-30", "is_empty": False},
        "digest",
    ).startswith("# A meeting")
