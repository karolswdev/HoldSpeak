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


def test_an_in_transaction_method_is_not_observed() -> None:
    """It runs inside the caller's write transaction, so its event could only
    wait out the busy timeout and be dropped (decide accept took 5 s)."""
    from holdspeak.services.observer import observe_service
    from holdspeak.services.project_service import ProjectService

    @observe_service
    class Probe:
        def write(self) -> str:
            return "w"

        def write_in_transaction(self, conn: object) -> str:
            return "t"

    assert getattr(Probe.write, "__wrapped__", None) is not None
    assert getattr(Probe.write_in_transaction, "__wrapped__", None) is None
    assert getattr(ProjectService.create_item_in_transaction, "__wrapped__", None) is None
    assert getattr(ProjectService.create_item, "__wrapped__", None) is not None


def _whole_summary(value: object, limit: int = 2048) -> str:
    """The summary as it was read before the perf lane (2026-11-08): the
    whole value redacted and encoded, then cut."""
    import json

    from holdspeak.redaction import redact_bounded
    from holdspeak.services.observer import _redact_tree

    summary = redact_bounded(json.dumps(_redact_tree(value), default=str, separators=(",", ":")))
    return summary[: limit - 1] + "…" if len(summary) > limit else summary


def test_a_large_result_summary_is_the_summary_of_the_whole() -> None:
    """The summary reads only the head of a large result; it is the same text
    as the whole read, secrets redacted, at every size."""
    from holdspeak.services.observer import _truncate

    secret = "Bearer sk-live-0123456789abcdefghijklmnop"
    row = {"title": "Review the cutover", "owner": "Priya", "api_key": "sk-0123456789abcdef0123",
           "detail": f"Authorization: {secret}", "n": 3, "due": None, "tags": ("a", "b")}
    big = {"items": [dict(row, id=f"row-{i}") for i in range(2000)], "count": 2000}
    secret_head = {"items": [{"note": f"Authorization: {secret} " * 40} for _ in range(400)]}
    one_long_string = {"text": "x" * 70000, "after": [1, 2, 3]}
    for value in (big, secret_head, one_long_string, row, [row] * 3, "short", list(range(5000))):
        assert _truncate(value) == _whole_summary(value)
    assert "sk-live" not in _truncate(big)
