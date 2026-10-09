"""PHILO-16 R2: the macOS calendar reader has an off switch, and every rig sets it.

EventKit is per macOS user, not per HOME. A fresh isolated HOME showed the
owner's real calendar names on the first-run Calendar step ("FOUND · 5").
`HOLDSPEAK_MACOS_CALENDAR=0` turns the reader off at its one gate
(`macos_calendar._eventkit`); the graph-walk hub and the glass hub set it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak import macos_calendar


def test_reader_is_on_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOLDSPEAK_MACOS_CALENDAR", raising=False)
    assert macos_calendar.reader_enabled() is True
    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", "1")
    assert macos_calendar.reader_enabled() is True


@pytest.mark.parametrize("value", ["0", "off", "false", "no", " OFF "])
def test_off_switch_closes_every_read(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", value)
    monkeypatch.setattr(macos_calendar.sys, "platform", "darwin")
    # Even with EventKit classes already loaded in this process, nothing reads.
    monkeypatch.setattr(macos_calendar, "_classes", {"EKEventStore": object(), "NSDate": object()})
    assert macos_calendar.reader_enabled() is False
    assert macos_calendar.available() is False
    assert macos_calendar.access_state() == "unavailable"
    assert macos_calendar.list_calendars() == []


def test_graph_walk_hub_env_turns_the_reader_off(tmp_path: Path) -> None:
    from scripts import graph_walk

    env = graph_walk._isolated_hub_env(tmp_path, inherited={"HOLDSPEAK_MACOS_CALENDAR": "1"})
    assert env["HOLDSPEAK_MACOS_CALENDAR"] == "0"


def test_glass_boot_turns_the_reader_off(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import holdspeak.web_server as web_server
    from tests.e2e import glass_infra
    import os

    seen: dict[str, str | None] = {}

    class _Server:
        def __init__(self, *_args, **_kwargs) -> None:
            seen["env"] = os.environ.get("HOLDSPEAK_MACOS_CALENDAR")

        def start(self) -> str:
            return "http://127.0.0.1:0"

    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", "1")
    monkeypatch.setattr(web_server, "MeetingWebServer", _Server)
    glass_infra._boot(tmp_path, monkeypatch)
    assert seen["env"] == "0"
