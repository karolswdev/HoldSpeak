"""CAD-8 — the end-to-end chief-of-staff flow + the telemetry-free audit + the off-switch."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.cadence.audit import export_audit
from holdspeak.cadence.brief import build_brief
from holdspeak.cadence.closeout import apply_decision, build_closeout
from holdspeak.cadence.service import CadenceService
from holdspeak.config import CadenceConfig
from holdspeak.db import Database

NOON = datetime(2026, 6, 28, 12, 0, 0)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    d = Database(tmp_path / "e2e.db")
    with d._connection() as c:
        c.execute("INSERT INTO meetings (id, title, started_at, created_at) "
                  "VALUES ('m1','Platform sync','2026-06-27T14:00:00','2026-06-27T14:00:00')")
        c.execute("INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
                  "VALUES ('a1','m1','Add a watchdog','Karol','2026-06-30','pending','reviewed','2026-06-26T10:00:00')")
    d.actuators.record_proposal(meeting_id="m1", window_id="m1:aftercare",
                                plugin_id="github_issue_actuator", plugin_version="1.0",
                                idempotency_key="k1", target="github", action="create_issue",
                                preview="Create issue: watchdog", reversible=False)
    return d


def test_full_chief_of_staff_flow(db):
    # 1. project + score
    result = CadenceService(db, CadenceConfig()).tick(NOON)
    assert result.projected == 2 and result.open_loops == 2

    # 2. the morning brief leads with the top move
    brief = build_brief(db, now=NOON)
    assert not brief.is_empty and brief.items[0].next_action.title

    # 3. the end-of-day closeout recommends a decision per loop
    co = build_closeout(db, now=NOON)
    assert co.open_count == 2 and co.recs

    # 4. apply a decision (snooze the top loop) — lifecycle only, local
    top_id = db.cadence.list_loops()[0].id
    assert apply_decision(db, top_id, "snooze", now=NOON) is True
    assert db.cadence.get_loop(top_id).status == "snoozed"

    # 5. the audit reflects the whole journey, telemetry-free
    audit = export_audit(db, now=NOON)
    assert audit["egress"]["scope"] == "local"
    assert audit["totals"]["loops"] == 2
    assert any(l["status"] == "snoozed" for l in audit["loops"])
    assert "by_source" in audit["totals"]


def test_audit_is_local_and_serializable(db):
    import json

    CadenceService(db, CadenceConfig()).tick(NOON)
    audit = export_audit(db, now=NOON)
    # round-trips as JSON (no non-serializable objects) and never claims off-machine egress
    dumped = json.loads(json.dumps(audit))
    assert dumped["egress"]["scope"] == "local"
    assert "nothing leaves" in dumped["egress"]["label"].lower()


def test_master_off_switch_keeps_the_thread_from_starting():
    # The runtime gate reads cadence.enabled via the mixin; disabled => no thread.
    from holdspeak.config import Config
    from holdspeak.runtime.cadence import CadenceMixin

    class _Stub(CadenceMixin):
        def __init__(self, enabled):
            self.config = Config()
            self.config.cadence.enabled = enabled

    assert _Stub(False)._cadence_enabled() is False  # master off-switch
    assert _Stub(True)._cadence_enabled() is True
    strict = _Stub(True)
    strict.config.control_mode = "safe"
    assert strict._cadence_enabled() is False  # safe requires explicit run-now


def test_run_now_works_even_when_disabled(db):
    # run-now / audit are explicit user actions and work regardless of the master switch;
    # the switch only governs the autonomous in-runtime thread.
    cfg = CadenceConfig(enabled=False)
    assert CadenceService(db, cfg).tick(NOON).projected == 2
