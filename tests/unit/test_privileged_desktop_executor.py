"""RFC §5b desktop boundary: warrant validation precedes every raw act."""

from __future__ import annotations

import hashlib
import hmac
import json
from copy import deepcopy

from holdspeak.privileged_effects.desktop_executor import (
    DesktopEffectExecutor,
    execute_authorized,
)

SECRET = "executor-test-secret"
NOW = 1_900_000_000.0
OPERATION_ID = "op_desktop_test"
FOCUS = "mac:42:com.example.Editor:7"


def _canonical(value) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _message(text: str = "private words") -> dict:
    focus_hash = hashlib.sha256(FOCUS.encode()).hexdigest()[:20]
    generation = f"focus-1-{focus_hash}"
    request = {
        "request_schema": 1,
        "request_id": "00000000-0000-0000-0000-000000000108",
        "idempotency_key": "desktop.type_text:phase-108",
        "operation": {"name": "desktop.type_text", "version": 1},
        "subject_refs": [],
        "target": {"ref": f"desktop-input:{generation}"},
        "arguments": {
            "text": text,
            "submit": False,
            "expected_generation": generation,
            "native_id": "00000000-0000-0000-0000-000000000108",
            "gesture": "hold_release",
            "requested_target": "focused",
            "delivery_method": "desktop",
        },
        "placement": "node:local-desktop",
    }
    material = {
        "name": "desktop.type_text",
        "version": 1,
        "target_ref": request["target"]["ref"],
        "placement": request["placement"],
        "arguments": request["arguments"],
    }
    warrant = {
        "warrant_id": "war_phase108",
        "operation_id": OPERATION_ID,
        "envelope_sha256": "sha256:"
        + hashlib.sha256(_canonical(material).encode()).hexdigest(),
        "target_ref": request["target"]["ref"],
        "placement": request["placement"],
        "policy_version": "operation-policy/v2",
        "issued_at": NOW - 1,
        "expires_at": NOW + 30,
        "execution_expires_at": NOW + 60,
        "uses": 1,
    }
    warrant["signature"] = hmac.new(
        SECRET.encode(), _canonical(warrant).encode(), hashlib.sha256
    ).hexdigest()
    return {
        "operation_id": OPERATION_ID,
        "warrant": warrant,
        "request": request,
        "use_clipboard": True,
    }


def _resign(message: dict) -> None:
    unsigned = {
        key: value for key, value in message["warrant"].items() if key != "signature"
    }
    message["warrant"]["signature"] = hmac.new(
        SECRET.encode(), _canonical(unsigned).encode(), hashlib.sha256
    ).hexdigest()


class _Driver:
    def __init__(self, calls: list[dict], **kwargs) -> None:
        self.calls = calls
        self.use_clipboard = kwargs["use_clipboard"]

    def type_text(self, text, **kwargs) -> None:
        self.calls.append(
            {
                "text": text,
                "use_clipboard": self.use_clipboard,
                **kwargs,
            }
        )


class _FailingDriver:
    def __init__(self, **_kwargs) -> None:
        pass

    def type_text(self, _text, **_kwargs) -> None:
        raise RuntimeError("raw driver failed after warrant consumption")


def _run(message, used, calls, *, focus=FOCUS):
    return execute_authorized(
        message,
        secret=SECRET,
        used_warrants=used,
        clock=lambda: NOW,
        focus_reader=lambda: focus,
        driver_factory=lambda **kwargs: _Driver(calls, **kwargs),
    )


def test_valid_warrant_executes_exactly_once() -> None:
    calls: list[dict] = []
    used: set[str] = set()
    message = _message()

    assert _run(message, used, calls) == {
        "state": "succeeded",
        "outcome": "succeeded",
    }
    assert calls == [
        {
            "text": "private words",
            "use_clipboard": True,
            "target_profile": None,
            "submit": False,
        }
    ]

    replay = _run(message, used, calls)
    assert replay["outcome"] == "desktop_executor_warrant_spent"
    assert len(calls) == 1


def test_forgery_payload_swap_and_expiry_never_reach_driver() -> None:
    cases = []
    forged = _message()
    forged["warrant"]["signature"] = "0" * 64
    cases.append((forged, "desktop_executor_warrant_signature_invalid"))

    swapped = _message()
    swapped["request"]["arguments"]["text"] = "swapped payload"
    cases.append((swapped, "desktop_executor_payload_mismatch"))

    expired = _message()
    expired["warrant"]["expires_at"] = NOW - 1
    _resign(expired)
    cases.append((expired, "desktop_executor_warrant_expired"))

    for message, reason in cases:
        calls: list[dict] = []
        result = _run(deepcopy(message), set(), calls)
        assert result["outcome"] == reason
        assert calls == []


def test_focus_is_rechecked_inside_executor_and_refusal_spends_warrant() -> None:
    calls: list[dict] = []
    used: set[str] = set()
    message = _message()

    refused = _run(message, used, calls, focus="mac:99:other")
    assert refused["outcome"] == "desktop_focus_generation_changed"
    assert calls == []

    replay = _run(message, used, calls)
    assert replay["outcome"] == "desktop_executor_warrant_spent"
    assert calls == []


def test_driver_failure_spends_warrant_before_a_replay_can_reach_driver() -> None:
    used: set[str] = set()
    message = _message()
    failed = execute_authorized(
        message,
        secret=SECRET,
        used_warrants=used,
        clock=lambda: NOW,
        focus_reader=lambda: FOCUS,
        driver_factory=_FailingDriver,
    )

    assert failed == {
        "state": "failed",
        "outcome": "desktop_effect_driver_failed",
    }
    calls: list[dict] = []
    replay = _run(message, used, calls)
    assert replay["outcome"] == "desktop_executor_warrant_spent"
    assert calls == []


def test_policy_version_and_request_shape_are_independently_checked() -> None:
    version = _message()
    version["warrant"]["policy_version"] = "operation-policy/obsolete"
    _resign(version)
    assert _run(version, set(), [])["outcome"] == (
        "desktop_executor_policy_version_mismatch"
    )

    widened = _message()
    widened["request"]["ambient_capability"] = "keyboard"
    assert _run(widened, set(), [])["outcome"] == ("desktop_executor_warrant_invalid")


def test_spawned_anonymous_pipe_child_rejects_before_raw_driver_import() -> None:
    executor = DesktopEffectExecutor(SECRET)
    try:
        result = executor.execute(
            operation_id=OPERATION_ID,
            warrant={},
            request={},
        )
    finally:
        executor.close()

    assert result == {
        "state": "refused",
        "outcome": "desktop_executor_warrant_invalid",
    }


def test_timeout_breaks_the_pipe_and_later_operations_are_never_sent() -> None:
    class _PipeEnd:
        def __init__(self) -> None:
            self.sent: list[dict] = []
            self.closed = False

        def send(self, message) -> None:
            self.sent.append(message)

        def poll(self, _timeout) -> bool:
            return False

        def close(self) -> None:
            self.closed = True

    class _Process:
        def __init__(self) -> None:
            self.alive = True

        def start(self) -> None:
            pass

        def is_alive(self) -> bool:
            return self.alive

        def join(self, timeout=None) -> None:
            del timeout

        def terminate(self) -> None:
            self.alive = False

    class _Context:
        def __init__(self) -> None:
            self.parent = _PipeEnd()
            self.child = _PipeEnd()
            self.process = _Process()

        def Pipe(self, *, duplex):
            assert duplex is True
            return self.parent, self.child

        def Process(self, **kwargs):
            assert kwargs["target"]
            return self.process

    context = _Context()
    executor = DesktopEffectExecutor(SECRET, context=context)
    message = _message()
    try:
        first = executor.execute(
            operation_id=OPERATION_ID,
            warrant=message["warrant"],
            request=message["request"],
        )
        second = executor.execute(
            operation_id="op_must_not_be_sent",
            warrant=message["warrant"],
            request=message["request"],
        )
    finally:
        executor.close()

    assert first == {
        "state": "indeterminate",
        "outcome": "desktop_effect_executor_timeout",
    }
    assert second == {
        "state": "failed",
        "outcome": "desktop_effect_executor_unavailable",
    }
    assert len(context.parent.sent) == 1
