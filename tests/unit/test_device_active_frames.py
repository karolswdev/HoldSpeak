"""HS-17 active-device frame model tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from holdspeak.device_audio import DeviceHealthFrame, DeviceQueryFrame


def test_device_health_frame_accepts_valid_payload() -> None:
    frame = DeviceHealthFrame.model_validate(
        {"type": "device_health", "battery_pct": 82, "rssi_dbm": -58, "at": 123}
    )

    assert frame.battery_pct == 82
    assert frame.rssi_dbm == -58
    assert frame.at == 123


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "device_health", "battery_pct": -1, "rssi_dbm": -58, "at": 123},
        {"type": "device_health", "battery_pct": 101, "rssi_dbm": -58, "at": 123},
        {"type": "device_health", "battery_pct": 82, "rssi_dbm": -121, "at": 123},
        {"type": "device_health", "battery_pct": 82, "rssi_dbm": 1, "at": 123},
        {"type": "device_health", "battery_pct": 82, "rssi_dbm": -58},
        {"type": "device_health", "battery_pct": 82, "rssi_dbm": -58, "at": 123, "x": 1},
    ],
)
def test_device_health_frame_rejects_invalid_payloads(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        DeviceHealthFrame.model_validate(payload)


def test_device_query_frame_accepts_unknown_names_for_dispatch() -> None:
    frame = DeviceQueryFrame.model_validate(
        {"type": "query", "name": "current_topic", "at": 44}
    )

    assert frame.name == "current_topic"
    assert frame.at == 44


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "query", "name": "", "at": 44},
        {"type": "query", "at": 44},
        {"type": "query", "name": "last_segment"},
        {"type": "query", "name": "last_segment", "at": 44, "x": 1},
    ],
)
def test_device_query_frame_rejects_invalid_payloads(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        DeviceQueryFrame.model_validate(payload)
