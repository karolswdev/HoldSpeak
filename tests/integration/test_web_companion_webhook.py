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

import holdspeak.config as config_module
import holdspeak.plugins.builtin.webhook_post_actuator as webhook_module
from holdspeak.config import Config
from holdspeak.db import Database, get_database, reset_database
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

URL = "https://hooks.example.com/services/secret-hook"
PROPOSE = "/api/companion/webhook/propose"


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


def _configure(settings_path, url=URL):
    config = Config.load()
    config.meeting.companion_webhook_url = url
    config.save(path=settings_path)


class _BroadcastSpy:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def __call__(self, message_type, data):
        self.events.append((message_type, data))


@pytest.fixture
def server():
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
    return client.post(f"/api/companion/webhook/{pid}/decision", json={"decision": decision, "decided_by": by})


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
def test_companion_status_reports_webhook_configured(client, db, settings_path):
    assert client.get("/api/companion/status").json()["connectors"]["webhook_configured"] is False
    _configure(settings_path)
    on = client.get("/api/companion/status").json()
    assert on["connectors"]["webhook_configured"] is True


@pytest.mark.integration
def test_slack_and_webhook_decisions_do_not_cross(client, db, settings_path):
    # a webhook proposal cannot be decided on the slack route, and vice-versa
    _configure(settings_path)
    pid = client.post(PROPOSE, json={"text": "ping"}).json()["proposal"]["id"]
    crossed = client.post(f"/api/companion/slack/{pid}/decision", json={"decision": "approved"})
    assert crossed.status_code == 404
