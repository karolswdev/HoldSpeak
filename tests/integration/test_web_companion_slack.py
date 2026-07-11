"""HSM-14 — the iPad desk connector sends through the HOST's actuator framework.

The conditions under test: a companion (the iPad desk) proposes arbitrary text
to Slack via `/api/desk/actuators/slack/propose`; it carries NO credential and the
host refuses honestly when Slack is unconfigured or the text is empty; the
preview is byte-equal to the wire body; nothing egresses before approval;
approving via `/api/desk/actuators/slack/{id}/decision` executes through the real
gated connector stack (transport faked at the lowest seam) with the webhook URL
joined in memory only — never on the proposal, in a response, or a broadcast;
and the companion status reports `slack_configured` without leaking the URL so
the iPad can gate its connector tile on host connectivity + config.
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
from holdspeak.plugins.actuator_executor import (  # noqa: E402
    ActuatorExecutionError,
    ActuatorExecutor,
)
from holdspeak.slack_export import build_slack_connector  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402

URL = "https://hooks.slack.com/services/T0/B0/secret-credential"
PROPOSE = "/api/desk/actuators/slack/propose"


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
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    Config().save(path=target)
    return target


def _configure_slack(settings_path, url=URL):
    config = Config.load()
    config.meeting.slack_webhook_url = url
    config.save(path=settings_path)


class _BroadcastSpy:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def __call__(self, message_type, data):
        self.events.append((message_type, data))


@pytest.fixture
def server():
    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
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
    """Fake ONLY the HTTP transport — the full gated-connector stack runs."""
    calls: list[tuple[str, object]] = []

    def fake_post(url, body, *, timeout):
        calls.append((url, body))
        return webhook_module.WebhookResponse(status=200, body="ok")

    monkeypatch.setattr(webhook_module, "_default_post", fake_post)
    return calls


def _decide(client, pid, decision, by="karol"):
    return client.post(
        f"/api/desk/actuators/slack/{pid}/decision",
        json={"decision": decision, "decided_by": by},
    )


# ── propose: honest refusals ─────────────────────────────────────────────────


@pytest.mark.integration
def test_unconfigured_refuses_with_400(client, db):
    res = client.post(PROPOSE, json={"text": "ship it"})
    assert res.status_code == 400
    assert "not configured" in res.json()["error"]


@pytest.mark.integration
def test_empty_text_refuses_with_400(client, db, settings_path):
    _configure_slack(settings_path)
    res = client.post(PROPOSE, json={"text": "   "})
    assert res.status_code == 400
    assert "text is required" in res.json()["error"]


# ── propose: the proposal IS the wire body ───────────────────────────────────


@pytest.mark.integration
def test_propose_records_a_proposal_whose_preview_is_the_wire_body(client, db, settings_path):
    _configure_slack(settings_path)
    res = client.post(PROPOSE, json={"text": "the risks list"})
    assert res.status_code == 200, res.text
    proposal = res.json()["proposal"]
    assert proposal["status"] == "proposed"            # nothing executed
    assert proposal["target"] == "slack"
    assert proposal["action"] == "post_message"
    # v5 (Phase 72): desk proposals are owner-typed — no sentinel meeting.
    assert proposal["origin"] == "desk"
    assert proposal["meeting_id"] is None
    assert proposal["payload"]["body"]["text"] == proposal["preview"]
    assert "the risks list" in proposal["preview"]


@pytest.mark.integration
def test_title_is_bolded_into_the_body(client, db, settings_path):
    _configure_slack(settings_path)
    proposal = client.post(PROPOSE, json={"text": "body here", "title": "Risks"}).json()["proposal"]
    assert proposal["preview"].startswith("*Risks*")
    assert "body here" in proposal["preview"]


@pytest.mark.integration
def test_identical_content_dedupes(client, db, settings_path):
    _configure_slack(settings_path)
    a = client.post(PROPOSE, json={"text": "same"}).json()["proposal"]
    b = client.post(PROPOSE, json={"text": "same"}).json()["proposal"]
    assert a["id"] == b["id"]
    c = client.post(PROPOSE, json={"text": "different"}).json()["proposal"]
    assert c["id"] != a["id"]


@pytest.mark.integration
def test_source_identity_returns_the_receipt_to_the_desk_subject(
    client, db, settings_path, posts
):
    _configure_slack(settings_path)
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
    assert receipt["title"] == "Slack send succeeded"
    assert receipt["detail_url"] == "/?open=note:n1"


@pytest.mark.integration
def test_source_identity_must_be_a_known_qualified_kind(client, db, settings_path):
    _configure_slack(settings_path)
    response = client.post(
        PROPOSE,
        json={"text": "ship", "source_ref": "unknown:n1"},
    )
    assert response.status_code == 400
    assert "unknown resource kind" in response.json()["error"]


@pytest.mark.integration
def test_source_identity_must_resolve_to_live_material(client, db, settings_path):
    _configure_slack(settings_path)
    response = client.post(
        PROPOSE,
        json={"text": "ship", "source_ref": "note:missing"},
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Unknown Note source: missing"


# ── nothing egresses before approval ─────────────────────────────────────────


@pytest.mark.integration
def test_a_proposed_send_never_posts(client, db, settings_path, posts):
    _configure_slack(settings_path)
    proposal = client.post(PROPOSE, json={"text": "ship it"}).json()["proposal"]
    executor = ActuatorExecutor(db, connector=build_slack_connector(URL), allow_actuators=True)
    with pytest.raises(ActuatorExecutionError):
        executor.execute(proposal["id"])
    assert posts == []


@pytest.mark.integration
def test_rejection_posts_nothing(client, db, settings_path, posts, broadcasts):
    _configure_slack(settings_path)
    pid = client.post(PROPOSE, json={"text": "ship it"}).json()["proposal"]["id"]
    res = _decide(client, pid, "rejected")
    assert res.json()["proposal"]["status"] == "rejected"
    assert posts == []


# ── approval executes through the real gated stack ───────────────────────────


@pytest.mark.integration
def test_approval_posts_the_preview_byte_equal(client, db, settings_path, posts, broadcasts):
    _configure_slack(settings_path)
    proposal = client.post(PROPOSE, json={"text": "the risks list"}).json()["proposal"]
    assert posts == []                                  # proposing sent nothing

    final = _decide(client, proposal["id"], "approved").json()["proposal"]
    assert final["status"] == "executed"
    assert final["result"]["status"] == 200
    assert final["result"]["host"] == "hooks.slack.com"

    assert len(posts) == 1
    url, body = posts[0]
    assert url == URL
    assert body == {"text": proposal["preview"]}

    audit = db.actuators.list_audit(proposal["id"])
    assert [a.to_status for a in audit] == ["proposed", "approved", "executed"]


@pytest.mark.integration
def test_url_removed_between_propose_and_approve_fails_honestly(client, db, settings_path, posts):
    _configure_slack(settings_path)
    pid = client.post(PROPOSE, json={"text": "ship it"}).json()["proposal"]["id"]
    _configure_slack(settings_path, url="")
    final = _decide(client, pid, "approved").json()["proposal"]
    assert final["status"] == "failed"
    assert "not configured" in final["error"]
    assert posts == []


@pytest.mark.integration
def test_decision_on_unknown_proposal_404(client, db, settings_path):
    _configure_slack(settings_path)
    res = _decide(client, "ghost", "approved")
    assert res.status_code == 404


# ── the credential rule (Phase 61 lock, here for the companion path) ─────────


@pytest.mark.integration
def test_the_url_never_rides_a_response_or_broadcast(client, db, settings_path, posts, broadcasts):
    _configure_slack(settings_path)
    propose = client.post(PROPOSE, json={"text": "ship it"})
    pid = propose.json()["proposal"]["id"]
    decide = _decide(client, pid, "approved")
    for blob in (propose.text, decide.text):
        assert "secret-credential" not in blob
        assert "hooks.slack.com/services" not in blob
    for _kind, data in broadcasts.events:
        wire = json.dumps(data)
        assert "secret-credential" not in wire
        assert "hooks.slack.com/services" not in wire


@pytest.mark.integration
def test_the_wire_events_ride_for_qlippy(client, db, settings_path, posts, broadcasts):
    _configure_slack(settings_path)
    pid = client.post(PROPOSE, json={"text": "ship it"}).json()["proposal"]["id"]
    _decide(client, pid, "approved")
    kinds = [k for k, _ in broadcasts.events]
    assert "actuator_proposed" in kinds
    assert "actuator_result" in kinds
    result = next(d for k, d in broadcasts.events if k == "actuator_result")
    assert result["status"] == "executed"
    assert result["target"] == "slack"
    assert "payload" not in result                      # preview only, never the machine payload


# ── the connectivity/config gate signal ──────────────────────────────────────


@pytest.mark.integration
def test_companion_status_reports_slack_configured_without_the_url(client, db, settings_path):
    off = client.get("/api/desk/actuators/status")
    assert off.status_code == 200
    assert off.json()["slack_configured"] is False

    _configure_slack(settings_path)
    on = client.get("/api/desk/actuators/status")
    assert on.json()["slack_configured"] is True
    assert "secret-credential" not in on.text
