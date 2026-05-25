"""AIPI-4-07 — remote gesture simulation: `_press` helper unit tests.

Covers the gesture-name → service-name + duration_ms mapping, the
missing-service error path, and the malformed-gesture defensive check.
The integration wrapper `_remote_press` is untested (creates an
APIClient + opens a network connection — same pattern as `_check`,
`_run`, `_send_test_audio` per AIPI-2-08's deliberate decision).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import structlog

from bridge.cli import _press


class _FakeService:
    def __init__(self, name: str) -> None:
        self.name = name


def _make_client() -> MagicMock:
    client = MagicMock()
    client.execute_service = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_press_left_short_calls_simulate_left_press_with_100ms():
    client = _make_client()
    svc = _FakeService("simulate_left_press")
    services = {"simulate_left_press": svc, "simulate_voice_typing": _FakeService("simulate_voice_typing")}

    rc = await _press(client, services, "left-short", structlog.get_logger(), settle_s=0)

    assert rc == 0
    client.execute_service.assert_awaited_once_with(
        service=svc, data={"duration_ms": 100}
    )


@pytest.mark.asyncio
async def test_press_left_long_calls_simulate_left_press_with_6000ms():
    client = _make_client()
    svc = _FakeService("simulate_left_press")
    services = {"simulate_left_press": svc}

    rc = await _press(client, services, "left-long", structlog.get_logger(), settle_s=0)

    assert rc == 0
    client.execute_service.assert_awaited_once_with(
        service=svc, data={"duration_ms": 6000}
    )


@pytest.mark.asyncio
async def test_press_voice_typing_calls_simulate_voice_typing_with_3000ms():
    client = _make_client()
    svc = _FakeService("simulate_voice_typing")
    services = {"simulate_voice_typing": svc}

    rc = await _press(client, services, "voice-typing", structlog.get_logger(), settle_s=0)

    assert rc == 0
    client.execute_service.assert_awaited_once_with(
        service=svc, data={"duration_ms": 3000}
    )


@pytest.mark.asyncio
async def test_press_returns_1_when_service_missing():
    """Pre-AIPI-4-07 firmware doesn't have the simulate services —
    `--press` exits 1 with a remediation hint in the log."""
    client = _make_client()
    services = {}  # no simulate services

    rc = await _press(client, services, "left-short", structlog.get_logger(), settle_s=0)

    assert rc == 1
    client.execute_service.assert_not_awaited()


@pytest.mark.asyncio
async def test_press_returns_1_on_unknown_gesture():
    """argparse's `choices=` should make this unreachable from the CLI;
    defensive raise + exit 1 still belongs in the helper."""
    client = _make_client()
    services = {"simulate_left_press": _FakeService("simulate_left_press")}

    rc = await _press(client, services, "left-medium", structlog.get_logger())

    assert rc == 1
    client.execute_service.assert_not_awaited()


@pytest.mark.asyncio
async def test_press_returns_1_on_execute_service_error():
    """Network glitch / device gone away during execute — surface as
    a clean exit code, not a propagated exception."""
    client = _make_client()
    client.execute_service = AsyncMock(side_effect=RuntimeError("API gone"))
    svc = _FakeService("simulate_left_press")
    services = {"simulate_left_press": svc}

    rc = await _press(client, services, "left-short", structlog.get_logger(), settle_s=0)

    assert rc == 1
