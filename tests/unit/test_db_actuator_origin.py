"""HS-72-04 — owner-typed actuator proposals (schema v5).

A proposal now carries `origin` ('meeting' | 'desk'); `meeting_id` is null
exactly when origin='desk'. The old hidden 'companion' sentinel meeting (a
fake row that satisfied the NOT NULL FK) is gone, and the v4→v5 migration
re-types its rows and deletes it — proven here against a real v4-shaped
database, through the real backup-then-apply path.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.db import Database, reset_database

@pytest.fixture(autouse=True)
def _clean_db_singleton():
    reset_database()
    yield
    reset_database()


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
