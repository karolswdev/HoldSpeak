"""PHILO-15 05 (Astra r1 on #975): an unread source is a NOT READ row.

Brief tests that fence the Brief's OWN collectors and headline used to pass
``principal=None``: the needs-you rule then failed its owner reads, and the
Brief dropped that failure silently, so a fresh desk read "No changes". It
no longer does. This fixture answers the rule with an empty, fully read
result, so those tests keep fencing what they name. The rule itself is
fenced by the needs-you and philo15_05 tests.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def quiet_needs_you(monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.services import project_service

    monkeypatch.setattr(
        project_service.ProjectService, "needs_you",
        lambda self, principal: {"items": [], "blockers": [], "failedMeetings": [], "count": 0, "sourceErrors": {}},
    )
