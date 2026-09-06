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


# -- HS-175 counsel-on-built C11: the two windows as ruled -------------------
#
# - compute_window is byte-identical (its body digest is pinned).
# - the forward half reads [now, Sunday 23:59], never from Monday 00:00.
# - boundaries are UTC-normalised against the UTC-stored starts_at; a naive
#   local `now` (what the cadence and the route pass) is read as local.
# - an occurrence already recorded in the lookback is deduped out.
# - _compose counts calendar items as meetings / armed / due, never "watch items".

import ast
import hashlib
import inspect
import textwrap

from holdspeak.services.monday_brief_service import BriefItem

UTC = datetime.timezone.utc
COMPUTE_WINDOW_BODY_SHA256 = "2a4925ac6b2f80ae2d3061b52a148af34af7a2cc03c0171d55f7a792c02b4a9f"


def _seed_utc_event(db, eid: str, title: str, starts_at: str, *, uid: str | None = None) -> None:
    """Seed the production shape: starts_at/ends_at stored as UTC '+00:00'."""
    start = datetime.datetime.fromisoformat(starts_at)
    end = (start + datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO calendar_events
               (id, uid, title, starts_at, ends_at, last_seen_at,
                subscription_revision, source_id, source_label)
               VALUES (?, ?, ?, ?, ?, 1000.0, 'rev1', 'src1', 'WORK')""",
            (eid, uid or f"uid-{eid}", title, starts_at, end),
        )


def _seed_recorded_meeting(db, mid: str, *, calendar_event_id: str, started_at: str, ended_at: str) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO meetings (id, title, started_at, ended_at, capture_status, calendar_event_id)
               VALUES (?, 'Recorded', ?, ?, 'finalized', ?)""",
            (mid, started_at, ended_at, calendar_event_id),
        )


def _this_week(brief, ref: str):
    return [i for i in brief.sections["this_week"] if i.source_ref == ref]


class TestComputeWindowByteIdentical:
    def test_body_digest_pinned(self, db):
        """The SINCE FRIDAY half is untouched: the body (docstring stripped)
        hashes to the digest counsel verified against be6c630e."""
        src = textwrap.dedent(inspect.getsource(MondayBriefService.compute_window))
        fn = ast.parse(src).body[0]
        body = fn.body
        if isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
            body = body[1:]
        digest = hashlib.sha256(
            ast.unparse(ast.Module(body=body, type_ignores=[])).encode()
        ).hexdigest()
        assert digest == COMPUTE_WINDOW_BODY_SHA256


class TestForwardHalfReadsFromNow:
    def test_monday_afternoon_counts_only_what_is_coming(self, db):
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)  # Monday
        _seed_utc_event(db, "e-past", "Morning sync", "2026-09-07T10:00:00+00:00")  # this week, already past
        _seed_utc_event(db, "e-next", "Design review", "2026-09-08T09:00:00+00:00")
        _seed_utc_event(db, "e-sun", "Sunday late", "2026-09-13T23:30:00+00:00")  # inside Sunday 23:59
        _seed_utc_event(db, "e-mon", "Next Monday", "2026-09-14T00:30:00+00:00")  # next week

        brief = svc.generate(OWNER, now=now)

        assert _this_week(brief, "calendar:week")[0].text == "2 meetings this week"
        nxt = [i for i in brief.sections["this_week"] if i.text.startswith("Next:")]
        assert [i.text for i in nxt] == ["Next: Design review at 09:00"]
        assert "2 meetings this week" in brief.headline
        assert "watch item" not in brief.headline
        # The lookback is untouched: Monday still opens at Friday 17:00.
        assert brief.period_start == datetime.datetime(2026, 9, 4, 17, 0, tzinfo=UTC).isoformat()

    def test_naive_local_now_is_read_as_local(self, db, monkeypatch):
        """Counsel H6-1 inverted: under TZ=Europe/Warsaw a naive Saturday
        10:00 local `now` counts the two Saturday meetings and NOT next
        Monday's 00:30 local one; `Next:` is one hour away, in local time."""
        monkeypatch.setenv("TZ", "Europe/Warsaw")
        time.tzset()
        try:
            svc = MondayBriefService(db)
            _seed_utc_event(db, "e-11", "Standup", "2026-09-05T09:00:00+00:00")   # Sat 11:00 local
            _seed_utc_event(db, "e-15", "Review", "2026-09-05T13:00:00+00:00")    # Sat 15:00 local
            _seed_utc_event(db, "e-mon", "Next-week planning", "2026-09-06T22:30:00+00:00")  # Mon 00:30 local

            brief = svc.generate(OWNER, now=datetime.datetime(2026, 9, 5, 10, 0))  # naive, Saturday

            assert _this_week(brief, "calendar:week")[0].text == "2 meetings this week"
            nxt = [i for i in brief.sections["this_week"] if i.text.startswith("Next:")]
            assert [i.text for i in nxt] == ["Next: Standup at 11:00"]
        finally:
            monkeypatch.undo()
            time.tzset()

    def test_commitment_due_today_counts_and_next_week_does_not(self, db):
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)  # Monday
        art = f"art-{uuid.uuid4().hex[:8]}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions (id, text, rationale, source_artifact_id, source_meeting_id,
                                          lifecycle, project_key, decided_at)
                   VALUES ('d1', 'Ship the spec', '', ?, '', 'recorded', '', datetime('now'))""",
                (art,),
            )
            for cid, due in (("dc-today", "2026-09-07"), ("dc-sun", "2026-09-13"), ("dc-next", "2026-09-14")):
                conn.execute(
                    """INSERT INTO decision_commitments
                       (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                       VALUES (?, 'd1', ?, 'karol', ?, 'open', datetime('now'), datetime('now'))""",
                    (cid, f"ai-{cid}", due),
                )

        brief = svc.generate(OWNER, now=now)

        due = _this_week(brief, "meeting_watch:commitments_due")
        assert [i.text for i in due] == ["2 commitments due this week"]
        assert "2 commitments due" in brief.headline


class TestRecordedOccurrenceDedup:
    def test_recorded_occurrence_is_since_fridays_not_this_weeks(self, db):
        """The calendar_uid dedup, occurrence-scoped: an event whose
        recording already sits in the lookback as `Meeting recorded` is
        neither counted nor named in THIS WEEK."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)
        _seed_utc_event(db, "e-a", "Standup", "2026-09-07T15:00:00+00:00")  # still 'coming' by the clock
        _seed_utc_event(db, "e-b", "Review", "2026-09-08T09:00:00+00:00")
        # The owner started the armed row early and stopped it: recorded, inside the lookback.
        _seed_recorded_meeting(
            db, "m-a", calendar_event_id="e-a",
            started_at="2026-09-07T13:40:00+00:00", ended_at="2026-09-07T13:58:00+00:00",
        )

        brief = svc.generate(OWNER, now=now)

        assert _this_week(brief, "calendar:week")[0].text == "1 meeting this week"
        assert [i.source_ref for i in brief.sections["this_week"] if i.text.startswith("Next:")] == ["calendar_event:e-b"]
        assert any(i.text.startswith("Meeting recorded") for i in brief.sections["changed"])

    def test_recurring_series_next_occurrence_survives(self, db):
        """Dedup by uid ALONE would hide Tuesday's standup because Monday's
        was recorded; the occurrence key keeps it."""
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)
        _seed_utc_event(db, "e-mon", "Standup", "2026-09-07T09:00:00+00:00", uid="series-1")
        _seed_utc_event(db, "e-tue", "Standup", "2026-09-08T09:00:00+00:00", uid="series-1")
        _seed_recorded_meeting(
            db, "m-mon", calendar_event_id="e-mon",
            started_at="2026-09-07T08:55:00+00:00", ended_at="2026-09-07T09:30:00+00:00",
        )

        brief = svc.generate(OWNER, now=now)

        assert _this_week(brief, "calendar:week")[0].text == "1 meeting this week"
        assert [i.source_ref for i in brief.sections["this_week"] if i.text.startswith("Next:")] == ["calendar_event:e-tue"]


class TestComposeCountsCalendarItems:
    def test_headline_names_meetings_armed_and_due(self):
        """Counsel's repro_compose inverted: no 'watch items' on a desk with
        zero Watch changes; `Next:` is detail, not a count."""
        svc = MondayBriefService(db=None)
        tw = [
            BriefItem("a", "this_week", "3 meetings this week", source_ref="calendar:week", priority=60),
            BriefItem("b", "this_week", "Next: Standup at 07:00", source_ref="calendar_event:x", priority=55),
            BriefItem("c", "this_week", "2 armed", source_ref="calendar:armed", priority=53),
            BriefItem("d", "this_week", "1 commitment due this week", detail="Ship v2 | 2026-09-04",
                      source_ref="meeting_watch:commitments_due", priority=51),
        ]
        headline, _ = svc._compose(
            {"this_week": tw, "changed": [], "broke": [], "waiting": [], "decisions": []}
        )
        assert headline == "3 meetings this week, 2 armed, 1 commitment due."

    def test_headline_with_decisions(self):
        svc = MondayBriefService(db=None)
        tw = [
            BriefItem("a", "this_week", "1 meeting this week", source_ref="calendar:week", priority=60),
            BriefItem("e", "this_week", "2 new decisions from meetings", source_ref="meeting_watch:decisions", priority=52),
        ]
        headline, _ = svc._compose(
            {"this_week": tw, "changed": [], "broke": [], "waiting": [], "decisions": []}
        )
        assert headline == "1 meeting this week, 2 new decisions."


class TestCommitmentSaidOnce:
    """C11 follow-up: a commitment THIS WEEK counts is dropped from the
    lookback's `Commitment due` items -- dedup by commitment id, not text."""

    def _seed(self, db, cid: str, due: str, text: str) -> None:
        art = f"art-{uuid.uuid4().hex[:8]}"
        did = f"d-{cid}"
        with db._connection() as conn:
            conn.execute(
                """INSERT INTO decisions (id, text, rationale, source_artifact_id, source_meeting_id,
                                          lifecycle, project_key, decided_at)
                   VALUES (?, ?, '', ?, '', 'recorded', '', datetime('now'))""",
                (did, text, art),
            )
            conn.execute(
                """INSERT INTO decision_commitments
                   (id, decision_id, action_item_id, owner, due_at, status, created_at, updated_at)
                   VALUES (?, ?, ?, 'karol', ?, 'open', datetime('now'), datetime('now'))""",
                (cid, did, f"ai-{cid}", due),
            )

    def test_commitment_due_today_appears_once_in_this_week(self, db):
        svc = MondayBriefService(db)
        now = datetime.datetime(2026, 9, 7, 14, 0, tzinfo=UTC)  # Monday
        self._seed(db, "dc-today", "2026-09-07", "Ship the spec")   # THIS WEEK's
        self._seed(db, "dc-past", "2026-09-01", "Ship the spec")    # overdue: the lookback's, same TEXT

        brief = svc.generate(OWNER, now=now)

        due = _this_week(brief, "meeting_watch:commitments_due")
        assert [i.text for i in due] == ["1 commitment due this week"]
        lookback_due = [i for i in brief.sections["decisions"] if i.text.startswith("Commitment due")]
        # The same text is no dedup key: the overdue one (a different id) stays.
        assert [i.text for i in lookback_due] == ["Commitment due 2026-09-01: Ship the spec"]
        assert not any("2026-09-07" in i.text for i in lookback_due)


class TestShadeReadOfSeededBrief:
    """The shade's read (GET /api/brief/latest) of the hs171 shade rig's seed
    (tests/e2e/test_hs171_shade_glass.py::_seed_brief): a brief row with four
    `waiting` items, generated_at = naive local now.  Mirrored here against
    the route, then a hub-like cadence `generate()` (naive local `now`, the
    same local day) runs AFTER the seed -- the shade must still see the
    seeded brief with its four items.

    The rig hardcodes period_end='2026-09-05'; this test seeds today's date
    so it says what the rig means on any day (a cadence generate on a later
    local day writes a newer brief, which is the shade's own hazard, not
    the seed's)."""

    def _client(self, db, monkeypatch):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from holdspeak.web.routes import monday_brief as brief_routes

        monkeypatch.setattr(brief_routes, "get_database", lambda: db)
        monkeypatch.setattr(brief_routes, "get_observer", lambda: None)
        app = FastAPI()
        app.include_router(brief_routes.build_monday_brief_router(None))
        return TestClient(app)

    def test_latest_returns_the_seed_before_and_after_a_hub_generate(self, db, monkeypatch):
        client = self._client(db, monkeypatch)
        assert client.get("/api/brief/latest").json() is None

        today = datetime.date.today().isoformat()
        brief_id = str(uuid.uuid4())
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO monday_briefs (id, period_start, period_end, headline, generated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (brief_id, "2026-09-01", today, "4 things this week", datetime.datetime.now().isoformat()),
            )
            for i in range(4):
                conn.execute(
                    "INSERT INTO monday_brief_items (id, brief_id, section, text, priority) "
                    "VALUES (?, ?, 'waiting', ?, 0)",
                    (f"brief-item-{i}", brief_id, f"Item {i + 1}"),
                )

        def shade_sees(payload):
            sections = payload["sections"]
            return (
                payload["id"], payload["is_empty"],
                sum(len(v) for v in sections.values()), len(sections.get("this_week", [])),
            )

        first = client.get("/api/brief/latest")
        assert first.status_code == 200
        assert shade_sees(first.json()) == (brief_id, False, 4, 0)

        # The hub's cadence regenerates with a naive local `now` (runtime/cadence.py:112-121).
        generated = MondayBriefService(db).generate(None, now=datetime.datetime.now())
        assert generated.id == brief_id, "same local day: generate() returns the seed, writes no row"

        again = client.get("/api/brief/latest")
        assert again.status_code == 200
        assert shade_sees(again.json()) == (brief_id, False, 4, 0)
        assert client.post("/api/brief/generate").status_code == 200


class TestComposeNeverPrintsABareStop:
    def test_next_row_alone_is_one_item(self):
        """Counsel's H-E: a this_week holding only a `Next:` row (impossible
        in the product) must not headline as '.'."""
        svc = MondayBriefService(db=None)
        tw = [BriefItem("b", "this_week", "Next: Standup at 07:00", source_ref="calendar_event:x", priority=55)]
        headline, _ = svc._compose(
            {"this_week": tw, "changed": [], "broke": [], "waiting": [], "decisions": []}
        )
        assert headline == "1 item this week."
