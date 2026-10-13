"""Settings, through the real hub (the test diet, 2026-10-11).

The hub boots over an isolated database and config file (the rig of
``tests/unit/test_philo9_b1_connections.py``). Each test reads or writes the
real routes the Settings face reads, and asserts the fact the browser test it
replaces asserted on the hub side.

The wire fixtures under ``web/src/desk/__tests__/fixtures/settings-wire/`` are
what the Settings vitest (``web/src/desk/__tests__/settings.app.test.tsx``)
answers its ``fetch`` with. ``test_the_settings_wire_fixtures_carry_no_invented_field``
proves every field in them is a field the live hub sends (the scar law: a test
double that lies about the field a check reads proves nothing). To write them
again from the live hub: ``HOLDSPEAK_WRITE_WIRE_FIXTURES=1`` on this file.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

import holdspeak.principals as principals
from holdspeak.principals import AgentCredentialStore
from holdspeak.runtime import composition
from tests.unit.test_philo9_b1_connections import CountingRunner, _boot

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "settings-wire"

# file name -> the GET route it records, on a cold hub (nothing seeded).
COLD_ROUTES = {
    "settings.json": "/api/settings",
    "hub.json": "/api/settings/hub",
    "authority-policy.json": "/api/authority/policy",
    "calendar-sources.json": "/api/calendar/sources",
    "people-access.json": "/api/settings/people-access",
    "remote-off.json": "/api/settings/remote",
    "system-identity.json": "/api/system/identity",
    "projects.json": "/api/projects",
}


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    # The hub keeps agent credentials in a process-global store; this hub
    # gets its own (as the HS-174 glass did), so no other test adds rows.
    monkeypatch.setattr(principals, "agent_credentials", AgentCredentialStore())
    rig = _boot(tmp_path, monkeypatch, CountingRunner(), CountingRunner())
    yield rig
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _get(hub: Any, path: str) -> Any:
    resp = hub.client.get(path)
    assert resp.status_code == 200, (path, resp.status_code, resp.text[:300])
    return resp.json()


def _issue(hub: Any, identity: str) -> dict[str, Any]:
    resp = hub.client.post(
        "/api/settings/remote/credentials",
        json={"identity": identity, "palette": "PROJECT", "ttl_seconds": 3600},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _mcp_initialize(hub: Any, token: str) -> Any:
    return hub.client.post(
        "/api/mcp",
        json={
            "jsonrpc": "2.0", "id": "probe", "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "diet-probe", "version": "1.0"}},
        },
        # The probe's own token replaces the owner's (the rig's client
        # carries the owner token by default; tests/conftest.py).
        headers={"X-HoldSpeak-Token": token, "Authorization": f"Bearer {token}"},
    )


# ── the cold hub ──────────────────────────────────────────────────────


def test_a_cold_hub_has_no_default_engine_and_sweeps_every_15_minutes(hub: Any) -> None:
    """replaces: tests/e2e/test_hs170_settings_hub_glass.py::test_settings_hub_cold (the hub half)

    The face's "No engine yet" headline, the Runs on NO DEFAULT chip and the
    Rhythm EVERY 15 MIN token are drawn from these facts.
    """
    wire = _get(hub, "/api/settings/hub")
    assert wire["models"] == {"engines": 0, "groupsSet": 0, "defaultSet": False}
    assert wire["meetings"]["engineSet"] is not True
    assert wire["voice"].get("engineSet") is not True
    assert wire["answers"]["engineSet"] is not True
    assert wire["rhythm"]["sweepEveryMinutes"] == 15
    assert wire["rhythm"]["loops"] == 0
    assert wire["system"]["host"] == "THIS DEVICE"
    assert wire["system"]["remote"] is False
    # The owner ruling of 2026-10-05: a summary runs after every meeting.
    assert wire["meetings"]["auto"] == "every"
    assert _get(hub, "/api/settings")["meeting"]["intelligence_auto"] == "every"


def test_the_hub_names_remote_access_on_after_the_switch(hub: Any) -> None:
    """replaces: tests/e2e/test_hs174_remote_settings_glass.py::test_remote_on_issue_revoke (the System row: Other devices: on)"""
    assert _get(hub, "/api/settings/hub")["system"]["remote"] is False
    resp = hub.client.put("/api/settings/remote", json={"enabled": True})
    assert resp.status_code == 200 and resp.json()["enabled"] is True, resp.text
    assert _get(hub, "/api/settings/hub")["system"]["remote"] is True


# ── remote access: issue, list, revoke ────────────────────────────────


def test_a_credential_token_is_shown_once_and_a_revoke_ends_only_that_credential(hub: Any) -> None:
    """replaces: tests/e2e/test_hs174_remote_settings_glass.py::test_remote_on_issue_revoke

    The token leaves the hub once (the issue answer); the list never carries
    it; a new credential is NEVER USED (``last_used_at`` null); Revoke on one
    credential removes that row only, and the other one still opens an MCP
    session through the real Streamable HTTP route.
    """
    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    first = _issue(hub, "test-glass-runner")
    other = _issue(hub, "other-glass-runner")
    assert len(first["token"]) > 10 and len(other["token"]) > 10

    listed = _get(hub, "/api/settings/remote")
    rows = {c["identity"]: c for c in listed["credentials"]}
    assert set(rows) == {"test-glass-runner", "other-glass-runner"}
    assert first["token"] not in json.dumps(listed) and other["token"] not in json.dumps(listed)
    assert all("token" not in c for c in listed["credentials"])
    assert rows["test-glass-runner"]["last_used_at"] is None  # the face: NEVER USED
    assert listed["total_count"] == 2 and listed["active_count"] == 2

    resp = hub.client.delete(f"/api/settings/remote/credentials/{first['id']}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["revoked"] == first["id"]

    after = _get(hub, "/api/settings/remote")
    assert [c["identity"] for c in after["credentials"]] == ["other-glass-runner"]

    ok = _mcp_initialize(hub, other["token"])
    assert ok.status_code == 200 and ok.json().get("result"), ok.text
    gone = _mcp_initialize(hub, first["token"])
    assert gone.status_code == 401, (gone.status_code, gone.text[:200])


# ── People: his name and the other names for him ──────────────────────


def test_the_owner_name_and_aliases_save_and_read_back(hub: Any) -> None:
    """replaces: tests/e2e/test_hs170_settings_hub_glass.py::test_settings_people_edits_name_and_alias_after_setup (the hub half)"""
    for owner in (
        {"name": "Karl", "aliases": []},
        {"name": "Karol Sane", "aliases": ["Carol"]},
        {"aliases": ["Carol", "Karolek"]},
    ):
        resp = hub.client.put("/api/settings", json={"owner": owner})
        assert resp.status_code == 200 and resp.json().get("success") is not False, resp.text
    assert _get(hub, "/api/settings")["owner"] == {"name": "Karol Sane", "aliases": ["Carol", "Karolek"]}


# ── Meetings: the retired Slack webhook never comes back ──────────────


def test_a_legacy_slack_webhook_in_config_never_reaches_the_settings_wire(hub: Any) -> None:
    """replaces: tests/e2e/test_philo11_05b_meeting_faces_glass.py::test_the_meeting_faces_and_slack_destinations (R7: no Credentials Slack row for a legacy webhook)"""
    import holdspeak.config as config_facade
    from holdspeak.config import Config

    legacy = "https://hooks.slack.com/services/LEGACY/ROW/diet-legacy-sentinel"
    cfg = Config.load()
    cfg.meeting.slack_webhook_url = legacy
    cfg.save(path=config_facade.CONFIG_FILE)
    wire = _get(hub, "/api/settings")
    assert "slack_webhook_url" not in wire["meeting"]
    assert not any("slack" in key for key in wire.get("_secrets", {}))
    assert "diet-legacy-sentinel" not in json.dumps(wire)


# ── the wire fixtures the Settings vitest reads ──────────────────────


def _scrub(value: Any, tmp: str) -> Any:
    if isinstance(value, dict):
        return {k: _scrub(v, tmp) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v, tmp) for v in value]
    if isinstance(value, str) and tmp in value:
        return value.replace(tmp, "/Users/owner")
    return value


def _invented(fixture: Any, live: Any, path: str = "$") -> list[str]:
    """Every field the fixture carries that the live answer does not."""
    if isinstance(fixture, dict):
        if not isinstance(live, dict):
            return [f"{path} is an object, the hub sends {type(live).__name__}"]
        out: list[str] = []
        for key, value in fixture.items():
            if key not in live:
                out.append(f"{path}.{key}")
            else:
                out.extend(_invented(value, live[key], f"{path}.{key}"))
        return out
    if isinstance(fixture, list) and fixture and isinstance(live, list) and live:
        # Every element (Astra r1 on #1100), each against the live row in its
        # place, or the hub's last row when the fixture holds more rows.
        out = []
        for i, item in enumerate(fixture):
            out.extend(_invented(item, live[min(i, len(live) - 1)], f"{path}[{i}]"))
        return out
    return []


def _live_wire(hub: Any, tmp_path: Path) -> dict[str, Any]:
    import holdspeak.config as config_facade
    from holdspeak.config import Config
    from holdspeak.config.integrations import CalendarConfig, CalendarSource

    wire = {name: _get(hub, route) for name, route in COLD_ROUTES.items()}
    assert hub.client.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    wire["remote-issue.json"] = issued = _issue(hub, "sweep-runner")
    wire["remote-on.json"] = _get(hub, "/api/settings/remote")
    gone = _issue(hub, "goner")
    revoked = hub.client.delete(f"/api/settings/remote/credentials/{gone['id']}")
    assert revoked.status_code == 200, revoked.text
    wire["remote-revoke.json"] = revoked.json()
    assert issued["identity"] == "sweep-runner"
    # One file calendar source, auto-record for Room meetings: the row shape.
    ics = tmp_path / "work.ics"
    ics.write_text("BEGIN:VCALENDAR\nVERSION:2.0\nEND:VCALENDAR\n")
    cfg = Config.load()
    cfg.calendar = CalendarConfig(sources=[CalendarSource(id="src-work", label="WORK", url=str(ics), enabled=True)])
    cfg.meeting.auto_record = "room_linked"
    cfg.save(path=config_facade.CONFIG_FILE)
    wire["calendar-sources-one.json"] = _get(hub, "/api/calendar/sources")
    put = hub.client.put("/api/settings", json={"owner": {"name": "Karl", "aliases": []}})
    assert put.status_code == 200, put.text
    wire["settings-put.json"] = put.json()
    return wire


def test_the_settings_wire_fixtures_carry_no_invented_field(hub: Any, tmp_path: Path) -> None:
    """The vitest doubles are the live hub's own answers (scar law)."""
    wire = _live_wire(hub, tmp_path)
    if os.environ.get("HOLDSPEAK_WRITE_WIRE_FIXTURES") == "1":
        FIXTURES.mkdir(parents=True, exist_ok=True)
        for name, body in wire.items():
            if "token" in body:  # the issue answer: never keep a live token
                body = {**body, "token": "hs_agent_fixture_token_shown_once"}
            text = json.dumps(_scrub(body, str(tmp_path)), indent=2, sort_keys=True) + "\n"
            (FIXTURES / name).write_text(text)
    problems: list[str] = []
    for name, body in wire.items():
        fixture_path = FIXTURES / name
        assert fixture_path.exists(), f"missing fixture {name}; write it with HOLDSPEAK_WRITE_WIRE_FIXTURES=1"
        problems += [f"{name}: {p}" for p in _invented(json.loads(fixture_path.read_text()), body)]
    assert not problems, (
        "a Settings vitest fixture carries a field the hub does not send "
        "(write them again with HOLDSPEAK_WRITE_WIRE_FIXTURES=1): " + ", ".join(problems)
    )


# ── the grant wire (Remote access: desk and project grants) ──────────
#
# The answers the Remote access grant vitest reads (settings.app.test.tsx,
# "Settings › System › Remote access grants"). The hub half of each grant
# fact (kernel op names, revocation reasons, credential revoke ends the
# grant first) is fenced in tests/unit/test_philo7_article_xi.py,
# test_philo7_round_two.py and test_philo9_project_grant.py.


def _answer(resp: Any) -> Any:
    return resp.json()


def _grant_wire(hub: Any) -> dict[str, Any]:
    import time

    c = hub.client
    wire: dict[str, Any] = {}
    assert c.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    desk = c.post("/api/settings/remote/credentials", json={"identity": "desk-agent", "palette": "DESK"})
    assert desk.status_code == 200, desk.text
    wire["grant-remote-never.json"] = _get(hub, "/api/settings/remote")
    allowed = c.put("/api/settings/remote/delegations/desk-agent", json={})
    assert allowed.status_code == 200, allowed.text
    wire["grant-allow.json"] = _answer(allowed)
    wire["grant-remote-live.json"] = _get(hub, "/api/settings/remote")
    stopped = c.delete("/api/settings/remote/delegations/desk-agent")
    assert stopped.status_code == 200, stopped.text
    wire["grant-stop.json"] = _answer(stopped)
    wire["grant-remote-stopped.json"] = _get(hub, "/api/settings/remote")
    refused = c.delete("/api/settings/remote/delegations/desk-agent")
    assert refused.status_code == 409, refused.text
    wire["grant-stop-refused.json"] = _answer(refused)
    # A LIVE grant whose credential is gone, read with remote OFF.
    orphan = c.post("/api/settings/remote/credentials", json={"identity": "orphan-agent", "palette": "DESK"})
    assert c.put("/api/settings/remote/delegations/orphan-agent", json={}).status_code == 200
    token = orphan.json()["token"]
    gone = c.request("DELETE", "/api/principals/self",
                     headers={"X-HoldSpeak-Token": token, "Authorization": f"Bearer {token}"})
    assert gone.status_code == 200, gone.text
    assert c.put("/api/settings/remote", json={"enabled": False}).status_code == 200
    wire["grant-remote-orphan-off.json"] = _get(hub, "/api/settings/remote")
    assert c.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    # A stored LIVE grant past its expiry.
    assert c.put("/api/settings/remote/delegations/desk-agent", json={"expires_at": time.time() + 0.5}).status_code == 200
    time.sleep(0.8)
    wire["grant-remote-expired.json"] = _get(hub, "/api/settings/remote")
    # Project grants: a PROJECT credential and two projects.
    pay = c.post("/api/projects", json={"name": "Payments ledger cutover"}).json()["project"]["id"]
    c.post("/api/projects", json={"name": "Staff hiring loop"})
    _issue(hub, "sweep-runner")
    wire["grant-projects.json"] = _get(hub, "/api/projects")
    project_allowed = c.put(f"/api/settings/remote/delegations/sweep-runner/projects/{pay}", json={})
    assert project_allowed.status_code == 200, project_allowed.text
    wire["grant-project-allow.json"] = _answer(project_allowed)
    wire["grant-remote-project-live.json"] = _get(hub, "/api/settings/remote")
    assert c.delete(f"/api/settings/remote/delegations/sweep-runner/projects/{pay}").status_code == 200
    project_refused = c.delete(f"/api/settings/remote/delegations/sweep-runner/projects/{pay}")
    assert project_refused.status_code == 409, project_refused.text
    wire["grant-project-stop-refused.json"] = _answer(project_refused)
    # The owner revokes a credential whose desk grant is LIVE: the grant ends first.
    assert c.put("/api/settings/remote/delegations/desk-agent", json={}).status_code == 200
    revoked = c.delete(f"/api/settings/remote/credentials/{desk.json()['id']}")
    assert revoked.status_code == 200, revoked.text
    wire["grant-revoke-credential.json"] = _answer(revoked)
    # Remote OFF keeps a credential whose desk grant is LIVE (board 5d) and
    # hides a credential with no grant (sweep-runner's project grant is gone).
    again = c.post("/api/settings/remote/credentials", json={"identity": "desk-agent", "palette": "DESK"})
    assert again.status_code == 200, again.text
    assert c.put("/api/settings/remote/delegations/desk-agent", json={}).status_code == 200
    assert c.put("/api/settings/remote", json={"enabled": False}).status_code == 200
    wire["grant-remote-off-live.json"] = _get(hub, "/api/settings/remote")
    assert c.put("/api/settings/remote", json={"enabled": True}).status_code == 200
    return wire


def test_the_grant_wire_fixtures_carry_no_invented_field(hub: Any, tmp_path: Path) -> None:
    """The grant vitest doubles are the live hub's own answers (scar law)."""
    wire = _grant_wire(hub)
    assert wire["grant-stop-refused.json"]["error"] == "desk_delegation_required"
    assert wire["grant-project-stop-refused.json"]["error"] == "project_delegation_required"
    assert wire["grant-remote-expired.json"]["credentials"][0]["delegation"]["state"] == "EXPIRED"
    assert wire["grant-revoke-credential.json"]["grant_revoked"] is True
    if os.environ.get("HOLDSPEAK_WRITE_WIRE_FIXTURES") == "1":
        FIXTURES.mkdir(parents=True, exist_ok=True)
        for name, body in wire.items():
            text = json.dumps(_scrub(body, str(tmp_path)), indent=2, sort_keys=True) + "\n"
            (FIXTURES / name).write_text(text)
    problems: list[str] = []
    for name, body in wire.items():
        fixture_path = FIXTURES / name
        assert fixture_path.exists(), f"missing fixture {name}; write it with HOLDSPEAK_WRITE_WIRE_FIXTURES=1"
        problems += [f"{name}: {p}" for p in _invented(json.loads(fixture_path.read_text()), body)]
    assert not problems, "a grant vitest fixture carries a field the hub does not send: " + ", ".join(problems)


def test_the_calendar_sources_wire_names_each_sources_kind_and_egress(hub: Any, tmp_path: Path) -> None:
    """replaces: tests/e2e/test_hs144_door_glass.py::test_meetings_settings_calendar_glass_and_egress_fact

    A settings write answers with the backend-derived sources fact: an HTTPS
    source sends out (its host named), a file source does not, and no source
    is an empty list. (The Meetings face that draws it is fenced in
    web/src/desk/__tests__/settings.app.test.tsx, "Settings › Meetings".)
    """
    def put_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
        resp = hub.client.put("/api/settings", json={"calendar": {"sources": sources}})
        assert resp.status_code == 200, resp.text
        return resp.json()["settings"]["_calendar_sources"]

    fact = put_sources([{"id": "hs144-egress", "label": "", "url": "https://calendar.example.test/team.ics", "enabled": True}])
    assert fact == [{
        "id": "hs144-egress", "label": "", "kind": "https", "host": "calendar.example.test",
        "refresh_seconds": 900, "egress": True, "enabled": True,
    }]
    fact = put_sources([{"id": "hs144-egress", "label": "", "url": str(tmp_path / "calendar.ics"), "enabled": True}])
    assert fact[0]["egress"] is False
    assert put_sources([]) == []
