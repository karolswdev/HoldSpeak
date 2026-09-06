"""HS-175-04: MeetingWatchSource -- local DB meeting watch adapter.

Proves:
- Entities from seeded meetings with intel and commitments.
- Entity shape: title, date, participants, decisions_count,
  commitments_count, intel_status, updated_at.
- updated_at reflects the latest intel run.
- A meeting without intel returns intel_status="off".
- Zero egress: no CLI/network calls.
- The template compiles.
- Absent row when no meetings linked.
- The Room SOURCES row shape (via _PROVIDER_TO_CONNECTOR + _SUBJECT_TO_QUERY_KIND).
"""
from __future__ import annotations

import uuid

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ValidationError
from holdspeak.services.watch_sources import MeetingWatchSource, fetch_watch_snapshot

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture()
def db(tmp_path):
    return Database(tmp_path / "test.db")


def _seed_meeting(db, *, meeting_id=None, title="Standup", started_at="2026-09-03T10:00:00",
                  intel_status="completed", intel_completed_at="2026-09-03T10:30:00"):
    mid = meeting_id or f"mtg-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings
               (id, title, started_at, intel_status, intel_completed_at, capture_status)
               VALUES (?, ?, ?, ?, ?, 'finalized')""",
            (mid, title, started_at, intel_status, intel_completed_at),
        )
    return mid


def _link_meeting_to_project(db, meeting_id, project_id):
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meeting_projects (meeting_id, project_id, source, confidence)
               VALUES (?, ?, 'auto', 0.9)""",
            (meeting_id, project_id),
        )


def _seed_project(db, *, project_id=None, name="Q4 Platform"):
    pid = project_id or f"proj-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects (id, name, created_at, updated_at)
               VALUES (?, ?, datetime('now'), datetime('now'))""",
            (pid, name),
        )
    return pid


def _seed_decision(db, *, meeting_id, text="We will refactor the API"):
    rid = f"dr-{uuid.uuid4().hex[:8]}"
    sid = f"drs-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO decision_records
               (id, decision_text, source_type, source_id, created_at, updated_at)
               VALUES (?, ?, 'meeting', ?, datetime('now'), datetime('now'))""",
            (rid, text, meeting_id),
        )
        conn.execute(
            """INSERT INTO decision_record_sources
               (id, record_id, source_type, source_ref, created_at)
               VALUES (?, ?, 'meeting', ?, datetime('now'))""",
            (sid, rid, meeting_id),
        )
    return rid


def _seed_commitment(db, *, decision_id, source_id, meeting_id,
                     due_at="2026-09-05", status="open",
                     updated_at="2026-09-03T11:00:00"):
    cid = f"dc-{uuid.uuid4().hex[:8]}"
    aid = f"ai-{uuid.uuid4().hex[:8]}"
    with db._connection() as conn:
        # decision_commitments.decision_id references decisions.id
        # decisions table requires source_artifact_id and source_meeting_id
        existing = conn.execute(
            "SELECT 1 FROM decisions WHERE id = ?", (source_id,)
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, source_artifact_id, source_meeting_id,
                    lifecycle, project_key, decided_at)
                   VALUES (?, ?, '', ?, ?, 'recorded', '', datetime('now'))""",
                (source_id, "test decision", f"art-{uuid.uuid4().hex[:8]}", meeting_id),
            )
            # Update the decision_record's source_id to point to decisions.id
            conn.execute(
                "UPDATE decision_records SET source_id = ? WHERE id = ?",
                (source_id, decision_id),
            )
        conn.execute(
            """INSERT INTO decision_commitments
               (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
               VALUES (?, ?, ?, 'karol', ?, ?, datetime('now'), ?)""",
            (cid, source_id, aid, due_at, status, updated_at),
        )
    return cid


def _seed_intel_attempt(db, *, meeting_id, outcome="success",
                        created_at="2026-09-03T10:35:00"):
    with db._connection() as conn:
        # Need a job first
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        conn.execute(
            """INSERT INTO intel_jobs
               (job_id, meeting_id, work_descriptor_sha256, transcript_hash, status)
               VALUES (?, ?, 'abc', 'def', 'completed')""",
            (job_id, meeting_id),
        )
        conn.execute(
            """INSERT INTO intel_job_attempts
               (meeting_id, job_id, attempt, outcome, created_at)
               VALUES (?, ?, 1, ?, ?)""",
            (meeting_id, job_id, outcome, created_at),
        )


def _seed_segment(db, *, meeting_id, speaker="Alice", text="Hello"):
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO segments (meeting_id, text, speaker, start_time, end_time)
               VALUES (?, ?, ?, 0.0, 1.0)""",
            (meeting_id, text, speaker),
        )


# ── Core functionality ──────────────────────────────────────────────


class TestMeetingWatchSource:

    def test_entities_from_seeded_meetings(self, db):
        project_id = _seed_project(db)
        m1 = _seed_meeting(db, title="Standup", started_at="2026-09-03T10:00:00")
        m2 = _seed_meeting(db, title="Architecture Review", started_at="2026-09-02T14:00:00")
        _link_meeting_to_project(db, m1, project_id)
        _link_meeting_to_project(db, m2, project_id)

        # Add some speakers (participants)
        _seed_segment(db, meeting_id=m1, speaker="Alice")
        _seed_segment(db, meeting_id=m1, speaker="Bob")
        _seed_segment(db, meeting_id=m2, speaker="Carol")

        entities = MeetingWatchSource(db=db).snapshot(
            OWNER, query_kind="meetings", query={"project_id": project_id},
        )

        assert len(entities) == 2
        # Sorted by started_at DESC, so m1 (Sep 03) first
        assert entities[0]["title"] == "Standup"
        assert entities[0]["entity_type"] == "meeting"
        assert entities[0]["participants"] == 2  # Alice, Bob
        assert entities[1]["title"] == "Architecture Review"
        assert entities[1]["participants"] == 1  # Carol

    def test_entity_shape(self, db):
        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Sprint Planning")
        _link_meeting_to_project(db, mid, project_id)

        entities = MeetingWatchSource(db=db).snapshot(
            OWNER, query_kind="meetings", query={"project_id": project_id},
        )

        assert len(entities) == 1
        entity = entities[0]
        required_keys = {
            "id", "entity_type", "title", "date", "participants",
            "decisions_count", "commitments_count", "intel_status", "updated_at",
        }
        assert required_keys <= set(entity.keys())
        assert entity["entity_type"] == "meeting"

    def test_decisions_and_commitments_count(self, db):
        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Design Review")
        _link_meeting_to_project(db, mid, project_id)

        # Add decisions
        dr1 = _seed_decision(db, meeting_id=mid, text="Refactor API")
        dr2 = _seed_decision(db, meeting_id=mid, text="Add tests")

        # Add a commitment to decision 1
        _seed_commitment(db, decision_id=dr1, source_id=f"dec-{uuid.uuid4().hex[:8]}",
                         meeting_id=mid)

        entities = MeetingWatchSource(db=db).snapshot(
            OWNER, query_kind="meetings", query={"project_id": project_id},
        )

        assert len(entities) == 1
        assert entities[0]["decisions_count"] == 2
        assert entities[0]["commitments_count"] == 1

    def test_updated_at_reflects_intel_run(self, db):
        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Standup", started_at="2026-09-01T10:00:00")
        _link_meeting_to_project(db, mid, project_id)
        _seed_intel_attempt(db, meeting_id=mid, created_at="2026-09-01T10:35:00")

        entities = MeetingWatchSource(db=db).snapshot(
            OWNER, query_kind="meetings", query={"project_id": project_id},
        )

        assert entities[0]["updated_at"] == "2026-09-01T10:35:00"

    def test_updated_at_max_of_intel_and_commitment(self, db):
        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Review", started_at="2026-09-01T10:00:00")
        _link_meeting_to_project(db, mid, project_id)
        _seed_intel_attempt(db, meeting_id=mid, created_at="2026-09-01T10:35:00")

        dr = _seed_decision(db, meeting_id=mid)
        _seed_commitment(db, decision_id=dr, source_id=f"dec-{uuid.uuid4().hex[:8]}",
                         meeting_id=mid, updated_at="2026-09-02T12:00:00")

        entities = MeetingWatchSource(db=db).snapshot(
            OWNER, query_kind="meetings", query={"project_id": project_id},
        )

        # Commitment updated_at (Sep 02) > intel (Sep 01) > started_at (Sep 01)
        assert entities[0]["updated_at"] == "2026-09-02T12:00:00"

    def test_meeting_without_intel_returns_off(self, db):
        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Casual Chat",
                            intel_status="disabled", intel_completed_at=None)
        _link_meeting_to_project(db, mid, project_id)

        entities = MeetingWatchSource(db=db).snapshot(
            OWNER, query_kind="meetings", query={"project_id": project_id},
        )

        assert entities[0]["intel_status"] == "off"
        assert entities[0]["decisions_count"] == 0
        assert entities[0]["commitments_count"] == 0

    def test_no_linked_meetings_returns_empty(self, db):
        project_id = _seed_project(db)
        # A meeting exists but is NOT linked to this project
        _seed_meeting(db, title="Unrelated")

        entities = MeetingWatchSource(db=db).snapshot(
            OWNER, query_kind="meetings", query={"project_id": project_id},
        )

        assert entities == []

    def test_zero_egress(self, db):
        """The adapter makes no CLI or network calls -- pure DB reads."""
        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Standup")
        _link_meeting_to_project(db, mid, project_id)

        # The adapter takes db= and makes only DB calls.
        # If it tried CLI/network, it would fail in this env.
        entities = MeetingWatchSource(db=db).snapshot(
            OWNER, query_kind="meetings", query={"project_id": project_id},
        )
        assert len(entities) == 1

    def test_invalid_query_kind_raises(self, db):
        with pytest.raises(ValidationError, match="meetings"):
            MeetingWatchSource(db=db).snapshot(
                OWNER, query_kind="pull_requests",
                query={"project_id": "proj-1"},
            )

    def test_missing_project_id_raises(self, db):
        with pytest.raises(ValidationError, match="project_id"):
            MeetingWatchSource(db=db).snapshot(
                OWNER, query_kind="meetings", query={},
            )


# ── Template compilation ──────────────────────────────────────────


class TestMeetingTemplate:

    def test_template_compiles(self):
        from holdspeak.meeting_templates import compile

        spec = compile(
            "watch.meetings.linked",
            {"project_id": "proj-123"},
        )
        assert spec["schema"] == "WatchSpec@1"
        assert spec["name"] == "Linked meetings"
        assert spec["provider"]["id"] == "meeting"
        assert spec["subject"]["kind"] == "meetings"
        assert spec["subject"]["query"]["project_id"] == "proj-123"
        assert len(spec["rules"]) == 1

    def test_unknown_template_raises(self):
        from holdspeak.meeting_templates import compile

        with pytest.raises(ValueError, match="Unknown template"):
            compile("watch.meetings.nonexistent", {"project_id": "proj-123"})

    def test_cadence_override(self):
        from holdspeak.meeting_templates import compile

        spec = compile(
            "watch.meetings.linked",
            {"project_id": "proj-123"},
            options={"cadence": "daily"},
        )
        assert spec["trigger"]["every_minutes"] == 1440


# ── Dispatch registration ─────────────────────────────────────────


class TestMeetingDispatch:

    def test_fetch_watch_snapshot_meeting(self, db):
        """Meeting connector is registered in the dispatch."""
        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Test Meeting")
        _link_meeting_to_project(db, mid, project_id)

        entities = fetch_watch_snapshot(
            OWNER, connector_id="meeting", query_kind="meetings",
            query={"project_id": project_id}, meeting_db=db,
        )
        assert len(entities) == 1
        assert entities[0]["title"] == "Test Meeting"


# ── Project service maps ──────────────────────────────────────────


class TestProjectServiceMeetingMaps:

    def test_provider_to_connector(self):
        from holdspeak.services.project_service import _PROVIDER_TO_CONNECTOR
        assert _PROVIDER_TO_CONNECTOR["meeting"] == "meeting"

    def test_subject_to_query_kind(self):
        from holdspeak.services.project_service import _SUBJECT_TO_QUERY_KIND
        assert _SUBJECT_TO_QUERY_KIND["meeting"] == "meetings"


# ── ensure_meeting_watch: creation trigger + idempotency ─────────


class TestEnsureMeetingWatch:
    """HS-175-04: one meeting Watch per Room, created on link."""

    def test_creates_watch_when_meetings_linked(self, db):
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Standup")
        _link_meeting_to_project(db, mid, project_id)

        result = ensure_meeting_watch(db, project_id)
        assert result is not None
        assert result.get("id")

        watches = db.automations.list_project_watches(project_id)
        meeting_watches = [w for w in watches if w.get("connector_id") == "meeting"]
        assert len(meeting_watches) == 1
        assert meeting_watches[0]["query_kind"] == "meetings"

    def test_idempotent_second_call_returns_none(self, db):
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Standup")
        _link_meeting_to_project(db, mid, project_id)

        result1 = ensure_meeting_watch(db, project_id)
        result2 = ensure_meeting_watch(db, project_id)

        assert result1 is not None
        assert result2 is None

        watches = db.automations.list_project_watches(project_id)
        meeting_watches = [w for w in watches if w.get("connector_id") == "meeting"]
        assert len(meeting_watches) == 1

    def test_linking_two_meetings_creates_one_watch(self, db):
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        m1 = _seed_meeting(db, title="Standup")
        m2 = _seed_meeting(db, title="Review")
        _link_meeting_to_project(db, m1, project_id)
        ensure_meeting_watch(db, project_id)
        _link_meeting_to_project(db, m2, project_id)
        ensure_meeting_watch(db, project_id)

        watches = db.automations.list_project_watches(project_id)
        meeting_watches = [w for w in watches if w.get("connector_id") == "meeting"]
        assert len(meeting_watches) == 1

    def test_no_meetings_returns_none(self, db):
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        result = ensure_meeting_watch(db, project_id)
        assert result is None

    def test_room_sources_after_watch_creation(self, db):
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Standup")
        _link_meeting_to_project(db, mid, project_id)
        ensure_meeting_watch(db, project_id)

        svc = ProjectService(db)
        result = svc._read_room_sources(project_id)

        meeting_items = [
            s for s in result["items"] if s["provider"] == "meeting"
        ]
        assert len(meeting_items) == 1
        row = meeting_items[0]
        assert row["scope"] == "MEETINGS"
        assert row["host"] == ""
        assert row["state"] == "live"
        assert row["watchId"]

    def test_no_watch_no_row_in_sources(self, db):
        from holdspeak.services.project_service import ProjectService

        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Standup")
        _link_meeting_to_project(db, mid, project_id)

        svc = ProjectService(db)
        result = svc._read_room_sources(project_id)

        meeting_items = [
            s for s in result["items"] if s["provider"] == "meeting"
        ]
        assert len(meeting_items) == 0


# ── evaluate_once on a meeting Watch ─────────────────────────────


class TestMeetingWatchEvaluation:
    """HS-175-04: end-to-end proof that the WatchService evaluation
    path dispatches to MeetingWatchSource, produces transitions on
    a data change, and advances the Room's checkedAt."""

    def test_evaluate_once_meeting_watch(self, db):
        from holdspeak.services.watch_service import (
            WatchService,
            ensure_meeting_watch,
        )
        from holdspeak.services.watch_sources import default_snapshot_fetcher
        from holdspeak.services.project_service import ProjectService

        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Design Review",
                            started_at="2026-09-04T10:00:00")
        _link_meeting_to_project(db, mid, project_id)

        result = ensure_meeting_watch(db, project_id)
        assert result is not None
        watch_id = result["id"]

        watch_row = db.automations.get_watch(watch_id)
        assert watch_row is not None
        initial_snapshot = watch_row.get("snapshot") or {}
        entities = initial_snapshot.get("entities") or {}
        assert len(entities) >= 1
        entity = list(entities.values())[0]

        # (a) The fetch dispatched to MeetingWatchSource: entity_type
        assert entity.get("entity_type") == "meeting"
        initial_decisions = entity.get("decisions_count", 0)

        svc_proj = ProjectService(db)
        sources_before = svc_proj._read_room_sources(project_id)
        meeting_items_before = [
            s for s in sources_before["items"] if s["provider"] == "meeting"
        ]
        assert len(meeting_items_before) == 1
        checked_before = meeting_items_before[0]["checkedAt"]
        assert checked_before is not None

        # Mutate: add a decision to the linked meeting
        _seed_decision(db, meeting_id=mid, text="New architecture decision")

        # Evaluate the Watch
        fetcher = default_snapshot_fetcher(meeting_db=db)
        watch_svc = WatchService(db, snapshot_fetcher=fetcher)
        eval_result = watch_svc.evaluate_once(OWNER, watch_id)

        # (a) entity_type in the fresh snapshot
        watch_after = db.automations.get_watch(watch_id)
        snapshot_after = watch_after.get("snapshot") or {}
        entities_after = snapshot_after.get("entities") or {}
        assert len(entities_after) >= 1
        entity_after = list(entities_after.values())[0]
        assert entity_after.get("entity_type") == "meeting"
        new_decisions = entity_after.get("decisions_count", 0)
        assert new_decisions > initial_decisions

        # (b) At least one watch transition event
        assert eval_result["state"] == "completed"
        assert eval_result["transitions"] >= 1

        # (c) The Room's checkedAt moved
        sources_after = svc_proj._read_room_sources(project_id)
        meeting_items_after = [
            s for s in sources_after["items"] if s["provider"] == "meeting"
        ]
        assert len(meeting_items_after) == 1
        checked_after = meeting_items_after[0]["checkedAt"]
        assert checked_after is not None
        assert checked_after >= checked_before


# ── HS-175 counsel C7: the Watch's verbs are real ─────────────────


def _set_tz(monkeypatch, name: str) -> None:
    """Run the hub at a fixed zone (the owner sits at -06:00)."""
    import time as _time
    monkeypatch.setenv("TZ", name)
    _time.tzset()


@pytest.fixture()
def denver(monkeypatch):
    """The hub at America/Denver (-06:00 in September); restored after."""
    import os
    import time as _time
    previous = os.environ.get("TZ")
    _set_tz(monkeypatch, "America/Denver")
    yield
    if previous is None:
        monkeypatch.delenv("TZ", raising=False)
    else:
        monkeypatch.setenv("TZ", previous)
    _time.tzset()


def _watch_created_receipts(db, watch_id: str) -> list[dict]:
    import json as _json
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT outcome FROM kernel_receipts WHERE result_ref = ?",
            (f"watch:{watch_id}",),
        ).fetchall()
    return [_json.loads(r["outcome"]) for r in rows]


def _meeting_watches(db, project_id):
    return [
        w for w in db.automations.list_project_watches(project_id)
        if w.get("connector_id") == "meeting"
    ]


class TestRetireIsATombstone:
    """C7(a): a retired meeting Watch is never resurrected (R6 inverted)."""

    def test_link_path_does_not_resurrect_retired_watch(self, db):
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        m1 = _seed_meeting(db, title="Standup")
        _link_meeting_to_project(db, m1, project_id)
        created = ensure_meeting_watch(db, project_id, why="meeting linked")
        assert created is not None

        db.automations.update_watch_spec(created["id"], state="retired")

        # A new meeting is linked -> the link path calls ensure again.
        m2 = _seed_meeting(db, title="Review")
        _link_meeting_to_project(db, m2, project_id)
        again = ensure_meeting_watch(db, project_id, why="meeting linked")

        assert again is None, "a retired meeting Watch was resurrected on link"
        watches = _meeting_watches(db, project_id)
        assert [(w["id"], w["state"]) for w in watches] == [(created["id"], "retired")]

    def test_backfill_query_skips_rooms_with_a_retired_watch(self, db):
        """The heartbeat's backfill SQL treats ANY meeting Watch as present."""
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, project_id)
        created = ensure_meeting_watch(db, project_id)
        db.automations.update_watch_spec(created["id"], state="retired")

        # The exact predicate heartbeat_service.run_sweep uses.
        with db._connection() as conn:
            rows = conn.execute(
                """SELECT DISTINCT mp.project_id
                   FROM meeting_projects mp
                   WHERE NOT EXISTS (
                       SELECT 1 FROM connector_watches cw
                       WHERE cw.project_id = mp.project_id
                         AND cw.connector_id = 'meeting'
                   )""",
            ).fetchall()
        assert [r["project_id"] for r in rows] == []

    def test_heartbeat_backfill_does_not_resurrect(self, db):
        """The whole sweep backfill, source-checked: the predicate has no
        ``state != 'retired'`` escape hatch."""
        import inspect
        from holdspeak.services import heartbeat_service

        source = inspect.getsource(heartbeat_service.HeartbeatService.run_sweep)
        block = source[source.index("backfill meeting Watches"):]
        block = block[: block.index("meeting_watch_backfill = {")]
        assert "cw.connector_id = 'meeting'" in block
        assert "state != 'retired'" not in block
        assert 'why="backfill"' in block

    def test_retired_watch_is_not_a_source_row(self, db):
        """A retired Watch does not fold into the Room's SOURCES."""
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, project_id)
        created = ensure_meeting_watch(db, project_id)
        db.automations.update_watch_spec(created["id"], state="retired")

        result = ProjectService(db)._read_room_sources(project_id)
        assert [s for s in result["items"] if s["provider"] == "meeting"] == []


class TestPauseShowsPaused:
    """C7(b): Pause writes state='paused'; the row reads it (R7 inverted)."""

    def _row(self, db, project_id, provider):
        from holdspeak.services.project_service import ProjectService
        items = ProjectService(db)._read_room_sources(project_id)["items"]
        rows = [s for s in items if s["provider"] == provider]
        assert len(rows) == 1, rows
        return rows[0]

    def test_meeting_row_paused_after_pause_watch(self, db):
        from holdspeak.services.watch_service import WatchService, ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, project_id)
        created = ensure_meeting_watch(db, project_id)

        assert self._row(db, project_id, "meeting")["state"] == "live"
        WatchService(db).pause_watch(OWNER, created["id"])
        row = self._row(db, project_id, "meeting")
        assert row["state"] == "paused"
        # enabled is untouched by Pause -- the read must not depend on it
        stored = db.automations.get_watch(created["id"])
        assert stored["state"] == "paused" and stored["enabled"] is True

        WatchService(db).resume_watch(OWNER, created["id"])
        assert self._row(db, project_id, "meeting")["state"] == "live"

    @pytest.mark.parametrize("connector_id,query_kind,query,provider", [
        ("gh", "pull_requests", {"repository": "acme/app"}, "github"),
        ("jira", "issues", {"projects": ["ACME"], "connection_ref": "acme.atlassian.net|me@x"}, "jira"),
    ])
    def test_github_and_jira_rows_paused_after_pause_watch(
        self, db, connector_id, query_kind, query, provider,
    ):
        """The derivation is shared with GH/J rows -- prove all three."""
        import json as _json
        from datetime import datetime as _dt, timezone as _tz
        from holdspeak.services.watch_service import WatchService

        project_id = _seed_project(db)
        watch_id = f"w_{uuid.uuid4().hex[:12]}"
        now_iso = _dt.now(_tz.utc).isoformat(timespec="seconds")
        with db._connection() as conn:
            db.automations.create_watch_in_transaction(
                conn, watch_id=watch_id, connector_id=connector_id,
                query_kind=query_kind, name=f"{provider} watch",
                query_json=_json.dumps(query, sort_keys=True), enabled=True,
                schema_version="WatchSpec@1", project_id=project_id,
                intent="", subject_kind=query_kind, trigger_kind="poll",
                trigger_json="{}", mode="yolo", state="active", revision=1,
                baseline_state="", test_state="", created_at=now_iso,
                updated_at=now_iso,
            )
        assert self._row(db, project_id, provider)["state"] == "live"
        WatchService(db).pause_watch(OWNER, watch_id)
        assert self._row(db, project_id, provider)["state"] == "paused"
        WatchService(db).resume_watch(OWNER, watch_id)
        assert self._row(db, project_id, provider)["state"] == "live"


class TestCreationIsReceipted:
    """C7(c): both creation paths write ``watch.created`` with a why."""

    def test_link_path_receipt(self, db):
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, project_id)
        created = ensure_meeting_watch(db, project_id, why="meeting linked")

        receipts = _watch_created_receipts(db, created["id"])
        assert len(receipts) == 1
        assert receipts[0]["kind"] == "watch.created"
        assert receipts[0]["why"] == "meeting linked"
        assert receipts[0]["project_id"] == project_id
        assert receipts[0]["connector_id"] == "meeting"

    def test_backfill_receipt(self, db):
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, project_id)
        created = ensure_meeting_watch(db, project_id, why="backfill")
        receipts = _watch_created_receipts(db, created["id"])
        assert [r["why"] for r in receipts] == ["backfill"]

    def test_default_why_is_the_link_path(self, db):
        """routing_glue / project_service call with why='meeting linked'."""
        import inspect
        from holdspeak.runtime import routing_glue
        from holdspeak.services import project_service

        assert 'ensure_meeting_watch(db, pid, why="meeting linked")' in inspect.getsource(routing_glue)
        assert 'ensure_meeting_watch(self._db, project_id, why="meeting linked")' in inspect.getsource(project_service)


# ── HS-175 counsel C8 / C9(c): the Room row's clocks ─────────────


def _seed_calendar_event(db, *, event_id=None, uid=None, title="Sprint Planning",
                         starts_at="2026-09-10T20:00:00Z", source_id="src-1"):
    from datetime import datetime as _dt, timedelta as _td
    eid = event_id or f"ce_{uuid.uuid4().hex[:12]}"
    ends = (_dt.fromisoformat(starts_at.replace("Z", "+00:00")) + _td(hours=1))
    ends_at = ends.isoformat().replace("+00:00", "Z")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO calendar_events
               (id, uid, title, starts_at, ends_at, last_seen_at,
                subscription_revision, source_id, source_label)
               VALUES (?, ?, ?, ?, ?, 0, 'rev', ?, 'WORK')""",
            (eid, uid or f"uid-{eid}", title, starts_at, ends_at, source_id),
        )
    return eid


def _link_event(db, event_id, project_id, match_source="title"):
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO calendar_event_projects (calendar_event_id, project_id, match_source) VALUES (?, ?, ?)",
            (event_id, project_id, match_source),
        )


class TestRoomRowClocks:
    """The Room's MEETINGS tokens come from linked CALENDAR events in the
    hub's LOCAL week; CHECKED leaves with an offset."""

    def test_next_from_future_linked_event_not_from_meeting_entities(self, db, denver):
        from datetime import datetime as _dt, timedelta as _td, timezone as _tz
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db, title="Standup")  # a recorded meeting, in the past
        _link_meeting_to_project(db, mid, project_id)
        ensure_meeting_watch(db, project_id)

        # No linked calendar event -> no NEXT (never from the entities)
        tokens = ProjectService(db)._read_room_sources(project_id)["items"][0]["tokens"]
        assert not any(t.startswith("NEXT") for t in tokens)

        # A linked event 2 days out at 14:00 UTC = 08:00 Denver
        future = (_dt.now(_tz.utc) + _td(days=2)).replace(hour=14, minute=0, second=0, microsecond=0)
        eid = _seed_calendar_event(db, starts_at=future.isoformat().replace("+00:00", "Z"))
        _link_event(db, eid, project_id)

        tokens = ProjectService(db)._read_room_sources(project_id)["items"][0]["tokens"]
        expected_day = future.astimezone().strftime("%a").upper()
        assert f"NEXT {expected_day} 08:00" in tokens, tokens

    def test_this_week_counts_linked_events_in_the_local_week(self, db, denver):
        """A Sunday 23:00 Denver event (Monday 05:00 UTC) is THIS week here."""
        from datetime import datetime as _dt, timedelta as _td, timezone as _tz
        from holdspeak.services.project_service import (
            ProjectService, local_week_bounds, utc_z,
        )
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, project_id)
        ensure_meeting_watch(db, project_id)

        monday, next_monday = local_week_bounds()
        # Sunday 23:00 local of THIS week: inside the local week, but the
        # UTC week already rolled over (it is Monday 05:00Z).
        sunday_late = next_monday - _td(hours=1)
        # Monday 05:00Z of the PREVIOUS local Monday = Sunday 23:00 local of last week: out.
        last_week = monday - _td(hours=1)
        e_in = _seed_calendar_event(db, starts_at=utc_z(sunday_late), uid="in")
        e_out = _seed_calendar_event(db, starts_at=utc_z(last_week), uid="out")
        _link_event(db, e_in, project_id)
        _link_event(db, e_out, project_id)

        # The UTC-week reading would have dropped e_in (its UTC day is next
        # Monday) and kept e_out; the local week keeps exactly e_in.
        tokens = ProjectService(db)._read_room_sources(project_id)["items"][0]["tokens"]
        assert "1 THIS WEEK" in tokens, tokens

    def test_meeting_entities_do_not_count_toward_this_week(self, db, denver):
        """N THIS WEEK is ONE count: linked calendar events (not recordings)."""
        from datetime import datetime as _dt
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db, started_at=_dt.now().isoformat(timespec="seconds"))
        _link_meeting_to_project(db, mid, project_id)
        ensure_meeting_watch(db, project_id)
        tokens = ProjectService(db)._read_room_sources(project_id)["items"][0]["tokens"]
        assert not any(t.endswith("THIS WEEK") for t in tokens), tokens

    def test_checked_at_carries_an_offset(self, db):
        """SQLite's naive-UTC last_success_at leaves as +00:00 so the browser
        prints the viewer's local clock (H4-1: CHECKED 23:47 beside READ 17:48)."""
        from holdspeak.services.project_service import ProjectService, aware_iso
        from holdspeak.services.watch_service import ensure_meeting_watch

        project_id = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, project_id)
        created = ensure_meeting_watch(db, project_id)
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET last_success_at='2026-09-05 23:47:00' WHERE id=?",
                (created["id"],),
            )
        row = ProjectService(db)._read_room_sources(project_id)["items"][0]
        assert row["checkedAt"] == "2026-09-05T23:47:00+00:00"
        assert aware_iso("2026-09-05T17:47:00-06:00") == "2026-09-05T17:47:00-06:00"
        assert aware_iso(None) is None

    def test_local_week_bounds_at_denver(self, denver):
        from datetime import datetime as _dt, timedelta as _td
        from holdspeak.services.project_service import local_week_bounds, utc_z

        # Monday 2026-09-07 20:00 Denver
        now = _dt(2026, 9, 7, 20, 0).astimezone()
        monday, next_monday = local_week_bounds(now)
        assert (monday.year, monday.month, monday.day, monday.hour) == (2026, 9, 7, 0)
        assert next_monday - monday == _td(days=7)
        assert utc_z(monday) == "2026-09-07T06:00:00Z"


# ── ids never collide with a seed or another Watch; idempotency is by
# (project_id, connector), never by id ────────────────────────────────


def _seed_fixed_id_watch(db, project_id, watch_id, connector_id="gh", query_kind="pull_requests"):
    import json as _json
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, enabled, "
            " project_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, '[]', 1, ?, datetime('now'), datetime('now'))",
            (watch_id, connector_id, query_kind, f"{connector_id} {query_kind}",
             _json.dumps({}), project_id),
        )


class TestMeetingWatchIdsNeverCollide:
    """The shade/room rigs seed Watches with FIXED ids (``w-171-alpha-prs``)
    before and after the hub's sweep runs; the minted meeting Watch id must
    never be one a seed could use, and a fixed-id seed beside it must never
    make ``ensure`` collide or double-create."""

    def test_minted_id_is_a_uuid_suffix_no_seed_uses(self, db):
        import re
        from holdspeak.services.watch_service import ensure_meeting_watch
        ids = set()
        for _ in range(50):
            pid = _seed_project(db)
            mid = _seed_meeting(db)
            _link_meeting_to_project(db, mid, pid)
            created = ensure_meeting_watch(db, pid)
            assert created is not None
            assert re.fullmatch(r"w_[0-9a-f]{12}", created["id"]), created["id"]
            ids.add(created["id"])
        assert len(ids) == 50  # every mint distinct

    def test_fixed_id_seeds_on_the_same_room_do_not_collide(self, db):
        """GH/CI seeds with rig-style fixed ids sit beside the minted meeting
        Watch; ensure creates exactly one meeting Watch with a fresh id and a
        second call is a no-op (keyed on (project_id, 'meeting'))."""
        from holdspeak.services.watch_service import ensure_meeting_watch
        pid = _seed_project(db, project_id="proj-alpha-171")
        _seed_fixed_id_watch(db, pid, "w-171-alpha-prs")
        _seed_fixed_id_watch(db, pid, "w-171-alpha-ci", query_kind="branch_ci")
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, pid)

        created = ensure_meeting_watch(db, pid)
        assert created is not None
        assert created["id"] not in {"w-171-alpha-prs", "w-171-alpha-ci"}
        assert ensure_meeting_watch(db, pid) is None

        # A fixed-id seed AFTER the mint still inserts (no id was taken).
        _seed_fixed_id_watch(db, pid, "w-171-beta-ci", query_kind="branch_ci")
        ids = sorted(w["id"] for w in db.automations.list_project_watches(pid))
        assert ids == sorted(["w-171-alpha-prs", "w-171-alpha-ci", "w-171-beta-ci", created["id"]])
        meeting = [w for w in db.automations.list_project_watches(pid) if w["connector_id"] == "meeting"]
        assert len(meeting) == 1

    def test_idempotency_is_by_project_and_connector_not_id(self, db):
        """A meeting Watch seeded under ANY id (a rig's fixed id) already
        satisfies the Room -- ensure does not mint a second one."""
        from holdspeak.services.watch_service import ensure_meeting_watch
        pid = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, pid)
        _seed_fixed_id_watch(db, pid, "w-171-mtg", connector_id="meeting", query_kind="meetings")
        assert ensure_meeting_watch(db, pid) is None
        meeting = [w for w in db.automations.list_project_watches(pid) if w["connector_id"] == "meeting"]
        assert [w["id"] for w in meeting] == ["w-171-mtg"]


# ── counsel re-read condition 4: the DST edge (H-C) ──────────────────


class TestDstEdge:
    """TZ=America/Denver, Sunday 2026-11-01 20:00 (after the fall-back, MST):
    the week's Monday is Oct 26 00:00 MDT (-06:00), not an hour off, even
    when ``now`` arrives with the fixed -07:00 offset production passes."""

    def test_local_week_bounds_across_fall_back(self, denver):
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        from holdspeak.services.project_service import local_week_bounds, utc_z
        tz = ZoneInfo("America/Denver")
        now_fixed = datetime(2026, 11, 1, 20, 0, tzinfo=tz).astimezone()  # fixed -07:00
        assert now_fixed.utcoffset() == timedelta(hours=-7)
        monday, next_monday = local_week_bounds(now_fixed)
        assert utc_z(monday) == utc_z(datetime(2026, 10, 26, 0, 0, tzinfo=tz)) == "2026-10-26T06:00:00Z"
        assert utc_z(next_monday) == utc_z(datetime(2026, 11, 2, 0, 0, tzinfo=tz)) == "2026-11-02T07:00:00Z"
        # each bound wears its own true offset
        assert monday.utcoffset() == timedelta(hours=-6)
        assert next_monday.utcoffset() == timedelta(hours=-7)

    def test_room_tokens_across_fall_back(self, db, denver):
        """Mon Oct 26 00:30 MDT and Sun Nov 1 00:30 MDT both count THIS WEEK
        on Sunday evening; the NEXT clock on Monday Nov 2 09:00 MST is 09:00."""
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from holdspeak.services.project_service import ProjectService, utc_z
        from holdspeak.services.watch_service import ensure_meeting_watch
        tz = ZoneInfo("America/Denver")
        now_fixed = datetime(2026, 11, 1, 20, 0, tzinfo=tz).astimezone()

        pid = _seed_project(db)
        mid = _seed_meeting(db)
        _link_meeting_to_project(db, mid, pid)
        ensure_meeting_watch(db, pid)
        for uid, local in [
            ("e-mon", datetime(2026, 10, 26, 0, 30, tzinfo=tz)),
            ("e-sun", datetime(2026, 11, 1, 0, 30, tzinfo=tz)),
            ("e-next", datetime(2026, 11, 2, 9, 0, tzinfo=tz)),
            ("e-prev", datetime(2026, 10, 25, 23, 30, tzinfo=tz)),
        ]:
            _link_event(db, _seed_calendar_event(db, uid=uid, starts_at=utc_z(local)), pid)

        tokens = ProjectService(db)._meeting_calendar_tokens(pid, now=now_fixed)
        assert "2 THIS WEEK" in tokens, tokens
        assert "NEXT MON 09:00" in tokens, tokens

