"""An agent's reads of the connections family (Codex on #2140, NOT RATIFIED).

One test per finding: an agent's engine detection starts no check and changes
no assignment; its answer carries no host, address, path or key flag; its PR
read is the delegated repository's, within a budget; Jira search is the
owner's; a bare root never opens the owner's database.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind

AGENT = Principal(PrincipalKind.AGENT, "agent:run:run_codex2140")
OWNER = Principal(PrincipalKind.OWNER, "owner")


def _service(tmp_path: Path, kicks: list[str]) -> Any:
    from holdspeak.services.concierge_service import ConciergeService

    db = Database(tmp_path / "engines.db")
    db.profiles.upsert(profile_id="lan-box", name="LAN box", kind="openAICompatible",
                       base_url="http://192.168.1.43:8080/v1", model="qwen")
    db.profiles.upsert(profile_id="Migrated-box", name="Migrated endpoint", kind="openAICompatible",
                       base_url="http://192.168.1.44:8080/v1", model="default")
    db.profiles.upsert(profile_id="cloud-x", name="Cloud X", kind="openAICompatible",
                       base_url="https://api.example.com/v1", model="x-large", requires_key=True)
    source = SimpleNamespace(
        inference_setup_service=SimpleNamespace(_db=db, _home_provider=lambda: tmp_path / "home"),
        inference_default_service=SimpleNamespace(kick=kicks.append),
    )
    return ConciergeService(source)


@pytest.fixture()
def no_egress(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every endpoint check or loopback scan the detection would start, by name."""
    started: list[str] = []
    monkeypatch.setattr("holdspeak.setup_runtime.discover_endpoint_models",
                        lambda base, **_k: started.append(base) or {"ok": True, "models": ["qwen"]})
    monkeypatch.setattr("holdspeak.services.inference_default_service.scan_loopback_engines",
                        lambda: started.append("loopback") or [])
    monkeypatch.setattr("holdspeak.services.concierge_service.ConciergeService._live_hub",
                        staticmethod(lambda: True))
    from holdspeak.net_bounds import endpoint_checks

    endpoint_checks.reset()
    yield started
    endpoint_checks.reset()


def test_an_agents_detection_starts_no_check_and_changes_no_assignment(tmp_path: Path, no_egress: list[str]) -> None:
    """Findings 1 and 2: stored checks only; no default kick for an agent."""
    kicks: list[str] = []
    service = _service(tmp_path, kicks)
    for _ in range(2):
        service.detect(AGENT)
        service.detect(AGENT, fresh=True)
        service.propose(AGENT)
    assert no_egress == [] and kicks == [], (no_egress, kicks)
    # The owner's read checks and kicks, as before.
    service.detect(OWNER)
    assert "http://192.168.1.43:8080/v1" in no_egress and kicks == ["detect"], (no_egress, kicks)


def test_an_agents_engine_answer_carries_no_host_address_path_or_key_flag(
    tmp_path: Path, no_egress: list[str],
) -> None:
    """Finding 3: one projection for detect and propose; the owner's has the detail."""
    service = _service(tmp_path, [])
    owner = json.dumps(service.detect(OWNER))
    assert "192.168.1.43" in owner and "keySet" in owner  # the detail the agent must not get
    detected, proposed = service.detect(AGENT), service.propose(AGENT)
    assert detected["engines"], detected
    for engine in detected["engines"]:
        assert set(engine) == {"id", "name", "kind", "class", "capability", "state"}, engine
    text = json.dumps([detected, proposed])
    for private in ("192.168.1.43", "192.168.1.44", "api.example.com", "baseUrl", '"host"', '"path"', "keySet", "THIS DEVICE"):
        assert private not in text, private
    lan = next(e for e in detected["engines"] if e["id"].endswith("lan-box"))
    assert lan["state"] == "READY" and lan["class"] == "remote", lan  # the owner's stored check
    assert all(set(row) == {"group", "label", "engineId", "state"} for row in proposed["rows"]), proposed


def test_an_agents_pr_read_is_its_launchs_repository_within_a_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Finding 4: another repository is refused; the read after the budget is refused; the owner is unscoped."""
    from holdspeak.principals import agent_credentials
    from holdspeak.services import github_provider
    from holdspeak.services.errors import ServiceError
    from holdspeak.services.github_provider import AGENT_PR_READS, GitHubProviderAdapter, delegated_repo_ref

    def gh(command: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        repo = command[command.index("-R") + 1]
        return subprocess.CompletedProcess(command, 0, json.dumps({"number": int(command[3]), "title": repo}), "")

    adapter = GitHubProviderAdapter(runner=gh)
    monkeypatch.setattr(github_provider, "_agent_pr_reads", {})
    credential = agent_credentials.issue(AGENT.identity, launch_id="run_codex2140",
                                         scope_items=(delegated_repo_ref("Acme/Ledger"),))
    try:
        agent = credential.principal
        with pytest.raises(ServiceError) as other:
            adapter.pr_get(agent, owner_repo="acme/payroll", number=1)
        assert other.value.code == "repository_not_delegated"
        with pytest.raises(ServiceError) as unlaunched:
            adapter.pr_get(Principal(PrincipalKind.AGENT, "agent:run:no-launch"), owner_repo="acme/ledger", number=1)
        assert unlaunched.value.code == "repository_not_delegated"
        for number in range(1, AGENT_PR_READS + 1):
            assert adapter.pr_get(agent, url=f"https://github.com/acme/ledger/pull/{number}")["number"] == number
        with pytest.raises(ServiceError) as spent:
            adapter.pr_get(agent, owner_repo="acme/ledger", number=1)
        assert spent.value.code == "read_budget_spent"
        assert adapter.pr_get(OWNER, owner_repo="acme/payroll", number=7)["number"] == 7
    finally:
        agent_credentials.revoke(AGENT.identity)


def test_jira_search_is_the_owners_and_no_agent_palette_offers_it() -> None:
    """Finding 5: owner only, egress class, out of CONDUCTOR and ASK; an agent's call is refused."""
    from holdspeak.mcp.families import declared
    from holdspeak.mcp.palettes import ASK, CONDUCTOR, resolve_palette
    from holdspeak.mcp.tool_authority import TOOL_AUTHORITY
    from holdspeak.operations import DESCRIPTORS

    (search,) = [d for d in DESCRIPTORS if d.name == "provider.jira_search"]
    assert search.owner_only and TOOL_AUTHORITY["provider.jira_search"] == "egress"
    assert "provider.jira_search" not in resolve_palette(CONDUCTOR)
    assert "provider.jira_search" not in resolve_palette(ASK)
    with pytest.raises(Exception) as refused:
        declared.dispatch("provider.jira_search", {"connection_ref": "a|b", "jql": "project = KAN"}, AGENT)
    assert "owner" in str(refused.value).lower(), refused.value


def test_a_bare_root_never_opens_the_owners_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Note 6: no database injected and the default one is the account's own: refused by name."""
    from holdspeak.db import core as db_core
    from holdspeak.runtime import composition

    account = tmp_path / "account"
    owners = account / ".local" / "share" / "holdspeak" / "holdspeak.db"
    owners.parent.mkdir(parents=True)
    owners.write_bytes(b"")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", owners)
    monkeypatch.setattr(db_core, "_db", None)
    monkeypatch.setattr(composition, "_account_home", lambda: account)
    opened: list[str] = []
    composition.install(composition.bare(label="codex-2140"))
    with pytest.raises(composition.NoRuntimeError, match="bare_root_needs_database"):
        composition.db_or(lambda: opened.append("db"))
    with pytest.raises(composition.NoRuntimeError, match="bare_root_needs_database"):
        composition.observer_or(lambda: opened.append("observer"))
    assert opened == []
    injected = Database(tmp_path / "injected.db")
    composition.install(composition.bare(injected, label="codex-2140"))
    assert composition.db_or(lambda: opened.append("db")) is injected and opened == []
