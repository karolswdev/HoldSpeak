"""Capture (the Record verb), through the real hub (the test diet, 2026-10-11).

A hub with no meeting recorder wired (the rig of
``tests/unit/test_philo5_the_loop.py``) refuses a start with 501. The face's
words for that answer ("NOT RECORDING · NO RECORDER ON THIS HUB", OK and no
Retry) are fenced in ``web/src/desk/store/__tests__/recordingSlice.test.ts``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "unit"))
from test_philo5_the_loop import Hub, _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_a_start_on_a_hub_with_no_recorder_is_refused_501(hub: Hub) -> None:
    """replaces: tests/e2e/test_philo13_04_faces_glass.py::TestFacesDoNotLie::test_a_refused_start_says_not_recording (the hub half)"""
    answer = hub.client.post("/api/meeting/start", json={})
    assert answer.status_code == 501, answer.text
    assert answer.json()["success"] is False
