"""First run: Skip on Calendar and Connections (owner ruling 2026-10-06).

A Skip press writes ``first_run.skipped`` through ``PUT /api/settings``; a
reload reads it back, so the step stays skipped. The hub boots on an
isolated HOME.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from holdspeak.config import Config, FirstRunConfig
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    monkeypatch.setenv("HOME", str(tmp_path))
    hub = _boot(tmp_path, monkeypatch)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text
    return response.json()


def test_only_the_optional_steps_can_be_skipped() -> None:
    cfg = FirstRunConfig(skipped=["connections", " Calendar ", "local_ai", "you", "calendar"])
    assert cfg.skipped == ["calendar", "connections"]
    assert FirstRunConfig(skipped="calendar").skipped == []  # type: ignore[arg-type]


def test_a_skip_round_trips_through_settings(hub: Hub) -> None:
    before = _ok(hub.client.get("/api/settings"))
    assert before["first_run"] == {"skipped": []}
    saved = _ok(hub.client.put("/api/settings", json={"first_run": {"skipped": ["calendar", "first_words"]}}))
    assert saved["settings"]["first_run"] == {"skipped": ["calendar"]}
    assert Config.load().first_run.skipped == ["calendar"]
    # A partial write of another section (the You card's) keeps the skip.
    _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol Sane", "aliases": []}}))
    assert _ok(hub.client.get("/api/settings"))["first_run"] == {"skipped": ["calendar"]}
    refused = hub.client.put("/api/settings", json={"first_run": {"skipped": "calendar"}})
    assert refused.status_code == 400, refused.text
