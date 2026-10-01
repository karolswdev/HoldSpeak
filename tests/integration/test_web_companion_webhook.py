"""HSM-14 — the iPad desk's generic Webhook connector, grounded in the host actuators.

The generic sibling of the companion Slack path: a companion proposes arbitrary
text to a configured webhook; the host refuses honestly when unconfigured/empty;
the preview is the wire body; nothing egresses before approval; approving runs
through the real gated webhook connector (the URL's host allow-listed, transport
faked) with the URL joined in memory only — never on the proposal, response, or
broadcast; and the companion status reports `webhook_configured` without the URL.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

import holdspeak.config as config_module  # noqa: E402
import holdspeak.plugins.builtin.webhook_post_actuator as webhook_module  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import get_database, reset_database  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402

URL = "https://hooks.example.com/services/secret-hook"
PROPOSE = "/api/desk/actuators/webhook/propose"


@pytest.fixture
def temp_db_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_dir):
    reset_database()
    return get_database(temp_db_dir / "test.db")


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    """HS-139-08: pin posture to neutral so the propose→approve lifecycle
    tests exercise the manual-decision path. Yolo auto-execution is
    covered by the dedicated yolo test."""
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    cfg = Config()
    cfg.control_mode = "neutral"
    cfg.save(path=target)
    return target


def _configure(settings_path, url=URL):
    config = Config.load()
    config.meeting.companion_webhook_url = url
    config.save(path=settings_path)


def _set_control_mode(settings_path, mode):
    config = Config.load()
    config.control_mode = mode
    config.save(path=settings_path)


class _BroadcastSpy:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def __call__(self, message_type, data):
        self.events.append((message_type, data))


@pytest.fixture
def server(db):
    # HS-132-12: the hub composes its services against `get_database()` at app
    # construction, so the temp-database swap must land BEFORE the server is
    # built. Without this the routes write the real user database while the
    # test reads the temp one.
    _ = db
    return MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_a, **_k: None, on_stop=lambda *_a, **_k: None, get_state=lambda: None),
        host="127.0.0.1",
    )


@pytest.fixture
def broadcasts(server, monkeypatch):
    spy = _BroadcastSpy()
    monkeypatch.setattr(server, "broadcast", spy)
    return spy


@pytest.fixture
def client(server, settings_path) -> TestClient:
    return TestClient(server.app)


@pytest.fixture
def posts(monkeypatch):
    calls: list[tuple[str, object]] = []

    def fake_post(url, body, *, timeout):
        calls.append((url, body))
        return webhook_module.WebhookResponse(status=200, body="ok")

    monkeypatch.setattr(webhook_module, "_default_post", fake_post)
    return calls


def _decide(client, pid, decision, by="karol"):
    return client.post(f"/api/desk/actuators/webhook/{pid}/decision", json={"decision": decision, "decided_by": by})


@pytest.mark.integration
def test_unconfigured_refuses_with_400(client, db):
    res = client.post(PROPOSE, json={"text": "ping"})
    assert res.status_code == 400
    assert "not configured" in res.json()["error"]


@pytest.mark.integration
def test_empty_text_refuses_with_400(client, db, settings_path):
    _configure(settings_path)
    res = client.post(PROPOSE, json={"text": "  "})
    assert res.status_code == 400


@pytest.mark.integration
def test_propose_preview_is_the_wire_body(client, db, settings_path):
    _configure(settings_path)
    proposal = client.post(PROPOSE, json={"text": "the brief"}).json()["proposal"]
    assert proposal["status"] == "proposed"
    assert proposal["target"] == "webhook"
    assert proposal["payload"]["body"]["text"] == proposal["preview"]
    assert "the brief" in proposal["preview"]


@pytest.mark.integration
def test_identical_content_dedupes(client, db, settings_path):
    """The live generic webhook retains the companion idempotency fence."""
    _configure(settings_path)
    a = client.post(PROPOSE, json={"text": "same"}).json()["proposal"]
    b = client.post(PROPOSE, json={"text": "same"}).json()["proposal"]
    assert a["id"] == b["id"]
    c = client.post(PROPOSE, json={"text": "different"}).json()["proposal"]
    assert c["id"] != a["id"]


@pytest.mark.integration
def test_source_identity_returns_the_receipt_to_the_desk_subject(
    client, db, settings_path, posts
):
    _configure(settings_path)
    db.notes.upsert(
        note_id="n1",
        title="Release checklist",
        body_markdown="release is ready",
    )
    proposed = client.post(
        PROPOSE,
        json={
            "text": "release is ready",
            "title": "Release checklist",
            "source_ref": "note:n1",
            "source_label": "Release checklist",
        },
    )
    assert proposed.status_code == 200
    proposal = proposed.json()["proposal"]
    assert proposal["window_id"] == "note:n1"
    assert proposal["payload"]["_source"] == {
        "ref": "note:n1",
        "label": "Release checklist",
    }

    final = _decide(client, proposal["id"], "approved").json()["proposal"]
    assert final["status"] == "executed"
    receipt = db.projections.list(subject_ref="note:n1")["projections"][0]
    assert receipt["projection_kind"] == "receipt"
    assert receipt["subject_label"] == "Release checklist"
    assert receipt["title"] == "Custom webhook post succeeded"
    assert receipt["detail_url"] == "/?open=note:n1"


@pytest.mark.integration
def test_source_identity_must_be_a_known_qualified_kind(client, db, settings_path):
    _configure(settings_path)
    response = client.post(
        PROPOSE,
        json={"text": "ship", "source_ref": "unknown:n1"},
    )
    assert response.status_code == 400
    assert "unknown resource kind" in response.json()["error"]


@pytest.mark.integration
def test_source_identity_must_resolve_to_live_material(client, db, settings_path):
    _configure(settings_path)
    response = client.post(
        PROPOSE,
        json={"text": "ship", "source_ref": "note:missing"},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Unknown Note source: missing"


@pytest.mark.integration
def test_posture_change_never_widens_an_existing_proposal(
    client, db, settings_path, posts, broadcasts
):
    _configure(settings_path)
    proposal = client.post(PROPOSE, json={"text": "captured normal"}).json()[
        "proposal"
    ]
    assert proposal["policy_snapshot"]["mode"] == "neutral"
    _set_control_mode(settings_path, "yolo")

    repeated = client.post(PROPOSE, json={"text": "captured normal"}).json()[
        "proposal"
    ]
    assert repeated["id"] == proposal["id"]
    assert repeated["status"] == "proposed"
    assert repeated["policy_snapshot"]["mode"] == "neutral"
    assert posts == []

    final = _decide(client, proposal["id"], "approved").json()["proposal"]
    assert final["status"] == "executed"
    assert final["policy_snapshot"]["mode"] == "neutral"
    assert final["policy_snapshot"]["authority_basis"] == "per_action_decision"


@pytest.mark.integration
def test_decision_on_unknown_proposal_404(client, db, settings_path):
    _configure(settings_path)
    res = _decide(client, "ghost", "approved")
    assert res.status_code == 404


@pytest.mark.integration
def test_approval_posts_the_preview_byte_equal(client, db, settings_path, posts, broadcasts):
    _configure(settings_path)
    proposal = client.post(PROPOSE, json={"text": "the brief"}).json()["proposal"]
    assert posts == []
    final = _decide(client, proposal["id"], "approved").json()["proposal"]
    assert final["status"] == "executed"
    assert final["result"]["status"] == 200
    assert final["result"]["host"] == "hooks.example.com"
    assert len(posts) == 1
    url, body = posts[0]
    assert url == URL
    assert body == {"text": proposal["preview"]}


@pytest.mark.integration
def test_yolo_executes_the_configured_webhook_without_a_decision(
    client, db, settings_path, posts, broadcasts
):
    _configure(settings_path)
    _set_control_mode(settings_path, "yolo")
    proposal = client.post(PROPOSE, json={"text": "the brief"}).json()["proposal"]
    assert proposal["status"] == "executed"
    assert proposal["policy_snapshot"]["authority_basis"] == "control_posture"
    assert proposal["policy_snapshot"]["mode"] == "yolo"
    assert len(posts) == 1
    assert posts[0][1] == {"text": proposal["preview"]}


@pytest.mark.integration
def test_rejection_posts_nothing(client, db, settings_path, posts, broadcasts):
    _configure(settings_path)
    pid = client.post(PROPOSE, json={"text": "ping"}).json()["proposal"]["id"]
    assert _decide(client, pid, "rejected").json()["proposal"]["status"] == "rejected"
    assert posts == []


@pytest.mark.integration
def test_url_removed_between_propose_and_approve_fails_honestly(client, db, settings_path, posts):
    _configure(settings_path)
    pid = client.post(PROPOSE, json={"text": "ping"}).json()["proposal"]["id"]
    _configure(settings_path, url="")
    final = _decide(client, pid, "approved").json()["proposal"]
    assert final["status"] == "failed"
    assert posts == []


@pytest.mark.integration
def test_the_url_never_rides_a_response_or_broadcast(client, db, settings_path, posts, broadcasts):
    _configure(settings_path)
    propose = client.post(PROPOSE, json={"text": "ping"})
    decide = _decide(client, propose.json()["proposal"]["id"], "approved")
    for blob in (propose.text, decide.text):
        assert "secret-hook" not in blob
    for _kind, data in broadcasts.events:
        assert "secret-hook" not in json.dumps(data)


@pytest.mark.integration
def test_the_wire_events_ride_for_qlippy(client, db, settings_path, posts, broadcasts):
    """The live generic webhook path still emits a safe execution receipt."""
    _configure(settings_path)
    pid = client.post(PROPOSE, json={"text": "ping"}).json()["proposal"]["id"]
    _decide(client, pid, "approved")
    kinds = [kind for kind, _data in broadcasts.events]
    assert "actuator_proposed" in kinds
    assert "actuator_result" in kinds
    result = next(data for kind, data in broadcasts.events if kind == "actuator_result")
    assert result["status"] == "executed"
    assert result["target"] == "webhook"
    assert "payload" not in result


@pytest.mark.integration
def test_companion_status_reports_webhook_configured(client, db, settings_path):
    assert client.get("/api/desk/actuators/status").json()["webhook_configured"] is False
    _configure(settings_path)
    on = client.get("/api/desk/actuators/status").json()
    assert on["webhook_configured"] is True


@pytest.mark.integration
def test_slack_and_webhook_decisions_do_not_cross(client, db, settings_path):
    # A live webhook proposal cannot be decided through the parked Slack
    # endpoint. The endpoint returns its named capability refusal, and does
    # not consume the webhook proposal.
    _configure(settings_path)
    pid = client.post(PROPOSE, json={"text": "ping"}).json()["proposal"]["id"]
    crossed = client.post(f"/api/desk/actuators/slack/{pid}/decision", json={"decision": "approved"})
    assert crossed.status_code == 400
    assert crossed.json()["error"] == "slack_moved_to_channel"

    # A historical Slack proposal is still readable, but the live webhook
    # decision route refuses to act on it by target. This keeps the original
    # cross-target guard on a real persisted proposal.
    historical = db.actuators.record_proposal(
        meeting_id=None,
        origin="desk",
        window_id="legacy:slack",
        plugin_id="webhook_post",
        plugin_version="1",
        idempotency_key="legacy-slack-cross-target-1",
        target="slack",
        action="post_message",
        preview="historical Slack message",
        payload={"body": {"text": "historical Slack message"}},
        required_capabilities=["actuator"],
        fixed_destination=True,
    )
    reverse = client.post(
        f"/api/desk/actuators/webhook/{historical.id}/decision",
        json={"decision": "approved"},
    )
    assert reverse.status_code == 404
