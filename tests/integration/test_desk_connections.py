"""Connections, through the real hub (the test diet, 2026-10-11).

The rig of ``tests/unit/test_philo9_b1_connections.py``: the real hub on an
isolated database with the REAL provider adapters; the only seam is their
subprocess runner (a counting ``gh`` / ``acli``).

The wire fixtures under ``web/src/desk/__tests__/fixtures/connections-wire/``
are what ``web/src/desk/__tests__/connections.app.test.tsx`` answers its
``fetch`` with; ``test_the_connections_wire_fixtures_carry_no_invented_field``
proves each field is one the live hub sends. Write them again with
``HOLDSPEAK_WRITE_WIRE_FIXTURES=1``.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.runtime import composition
from tests.integration.test_desk_settings import _invented
from tests.unit.test_philo9_b1_connections import CountingRunner, _boot

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "connections-wire"
EMAIL = "owner@example.com"
ALPHA, BETA = "alpha.atlassian.net", "beta.atlassian.net"


def _which(acli_present: bool):
    real = shutil.which

    def which(name: str, *args: Any, **kwargs: Any) -> str | None:
        if name == "acli":
            return "/usr/local/bin/acli" if acli_present else None
        return real(name, *args, **kwargs)

    return which


@pytest.fixture
def rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    def boot(acli_present: bool = True):
        monkeypatch.setattr(shutil, "which", _which(acli_present))
        gh, acli = CountingRunner(), CountingRunner()
        return _boot(tmp_path, monkeypatch, gh, acli), gh, acli

    yield boot
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _tools(hub: Any) -> dict[str, dict[str, Any]]:
    resp = hub.client.get("/api/connections")
    assert resp.status_code == 200, resp.text
    return {t["provider_id"]: t for t in resp.json()["tools"]}


def _seed_two_ages(hub: Any) -> None:
    """GitHub checked now; Jira alpha checked 2 h back; Jira beta never checked."""
    assert hub.client.post("/api/connections/github/recheck").status_code == 200
    for site in (ALPHA, BETA):
        resp = hub.client.post("/api/providers/jira/connections", json={"site": site, "email": EMAIL})
        assert resp.status_code == 200, resp.text
    resp = hub.client.post(f"/api/providers/jira/connections/{ALPHA}|{EMAIL}/recheck")
    assert resp.status_code == 200, resp.text
    two_hours = (datetime.now(timezone.utc) - timedelta(hours=2, minutes=5)).isoformat()
    hub.db.automations.update_provider_connection(f"wpc_jira_{ALPHA}|{EMAIL}", last_checked_at=two_hours)


@pytest.mark.parametrize(("acli_present", "state"), [(True, "never_checked"), (False, "unavailable")])
def test_the_empty_jira_card_is_the_tools_own_state(rig, acli_present: bool, state: str) -> None:
    """replaces: tests/e2e/test_philo9_b1_connections_glass.py::test_the_empty_jira_card_shows_its_own_state (the hub half)

    No Jira row: ``acli`` on PATH reads never checked; missing reads
    unavailable (the face words: "Never checked" / "acli missing"), never the
    hardcoded not-set-up the face once drew. The read runs no CLI.
    """
    hub, gh, acli = rig(acli_present)
    jira = _tools(hub)["jira"]
    assert jira["connections"] == []
    assert jira["state"] == state, jira
    assert gh.calls == [] and acli.calls == []


def test_each_row_carries_its_own_check_age_and_the_read_runs_no_cli(rig) -> None:
    """replaces: tests/e2e/test_philo9_b1_connections_glass.py::test_each_card_shows_its_own_age (the hub half)"""
    hub, gh, acli = rig(True)
    _seed_two_ages(hub)
    gh.calls.clear()
    acli.calls.clear()

    tools = _tools(hub)
    assert tools["github"]["state"] == "connected"
    assert tools["github"]["checked_age_seconds"] < 60
    rows = {c["account"]["site"]: c for c in tools["jira"]["connections"]}
    assert rows[ALPHA]["state"] == "connected"
    assert 2 * 3600 <= rows[ALPHA]["checked_age_seconds"] < 3 * 3600
    assert rows[BETA]["state"] == "never_checked" and rows[BETA]["last_checked_at"] is None
    assert tools["confluence"]["state"] == "never_checked"
    assert tools["calendar"]["state"] == "not_configured" and tools["calendar"]["last_checked_at"] is None
    assert tools["models"]["last_checked_at"] is None
    assert gh.calls == [] and acli.calls == [], (gh.calls, acli.calls)


def test_the_connections_wire_fixtures_carry_no_invented_field(rig, tmp_path: Path) -> None:
    """The vitest doubles are the live hub's own answers (scar law)."""
    hub, _gh, _acli = rig(True)
    wire = {"connections-cold.json": json.loads(hub.client.get("/api/connections").text)}
    _seed_two_ages(hub)
    wire["connections-checked.json"] = json.loads(hub.client.get("/api/connections").text)
    if os.environ.get("HOLDSPEAK_WRITE_WIRE_FIXTURES") == "1":
        FIXTURES.mkdir(parents=True, exist_ok=True)
        for name, body in wire.items():
            (FIXTURES / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    problems: list[str] = []
    for name, body in wire.items():
        path = FIXTURES / name
        assert path.exists(), f"missing fixture {name}; write it with HOLDSPEAK_WRITE_WIRE_FIXTURES=1"
        problems += [f"{name}: {p}" for p in _invented(json.loads(path.read_text()), body)]
    assert not problems, "a Connections vitest fixture carries a field the hub does not send: " + ", ".join(problems)


# ── fork C2: the GitHub Recheck answer and a sign-in read from gh's config ──


def test_the_recheck_and_signed_in_wire_fixtures_carry_no_invented_field(
        rig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The Recheck answer (a tool entry) and the list with a gh-config sign-in are the live hub's (scar law).

    The hub half of the sign-in (``signed_in``, the login, no check time,
    ``checked_by: gh_config``) is fenced in
    tests/unit/test_onboarding_backends.py::test_b31_first_run_and_connections_read_one_gh_sign_in.
    """
    gh_dir = tmp_path / "gh-config"
    gh_dir.mkdir()
    (gh_dir / "hosts.yml").write_text(
        "github.com:\n    users:\n        karolswdev:\n    git_protocol: https\n    user: karolswdev\n",
        encoding="utf-8")
    monkeypatch.setenv("GH_CONFIG_DIR", str(gh_dir))
    hub, _gh, _acli = rig(True)
    signed = json.loads(hub.client.get("/api/connections").text)
    github = next(t for t in signed["tools"] if t["provider_id"] == "github")
    assert (github["state"], github["account"], github["last_checked_at"], github["checked_by"]) == (
        "signed_in", {"login": "karolswdev"}, None, "gh_config")
    recheck = hub.client.post("/api/connections/github/recheck")
    assert recheck.status_code == 200, recheck.text
    wire = {"connections-signed-in.json": signed, "recheck-github.json": recheck.json()}
    assert wire["recheck-github.json"]["state"] == "connected"
    if os.environ.get("HOLDSPEAK_WRITE_WIRE_FIXTURES") == "1":
        for name, body in wire.items():
            (FIXTURES / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    problems: list[str] = []
    for name, body in wire.items():
        path = FIXTURES / name
        assert path.exists(), f"missing fixture {name}; write it with HOLDSPEAK_WRITE_WIRE_FIXTURES=1"
        problems += [f"{name}: {p}" for p in _invented(json.loads(path.read_text()), body)]
    assert not problems, "a Connections vitest fixture carries a field the hub does not send: " + ", ".join(problems)
