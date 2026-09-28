"""PHILO-9-02 B1: the connection read contract, fenced through the REAL hub.

The hub boots over an isolated database with the REAL provider adapters. The
only seam is the adapters' own subprocess runner (``gh_runner`` /
``acli_runner``, the hub's test seam since HS-161-06): a counting runner that
answers like the real CLIs. No adapter is mocked, so a read that probes shows
up as a counted ``gh`` / ``acli`` call.

* (a) ``GET /api/connections`` and MCP ``connection.list`` make zero provider
  calls for GitHub, Jira and Confluence.
* (b) a remote row with a stored check returns its own stored
  ``last_checked_at`` and its age; a row or provider with none returns
  ``never_checked`` and ``last_checked_at: null``.
* (c) Calendar and Models still read live (a config change shows at once,
  with no check time).
* (d) the Confluence Recheck makes a real probe and stores its time.

Red on main: the list runs ``gh auth status`` on every read and stamps the
read time; a never-probed GitHub reads ``owner_action_required`` or
``degraded``, an unchecked row reads ``owner_action_required``; the Confluence
Recheck makes zero calls and answers ``last_checked_at: null``.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import TOKEN, Hub  # noqa: E402

JIRA_SITE, JIRA_EMAIL = "alpha.atlassian.net", "owner@example.com"
CONF_SITE, CONF_EMAIL = "beta.atlassian.net", "owner@example.com"
REMOTE = ("github", "jira", "confluence")


class CountingRunner:
    """The CLI answering like the real one; every call counted by argv."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        if argv[:3] == ["gh", "auth", "status"]:
            out = "github.com\n  Logged in to github.com account karol-test (keyring)\n"
            return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "switch"]:
            return subprocess.CompletedProcess(argv, 0, stdout="switched\n", stderr="")
        if argv[:1] == ["acli"] and argv[2:4] == ["auth", "status"]:
            site = JIRA_SITE if argv[1] == "jira" else CONF_SITE
            out = f"✓ Authenticated\n  Site: {site}\n  Email: {JIRA_EMAIL}\n  Authentication Type: token\n"
            return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected call")

    def count(self) -> int:
        return len(self.calls)


def _boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gh: CountingRunner, acli: CountingRunner) -> Hub:
    import holdspeak.config as config_facade
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks
    from starlette.testclient import TestClient

    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "hub.db")
    monkeypatch.setattr(config_facade, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(tmp_path / "people.key"))
    reset_database()
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        auth_token=TOKEN,
        gh_runner=gh,
        acli_runner=acli,
    )
    server.broadcast = lambda *_a, **_k: None
    root = composition.installed()
    assert root is not None and root.bare_root is False, "the hub installed no root"
    client = TestClient(server.app, client=("127.0.0.1", 50000))
    client.headers.update({"Authorization": f"Bearer {TOKEN}"})
    hub = Hub(server, root, client, [])
    assert Path(str(hub.db.db_path)).parent == tmp_path, "the hub is not on the isolated database"
    return hub


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    gh, acli = CountingRunner(), CountingRunner()
    hub = _boot(tmp_path, monkeypatch, gh, acli)
    yield hub, gh, acli
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _tools(body: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {t["provider_id"]: t for t in body["tools"]}


def _http_list(hub: Hub) -> dict[str, dict[str, Any]]:
    resp = hub.client.get("/api/connections")
    assert resp.status_code == 200, resp.text
    return _tools(resp.json())


def _mcp_list(hub: Hub) -> dict[str, dict[str, Any]]:
    is_error, body = hub.mcp("connection.list", {})
    assert is_error is False, body
    return _tools(body)


def _stored(hub: Hub, connection_id: str) -> dict[str, Any]:
    row = hub.db.automations.get_provider_connection(connection_id)
    assert row is not None, f"no stored row {connection_id}"
    return row


def _seed_checked(hub: Hub) -> None:
    """Real producers: probe GitHub, add + probe one Jira and one Confluence row."""
    resp = hub.client.post("/api/connections/github/recheck")
    assert resp.status_code == 200, resp.text
    resp = hub.client.post("/api/providers/jira/connections",
                           json={"site": JIRA_SITE, "email": JIRA_EMAIL})
    assert resp.status_code == 200, resp.text
    resp = hub.client.post(f"/api/providers/jira/connections/{JIRA_SITE}|{JIRA_EMAIL}/recheck")
    assert resp.status_code == 200, resp.text
    resp = hub.client.post(f"/api/providers/confluence/connections/{CONF_SITE}|{CONF_EMAIL}/recheck")
    assert resp.status_code == 200, resp.text


# ── (a) the list makes no provider call ──────────────────────────────


@pytest.mark.parametrize("transport", ["http", "mcp"])
def test_list_makes_no_provider_call(rig, transport: str) -> None:
    hub, gh, acli = rig
    _seed_checked(hub)
    assert gh.count() >= 1 and acli.count() >= 2, "the seed did not reach the runner seam"
    gh.calls.clear()
    acli.calls.clear()

    tools = _http_list(hub) if transport == "http" else _mcp_list(hub)
    tools = _http_list(hub) if transport == "http" else _mcp_list(hub)

    assert set(REMOTE) <= set(tools)
    assert gh.calls == [], f"the list ran gh: {gh.calls}"
    assert acli.calls == [], f"the list ran acli: {acli.calls}"


def test_list_on_a_fresh_hub_makes_no_provider_call(rig) -> None:
    hub, gh, acli = rig
    _http_list(hub)
    _mcp_list(hub)
    assert gh.calls == [] and acli.calls == [], (gh.calls, acli.calls)


# ── (b) each row's own stored time, or never_checked ─────────────────


def _age_ok(entry: dict[str, Any]) -> None:
    checked = datetime.fromisoformat(entry["last_checked_at"])
    expected = (datetime.now(timezone.utc) - checked).total_seconds()
    assert isinstance(entry["checked_age_seconds"], int), entry
    assert 0 <= entry["checked_age_seconds"] <= expected + 1, entry


def test_each_remote_row_returns_its_own_stored_time(rig) -> None:
    hub, _gh, _acli = rig
    _seed_checked(hub)
    gh_row = _stored(hub, "wpc_github")
    jira_row = _stored(hub, f"wpc_jira_{JIRA_SITE}|{JIRA_EMAIL}")
    conf_row = _stored(hub, f"wpc_confluence_{CONF_SITE}|{CONF_EMAIL}")

    for tools in (_http_list(hub), _mcp_list(hub)):
        github = tools["github"]
        assert github["state"] == "connected"
        assert github["last_checked_at"] == gh_row["last_checked_at"]
        _age_ok(github)

        jira = tools["jira"]
        (jira_conn,) = jira["connections"]
        assert jira_conn["state"] == "connected"
        assert jira_conn["last_checked_at"] == jira_row["last_checked_at"]
        _age_ok(jira_conn)

        conf = tools["confluence"]
        (conf_conn,) = conf["connections"]
        assert conf["state"] == "connected"
        assert conf_conn["state"] == "connected"
        assert conf_conn["last_checked_at"] == conf_row["last_checked_at"]
        _age_ok(conf_conn)

    # Two probes, two stored times: the list does not flatten them to one.
    assert jira_row["last_checked_at"] != conf_row["last_checked_at"]


def test_no_stored_check_reads_never_checked(rig) -> None:
    hub, gh, acli = rig
    # A Jira row added but never probed (the real add route).
    resp = hub.client.post("/api/providers/jira/connections",
                           json={"site": JIRA_SITE, "email": JIRA_EMAIL})
    assert resp.status_code == 200, resp.text

    for tools in (_http_list(hub), _mcp_list(hub)):
        github = tools["github"]
        assert github["state"] == "never_checked", github
        assert github["last_checked_at"] is None
        assert github["checked_age_seconds"] is None

        (jira_conn,) = tools["jira"]["connections"]
        assert jira_conn["state"] == "never_checked", jira_conn
        assert jira_conn["last_checked_at"] is None
        assert tools["jira"]["state"] == "never_checked"

        conf = tools["confluence"]
        assert conf["state"] == "never_checked", conf
        assert conf["last_checked_at"] is None
    assert gh.calls == [] and acli.calls == []


# ── (c) Calendar and Models read live ────────────────────────────────


def test_calendar_and_models_read_live(rig) -> None:
    from holdspeak.config import Config
    from holdspeak.config.integrations import CalendarSource

    hub, gh, acli = rig
    before = _http_list(hub)
    assert before["calendar"]["state"] == "not_configured"
    assert before["calendar"]["last_checked_at"] is None
    assert before["models"]["last_checked_at"] is None

    config = Config.load()
    config.calendar.sources = [CalendarSource(id="work", label="Work",
                                              url="https://example.com/work.ics")]
    config.save()

    # No recheck: the next list reads the config as it is now.
    after = _http_list(hub)
    assert after["calendar"]["state"] == "connected"
    assert after["calendar"]["account"] == {"sources": 1}
    assert after["calendar"]["last_checked_at"] is None
    assert _mcp_list(hub)["calendar"]["state"] == "connected"
    assert after["models"]["account"]["total"] == 7
    assert gh.calls == [] and acli.calls == []


# ── (d) the Confluence Recheck makes a real probe ────────────────────


def test_confluence_recheck_probes_and_stores_its_time(rig) -> None:
    hub, _gh, acli = rig
    adapter = composition.service("confluence_provider", lambda: None)
    assert adapter is not None
    adapter.add_connection(None, CONF_SITE, CONF_EMAIL)
    cid = f"wpc_confluence_{CONF_SITE}|{CONF_EMAIL}"
    assert _stored(hub, cid)["last_checked_at"] is None
    acli.calls.clear()

    resp = hub.client.post("/api/connections/confluence/recheck")
    assert resp.status_code == 200, resp.text
    entry = resp.json()

    probes = [c for c in acli.calls if c[:2] == ["acli", "confluence"]]
    assert [c[2:4] for c in probes] == [["auth", "switch"], ["auth", "status"]], acli.calls
    stored = _stored(hub, cid)["last_checked_at"]
    assert stored is not None
    (conn,) = entry["connections"]
    assert conn["state"] == "connected"
    assert conn["last_checked_at"] == stored
