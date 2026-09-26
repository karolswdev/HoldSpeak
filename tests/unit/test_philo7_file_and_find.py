"""PHILO-7-04 fences for the cold-context rehearsal driver.

Every input is a real producer's output: the Phase 5 rehearsal's retained
Codex logs and server transcript, this story's retained cold-context attempt
(Codex 0.155's own ``mcp list``, rollout and event log against the rig hub),
and receipts minted by the real hub through the real remote route. The reds
are the Phase 5 logs themselves and deliberate mutations of real records.
"""
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
    PHASE7 / "lane-report-story-04.md",
    REPO / "docs/internal/philo/phase-7/file-and-find/rehearsal.md",
)


def _events(stage_dir: Path) -> list[dict[str, Any]]:
    return driver.read_events(stage_dir / "events.jsonl")


# ── the zero-read fence ──────────────────────────────────────────────────


@pytest.mark.parametrize(("stage", "count"), [("decision_thought", 25), ("import", 3)])
def test_the_zero_read_fence_fails_on_the_phase5_logs(stage: str, count: int) -> None:
    findings = driver.zero_read_findings(_events(PHASE5_RUN / "codex" / stage))
    assert len(findings) == count
    assert {f["type"] for f in findings} == {"command_execution"}


def test_the_phase5_run_counts_28_repository_commands_in_all() -> None:
    total = sum(len(driver.zero_read_findings(_events(stage)))
                for stage in sorted((PHASE5_RUN / "codex").iterdir()))
    assert total == 28


def test_a_turn_whose_only_actions_are_mcp_calls_passes() -> None:
    """The Phase 5 summary turn: four holdspeak calls, no shell."""
    events = _events(PHASE5_RUN / "codex" / "summary")
    assert [e for e in events if (e.get("item") or {}).get("type") == "mcp_tool_call"]
    assert driver.zero_read_findings(events) == []


@pytest.mark.parametrize("mutation", ["other_server", "file_change", "web_search"])
def test_any_other_action_turns_the_fence_red(mutation: str) -> None:
    events = copy.deepcopy(_events(PHASE5_RUN / "codex" / "summary"))
    call = next(e for e in events if e.get("type") == "item.completed"
                and (e.get("item") or {}).get("type") == "mcp_tool_call")
    if mutation == "other_server":
        call["item"]["server"] = "codex_apps"
    elif mutation == "file_change":
        call["item"] = {"id": "x", "type": "file_change", "changes": [{"path": "AGENTS.md"}]}
    else:
        call["item"] = {"id": "x", "type": "web_search", "query": "holdspeak repository"}
    assert len(driver.zero_read_findings(events)) == 1


def test_the_retained_cold_sessions_have_zero_findings() -> None:
    for stage in ("owner_file", "agent_ungranted", "agent_granted"):
        assert driver.zero_read_findings(_events(ATTEMPT / "codex" / stage)) == []


# ── every chosen tool is in the session's tools/list answer ─────────────


def _phase5_window(stage: str) -> list[dict[str, Any]]:
    rows = driver.read_events(PHASE5_RUN / "rehearsal-transcript.jsonl")
    start = json.loads((PHASE5_RUN / "codex" / stage / "transcript-window.json").read_text())["exchange_start"]
    return rows[start:]


def test_every_chosen_tool_is_in_the_sessions_tools_list() -> None:
    stage = PHASE5_RUN / "codex" / "summary"
    listed = driver.listed_tools(_phase5_window("summary"))
    calls = driver.p5._codex_mcp_calls(stage)
    assert len(listed) > 100 and calls
    assert driver.unlisted_tool_findings(calls, listed) == []
    assert driver.unlisted_tool_findings(calls, listed - {calls[0]["tool"]}) == [calls[0]["tool"]]


def test_the_cold_sessions_received_the_catalogue() -> None:
    rows = driver.read_events(ATTEMPT / "rehearsal-transcript.jsonl")
    for stage in ("owner_file", "agent_ungranted", "agent_granted"):
        start = json.loads((ATTEMPT / "codex" / stage / "transcript-window.json").read_text())["exchange_start"]
        audit = json.loads((ATTEMPT / "codex" / stage / "mcp-audit.json").read_text())
        assert len(driver.listed_tools(rows[start:start + 3])) == audit["tools_listed"] > 200


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


def test_the_retained_launch_setups_were_lawful() -> None:
    for leg_dir in ("owner", "agent_ungranted", "agent_granted"):
        record = _retained_setup(leg_dir)
        assert record["findings"] == []
        assert record["codex_home"]["files"] == ["auth.json"]
        assert record["codex_process_home"]["files"] == [".codex/auth.json"]
        assert all(parent["present"] == [] for parent in record["parents_checked"])
        assert "/" in [parent["path"] for parent in record["parents_checked"]]


@pytest.mark.parametrize("leg,leg_dir", [("owner", "owner"), ("agent", "agent_granted")])
def test_a_fresh_cold_root_passes_with_the_retained_codex_config(tmp_path: Path, leg: str, leg_dir: str) -> None:
    assert _check(_cold(tmp_path), _retained_setup(leg_dir), leg) == []


MUTATIONS = [
    "agents_in_parent", "claude_in_work", "codex_dir_in_parent", "file_in_work",
    "config_in_codex_home", "rules_in_codex_home", "extra_in_home", "git_in_parent",
    "second_server", "server_elsewhere", "no_bearer",
]


@pytest.mark.parametrize("mutation", MUTATIONS)
def test_each_launch_mutation_turns_the_check_red(tmp_path: Path, mutation: str) -> None:
    cold = _cold(tmp_path)
    leg = "agent" if mutation == "no_bearer" else "owner"
    record = _retained_setup("agent_granted" if leg == "agent" else "owner")
    servers = copy.deepcopy(record["servers"])
    if mutation == "agents_in_parent":
        (cold.root / "AGENTS.md").write_text("x")
    elif mutation == "claude_in_work":
        (cold.work / "CLAUDE.md").write_text("x")
    elif mutation == "codex_dir_in_parent":
        (cold.root.parent / ".codex").mkdir()
    elif mutation == "file_in_work":
        (cold.work / "notes.txt").write_text("x")
    elif mutation == "config_in_codex_home":
        (cold.codex_home / "config.toml").write_text('[projects."/x"]\ntrust_level = "trusted"\n')
    elif mutation == "rules_in_codex_home":
        (cold.codex_home / "rules").mkdir()
        (cold.codex_home / "rules" / "default.rules").write_text("x")
    elif mutation == "extra_in_home":
        (cold.home / ".zshrc").write_text("x")
    elif mutation == "git_in_parent":
        (cold.root / ".git").mkdir()
    elif mutation == "second_server":
        servers.append({**servers[0], "name": "codex_apps"})
    elif mutation == "server_elsewhere":
        servers[0]["transport"]["env"]["HOME"] = str(Path.home())
    elif mutation == "no_bearer":
        servers[0]["transport"]["bearer_token_env_var"] = None
    assert _check(cold, record, leg, servers) != []


def test_a_working_root_inside_the_repository_is_red(tmp_path: Path) -> None:
    record = _retained_setup("owner")
    transport = record["servers"][0]["transport"]
    work = REPO / ".tmp" / "philo7-04-inside"
    work.mkdir(parents=True, exist_ok=True)
    try:
        cold = _cold(tmp_path)
        findings, _ = driver.launch_setup_findings(
            work=work, codex_home=cold.codex_home, codex_process_home=cold.home,
            servers=record["servers"], leg="owner", hub_home=Path(transport["env"]["HOME"]),
            hub_url="http://127.0.0.1:1", mcp_command=Path(transport["command"]),
        )
    finally:
        work.rmdir()
    assert any("AGENTS.md" in f or "CLAUDE.md" in f or ".git" in f or "checkout" in f for f in findings)


# ── the initial context ──────────────────────────────────────────────────


def test_the_retained_initial_context_holds_no_repository_pointer() -> None:
    for stage in ("owner_file", "agent_ungranted", "agent_granted"):
        rollout = driver.read_events(ATTEMPT / "codex" / stage / "rollout.jsonl")
        findings, initial = driver.initial_context_findings(rollout)
        assert findings == [] and initial
        state = next(line for line in initial if line.get("type") == "world_state")["payload"]["state"]
        assert state["agents_md"] == {}


@pytest.mark.parametrize("mutation", ["repo_path", "agents_md", "instructions_header"])
def test_a_repository_pointer_in_the_initial_context_is_red(mutation: str) -> None:
    rollout = copy.deepcopy(driver.read_events(ATTEMPT / "codex" / "owner_file" / "rollout.jsonl"))
    if mutation == "agents_md":
        line = next(line for line in rollout if line.get("type") == "world_state")
        line["payload"]["state"]["agents_md"] = {str(REPO): "# AGENTS.md"}
    else:
        line = next(line for line in rollout if line.get("type") == "response_item"
                    and line["payload"].get("role") == "developer")
        text = f"cwd {REPO}" if mutation == "repo_path" else "# AGENTS.md instructions for /x"
        line["payload"]["content"].append({"type": "input_text", "text": text})
    findings, _ = driver.initial_context_findings(rollout)
    assert findings


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


def test_every_record_states_the_claim_verbatim_and_no_forbidden_wording() -> None:
    for record in RECORDS:
        text = record.read_text()
        assert driver.CLAIM in text, record
        assert driver.r3_wording_findings(text) == [], record
    for run, claim in ((ATTEMPT, driver.CLAIM_CODEX), (FINAL, driver.CLAIM)):
        for name in ("run.json", "run-status.json"):
            payload = json.loads((run / name).read_text())
            assert payload["claim"] == claim
            assert driver.r3_wording_findings(json.dumps(payload)) == []


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


def test_the_pairing_audit_pairs_every_call_and_refuses_a_changed_answer(tmp_path: Path) -> None:
    stage = PHASE5_RUN / "codex" / "summary"
    start = json.loads((stage / "transcript-window.json").read_text())["exchange_start"]
    hub = _TranscriptHub(tmp_path, PHASE5_RUN / "rehearsal-transcript.jsonl")
    audit = driver.p5._reconcile_mcp_calls(stage, hub, start)
    assert audit["codex_calls"] == len(audit["matches"]) == 4
    rows = driver.read_events(PHASE5_RUN / "rehearsal-transcript.jsonl")
    index = audit["matches"][0]["exchange_index"]
    rows[index]["response_body"]["result"]["content"][0]["text"] += " "
    mutated = tmp_path / "mutated.jsonl"
    mutated.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(RuntimeError, match="reconciliation"):
        driver.p5._reconcile_mcp_calls(stage, _TranscriptHub(tmp_path, mutated), start)


def test_the_cold_sessions_pair_their_handshake() -> None:
    for stage in ("owner_file", "agent_ungranted", "agent_granted"):
        audit = json.loads((ATTEMPT / "codex" / stage / "mcp-audit.json").read_text())
        assert audit["reconciliation_error"] is None
        methods = [row["rpc_method"] for row in audit["reconciliation"]["unmatched_turn_exchanges"]]
        assert methods == ["initialize", "notifications/initialized", "tools/list"]


# ── the AGENT leg: the bearer and the receipts ───────────────────────────


def test_codex_sent_the_desk_bearer_from_the_cold_config() -> None:
    """First-run answer: Codex 0.155 authenticated on /api/mcp with the DESK
    bearer named by ``bearer_token_env_var``; the credential shows its use."""
    legs = json.loads((ATTEMPT / "legs.json").read_text())
    for label in ("ungranted", "granted"):
        run = legs["agent"]["runs"][label]
        assert run["bearer_answer"]["sent_and_accepted"] is True
        assert [s["status"] for s in run["bearer_answer"]["mcp_statuses"]] == [200, 204, 200]
        assert run["credential_after"][0]["last_used_at"] is not None
        env = json.loads((ATTEMPT / "codex" / f"agent_{label}" / "environment.json").read_text())["env"]
        assert env[driver.BEARER_ENV].startswith("<redacted sha256:")
    assert legs["agent"]["credential"]["route"] == "POST /api/settings/remote/credentials"


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


def test_the_claude_zero_read_fence_fails_on_a_real_claude_read_of_the_repository() -> None:
    """A real ``claude -p`` in the same cold setup, told to read a repo file."""
    events = driver.read_events(CLAUDE_RED / "events.jsonl")
    assert driver.is_claude_log(events)
    findings = driver.any_zero_read_findings(events)
    # The red was minted from the lane's worktree; the path names that checkout.
    assert len(findings) == 1 and "/CLAUDE.md" in findings[0]["detail"]
    assert findings[0]["detail"].split()[0] in {"Bash", "Read"}


def test_the_combined_fence_still_fails_on_the_phase5_codex_logs() -> None:
    total = sum(len(driver.any_zero_read_findings(_events(stage)))
                for stage in sorted((PHASE5_RUN / "codex").iterdir()))
    assert total == 28


def test_every_closing_session_has_zero_findings_and_used_holdspeak() -> None:
    for stage in SESSIONS:
        events = _claude(stage)
        assert driver.any_zero_read_findings(events) == [], stage
        assert any(u["name"].startswith(driver.CLAUDE_MCP_PREFIX) for u in driver.claude_tool_uses(events))


@pytest.mark.parametrize("tool,tool_input", [
    ("Read", {"file_path": str(REPO / "AGENTS.md")}),
    ("Glob", {"pattern": "**/*.py", "path": str(REPO)}),
    ("Grep", {"pattern": "zone.file", "path": str(REPO)}),
    ("Bash", {"command": "ls"}),
    ("WebFetch", {"url": "https://github.com/karolswdev/HoldSpeak"}),
    ("Task", {"prompt": "read the repo"}),
    ("ReadMcpResourceTool", {"server": "other", "uri": "file:///x"}),
])
def test_any_other_claude_tool_turns_the_fence_red(tool: str, tool_input: dict[str, Any]) -> None:
    events = copy.deepcopy(_claude("owner_find"))
    events.append({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "toolu_red", "name": tool, "input": tool_input}]}})
    assert len(driver.any_zero_read_findings(events)) == 1


def test_every_chosen_holdspeak_tool_is_in_the_init_tool_list() -> None:
    for stage in SESSIONS:
        assert driver.claude_unlisted(_claude(stage)) == []
    events = copy.deepcopy(_claude("owner_file"))
    init = driver.claude_init(events)
    init["tools"] = [t for t in init["tools"] if t != "mcp__holdspeak__zone_file"]
    assert driver.claude_unlisted(events) == ["mcp__holdspeak__zone_file"]


def test_the_init_events_show_the_one_server_and_no_api_key() -> None:
    for stage in SESSIONS:
        init = driver.claude_init(_claude(stage))
        assert driver.claude_init_findings(init, "owner") == []
        assert init["permissionMode"] == "bypassPermissions" and init["model"] == driver.CLAUDE_MODEL


@pytest.mark.parametrize("mutation", ["second_server", "failed", "api_key"])
def test_an_init_mutation_turns_the_check_red(mutation: str) -> None:
    init = copy.deepcopy(driver.claude_init(_claude("owner_file")))
    if mutation == "second_server":
        init["mcp_servers"].append({"name": "claude.ai Gmail", "status": "connected"})
    elif mutation == "failed":
        init["mcp_servers"][0]["status"] = "failed"
    else:
        init["apiKeySource"] = "ANTHROPIC_API_KEY"
    assert driver.claude_init_findings(init, "owner")


def test_the_initial_context_loaded_no_instructions() -> None:
    for stage in ("owner_file", "agent_ungranted", "agent_granted"):
        lines = driver.read_events(FINAL / "claude" / stage / "initial-context.jsonl")
        findings, initial = driver.claude_context_findings(lines)
        assert findings == [] and initial
        kinds = {(line.get("attachment") or {}).get("type") for line in lines}
        assert "prompt_snapshot" in kinds
        assert not kinds & driver.CLAUDE_INSTRUCTION_ATTACHMENTS


@pytest.mark.parametrize("mutation", ["nested_memory", "claude_md_contents", "memory_contents", "repo_path"])
def test_an_instruction_in_the_initial_context_is_red(mutation: str) -> None:
    lines = copy.deepcopy(driver.read_events(FINAL / "claude" / "owner_file" / "initial-context.jsonl"))
    if mutation == "nested_memory":
        lines.insert(1, {"type": "attachment", "attachment": {"type": "nested_memory", "path": "/x/CLAUDE.md"}})
    else:
        text = {"claude_md_contents": f"Contents of {REPO}/CLAUDE.md (project instructions)",
                "memory_contents": "Contents of /Users/x/.claude/projects/y/memory/MEMORY.md",
                "repo_path": f"cwd {REPO}"}[mutation]
        lines.insert(1, {"type": "attachment", "attachment": {"type": "session_context", "text": text}})
    findings, _ = driver.claude_context_findings(lines)
    assert findings


def _final_setup(label: str) -> dict[str, Any]:
    return json.loads((FINAL / label / "launch-setup.json").read_text())


def test_the_retained_claude_launch_setups_were_lawful() -> None:
    for label in ("owner", "agent_ungranted", "agent_granted"):
        record = _final_setup(label)
        assert record["findings"] == []
        assert record["home"]["files"] == [".claude/.credentials.json"]
        assert record["env_keys"] == ["HOME", "LANG", "PATH", "TMPDIR", "USER"]
        assert "--strict-mcp-config" in record["flags"] and "bypassPermissions" in record["flags"]
        assert all(parent["present"] == [] for parent in record["parents_checked"])
        assert list(record["mcp_config"]["mcpServers"]) == ["holdspeak"]
    auth = json.loads((FINAL / "claude-auth.json").read_text())
    assert "refreshToken" not in auth["kept"] and "accessToken" in auth["kept"]


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


def test_the_claude_pairing_pairs_every_call_and_refuses_a_changed_answer() -> None:
    for stage in SESSIONS:
        audit = json.loads((FINAL / "claude" / stage / "mcp-audit.json").read_text())
        paired = driver.claude_pairing(_claude(stage), _turn_window(stage))
        assert len(paired["matches"]) == audit["reconciliation"]["claude_calls"] > 0
    window = copy.deepcopy(_turn_window("owner_find"))
    index = driver.claude_pairing(_claude("owner_find"), window)["matches"][0]["exchange_index"]
    window[index]["response_body"]["result"]["content"][0]["text"] += " "
    with pytest.raises(RuntimeError, match="reconciliation"):
        driver.claude_pairing(_claude("owner_find"), window)


def test_the_closing_agent_leg_receipts_pass_the_check() -> None:
    legs = json.loads((FINAL / "legs.json").read_text())["agent"]
    refused = [r["receipt"] for r in legs["runs"]["ungranted"]["receipts"]]
    filed = [r["receipt"] for r in legs["runs"]["granted"]["receipts"]]
    assert len(refused) == len(filed) == 1
    identity = legs["credential"]["identity"]
    assert identity == "claude-desk-agent"
    assert driver.agent_receipt_findings(refused[0], filed[0], identity=identity,
                                         grant_id=legs["grant"]["response"]["grant_id"]) == []
    for label in ("ungranted", "granted"):
        run = legs["runs"][label]
        assert run["bearer_answer"]["sent_and_accepted"] is True
        assert run["awaiting_decision"] == 0
    token_hash = legs["credential"]["token_sha256_12"]
    for label in ("agent_ungranted", "agent_granted"):
        text = (FINAL / label / "mcp-config.redacted.json").read_text()
        assert f"<redacted sha256:{token_hash}>" in text


# ── no account material in the retained records (the repository is public) ─


def test_no_retained_story04_record_holds_an_email_or_a_token() -> None:
    assert driver.account_leak_findings(PHASE7 / "assets/story-04-shots") == []
    assert driver.account_leak_findings(CLAUDE_RED) == []


@pytest.mark.parametrize("planted", [
    "someone.real@example.org",
    "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV",
    "sk-ant-oat01-abcdefghijklmnopqrstuvwxyz",
    "Authorization: Bearer abcdefghijklmnopqrstuvwx",
])
def test_the_leak_fence_turns_red_on_a_planted_value(tmp_path: Path, planted: str) -> None:
    source = FINAL / "claude" / "owner_file" / "initial-context.jsonl"
    target = tmp_path / "run" / "initial-context.jsonl"
    target.parent.mkdir()
    target.write_text(source.read_text() + json.dumps({"planted": planted}) + "\n")
    assert driver.account_leak_findings(tmp_path / "run")


def test_the_redaction_keeps_tools_and_servers_and_drops_the_account(tmp_path: Path) -> None:
    """Over a copy of a real retained event line, with the real account shape
    re-planted: the e-mail, an organisation id and synced skill names go;
    every tool name and the MCP server list stay."""
    events = driver.read_events(FINAL / "claude" / "owner_file" / "events.jsonl")
    init = copy.deepcopy(driver.claude_init(events))
    init["skills"] = ["dataviz", "account-skill-one", "anthropic-skills:account-skill-two"]
    run = tmp_path / "run"
    (run / ".claude/skills/synced/11111111-1111-1111-1111-111111111111_22222222-2222-2222-2222-222222222222/account-skill-one").mkdir(parents=True)
    listing = {"home": [".claude/skills/synced/11111111-1111-1111-1111-111111111111_22222222-2222-2222-2222-222222222222/account-skill-one/SKILL.md"]}
    (run / "home-at-launch.json").write_text(json.dumps(listing))
    context = {"type": "attachment", "attachment": {"type": "session_context", "context": {
        "userEmail": "The user's email address is person@example.org."}}}
    org = {"type": "attachment", "attachment": {"type": "credential_org",
                                                "organizationUuid": "11111111-1111-1111-1111-111111111111"}}
    (run / "events.jsonl").write_text("".join(json.dumps(x) + "\n" for x in (init, context, org)))
    assert driver.account_leak_findings(run)
    driver.redact_run(run)
    assert driver.account_leak_findings(run) == []
    lines = driver.read_events(run / "events.jsonl")
    assert lines[0]["tools"] == init["tools"] and lines[0]["mcp_servers"] == init["mcp_servers"]
    assert lines[0]["skills"] == ["dataviz", "<2 account skills, names redacted>"]
    assert driver.ACCOUNT_EMAIL in json.dumps(lines[1])
    assert lines[2]["attachment"]["organizationUuid"] == driver.ACCOUNT_ID
    assert "account-skill-one" not in (run / "home-at-launch.json").read_text()


# ── the owner's review: the decision carries its reason ──────────────────


def _decision_rows(run: Path) -> list[dict[str, Any]]:
    legs = json.loads((run / "legs.json").read_text())
    record = legs["owner"]["readbacks"]["decision_list"]
    rows = record["response"]
    rows = rows.get("decisions") if isinstance(rows, dict) else rows
    return [row for row in rows if "nightly build" in json.dumps(row).lower()]


def test_the_reason_check_is_red_on_the_thin_decision_the_owner_reviewed() -> None:
    (thin,) = _decision_rows(THIN)
    assert (THIN / "OWNER-REVIEW.txt").read_text().strip() == "owner review: the decision is thin"
    findings = driver.decision_reason_findings(thin)
    assert findings == ["the decision has no context: its reason is missing"]


def test_the_closing_decision_carries_its_reason_read_back_durably() -> None:
    legs = json.loads((FINAL / "legs.json").read_text())
    decision = legs["owner"]["decision"]
    assert driver.decision_reason_findings(decision) == []
    detail = legs["owner"]["readbacks"]["decision_read"]["response"]
    assert detail["context_markdown"] == decision["context_markdown"]
    assert decision["status"] == "proposed"
    assert "reason" not in legs["owner"]["readback_problems"]


@pytest.mark.parametrize("mutation", ["no_context", "reason_in_title", "other_reason"])
def test_a_thin_or_misplaced_reason_turns_the_check_red(mutation: str) -> None:
    decision = dict(json.loads((FINAL / "legs.json").read_text())["owner"]["decision"])
    if mutation == "no_context":
        decision["context_markdown"] = ""
    elif mutation == "reason_in_title":
        decision["title"] = decision["title"] + " because our runners are full"
    else:
        decision["context_markdown"] = "It seems like a good idea."
    assert driver.decision_reason_findings(decision)


def test_the_owner_shots_come_before_the_agent_files_and_show_the_reason() -> None:
    owner = json.loads((FINAL / "observations" / "owner-desk.json").read_text())
    agent = json.loads((FINAL / "observations" / "agent-desk.json").read_text())
    for row in owner["zone"]["pullouts"]:
        assert row["ok"] and row["absent"] == driver.AGENT_NOTE["title"]
        assert not any(driver.AGENT_NOTE["title"] in text for text in row["pullout_texts"])
    for row in owner["decision"]["pullouts"]:
        readable = row["readable"]
        assert readable["found"] and readable["visible"] and readable["in_viewport"] and readable["hit"]
        assert readable["font_px"] >= 12 and "full every night" in readable["text"]
    for row in agent["zone"]["pullouts"]:
        assert row["ok"] and any(driver.AGENT_NOTE["title"] in t and driver.OWNER_NOTE["title"] in t
                                 for t in row["pullout_texts"])
    for stage in ("owner-zone", "owner-decision", "brief", "agent-zone"):
        for width in (1440, 393):
            assert (FINAL / "shots" / stage / f"{width}.png").exists()
