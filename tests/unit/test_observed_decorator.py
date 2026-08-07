import asyncio

import pytest

from holdspeak.services.observer import observe_service, observed


class _FakePrincipal:
    class kind:
        value = "OWNER"

    identity = "test-user"


class _CollectingObserver:
    def __init__(self):
        self.events = []

    def on_event(self, event):
        self.events.append(event)


class _FailingObserver:
    def on_event(self, event):
        raise RuntimeError("observer unavailable")


def test_observed_sync_captures_event():
    observer = _CollectingObserver()

    class Service:
        def __init__(self):
            self._observer = observer

        @observed
        def process(self, principal: "Principal", value: str):
            return {"value": value}

    assert Service().process(_FakePrincipal(), "hello") == {"value": "hello"}

    assert len(observer.events) == 1
    event = observer.events[0]
    assert event.service == "Service"
    assert event.method == "process"
    assert event.principal_kind == "OWNER"
    assert event.principal_identity == "test-user"
    assert event.args_summary == '{"value":"hello"}'
    assert event.result_summary == '{"value":"hello"}'
    assert event.duration_ms > 0
    assert event.is_async is False


def test_observed_async_captures_event():
    observer = _CollectingObserver()

    class Service:
        def __init__(self):
            self._observer = observer

        @observed
        async def process(self, principal: "Principal", value: str):
            return value.upper()

    assert asyncio.run(Service().process(_FakePrincipal(), "hello")) == "HELLO"

    assert len(observer.events) == 1
    event = observer.events[0]
    assert event.service == "Service"
    assert event.method == "process"
    assert event.principal_kind == "OWNER"
    assert event.principal_identity == "test-user"
    assert event.is_async is True


def test_observed_exception_captures_error():
    observer = _CollectingObserver()

    class CodedError(Exception):
        code = "DENIED"

    class Service:
        def __init__(self):
            self._observer = observer

        @observed
        def process(self, principal: "Principal"):
            raise CodedError("access denied")

    with pytest.raises(CodedError, match="access denied"):
        Service().process(_FakePrincipal())

    assert len(observer.events) == 1
    event = observer.events[0]
    assert "CodedError" in event.error
    assert event.error_code == "DENIED"
    assert event.result_summary == ""


def test_observed_observer_failure_does_not_break_method():
    class Service:
        _observer = _FailingObserver()

        @observed
        def process(self, principal: "Principal"):
            return "completed"

    assert Service().process(_FakePrincipal()) == "completed"


def test_observed_correlation_shared_across_nested_calls():
    observer = _CollectingObserver()

    class Service:
        def __init__(self):
            self._observer = observer

        @observed
        def outer(self, principal: "Principal"):
            return self.inner(principal)

        @observed
        def inner(self, principal: "Principal"):
            return "completed"

    assert Service().outer(_FakePrincipal()) == "completed"
    assert len(observer.events) == 2
    assert observer.events[0].correlation_id == observer.events[1].correlation_id


def test_observed_truncation():
    observer = _CollectingObserver()
    large_value = "x" * 4096

    class Service:
        def __init__(self):
            self._observer = observer

        @observed
        def process(self, principal: "Principal", value: str):
            return large_value

    Service().process(_FakePrincipal(), large_value)

    event = observer.events[0]
    assert len(event.args_summary) <= 2049
    assert len(event.result_summary) <= 2049
    assert event.args_summary.endswith("…")
    assert event.result_summary.endswith("…")


def test_observe_service_class_decorator():
    observer = _CollectingObserver()

    @observe_service
    class Service:
        def __init__(self):
            self._observer = observer

        def public(self, principal: "Principal"):
            return "public"

        def _private(self, principal: "Principal"):
            return "private"

    service = Service()
    assert service.public(_FakePrincipal()) == "public"
    assert service._private(_FakePrincipal()) == "private"
    assert [event.method for event in observer.events] == ["public"]
