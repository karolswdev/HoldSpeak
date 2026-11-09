# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_event_linked_provenance.py to restore.

# ruff: noqa


# --- TestWebServerLambdaCalendarEventId: P2: copies a lambda from web_server.py into the test and tests the copy against a fake
class TestWebServerLambdaCalendarEventId:
    """The web_server lambda accepts calendar_event_id kwarg and sets it
    on the callbacks object."""

    def test_lambda_sets_pending_calendar_event_id(self):
        """Proves the lambda signature and setattr behavior."""

        class FakeCallbacks:
            pending_title: Optional[str] = None
            pending_calendar_event_id: Optional[str] = None
            _start_meeting_called = False

            def _start_meeting(self, *, principal=None):
                self._start_meeting_called = True

        callbacks = FakeCallbacks()

        # Reproduce the lambda from web_server.py:986-991
        start_meeting_fn = lambda principal, title, calendar_event_id=None: (
            setattr(callbacks, "pending_title", title) or
            setattr(callbacks, "pending_calendar_event_id", calendar_event_id or None) or
            callbacks._start_meeting(principal=principal)
        )

        principal = Principal(PrincipalKind.SCHEDULER, "sr:test")

        # With calendar_event_id
        start_meeting_fn(
            principal=principal,
            title="Sprint Review",
            calendar_event_id="ce_lambda_test",
        )
        assert callbacks.pending_title == "Sprint Review"
        assert callbacks.pending_calendar_event_id == "ce_lambda_test"
        assert callbacks._start_meeting_called

    def test_lambda_none_when_no_event(self):
        """Non-event schedules pass calendar_event_id=None."""

        class FakeCallbacks:
            pending_title: Optional[str] = None
            pending_calendar_event_id: Optional[str] = None

            def _start_meeting(self, *, principal=None):
                pass

        callbacks = FakeCallbacks()

        start_meeting_fn = lambda principal, title, calendar_event_id=None: (
            setattr(callbacks, "pending_title", title) or
            setattr(callbacks, "pending_calendar_event_id", calendar_event_id or None) or
            callbacks._start_meeting(principal=principal)
        )

        start_meeting_fn(
            principal=Principal(PrincipalKind.SCHEDULER, "sr:test"),
            title="Manual",
        )
        assert callbacks.pending_calendar_event_id is None


# --- TestReadSideExposesCalendarEventId::test_to_dict_includes_calendar_event_id: P1: sets a field on a dataclass and reads it back from to_dict; the service get/list tests cover the path
# (was a method of class TestReadSideExposesCalendarEventId)
def test_to_dict_includes_calendar_event_id(self):
    state = MeetingState(
        id="m-dict-01",
        started_at=datetime.now(),
        calendar_event_id="ce_abc",
    )
    d = state.to_dict()
    assert d["calendar_event_id"] == "ce_abc"


# --- TestReadSideExposesCalendarEventId::test_to_dict_null_when_unlinked: P1: sets a field on a dataclass and reads it back from to_dict; the service get/list tests cover the path
# (was a method of class TestReadSideExposesCalendarEventId)
def test_to_dict_null_when_unlinked(self):
    state = MeetingState(
        id="m-dict-02",
        started_at=datetime.now(),
    )
    d = state.to_dict()
    assert d["calendar_event_id"] is None


# --- TestMeetingsCalendarEventIdColumn::test_column_exists_and_nullable: P5: the unlinked-is-None test in the same class asserts the same
# (was a method of class TestMeetingsCalendarEventIdColumn)
def test_column_exists_and_nullable(self, tmp_path):
    db = make_db(tmp_path)
    meeting = MeetingState(
        id="m-test-01",
        started_at=datetime.now(),
    )
    db.meetings.save_meeting(meeting)
    loaded = db.meetings.get_meeting("m-test-01")
    assert loaded is not None
    assert loaded.calendar_event_id is None
