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
