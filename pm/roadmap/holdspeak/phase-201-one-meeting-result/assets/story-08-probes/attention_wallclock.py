"""Temporary HS-201-08 red replay: freeze production heartbeat wall clock."""

from datetime import datetime as _RealDateTime, timezone

import pytest


class _FrozenDateTime(_RealDateTime):
    @classmethod
    def now(cls, tz=None):
        at = _RealDateTime(2026, 9, 7, 2, 30, tzinfo=timezone.utc)
        return at if tz is not None else at.replace(tzinfo=None)


@pytest.fixture(autouse=True)
def _freeze_heartbeat_wall_clock(monkeypatch):
    import holdspeak.services.heartbeat_service as heartbeat_service

    monkeypatch.setattr(heartbeat_service, "datetime", _FrozenDateTime)
