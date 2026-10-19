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


# ── Betterment ST2: Check leaves acli where it was; state words; Found ──

ACLI_YAML = """\
version: 1
current_profile: "{current}"
profiles:
  - site: alpha.atlassian.net
    cloud_id: c1
    account_id: a1
    display_name: Owner
    email: owner@example.com
    auth_type: token
  - site: beta.atlassian.net
    cloud_id: c2
    account_id: a1
    display_name: Owner
    email: owner@example.com
    auth_type: token
{extra}"""
THIRD = """\
  - site: gamma.atlassian.net
    cloud_id: c3
    account_id: a1
    display_name: Owner
    email: owner@example.com
    auth_type: token
"""
PROFILE_KEY = {ALPHA: "c1:a1", BETA: "c2:a1", "gamma.atlassian.net": "c3:a1"}


class StubAcli:
    """acli as it behaves on disk: ``auth switch`` rewrites ``current_profile``
    in its own registry file; ``auth status`` reads it back."""

    def __init__(self, home: Path) -> None:
        self.home = home
        self.calls: list[list[str]] = []

    def path(self, product: str) -> Path:
        return self.home / ".config" / "acli" / f"{product}_config.yaml"

    def write(self, product: str, current: str, extra: str = "") -> None:
        self.path(product).parent.mkdir(parents=True, exist_ok=True)
        self.path(product).write_text(ACLI_YAML.format(current=PROFILE_KEY[current], extra=extra), encoding="utf-8")

    def current(self, product: str) -> str:
        text = self.path(product).read_text(encoding="utf-8")
        key = text.split('current_profile: "', 1)[1].split('"', 1)[0]
        return next(site for site, k in PROFILE_KEY.items() if k == key)

    def __call__(self, argv: list[str], **_: Any):
        import subprocess

        self.calls.append(list(argv))
        product = argv[1]
        if argv[2:4] == ["auth", "switch"]:
            site = argv[argv.index("--site") + 1]
            text = self.path(product).read_text(encoding="utf-8")
            old = text.split('current_profile: "', 1)[1].split('"', 1)[0]
            self.path(product).write_text(text.replace(old, PROFILE_KEY[site], 1), encoding="utf-8")
            return subprocess.CompletedProcess(argv, 0, stdout="switched\n", stderr="")
        if argv[2:4] == ["auth", "status"]:
            out = f"✓ Authenticated\n  Site: {self.current(product)}\n  Email: {EMAIL}\n  Authentication Type: token\n"
            return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected call")


@pytest.fixture
def acli_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database
    from tests.unit.test_philo9_b1_connections import _boot as boot_hub

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GH_CONFIG_DIR", str(home / ".config" / "gh"))
    monkeypatch.setattr(shutil, "which", _which(True))
    acli = StubAcli(home)
    acli.write("jira", ALPHA)
    acli.write("confluence", ALPHA)

    def boot(gh: Any = None):
        return boot_hub(tmp_path, monkeypatch, gh or CountingRunner(), acli)

    yield boot, acli
    reset_database()
    composition.install(composition.bare(label="pytest"))


@pytest.mark.parametrize("product", ["jira", "confluence"])
def test_check_on_the_second_site_leaves_acli_on_the_first(acli_home, product: str) -> None:
    """Check on beta switches acli to beta to read its status, then back to alpha."""
    boot, acli = acli_home
    hub = boot()
    for site in (ALPHA, BETA):
        assert hub.client.post(f"/api/providers/{product}/connections",
                               json={"site": site, "email": EMAIL}).status_code == 200
    resp = hub.client.post(f"/api/connections/{product}/recheck", json={"ref": f"{BETA}|{EMAIL}"})
    assert resp.status_code == 200, resp.text
    rows = {c["account"]["site"]: c for c in resp.json()["connections"]}
    assert rows[BETA]["state"] == "connected", rows[BETA]
    assert acli.current(product) == ALPHA, "the Check left acli on the checked account"
    switches = [c[c.index("--site") + 1] for c in acli.calls if c[2:4] == ["auth", "switch"]]
    assert switches == [BETA, ALPHA], acli.calls


def test_a_check_of_the_current_account_does_not_switch_back(acli_home) -> None:
    boot, acli = acli_home
    hub = boot()
    hub.client.post("/api/providers/jira/connections", json={"site": ALPHA, "email": EMAIL})
    assert hub.client.post("/api/connections/jira/recheck", json={"ref": f"{ALPHA}|{EMAIL}"}).status_code == 200
    assert [c for c in acli.calls if c[2:4] == ["auth", "switch"]] == [
        ["acli", "jira", "auth", "switch", "--site", ALPHA, "--email", EMAIL]]
    assert acli.current("jira") == ALPHA


def test_a_new_profile_in_acli_is_found_and_use_connects_it(acli_home) -> None:
    """A third profile in acli's file shows under Found (not connected); one Use connects it."""
    boot, acli = acli_home
    acli.write("jira", ALPHA, extra=THIRD)
    hub = boot()
    for site in (ALPHA, BETA):
        hub.client.post("/api/providers/jira/connections", json={"site": site, "email": EMAIL})
        hub.client.post("/api/connections/jira/recheck", json={"ref": f"{site}|{EMAIL}"})
    found = hub.client.get("/api/onboarding/connections").json()["candidates"]
    jira = {c["site"]: c for c in found if c["provider"] == "jira"}
    assert jira[ALPHA]["connected"] and jira[BETA]["connected"]
    gamma = jira["gamma.atlassian.net"]
    assert gamma["connected"] is False and gamma["verb"], gamma
    used = hub.client.post("/api/onboarding/connections/use", json={"id": gamma["id"]})
    assert used.status_code == 200, used.text
    rows = {c["account"]["site"]: c for c in used.json()["entry"]["connections"]}
    assert rows["gamma.atlassian.net"]["state"] == "connected"
    assert acli.current("jira") == ALPHA, "Use moved his terminal's acli account"


def test_state_words_a_refused_gh_says_it_was_not_run(rig) -> None:
    """A refused CLI (the test guard) reads ``gh was not run``, never a bare degraded."""
    from holdspeak.cli_guard import RealCliRefusedInTests

    hub, _gh, _acli = rig(True)

    def refused(argv: list[str], **_: Any):
        raise RealCliRefusedInTests("real_cli_refused_in_tests: gh at /opt/homebrew/bin/gh; inject a runner")

    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.github_provider import GitHubProviderAdapter

    # The hub's own adapter class on the hub's database, with the runner the
    # guard puts in front of a real gh: the stored row is what the list reads.
    GitHubProviderAdapter(db=hub.db, runner=refused).connection_status(
        Principal(PrincipalKind.OWNER, "st2-owner"))
    github = _tools(hub)["github"]
    assert github["state"] == "degraded"
    assert github["reason"] == "gh was not run", github


def test_state_words_another_account_and_what_uses_it(acli_home) -> None:
    """A read-back naming another account is flagged; a destination on the row is listed under used_by."""
    import subprocess

    boot, acli = acli_home
    hub = boot()
    hub.client.post("/api/providers/jira/connections", json={"site": BETA, "email": EMAIL})
    original = StubAcli.__call__

    def other(self: StubAcli, argv: list[str], **kw: Any):
        if argv[2:4] == ["auth", "status"]:
            self.calls.append(list(argv))
            out = f"✓ Authenticated\n  Site: {BETA}\n  Email: someone.else@example.com\n  Authentication Type: token\n"
            return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")
        return original(self, argv, **kw)

    StubAcli.__call__ = other  # type: ignore[method-assign]
    try:
        hub.client.post("/api/connections/jira/recheck", json={"ref": f"{BETA}|{EMAIL}"})
    finally:
        StubAcli.__call__ = original  # type: ignore[method-assign]
    row = _tools(hub)["jira"]["connections"][0]
    assert row["state"] == "degraded" and row["other_account"] is True and row["reason"] is None, row
    assert acli.current("jira") == ALPHA

    with hub.db._connection() as conn:
        conn.execute(
            "INSERT INTO channel_destinations (id, name, channel, account_json, target_json, target_digest, created_at)"
            " VALUES ('d1', 'Team Jira', 'jira', ?, '{}', 'x', '2026-10-18T00:00:00Z')",
            (json.dumps({"site": BETA, "email": EMAIL}),),
        )
    row = _tools(hub)["jira"]["connections"][0]
    assert row["used_by"] == [{"kind": "destination", "name": "Team Jira"}], row


def test_remove_drops_the_row_and_add_again_brings_it_back(acli_home) -> None:
    boot, acli = acli_home
    hub = boot()
    hub.client.post("/api/providers/confluence/connections", json={"site": ALPHA, "email": EMAIL})
    resp = hub.client.delete(f"/api/providers/confluence/connections/{ALPHA}|{EMAIL}")
    assert resp.status_code == 200, resp.text
    assert _tools(hub)["confluence"]["connections"] == []
    assert hub.client.delete(f"/api/providers/confluence/connections/{ALPHA}|{EMAIL}").status_code == 404
    assert hub.client.post("/api/providers/confluence/connections", json={"site": ALPHA, "email": EMAIL}).status_code == 200
    assert len(_tools(hub)["confluence"]["connections"]) == 1
    assert acli.calls == [], "Remove and Add run no acli"


def test_the_st2_wire_fixtures_are_the_hubs_own(acli_home) -> None:
    """Two Jira sites checked, a third only in acli's file (Found), and its Use: the hub's own answers.

    The vitest doubles of ``connections-pane.test.tsx`` (Betterment ST2).
    Write them again with ``HOLDSPEAK_WRITE_WIRE_FIXTURES=1``.
    """
    boot, acli = acli_home
    acli.write("jira", ALPHA, extra=THIRD)
    hub = boot()
    for site in (ALPHA, BETA):
        hub.client.post("/api/providers/jira/connections", json={"site": site, "email": EMAIL})
        hub.client.post("/api/connections/jira/recheck", json={"ref": f"{site}|{EMAIL}"})
    wire: dict[str, Any] = {
        "st2-connections.json": json.loads(hub.client.get("/api/connections").text),
        "st2-found.json": json.loads(hub.client.get("/api/onboarding/connections").text),
    }
    gamma = next(c for c in wire["st2-found.json"]["candidates"] if c["site"] == "gamma.atlassian.net")
    used = hub.client.post("/api/onboarding/connections/use", json={"id": gamma["id"]})
    assert used.status_code == 200, used.text
    wire["st2-use.json"] = used.json()
    wire["st2-connections-after-use.json"] = json.loads(hub.client.get("/api/connections").text)
    wire["st2-found-after-use.json"] = json.loads(hub.client.get("/api/onboarding/connections").text)
    removed = hub.client.delete(f"/api/providers/jira/connections/{BETA}|{EMAIL}")
    assert removed.status_code == 200, removed.text
    wire["st2-remove.json"] = removed.json()
    if os.environ.get("HOLDSPEAK_WRITE_WIRE_FIXTURES") == "1":
        for name, body in wire.items():
            (FIXTURES / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    problems: list[str] = []
    for name, body in wire.items():
        path = FIXTURES / name
        assert path.exists(), f"missing fixture {name}; write it with HOLDSPEAK_WRITE_WIRE_FIXTURES=1"
        problems += [f"{name}: {p}" for p in _invented(json.loads(path.read_text()), body)]
    assert not problems, "an ST2 vitest fixture carries a field the hub does not send: " + ", ".join(problems)
