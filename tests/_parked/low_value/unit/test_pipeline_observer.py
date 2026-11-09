# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_pipeline_observer.py to restore.

# ruff: noqa


# --- test_pipeline_event_is_frozen: P3/P1: a frozen dataclass raises, reads back the literals it was built with, and a no-op observer satisfies its Protocol
def test_pipeline_event_is_frozen() -> None:
    event = make_event()

    with pytest.raises(FrozenInstanceError):
        event.event_id = "other-event"


# --- test_pipeline_event_exposes_all_fields: P3/P1: a frozen dataclass raises, reads back the literals it was built with, and a no-op observer satisfies its Protocol
def test_pipeline_event_exposes_all_fields() -> None:
    event = make_event()

    assert event.event_id == "event-123"
    assert event.timestamp == 123.456
    assert event.service == "PrimitiveService"
    assert event.method == "create_note"
    assert event.principal_kind == "user"
    assert event.principal_identity == "user-123"
    assert event.args_summary == '{"title":"Note"}'
    assert event.result_summary == '{"id":"note-123"}'
    assert event.error is None
    assert event.error_code is None
    assert event.duration_ms == 12.5
    assert event.correlation_id == "correlation-123"
    assert event.is_async is False


# --- test_null_observer_does_not_raise: P3/P1: a frozen dataclass raises, reads back the literals it was built with, and a no-op observer satisfies its Protocol
def test_null_observer_does_not_raise() -> None:
    NullObserver().on_event(make_event())


# --- test_null_observer_satisfies_pipeline_observer_protocol: P3/P1: a frozen dataclass raises, reads back the literals it was built with, and a no-op observer satisfies its Protocol
def test_null_observer_satisfies_pipeline_observer_protocol() -> None:
    assert isinstance(NullObserver(), PipelineObserver)
