from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from holdspeak.services.observer import NullObserver, PipelineEvent, PipelineObserver


def make_event() -> PipelineEvent:
    return PipelineEvent(
        event_id="event-123",
        timestamp=123.456,
        service="PrimitiveService",
        method="create_note",
        principal_kind="user",
        principal_identity="user-123",
        args_summary='{"title":"Note"}',
        result_summary='{"id":"note-123"}',
        error=None,
        error_code=None,
        duration_ms=12.5,
        correlation_id="correlation-123",
        is_async=False,
    )


def test_pipeline_event_is_frozen() -> None:
    event = make_event()

    with pytest.raises(FrozenInstanceError):
        event.event_id = "other-event"


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


def test_null_observer_does_not_raise() -> None:
    NullObserver().on_event(make_event())


def test_null_observer_satisfies_pipeline_observer_protocol() -> None:
    assert isinstance(NullObserver(), PipelineObserver)
