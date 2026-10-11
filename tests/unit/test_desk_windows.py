"""Desk windows on the hub (test diet, 2026-10-11): window facts moved off the browser.

Each section below is one moved browser fact, against the hub's window service
(``holdspeak/services/desk_window_service.py``). Sections are appended by app.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.services.desk_window_service import DeskWindowService


@pytest.fixture()
def windows(tmp_path: Path) -> DeskWindowService:
    return DeskWindowService(Database(tmp_path / "windows.db"))


def _front(svc: DeskWindowService) -> list[str]:
    return [w["id"] for w in svc.list()["windows"] if w["front"]]


# ── Chair: Window > Chair > Brief comes to the front ──────────────────────
# replaces: tests/e2e/test_philo14_a1_fresh_arrival_glass.py::TestChairWindowComesToFront::test_window_chair_brief_opens_in_front_of_settings
# The browser half (the menu pick puts chair:brief last in the client's
# order, also when the Chair mounts after the pick) is fenced in
# web/src/desk/chair/__tests__/chairWindows.philo1311.test.tsx:294-321.


def test_chair_brief_opens_in_front_of_settings_and_runs_on(windows: DeskWindowService) -> None:
    # His rehearsal desk: Needs you, Runs on (the Concierge window) and Settings open.
    for window_id in ("chair:needs", "surface-concierge", "surface-settings"):
        windows.open(window_id)
    assert _front(windows) == ["surface-settings"]

    # 1) a fresh Brief opens over them
    row: dict[str, Any] = windows.open("chair:brief")
    assert row["front"] is True
    assert _front(windows) == ["chair:brief"]

    # 2) Settings comes up again; the open Brief behind it comes to the front
    windows.open("surface-settings")
    assert _front(windows) == ["surface-settings"]
    windows.open("chair:brief")
    assert _front(windows) == ["chair:brief"]
    depths = {w["id"]: w["depth"] for w in windows.list()["windows"]}
    assert depths["chair:brief"] > max(depths["surface-settings"], depths["surface-concierge"])
