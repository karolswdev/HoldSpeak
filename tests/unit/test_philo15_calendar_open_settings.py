"""PHILO-15 04 (gap 12): a denied calendar has a way forward.

``POST /api/onboarding/calendar/macos/settings`` is ``calendar.open_settings``:
the owner's press opens System Settings at Privacy & Security > Calendars. It
is an owner-only, admitted kernel operation with one receipt (succeeded, or
refused by name when the open fails). An agent is refused. The real hub app,
the real kernel; only the macOS ``open`` is a double.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_conductor_k6_agent_mcp import _client, _launch_credential, _reach, hub  # noqa: E402,F401

PATH = "/api/onboarding/calendar/macos/settings"


class _Mac:
    def __init__(self, opens: bool) -> None:
        self.opens = opens
        self.calls = 0

    def open_privacy_settings(self) -> bool:
        self.calls += 1
        return self.opens


def _service(hub: Any) -> Any:
    return hub.root.operations.target("calendar.open_settings")


def test_the_owner_opens_the_calendars_pane_with_a_receipt(hub, monkeypatch) -> None:
    mac = _Mac(True)
    monkeypatch.setattr(_service(hub), "_macos", mac)
    resp = hub.client.post(PATH, json={})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert (body["opened"], body["pane"]) == (True, "privacy_calendars")
    assert body["receipt"]["outcome"] == "succeeded" and body["operation_id"]
    assert mac.calls == 1


def test_a_failed_open_is_refused_by_name_with_a_receipt(hub, monkeypatch) -> None:
    monkeypatch.setattr(_service(hub), "_macos", _Mac(False))
    resp = hub.client.post(PATH, json={})
    assert resp.status_code == 409, resp.text
    body = resp.json()
    assert body.get("code") == "system_settings_not_opened" or body.get("error_code") == "system_settings_not_opened"


def test_an_agent_never_opens_it(hub, monkeypatch) -> None:
    mac = _Mac(True)
    monkeypatch.setattr(_service(hub), "_macos", mac)
    _reach(hub, False)
    agent = _client(hub, _launch_credential().token)
    assert agent.post(PATH, json={}).status_code == 403
    assert mac.calls == 0


def test_the_descriptor_is_owner_only_http_only_and_admitted() -> None:
    from holdspeak.kernel.project import ONBOARDING_ADMITTED
    from holdspeak.onboarding_operations import CALENDAR_OPEN_SETTINGS as op

    assert op.owner_only and op.owner_press and op.admission.rule == "admitted"
    assert op.exposure == ("http:POST /api/onboarding/calendar/macos/settings",)
    assert "calendar.open_settings" in ONBOARDING_ADMITTED


def test_the_open_targets_the_calendars_privacy_pane(monkeypatch) -> None:
    from holdspeak import macos_calendar

    ran: list[list[str]] = []

    class Done:
        returncode = 0

    monkeypatch.setattr(macos_calendar.sys, "platform", "darwin")
    monkeypatch.setattr("subprocess.run", lambda argv, **_: ran.append(argv) or Done())
    assert macos_calendar.open_privacy_settings() is True
    assert ran == [["/usr/bin/open",
                    "x-apple.systempreferences:com.apple.preference.security?Privacy_Calendars"]]
    monkeypatch.setattr(macos_calendar.sys, "platform", "linux")
    assert macos_calendar.open_privacy_settings() is False


@pytest.mark.parametrize("extra", [{"url": "x"}])
def test_the_op_takes_no_arguments(hub, monkeypatch, extra) -> None:
    mac = _Mac(True)
    monkeypatch.setattr(_service(hub), "_macos", mac)
    assert hub.client.post(PATH, json=extra).status_code == 400
    assert mac.calls == 0
