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
def test_aftercare_does_not_advertise_legacy_slack(client, db, seeded):
    res = client.get("/api/meetings/m1/aftercare")
    assert res.status_code == 200
    assert "slack_configured" not in res.json()


@pytest.mark.integration
def test_aftercare_keeps_the_legacy_url_out_of_the_response(client, db, settings_path, seeded):
    config = Config.load()
    config.meeting.slack_webhook_url = URL
    config.save(path=settings_path)
    res = client.get("/api/meetings/m1/aftercare")
    assert "slack_configured" not in res.json()
    # The retired credential never rides the response.
    assert "secret-credential" not in res.text
    assert "hooks.slack.com" not in res.text


# ── the page locks ───────────────────────────────────────────────────────────


# HS-132-12: HS-117-09 decomposed HistoryCore — the aftercare gadget rows
# live in history/AftercareGadgets.tsx, the proposal rows and their wire
# calls in history/useMeetingData.tsx, and the empty-queue token in
# history/NeedsYouTable.tsx.
_HISTORY = _REPO / "web/src/pages/cores/history"


