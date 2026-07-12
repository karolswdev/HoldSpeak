"""Send-to-Slack surfaces: capability gating, policy, and wiring.

The conditions under test: the aftercare response carries the capability
flag (a bool, never the URL); the history page's buttons are gated on that
flag, so an unconfigured install renders no Slack affordance at all; the
buttons wire to the export route through `proposeSlack`; and the result uses
the central operation-policy snapshot rather than assuming every posture asks
for approval.
"""
from __future__ import annotations

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

import holdspeak.config as config_module  # noqa: E402
from holdspeak.config import Config  # noqa: E402
from holdspeak.db import Database, get_database, reset_database  # noqa: E402
from holdspeak.meeting_session import IntelSnapshot, MeetingState  # noqa: E402
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks  # noqa: E402

_REPO = Path(__file__).resolve().parents[2]
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
                    {
                        "id": "a1",
                        "task": "Wire the rate limiter",
                        "owner": "Priya",
                        "due": "Friday",
                        "status": "pending",
                        "review_state": "accepted",
                        "source_timestamp": None,
                        "created_at": datetime(2026, 6, 11, 10, 0, 0).isoformat(),
                    }
                ],
            ),
        )
    )


@pytest.fixture
def client(settings_path) -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


# ── the capability flag ──────────────────────────────────────────────────────


@pytest.mark.integration
def test_aftercare_flag_is_false_when_unconfigured(client, db, seeded):
    res = client.get("/api/meetings/m1/aftercare")
    assert res.status_code == 200
    assert res.json()["slack_configured"] is False


@pytest.mark.integration
def test_aftercare_flag_is_true_and_never_the_url(client, db, settings_path, seeded):
    config = Config.load()
    config.meeting.slack_webhook_url = URL
    config.save(path=settings_path)
    res = client.get("/api/meetings/m1/aftercare")
    assert res.json()["slack_configured"] is True
    # The flag is a bool; the credential never rides the response.
    assert "secret-credential" not in res.text
    assert "hooks.slack.com" not in res.text


# ── the page locks ───────────────────────────────────────────────────────────


def test_history_buttons_are_gated_on_the_flag():
    page = " ".join(
        (_REPO / "web/src/pages/HistoryPage.tsx").read_text().split()
    )
    assert "Send digest to Slack" in page and "Send follow-up to Slack" in page
    assert "aftercare.slack_configured" in page
    assert 'proposeSlack("digest")' in page and 'proposeSlack("followup")' in page
    assert 'apiFetch<JsonRecord>("/api/authority/policy")' in page
    assert "controlModeDescription" in page


def test_proposal_rows_render_the_central_policy_and_refusal_truth():
    page = " ".join(
        (_REPO / "web/src/pages/HistoryPage.tsx").read_text().split()
    )
    assert "row.policy_snapshot" in page and "row.operation" in page
    assert 'policy.outcome === "refused"' in page
    assert 'row.status === "proposed" && !refused' in page
    assert "operation.effect_class" in page
    assert "operation.destination" in page
    assert "policy.authority_basis" in page
    assert "Proposed external actions appear here before execution" in page


def test_history_app_wires_the_export_route():
    js = (_REPO / "web/src/pages/HistoryPage.tsx").read_text()
    assert "proposeSlack" in js
    assert "/export/slack" in js
    assert "setActive(\"proposals\")" in js


def test_settings_field_ships_the_honest_copy():
    page = (_REPO / "web/src/pages/SettingsPage.tsx").read_text()
    assert "SettingsFields" in page and "meeting" in page
    assert 'apiFetch<{ settings?: JsonRecord }>' in page and '"/api/settings"' in page
