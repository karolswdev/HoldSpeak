"""PHILO-7-04 fences for the cold-context rehearsal driver.

Every input is a real producer's output: the Phase 5 rehearsal's retained
Codex logs and server transcript, this story's retained cold-context attempt
(Codex 0.155's own ``mcp list``, rollout and event log against the rig hub),
and receipts minted by the real hub through the real remote route. The reds
are the Phase 5 logs themselves and deliberate mutations of real records.
"""
# History reads are parked: tests/_parked/history/tests/unit/test_philo7_file_and_find.py holds this file as it was, with the
# 37 test function(s) that read evidence archived on branch
# archive/evidence-2026-10-04 (pm/ARCHIVE.md).
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("philo7_file_and_find", REPO / "scripts/philo7_file_and_find.py")
assert SPEC and SPEC.loader
driver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(driver)

PHASE5_RUN = REPO / (
    "pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/"
    "final/20260925T001407Z-his-words-real"
)
PHASE7 = REPO / "pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract"
ATTEMPT = PHASE7 / "assets/story-04-shots/attempts/20260925T215624Z-file-and-find"
FINAL = PHASE7 / "assets/story-04-shots/final/20260926T015522Z-file-and-find"
#: The first closing run; the owner's review: "the decision is thin".
THIN = PHASE7 / "assets/story-04-shots/attempts/20260926T014230Z-file-and-find"
CLAUDE_RED = REPO / "docs/internal/philo/phase-7/file-and-find/red-claude-read"
SESSIONS = ("owner_file", "owner_find", "owner_decide", "owner_brief", "agent_ungranted", "agent_granted")
RECORDS = (
    PHASE7 / "evidence-story-04.md",
    REPO / "docs/internal/philo/phase-7/file-and-find/rehearsal.md",
)


def _events(stage_dir: Path) -> list[dict[str, Any]]:
    return driver.read_events(stage_dir / "events.jsonl")


# ── the zero-read fence ──────────────────────────────────────────────────


# ── every chosen tool is in the session's tools/list answer ─────────────


def _phase5_window(stage: str) -> list[dict[str, Any]]:
    rows = driver.read_events(PHASE5_RUN / "rehearsal-transcript.jsonl")
    start = json.loads((PHASE5_RUN / "codex" / stage / "transcript-window.json").read_text())["exchange_start"]
    return rows[start:]


# ── the launch setup ─────────────────────────────────────────────────────


def _retained_setup(leg_dir: str) -> dict[str, Any]:
    return json.loads((ATTEMPT / leg_dir / "launch-setup.json").read_text())


def _cold(tmp_path: Path) -> Any:
    auth = tmp_path / "auth-source.json"
    auth.write_text("{}")
    return driver.Cold(tmp_path / "root", "cold", auth)


def _check(cold: Any, record: dict[str, Any], leg: str, servers: Any = None) -> list[str]:
    servers = copy.deepcopy(record["servers"]) if servers is None else servers
    transport = record["servers"][0]["transport"]  # the run's own hub, never the mutation's
    if leg == "owner":
        hub_home = Path(transport["env"]["HOME"])
        hub_url = "http://127.0.0.1:1"
        command = Path(transport["command"])
    else:
        hub_home = Path("/nowhere")
        hub_url = transport["url"].removesuffix("/api/mcp")
        command = driver.MCP_COMMAND
    findings, _ = driver.launch_setup_findings(
        work=cold.work, codex_home=cold.codex_home, codex_process_home=cold.home,
        servers=servers, leg=leg, hub_home=hub_home, hub_url=hub_url, mcp_command=command,
    )
    return findings


MUTATIONS = [
    "agents_in_parent", "claude_in_work", "codex_dir_in_parent", "file_in_work",
    "config_in_codex_home", "rules_in_codex_home", "extra_in_home", "git_in_parent",
    "second_server", "server_elsewhere", "no_bearer",
]


# ── the initial context ──────────────────────────────────────────────────


# ── the owner's words ────────────────────────────────────────────────────


def test_the_prompts_are_ordinary_words() -> None:
    for prompt in driver.PROMPTS.values():
        assert driver.prompt_findings(prompt) == [], prompt


@pytest.mark.parametrize("injected", [
    "use zone.file", "with directory_id", "note:note_7ad7d3ec", "{\"kind\": \"notes\"}",
    "call desk.create", "advance the test clock",
])
def test_technical_words_turn_the_prompt_fence_red(injected: str) -> None:
    assert driver.prompt_findings(driver.PROMPTS["owner_file"] + " " + injected)


# ── the R3 wording ───────────────────────────────────────────────────────


@pytest.mark.parametrize("sentence", [
    "The session ran in a sandbox.",
    "Repository access was unavailable to Codex.",
    "Codex could not read the repository.",
    "It had no repository access.",
])
def test_forbidden_wording_turns_the_fence_red(sentence: str) -> None:
    assert driver.r3_wording_findings(sentence)


def test_the_codex_flag_name_alone_is_not_a_claim() -> None:
    assert driver.r3_wording_findings("$ codex exec --dangerously-bypass-approvals-and-sandbox") == []


# ── the pairing audit, carried from Phase 5 ──────────────────────────────


class _TranscriptHub:
    def __init__(self, home: Path, transcript_path: Path) -> None:
        self.home = home
        self.transcript_path = transcript_path


# ── the AGENT leg: the bearer and the receipts ───────────────────────────


sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo7_article_xi import AGENT_ID, _agent, _seed, _tool, hub  # noqa: E402,F401


def test_the_agent_receipt_check_over_real_receipts(hub: Any) -> None:  # noqa: F811
    ids = _seed(hub)
    agent = _agent(hub)
    ref = f"note:{ids['note']}"
    is_error, refused = _tool(agent, "zone.file", {"directory_id": ids["zone"], "primitive_id": ref})
    assert is_error is True
    _, refused_read = hub.mcp("kernel.receipt", {"operation_id": refused["operation_id"]})
    refused_receipt = refused_read["objects"][0]["receipt"]
    granted = hub.client.put(f"/api/settings/remote/delegations/{AGENT_ID}", json={}).json()
    is_error, filed = _tool(agent, "zone.file", {"directory_id": ids["zone"], "primitive_id": ref})
    assert is_error is False
    _, filed_read = hub.mcp("kernel.receipt", {"operation_id": filed["operation_id"]})
    filed_receipt = filed_read["objects"][0]["receipt"]
    grant_id = granted["grant_id"]

    assert driver.agent_receipt_findings(refused_receipt, filed_receipt,
                                         identity=AGENT_ID, grant_id=grant_id) == []
    # the reds: the receipts swapped, another grant, another actor, a missing run
    assert driver.agent_receipt_findings(filed_receipt, refused_receipt, identity=AGENT_ID, grant_id=grant_id)
    assert driver.agent_receipt_findings(refused_receipt, filed_receipt, identity=AGENT_ID,
                                         grant_id="deskdeleg_other")
    assert driver.agent_receipt_findings(refused_receipt, filed_receipt, identity="someone-else",
                                         grant_id=grant_id)
    assert driver.agent_receipt_findings(refused_receipt, None, identity=AGENT_ID, grant_id=grant_id)


# ── the Claude client (R6: "Claude closes it") ───────────────────────────


def _claude(stage: str) -> list[dict[str, Any]]:
    return driver.read_events(FINAL / "claude" / stage / "events.jsonl")


def _final_setup(label: str) -> dict[str, Any]:
    return json.loads((FINAL / label / "launch-setup.json").read_text())


def _claude_cold(tmp_path: Path) -> Any:
    return driver.ClaudeCold(tmp_path / "root", "cold", {"claudeAiOauth": {"accessToken": "x"}})


def _claude_check(cold: Any, leg: str, config: dict[str, Any]) -> list[str]:
    findings, _ = driver.claude_launch_findings(
        work=cold.work, home=cold.home, mcp_config=config, leg=leg,
        hub_home=Path("/hub-home"), hub_url="http://127.0.0.1:1",
    )
    return findings


@pytest.mark.parametrize("leg", ["owner", "agent"])
def test_a_fresh_claude_cold_root_passes(tmp_path: Path, leg: str) -> None:
    config = driver.claude_mcp_config(leg, Path("/hub-home"), "http://127.0.0.1:1", "tok")
    assert _claude_check(_claude_cold(tmp_path), leg, config) == []


CLAUDE_MUTATIONS = ["claude_md_in_parent", "dot_claude_in_parent", "agents_in_work", "settings_in_home",
                    "memory_in_home", "second_server", "sidecar_elsewhere", "no_bearer", "owner_token_url"]


@pytest.mark.parametrize("mutation", CLAUDE_MUTATIONS)
def test_each_claude_launch_mutation_turns_the_check_red(tmp_path: Path, mutation: str) -> None:
    cold = _claude_cold(tmp_path)
    leg = "agent" if mutation in {"no_bearer", "owner_token_url"} else "owner"
    config = driver.claude_mcp_config(leg, Path("/hub-home"), "http://127.0.0.1:1", "tok")
    server = config["mcpServers"]["holdspeak"]
    if mutation == "claude_md_in_parent":
        (cold.root / "CLAUDE.md").write_text("x")
    elif mutation == "dot_claude_in_parent":
        (cold.root.parent / ".claude").mkdir()
    elif mutation == "agents_in_work":
        (cold.work / "AGENTS.md").write_text("x")
    elif mutation == "settings_in_home":
        (cold.home / ".claude" / "settings.json").write_text("{}")
    elif mutation == "memory_in_home":
        (cold.home / ".claude" / "CLAUDE.md").write_text("x")
    elif mutation == "second_server":
        config["mcpServers"]["pixellab"] = {"type": "http", "url": "https://example.invalid/mcp"}
    elif mutation == "sidecar_elsewhere":
        server["env"]["HOME"] = str(Path.home())
    elif mutation == "no_bearer":
        server["headers"] = {}
    else:
        server["url"] = "http://127.0.0.1:2/api/mcp"
    assert _claude_check(cold, leg, config) != []


def _turn_window(stage: str) -> list[dict[str, Any]]:
    """The server rows of one turn: from its start to the next turn's start."""
    rows = driver.read_events(FINAL / "rehearsal-transcript.jsonl")
    starts = [json.loads((FINAL / "claude" / s / "transcript-window.json").read_text())["exchange_start"]
              for s in SESSIONS]
    index = SESSIONS.index(stage)
    end = starts[index + 1] if index + 1 < len(starts) else len(rows)
    return rows[starts[index]:end]


# ── no account material in the retained records (the repository is public) ─


# ── the owner's review: the decision carries its reason ──────────────────


def _decision_rows(run: Path) -> list[dict[str, Any]]:
    legs = json.loads((run / "legs.json").read_text())
    record = legs["owner"]["readbacks"]["decision_list"]
    rows = record["response"]
    rows = rows.get("decisions") if isinstance(rows, dict) else rows
    return [row for row in rows if "nightly build" in json.dumps(row).lower()]


def test_repo_doc_resources_are_every_repo_backed_resource() -> None:
    """Every resource branch in resources.py that reads the checkout
    (``_REPO_ROOT``) is in REPO_DOC_RESOURCES, and nothing else is."""
    import re as _re

    source = (REPO / "holdspeak/mcp/resources.py").read_text()
    branches = _re.split(r'\n    if uri == "', source)
    backed = {"" + b.split('"', 1)[0] for b in branches[1:] if "_REPO_ROOT" in b.split("\n    if ", 1)[0]}
    assert backed == set(driver.REPO_DOC_RESOURCES) == {"holdspeak://desk/constitution"}


