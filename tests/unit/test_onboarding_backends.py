"""Onboarding backends (owner, 2026-10-05): detect what he has; one "Use it".

Real producers where the product owns the code: the ICS renderer feeds the
real ICS parser; the calendar write goes through the real SettingsService and
Config file; the connectors are the real GitHub / Jira / Confluence adapters
and ConnectionsService over a real database.  The seams are the process edge
(the gh / acli runner, as the adapters' own tests use), the HTTPS fetch edge
(the reader), and the macOS permission (EventKit cannot grant access in a
test, and a test must never show the owner a prompt).
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from holdspeak.calendar_ingest import parse_calendar_bytes
from holdspeak.calendar_ingest_conductor import CalendarSourceError, CalendarSourceReader
from holdspeak.config.integrations import calendar_subscription_summary, validate_calendar_subscription
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.connections_service import ConnectionsService
from holdspeak.services.errors import ConflictError, NotFound, ValidationError
from holdspeak.services.github_provider import GitHubProviderAdapter
from holdspeak.services.jira_provider import JiraProviderAdapter
from holdspeak.services.onboarding_service import OnboardingService, read_gh_accounts

OWNER = Principal(PrincipalKind.OWNER, "onboarding-owner")
NOW = datetime(2026, 10, 5, 15, 0, tzinfo=timezone.utc)


def _ics(*events: dict[str, Any], name: str = "Work") -> bytes:
    from holdspeak.macos_calendar import events_as_ics

    return events_as_ics(list(events), calendar_name=name)


def _event(uid: str, hours: int, title: str = "1:1 with Ana", **extra: Any) -> dict[str, Any]:
    start = NOW + timedelta(hours=hours)
    return {"uid": uid, "title": title, "start": start, "end": start + timedelta(minutes=30), **extra}


class FakeMac:
    """The macOS permission seam: a state and the calendars EventKit would list."""

    def __init__(self, state: str = "not_determined", calendars: list[dict[str, Any]] | None = None) -> None:
        self.state = state
        self.calendars = calendars or []
        self.requests = 0

    def access_state(self) -> str:
        return self.state

    def request_access(self) -> str:
        self.requests += 1
        self.state = "full_access"
        return self.state

    def list_calendars(self) -> list[dict[str, Any]]:
        return list(self.calendars) if self.state == "full_access" else []


class Reader:
    def __init__(self, raw: bytes = b"", error: str = "") -> None:
        self.raw, self.error, self.urls = raw, error, []

    def read(self, url: str) -> bytes:
        self.urls.append(url)
        if self.error:
            raise CalendarSourceError(self.error)
        return self.raw


@pytest.fixture()
def settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak import config as config_module
    from holdspeak.services.settings_service import SettingsService

    monkeypatch.setattr(config_module, "CONFIG_FILE", tmp_path / "config.json")
    config_module.Config().save()
    return SettingsService(Database(tmp_path / "settings.db"))


def _service(tmp_path: Path, *, mac=None, reader=None, settings=None, **kwargs: Any) -> OnboardingService:
    refreshed: list[int] = []
    service = OnboardingService(
        settings_service=settings, macos=mac or FakeMac(), calendar_reader=reader,
        calendar_refresh=lambda: refreshed.append(1), home_provider=lambda: tmp_path / "home",
        environ={}, clock=lambda: NOW, **kwargs,
    )
    service.refreshed = refreshed  # type: ignore[attr-defined]
    return service


# ── the macOS calendar source ────────────────────────────────────────────


def test_rendered_macos_events_read_through_the_real_ics_parser() -> None:
    raw = _ics(
        _event("evt-1", 2, url="https://zoom.us/j/1", attendees=["ana@example.com"], location="Room 4"),
        _event("evt-2", 26, title="Planning"),
    )
    parsed = parse_calendar_bytes(raw, now=NOW, subscription_revision="r")
    assert parsed.feed_error is None and parsed.skips == ()
    assert [(e.uid, e.title) for e in parsed.events] == [("evt-1", "1:1 with Ana"), ("evt-2", "Planning")]
    first = parsed.events[0]
    assert first.meeting_url == "https://zoom.us/j/1"
    assert first.attendees == ("ana@example.com",)
    assert first.location == "Room 4"


def test_an_eventkit_source_is_valid_local_and_read_through_eventkit(monkeypatch) -> None:
    assert validate_calendar_subscription(" eventkit:ABC-123 ") == "eventkit:ABC-123"
    for bad in ("eventkit:", "eventkit:a b", "eventkit:x/y"):
        with pytest.raises(ValueError):
            validate_calendar_subscription(bad)
    summary = calendar_subscription_summary("eventkit:ABC-123")
    assert summary["kind"] == "macos" and summary["egress"] is False

    import holdspeak.macos_calendar as macos_calendar

    asked: list[str] = []
    monkeypatch.setattr(
        macos_calendar, "read_calendar_ics",
        lambda source: asked.append(source) or _ics(_event("evt-1", 1)),
    )
    raw = CalendarSourceReader().read("eventkit:ABC-123")
    assert asked == ["eventkit:ABC-123"]
    assert len(parse_calendar_bytes(raw, now=NOW, subscription_revision="r").events) == 1


def test_a_webcal_link_reads_as_https() -> None:
    assert validate_calendar_subscription("webcal://p01-caldav.icloud.com/published/2/abc") == (
        "https://p01-caldav.icloud.com/published/2/abc"
    )


def test_the_permission_read_never_prompts_and_names_a_state() -> None:
    from holdspeak import macos_calendar

    # The real EventKit status read on this machine (or "unavailable" off macOS).
    assert macos_calendar.access_state() in {*macos_calendar.STATES.values(), "unavailable", "unknown"}


def test_without_full_access_an_eventkit_read_is_refused_by_name(monkeypatch) -> None:
    from holdspeak import macos_calendar

    monkeypatch.setattr(macos_calendar, "access_state", lambda: "denied")
    with pytest.raises(CalendarSourceError) as caught:
        macos_calendar.read_calendar_ics("eventkit:ABC")
    assert caught.value.error_class == "calendar_source_permission"


# ── calendar detect / access / check / use ───────────────────────────────


def test_detect_offers_the_macos_prompt_only_while_it_can_appear(tmp_path, settings) -> None:
    mac = FakeMac("not_determined", [{"id": "CAL-1", "title": "Work", "account": "iCloud", "kind": "caldav"}])
    service = _service(tmp_path, mac=mac, settings=settings)
    first = service.calendar_detect(OWNER)
    assert first["macos"] == {"state": "not_determined", "can_request": True}
    assert first["candidates"] == [] and mac.requests == 0  # detect never prompts

    granted = service.calendar_request_access(OWNER)
    assert mac.requests == 1
    assert granted["macos"]["state"] == "full_access" and granted["macos"]["can_request"] is False
    assert granted["candidates"] == [{
        "id": "eventkit:CAL-1", "kind": "macos", "label": "Work", "account": "iCloud",
        "calendar_kind": "caldav", "lamp": "local", "egress_host": None, "in_use": False, "verb": "Use it",
    }]


def test_use_it_adds_the_macos_calendar_through_settings_once(tmp_path, settings) -> None:
    from holdspeak.config import Config

    mac = FakeMac("full_access", [{"id": "CAL-1", "title": "Work", "account": "iCloud", "kind": "caldav"}])
    service = _service(tmp_path, mac=mac, settings=settings)
    result = service.calendar_use(OWNER, {"id": "eventkit:CAL-1"})
    assert result["added"] is True
    assert result["source"]["url"] == "eventkit:CAL-1" and result["source"]["kind"] == "macos"
    assert result["source"]["label"] == "Work"
    assert [(s.url, s.label) for s in Config.load().calendar.sources] == [("eventkit:CAL-1", "Work")]
    assert service.calendar_detect(OWNER)["candidates"][0]["in_use"] is True
    again = service.calendar_use(OWNER, {"id": "eventkit:CAL-1"})
    assert again["added"] is False and len(Config.load().calendar.sources) == 1
    with pytest.raises(NotFound):
        service.calendar_use(OWNER, {"id": "eventkit:GONE"})


def test_use_it_on_a_macos_calendar_needs_the_permission(tmp_path, settings) -> None:
    service = _service(tmp_path, mac=FakeMac("denied"), settings=settings)
    with pytest.raises(ConflictError) as caught:
        service.calendar_use(OWNER, {"id": "eventkit:CAL-1"})
    assert caught.value.code == "calendar_permission_required"


def test_check_reads_an_ics_url_once_and_names_its_host(tmp_path, settings) -> None:
    reader = Reader(_ics(_event("a", 3), _event("b", 30), name="Team calendar"))
    service = _service(tmp_path, reader=reader, settings=settings)
    result = service.calendar_check(OWNER, "webcal://calendar.example.com/feed.ics")
    assert reader.urls == ["https://calendar.example.com/feed.ics"]
    assert result["ok"] is True and result["host"] == "calendar.example.com" and result["lamp"] == "cloud"
    assert result["events_next_days"] == 2
    assert result["candidate"]["id"] == "https://calendar.example.com/feed.ics"
    assert result["candidate"]["label"] == "Team calendar" and result["candidate"]["verb"] == "Use it"

    added = service.calendar_use(OWNER, {"id": result["candidate"]["id"], "label": result["candidate"]["label"]})
    assert added["source"]["kind"] == "https" and added["source"]["egress_host"] == "calendar.example.com"
    assert service.refreshed == [1]  # type: ignore[attr-defined]


def test_check_names_a_failed_read_and_refuses_a_bad_link(tmp_path, settings) -> None:
    failing = _service(tmp_path, reader=Reader(error="calendar_source_http_error"), settings=settings)
    result = failing.calendar_check(OWNER, "https://calendar.example.com/x.ics")
    assert result["ok"] is False and result["error_class"] == "calendar_source_http_error"
    not_ics = _service(tmp_path, reader=Reader(b"<html>login</html>"), settings=settings)
    assert not_ics.calendar_check(OWNER, "https://calendar.example.com/x")["ok"] is False
    for bad in ("http://calendar.example.com/x.ics", "/Users/me/cal.ics", "https://user:pw@x.example/c.ics"):
        with pytest.raises(ValidationError):
            failing.calendar_check(OWNER, bad)


# ── connections ──────────────────────────────────────────────────────────

_HOSTS_YML = """\
github.com:
    git_protocol: https
    users:
        karolswdev:
            oauth_token: gho_SECRET_ONE
        karoldriven:
            oauth_token: gho_SECRET_TWO
    user: karolswdev
    oauth_token: gho_SECRET_ONE
"""

_ACLI_YML = """\
version: 1
current_profile: cloud-1:acct-1
profiles:
  - site: alpha.atlassian.net
    cloud_id: cloud-1
    account_id: acct-1
    display_name: Karol S
    email: Karol@Example.com
    auth_type: oauth
"""


def _home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    (home / ".config" / "gh").mkdir(parents=True)
    (home / ".config" / "gh" / "hosts.yml").write_text(_HOSTS_YML)
    (home / ".config" / "acli").mkdir(parents=True)
    (home / ".config" / "acli" / "jira_config.yaml").write_text(_ACLI_YML)
    (home / ".config" / "acli" / "confluence_config.yaml").write_text(_ACLI_YML)
    return home


def _runner(log: list[list[str]]):
    def run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        argv = list(args[0])
        log.append(argv)
        if argv[:3] == ["gh", "auth", "status"]:
            out = "github.com\n  Logged in to github.com account karolswdev (keyring)\n"
        elif argv[-2:] == ["auth", "status"]:
            out = "✓ Authenticated\n  Site: alpha.atlassian.net\n  Email: karol@example.com\n"
        elif "switch" in argv:
            out = "✓ Switched to account: alpha.atlassian.net [karol@example.com]"
        else:
            out = ""
        return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
    return run


def _connections(tmp_path: Path, log: list[list[str]]) -> tuple[OnboardingService, Database]:
    from holdspeak.services.confluence_provider import ConfluenceProviderAdapter

    home = _home(tmp_path)
    db = Database(tmp_path / "connections.db")
    runner = _runner(log)
    jira = JiraProviderAdapter(db=db, runner=runner, registry_path=home / ".config" / "acli" / "jira_config.yaml")
    confluence = ConfluenceProviderAdapter(db=db, runner=runner)
    connections = ConnectionsService(
        github_adapter=GitHubProviderAdapter(db=db, runner=runner),
        jira_adapter=jira, confluence_adapter=confluence,
    )
    service = OnboardingService(
        connections_service=connections, jira_provider=jira, confluence_provider=confluence,
        home_provider=lambda: home, environ={}, macos=FakeMac(),
        which=lambda name: f"/usr/bin/{name}",
    )
    return service, db


def test_gh_accounts_are_read_without_any_token(tmp_path) -> None:
    home = _home(tmp_path)
    rows = read_gh_accounts(home / ".config" / "gh" / "hosts.yml")
    assert rows == [
        {"host": "github.com", "login": "karolswdev", "active": True},
        {"host": "github.com", "login": "karoldriven", "active": False},
    ]
    assert "SECRET" not in repr(rows)


def test_detect_runs_no_process_and_lists_every_signed_in_account(tmp_path) -> None:
    log: list[list[str]] = []
    service, _db = _connections(tmp_path, log)
    detected = service.connections_detect(OWNER)
    assert log == []  # files only: no gh, no acli
    assert "SECRET" not in repr(detected)
    by_id = {c["id"]: c for c in detected["candidates"]}
    assert set(by_id) == {
        "github:github.com:karolswdev", "github:github.com:karoldriven",
        "jira:alpha.atlassian.net|karol@example.com", "confluence:alpha.atlassian.net|karol@example.com",
    }
    assert by_id["github:github.com:karolswdev"]["verb"] == "Use it"
    assert by_id["github:github.com:karoldriven"]["verb"] is None  # not gh's active login
    jira = by_id["jira:alpha.atlassian.net|karol@example.com"]
    assert jira["active"] is True and jira["connected"] is False and jira["egress_host"] == "alpha.atlassian.net"
    assert detected["tools"]["gh"]["installed"] is True


def test_use_it_connects_github_through_its_status_probe(tmp_path) -> None:
    log: list[list[str]] = []
    service, _db = _connections(tmp_path, log)
    result = service.connections_use(OWNER, {"id": "github:github.com:karolswdev"})
    assert ["gh", "auth", "status"] in log
    assert result["entry"]["state"] == "connected"
    detected = {c["id"]: c for c in service.connections_detect(OWNER)["candidates"]}
    assert detected["github:github.com:karolswdev"]["connected"] is True
    with pytest.raises(ConflictError) as caught:
        service.connections_use(OWNER, {"id": "github:github.com:karoldriven"})
    assert caught.value.code == "github_account_not_active"


@pytest.mark.parametrize("provider", ["jira", "confluence"])
def test_use_it_adds_the_atlassian_connection_with_switch_and_verify(tmp_path, provider) -> None:
    log: list[list[str]] = []
    service, _db = _connections(tmp_path, log)
    candidate = f"{provider}:alpha.atlassian.net|karol@example.com"
    result = service.connections_use(OWNER, {"id": candidate})
    assert ["acli", provider, "auth", "switch", "--site", "alpha.atlassian.net",
            "--email", "karol@example.com"] in log
    assert ["acli", provider, "auth", "status"] in log
    rows = result["entry"]["connections"]
    assert [(r["connection_ref"], r["state"]) for r in rows] == [
        ("alpha.atlassian.net|karol@example.com", "connected"),
    ]
    detected = {c["id"]: c for c in service.connections_detect(OWNER)["candidates"]}
    assert detected[candidate]["connected"] is True


def test_use_it_refuses_an_unknown_candidate(tmp_path) -> None:
    service, _db = _connections(tmp_path, [])
    with pytest.raises(NotFound):
        service.connections_use(OWNER, {"id": "jira:nobody.atlassian.net|x@y.z"})


# ── the routes ───────────────────────────────────────────────────────────


def _app(service: OnboardingService):
    from fastapi import FastAPI, Request

    from holdspeak.web.routes.onboarding import build_onboarding_router

    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_onboarding_router(SimpleNamespace(onboarding_service=service)))
    return TestClient(app)


def test_the_routes_parse_and_serialize_the_service(tmp_path, settings) -> None:
    mac = FakeMac("full_access", [{"id": "CAL-1", "title": "Work", "account": "iCloud", "kind": "caldav"}])
    client = _app(_service(tmp_path, mac=mac, settings=settings, reader=Reader(_ics(_event("a", 2)))))
    detect = client.get("/api/onboarding/calendar")
    assert detect.status_code == 200 and detect.json()["candidates"][0]["id"] == "eventkit:CAL-1"
    assert client.post("/api/onboarding/calendar/macos/access").json()["macos"]["state"] == "full_access"
    check = client.post("/api/onboarding/calendar/check", json={"url": "https://c.example.com/a.ics"})
    assert check.status_code == 200 and check.json()["ok"] is True
    use = client.post("/api/onboarding/calendar/use", json={"id": "eventkit:CAL-1"})
    assert use.status_code == 200 and use.json()["added"] is True
    bad = client.post("/api/onboarding/calendar/check", json={"url": "ftp://x"})
    assert bad.status_code == 400 and bad.json()["code"] == "calendar_url_invalid"
    assert client.post("/api/onboarding/calendar/use", content=b"[]").status_code == 400
    assert client.get("/api/onboarding/connections").status_code == 200
    assert client.post("/api/onboarding/connections/use", json={"id": "nope"}).status_code == 503


@pytest.mark.timeout(60)
def test_the_hub_mounts_the_routes(tmp_path, monkeypatch) -> None:
    from holdspeak.principals import PrincipalRight, required_right
    from tests.unit.test_web_server_startup import _server

    for method, path in (("GET", "/api/onboarding/calendar"), ("POST", "/api/onboarding/connections/use")):
        assert required_right(method, path) is PrincipalRight.OWNER
    server = _server(tmp_path, monkeypatch)
    client = TestClient(server.app)
    answer = client.get(
        "/api/onboarding/connections", headers={"Authorization": f"Bearer {server.auth_token}"},
    )
    assert answer.status_code == 200, answer.text
    assert set(answer.json()) == {"candidates", "tools"}
