"""Round-trip tests for the HoldSpeak wire-protocol Pydantic models.

Mirrors HoldSpeak's `tests/unit/test_device_handshake.py` style — the
two test suites should fail together if either side drifts. Source of
truth: ~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from holdspeak_proto import (
    DEVICE_HANDSHAKE_VERSION,
    ErrorFrame,
    EventFrame,
    Heartbeat,
    Hello,
    HelloAck,
    QueryFrame,
    StartFrame,
    Status,
    StopFrame,
)

# ---------- Hello (handshake) ----------


def test_hello_round_trip():
    hello = Hello(
        device_id="aipi-1",
        label="Karol",
        psk="abc123",
        version=DEVICE_HANDSHAKE_VERSION,
    )
    parsed = Hello.model_validate_json(hello.model_dump_json())
    assert parsed == hello
    assert parsed.type == "hello"


def test_hello_default_type_and_version():
    hello = Hello(device_id="aipi-1", label="Karol", psk="abc")
    assert hello.type == "hello"
    assert hello.version == DEVICE_HANDSHAKE_VERSION


def test_hello_strips_whitespace():
    hello = Hello(
        device_id="  aipi-1  ",
        label="\tKarol\n",
        psk="  abc  ",
        version=1,
    )
    assert hello.device_id == "aipi-1"
    assert hello.label == "Karol"
    assert hello.psk == "abc"


def test_hello_rejects_unknown_field():
    with pytest.raises(ValidationError):
        Hello.model_validate(
            {
                "type": "hello",
                "device_id": "aipi-1",
                "label": "Karol",
                "psk": "abc",
                "version": 1,
                "unexpected": "field",
            }
        )


def test_hello_rejects_empty_strings():
    for empty_field in ("device_id", "label", "psk"):
        kwargs = {"device_id": "x", "label": "y", "psk": "z", "version": 1}
        kwargs[empty_field] = ""
        with pytest.raises(ValidationError):
            Hello(**kwargs)


def test_hello_rejects_whitespace_only_after_strip():
    # str_strip_whitespace runs *before* validation → after strip the
    # value is empty → the non_empty validator rejects it.
    with pytest.raises(ValidationError):
        Hello(device_id="   ", label="Karol", psk="abc", version=1)


# ---------- HelloAck ----------


def test_hello_ack_round_trip():
    raw = '{"type":"hello-ack","device_id":"aipi-1","label":"Karol"}'
    ack = HelloAck.model_validate_json(raw)
    assert ack.device_id == "aipi-1"
    assert ack.label == "Karol"


def test_hello_ack_rejects_wrong_type_literal():
    with pytest.raises(ValidationError):
        HelloAck.model_validate(
            {"type": "hello", "device_id": "aipi-1", "label": "Karol"}
        )


def test_hello_ack_rejects_unknown_field():
    with pytest.raises(ValidationError):
        HelloAck.model_validate(
            {
                "type": "hello-ack",
                "device_id": "aipi-1",
                "label": "Karol",
                "extra": True,
            }
        )


# ---------- Heartbeat / Start / Stop ----------


def test_heartbeat_default_type():
    hb = Heartbeat()
    assert hb.type == "heartbeat"
    assert json.loads(hb.model_dump_json()) == {"type": "heartbeat"}


def test_start_stop_default_types():
    assert StartFrame().type == "start"
    assert StopFrame().type == "stop"
    assert json.loads(StartFrame().model_dump_json()) == {"type": "start"}
    assert json.loads(StopFrame().model_dump_json()) == {"type": "stop"}


# ---------- Status (server → device) ----------


def test_status_round_trip():
    raw = '{"type":"status","text":"Listening...","ttl_ms":0}'
    status = Status.model_validate_json(raw)
    assert status.text == "Listening..."
    assert status.ttl_ms == 0


def test_status_rejects_missing_field():
    with pytest.raises(ValidationError):
        Status.model_validate({"type": "status", "text": "Hi"})


# ---------- ErrorFrame ----------


def test_error_frame_round_trip():
    raw = (
        '{"type":"error","code":"session_busy",'
        '"reason":"another voice-typing session is already active"}'
    )
    err = ErrorFrame.model_validate_json(raw)
    assert err.code == "session_busy"
    assert "session" in err.reason


def test_error_frame_rejects_unknown_field():
    with pytest.raises(ValidationError):
        ErrorFrame.model_validate(
            {
                "type": "error",
                "code": "x",
                "reason": "y",
                "extra": True,
            }
        )


# ---------- EventFrame ----------


def test_event_frame_with_at():
    ev = EventFrame(name="long_press", at=47.5)
    assert ev.type == "event"
    assert ev.at == 47.5
    parsed = EventFrame.model_validate_json(ev.model_dump_json())
    assert parsed == ev


def test_event_frame_at_optional():
    ev = EventFrame(name="long_press")
    assert ev.at is None


def test_event_frame_rejects_unknown_field():
    with pytest.raises(ValidationError):
        EventFrame.model_validate(
            {
                "type": "event",
                "name": "long_press",
                "at": 1.0,
                "device_id": "leaked",
            }
        )


# ---------- QueryFrame ----------


def test_query_frame_round_trip():
    query = QueryFrame(name="last_segment", at=1235)
    parsed = QueryFrame.model_validate_json(query.model_dump_json())
    assert parsed == query
    assert parsed.type == "query"


@pytest.mark.parametrize("name", ["agent_question", "agent_next"])
def test_query_frame_accepts_agent_companion_names(name):
    query = QueryFrame(name=name, at=1235)

    assert query.name == name


def test_query_frame_rejects_unknown_name():
    with pytest.raises(ValidationError):
        QueryFrame.model_validate(
            {
                "type": "query",
                "name": "current_topic",
                "at": 1235,
            }
        )


def test_query_frame_rejects_unknown_field():
    with pytest.raises(ValidationError):
        QueryFrame.model_validate(
            {
                "type": "query",
                "name": "last_segment",
                "at": 1235,
                "request_id": "future",
            }
        )
