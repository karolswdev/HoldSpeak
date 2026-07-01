"""HS-61-02 — the Send-to-Slack surfaces: gating, wiring, honest copy.

The conditions under test: the aftercare response carries the capability
flag (a bool, never the URL); the history page's buttons are gated on that
flag, so an unconfigured install renders no Slack affordance at all; the
buttons wire to the export route through `exportToSlack`; the settings field
ships with the honest copy (what is sent, only after approval, only to this
URL's host, stored locally).
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

import holdspeak.config as config_module
from holdspeak.config import Config
from holdspeak.db import Database, get_database, reset_database
from holdspeak.meeting_session import IntelSnapshot, MeetingState
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

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
    page = (_REPO / "web" / "src" / "pages" / "history.astro").read_text()
    assert page.count("Send to Slack") >= 2  # the digest + the draft button
    # Every Slack affordance hides behind the capability flag — unconfigured
    # renders no Slack mention at all.
    assert page.count('x-show="selectedMeetingAftercare?.slack_configured"') >= 2
    assert "exportToSlack('digest')" in page
    assert "exportToSlack('followup')" in page
    # The follow-up note stays honest in both states — and short (HS-62-02:
    # no reassurance tails).
    assert "'Preview and copy only.'" in page
    assert "Send to Slack creates a proposal; approve it below." in page


def test_proposal_guard_copy_tells_the_per_target_truth():
    # The guard copy tells the per-target truth, in one short line each
    # (HS-62-02 swept the "Nothing runs without your approval" preamble).
    for page_name in ("history.astro", "live.astro"):
        page = (_REPO / "web" / "src" / "pages" / page_name).read_text()
        assert "Approving sends this message to Slack." in page, page_name
        assert "Approving records the decision; execution is a separate step." in page, page_name


def test_history_app_wires_the_export_route():
    js = (_REPO / "web" / "src" / "scripts" / "history-app.js").read_text()
    assert "async exportToSlack(what)" in js
    assert "/export/slack" in js
    assert "Slack proposal created — approve it below." in js
    # The decision flash tells the truth about the execute-on-approve leg.
    assert "Approved — sent to Slack." in js


def test_settings_field_ships_the_honest_copy():
    page = (_REPO / "web" / "src" / "pages" / "settings.astro").read_text()
    assert "Send to Slack webhook URL" in page
    assert 'x-model="settings.meeting.slack_webhook_url"' in page
    for truth in (
        "Sends exactly what you preview",
        "after you approve each send",
        "only to this URL's host",
        "Leave empty to turn the feature off",
    ):
        assert truth in page, truth
