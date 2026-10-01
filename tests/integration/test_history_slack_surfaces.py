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


def _flat(path: Path) -> str:
    return " ".join(path.read_text().split())


def test_the_aftercare_slack_rows_are_gone():
    """PHILO-11-05 (R7, canvas C5): the DIGEST → SLACK / FOLLOW-UP → SLACK rows
    only proposed; they are removed with their component. The digest and the
    follow-up are forms of the meeting's ONE SEND well. The component is
    PARKED, not deleted (owner law; the sealed graph passes cite its path):
    nothing mounts or exports it."""
    import subprocess
    mounts = subprocess.run(["git", "grep", "-l", "AftercareGadgets", "--", "web/src"], cwd=_REPO,
                            capture_output=True, text=True).stdout.split()
    assert mounts == ["web/src/pages/cores/history/AftercareGadgets.tsx"], mounts
    detail = _flat(_HISTORY / "MeetingDetail.tsx")
    assert "AftercareGadgets" not in detail
    assert "<MeetingSendWell" in detail
    assert "DIGEST → SLACK" not in detail and "FOLLOW-UP → SLACK" not in detail
    well = _flat(_REPO / "web/src/meetings/MeetingSendWell.tsx")
    for kind in ("meeting_summary", "meeting_digest", "meeting_followup"):
        assert f'"{kind}"' in well, kind
    data = _flat(_HISTORY / "useMeetingData.tsx")
    assert '"/api/authority/policy"' in data


def test_proposal_rows_render_the_central_policy_and_refusal_truth():
    page = _flat(_HISTORY / "useMeetingData.tsx")
    assert "row.policy_snapshot" in page and "row.operation" in page
    assert 'policy.outcome === "refused"' in page
    assert 'row.status === "proposed" && !refused' in page
    assert "operation.effect_class" in page
    assert "operation.destination" in page
    assert "policy.authority_basis" in page
    # HS-170-04: the empty needs-you section is ABSENT (UX-CANON A.8:
    # no counters of zero, empty sections absent). NeedsYouTable returns
    # null at zero — the honest guard, not a celebratory sentence.
    flat = _flat(_HISTORY / "NeedsYouTable.tsx")
    assert "needsRows.length === 0" in flat  # the honest guard
    assert "return null" in flat  # section-absent at zero


def test_history_app_no_longer_calls_the_parked_export_route():
    """PHILO-11-05: the parked `/export/slack` route has no caller on the face."""
    js = (_HISTORY / "useMeetingData.tsx").read_text()
    assert "proposeSlack" not in js
    assert "/export/slack" not in js
    # HS-100-08: proposals live ON the outcomes face; deciding refreshes the same rows.
    assert "setProposals(" in js


def test_settings_field_ships_the_honest_copy():
    # HS-111-01: the prose died with the SaaS page. The honest truth
    # survives structurally — the Slack webhook is a dedicated secret on
    # the Prefs surface: the UI shows configured-ness (SET/—) and the
    # write-only path, never the URL, and the token states the residency.
    page = (_REPO / "web/src/pages/cores/SettingsCore.tsx").read_text()
    # PHILO-11-05 (R7, canvas D4): no Slack webhook row in Credentials; Slack lives in Destinations.
    assert "Slack webhook" not in page
    assert "<SecretRow" in page and "configured={Boolean(state.configured)}" in page
    assert "values stay on this hub" in page
    # HS-132-12: the JsonRecord alias was inlined; the typed settings read
    # against /api/settings is the invariant, not the alias name.
    assert 'apiFetch<{ settings?: Record<string, unknown> }>' in page
    assert '"/api/settings"' in page
    gadgets = (_REPO / "web/src/desk/surface/gadgets.tsx").read_text()
    # The chip renders the configured fact, never the credential value.
    assert '{configured ? "SET" : "—"}' in gadgets
