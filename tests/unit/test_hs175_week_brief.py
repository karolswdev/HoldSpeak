"""HS-175-05: The week brief -- two-window design and new collectors.

Proves:
- compute_window UNCHANGED: lookback to the preceding close.
- compute_lookahead: now to Sunday 23:59 (the THIS WEEK section).
- Calendar events collector returns events in the week range.
- Meeting watch collector returns decisions/commitments counts.
- Daily fallback without a calendar (empty collector results).
- The brief's totals are correct.
"""
from __future__ import annotations

import datetime
import time
import uuid

import pytest

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.monday_brief_service import MondayBriefService

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture()
def db(tmp_path):
    return Database(tmp_path / "test.db")


# ── compute_window (UNCHANGED) ─────────────────────────────────────
# The lookback is NOT widened. These tests confirm it stayed the same.
# Sep 2026 calendar:
#   Mon Tue Wed Thu Fri Sat Sun
#        1   2   3   4   5   6
#    7   8   9  10  11  12  13


class TestComputeWindowUnchanged:

    def test_monday_still_looks_back_to_friday(self, db):
        """On Monday Sep 7, period_start is Friday Sep 4 at 17:00."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 9, 30, 0)
        assert now.weekday() == 0  # Monday
        start, end = svc.compute_window(now)

        assert start == datetime.datetime(2026, 9, 4, 17, 0)
        assert end == now

    def test_wednesday_looks_back_to_tuesday(self, db):
        """On Wednesday Sep 2, period_start is Tuesday Sep 1 at 17:00."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 2, 14, 30, 0)
        assert now.weekday() == 2  # Wednesday
        start, end = svc.compute_window(now)

        assert start == datetime.datetime(2026, 9, 1, 17, 0)
        assert end == now


# ── compute_lookahead (NEW) ─────────────────────────────────────────


class TestComputeLookahead:

    def test_wednesday_to_sunday(self, db):
        """On Wednesday Sep 2 2026, look-ahead extends to Sunday Sep 6."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 2, 14, 30, 0)
        assert now.weekday() == 2  # Wednesday
        start, end = svc.compute_lookahead(now)

        assert start == now
        assert end.weekday() == 6  # Sunday
        assert end.date() == datetime.date(2026, 9, 6)
        assert end.hour == 23 and end.minute == 59

    def test_monday_to_sunday(self, db):
        """On Monday Sep 7, look-ahead extends to Sunday Sep 13."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 8, 0, 0)
        assert now.weekday() == 0
        _, end = svc.compute_lookahead(now)

        assert end.date() == datetime.date(2026, 9, 13)

    def test_sunday_to_same_sunday(self, db):
        """On Sunday Sep 6, the look-ahead end is Sunday Sep 6 23:59."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 6, 10, 0, 0)
        assert now.weekday() == 6  # Sunday
        _, end = svc.compute_lookahead(now)

        assert end.date() == datetime.date(2026, 9, 6)
        assert end.hour == 23

    def test_default_now_is_tz_aware(self, db):
        """When no `now` is passed, the default is tz-aware local time."""
        svc = MondayBriefService(db)
        start, end = svc.compute_lookahead()

        assert start.tzinfo is not None, "Default now should be tz-aware"
        assert end.tzinfo is not None, "End should inherit tzinfo from now"


# ── Calendar events collector ───────────────────────────────────────


class TestCollectCalendarEvents:

    def _seed_calendar_event(self, db, *, event_id=None, title="Standup",
                             starts_at="2026-09-03T10:00:00",
                             meeting_url=None, uid=None):
        eid = event_id or f"evt-{uuid.uuid4().hex[:8]}"
        uid_val = uid or f"uid-{uuid.uuid4().hex[:8]}"
        ends_at = starts_at[:11] + "11:00:00"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES (?, ?, ?, ?, ?, ?, 'rev1', 'src1', 'WORK')""",
                (eid, uid_val, title, starts_at, ends_at, 1000.0),
            )
        return eid

    def test_counts_events_in_range(self, db):
        svc = MondayBriefService(db)
        self._seed_calendar_event(db, title="Standup", starts_at="2026-09-01T10:00:00")
        self._seed_calendar_event(db, title="Review", starts_at="2026-09-03T14:00:00")
        # Event outside range (next week)
        self._seed_calendar_event(db, title="Next Week", starts_at="2026-09-14T10:00:00")

        items = svc._collect_calendar_events(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-09-03T08:00:00",
        )

        total_items = [i for i in items if i.source_ref == "calendar:week"]
        assert len(total_items) == 1
        assert "2 meetings this week" in total_items[0].text
        assert total_items[0].section == "this_week"

    def test_next_event_after_now(self, db):
        svc = MondayBriefService(db)
        self._seed_calendar_event(db, title="Past Standup", starts_at="2026-09-01T10:00:00")
        self._seed_calendar_event(db, title="Upcoming Review", starts_at="2026-09-04T14:00:00")

        items = svc._collect_calendar_events(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-09-03T08:00:00",
        )

        next_items = [i for i in items if i.text.startswith("Next:")]
        assert len(next_items) == 1
        assert "Upcoming Review" in next_items[0].text

    def test_empty_when_no_events(self, db):
        svc = MondayBriefService(db)
        items = svc._collect_calendar_events(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-09-03T08:00:00",
        )
        assert items == []

    def test_armed_count(self, db):
        svc = MondayBriefService(db)
        eid = self._seed_calendar_event(db, title="Team Standup",
                                        starts_at="2026-09-04T10:00:00",
                                        meeting_url="https://teams.example.com/join")

        # Seed an armed scheduled recording linked to this event
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO scheduled_recordings
                   (id, title, cron_expr, enabled, next_fire_at, state,
                    calendar_event_id, calendar_uid, calendar_source_id,
                    created_at)
                   VALUES (?, 'Team Standup', '0 55 9 * * *', 1, ?, 'idle',
                           ?, 'uid1', 'src1', ?)""",
                (f"sr-{uuid.uuid4().hex[:8]}", time.time(),
                 eid, time.time()),
            )

        items = svc._collect_calendar_events(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-09-03T08:00:00",
        )

        armed_items = [i for i in items if i.source_ref == "calendar:armed"]
        assert len(armed_items) == 1
        assert "1 armed" in armed_items[0].text


# ── Meeting watch collector ─────────────────────────────────────────


class TestCollectMeetingWatch:

    def _seed_decision_record(self, db, *, meeting_id, text="Decision",
                              created_at="2026-09-03T11:00:00"):
        rid = f"dr-{uuid.uuid4().hex[:8]}"
        sid = f"drs-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decision_records
                   (id, decision_text, source_type, source_id, created_at, updated_at)
                   VALUES (?, ?, 'meeting', ?, ?, ?)""",
                (rid, text, meeting_id, created_at, created_at),
            )
            conn.execute(
                """INSERT INTO decision_record_sources
                   (id, record_id, source_type, source_ref, created_at)
                   VALUES (?, ?, 'meeting', ?, ?)""",
                (sid, rid, meeting_id, created_at),
            )
        return rid

    def _seed_commitment(self, db, *, due_at="2026-09-04", status="open"):
        cid = f"dc-{uuid.uuid4().hex[:8]}"
        did = f"d-{uuid.uuid4().hex[:8]}"
        aid = f"ai-{uuid.uuid4().hex[:8]}"
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, source_artifact_id, source_meeting_id,
                    lifecycle, project_key, decided_at)
                   VALUES (?, 'test', '', ?, '', 'recorded', '', datetime('now'))""",
                (did, art_id),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                   VALUES (?, ?, ?, 'karol', ?, ?, datetime('now'), datetime('now'))""",
                (cid, did, aid, due_at, status),
            )
        return cid

    def test_new_decisions(self, db):
        svc = MondayBriefService(db)
        mid = f"mtg-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO meetings
                   (id, title, started_at, capture_status)
                   VALUES (?, 'Test', '2026-09-03T10:00:00', 'finalized')""",
                (mid,),
            )
        self._seed_decision_record(db, meeting_id=mid, created_at="2026-09-03T11:00:00")
        self._seed_decision_record(db, meeting_id=mid, created_at="2026-09-03T11:05:00")

        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            "2026-08-31T00:00:00",
        )

        decision_items = [i for i in items if "decision" in i.text.lower()]
        assert len(decision_items) == 1
        assert "2 new decisions" in decision_items[0].text

    def test_commitments_due_this_week(self, db):
        svc = MondayBriefService(db)
        self._seed_commitment(db, due_at="2026-09-02", status="open")
        self._seed_commitment(db, due_at="2026-09-04", status="open")
        # Commitment outside the week
        self._seed_commitment(db, due_at="2026-09-10", status="open")

        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59",
            None,
        )

        due_items = [i for i in items if "commitment" in i.text.lower() and "due" in i.text.lower()]
        assert len(due_items) == 1
        assert "2 commitments due this week" in due_items[0].text

    def test_empty_when_no_data(self, db):
        svc = MondayBriefService(db)
        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59", None,
        )
        assert items == []


# ── Integration: brief generation ───────────────────────────────────


class TestBriefGenerationThisWeek:

    def test_generate_lookback_unchanged(self, db):
        """The generated brief's lookback (period_start) is unchanged."""
        svc = MondayBriefService(db)
        # Thursday Sep 3 2026 -- lookback to Wednesday Sep 2 17:00
        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        assert now.weekday() == 3  # Thursday
        brief = svc.generate(OWNER, now=now)

        start_dt = datetime.datetime.fromisoformat(brief.period_start)
        # Lookback: Thursday -> previous day 17:00 = Wednesday 17:00
        assert start_dt == datetime.datetime(2026, 9, 2, 17, 0)

    def test_sections_include_this_week(self, db):
        """The generated brief always has a this_week key in sections."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        brief = svc.generate(OWNER, now=now)

        assert "this_week" in brief.sections
        assert isinstance(brief.sections["this_week"], list)

    def test_calendar_items_land_in_this_week(self, db):
        """Calendar event items go to this_week, not changed."""
        svc = MondayBriefService(db)
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES ('evt1', 'uid1', 'Standup',
                           '2026-09-04T10:00:00', '2026-09-04T11:00:00',
                           1000.0, 'rev1', 'src1', 'WORK')"""
            )

        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        brief = svc.generate(OWNER, now=now)

        tw = brief.sections["this_week"]
        cal_items = [i for i in tw if i.source_ref and "calendar" in i.source_ref]
        assert len(cal_items) > 0, "Calendar items should be in this_week section"

        changed = brief.sections["changed"]
        cal_in_changed = [i for i in changed if i.source_ref and "calendar" in i.source_ref]
        assert len(cal_in_changed) == 0, "Calendar items should NOT be in changed section"

    def test_meeting_watch_items_land_in_this_week(self, db):
        """Meeting watch (commitments due) items go to this_week."""
        svc = MondayBriefService(db)
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, source_artifact_id, source_meeting_id,
                    lifecycle, project_key, decided_at)
                   VALUES ('d1', 'test', '', ?, '', 'recorded', '', datetime('now'))""",
                (art_id,),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status,
                    created_at, updated_at)
                   VALUES ('dc1', 'd1', 'ai1', 'karol', '2026-09-04',
                           'open', datetime('now'), datetime('now'))"""
            )

        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        brief = svc.generate(OWNER, now=now)

        tw = brief.sections["this_week"]
        watch_items = [i for i in tw if i.source_ref and "meeting_watch" in i.source_ref]
        assert len(watch_items) > 0, "Meeting watch items should be in this_week"

    def test_headline_includes_meeting_count(self, db):
        """When calendar events exist, the headline includes meeting count."""
        svc = MondayBriefService(db)
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES ('evt1', 'uid1', 'Standup',
                           '2026-09-04T10:00:00', '2026-09-04T11:00:00',
                           1000.0, 'rev1', 'src1', 'WORK')"""
            )
            conn.execute(
                """INSERT INTO calendar_events
                   (id, uid, title, starts_at, ends_at, last_seen_at,
                    subscription_revision, source_id, source_label)
                   VALUES ('evt2', 'uid2', 'Review',
                           '2026-09-05T14:00:00', '2026-09-05T15:00:00',
                           1000.0, 'rev1', 'src1', 'WORK')"""
            )

        now = datetime.datetime(2026, 9, 3, 14, 0, 0)
        brief = svc.generate(OWNER, now=now)

        assert "2 meetings this week" in brief.headline

    def test_commitment_detail_includes_text_and_date(self, db):
        """Commitment due item carries the first commitment's text + date."""
        svc = MondayBriefService(db)
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions
                   (id, text, rationale, source_artifact_id, source_meeting_id,
                    lifecycle, project_key, decided_at)
                   VALUES ('d1', 'Ania owns the API spec', '', ?, '', 'recorded', '', datetime('now'))""",
                (art_id,),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status,
                    created_at, updated_at)
                   VALUES ('dc1', 'd1', 'ai1', 'karol', '2026-09-04',
                           'open', datetime('now'), datetime('now'))"""
            )

        items = svc._collect_meeting_watch(
            "2026-08-31T00:00:00", "2026-09-06T23:59:59", None,
        )

        due_items = [i for i in items if i.source_ref == "meeting_watch:commitments_due"]
        assert len(due_items) == 1
        assert due_items[0].detail is not None
        assert "Ania owns the API spec" in due_items[0].detail
        assert "2026-09-04" in due_items[0].detail
