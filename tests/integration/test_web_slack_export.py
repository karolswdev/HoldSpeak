"""HS-61-01 — Send to Slack at the web boundary.

The conditions under test: the export route refuses honestly (unconfigured /
unknown kind / missing meeting / empty aftercare) and otherwise records a
`proposed` proposal whose preview is byte-equal to the wire body; nothing
egresses before approval (the lock); approving through the EXISTING decision
endpoint executes through the real gated connector stack (transport faked at
the lowest seam) and the body equals the preview; the webhook URL never
appears in any response or broadcast; the settings boundary enforces THE
shared URL rule with clean 400s.
"""
from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime
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
from holdspeak.meeting_session import IntelSnapshot, MeetingState
from holdspeak.plugins.actuator_executor import ActuatorExecutionError, ActuatorExecutor
from holdspeak.slack_export import build_slack_connector
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

URL = "https://hooks.slack.com/services/T0/B0/secret-credential"


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


def _action(item_id, task, *, owner=None):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": "Friday",
        "status": "pending",
        "review_state": "accepted",
        "source_timestamp": None,
        "created_at": datetime(2026, 6, 11, 10, 0, 0).isoformat(),
    }


@pytest.fixture
def seeded(db: Database):
    db.meetings.save_meeting(
        MeetingState(
            id="m1",
            started_at=datetime(2026, 6, 11, 10, 0, 0),
            title="API design follow-up",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    _action("a1", "Wire the rate limiter", owner="Priya"),
                ],
            ),
        )
    )
    db.meetings.save_meeting(
        MeetingState(id="m-empty", started_at=datetime(2026, 6, 11, 11, 0, 0), title="Quiet")
    )


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


# ── the route matrix ─────────────────────────────────────────────────────────


@pytest.mark.integration
def test_unconfigured_refuses_with_400(client, seeded):
    res = client.post("/api/meetings/m1/export/slack", json={"what": "digest"})
    assert res.status_code == 400
    assert "not configured" in res.json()["error"]


@pytest.mark.integration
def test_unknown_kind_refuses_with_400(client, settings_path, seeded):
    _configure_slack(settings_path)
    res = client.post("/api/meetings/m1/export/slack", json={"what": "carrier-pigeon"})
    assert res.status_code == 400
    assert "Unknown export kind" in res.json()["error"]


@pytest.mark.integration
def test_missing_meeting_404(client, settings_path, seeded):
    _configure_slack(settings_path)
    res = client.post("/api/meetings/ghost/export/slack", json={"what": "digest"})
    assert res.status_code == 404


@pytest.mark.integration
def test_empty_aftercare_refuses_with_400(client, settings_path, seeded):
    _configure_slack(settings_path)
    res = client.post("/api/meetings/m-empty/export/slack", json={"what": "digest"})
    assert res.status_code == 400
    assert "nothing open" in res.json()["error"]


@pytest.mark.integration
def test_export_records_a_proposal_whose_preview_is_the_wire_body(
    client, db, settings_path, seeded
):
    _configure_slack(settings_path)
    res = client.post("/api/meetings/m1/export/slack", json={"what": "digest"})
    assert res.status_code == 200, res.text
    proposal = res.json()["proposal"]
    assert proposal["status"] == "proposed"  # nothing executed
    assert proposal["target"] == "slack"
    assert proposal["action"] == "post_message"
    # Executed == previewed, byte for byte: the stored body IS the preview.
    assert proposal["payload"]["body"]["text"] == proposal["preview"]
    assert "Wire the rate limiter" in proposal["preview"]


@pytest.mark.integration
def test_identical_content_dedupes_changed_content_reproposes(
    client, db, settings_path, seeded
):
    _configure_slack(settings_path)
    first = client.post("/api/meetings/m1/export/slack", json={"what": "digest"}).json()
    second = client.post("/api/meetings/m1/export/slack", json={"what": "digest"}).json()
    assert first["proposal"]["id"] == second["proposal"]["id"]
    # The other kind is different content → its own proposal.
    followup = client.post(
        "/api/meetings/m1/export/slack", json={"what": "followup"}
    ).json()
    assert followup["proposal"]["id"] != first["proposal"]["id"]


# ── never egress unapproved ──────────────────────────────────────────────────


@pytest.mark.integration
def test_a_proposed_export_never_posts(client, db, settings_path, seeded, posts):
    _configure_slack(settings_path)
    proposal = client.post(
        "/api/meetings/m1/export/slack", json={"what": "digest"}
    ).json()["proposal"]

    # The executor refuses a non-approved proposal — no transport call.
    executor = ActuatorExecutor(
        db, connector=build_slack_connector(URL), allow_actuators=True
    )
    with pytest.raises(ActuatorExecutionError):
        executor.execute(proposal["id"])
    assert posts == []


@pytest.mark.integration
def test_rejection_posts_nothing(client, db, settings_path, seeded, posts, broadcasts):
    _configure_slack(settings_path)
    proposal = client.post(
        "/api/meetings/m1/export/slack", json={"what": "digest"}
    ).json()["proposal"]
    res = client.post(
        f"/api/meetings/m1/proposals/{proposal['id']}/decision",
        json={"decision": "rejected", "decided_by": "karol"},
    )
    assert res.json()["proposal"]["status"] == "rejected"
    assert posts == []


# ── approval executes through the real stack ─────────────────────────────────


@pytest.mark.integration
def test_approval_posts_the_preview_byte_equal(
    client, db, settings_path, seeded, posts, broadcasts
):
    _configure_slack(settings_path)
    proposal = client.post(
        "/api/meetings/m1/export/slack", json={"what": "digest"}
    ).json()["proposal"]
    assert posts == []  # proposing sent nothing

    res = client.post(
        f"/api/meetings/m1/proposals/{proposal['id']}/decision",
        json={"decision": "approved", "decided_by": "karol"},
    )
    final = res.json()["proposal"]
    assert final["status"] == "executed"
    assert final["result"]["status"] == 200
    assert final["result"]["host"] == "hooks.slack.com"

    # Exactly one POST, to the configured URL, body byte-equal to the preview.
    assert len(posts) == 1
    url, body = posts[0]
    assert url == URL
    assert body == {"text": proposal["preview"]}

    # The audit trail is the full lifecycle.
    audit = db.actuators.list_audit(proposal["id"])
    assert [a.to_status for a in audit] == ["proposed", "approved", "executed"]


@pytest.mark.integration
def test_approval_with_the_url_since_removed_fails_honestly(
    client, db, settings_path, seeded, posts, broadcasts
):
    _configure_slack(settings_path)
    proposal = client.post(
        "/api/meetings/m1/export/slack", json={"what": "digest"}
    ).json()["proposal"]
    _configure_slack(settings_path, url="")  # unconfigured between propose and approve
    res = client.post(
        f"/api/meetings/m1/proposals/{proposal['id']}/decision",
        json={"decision": "approved", "decided_by": "karol"},
    )
    final = res.json()["proposal"]
    assert final["status"] == "failed"
    assert "not configured" in final["error"]
    assert posts == []


@pytest.mark.integration
def test_github_approvals_keep_todays_behavior(client, db, settings_path, seeded, posts):
    # The execute-on-approve leg is scoped to target="slack"; a GitHub
    # proposal still only flips state (no connector exists in the route).
    _configure_slack(settings_path)
    filed = client.post(
        "/api/meetings/m1/aftercare/file-issue",
        json={"action_item_id": "a1", "repo": "acme/app"},
    ).json()["proposal"]
    res = client.post(
        f"/api/meetings/m1/proposals/{filed['id']}/decision",
        json={"decision": "approved", "decided_by": "karol"},
    )
    assert res.json()["proposal"]["status"] == "approved"  # not executed
    assert posts == []


# ── the credential rule ──────────────────────────────────────────────────────


@pytest.mark.integration
def test_the_url_never_rides_a_response_or_broadcast(
    client, db, settings_path, seeded, posts, broadcasts
):
    _configure_slack(settings_path)
    propose = client.post("/api/meetings/m1/export/slack", json={"what": "digest"})
    pid = propose.json()["proposal"]["id"]
    decide = client.post(
        f"/api/meetings/m1/proposals/{pid}/decision",
        json={"decision": "approved", "decided_by": "karol"},
    )
    listed = client.get("/api/meetings/m1/proposals")

    for blob in (propose.text, decide.text, listed.text):
        assert "secret-credential" not in blob
        assert "hooks.slack.com/services" not in blob
    for _kind, data in broadcasts.events:
        wire = json.dumps(data)
        assert "secret-credential" not in wire
        assert "hooks.slack.com/services" not in wire


@pytest.mark.integration
def test_the_wire_events_ride_for_qlippy(
    client, db, settings_path, seeded, posts, broadcasts
):
    _configure_slack(settings_path)
    pid = client.post("/api/meetings/m1/export/slack", json={"what": "digest"}).json()[
        "proposal"
    ]["id"]
    client.post(
        f"/api/meetings/m1/proposals/{pid}/decision",
        json={"decision": "approved", "decided_by": "karol"},
    )
    kinds = [k for k, _ in broadcasts.events]
    assert "actuator_proposed" in kinds
    assert "actuator_result" in kinds
    result = next(d for k, d in broadcasts.events if k == "actuator_result")
    assert result["status"] == "executed"
    assert result["target"] == "slack"
    assert "payload" not in result  # preview only, never the machine payload


# ── the settings boundary ────────────────────────────────────────────────────


@pytest.mark.integration
def test_slack_url_uses_write_only_settings_boundary(client, settings_path):
    res = client.put(
        "/api/settings/secrets/slack_webhook_url",
        json={"value": URL},
    )
    assert res.status_code == 200, res.text
    settings = client.get("/api/settings").json()
    assert "slack_webhook_url" not in settings["meeting"]
    assert settings["_secrets"]["slack_webhook_url"] == {
        "configured": True, "destination": "hooks.slack.com",
    }
    # Clearing it turns the feature back off.
    assert client.delete("/api/settings/secrets/slack_webhook_url").status_code == 200
    assert client.get("/api/settings").json()["_secrets"]["slack_webhook_url"] == {
        "configured": False,
    }


@pytest.mark.integration
@pytest.mark.parametrize(
    "bad",
    [
        "http://hooks.slack.com/services/x",  # plain http off-loopback
        "ftp://hooks.slack.com/x",
        "https://",
        "not a url",
    ],
)
def test_malformed_slack_url_refused_and_changes_nothing(client, settings_path, bad):
    res = client.put(
        "/api/settings/secrets/slack_webhook_url", json={"value": bad}
    )
    assert res.status_code == 400
    assert "webhook" in res.json()["error"].lower()
    assert client.get("/api/settings").json()["_secrets"]["slack_webhook_url"] == {
        "configured": False,
    }
