"""HS-72-04 — owner-typed actuator proposals (schema v5).

A proposal now carries `origin` ('meeting' | 'desk'); `meeting_id` is null
exactly when origin='desk'. The old hidden 'companion' sentinel meeting (a
fake row that satisfied the NOT NULL FK) is gone, and the v4→v5 migration
re-types its rows and deletes it — proven here against a real v4-shaped
database, through the real backup-then-apply path.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from holdspeak.db import Database, reset_database

_V4_ACTUATOR_DDL = """
CREATE TABLE actuator_proposals (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    window_id TEXT NOT NULL DEFAULT '',
    plugin_id TEXT NOT NULL,
    plugin_version TEXT NOT NULL DEFAULT 'unknown',
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'proposed',
    target TEXT NOT NULL,
    action TEXT NOT NULL,
    preview TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    reversible INTEGER NOT NULL DEFAULT 0,
    required_capabilities_json TEXT NOT NULL DEFAULT '[]',
    decided_by TEXT,
    result_json TEXT,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at TEXT,
    executed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@pytest.fixture(autouse=True)
def _clean_db_singleton():
    reset_database()
    yield
    reset_database()


def _make_v4_facsimile(db_path: Path) -> None:
    """A current DB, downgraded to the v4 actuator shape + sentinel data.

    Everything except the actuator table was identical in v4, so the honest
    facsimile is: build fresh, swap in the OLD actuator DDL, seed a sentinel
    meeting with a desk proposal (plus a real meeting with a real proposal
    and audit rows), and stamp version 4.
    """
    db = Db = Database(db_path)
    from holdspeak.meeting_session import MeetingState
    from datetime import datetime

    db.meetings.save_meeting(MeetingState(id="m-real", started_at=datetime.now(), title="Real"))
    db.meetings.save_meeting(MeetingState(id="companion", started_at=datetime.now(), title="Desk · companion sends"))
    reset_database()

    conn = sqlite3.connect(str(db_path))
    conn.executescript("PRAGMA foreign_keys = OFF;\nDROP TABLE actuator_proposals;" + _V4_ACTUATOR_DDL)
    conn.executescript(
        """
        INSERT INTO actuator_proposals (id, meeting_id, plugin_id, idempotency_key,
                                        target, action, preview)
        VALUES ('p-meeting', 'm-real', 'slack_export', 'k1', 'slack', 'post_message', 'hello'),
               ('p-desk', 'companion', 'webhook_post', 'k2', 'slack', 'post_message', 'from the desk');
        INSERT INTO actuator_proposal_audit (proposal_id, actor, from_status, to_status, detail)
        VALUES ('p-meeting', 'system', NULL, 'proposed', 'seed'),
               ('p-desk', 'system', NULL, 'proposed', 'seed');
        DELETE FROM schema_version;
        INSERT INTO schema_version (version) VALUES (4);
        """
    )
    conn.commit()
    conn.close()


def test_v4_upgrade_retypes_desk_rows_and_kills_the_sentinel(tmp_path: Path) -> None:
    db_path = tmp_path / "v4.db"
    _make_v4_facsimile(db_path)
    reset_database()

    db = Database(db_path)  # the real backup-then-apply upgrade runs here

    # The meeting-owned proposal is untouched.
    kept = db.actuators.get_proposal("p-meeting")
    assert kept is not None and kept.origin == "meeting" and kept.meeting_id == "m-real"
    # The sentinel-attached proposal is re-typed, not lost.
    desk = db.actuators.get_proposal("p-desk")
    assert desk is not None and desk.origin == "desk" and desk.meeting_id is None
    assert desk.preview == "from the desk"
    # The audit trail survived the rebuild verbatim.
    assert [a.to_status for a in db.actuators.list_audit("p-desk")] == ["proposed"]
    # The sentinel meeting is gone from the store entirely.
    assert db.meetings.get_meeting("companion") is None
    # A backup was taken before the rebuild (the Phase-50 contract:
    # `<name>.<timestamp>.bak`).
    assert list(tmp_path.glob("v4.db.*.bak")), "no backup before migration"


def test_desk_proposals_carry_null_meeting_id(tmp_path: Path) -> None:
    db = Database(tmp_path / "fresh.db")
    p = db.actuators.record_proposal(
        meeting_id=None, origin="desk", window_id="companion:slack",
        plugin_id="webhook_post", plugin_version="1", idempotency_key="d1",
        target="slack", action="post_message", preview="x",
    )
    assert p.origin == "desk" and p.meeting_id is None


def test_meeting_proposals_still_require_a_meeting(tmp_path: Path) -> None:
    db = Database(tmp_path / "fresh.db")
    with pytest.raises(ValueError, match="meeting_id is required"):
        db.actuators.record_proposal(
            meeting_id=None, window_id="w", plugin_id="p", plugin_version="1",
            idempotency_key="m1", target="slack", action="a", preview="x",
        )


def test_unknown_origin_is_rejected(tmp_path: Path) -> None:
    db = Database(tmp_path / "fresh.db")
    with pytest.raises(ValueError, match="invalid proposal origin"):
        db.actuators.record_proposal(
            meeting_id="m", origin="carrier-pigeon", window_id="w", plugin_id="p",
            plugin_version="1", idempotency_key="o1", target="t", action="a", preview="x",
        )
