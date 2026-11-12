"""Betterment daily D10 MCP reads use the web faces' producers."""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.runtime import composition

from tests.fixtures.daily_week import seed
from tests.unit.test_desk_needs_you import _boot, _needs, _ok


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    running = _boot(tmp_path, monkeypatch)
    yield running
    from holdspeak.db import reset_database

    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_today_get_matches_the_faces_on_the_real_hub(hub) -> None:
    """Today returns the same Needs-you, day, brief, and Prepared reads."""
    seed(hub, engine=True)
    root = composition.current()
    assert root.operations.descriptor("today.get").effect == "read"
    assert root.operations.target("today.get") is root.today_service
    is_error, today = hub.mcp("today.get", {})
    assert not is_error, today

    needs = _needs(hub)
    assert today["needs_you"]["count"] == needs["count"]
    member_refs = {row["ref"] for row in needs["members"]}
    expected_top = [row for row in needs["items"] if row.get("ref") in member_refs][:5]
    assert today["needs_you"]["items"] == expected_top
    assert today["needs_you"]["top"] == expected_top

    door = _ok(hub.client.get("/api/door"))
    meetings = _ok(hub.client.get("/api/meetings?limit=40"))
    assert today["day"]["upcoming"] == door["upcoming"]
    assert today["day"]["week"] == door["week"]
    assert today["day"]["meetings"] == meetings["meetings"]

    brief = _ok(hub.client.get("/api/brief/latest?ensure=1"))
    assert today["since_yesterday"]["id"] == brief["id"]
    assert today["since_yesterday"]["sections"] == brief["sections"]
    assert today["prepared"] == _ok(hub.client.get("/api/automations/prepared"))
